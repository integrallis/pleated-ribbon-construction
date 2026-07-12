# db_bench end-to-end (RocksDB v10.2.0, i9-14900HX)

Does pleating's filter-build speedup show up during **real compaction**, and how large is it relative
to total compaction cost? Reported as an honest decomposition, not a headline whole-database number.

## Workload

`fillrandom` 30M keys, **8-byte values** (small values → filter-build is a meaningful share of
compaction; a deliberately filter-favorable, labelled config), 16-byte keys, Ribbon filter
(`--use_ribbon_filter=1 --bloom_bits=10` → `NewRibbonFilterPolicy(10)`: Bloom at flush, Ribbon on
compacted levels), no compression, 128 MB memtable, **256 MB target SST** (→ ~8–9M keys per ribbon
filter), WAL off, single thread, then `waitforcompaction`. Stock vs pleated = same binary,
`PLEAT_RIBBON` toggled. Filter-build time measured directly via the `PLEAT_BUILD_TIME` banding-wall
accumulator (chrono only, scoped to `ResetAndFindSeedToSolve`). Raw logs: `db_bench_*.raw.log`.

## Filter-build (banding) speedup — the robust result

Across the workload, RocksDB built ~23.5M keys' worth of ribbon filters during compaction
(near-identical key totals stock vs pleated → directly comparable):

| run | stock banding | pleated banding | speedup |
|---|---|---|---|
| clean (no statistics overhead) | 1695.8 ms (72.0 ns/key) | 835.5 ms (35.5 ns/key) | **2.03x** |
| with `statistics=1 stats_level=4` | 2031.8 ms (86.3 ns/key) | 1315.2 ms (55.9 ns/key) | 1.54x* |

*The statistics-instrumented run adds a roughly constant per-key overhead that dilutes the ratio; the
clean run is the truer filter-build cost. The 2.03x matches the isolated `filter_bench` measurement at
the same ~8M keys/filter operating point (72.5 → 34.6 ns/key), so the two harnesses agree.

## Decomposition (statistics run, self-consistent)

- Filter construction (banding) is **~30% of compaction CPU** in this filter-heavy config
  (2.03 s banding / 6.82 s total compaction CPU).
- Pleating cuts filter-build ~2x, saving ~0.7 s, which lowers **compaction CPU by ~4.6%**
  (6.82 s → 6.50 s) and compaction wall by ~4.1% (6.97 s → 6.69 s).
- The **write path is unaffected**: `fillrandom` was 41.5 s (stock) vs 42.6 s (pleated) — filters are
  built in background compaction, so whole-workload wall-clock is write-dominated and barely moves.
  The value is **reclaimed compaction CPU**, not user-visible write latency, in this workload.

## Honest reading

The solid, cross-validated result is the **~2x filter-build speedup during real compaction**
(reproduced in both `filter_bench` and `db_bench`, mechanism confirmed by hardware counters: ~25x
fewer banding cache-misses, identical instruction count). Its end-to-end footprint is a **~5% cut in
compaction CPU** *in a filter-favorable config* (small values, large SSTs). On a values-heavy
workload with default 64 MB SSTs, filters are a smaller share and per-SST filters sit nearer the
pleating crossover, so the end-to-end effect shrinks — pleating's benefit grows with per-SST filter
size. The compaction-CPU percentage is from a single run over nondeterministic compaction (2
compaction events; coarse histogram); the filter-build speedup is the robust, repeatable claim.
Multiple reps and a per-SST-size sweep are the natural follow-ups before using the end-to-end
percentage in the paper.

## Integrity note

Two extraction mistakes were made and corrected while producing this file: (1) an initial run was
piped through `tail -60`, discarding the summary lines; (2) a cumulative accumulator's per-mode
totals were briefly misattributed (read as stock=35.5/pleated=35.5, a false null), then corrected
against the raw per-filter increments to stock=72.0/pleated=35.5. The underlying measurements were
never wrong — only their reading — and the fix was to parse full per-mode logs by explicit markers
rather than positional `tail`. Numbers here are recomputed from the committed raw logs.
