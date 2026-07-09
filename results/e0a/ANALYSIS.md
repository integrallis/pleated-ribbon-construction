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
| 32KiB_l1 | 665 Mops/s (1.50 ns/key) | 641 Mops/s (1.56 ns/key) | 553 Mops/s (1.81 ns/key) | 555 Mops/s (1.80 ns/key) | 74 Mops/s (13.44 ns/key) |
| 256KiB_l2 | 622 Mops/s (1.61 ns/key) | 639 Mops/s (1.57 ns/key) | 507 Mops/s (1.97 ns/key) | 558 Mops/s (1.79 ns/key) | 67 Mops/s (14.95 ns/key) |
| 4MiB_l3 | 452 Mops/s (2.21 ns/key) | 495 Mops/s (2.02 ns/key) | 432 Mops/s (2.31 ns/key) | 537 Mops/s (1.86 ns/key) | 48 Mops/s (20.89 ns/key) |
| 64MiB_ram | 89 Mops/s (11.26 ns/key) | 148 Mops/s (6.77 ns/key) | 105 Mops/s (9.56 ns/key) | 531 Mops/s (1.88 ns/key) | 13 Mops/s (74.72 ns/key) |
| 512MiB_ram | 78 Mops/s (12.75 ns/key) | 113 Mops/s (8.82 ns/key) | 90 Mops/s (11.11 ns/key) | 541 Mops/s (1.85 ns/key) | 12 Mops/s (85.36 ns/key) |

## Pre-registered decision rules

- 4MiB_l3: lanes/prefetch = 0.87×, hot-control/lanes = 1.24×
- 64MiB_ram: lanes/prefetch = 0.71×, hot-control/lanes = 5.08×
- 512MiB_ram: lanes/prefetch = 0.79×, hot-control/lanes = 6.01×

**Rule 2 met** at ['64MiB_ram', '512MiB_ram']: ≥3× compute headroom but lanes not winning → redesign probe before layout work.

## Auto-vectorization (raw: asm/): 138 packed-SIMD instruction lines in lanes kernel (vectorized)
