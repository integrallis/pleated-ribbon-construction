# E2 — Pleated construction in production RocksDB

Does pleating (partition-instead-of-sort) transfer from our standalone homogeneous-w=64 harness to
the **standard w=128 ribbon RocksDB actually ships** (`Standard128RibbonBitsBuilder`), in RocksDB's
own build path, with its own filter unchanged?

## Setup

- **RocksDB:** v10.2.0 (`ROCKSDB_MAJOR.MINOR.PATCH = 10.2.0`), upstream commit `31b239747`
  (`git describe`: `v9.11.1-46-g31b239747`). Checkout at `~/Code/hes/rocksdb`.
- **Patch:** `pleat-rocksdb.patch` (this directory). Two changes, both behind environment variables
  so a single binary runs stock or pleated:
  - `table/block_based/filter_policy.cc` — `PLEAT_RIBBON`: one counting pass reorders the collected
    key-hashes into ~L2-sized start-window order (shift 16) *before*
    `banding.ResetAndFindSeedToSolve(...)`. This changes key order while leaving the downstream
    builder unchanged. The checked-in E2 correctness evidence is RocksDB's test suite passing and
    measured false-positive rates matching stock to six digits; the benchmark artifacts do not
    include a byte-for-byte comparison of stock and pleated filter outputs. Also `PLEAT_PROFILE`:
    scopes cache-miss/instruction hardware counters to exactly the banding call via
    `perf_event_open` self-monitoring (no sudo; `perf_event_paranoid <= 2`).
  - `util/ribbon_impl.h` — `PLEAT_NO_PREFETCH`: disables RocksDB's shipped construction prefetch
    (the `UsePrefetch()` heuristic behind its own `TODO: verify/validate` comment), so pleating can
    be measured against a no-prefetch baseline (both attack the same start-locating miss).
- **Machine:** Intel i9-14900HX (x86_64), the same box as the paper's e1b x86 data.

To apply and build:

```bash
cd ~/Code/hes/rocksdb              # v10.2.0, commit 31b239747
git apply --check /path/to/pleated-ribbon-construction/experiments/e2_rocksdb/pleat-rocksdb.patch
git apply /path/to/pleated-ribbon-construction/experiments/e2_rocksdb/pleat-rocksdb.patch
make -j"$(nproc)" DEBUG_LEVEL=0 filter_bench db_bench
test table/block_based/filter_policy.o -nt table/block_based/filter_policy.cc
strings ./filter_bench | rg -F 'PLEAT_PROFILE banding'
```

The final two commands are measurement gates: confirm the patched object was rebuilt and the
instrumentation marker is present in the executable. Do not record a run if either check fails.

## Reproduce (filter_bench — construction microbenchmark)

`-impl 2` selects the Ribbon128 filter; "Build avg ns/key" is the reported construction cost.

```bash
# stock vs pleated across scale; three repetitions are recorded in the committed sweep
for kpf in 100000 1000000 3000000 10000000 30000000 100000000; do
  max_m=$((kpf / 1000000 * 3))
  if (( max_m < 40 )); then max_m=40; fi
  ./filter_bench -impl 2 -m_keys_total_max "$max_m" \
      -average_keys_per_filter "$kpf" -net_includes_hashing -quick
  PLEAT_RIBBON=1 ./filter_bench -impl 2 -m_keys_total_max "$max_m" \
      -average_keys_per_filter "$kpf" -net_includes_hashing -quick
done

# banding-phase hardware counters at 100M keys/filter
PLEAT_PROFILE=1 ./filter_bench -impl 2 -m_keys_total_max 300 \
    -average_keys_per_filter 100000000 -net_includes_hashing -quick
PLEAT_RIBBON=1 PLEAT_PROFILE=1 ./filter_bench -impl 2 -m_keys_total_max 300 \
    -average_keys_per_filter 100000000 -net_includes_hashing -quick
```

Raw output is in `results/filter_bench.md`.

## Results (filter_bench, 3 reps; the paper's Table 3 / Figure 4)

Raw per-rep data: `results/sweep_fb.csv` (6 sizes x 2 modes x 3 reps). Means below. The measured
false-positive rate matches stock to six digits at every size. This is the recorded FPR check; it
does not by itself establish byte-for-byte identity of the filter outputs.

**Total construction cost, ns/key** (`filter_bench` "Build avg ns/key", means of 3):

| keys/filter | stock | pleated | speedup |
|---|---|---|---|
| 100,000 (fits cache) | 57.6 | 59.4 | 0.97x (pleating slightly slower below crossover) |
| 1,000,000 | 55.9 | 54.4 | 1.03x (near crossover) |
| 10,000,000 | 88.7 | 54.7 | 1.62x |
| 100,000,000 (paper regime) | 97.4 | 54.8 | **1.78x** |

Pleated build cost is ~flat (~55 ns/key) across all sizes because banding stays cache-resident;
stock degrades (56 -> 89 -> 97) as the table outgrows cache. The banding phase alone (from the
`PLEAT_BUILD_TIME` accumulator) goes stock 80.0 -> pleated 31.8 ns/key at 100M (2.5x), the purest
measure of the effect.

**Banding-phase hardware counters at 100M keys/filter** (scoped to the banding call):

| | stock | pleated |
|---|---|---|
| cache-misses / key | 11.47, 11.42 | 0.46, 0.47 |
| instructions / key | 243 | 243 |

Pleating cuts banding cache-misses ~25x with **identical instruction count** — a pure
memory-locality effect, exactly the dependent-miss mechanism of the paper. (The standard w=128
kernel does ~243 instr/key vs ~98 for homogeneous w=64, which is why the *time* speedup is 1.77x
here vs 2.05x in the homogeneous harness: more compute per step dilutes the memory saving.)

The `PLEAT_NO_PREFETCH` control shows RocksDB's shipped construction prefetch is worth ~1.3x on the
unpleated build (stock ~95 vs no-prefetch ~122 at 20M/filter), and pleating subsumes it
(pleated-with-prefetch approximately equals pleated-without) — matching the paper's homogeneous
finding that partitioning mostly subsumes the prefetch.

## db_bench (end-to-end build-during-compaction, 3 reps)

Raw per-rep data: `results/dbbench_reps.csv`. Reported as an honest decomposition: filter-build is a
*fraction* of compaction (which is dominated by merge + I/O), so the end-to-end delta is diluted.
3-rep means: the filter-build speedup survives inside real compaction (banding 77.6+/-1.5 ->
44.2+/-6.1 ns/key, statistics-instrumented; ~2x uninstrumented); filter build is ~23% of compaction
CPU (1.83s of 7.9s); total compaction CPU falls ~9% (7.9+/-0.8 -> 7.2+/-0.4 s) **but that difference
is within run-to-run variance at n=3**, so it is directional, not tightly bounded. Write path
unaffected. `results/db_bench.md` has the earlier single-run detail and the integrity note.

## Integrity note

Every number here comes from a binary verified to contain the pleat code: the object file was
recompiled without error, the binary timestamp is newer than the source, and the `PLEAT_PROFILE`
marker string is confirmed embedded in the binary before measuring. (An earlier draft of this
experiment reported a spurious null because a compile error left `make` running a stale stock
binary; that is why the build is now gated.) FP-rate identity between stock and pleated is the
correctness gate — a different filter would show a different measured FP rate.
