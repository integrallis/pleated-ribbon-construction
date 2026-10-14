generated-by: experiments/e7_rigour/analyze.py over results/e7/x86-intel/raw/ (machine: Intel(R) Xeon(R) Platinum 8488C, x86_64, kernel 7.0.0-1014-aws, virt: none, profile: full, source a6ad7dea19ee47112b2ac533ef328b6ac2bb09e6)

# E7 analysis, x86-intel (derived; do not hand-edit)

Pinned CPU 2 (siblings 2,50), governor performance, intel no_turbo 0, boost None, SMT active 1, THP always [madvise] never, g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0.

Cells are median (minimum–maximum) over the repetitions; ratios are ratios of medians with a 95% bootstrap interval.

## Cross-check of e7_driver against e1b_phase1

| keys | strategy | fingerprints equal | median total e1b_phase1 | median total e7_driver | ratio | tolerance |
|---|---|---|---|---|---|---|
| 10,000,000 | reference | yes | 42.62 | 42.30 | 0.993 | ±5% |
| 10,000,000 | sort_ips2ra | yes | 55.12 | 55.08 | 0.999 | ±10% |
| 10,000,000 | partitioned | yes | 35.11 | 34.66 | 0.987 | ±5% |
| 100,000,000 | reference | yes | 89.93 | 89.96 | 1.000 | ±5% |
| 100,000,000 | sort_ips2ra | yes | 58.27 | 57.79 | 0.992 | ±10% |
| 100,000,000 | partitioned | yes | 36.13 | 35.76 | 0.990 | ±5% |

Cross-check passed.

## Construction by key count and strategy (ns/key)

| keys | strategy | reps | reorder | banding | back-substitution | total |
|---|---|---|---|---|---|---|
| 10,000,000 | noprefetch | 10 | 0.0 (0.0–0.0) | 50.3 (50.1–50.8) | 4.7 (4.7–4.7) | 55.0 (54.8–55.5) |
| 10,000,000 | partitioned | 10 | 7.3 (7.2–7.4) | 23.2 (23.1–23.3) | 4.7 (4.7–4.7) | 35.2 (35.0–35.3) |
| 10,000,000 | reference | 10 | 0.0 (0.0–0.0) | 38.6 (38.4–38.9) | 4.6 (4.6–4.7) | 43.3 (43.0–43.5) |
| 10,000,000 | sort_ips2ra | 10 | 31.6 (31.2–32.0) | 19.3 (19.2–19.4) | 4.6 (4.6–4.6) | 55.6 (55.2–56.0) |
| 10,000,000 | sort_radix | 10 | 37.0 (36.5–37.3) | 19.3 (19.2–19.4) | 4.6 (4.6–4.6) | 60.9 (60.5–61.2) |
| 10,000,000 | sort_std | 10 | 84.5 (84.1–85.0) | 19.3 (19.2–19.4) | 4.6 (4.6–4.7) | 108.5 (108.1–108.9) |
| 100,000,000 | noprefetch | 10 | 0.0 (0.0–0.0) | 116.7 (114.8–117.7) | 4.7 (4.7–4.7) | 121.4 (119.5–122.4) |
| 100,000,000 | partitioned | 10 | 8.2 (8.2–8.3) | 23.3 (23.2–23.3) | 4.6 (4.6–4.7) | 36.1 (36.1–36.2) |
| 100,000,000 | reference | 10 | 0.0 (0.0–0.0) | 84.8 (84.3–86.6) | 4.7 (4.7–4.7) | 89.4 (89.0–91.2) |
| 100,000,000 | sort_ips2ra | 10 | 34.3 (34.1–35.4) | 19.3 (19.3–19.4) | 4.6 (4.6–4.6) | 58.3 (58.0–59.4) |
| 100,000,000 | sort_radix | 10 | 38.0 (37.8–38.1) | 19.4 (19.3–19.4) | 4.6 (4.6–4.6) | 62.0 (61.8–62.1) |
| 100,000,000 | sort_std | 10 | 96.9 (96.7–97.5) | 19.4 (19.3–19.4) | 4.6 (4.6–4.6) | 120.9 (120.7–121.6) |
| 400,000,000 | noprefetch | 10 | 0.0 (0.0–0.0) | 126.1 (124.6–127.6) | 4.7 (4.7–4.7) | 130.8 (129.3–132.3) |
| 400,000,000 | partitioned | 10 | 9.1 (9.1–9.2) | 23.3 (23.2–23.3) | 4.6 (4.6–4.6) | 37.0 (37.0–37.1) |
| 400,000,000 | reference | 10 | 0.0 (0.0–0.0) | 90.7 (90.1–91.4) | 4.6 (4.6–4.6) | 95.4 (94.7–96.0) |
| 400,000,000 | sort_ips2ra | 10 | 33.9 (33.8–34.8) | 19.3 (19.3–19.4) | 4.6 (4.6–4.6) | 57.9 (57.8–58.8) |
| 400,000,000 | sort_radix | 10 | 37.6 (37.6–37.7) | 19.3 (19.2–19.4) | 4.6 (4.6–4.7) | 61.6 (61.5–61.7) |
| 400,000,000 | sort_std | 10 | 103.8 (103.6–104.1) | 19.3 (19.2–19.4) | 4.6 (4.6–4.6) | 127.8 (127.5–128.1) |

| keys | reference / partitioned | best full sort | best sort / partitioned |
|---|---|---|---|
| 10,000,000 | 1.23× [1.23, 1.23] | sort_ips2ra | 1.58× [1.57, 1.59] |
| 100,000,000 | 2.47× [2.46, 2.49] | sort_ips2ra | 1.61× [1.61, 1.61] |
| 400,000,000 | 2.57× [2.56, 2.59] | sort_ips2ra | 1.56× [1.56, 1.56] |

## Parallel build, 100M keys (ns/key)

| threads | reps | banding | total | banding vs its own 1 thread | banding vs sequential partitioned | deferred keys |
|---|---|---|---|---|---|---|
| 1 | 10 | 28.0 (27.9–28.1) | 40.9 (40.8–40.9) | 1.00× [1.00, 1.00] | 0.83× [0.83, 0.83] | 0.0000% |
| 2 | 10 | 14.5 (14.4–14.6) | 27.3 (27.3–27.5) | 1.93× [1.93, 1.94] | 1.61× [1.60, 1.61] | 0.0150% |
| 4 | 10 | 7.4 (7.3–7.4) | 20.2 (20.2–20.3) | 3.80× [3.79, 3.80] | 3.15× [3.14, 3.16] | 0.0451% |
| 8 | 10 | 3.9 (3.9–3.9) | 16.7 (16.7–16.8) | 7.21× [7.19, 7.23] | 5.98× [5.97, 6.00] | 0.1052% |
| 16 | 10 | 2.2 (2.2–2.8) | 15.0 (15.0–15.6) | 12.88× [12.86, 12.92] | 10.69× [10.67, 10.72] | 0.2252% |

Sequential partitioned banding: 23.3 (23.3–23.3) ns/key.

## Counters scoped to banding, per key

Events resolved on this machine: `mem_load_retired.l2_miss` = 0x10d1, `mem_load_retired.l3_miss` = 0x20d1, `dtlb_load_misses.walk_completed` = 0xe12.

| keys | event | reference | LSD radix | ips2ra | partitioned | recovery of the best sort's reduction |
|---|---|---|---|---|---|---|
| 100,000,000 | cycles | 323.200 (322.790–326.150) | 71.590 (71.540–71.610) | 71.600 (71.550–71.650) | 87.130 (87.020–87.170) | - |
| 100,000,000 | dtlb_load_misses.walk_completed | 0.988 (0.987–0.988) | 0.000 (0.000–0.000) | 0.000 (0.000–0.000) | 0.002 (0.002–0.002) | 99.8% [99.8, 99.8] |
| 100,000,000 | generic cache-misses | 3.218 (3.217–3.221) | 0.262 (0.261–0.262) | 0.261 (0.261–0.261) | 0.262 (0.262–0.262) | 100.0% [100.0, 100.0] |
| 100,000,000 | instructions | 97.850 (97.780–97.920) | 97.840 (97.770–97.910) | 97.840 (97.770–97.910) | 97.850 (97.780–97.920) | - |
| 100,000,000 | mem_load_retired.l2_miss | 0.111 (0.110–0.111) | 0.001 (0.001–0.001) | 0.001 (0.001–0.001) | 0.017 (0.017–0.017) | 85.0% [84.9, 85.1] |
| 100,000,000 | mem_load_retired.l3_miss | 0.096 (0.096–0.096) | 0.001 (0.001–0.001) | 0.001 (0.001–0.001) | 0.017 (0.017–0.017) | 83.3% [83.2, 83.4] |
| 400,000,000 | cycles | 345.920 (345.540–348.750) | 71.530 (71.470–71.590) | 71.530 (71.480–71.580) | 87.060 (87.010–87.120) | - |
| 400,000,000 | dtlb_load_misses.walk_completed | 0.994 (0.994–0.994) | 0.000 (0.000–0.000) | 0.000 (0.000–0.000) | 0.002 (0.002–0.002) | 99.8% [99.8, 99.8] |
| 400,000,000 | generic cache-misses | 3.650 (3.650–3.653) | 0.262 (0.262–0.262) | 0.262 (0.262–0.262) | 0.262 (0.262–0.262) | 100.0% [100.0, 100.0] |
| 400,000,000 | instructions | 97.810 (97.800–97.830) | 97.800 (97.790–97.820) | 97.800 (97.790–97.820) | 97.810 (97.800–97.830) | - |
| 400,000,000 | mem_load_retired.l2_miss | 0.109 (0.109–0.110) | 0.001 (0.001–0.001) | 0.001 (0.001–0.001) | 0.017 (0.017–0.017) | 84.9% [84.8, 85.0] |
| 400,000,000 | mem_load_retired.l3_miss | 0.106 (0.105–0.106) | 0.001 (0.001–0.001) | 0.001 (0.001–0.001) | 0.017 (0.017–0.017) | 84.9% [84.8, 85.0] |

## Configurations, 100M synthetic keys (total ns/key)

| band width / result bits / slots per key | reference total | ips2ra total | partitioned total | reference / partitioned | ips2ra / partitioned | FPR | bits/key |
|---|---|---|---|---|---|---|---|
| 128 / 16 / 1.062501 | 159.9 (158.9–160.3) | 80.9 (80.8–81.1) | 64.2 (64.0–64.2) | 2.49× [2.48, 2.50] | 1.26× [1.26, 1.27] | 0.000018 | 17.00 |
| 128 / 7 / 1.044923 | 161.5 (161.0–161.7) | 77.9 (77.8–78.0) | 60.8 (60.6–60.9) | 2.66× [2.65, 2.66] | 1.28× [1.28, 1.29] | 0.008086 | 7.31 |
| 128 / 8 / 1.046876 | 161.2 (161.0–161.4) | 78.2 (78.0–78.6) | 61.1 (61.0–61.2) | 2.64× [2.64, 2.64] | 1.28× [1.28, 1.29] | 0.004027 | 8.38 |
| 64 / 16 / 1.125 | 89.5 (89.2–90.3) | 60.7 (60.7–61.7) | 39.2 (39.2–39.2) | 2.28× [2.28, 2.30] | 1.55× [1.55, 1.57] | 0.000031 | 18.00 |
| 64 / 7 / 1.05 | 101.6 (101.3–101.8) | 64.6 (64.5–64.6) | 42.2 (42.2–42.3) | 2.41× [2.40, 2.41] | 1.53× [1.53, 1.53] | 0.021588 | 7.35 |
| 64 / 7 / 1.089844 | 90.0 (89.7–90.8) | 57.6 (57.6–57.7) | 35.7 (35.7–35.7) | 2.52× [2.51, 2.54] | 1.61× [1.61, 1.62] | 0.008216 | 7.63 |
| 64 / 7 / 1.15 | 80.6 (80.6–81.1) | 54.2 (54.2–54.3) | 32.7 (32.7–32.8) | 2.46× [2.46, 2.48] | 1.66× [1.65, 1.66] | 0.007829 | 8.05 |
| 64 / 8 / 1.09375 | 89.9 (89.5–90.4) | 57.9 (57.8–57.9) | 35.9 (35.9–35.9) | 2.50× [2.49, 2.52] | 1.61× [1.61, 1.61] | 0.004140 | 8.75 |

## Key sets (total ns/key, hashing included)

| key set | keys | mean key bytes | hashing | reference total | ips2ra total | partitioned total | reference / partitioned | ips2ra / partitioned |
|---|---|---|---|---|---|---|---|---|
| cc_hosts_direct | 100,000,000 | 19.7 | 0.0 | 97.9 (97.7–98.0) | 139.1 (139.0–140.9) | 102.3 (102.3–102.5) | 0.96× [0.95, 0.96] | 1.36× [1.36, 1.38] |
| cc_hosts_hashed | 100,000,000 | 19.7 | 4.4 | 94.2 (93.8–94.7) | 61.5 (61.5–61.6) | 40.1 (40.1–40.1) | 2.35× [2.34, 2.36] | 1.53× [1.53, 1.54] |
| sosd_fb_hashed | 100,000,000 | 8.0 | 0.0 | 89.8 (89.3–90.0) | 57.3 (57.2–58.5) | 35.6 (35.6–35.6) | 2.52× [2.51, 2.53] | 1.61× [1.61, 1.64] |
| sosd_osm_hashed | 100,000,000 | 8.0 | 0.0 | 89.7 (89.3–90.0) | 57.3 (57.3–57.3) | 35.6 (35.6–35.7) | 2.52× [2.51, 2.53] | 1.61× [1.61, 1.61] |
| sosd_wiki_hashed | 90,000,000 | 8.0 | 0.0 | 89.0 (88.4–89.6) | 57.2 (57.2–57.5) | 35.6 (35.5–35.6) | 2.50× [2.49, 2.52] | 1.61× [1.61, 1.62] |
| synth16_direct | 100,000,000 | 16.0 | 0.0 | 95.3 (94.2–95.7) | 127.5 (127.4–127.9) | 91.8 (91.7–91.9) | 1.04× [1.03, 1.04] | 1.39× [1.39, 1.39] |
| synth16_hashed | 100,000,000 | 16.0 | 3.1 | 93.2 (93.1–93.6) | 60.2 (60.2–61.0) | 38.8 (38.8–38.8) | 2.40× [2.40, 2.41] | 1.55× [1.55, 1.57] |
| synth64_direct | 100,000,000 | 64.0 | 0.0 | 104.6 (103.3–104.9) | 165.3 (165.1–165.6) | 133.1 (132.8–133.4) | 0.79× [0.78, 0.79] | 1.24× [1.24, 1.24] |
| synth64_hashed | 100,000,000 | 64.0 | 8.8 | 98.5 (98.5–99.3) | 65.7 (65.6–65.7) | 44.4 (44.4–44.4) | 2.22× [2.22, 2.24] | 1.48× [1.48, 1.48] |

`_hashed`: strings hashed once with XXH3, then 64-bit values (integer sets are used as they are). `_direct`: the string is the filter's key and is hashed again in every pass.

Sources: sosd_fb: https://dataverse.harvard.edu/api/access/datafile/:persistentId?persistentId=doi:10.7910/DVN/JGVF9A/EATHF7; sosd_osm: https://dataverse.harvard.edu/api/access/datafile/:persistentId?persistentId=doi:10.7910/DVN/JGVF9A/8FX9BV; sosd_wiki: https://dataverse.harvard.edu/api/access/datafile/:persistentId?persistentId=doi:10.7910/DVN/JGVF9A/SVN8PI; cc_hosts: https://data.commoncrawl.org/projects/hyperlinkgraph/cc-main-2025-mar-apr-may/host/cc-main-2025-mar-apr-may-host-vertices.paths.gz; synth16: numpy default_rng(247); first 8 bytes are the index; synth64: numpy default_rng(295); first 8 bytes are the index.

## Transparent huge pages, 100M synthetic keys (total ns/key; no hypothesis)

| THP | reference | ips2ra | partitioned | reference / partitioned |
|---|---|---|---|---|
| madvise | 89.6 (89.0–90.6) | 57.3 (57.3–57.4) | 35.6 (35.6–35.7) | 2.52× [2.50, 2.54] |
| always | 82.4 (81.9–82.7) | 52.5 (52.3–52.5) | 33.3 (33.3–33.3) | 2.48× [2.46, 2.49] |
| never | 89.8 (89.3–90.1) | 57.3 (57.2–57.4) | 35.6 (35.6–35.7) | 2.52× [2.51, 2.53] |

## Compaction in db_bench (CPU seconds of compaction)

| SST target | reps per arm | stock | pleated | pleated / stock | SST files at end (stock, pleated) |
|---|---|---|---|---|---|
| 64 MiB | 5 | 8.31 (8.29–8.47) | 7.92 (7.91–8.00) | 0.954× [0.936, 0.963] | 11, 11 |
| 256 MiB | 20 | 9.42 (9.39–9.44) | 8.01 (7.99–8.05) | 0.850× [0.849, 0.852] | 6, 6 |
| 1024 MiB | 5 | 9.83 (9.81–9.83) | 8.06 (8.01–8.08) | 0.820× [0.815, 0.822] | 5, 5 |

## Registered rules (primary machine: these decide)

- **H1** (reference at least 1.5× partitioned at 100M and 400M, interval above 1): HOLDS
- **H1b** (partitioned below every full sort at 100M and 400M, interval excluding 1): HOLDS
- **H6** (16-thread banding at least 3× sequential partitioned banding): HOLDS
- **H2** (at least 90% recovery on `mem_load_retired.l2_miss` at 100M and 400M): FAILS
- **H3** (reference at least 1.3× partitioned in each of the eight configurations): HOLDS
- **H4** (reference at least 1.5× partitioned, hashing included, for every integer set and every string set hashed once): HOLDS
- **H5** (pleated compaction CPU below stock at 256 MiB, interval excluding 1): HOLDS

## Checks on every run

- No false negatives; equal fingerprints across strategies in every repetition; every bits/key figure at or above log2(1/FPR).
