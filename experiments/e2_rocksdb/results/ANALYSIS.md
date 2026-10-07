generated-by: experiments/e2_rocksdb/analyze.py over experiments/e2_rocksdb/results/{sweep_fb.csv,dbbench_reps.csv} (machine: Intel i9-14900HX per README; RocksDB v10.2.0)

# E2 analysis (derived — do not hand-edit)

## filter_bench sweep (means over reps)

| keys/filter | reps | stock total ns/key | pleated total ns/key | speedup | stock banding | pleated banding | stock miss/key | pleated miss/key | FP stock == pleated |
|---|---|---|---|---|---|---|---|---|---|
| 100,000 | 3/3 | 57.61 | 59.38 | 0.97x | 43.78 | 45.74 | nan | nan | yes |
| 1,000,000 | 3/3 | 55.87 | 54.41 | 1.03x | 42.71 | 36.79 | 0.494 | 0.491 | yes |
| 3,000,000 | 3/3 | 78.82 | 55.12 | 1.43x | 64.28 | 35.95 | 5.435 | 0.456 | yes |
| 10,000,000 | 3/3 | 88.68 | 54.72 | 1.62x | 72.46 | 34.11 | 5.862 | 0.443 | yes |
| 30,000,000 | 3/3 | 91.84 | 55.46 | 1.66x | 75.43 | 33.37 | 10.835 | 0.463 | yes |
| 100,000,000 | 3/3 | 97.44 | 54.84 | 1.78x | 79.95 | 31.76 | 11.500 | 0.466 | yes |

## db_bench (mean ± sample stdev over reps)

| mode | reps | banding ns/key | filter banding s | compaction CPU s | banding share of compaction CPU |
|---|---|---|---|---|---|
| stock | 3 | 77.6±1.5 | 1.83±0.04 | 7.89±0.78 | 23.2% |
| pleated | 3 | 44.2±6.1 | 1.04±0.14 | 7.15±0.37 | 14.5% |

Compaction CPU difference of means: 0.73 s (9.3%); sample stdevs are 0.78 s (stock) and 0.37 s (pleated), so with n=3 the difference is within one combined stdev.
