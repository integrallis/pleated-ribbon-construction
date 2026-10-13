// E7 driver: input-ordering strategies around fastfilter_cpp's UNMODIFIED homogeneous ribbon
// kernel, generalised from e1b_phase1.cc in four directions (experiments/e7_rigour/README.md):
//
//   - band width and result bits are compile-time parameters (-DE7_W=64|128, -DE7_R=<columns>);
//   - the slot overhead m/n can be given on the command line;
//   - keys can come from a file of 64-bit integers or from a file of strings;
//   - the hardware counters scoped to the banding call can be named raw PMU events.
//
// Sequential strategies only (reference, sort_radix, sort_ips2ra, partitioned): the parallel
// build stays in e1b_phase1.cc. For -DE7_W=64 -DE7_R=7, synthetic keys and the default overhead
// this driver must produce the same solution fingerprint as e1b_phase1 for the same (n, rep);
// the runner's crosscheck stage refuses to go on otherwise.
//
// Two binaries per (W, R):
//   default        Key = uint64_t. String keys are hashed once (XXH3) into a uint64_t array,
//                  timed as its own phase, and everything after that sees integers.
//   -DE7_STRKEYS   Key = a reference to the string. The kernel's hash function is XXH3 over the
//                  string bytes, so the hash is recomputed in each partition pass and in banding,
//                  and reordering permutes references, not string bytes.
//
// Usage: e7_driver <n_keys> <strategy> <rep> <keys> [overhead=default] [window_shift=default]
//   keys: synth | u64:<file> | str:<file>
//     u64 file: raw little-endian uint64_t values; the first n are used.
//     str file: uint64_t count, uint64_t offsets[count + 1], then the bytes; first n used.
//   env E7_COUNTERS: none (default) | generic | raw:<hex>[,<hex>...]
//     generic = cycles, instructions, the generic cache-miss event (as e1b_phase1 on x86).
//     raw     = PERF_TYPE_RAW event codes, counted as one group, reported in the given order.
// Output: one JSON line on stdout. Exit 1 on any false negative.

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <memory>
#include <string>
#include <vector>

#define XXH_INLINE_ALL
#include <xxhash.h>

#include "ribbon_impl.h"        // harness/fastfilter_cpp/src/ribbon (pinned, unmodified)
#include "linux-perf-events.h"  // harness/fastfilter_cpp/benchmarks (pinned, unmodified)
#include "ips2ra.hpp"           // harness/BuRR/ips2ra (pinned; BuRR's own sorter, sequential)

#ifndef E7_W
#define E7_W 64
#endif
#ifndef E7_R
#define E7_R 7
#endif

#if E7_W == 64
using CoeffType = uint64_t;
#elif E7_W == 128
using CoeffType = ribbon::Unsigned128;
#else
#error "E7_W must be 64 or 128"
#endif

struct StrRef {
  const char* p;
  uint64_t len;
};

#ifdef E7_STRKEYS
using KeyType = StrRef;
#else
using KeyType = uint64_t;
#endif

// ---- Configuration as filterapi.h's RibbonTS (HomogRibbonFilter), with the key type and, for
// string keys, the hash function replaced ----
struct TS {
  static constexpr bool kIsFilter = true;
  static constexpr bool kHomogeneous = true;
  static constexpr bool kFirstCoeffAlwaysOne = true;
  static constexpr bool kUseSmash = false;
  using CoeffRow = CoeffType;
  using Hash = uint64_t;
  using Key = KeyType;
  using Seed = uint32_t;
  using Index = size_t;
  using ResultRow = uint32_t;
  static constexpr bool kAllowZeroStarts = false;
  static constexpr uint32_t kFixedNumColumns = E7_R;

#ifdef E7_STRKEYS
  static Hash HashFn(const Key& input, Seed raw_seed) {
    return XXH3_64bits_withSeed(input.p, input.len, raw_seed);
  }
#else
  // Verbatim from filterapi.h.
  static Hash HashFn(const Hash& input, Seed raw_seed) {
    uint64_t h = input + raw_seed;
    h ^= h >> 33;
    h *= UINT64_C(0xff51afd7ed558ccd);
    h ^= h >> 33;
    h *= UINT64_C(0xc4ceb9fe1a85ec53);
    h ^= h >> 33;
    return h;
  }
#endif
};

IMPORT_RIBBON_IMPL_TYPES(TS);
static constexpr double kFractionalCols = (double)E7_R;

// ---- Keys ----
static inline uint64_t mix64(uint64_t z) {
  z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
  z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
  return z ^ (z >> 31);
}

// Same generator and seed as e1b_phase1.cc.
[[maybe_unused]] static std::vector<uint64_t> make_keys(size_t n, uint64_t seed) {
  std::vector<uint64_t> keys(n);
  uint64_t s = seed;
  for (size_t i = 0; i < n; i++) {
    s += UINT64_C(0x9e3779b97f4a7c15);
    keys[i] = mix64(s);
  }
  return keys;
}

static std::vector<char> read_file(const std::string& path) {
  std::ifstream f(path, std::ios::binary | std::ios::ate);
  if (!f) {
    fprintf(stderr, "cannot open %s\n", path.c_str());
    exit(2);
  }
  const std::streamsize size = f.tellg();
  std::vector<char> data((size_t)size);
  f.seekg(0);
  if (!f.read(data.data(), size)) {
    fprintf(stderr, "cannot read %s\n", path.c_str());
    exit(2);
  }
  return data;
}

// The strings of a prepared file: count, offsets[count + 1], bytes.
struct StringSet {
  std::vector<char> data;
  const uint64_t* offsets = nullptr;
  const char* bytes = nullptr;
  size_t count = 0;

  explicit StringSet(const std::string& path) : data(read_file(path)) {
    if (data.size() < 16) {
      fprintf(stderr, "%s is too short\n", path.c_str());
      exit(2);
    }
    uint64_t c;
    memcpy(&c, data.data(), 8);
    count = (size_t)c;
    offsets = reinterpret_cast<const uint64_t*>(data.data() + 8);
    bytes = data.data() + 8 + 8 * (count + 1);
    if (data.size() < 8 + 8 * (count + 1) || data.size() != 8 + 8 * (count + 1) + offsets[count]) {
      fprintf(stderr, "%s is not a prepared string file\n", path.c_str());
      exit(2);
    }
  }
  StrRef at(size_t i) const { return StrRef{bytes + offsets[i], offsets[i + 1] - offsets[i]}; }
};

static double now_ns() {
  return std::chrono::duration<double, std::nano>(
             std::chrono::steady_clock::now().time_since_epoch())
      .count();
}

// ---- Reorder strategies (as e1b_phase1.cc, over the key type) ----

static std::vector<KeyType> reorder_partitioned(const std::vector<KeyType>& keys,
                                                const Hasher& hasher, size_t num_starts,
                                                size_t shift) {
  const size_t n_windows = (num_starts >> shift) + 2;
  std::vector<size_t> counts(n_windows + 1, 0);
  // Pass A: count per window (hash recomputed; no pair materialization).
  for (const KeyType& k : keys) {
    size_t start = hasher.GetStart(hasher.GetHash(k), num_starts);
    counts[(start >> shift) + 1]++;
  }
  for (size_t w = 1; w <= n_windows; w++) counts[w] += counts[w - 1];
  // Pass B: place keys in window order (arrival order preserved within a window).
  std::vector<KeyType> out(keys.size());
  std::vector<size_t> cursor(counts.begin(), counts.end() - 1);
  for (const KeyType& k : keys) {
    size_t start = hasher.GetStart(hasher.GetHash(k), num_starts);
    out[cursor[start >> shift]++] = k;
  }
  return out;
}

struct StartKey {
  uint32_t start;
  KeyType key;
};

static std::vector<StartKey> make_pairs(const std::vector<KeyType>& keys, const Hasher& hasher,
                                        size_t num_starts) {
  std::vector<StartKey> pairs(keys.size());
  for (size_t i = 0; i < keys.size(); i++) {
    pairs[i].start = (uint32_t)hasher.GetStart(hasher.GetHash(keys[i]), num_starts);
    pairs[i].key = keys[i];
  }
  return pairs;
}

static std::vector<KeyType> reorder_sort_ips2ra(const std::vector<KeyType>& keys,
                                                const Hasher& hasher, size_t num_starts) {
  auto pairs = make_pairs(keys, hasher, num_starts);
  ips2ra::sort(pairs.begin(), pairs.end(), [](const StartKey& p) { return p.start; });
  std::vector<KeyType> out(keys.size());
  for (size_t i = 0; i < pairs.size(); i++) out[i] = pairs[i].key;
  return out;
}

// LSD radix sort by start, 3 x 10-bit passes (num_starts < 2^30 at all sizes used here).
static std::vector<KeyType> reorder_sort_radix(const std::vector<KeyType>& keys,
                                               const Hasher& hasher, size_t num_starts) {
  auto a = make_pairs(keys, hasher, num_starts);
  std::vector<StartKey> b(a.size());
  for (int pass = 0; pass < 3; pass++) {
    const int shift = pass * 10;
    std::vector<size_t> hist(1024 + 1, 0);
    for (const auto& p : a) hist[((p.start >> shift) & 1023) + 1]++;
    for (int i = 1; i <= 1024; i++) hist[i] += hist[i - 1];
    for (const auto& p : a) b[hist[(p.start >> shift) & 1023]++] = p;
    std::swap(a, b);
  }
  std::vector<KeyType> out(keys.size());
  for (size_t i = 0; i < a.size(); i++) out[i] = a[i].key;
  return out;
}

// The banding call, which is what StandardBanding::AddRange does. It has a function of its own
// because, inlined into the long function below, GCC 13 compiled the kernel's loop to 15 more
// instructions per key than in e1b_phase1 (114.75 against 99.75 at band width 64, measured while
// testing the cross-check); on its own it compiles to 97.75.
__attribute__((noinline)) static bool band_all(Banding* b, const std::vector<KeyType>& in) {
  return ribbon::BandingAddRange(b, *b, in.begin(), in.end());
}

static int run(int argc, char** argv) {
  if (argc < 5 || argc > 7) {
    fprintf(stderr,
            "usage: %s <n_keys> <strategy> <rep> <synth|u64:file|str:file> [overhead=default] "
            "[window_shift=default]\n",
            argv[0]);
    return 2;
  }
  const size_t n = strtoull(argv[1], nullptr, 10);
  const std::string strategy = argv[2];
  const int rep = atoi(argv[3]);
  const std::string source = argv[4];
  const std::string overhead_arg = argc > 5 ? argv[5] : "default";
  // 2^16 slots of banding state are about 768 KiB at w = 64 (12 bytes per slot); at w = 128 a
  // slot takes 20 bytes, so the default is 2^15 slots (640 KiB).
  const size_t default_shift = E7_W == 64 ? 16 : 15;
  const size_t shift =
      (argc > 6 && std::string(argv[6]) != "default") ? strtoull(argv[6], nullptr, 10)
                                                      : default_shift;
  if (strategy != "reference" && strategy != "sort_radix" && strategy != "sort_ips2ra" &&
      strategy != "partitioned") {
    fprintf(stderr, "unknown strategy %s\n", strategy.c_str());
    return 2;
  }

  // Sizing as HomogRibbonFilter (filterapi.h) unless the overhead is given.
  const double overhead = overhead_arg == "default"
                              ? 1.0 + (4.0 + kFractionalCols * 0.25) / (8.0 * sizeof(CoeffType))
                              : strtod(overhead_arg.c_str(), nullptr);
  if (!(overhead > 1.0 && overhead < 2.0)) {
    fprintf(stderr, "overhead %s out of range\n", overhead_arg.c_str());
    return 2;
  }
  const size_t num_slots = InterleavedSoln::RoundUpNumSlots((size_t)(overhead * n));
  const size_t bytes = (size_t)((num_slots * kFractionalCols + 7) / 8);

  // ---- Keys. Loading and generating are outside every timer; hashing strings once is timed.
  std::unique_ptr<StringSet> strings;
  std::vector<KeyType> keys;
  double hash_ns = 0;
  double mean_key_bytes = 8;
  const std::string kind = source.substr(0, source.find(':'));
  const std::string path = source.find(':') == std::string::npos ? "" : source.substr(kind.size() + 1);
  if (kind == "str") {
    strings = std::make_unique<StringSet>(path);
    if (strings->count < n) {
      fprintf(stderr, "%s holds %zu strings, fewer than %zu\n", path.c_str(), strings->count, n);
      return 2;
    }
    mean_key_bytes = (double)strings->offsets[n] / n;
    keys.resize(n);
#ifdef E7_STRKEYS
    for (size_t i = 0; i < n; i++) keys[i] = strings->at(i);
#else
    double t = now_ns();
    for (size_t i = 0; i < n; i++) {
      const StrRef s = strings->at(i);
      keys[i] = XXH3_64bits(s.p, s.len);
    }
    hash_ns = now_ns() - t;
#endif
  } else {
#ifdef E7_STRKEYS
    fprintf(stderr, "this binary takes str:<file> keys only\n");
    return 2;
#else
    if (kind == "synth") {
      keys = make_keys(n, UINT64_C(0xA11CE) + rep);
    } else if (kind == "u64") {
      std::vector<char> raw = read_file(path);
      if (raw.size() < 8 * n) {
        fprintf(stderr, "%s holds fewer than %zu keys\n", path.c_str(), n);
        return 2;
      }
      keys.resize(n);
      memcpy(keys.data(), raw.data(), 8 * n);
    } else {
      fprintf(stderr, "unknown key source %s\n", source.c_str());
      return 2;
    }
#endif
  }

  Hasher hasher;
  Banding banding(num_slots);
  const size_t num_starts = banding.GetNumStarts();

  // ---- Reorder phase (timed).
  double t0 = now_ns();
  std::vector<KeyType> ordered;
  if (strategy == "partitioned") {
    ordered = reorder_partitioned(keys, hasher, num_starts, shift);
  } else if (strategy == "sort_radix") {
    ordered = reorder_sort_radix(keys, hasher, num_starts);
  } else if (strategy == "sort_ips2ra") {
    ordered = reorder_sort_ips2ra(keys, hasher, num_starts);
  }
  const double reorder_ns = now_ns() - t0;
  const std::vector<KeyType>& input = ordered.empty() ? keys : ordered;

  // ---- Counters, scoped to the banding call.
  const std::string counters = getenv("E7_COUNTERS") ? getenv("E7_COUNTERS") : "none";
  std::unique_ptr<LinuxEvents<PERF_TYPE_HARDWARE>> generic;
  std::unique_ptr<LinuxEvents<PERF_TYPE_RAW>> raw;
  std::vector<int> raw_codes;
  if (counters == "generic") {
    generic = std::make_unique<LinuxEvents<PERF_TYPE_HARDWARE>>(std::vector<int>{
        PERF_COUNT_HW_CPU_CYCLES, PERF_COUNT_HW_INSTRUCTIONS, PERF_COUNT_HW_CACHE_MISSES});
  } else if (counters.rfind("raw:", 0) == 0) {
    size_t pos = 4;
    while (pos < counters.size()) {
      size_t comma = counters.find(',', pos);
      if (comma == std::string::npos) comma = counters.size();
      raw_codes.push_back((int)strtol(counters.substr(pos, comma - pos).c_str(), nullptr, 16));
      pos = comma + 1;
    }
    raw = std::make_unique<LinuxEvents<PERF_TYPE_RAW>>(raw_codes);
  } else if (counters != "none") {
    fprintf(stderr, "unknown E7_COUNTERS %s\n", counters.c_str());
    return 2;
  }
  std::vector<unsigned long long> generic_results(3, 0), raw_results(raw_codes.size(), 0);

  // ---- Banding phase (timed).
  t0 = now_ns();
  if (generic) generic->start();
  if (raw) raw->start();
  const bool ok = band_all(&banding, input);
  if (generic) generic->end(generic_results);
  if (raw) raw->end(raw_results);
  const double banding_ns = now_ns() - t0;
  if (!ok) {
    fprintf(stderr, "banding failed (must not happen for homogeneous ribbon)\n");
    return 1;
  }

  // ---- Back-substitution phase (timed; reference code).
  std::unique_ptr<char[]> ptr(new char[bytes]);
  InterleavedSoln soln(ptr.get(), bytes);
  t0 = now_ns();
  soln.BackSubstFrom(banding);
  const double backsubst_ns = now_ns() - t0;

  uint64_t fnv = UINT64_C(0xcbf29ce484222325);
  for (size_t i = 0; i < bytes; i++) {
    fnv = (fnv ^ (uint8_t)ptr[i]) * UINT64_C(0x100000001b3);
  }

  // ---- Checks: zero false negatives; measured false-positive rate.
  size_t fn = 0;
  for (const KeyType& k : keys) fn += !soln.FilterQuery(k, hasher);
  const size_t n_probes = 2'000'000;
  size_t fp = 0;
#ifdef E7_STRKEYS
  // Probes are strings no key set here contains (they start with a byte no key starts with).
  char probe[32];
  probe[0] = '\x01';
  for (size_t i = 0; i < n_probes; i++) {
    const int len = snprintf(probe + 1, sizeof(probe) - 1, "e7-probe-%zu", i);
    fp += soln.FilterQuery(StrRef{probe, (uint64_t)len + 1}, hasher);
  }
#else
  uint64_t s = UINT64_C(0xD15EA5E);
  for (size_t i = 0; i < n_probes; i++) {
    s += UINT64_C(0x9e3779b97f4a7c15);
    fp += soln.FilterQuery(mix64(s) ^ UINT64_C(0x5555555555555555), hasher);
  }
#endif

  std::string counter_json = "\"counters\":\"" + counters + "\"";
  char buf[160];
  if (generic) {
    snprintf(buf, sizeof(buf),
             ",\"banding_cycles_per_key\":%.2f,\"banding_instr_per_key\":%.2f,"
             "\"banding_miss_per_key\":%.3f",
             (double)generic_results[0] / n, (double)generic_results[1] / n,
             (double)generic_results[2] / n);
    counter_json += buf;
  }
  if (raw) {
    counter_json += ",\"banding_raw_per_key\":{";
    for (size_t i = 0; i < raw_codes.size(); i++) {
      snprintf(buf, sizeof(buf), "%s\"0x%x\":%.4f", i ? "," : "", raw_codes[i],
               (double)raw_results[i] / n);
      counter_json += buf;
    }
    counter_json += "}";
  }

  printf(
      "{\"strategy\":\"%s\",\"n\":%zu,\"rep\":%d,\"w\":%d,\"r\":%d,\"keys\":\"%s\","
      "\"string_keys_direct\":%s,\"mean_key_bytes\":%.2f,\"overhead\":%.6f,\"num_slots\":%zu,"
      "\"hash_ns_per_key\":%.3f,\"reorder_ns_per_key\":%.3f,\"banding_ns_per_key\":%.3f,"
      "\"backsubst_ns_per_key\":%.3f,\"total_ns_per_key\":%.3f,%s,"
      "\"false_negatives\":%zu,\"fpr\":%.6f,\"bits_per_key\":%.3f,\"window_shift\":%zu,"
      "\"soln_fnv\":\"%016llx\"}\n",
      strategy.c_str(), n, rep, E7_W, E7_R, kind.c_str(),
#ifdef E7_STRKEYS
      "true",
#else
      "false",
#endif
      mean_key_bytes, (double)num_slots / n, num_slots, hash_ns / n, reorder_ns / n,
      banding_ns / n, backsubst_ns / n, (hash_ns + reorder_ns + banding_ns + backsubst_ns) / n,
      counter_json.c_str(), fn, (double)fp / n_probes, bytes * 8.0 / n, shift,
      (unsigned long long)fnv);
  return fn == 0 ? 0 : 1;
}

int main(int argc, char** argv) { return run(argc, argv); }
