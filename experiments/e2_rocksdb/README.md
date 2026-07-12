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
    `banding.ResetAndFindSeedToSolve(...)`. Banding is order-independent (first-coefficient
    pivoting), so the finished filter is **bit-for-bit identical** to the arrival-order build — the
    change is construction speed only. Also `PLEAT_PROFILE`: scopes cache-miss/instruction hardware
    counters to exactly the banding call via `perf_event_open` self-monitoring (no sudo;
    `perf_event_paranoid <= 2`).
  - `util/ribbon_impl.h` — `PLEAT_NO_PREFETCH`: disables RocksDB's shipped construction prefetch
    (the `UsePrefetch()` heuristic behind its own `TODO: verify/validate` comment), so pleating can
    be measured against a no-prefetch baseline (both attack the same start-locating miss).
- **Machine:** Intel i9-14900HX (x86_64), the same box as the paper's e1b x86 data.

To apply and build:

```bash
cd ~/Code/hes/rocksdb              # v10.2.0, commit 31b239747
git apply /path/to/pleat-rocksdb.patch
make -j"$(nproc)" DEBUG_LEVEL=0 filter_bench db_bench
```

## Reproduce (filter_bench — construction microbenchmark)

`-impl 2` selects the Ribbon128 filter; "Build avg ns/key" is the reported construction cost.

```bash
# stock vs pleated across scale
for kpf in 100000 1000000 100000000; do
  ./filter_bench -impl 2 -m_keys_total_max $((kpf/1000000*3<40?40:kpf/1000000*3)) \
      -average_keys_per_filter $kpf -net_includes_hashing -quick
  PLEAT_RIBBON=1 ./filter_bench -impl 2 -m_keys_total_max ... (same) ...
done

# banding-phase hardware counters (why it is faster)
PLEAT_PROFILE=1              ./filter_bench -impl 2 ... -quick   # stock:   ~11.4 misses/key
PLEAT_RIBBON=1 PLEAT_PROFILE=1 ./filter_bench -impl 2 ... -quick # pleated: ~0.46 misses/key
```

Raw output is in `results/filter_bench.md`.

## Results (filter_bench, verified reproducible)

**Construction cost, ns/key** (`-quick`, `-net_includes_hashing`; FP rate identical stock vs pleated
to 6 digits at every size, confirming bit-identical filters):

| keys/filter | stock | pleated | speedup |
|---|---|---|---|
| 100,000 (banding table fits cache) | 52.3 | 54.4 | 0.96x (pleating slightly slower below crossover) |
| 1,000,000 | 62.8 | 54.4 | 1.15x |
| 100,000,000 (paper regime) | ~95.3 (95.8, 94.9) | ~53.8 (54.1, 53.6) | **1.77x** |

Pleated build cost is ~flat (~54 ns/key) across all sizes because banding stays cache-resident;
stock degrades (52 -> 63 -> 94) as the table outgrows cache.

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

## db_bench (end-to-end build-during-compaction)

See `results/db_bench.md`. Reported as an honest decomposition: filter-construction time is a
*fraction* of compaction wall-clock (which is dominated by merge + I/O), so the end-to-end delta is
diluted; we report filter-build savings, its share of compaction, and the net compaction effect
rather than a headline whole-system number.

## Integrity note

Every number here comes from a binary verified to contain the pleat code: the object file was
recompiled without error, the binary timestamp is newer than the source, and the `PLEAT_PROFILE`
marker string is confirmed embedded in the binary before measuring. (An earlier draft of this
experiment reported a spurious null because a compile error left `make` running a stale stock
binary; that is why the build is now gated.) FP-rate identity between stock and pleated is the
correctness gate — a different filter would show a different measured FP rate.
