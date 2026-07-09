# E0 — feasibility: does vertical (lane-structured) batch probing have headroom at all?

**Status: protocol frozen before data collection (2026-07-09). No results existed when this
file was written.**

## Questions (pre-registered)

- **E0a (auto-vectorization).** Does `check_batch_lanes` — a vertical batch probe written as
  plain scalar Rust over an SBBF-geometry filter — compile to packed SIMD on AVX2
  (`-C target-cpu=native`)? Verified by disassembly, committed as an artifact. And does it beat
  per-key probing (`scalar`) and two-phase prefetch probing (`prefetch`) on batch-miss
  throughput?
- **E0b (memory vs compute).** Across filter sizes 32KiB → 512MiB, how does the gap between
  `lanes` (full-range addresses) and `lanes_hot_CONTROL` (identical instruction stream, all
  addresses forced into one L1-resident block) evolve? The control is NOT a filter — its results
  are wrong by construction; it exists solely to bound what the same code would do if memory
  were free.

## Fixed design

SBBF geometry (Parquet spec, arXiv:2101.01719): 256-bit blocks, 8×u32 words, k=8, per-word salts,
fastrange block selection, splitmix64-finalizer key mixing. 10 bits/key. Probe batch = 8192
absent keys (miss-dominated ≈ LSM point-lookup). Deterministic seeds (members 0xA11CE, probes
0xD15EA5E⊕0x5555…). Criterion.rs, 30 samples. Machine: i9-14900HX (AVX2, no AVX-512), Linux,
rustc 1.94.1. External anchors: `fastbloom` 0.9 per-key API (its number includes its own
hashing — noted asymmetry), and fastfilter_cpp `BlockedBloom` run separately on the same machine
as the cross-validation anchor.

## Decision rules (pre-registered)

1. If `lanes` beats `prefetch` by ≥1.3× at ≥ one realistic size (≥4MiB) → E0a supports the
   direction; proceed to designing an actual transposed layout (E1).
2. If `lanes` ≤ `prefetch` everywhere but `lanes_hot_CONTROL` shows ≥3× headroom at ≥4MiB →
   compute is not the bottleneck as written, but vectorization headroom exists; redesign the
   probe (e.g., software-pipelined gathers) before any layout work.
3. **Kill criterion:** if at realistic sizes (≥4MiB) `lanes_hot_CONTROL` ≈ `lanes` ≈ `prefetch`
   (within ~1.15×), probing is memory-latency-bound and no layout transposition can matter for
   miss-dominated point probes. The direction (RQ2 for point probes) dies; write up the negative
   result and pivot (bulk construction and/or sorted-probe compaction workloads become the only
   candidate wins).
4. FPR gate: measured FPR of our SBBF must land in [0.5%, 2%] at ~10.7 bits/key and must not
   beat information bounds (integrity check); otherwise fix the filter before interpreting any
   timing.

## Amendments

- **Amendment 1 (2026-07-09, before run-2 data collection):** run 1's probe set was a fixed 8192
  keys reused every criterion iteration; at RAM-scale sizes the probed lines stayed cached, so
  those rows measured a warm 512KiB working set (caught by the fastfilter_cpp anchor: 7×
  cross-harness discrepancy). Fix: 4M-key probe pool, each iteration advances one 8192-key
  window. Decision rules unchanged. Run-1 artifacts: `results/e0a_run1_superseded/` (citable for
  nothing except the auto-vectorization asm finding and, pending run-2 confirmation, the
  cache-resident rows).

## Stages

```bash
python run.py --stage check   # cargo tests (FPR/agreement guards) — no artifacts
python run.py --stage fpr     # writes results/e0a/summary.json (raw FPR artifact)
python run.py --stage bench   # criterion run → copies raw JSON into results/e0a/criterion/
python run.py --stage asm     # disassembles the lanes kernel → results/e0a/asm/
python run.py --stage anchor  # fastfilter_cpp BlockedBloom on same machine → results/e0a/anchor/
python run.py --stage analyze # derives results/e0a/ANALYSIS.md from artifacts only
```

Each stage refuses to run if its prerequisite artifact is missing. `analyze` reads only
committed artifacts; it never launches a benchmark.
