generated-by: experiments/e0_feasibility/analyze.py over results/e0a/ artifacts (bench machine: , rustc 1.98.1 (48a229cea 2026-09-01), RUSTFLAGS=-C target-cpu=native)

# E0 analysis (derived — do not hand-edit)

## FPR gate (raw: summary.json)

| filter | bits/key | measured FPR |
|---|---|---|
| lanefilter_sbbf | 10.00 | 1.2660% |
| fastbloom_0.9 | 10.00 | 0.8367% |

FPR gate (pre-registered [0.5%, 2%]): PASS

## Batch-miss probe throughput (raw: criterion/, mean over 30 samples, batch = 8192 keys)

| size | scalar | prefetch | lanes | lanes_hot_CONTROL | fastbloom_perkey |
|---|---|---|---|---|---|
| 32KiB_l1 | 470 Mops/s (2.13 ns/key) | 351 Mops/s (2.85 ns/key) | 279 Mops/s (3.59 ns/key) | 279 Mops/s (3.59 ns/key) | 58 Mops/s (17.35 ns/key) |
| 256KiB_l2 | 428 Mops/s (2.34 ns/key) | 279 Mops/s (3.59 ns/key) | 264 Mops/s (3.79 ns/key) | 279 Mops/s (3.59 ns/key) | 52 Mops/s (19.34 ns/key) |
| 4MiB_l3 | 229 Mops/s (4.37 ns/key) | 207 Mops/s (4.83 ns/key) | 192 Mops/s (5.22 ns/key) | 279 Mops/s (3.59 ns/key) | 34 Mops/s (29.51 ns/key) |
| 64MiB_ram | 67 Mops/s (14.93 ns/key) | 62 Mops/s (16.17 ns/key) | 54 Mops/s (18.42 ns/key) | 279 Mops/s (3.59 ns/key) | 11 Mops/s (94.74 ns/key) |
| 512MiB_ram | 60 Mops/s (16.56 ns/key) | 56 Mops/s (17.81 ns/key) | 48 Mops/s (20.65 ns/key) | 279 Mops/s (3.59 ns/key) | 9 Mops/s (107.72 ns/key) |

## Pre-registered decision rules

- 4MiB_l3: lanes/prefetch = 0.93×, hot-control/lanes = 1.46×
- 64MiB_ram: lanes/prefetch = 0.88×, hot-control/lanes = 5.14×
- 512MiB_ram: lanes/prefetch = 0.86×, hot-control/lanes = 5.76×

**Rule 2 met** at ['64MiB_ram', '512MiB_ram']: ≥3× compute headroom but lanes not winning → redesign probe before layout work.

## Auto-vectorization (raw: asm/): 233 packed-SIMD instruction lines in lanes kernel (vectorized)
