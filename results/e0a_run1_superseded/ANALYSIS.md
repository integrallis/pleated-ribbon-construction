generated-by: experiments/e0_feasibility/analyze.py over results/e0a/ artifacts (bench machine: Intel(R) Core(TM) i9-14900HX, rustc 1.94.1 (e408947bf 2026-03-25), RUSTFLAGS=-C target-cpu=native)

# E0 analysis (derived — do not hand-edit)

## FPR gate (raw: summary.json)

| filter | bits/key | measured FPR |
|---|---|---|
| lanefilter_sbbf | 10.00 | 1.2660% |
| fastbloom_0.9 | 10.00 | 0.8462% |

FPR gate (pre-registered [0.5%, 2%]): PASS

## Batch-miss probe throughput (raw: criterion/, mean over 30 samples, batch = 8192 keys)

| size | scalar | prefetch | lanes | lanes_hot_CONTROL | fastbloom_perkey |
|---|---|---|---|---|---|
| 32KiB_l1 | 661 Mops/s (1.51 ns/key) | 663 Mops/s (1.51 ns/key) | 576 Mops/s (1.74 ns/key) | 575 Mops/s (1.74 ns/key) | 95 Mops/s (10.55 ns/key) |
| 256KiB_l2 | 641 Mops/s (1.56 ns/key) | 677 Mops/s (1.48 ns/key) | 533 Mops/s (1.88 ns/key) | 564 Mops/s (1.77 ns/key) | 88 Mops/s (11.33 ns/key) |
| 4MiB_l3 | 578 Mops/s (1.73 ns/key) | 659 Mops/s (1.52 ns/key) | 476 Mops/s (2.10 ns/key) | 540 Mops/s (1.85 ns/key) | 77 Mops/s (13.02 ns/key) |
| 64MiB_ram | 525 Mops/s (1.91 ns/key) | 443 Mops/s (2.26 ns/key) | 432 Mops/s (2.31 ns/key) | 559 Mops/s (1.79 ns/key) | 58 Mops/s (17.16 ns/key) |
| 512MiB_ram | 470 Mops/s (2.13 ns/key) | 362 Mops/s (2.77 ns/key) | 398 Mops/s (2.51 ns/key) | 577 Mops/s (1.73 ns/key) | 49 Mops/s (20.49 ns/key) |

## Pre-registered decision rules

- 4MiB_l3: lanes/prefetch = 0.72×, hot-control/lanes = 1.13×
- 64MiB_ram: lanes/prefetch = 0.98×, hot-control/lanes = 1.29×
- 512MiB_ram: lanes/prefetch = 1.10×, hot-control/lanes = 1.45×

**No pre-registered rule fired cleanly** — intermediate regime; log interpretation in RESEARCH_LOG.md before any next step.

## Auto-vectorization (raw: asm/): 138 packed-SIMD instruction lines in lanes kernel (vectorized)
