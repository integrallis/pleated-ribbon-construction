generated-by: experiments/e1b_ribbon_construction/analyze_phase1.py over results/e1b/phase1/ (machine: Intel(R) Core(TM) i9-14900HX, x86_64)

# E1b Phase-1 analysis (derived — do not hand-edit)

## Per-phase construction cost (ns/key, mean +/- sample stdev over reps)

| n | strategy | reorder | banding | backsubst | TOTAL | banding miss/key | banding cyc/key |
|---|---|---|---|---|---|---|---|
| 10,000,000 | reference | 0.00±0.00 | 38.89±0.41 | 3.40 | **42.29±0.42** | 3.776 | 203.1 |
| 10,000,000 | noprefetch | 0.00±0.00 | 57.20±2.66 | 3.28 | **60.48±2.67** | 4.160 | 305.8 |
| 10,000,000 | sort_std | 58.77±0.58 | 13.27±0.18 | 3.30 | **75.35±0.72** | 0.077 | 71.8 |
| 10,000,000 | sort_radix | 24.61±4.64 | 13.59±0.45 | 3.36 | **41.56±4.88** | 0.073 | 71.4 |
| 10,000,000 | sort_ips2ra | 22.31±0.17 | 13.49±0.12 | 3.33 | **39.14±0.17** | 0.074 | 71.7 |
| 10,000,000 | partitioned | 5.15±0.25 | 15.24±0.40 | 3.47 | **23.86±0.65** | 0.164 | 79.9 |
| 100,000,000 | reference | 0.00±0.00 | 46.06±1.38 | 3.53 | **49.58±1.43** | 5.750 | 243.2 |
| 100,000,000 | noprefetch | 0.00±0.00 | 76.92±4.32 | 3.84 | **80.76±4.21** | 5.814 | 347.6 |
| 100,000,000 | sort_std | 76.77±7.13 | 15.47±2.23 | 3.88 | **96.12±8.91** | 0.074 | 69.0 |
| 100,000,000 | sort_radix | 23.35±1.92 | 14.69±0.79 | 3.70 | **41.73±1.15** | 0.076 | 70.6 |
| 100,000,000 | sort_ips2ra | 23.88±0.14 | 13.40±0.14 | 3.38 | **40.66±0.31** | 0.075 | 70.4 |
| 100,000,000 | partitioned | 5.54±0.08 | 15.20±0.11 | 3.43 | **24.17±0.21** | 0.170 | 81.4 |
| 400,000,000 | reference | 0.00±0.00 | 51.87±0.95 | 3.41 | **55.28±0.95** | 6.126 | 271.5 |
| 400,000,000 | noprefetch | 0.00±0.00 | 86.80±1.38 | 3.38 | **90.18±1.43** | 6.487 | 465.5 |
| 400,000,000 | sort_std | 72.51±0.80 | 13.31±0.09 | 3.77 | **89.59±0.54** | 0.076 | 71.5 |
| 400,000,000 | sort_radix | 24.20±3.55 | 13.86±0.99 | 3.42 | **41.48±4.52** | 0.075 | 70.4 |
| 400,000,000 | sort_ips2ra | 28.11±3.01 | 15.41±0.88 | 3.79 | **47.31±2.25** | 0.075 | 70.7 |
| 400,000,000 | partitioned | 6.14±0.02 | 15.11±0.07 | 3.41 | **24.66±0.06** | 0.170 | 81.3 |

## Registered H-E1b-1 evaluation

- Bit-identity across strategies (per n,rep): PASS
- Total false negatives across all runs: 0
- n=100,000,000: miss-recovery 98.3% (need ≥80%); reorder 5.54 vs best-sort 23.35 ns/key; totals part 24.17 / ref 49.58 / best-sort 40.66 → conditions ALL MET
- n=400,000,000: miss-recovery 98.4% (need ≥80%); reorder 6.14 vs best-sort 24.20 ns/key; totals part 24.66 / ref 55.28 / best-sort 41.48 → conditions ALL MET

**H-E1b-1 CONFIRMED at all ≥100M sizes.**
