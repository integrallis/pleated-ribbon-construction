// Direct check on the PINNED, UNMODIFIED fastfilter_cpp ribbon kernel (924e560): does the
// solved filter depend on insertion order when redundant rows are present?
// Homogeneous: deliberately under-provisioned so many rows reduce to zero and are dropped.
// Standard (non-homogeneous): a build that succeeds, tried under shuffled orders.
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <memory>
#include <random>
#include <vector>
#include "ribbon_impl.h"

template <bool kHomog>
struct TS_ {
  static constexpr bool kIsFilter = true;
  static constexpr bool kHomogeneous = kHomog;
  static constexpr bool kFirstCoeffAlwaysOne = true;
  static constexpr bool kUseSmash = false;
  using CoeffRow = uint64_t;
  using Hash = uint64_t;
  using Key = uint64_t;
  using Seed = uint32_t;
  using Index = size_t;
  using ResultRow = uint32_t;
  static constexpr bool kAllowZeroStarts = false;
  static constexpr uint32_t kFixedNumColumns = 7;
  static Hash HashFn(const Hash& input, Seed raw_seed) {
    uint64_t h = input + raw_seed;
    h ^= h >> 33; h *= UINT64_C(0xff51afd7ed558ccd);
    h ^= h >> 33; h *= UINT64_C(0xc4ceb9fe1a85ec53);
    h ^= h >> 33;
    return h;
  }
};

static uint64_t fnv(const char* p, size_t n) {
  uint64_t h = UINT64_C(0xcbf29ce484222325);
  for (size_t i = 0; i < n; i++) h = (h ^ (uint8_t)p[i]) * UINT64_C(0x100000001b3);
  return h;
}

template <bool kHomog>
int run(const char* label, size_t n, double slots_per_key, int orders, uint64_t seed) {
  using TS = TS_<kHomog>;
  IMPORT_RIBBON_IMPL_TYPES(TS);
  std::mt19937_64 rng(seed);
  std::vector<uint64_t> keys(n);
  for (auto& k : keys) k = rng();
  const size_t num_slots = InterleavedSoln::RoundUpNumSlots((size_t)(slots_per_key * n));
  const size_t bytes = (size_t)((num_slots * 7.0 + 7) / 8);
  uint64_t ref = 0; size_t occ0 = 0; int same = 0, built = 0, failed = 0;
  for (int o = 0; o < orders; o++) {
    if (o > 0) std::shuffle(keys.begin(), keys.end(), rng);
    Hasher hasher;
    Banding banding(num_slots);
    bool ok = ribbon::BandingAddRange(&banding, banding, keys.begin(), keys.end());
    if (!ok) { failed++; continue; }
    built++;
    std::unique_ptr<char[]> ptr(new char[bytes]);
    InterleavedSoln soln(ptr.get(), bytes);
    soln.BackSubstFrom(banding);
    size_t fn = 0;
    for (uint64_t k : keys) fn += !soln.FilterQuery(k, hasher);
    if (fn) { printf("%s: FALSE NEGATIVES %zu\n", label, fn); return 1; }
    uint64_t f = fnv(ptr.get(), bytes);
    size_t occ = banding.GetOccupiedCount();
    if (built == 1) { ref = f; occ0 = occ; same = 1; }
    else { same += (f == ref); if (occ != occ0) printf("%s: occupied count changed!\n", label); }
  }
  printf("%-34s n=%zu slots=%zu occupied=%zu dropped(redundant)=%zu orders=%d built=%d failed=%d "
         "identical_to_first=%d\n", label, n, num_slots, occ0, built ? n - occ0 : 0, orders, built,
         failed, same);
  return 0;
}

int main() {
  // homogeneous, generously sized: few or no redundant rows
  run<true>("homog, 1.10 slots/key", 200000, 1.10, 25, 1);
  // homogeneous, under-provisioned: many redundant rows dropped
  run<true>("homog, 1.00 slots/key", 200000, 1.00, 25, 2);
  run<true>("homog, 0.90 slots/key (overloaded)", 200000, 0.90, 25, 3);
  run<true>("homog, 0.50 slots/key (overloaded)", 50000, 0.50, 25, 4);
  // standard ribbon: either every order succeeds (consistent) or every order fails
  run<false>("standard, 1.10 slots/key", 200000, 1.10, 25, 5);
  run<false>("standard, 1.05 slots/key", 200000, 1.05, 25, 6);
  run<false>("standard, 1.00 slots/key", 200000, 1.00, 25, 7);
  return 0;
}
