# E6 — Peak memory, concurrent builds, and the parallel boundary fallback

**Status: protocol complete 2026-10-07, awaiting freeze. No data collected.** Nothing in this
directory is a result.

## Why

Two items from the manuscript review are still open in the paper:

- **Boundary safety (item 5).** The parallel build relies on a hard cap with a fallback: a
  reduction that would reach a thread's upper boundary is handed to the sequential tail. In every
  recorded run so far the count of such crossings is zero, so the fallback has never been
  exercised under measurement.
- **Time and memory together (item 6).** The paper states the transient memory of the partition
  pass from the code (8 bytes per key in the driver, 12 in the RocksDB patch) and says peak
  resident memory was not measured. The effect of several builders running at once, which is how
  compaction uses filters, is also unmeasured.

## Arms (one machine, one session; 100M keys; existing code only, no new benchmark code)

All stages use the unmodified driver `src/ribbon_reorder/e1b_phase1` at window shift 16 and, for
RocksDB, the E2-patched `filter_bench` at the E2 pin.

- **Stage `spill` — exercising the fallback.** `parallel` at T ∈ {2, 16} with the boundary margin
  set by the driver's existing `PLEAT_PARALLEL_G` override to 16384 (the default), 1024, 64, 8
  and 0 slots; 3 repetitions each, plus the sequential `partitioned` build of each repetition.
  Recorded: `spilled`, `deferred`, `false_negatives`, `soln_fnv`.
- **Stage `memory` — peak resident memory.** GNU `time -v` "Maximum resident set size" for the
  driver strategies `reference`, `sort_radix`, `sort_ips2ra`, `partitioned` and `parallel`
  (T=16), 3 repetitions each; and for `filter_bench -impl 2` at 100M keys per filter, stock and
  pleated, 3 repetitions each (flags as E2).
- **Stage `concurrent` — several builders at once.** K ∈ {1, 4, 8} simultaneous driver
  processes, each pinned to its own core with `taskset`, all running `reference` or all running
  `partitioned` (sequential), 3 repetitions. Recorded: each process's `total_ns_per_key`.

## Hypotheses (registered before data collection)

- **H-E6-1:** for every margin and thread count, including settings where `spilled` > 0, every
  parallel run has zero false negatives and the same solution fingerprint as the sequential
  build of the same repetition. If no setting produces `spilled` > 0, the stage is reported as
  "fallback not exercised" and the paper says so.
- **H-E6-2:** the driver's peak resident memory for `partitioned` exceeds `reference` by
  8 bytes per key, within ±25% (6 to 10 bytes per key).
- **H-E6-3:** with 4 and with 8 concurrent builders, `partitioned` remains at least 1.5× faster
  per process than `reference`.

## Decision rule

- The paper replaces "did not measure peak resident memory" with the measured peaks and deltas,
  whatever they are. If H-E6-2 fails, the code-derived figure in the paper is replaced by the
  measurement and the difference is explained or reported as unexplained.
- The RocksDB delta is descriptive (no threshold): `filter_bench` holds its filters and varies
  keys per filter, so the paper reports the measured peak for stock and pleated and their
  difference in MB.
- If H-E6-1 fails at any setting, the parallel build's correctness claim is withdrawn from the
  paper until explained. If it holds with `spilled` > 0 somewhere, the paper may say the
  fallback was exercised and preserved the output, naming the settings.
- If H-E6-3 fails, the paper reports the measured ratios and says the advantage shrinks under
  concurrent builds.
- No margin, strategy or K is added or dropped after data is seen.

## Known limits, fixed in advance

- Peak resident memory is for the whole process, including the 100M input keys and the
  verification pass; only differences between strategies are attributed to the pass.
- Concurrent builders are separate processes with separate inputs in memory, not threads of one
  storage engine; they share memory bandwidth and the last-level cache, which is the effect of
  interest.
- One machine; timing here is not comparable with the i9 results and is not mixed with them.

## Setup

- Machine: AWS c7a.4xlarge in us-east-1 (AMD EPYC 9R14, 16 physical cores, one thread per core,
  32 GB), named `rcb-bench-e6`, tagged `project=pleated-ribbon-construction`. Recorded in
  `machine.json`.
- Toolchain as E4 for the driver; RocksDB v10.2.0 at `31b239747` with the E2 patch, built as E3.

## Stages (each refuses to run before its prerequisite artifact exists)

1. `check` — driver smoke run, GNU `time` present, at least 16 CPUs, RocksDB build gates (E3's
   check); writes `results/e6/machine.json`, `check.json`.
2. `spill` — `results/e6/spill/*.json`.
3. `memory` — `results/e6/memory/*.json` (driver) and `results/e6/memory/fb_*.txt` (RocksDB).
4. `concurrent` — `results/e6/concurrent/*.json`.
5. `analyze` — `results/e6/ANALYSIS.md` and `paper/tables/e6.tex`.

`scripts/e6_remote.sh <host>` sets up the box, runs stages 1–4 and pulls `results/e6/` back.
The runner and analysis have been syntax-checked only; nothing has been run.
