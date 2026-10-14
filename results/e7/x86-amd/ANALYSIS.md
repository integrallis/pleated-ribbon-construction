generated-by: experiments/e7_rigour/analyze.py over results/e7/x86-amd/raw/ (machine: AMD EPYC 9R14 96-Core Processor, x86_64, kernel 7.0.0-1014-aws, virt: none, profile: replication, source c624167a1b03394715a47714fb1a9e737c388897)

# E7 analysis, x86-amd (derived; do not hand-edit)

Pinned CPU 2 (siblings 2), governor performance, intel no_turbo None, boost 1, SMT active 0, THP always [madvise] never, g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0.

Cells are median (minimum–maximum) over the repetitions; ratios are ratios of medians with a 95% bootstrap interval.

## Cross-check of e7_driver against e1b_phase1

| keys | strategy | fingerprints equal | median total e1b_phase1 | median total e7_driver | ratio | tolerance |
|---|---|---|---|---|---|---|
| 10,000,000 | reference | yes | 65.53 | 64.56 | 0.985 | ±5% |
| 10,000,000 | sort_ips2ra | yes | 56.05 | 55.43 | 0.989 | ±10% |
| 10,000,000 | partitioned | yes | 38.83 | 37.65 | 0.970 | ±5% |
| 100,000,000 | reference | yes | 81.94 | 81.01 | 0.989 | ±5% |
| 100,000,000 | sort_ips2ra | yes | 59.21 | 58.61 | 0.990 | ±10% |
| 100,000,000 | partitioned | yes | 39.98 | 39.15 | 0.979 | ±5% |

Cross-check passed.

## Construction by key count and strategy (ns/key)

| keys | strategy | reps | reorder | banding | back-substitution | total |
|---|---|---|---|---|---|---|
| 10,000,000 | noprefetch | 10 | 0.0 (0.0–0.0) | 76.5 (75.4–76.9) | 9.1 (9.0–9.1) | 85.5 (84.4–85.9) |
| 10,000,000 | partitioned | 10 | 9.7 (9.7–9.8) | 20.1 (20.0–20.2) | 9.0 (9.0–9.0) | 38.9 (38.7–39.0) |
| 10,000,000 | reference | 10 | 0.0 (0.0–0.0) | 56.9 (56.5–57.4) | 9.0 (9.0–9.1) | 65.9 (65.6–66.5) |
| 10,000,000 | sort_ips2ra | 10 | 31.4 (31.0–32.2) | 16.0 (15.9–16.1) | 9.0 (9.0–9.1) | 56.4 (56.0–57.3) |
| 10,000,000 | sort_radix | 10 | 28.2 (27.9–29.4) | 16.0 (15.9–16.1) | 9.0 (9.0–9.1) | 53.2 (53.0–54.4) |
| 10,000,000 | sort_std | 10 | 79.3 (78.1–80.8) | 16.0 (15.9–16.1) | 9.1 (9.0–9.1) | 104.4 (103.1–105.8) |
| 100,000,000 | noprefetch | 10 | 0.0 (0.0–0.0) | 101.8 (101.3–102.1) | 9.0 (9.0–9.0) | 110.8 (110.3–111.1) |
| 100,000,000 | partitioned | 10 | 10.9 (10.9–10.9) | 20.1 (20.1–20.1) | 9.0 (9.0–9.0) | 40.0 (40.0–40.0) |
| 100,000,000 | reference | 10 | 0.0 (0.0–0.0) | 73.0 (72.6–73.2) | 9.0 (9.0–9.0) | 82.0 (81.6–82.3) |
| 100,000,000 | sort_ips2ra | 10 | 34.2 (33.7–34.4) | 15.9 (15.9–16.0) | 9.1 (9.1–9.1) | 59.2 (58.7–59.4) |
| 100,000,000 | sort_radix | 10 | 28.1 (28.0–28.1) | 15.9 (15.9–16.0) | 9.1 (9.0–9.1) | 53.0 (53.0–53.1) |
| 100,000,000 | sort_std | 10 | 88.0 (87.2–88.9) | 15.9 (15.9–16.0) | 9.1 (9.1–9.1) | 113.0 (112.2–113.9) |
| 400,000,000 | noprefetch | 10 | 0.0 (0.0–0.0) | 132.2 (131.9–132.9) | 9.0 (9.0–9.0) | 141.3 (141.0–141.9) |
| 400,000,000 | partitioned | 10 | 13.8 (13.8–13.8) | 20.1 (20.1–20.1) | 9.0 (9.0–9.0) | 42.9 (42.9–42.9) |
| 400,000,000 | reference | 10 | 0.0 (0.0–0.0) | 91.7 (91.5–92.0) | 9.0 (9.0–9.0) | 100.8 (100.5–101.1) |
| 400,000,000 | sort_ips2ra | 10 | 34.6 (34.4–34.9) | 15.9 (15.9–15.9) | 9.0 (9.0–9.0) | 59.6 (59.3–59.9) |
| 400,000,000 | sort_radix | 10 | 27.9 (27.8–28.1) | 15.9 (15.9–16.0) | 9.0 (9.0–9.0) | 52.9 (52.8–53.1) |
| 400,000,000 | sort_std | 10 | 93.6 (92.7–94.5) | 15.9 (15.9–15.9) | 9.0 (9.0–9.0) | 118.6 (117.7–119.4) |

| keys | reference / partitioned | best full sort | best sort / partitioned |
|---|---|---|---|
| 10,000,000 | 1.70× [1.69, 1.70] | sort_radix | 1.37× [1.36, 1.38] |
| 100,000,000 | 2.05× [2.04, 2.06] | sort_radix | 1.33× [1.33, 1.33] |
| 400,000,000 | 2.35× [2.34, 2.35] | sort_radix | 1.23× [1.23, 1.24] |

## Parallel build, 100M keys (ns/key)

| threads | reps | banding | total | banding vs its own 1 thread | banding vs sequential partitioned | deferred keys |
|---|---|---|---|---|---|---|
| 1 | 10 | 25.3 (25.2–25.3) | 45.2 (45.2–45.3) | 1.00× [1.00, 1.00] | 0.79× [0.79, 0.79] | 0.0000% |
| 2 | 10 | 13.6 (13.4–13.8) | 33.5 (33.4–33.7) | 1.86× [1.85, 1.87] | 1.48× [1.47, 1.48] | 0.0150% |
| 4 | 10 | 7.0 (6.9–7.1) | 26.9 (26.9–27.0) | 3.63× [3.60, 3.64] | 2.88× [2.86, 2.89] | 0.0451% |
| 8 | 10 | 3.8 (3.7–4.0) | 23.7 (23.6–24.0) | 6.73× [6.50, 6.76] | 5.34× [5.16, 5.37] | 0.1052% |
| 16 | 10 | 2.2 (2.1–2.3) | 22.1 (22.1–22.2) | 11.73× [11.70, 11.76] | 9.31× [9.29, 9.34] | 0.2252% |

Sequential partitioned banding: 20.1 (20.1–20.1) ns/key.

## Counters scoped to banding, per key

Events resolved on this machine: `l2_cache_req_stat.dc_access_in_l2` = 0xf864, `l2_cache_req_stat.ic_dc_miss_in_l2` = 0x964, `ls_dmnd_fills_from_sys.dram_io_near` = 0x843, `ls_l1_d_tlb_miss.all` = 0xff45.

| keys | event | reference | LSD radix | ips2ra | partitioned | recovery of the best sort's reduction |
|---|---|---|---|---|---|---|
| 100,000,000 | cycles | 265.450 (264.780–265.620) | 57.070 (57.030–57.120) | 57.070 (57.040–57.120) | 72.180 (72.030–72.230) | - |
| 100,000,000 | generic cache-misses | 3.427 (3.426–3.428) | 0.001 (0.001–0.001) | 0.001 (0.001–0.001) | 0.124 (0.123–0.124) | 96.4% [96.4, 96.4] |
| 100,000,000 | instructions | 94.540 (94.480–94.610) | 94.540 (94.470–94.600) | 94.540 (94.470–94.600) | 94.540 (94.480–94.610) | - |
| 100,000,000 | l2_cache_req_stat.dc_access_in_l2 | 3.998 (3.997–3.998) | 0.264 (0.264–0.264) | 0.264 (0.264–0.264) | 2.304 (2.303–2.304) | 45.4% [45.4, 45.4] |
| 100,000,000 | l2_cache_req_stat.ic_dc_miss_in_l2 | 3.426 (3.426–3.428) | 0.001 (0.001–0.001) | 0.001 (0.001–0.001) | 0.124 (0.123–0.124) | 96.4% [96.4, 96.4] |
| 100,000,000 | ls_dmnd_fills_from_sys.dram_io_near | 0.184 (0.183–0.184) | 0.000 (0.000–0.000) | 0.000 (0.000–0.000) | 0.009 (0.008–0.009) | 95.4% [95.4, 95.5] |
| 100,000,000 | ls_l1_d_tlb_miss.all | 1.029 (1.029–1.029) | 0.004 (0.004–0.004) | 0.004 (0.004–0.004) | 0.467 (0.467–0.467) | 54.8% [54.8, 54.8] |
| 400,000,000 | cycles | 334.500 (334.020–334.930) | 57.070 (57.050–57.080) | 57.050 (57.050–57.070) | 72.120 (72.080–72.150) | - |
| 400,000,000 | generic cache-misses | 3.603 (3.602–3.605) | 0.001 (0.001–0.001) | 0.001 (0.001–0.001) | 0.124 (0.123–0.124) | 96.6% [96.6, 96.6] |
| 400,000,000 | instructions | 94.510 (94.500–94.530) | 94.500 (94.490–94.520) | 94.500 (94.490–94.520) | 94.510 (94.500–94.530) | - |
| 400,000,000 | l2_cache_req_stat.dc_access_in_l2 | 4.267 (4.267–4.268) | 0.264 (0.264–0.264) | 0.264 (0.264–0.264) | 2.303 (2.302–2.303) | 49.1% [49.1, 49.1] |
| 400,000,000 | l2_cache_req_stat.ic_dc_miss_in_l2 | 3.603 (3.602–3.603) | 0.001 (0.001–0.001) | 0.001 (0.001–0.001) | 0.124 (0.123–0.124) | 96.6% [96.6, 96.6] |
| 400,000,000 | ls_dmnd_fills_from_sys.dram_io_near | 0.178 (0.178–0.178) | 0.000 (0.000–0.000) | 0.000 (0.000–0.000) | 0.008 (0.008–0.008) | 95.3% [95.3, 95.3] |
| 400,000,000 | ls_l1_d_tlb_miss.all | 1.029 (1.029–1.030) | 0.004 (0.004–0.004) | 0.004 (0.004–0.004) | 0.467 (0.467–0.468) | 54.8% [54.8, 54.8] |

## Registered rules (replication machine: reported, not deciding)

- **H1** (reference at least 1.5× partitioned at 100M and 400M, interval above 1): HOLDS
- **H1b** (partitioned below every full sort at 100M and 400M, interval excluding 1): HOLDS
- **H6** (16-thread banding at least 3× sequential partitioned banding): HOLDS
- **H2** (at least 90% recovery on `l2_cache_req_stat.ic_dc_miss_in_l2` at 100M and 400M): HOLDS

## Checks on every run

- No false negatives; equal fingerprints across strategies in every repetition; every bits/key figure at or above log2(1/FPR).
