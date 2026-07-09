# E1a — partitioned, register-transposed bulk construction of blocked Bloom filters

**Status: DRAFT protocol (2026-07-09). Not yet frozen. Freeze checklist before any data
collection: (1) prior-art audit returned and its findings incorporated below, (2) user commits
this file. No timing data exists for the new strategies at draft time.**

## Motivation (from measured artifacts + literature)

E0 killed probe-side layout work on OoO x86: probes are bound by memory-level parallelism, and
the compute is already optimal (results/e0a/ANALYSIS.md, CLAIMS C6–C7). Construction is the
surviving candidate because it is *reorderable*: the builder controls the order of bit-setting,
so random read-modify-writes can be converted into streaming writes. The cost is real and
already measured on this machine (CLAIMS C9, results/e0a/anchor/): fastfilter_cpp BlockedBloom
per-key construction degrades from 2.22 ns/key at 1M keys (0.07 misses/key) to 11.48 ns/key at
100M keys (0.96 misses/key, IPC 0.48) — i.e., bulk build at scale is one random RMW miss per
key. The literature names filter (re)construction cost as an open problem (ribbon = 3–4×
Bloom's build CPU; RocksDB gates ribbon adoption on it; every LSM compaction rebuilds filters).

## Hypotheses (pre-registered)

- **H1 (partitioning):** two-pass construction — (pass 1) radix-partition `(block_index, mask)`
  pairs so each partition's filter region fits in L2; (pass 2) per-partition, OR-merge each
  block's masks in registers and issue **exactly one store per filter block, never a read** —
  beats per-key insertion by ≥2× at ≥64MiB filter sizes.
  Derivation of the prediction (honest back-of-envelope, to be tested, not cited as result):
  per-key at scale ≈ 11.5 ns/key (measured anchor); partitioned traffic ≈ read keys 8B + write
  pairs ~12B + read pairs ~12B + write filter 1.33B ≈ ~33B/key of *streaming* traffic ≈
  2–4 ns/key at realistic single-core bandwidth → predicted 3–5× ceiling; H1 claims a
  conservative ≥2×.
- **H2 (transposed merge — the FastLanes-flavored part):** within pass 2, lane-structured
  mask-merging written as plain auto-vectorizable scalar code (process the partition's pairs in
  W-wide groups, accumulate per-block 8×u32 masks in SIMD registers) adds ≥1.2× over a plain
  scalar per-pair merge loop. If H1 holds but H2 fails, the honest paper is about partitioned
  construction (novelty then rests entirely on the prior-art audit), not about transposition.
- **H3 (portability):** the same scalar source achieves H1's win on ARM NEON (tf-bench-arm,
  when capacity allows) without code changes.

## Kill criteria (pre-registered)

- **K1:** if per-key insertion ≥ partitioned everywhere (OoO absorbs construction misses as it
  does probe misses), construction-side layout work dies too. The project's deliverable becomes
  the measurement study: "batching/layout tricks for filter operations are obsolete on modern
  OoO cores" (E0 + E1a nulls + cross-ISA), target DaMoN/experiments track.
- **K2:** if the prior-art audit finds the (partition → register-merge → single-store) scheme
  already published for in-memory filters, H1's novelty dies regardless of numbers; salvage
  paths: (a) ribbon/binary-fuse construction (their scatter is the expensive one), (b) the
  cross-ISA/ARM angle, (c) integration into an LSM compaction path with end-to-end numbers.
- **Correctness gate (before any timing is interpreted):** the partitioned builders must produce
  a filter **bit-identical** to per-key construction over the same key set (OR is commutative —
  any deviation is a bug), plus the E0 FPR gate re-applied.

## Fixed design

- Filter: same SBBF geometry as E0 (Parquet spec; 256-bit blocks, 8×u32, k=8, salts,
  fastrange block selection, splitmix64-mixed u64 keys). 10 bits/key.
- Key sets: deterministic KeyStream seeds as E0 (members 0xA11CE). Keys arrive UNSORTED
  (hash-random) — the honest hard case; LSM keys are sorted by key, which is hash-random per
  block, same thing after mixing.
- Sizes: n ∈ {1M, 10M, 53.7M, 100M, 429M} keys → filters ~1.25MB, 12.5MB, 64MB, 125MB, 512MB.
- Strategies:
  1. `perkey` — existing `BlockedFilter::insert` loop (E0 code, unchanged).
  2. `perkey_prefetch` — two-phase batched insert with prefetch (control: is MLP alone enough?).
  3. `partitioned` — two-pass radix scatter/merge, scalar merge loop.
  4. `partitioned_transposed` — as 3, with the lane-structured register-merge inner loop (H2).
  P (partition count) chosen so each partition's filter span ≤ 1MB (half of one P-core's L2);
  partition buffers use software write-combining (64B staging per partition).
- Metrics: ns/key (criterion, ≥20 samples), plus one `perf stat` run per (strategy × size) for
  cycles/key, misses/key, IPC when perf is available; peak RSS recorded (partitioning costs
  ~20B/key transient memory — report it, don't hide it).
- Anchors: fastfilter_cpp `BlockedBloom` (id 51, per-key add) and `BlockedBloom-addAll` (id 52)
  plus `Bloom8-addAll` (id 43) at the same n on the same machine, same session.
- Machines: local i9-14900HX (AVX2) first; tf-bench-arm (NEON) when available; x86 AVX-512
  deferred per user decision.

## Decision rules

- R1: H1 confirmed at ≥64MB sizes → construction direction alive; E1b = ribbon/binary-fuse
  construction becomes the next protocol.
- R2: H2 confirmed anywhere → the transposition angle specifically is alive; write-up leads
  with it. H2 refuted → drop the FastLanes framing from claims; keep partitioning if R1 held
  and prior-art audit allows.
- R3: K1 fires → pivot to measurement-study write-up (still a paper; nulls published).
- All rule evaluations are mechanical, in analyze.py, from raw artifacts (E0 house style).

## Stages

```bash
python run.py --stage check    # unit tests incl. bit-identity of all builders — no artifacts
python run.py --stage pilot    # 1M & 10M only, local; sanity + variance estimate (NOT citable)
python run.py --stage bench    # full sweep (refuses to run before check+pilot artifacts exist)
python run.py --stage perf     # perf-stat pass (optional; degrades gracefully without perf)
python run.py --stage anchor   # fastfilter_cpp ids 43,51,52 at matching n
python run.py --stage analyze  # derives results/e1a/ANALYSIS.md; evaluates R1-R3
```

## Threats to validity (declared up front)

- Partitioning needs ~20B/key transient buffer — a real memory cost per-key insertion doesn't
  pay; reported alongside every throughput claim.
- Single-threaded first: multicore construction shifts the bandwidth/MSHR math; a follow-up
  protocol, not a silent extension of this one.
- CAX (ARM) is shared-vCPU: report CIs and repeats; label accordingly.
- The 429M point exceeds the 100M anchor's largest n; anchor comparisons stop at 100M.
- fastbloom is excluded here: its insert path hashes internally (asymmetry documented in E0);
  construction comparisons use our own strategies + fastfilter_cpp anchors only.
