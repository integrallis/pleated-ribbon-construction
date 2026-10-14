generated-by: experiments/e7_rigour/analyze.py over results/e7/arm-graviton4/raw/ (machine: Neoverse-V2 / AWS Graviton4 N/A CPU @ 2.8GHz, aarch64, kernel 7.0.0-1014-aws, virt: none, profile: replication, source a6ad7dea19ee47112b2ac533ef328b6ac2bb09e6)

# E7 analysis, arm-graviton4 (derived; do not hand-edit)

Pinned CPU 2 (siblings 2), governor None, intel no_turbo None, boost None, SMT active 0, THP always [madvise] never, g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0.

Cells are median (minimum–maximum) over the repetitions; ratios are ratios of medians with a 95% bootstrap interval.

## Cross-check of e7_driver against e1b_phase1

| keys | strategy | fingerprints equal | median total e1b_phase1 | median total e7_driver | ratio | tolerance |
|---|---|---|---|---|---|---|
| 10,000,000 | reference | yes | 65.37 | 63.99 | 0.979 | ±5% |
| 10,000,000 | sort_ips2ra | yes | 48.81 | 48.64 | 0.996 | ±10% |
| 10,000,000 | partitioned | yes | 35.35 | 34.90 | 0.987 | ±5% |
| 100,000,000 | reference | yes | 77.72 | 77.45 | 0.997 | ±5% |
| 100,000,000 | sort_ips2ra | yes | 50.88 | 50.64 | 0.995 | ±10% |
| 100,000,000 | partitioned | yes | 35.53 | 35.14 | 0.989 | ±5% |

Cross-check passed.

## Construction by key count and strategy (ns/key)

| keys | strategy | reps | reorder | banding | back-substitution | total |
|---|---|---|---|---|---|---|
| 10,000,000 | noprefetch | 10 | 0.0 (0.0–0.0) | 68.7 (66.9–69.6) | 7.8 (7.8–7.9) | 76.5 (74.8–77.4) |
| 10,000,000 | partitioned | 10 | 6.2 (6.1–6.2) | 21.3 (21.2–21.4) | 7.8 (7.8–7.8) | 35.3 (35.2–35.4) |
| 10,000,000 | reference | 10 | 0.0 (0.0–0.0) | 57.7 (56.1–58.7) | 7.8 (7.8–7.8) | 65.6 (64.0–66.5) |
| 10,000,000 | sort_ips2ra | 10 | 24.3 (24.3–24.5) | 16.7 (16.6–16.7) | 7.8 (7.8–7.8) | 48.8 (48.7–48.9) |
| 10,000,000 | sort_radix | 10 | 21.2 (21.1–21.3) | 16.6 (16.5–16.7) | 7.8 (7.8–7.8) | 45.6 (45.5–45.7) |
| 10,000,000 | sort_std | 10 | 65.7 (64.9–66.2) | 16.7 (16.6–16.7) | 7.8 (7.8–7.8) | 90.1 (89.4–90.7) |
| 100,000,000 | noprefetch | 10 | 0.0 (0.0–0.0) | 89.1 (88.2–90.5) | 7.8 (7.8–7.8) | 96.9 (96.0–98.3) |
| 100,000,000 | partitioned | 10 | 6.4 (6.4–6.4) | 21.3 (21.2–21.3) | 7.8 (7.8–7.8) | 35.5 (35.4–35.6) |
| 100,000,000 | reference | 10 | 0.0 (0.0–0.0) | 69.1 (68.1–70.0) | 7.8 (7.8–7.8) | 76.9 (76.0–77.8) |
| 100,000,000 | sort_ips2ra | 10 | 26.4 (26.3–26.5) | 16.7 (16.6–16.7) | 7.8 (7.8–7.8) | 50.9 (50.8–51.0) |
| 100,000,000 | sort_radix | 10 | 21.2 (21.2–21.2) | 16.7 (16.5–16.7) | 7.8 (7.8–7.8) | 45.7 (45.6–45.8) |
| 100,000,000 | sort_std | 10 | 73.3 (72.8–73.8) | 16.7 (16.6–16.7) | 7.8 (7.8–7.8) | 97.8 (97.3–98.3) |
| 400,000,000 | noprefetch | 10 | 0.0 (0.0–0.0) | 92.2 (88.0–94.8) | 7.8 (7.8–7.8) | 100.0 (95.9–102.7) |
| 400,000,000 | partitioned | 10 | 7.3 (7.3–7.3) | 21.2 (21.2–21.3) | 7.8 (7.8–7.8) | 36.3 (36.3–36.4) |
| 400,000,000 | reference | 10 | 0.0 (0.0–0.0) | 74.6 (72.4–75.6) | 7.8 (7.8–7.8) | 82.4 (80.2–83.4) |
| 400,000,000 | sort_ips2ra | 10 | 26.3 (26.3–26.3) | 16.7 (16.6–16.7) | 7.8 (7.8–7.8) | 50.8 (50.7–50.9) |
| 400,000,000 | sort_radix | 10 | 22.8 (22.8–22.9) | 16.7 (16.6–16.7) | 7.8 (7.8–7.8) | 47.3 (47.2–47.3) |
| 400,000,000 | sort_std | 10 | 78.0 (77.7–78.6) | 16.7 (16.7–16.7) | 7.8 (7.8–7.8) | 102.5 (102.2–103.1) |

| keys | reference / partitioned | best full sort | best sort / partitioned |
|---|---|---|---|
| 10,000,000 | 1.86× [1.84, 1.87] | sort_radix | 1.29× [1.29, 1.30] |
| 100,000,000 | 2.17× [2.15, 2.18] | sort_radix | 1.29× [1.29, 1.29] |
| 400,000,000 | 2.27× [2.25, 2.28] | sort_radix | 1.30× [1.30, 1.30] |

## Parallel build, 100M keys (ns/key)

| threads | reps | banding | total | banding vs its own 1 thread | banding vs sequential partitioned | deferred keys |
|---|---|---|---|---|---|---|
| 1 | 10 | 25.7 (25.7–25.7) | 39.9 (39.9–40.0) | 1.00× [1.00, 1.00] | 0.83× [0.83, 0.83] | 0.0000% |
| 2 | 10 | 14.3 (13.1–16.9) | 28.5 (27.4–31.2) | 1.80× [1.71, 1.95] | 1.49× [1.42, 1.62] | 0.0150% |
| 4 | 10 | 7.5 (6.7–9.9) | 21.7 (21.0–24.1) | 3.42× [2.96, 3.80] | 2.84× [2.45, 3.15] | 0.0451% |
| 8 | 10 | 4.6 (3.6–5.0) | 18.8 (17.8–19.2) | 5.58× [5.17, 7.16] | 4.62× [4.28, 5.93] | 0.1052% |
| 16 | 10 | 2.0 (2.0–2.5) | 16.3 (16.2–16.8) | 12.76× [10.21, 12.78] | 10.57× [8.46, 10.59] | 0.2252% |

Sequential partitioned banding: 21.3 (21.2–21.3) ns/key.

## Counters scoped to banding, per key

Events resolved on this machine: `l2d_cache_lmiss_rd` = 0x4009, `ll_cache_miss_rd` = 0x0037, `dtlb_walk` = 0x0034.

| keys | event | reference | LSD radix | ips2ra | partitioned | recovery of the best sort's reduction |
|---|---|---|---|---|---|---|
| 100,000,000 | dtlb_walk | 1.047 (1.046–1.047) | 0.004 (0.004–0.004) | 0.004 (0.004–0.004) | 0.004 (0.004–0.004) | 100.0% [100.0, 100.0] |
| 100,000,000 | l2d_cache_lmiss_rd | 1.765 (1.754–1.776) | 0.001 (0.001–0.001) | 0.001 (0.001–0.001) | 0.059 (0.058–0.059) | 96.7% [96.7, 96.8] |
| 100,000,000 | ll_cache_miss_rd | 3.245 (3.225–3.256) | 0.262 (0.262–0.262) | 0.262 (0.261–0.262) | 0.225 (0.225–0.225) | 101.2% [101.2, 101.2] |
| 400,000,000 | dtlb_walk | 1.053 (1.052–1.053) | 0.004 (0.004–0.004) | 0.004 (0.004–0.004) | 0.004 (0.004–0.004) | 100.0% [100.0, 100.0] |
| 400,000,000 | l2d_cache_lmiss_rd | 2.148 (2.141–2.151) | 0.001 (0.001–0.001) | 0.001 (0.001–0.001) | 0.054 (0.053–0.055) | 97.5% [97.5, 97.6] |
| 400,000,000 | ll_cache_miss_rd | 3.420 (3.415–3.433) | 0.262 (0.262–0.262) | 0.262 (0.262–0.262) | 0.225 (0.225–0.225) | 101.2% [101.1, 101.2] |

## Registered rules (replication machine: reported, not deciding)

- **H1** (reference at least 1.5× partitioned at 100M and 400M, interval above 1): HOLDS
- **H1b** (partitioned below every full sort at 100M and 400M, interval excluding 1): HOLDS
- **H6** (16-thread banding at least 3× sequential partitioned banding): HOLDS
- **H2** (at least 90% recovery on `l2d_cache_lmiss_rd` at 100M and 400M): HOLDS

## Checks on every run

- No false negatives; equal fingerprints across strategies in every repetition; every bits/key figure at or above log2(1/FPR).
