generated-by: experiments/e3_bloom_gap/analyze.py over results/e3/sweep_fb.csv (machine: AMD EPYC-Milan Processor, x86_64, virt: kvm; RocksDB 31b239747)

# E3 Stage A analysis (derived — do not hand-edit)

## Build cost, filter_bench "Build avg ns/key" (mean ± sample stdev over reps)

| keys/filter | arm | reps | build ns/key | FP rate % | bits/key stored |
|---|---|---|---|---|---|
| 100,000 | bloom | 3 | 15.87±0.08 | 0.9671 | 10.00 |
| 100,000 | stock | 3 | 78.88±0.24 | 0.9486 | 7.03 |
| 100,000 | pleated | 3 | 82.18±0.53 | 0.9486 | 7.03 |
| 1,000,000 | bloom | 3 | 20.16±0.24 | 0.9664 | 10.00 |
| 1,000,000 | stock | 3 | 94.18±1.90 | 0.9512 | 7.10 |
| 1,000,000 | pleated | 3 | 83.36±1.21 | 0.9512 | 7.10 |
| 10,000,000 | bloom | 3 | 22.65±1.00 | 0.9641 | 10.00 |
| 10,000,000 | stock | 3 | 164.63±3.48 | 0.9561 | 7.19 |
| 10,000,000 | pleated | 3 | 92.91±0.38 | 0.9561 | 7.19 |
| 100,000,000 | bloom | 3 | 37.12±0.22 | 0.9686 | 10.00 |
| 100,000,000 | stock | 3 | 167.85±1.63 | 0.9530 | 7.28 |
| 100,000,000 | pleated | 3 | 90.34±0.63 | 0.9530 | 7.28 |

## Ratios and registered rules

| keys/filter | stock/Bloom | pleated/Bloom | stock/pleated | FPR-matched | ribbon bits vs Bloom | stock FP == pleated FP |
|---|---|---|---|---|---|---|
| 100,000 | 4.97x | 5.18x | 0.96x | yes | -29.8% | yes |
| 1,000,000 | 4.67x | 4.13x | 1.13x | yes | -29.0% | yes |
| 10,000,000 | 7.27x | 4.10x | 1.77x | yes | -28.1% | yes |
| 100,000,000 | 4.52x | 2.43x | 1.86x | yes | -27.2% | yes |

- FPR-match criterion (≤10% relative): 100,000: matched, 1,000,000: matched, 10,000,000: matched, 100,000,000: matched
- Correctness gate (stock FP == pleated FP): PASS at every size
- **H-E3-1** (pleated/Bloom > 1.5 at every FPR-matched size ≥ 10,000,000): HOLDS
- **H-E3-2** (pleated/Bloom ≤ 1.25 at 100,000,000): FAILS — the paper says 'narrows the gap', with the measured ratios

Scope: one thread, RocksDB's own harness and builders, build time as filter_bench reports it (AddKey + Finish, hashing included). Not an equal-thread parallel comparison.
