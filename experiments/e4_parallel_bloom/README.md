# E4 — Bloom vs pleated ribbon construction at equal thread counts

**Status: protocol complete 2026-10-06, awaiting freeze (the author's commit). No data
collected.** Nothing in this directory is a result. No stage may be run for the record before
this file, `run.py`, `analyze.py`, the builders in `src/lanefilter/src/lib.rs` and
`src/lanefilter/benches/e4.rs` are committed.

## Question

The paper reports a 16-thread pleated-ribbon build (CLAIMS C23) and, separately, one-thread
Bloom builds. It has no Bloom build at the same thread count, so it cannot say how ribbon
compares with Bloom once both are parallel. Bloom insertion is order-free and trivially
parallel, so this comparison is expected to favour Bloom. E4 measures it.

## Arms (one machine, one session, 100M keys)

Thread counts T ∈ {1, 2, 4, 8, 16}.

- **Ribbon:** the existing E1b driver, unchanged (`src/ribbon_reorder/e1b_phase1`, pinned
  fastfilter_cpp kernel): `parallel` at each T, window shift 16, 3 repetitions; plus
  sequential `partitioned`, 3 repetitions. Reported cost is the driver's `total_ns_per_key`
  (reorder + banding + back-substitution; reorder and back-substitution are sequential, as in
  the paper). At T=1 the ribbon figure is the better of `parallel` at one thread and the
  sequential `partitioned` build, mirroring the Bloom rule below.
- **Bloom:** our SBBF prototype (`lanefilter`, Parquet split-block geometry, 10 bits/key), under
  Criterion (`benches/e4.rs`, 10 samples). Builders:
  - `perkey`, `perkey_prefetch` — the E1a sequential builders, unchanged.
  - `par_range` — each thread owns a block range; parallel count, scatter and apply passes;
    8 bytes/key transient.
  - `par_atomic` — threads take key chunks and OR into the shared filter with relaxed 64-bit
    atomic ORs behind a prefetch pipeline; no transient memory.
  - `par_scan` — each thread owns a block range, scans all keys and inserts only its own;
    no partition pass, no atomics, hashing repeated per thread.
  Timing includes allocation, page faults and thread spawn/join for every builder alike.
  **The Bloom figure at each T is the fastest of the builders at that T** (at T=1 the
  sequential builders are included), so the baseline is the strongest we can build, not the
  one we happened to write first.
- **Anchor (cross-validation):** fastfilter_cpp `BlockedBloom` (id 51), 100M keys, 3
  repetitions, seeds as E1b Phase 0.
- **Prototype quality:** `e0_fpr 100000000` records the prototype's measured FPR and bits/key
  at this size (it has so far been measured at 1M keys only).

## Why new benchmark code, and how it is validated

No pinned harness has a parallel Bloom build, so the three parallel builders are new code. Per
the framework-first policy:

- **Bit-identity gate.** OR is commutative, so every builder must produce the same bits as
  per-key insertion. Unit test `parallel_builders_bit_identical` (thread counts 1, 2, 3, 7, 8,
  16; three sizes) and a fingerprint check inside the bench, before timing, at the run size
  and every T. A mismatch aborts the bench.
- **Cross-validation on an overlapping configuration.** The prototype's sequential `perkey`
  build is compared with fastfilter_cpp `BlockedBloom` on the same box. If they differ by more
  than 25%, the analysis marks the Bloom numbers "cross-validation failed" and no ratio claim
  is made from them.
- **Ribbon gates (as E1b):** zero false negatives, and every parallel run's solution
  fingerprint equals the sequential `partitioned` fingerprint of the same repetition.

## Hypotheses (registered before data collection)

- **H-E4-1 (expected to hold):** at every T, pleated ribbon's total cost is more than 1.5× the
  best Bloom build at the same T.
- **H-E4-2 (claim gate, expected to FAIL):** at T=16, pleated ribbon's total cost is ≤ 1.25×
  the best Bloom build at T=16.

## Decision rule

- The paper reports, per T, the best Bloom cost (naming the builder), the ribbon total and
  their ratio, whatever they are.
- Any sentence comparing a multi-thread ribbon figure with Bloom must use the equal-thread
  ratio from this experiment. The existing README sentence that the 16-thread ribbon total is
  "about one thread's Bloom insertion time" must be accompanied by the T=16 ratio or removed.
- "Matches Bloom" wording for parallel construction is permitted only if H-E4-2 holds.
- **Kill criteria:** a failed bit-identity gate voids that builder's numbers; a failed ribbon
  gate voids the ribbon numbers; failed cross-validation voids all ratio claims. Voided
  numbers are still published in the analysis, marked as such.
- No builder is added, removed or retuned after data is seen. If a faster Bloom build is
  proposed later, it is a new registered run, not an edit to this one.

## Known limits, fixed in advance

- Not matched on false-positive rate or space: the prototype is 10 bits/key, the homogeneous
  ribbon about 7.6. E3 covers the matched-FPR comparison at one thread.
- Two harnesses (Criterion for Bloom, the C++ driver for ribbon), run back to back, not
  interleaved.
- The ribbon total keeps a sequential counting pass and back-substitution; the paper says so.
  This experiment measures the build as it exists, not an idealized parallel ribbon.
- 16 vCPUs on a cloud host are hardware threads of fewer physical cores. Topology is recorded;
  scaling statements apply to this machine only.

## Setup

- Machine: Hetzner CCX43 (16 dedicated x86 vCPUs, 64 GB), named `rcb-bench-e4`, labeled
  `project=ribbon-catches-bloom`. Not the i9-14900HX of C23; its numbers are labeled with this
  machine and not mixed with C23.
- Toolchain: rustc stable with `RUSTFLAGS=-C target-cpu=native`; g++ `-O3 -march=native` for
  the driver (the E1b Makefile); versions recorded in `machine.json`.

## Stages (each refuses to run before its prerequisite artifact exists)

1. `check` — `cargo test --release -p lanefilter` (the bit-identity gates), driver and
   fastfilter binaries present, driver smoke run; writes `results/e4/machine.json`,
   `check.json`.
2. `fpr` — `results/e4/fpr_100M.json`.
3. `anchor` — `results/e4/anchor/BlockedBloom_100000000_rep*.txt`.
4. `bloom` — Criterion, `E4_SIZES=full`; copies `new/*.json` to `results/e4/criterion/`.
5. `ribbon` — `results/e4/ribbon/{partitioned,parallel_t<T>}_rep*.json`.
6. `analyze` — `results/e4/ANALYSIS.md` and `paper/tables/e4_parallel.tex`.

`scripts/e4_remote.sh <host>` sets up the box, runs stages 1–5 there and pulls `results/e4/`
back; `analyze` runs locally.

The builders and bench were smoke-run at 1M keys on a laptop to confirm they run and pass the
gate; those timings were not recorded and are not results.

## Amendment 1 (2026-10-06, before any data was collected)

Hetzner refused the CCX43 in all three locations (`resource_limit_exceeded: dedicated core limit
exceeded`); the account's dedicated-core quota does not cover 16 cores. No server was created
and no stage was run. The machine is changed to an **AWS c7a.4xlarge** in us-east-1 (16 vCPUs
that are 16 physical cores, one thread per core, 32 GB), named `rcb-bench-e4`, tagged
`project=ribbon-catches-bloom`. Nothing else in the protocol changes: same arms, thread counts,
sizes, repetitions, gates, hypotheses and decision rule. One consequence, noted in advance: on
this instance type the 16 threads are separate physical cores, so the "hardware threads of
fewer physical cores" limit above does not apply to this run; the recorded topology is the
authority. `scripts/e4_remote.sh` gains `sudo` for a non-root login user; no benchmark code
changes.

