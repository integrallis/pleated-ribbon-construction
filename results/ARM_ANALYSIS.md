generated-by: experiments/e1b_ribbon_construction/analyze_arm.py over results/e1b/phase1/, results/e1b-arm-n1/phase1/, results/e1b-arm-v2/{phase1,parallel}/, results/e1b-arm-graviton4-pmu-20260930/e1b-100M.jsonl

# ARM replication analysis (derived — do not hand-edit)

## Construction total at 100M keys (ns/key, mean ± sample stdev)

| machine | reps | reference | best full sort (which) | partitioned | pleating vs reference | pleating vs best sort | reference banding |
|---|---|---|---|---|---|---|---|
| x86 (i9-14900HX) | 3 | 49.6±1.4 | 40.7±0.3 (sort_ips2ra) | 24.2±0.2 | 2.05x | 1.68x | 46.1 |
| N1 (Ampere Altra) | 3 | 122.8±0.3 | 64.6±0.3 (sort_radix) | 51.7±0.3 | 2.37x | 1.25x | 113.8 |
| V2 (Google Axion) | 3 | 93.7±0.5 | 44.8±0.3 (sort_radix) | 34.4±0.0 | 2.72x | 1.30x | 86.3 |

## Output checks

- False negatives summed over every x86/N1/V2 Phase-1 run: 0
- x86 (i9-14900HX): all strategies share one fingerprint at 9/9 (n, rep) points
- N1 (Ampere Altra): all strategies share one fingerprint at 9/9 (n, rep) points
- V2 (Google Axion): all strategies share one fingerprint at 9/9 (n, rep) points
- Cross-architecture: partitioned fingerprint identical on all three machines at 9/9 common (n, rep) points

## V2 (Google Axion) parallel banding, 100M keys

| threads | reps | banding ns/key | speedup vs T=1 | total ns/key | deferred % |
|---|---|---|---|---|---|
| 1 | 1 | 24.48 | 1.00x | 38.25 | 0.000% |
| 2 | 1 | 12.62 | 1.94x | 26.46 | 0.015% |
| 4 | 1 | 6.47 | 3.78x | 20.20 | 0.045% |
| 8 | 1 | 3.46 | 7.07x | 17.28 | 0.105% |

## Graviton4 (Neoverse-V2) PMU follow-up, 100M keys, banding-scoped l2d_cache_lmiss_rd

| strategy | reps | median L2 read misses/key | median total ns/key |
|---|---|---|---|
| reference | 3 | 1.770 | 81.89 |
| sort_radix | 3 | 0.001 | 45.83 |
| partitioned | 3 | 0.058 | 35.99 |

Miss-reduction recovery of partitioned vs sort_radix: 96.8%
