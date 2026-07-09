generated-by: experiments/e1a_construction/analyze.py over results/e1a/ artifacts (machine: Intel(R) Core(TM) i9-14900HX, x86_64, rustc 1.94.1 (e408947bf 2026-03-25))

# E1a analysis (derived — do not hand-edit)

## Construction throughput (mean ns/key; raw: criterion/)

| size | perkey | perkey_prefetch | partitioned | partitioned_grouped | partitioned_grouped_nt |
|---|---|---|---|---|---|
| 1M | 2.06 | 1.60 | 6.42 | 10.57 | 10.51 |
| 10M | 2.87 | 2.27 | 6.97 | 11.50 | 11.58 |
| 53.7M_64MBfilter | 11.11 | 6.08 | 7.65 | 12.19 | 11.90 |
| 100M | 12.12 | 7.35 | 7.69 | 11.79 | 12.29 |
| 429M_512MBfilter | 13.19 | 8.90 | 7.71 | 11.80 | 11.86 |

## Frozen decision rules

- 53.7M_64MBfilter: partitioned/perkey = 1.45x, grouped/partitioned = 0.63x, grouped_nt/partitioned = 0.64x
- 100M: partitioned/perkey = 1.58x, grouped/partitioned = 0.65x, grouped_nt/partitioned = 0.63x
- 429M_512MBfilter: partitioned/perkey = 1.71x, grouped/partitioned = 0.65x, grouped_nt/partitioned = 0.65x

H1 (replication, partitioned ≥2× perkey at ≥64MB): NOT met
H2 (novelty, grouped ≥1.2× over partitioned at ≥64MB): NOT met
H2-NT (grouped_nt ≥1.2× over partitioned at ≥64MB): NOT met
K2 status: H2 unmet as implemented — full K2 unless an amendment (logged before rerun) improves the apply; see README kill criteria.
