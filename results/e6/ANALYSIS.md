generated-by: experiments/e6_memory_and_boundary/analyze.py over results/e6/ (machine: AMD EPYC 9R14, x86_64, 16 CPUs)

# E6 analysis (derived — do not hand-edit)

Topology: {"CPU(s)": "16", "Thread(s) per core": "1", "Core(s) per socket": "16", "L2 cache": "16 MiB (16 instances)", "L3 cache": "64 MiB (2 instances)"}

## Boundary fallback (parallel banding with reduced margins)

| threads | margin (slots) | runs | spilled (min-max) | deferred (max) | fingerprint == sequential | false negatives |
|---|---|---|---|---|---|---|
| 2 | 16384 | 3 | 0-0 | 15279 | yes | 0 |
| 2 | 1024 | 3 | 0-0 | 995 | yes | 0 |
| 2 | 64 | 3 | 0-0 | 64 | yes | 0 |
| 2 | 8 | 3 | 0-1 | 8 | yes | 0 |
| 2 | 0 | 3 | 1-6 | 6 | yes | 0 |
| 16 | 16384 | 3 | 0-0 | 225937 | yes | 0 |
| 16 | 1024 | 3 | 0-0 | 14332 | yes | 0 |
| 16 | 64 | 3 | 0-0 | 910 | yes | 0 |
| 16 | 8 | 3 | 3-48 | 180 | yes | 0 |
| 16 | 0 | 3 | 52-138 | 138 | yes | 0 |

- **H-E6-1** (identical output and no false negatives at every setting): HOLDS
- Fallback exercised (some run with spilled > 0): yes, up to 138 keys in one run

## Peak resident memory, standalone driver, 100M keys (whole process)

| strategy | runs | peak RSS MB (mean, min-max) | delta vs reference MB | delta bytes/key | total ns/key |
|---|---|---|---|---|---|
| reference | 3 | 1689 (1689-1689) | +0 | +0.00 | 84.1 |
| sort_radix | 3 | 5412 (5412-5412) | +3723 | +39.04 | 55.6 |
| sort_ips2ra | 3 | 3887 (3887-3887) | +2198 | +23.04 | 60.8 |
| partitioned | 3 | 2452 (2452-2452) | +763 | +8.00 | 40.7 |
| parallel (16 threads) | 3 | 3125 (3125-3125) | +1436 | +15.05 | 22.5 |

- **H-E6-2** (partitioned exceeds reference by 8 bytes/key ±25%): HOLDS — measured +8.00 bytes/key

## Peak resident memory, RocksDB filter_bench, 100M keys per filter (whole process)

| arm | runs | peak RSS MB (mean, min-max) | build ns/key |
|---|---|---|---|
| stock | 3 | 3735 (3735-3735) | 169.3 |
| pleated | 3 | 4738 (4738-4738) | 96.9 |

Pleated minus stock peak: +1003 MB (descriptive; filter_bench varies keys per filter by up to 40% and holds its finished filters).

## Concurrent builders (K pinned processes, 100M keys each; per-process total ns/key)

| K | reference (mean, min-max) | partitioned (mean, min-max) | reference / partitioned |
|---|---|---|---|
| 1 | 81.7 (81.5-81.9) | 40.5 (40.4-40.5) | 2.02x |
| 4 | 87.7 (86.7-88.7) | 40.6 (40.5-40.8) | 2.16x |
| 8 | 91.0 (89.6-92.1) | 41.3 (41.1-41.4) | 2.20x |

- **H-E6-3** (partitioned ≥ 1.5x faster per process at K=4 and K=8): HOLDS

Scope: one machine; whole-process peak RSS includes the input keys and the verification pass, so only differences between strategies are attributed to the reorder; concurrent builders are separate processes.
