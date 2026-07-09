// E1b Phase 1 driver: input-ordering strategies around fastfilter_cpp's UNMODIFIED
// homogeneous ribbon kernel (StandardBanding/BandingAddRange/InterleavedSoln).
// See experiments/e1b_ribbon_construction/README.md (H-E1b-1, registered by amendment).
//
// Every strategy is exactly: (optional) permutation of the key array -> one call to the
// reference banding -> reference BackSubstFrom. The banding kernel, its internal prefetch
// pipeline, and back-substitution are the harness's code, untouched; measured deltas are
// attributable purely to input order. Configuration replicates HomogRibbon64_7
// (filterapi.h:520-575; benchmark id 1076 = the Phase-0 baseline).
//
// Usage: ./e1b_phase1 <n_keys> <strategy> <rep>
//   strategy in { reference, noprefetch, sort_std, sort_radix, partitioned }
// Output: one JSON line on stdout (the raw artifact). Exit 1 on any false negative.

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <memory>
#include <string>
#include <thread>
#include <vector>

#include "ribbon_impl.h"        // harness/fastfilter_cpp/src/ribbon (pinned, unmodified)
#include "linux-perf-events.h"  // harness/fastfilter_cpp/benchmarks (pinned, unmodified)
#include "ips2ra.hpp"           // harness/BuRR/ips2ra (pinned submodule; BuRR's own sorter, sequential)

// ---- Configuration copied verbatim from filterapi.h (HomogRibbon64_7) ----
template <typename CoeffType, bool kHomog, uint32_t kNumColumns, bool kSmash = false>
struct RibbonTS {
  static constexpr bool kIsFilter = true;
  static constexpr bool kHomogeneous = kHomog;
  static constexpr bool kFirstCoeffAlwaysOne = true;
  static constexpr bool kUseSmash = kSmash;
  using CoeffRow = CoeffType;
  using Hash = uint64_t;
  using Key = uint64_t;
  using Seed = uint32_t;
  using Index = size_t;
  using ResultRow = uint32_t;
  static constexpr bool kAllowZeroStarts = false;
  static constexpr uint32_t kFixedNumColumns = kNumColumns;

  static Hash HashFn(const Hash& input, Seed raw_seed) {
    uint64_t h = input + raw_seed;
    h ^= h >> 33;
    h *= UINT64_C(0xff51afd7ed558ccd);
    h ^= h >> 33;
    h *= UINT64_C(0xc4ceb9fe1a85ec53);
    h ^= h >> 33;
    return h;
  }
};

using TS = RibbonTS<uint64_t, /*kHomog=*/true, /*kNumColumns=*/7>;
IMPORT_RIBBON_IMPL_TYPES(TS);
static constexpr double kFractionalCols = 7.0;

// Same-code-different-UsePrefetch variant (static dispatch through the template call site).
// Quantifies the harness's always-on construction prefetch, which RocksDB's own comment
// marks "TODO: verify/validate".
struct NoPrefetchBanding : Banding {
  using Banding::Banding;
  inline bool UsePrefetch() const { return false; }
};

// ---- Deterministic keys: splitmix64, same constants/seed family as the Rust side ----
static inline uint64_t mix64(uint64_t z) {
  z = (z ^ (z >> 30)) * UINT64_C(0xbf58476d1ce4e5b9);
  z = (z ^ (z >> 27)) * UINT64_C(0x94d049bb133111eb);
  return z ^ (z >> 31);
}

static std::vector<uint64_t> make_keys(size_t n, uint64_t seed) {
  std::vector<uint64_t> keys(n);
  uint64_t s = seed;
  for (size_t i = 0; i < n; i++) {
    s += UINT64_C(0x9e3779b97f4a7c15);
    keys[i] = mix64(s);
  }
  return keys;
}

static double now_ns() {
  return std::chrono::duration<double, std::nano>(
             std::chrono::steady_clock::now().time_since_epoch())
      .count();
}

// ---- Reorder strategies ----

// Default window shift: 1<<16 slots/window x ~12 B/slot banding storage ~= 768 KiB, under
// half L2. Phase-1b sweeps this at runtime (identical code path for all sweep points).
static constexpr size_t kDefaultWindowShift = 16;

static std::vector<uint64_t> reorder_partitioned(const std::vector<uint64_t>& keys,
                                                 const Hasher& hasher, size_t num_starts,
                                                 size_t shift,
                                                 std::vector<size_t>* counts_out = nullptr) {
  const size_t n_windows = (num_starts >> shift) + 2;
  std::vector<size_t> counts(n_windows + 1, 0);
  // Pass A: count per window (hash recomputed; no pair materialization — E1a lesson).
  for (uint64_t k : keys) {
    size_t start = hasher.GetStart(hasher.GetHash(k), num_starts);
    counts[(start >> shift) + 1]++;
  }
  for (size_t w = 1; w <= n_windows; w++) counts[w] += counts[w - 1];
  // Pass B: place keys in window order (arrival order preserved within a window).
  std::vector<uint64_t> out(keys.size());
  std::vector<size_t> cursor(counts.begin(), counts.end() - 1);
  for (uint64_t k : keys) {
    size_t start = hasher.GetStart(hasher.GetHash(k), num_starts);
    out[cursor[start >> shift]++] = k;
  }
  if (counts_out) *counts_out = std::move(counts);
  return out;
}

struct StartKey {
  uint32_t start;
  uint64_t key;
};

static std::vector<StartKey> make_pairs(const std::vector<uint64_t>& keys,
                                        const Hasher& hasher, size_t num_starts) {
  std::vector<StartKey> pairs(keys.size());
  for (size_t i = 0; i < keys.size(); i++) {
    pairs[i].start = (uint32_t)hasher.GetStart(hasher.GetHash(keys[i]), num_starts);
    pairs[i].key = keys[i];
  }
  return pairs;
}

static std::vector<uint64_t> reorder_sort_std(const std::vector<uint64_t>& keys,
                                              const Hasher& hasher, size_t num_starts) {
  auto pairs = make_pairs(keys, hasher, num_starts);
  std::sort(pairs.begin(), pairs.end(),
            [](const StartKey& a, const StartKey& b) { return a.start < b.start; });
  std::vector<uint64_t> out(keys.size());
  for (size_t i = 0; i < pairs.size(); i++) out[i] = pairs[i].key;
  return out;
}

// ips2ra full sort (BuRR's own sorter; resolves ledger caveat C19).
static std::vector<uint64_t> reorder_sort_ips2ra(const std::vector<uint64_t>& keys,
                                                 const Hasher& hasher, size_t num_starts) {
  auto pairs = make_pairs(keys, hasher, num_starts);
  ips2ra::sort(pairs.begin(), pairs.end(),
               [](const StartKey& p) { return p.start; });
  std::vector<uint64_t> out(keys.size());
  for (size_t i = 0; i < pairs.size(); i++) out[i] = pairs[i].key;
  return out;
}

// LSD radix sort by start, 3 x 10-bit passes (num_starts < 2^30 at all sizes used here).
// Weaker than BuRR's ips2ra — declared in the protocol; sort-implementation-independent
// conclusions come from the separately-reported banding phase.
static std::vector<uint64_t> reorder_sort_radix(const std::vector<uint64_t>& keys,
                                                const Hasher& hasher, size_t num_starts) {
  auto a = make_pairs(keys, hasher, num_starts);
  std::vector<StartKey> b(a.size());
  for (int pass = 0; pass < 3; pass++) {
    const int shift = pass * 10;
    size_t hist[1024 + 1] = {0};
    for (const auto& p : a) hist[((p.start >> shift) & 1023) + 1]++;
    for (int i = 1; i <= 1024; i++) hist[i] += hist[i - 1];
    for (const auto& p : a) b[hist[(p.start >> shift) & 1023]++] = p;
    std::swap(a, b);
  }
  std::vector<uint64_t> out(keys.size());
  for (size_t i = 0; i < a.size(); i++) out[i] = a[i].key;
  return out;
}

// ---- One measured run; B = Banding (reference kernel) or NoPrefetchBanding ----
template <typename B>
int run(const std::string& strategy, size_t n, int rep, size_t shift, unsigned threads) {
  // Sizing copied from HomogRibbonFilter (filterapi.h): w=64, 7 columns.
  const double overhead = 1.0 + (4.0 + kFractionalCols * 0.25) / (8.0 * sizeof(uint64_t));
  const size_t num_slots = InterleavedSoln::RoundUpNumSlots((size_t)(overhead * n));
  const size_t bytes = (size_t)((num_slots * kFractionalCols + 7) / 8);

  std::vector<uint64_t> keys = make_keys(n, UINT64_C(0xA11CE) + rep);
  Hasher hasher;

  B banding(num_slots);
  const size_t num_starts = banding.GetNumStarts();

  // Reorder phase (timed).
  double t0 = now_ns();
  std::vector<uint64_t> ordered;
  std::vector<size_t> wcounts;
  if (strategy == "partitioned" || strategy == "parallel") {
    ordered = reorder_partitioned(keys, hasher, num_starts, shift,
                                  strategy == "parallel" ? &wcounts : nullptr);
  } else if (strategy == "sort_std") {
    ordered = reorder_sort_std(keys, hasher, num_starts);
  } else if (strategy == "sort_radix") {
    ordered = reorder_sort_radix(keys, hasher, num_starts);
  } else if (strategy == "sort_ips2ra") {
    ordered = reorder_sort_ips2ra(keys, hasher, num_starts);
  }  // reference / noprefetch: no reorder
  const double reorder_ns = now_ns() - t0;
  const std::vector<uint64_t>& input = ordered.empty() ? keys : ordered;

  // Banding phase (timed; perf counters scoped to this phase only). The call below is
  // byte-for-byte what StandardBanding::AddRange does (ribbon_impl.h:589-596), made
  // explicit so UsePrefetch() resolves against B statically.
  std::vector<int> evts = {PERF_COUNT_HW_CPU_CYCLES, PERF_COUNT_HW_INSTRUCTIONS,
                           PERF_COUNT_HW_CACHE_MISSES};
  LinuxEvents<PERF_TYPE_HARDWARE> unified(evts);
  std::vector<unsigned long long> results(evts.size(), 0);
  size_t deferred_count = 0;
  bool ok = true;
  t0 = now_ns();
  unified.start();
  if (strategy == "parallel") {
    // Slot-range parallel banding (H-E1b-2p): thread t owns windows [w_lo, w_hi); keys whose
    // start lies within G slots of the range's upper slot boundary are deferred to a
    // sequential tail (parallel-BuRR-style boundary handling). Correctness is checked
    // end-to-end by the bit-identity fingerprint (order-independence) + false-negative gate.
    constexpr size_t G = size_t{1} << 14;
    const size_t n_windows = wcounts.size() - 1;
    // Split window ranges at ~equal key counts.
    std::vector<size_t> w_bounds(threads + 1, 0);
    w_bounds[threads] = n_windows;
    for (unsigned t = 1; t < threads; t++) {
      const size_t target = (input.size() * t) / threads;
      w_bounds[t] = std::lower_bound(wcounts.begin(), wcounts.end(), target) - wcounts.begin();
    }
    std::vector<std::vector<uint64_t>> deferred(threads);
    std::vector<std::thread> pool;
    for (unsigned t = 0; t < threads; t++) {
      pool.emplace_back([&, t]() {
        const size_t k_lo = wcounts[w_bounds[t]];
        const size_t k_hi = wcounts[w_bounds[t + 1]];
        const bool last = (t + 1 == threads);
        const size_t s_hi = w_bounds[t + 1] << shift;
        std::vector<uint64_t> mine;
        mine.reserve(k_hi - k_lo);
        for (size_t i = k_lo; i < k_hi; i++) {
          const uint64_t k = input[i];
          if (!last) {
            const size_t start = hasher.GetStart(hasher.GetHash(k), num_starts);
            if (start + G >= s_hi) {
              deferred[t].push_back(k);
              continue;
            }
          }
          mine.push_back(k);
        }
        ribbon::BandingAddRange(&banding, banding, mine.begin(), mine.end());
      });
    }
    for (auto& th : pool) th.join();
    for (auto& d : deferred) {
      deferred_count += d.size();
      ok = ok && ribbon::BandingAddRange(&banding, banding, d.begin(), d.end());
    }
  } else {
    ok = ribbon::BandingAddRange(&banding, banding, input.begin(), input.end());
  }
  unified.end(results);
  const double banding_ns = now_ns() - t0;

  if (!ok) {
    fprintf(stderr, "banding failed (must not happen for homogeneous ribbon)\n");
    return 1;
  }

  // Back-substitution phase (timed; reference code).
  std::unique_ptr<char[]> ptr(new char[bytes]);
  InterleavedSoln soln(ptr.get(), bytes);
  t0 = now_ns();
  soln.BackSubstFrom(banding);
  const double backsubst_ns = now_ns() - t0;

  // Solution fingerprint (FNV-1a): the smoke run showed identical FPR across orderings,
  // suggesting the banded solution is order-independent — if fingerprints match across
  // strategies, the correctness gate upgrades to full bit-identity.
  uint64_t fnv = UINT64_C(0xcbf29ce484222325);
  for (size_t i = 0; i < bytes; i++) {
    fnv = (fnv ^ (uint8_t)ptr[i]) * UINT64_C(0x100000001b3);
  }

  // Correctness gates: zero false negatives; FPR near 2^-7 (measured, reported).
  size_t fn = 0;
  for (uint64_t k : keys) fn += !soln.FilterQuery(k, hasher);
  const size_t n_probes = 2'000'000;
  size_t fp = 0;
  uint64_t s = UINT64_C(0xD15EA5E);
  for (size_t i = 0; i < n_probes; i++) {
    s += UINT64_C(0x9e3779b97f4a7c15);
    fp += soln.FilterQuery(mix64(s) ^ UINT64_C(0x5555555555555555), hasher);
  }

  printf(
      "{\"strategy\":\"%s\",\"n\":%zu,\"rep\":%d,\"num_slots\":%zu,"
      "\"reorder_ns_per_key\":%.3f,\"banding_ns_per_key\":%.3f,"
      "\"backsubst_ns_per_key\":%.3f,\"total_ns_per_key\":%.3f,"
      "\"banding_cycles_per_key\":%.2f,\"banding_instr_per_key\":%.2f,"
      "\"banding_miss_per_key\":%.3f,"
      "\"false_negatives\":%zu,\"fpr\":%.6f,\"bits_per_key\":%.3f,"
      "\"window_shift\":%zu,\"threads\":%u,\"deferred\":%zu,"
      "\"soln_fnv\":\"%016llx\"}\n",
      strategy.c_str(), n, rep, num_slots, reorder_ns / n, banding_ns / n,
      backsubst_ns / n, (reorder_ns + banding_ns + backsubst_ns) / n,
      (double)results[0] / n, (double)results[1] / n, (double)results[2] / n, fn,
      (double)fp / n_probes, bytes * 8.0 / n, shift, threads, deferred_count,
      (unsigned long long)fnv);
  return fn == 0 ? 0 : 1;
}

int main(int argc, char** argv) {
  if (argc < 4 || argc > 6) {
    fprintf(stderr, "usage: %s <n_keys> <strategy> <rep> [window_shift=16] [threads=8]\n",
            argv[0]);
    return 2;
  }
  const size_t n = strtoull(argv[1], nullptr, 10);
  const std::string strategy = argv[2];
  const int rep = atoi(argv[3]);
  const size_t shift = argc > 4 ? strtoull(argv[4], nullptr, 10) : kDefaultWindowShift;
  const unsigned threads = argc > 5 ? (unsigned)atoi(argv[5]) : 8;
  const bool known =
      strategy == "reference" || strategy == "noprefetch" || strategy == "sort_std" ||
      strategy == "sort_radix" || strategy == "sort_ips2ra" ||
      strategy == "partitioned" || strategy == "parallel";
  if (!known) {
    fprintf(stderr, "unknown strategy %s\n", strategy.c_str());
    return 2;
  }
  if (strategy == "noprefetch")
    return run<NoPrefetchBanding>(strategy, n, rep, shift, threads);
  return run<Banding>(strategy, n, rep, shift, threads);
}
