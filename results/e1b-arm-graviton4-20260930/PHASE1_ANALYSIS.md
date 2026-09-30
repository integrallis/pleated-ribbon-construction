generated-by: experiments/e1b_ribbon_construction/analyze_phase1.py over results/e1b/phase1/ (machine: , aarch64)

# E1b Phase-1 analysis (derived — do not hand-edit)

## Per-phase construction cost (ns/key, mean +/- sample stdev over reps)

| n | strategy | reorder | banding | backsubst | TOTAL | banding miss/key | banding cyc/key |
|---|---|---|---|---|---|---|---|
| 10,000,000 | reference | 0.00±0.00 | 68.27±0.74 | 7.85 | **76.11±0.75** | 0.000 | 0.0 |
| 10,000,000 | noprefetch | 0.00±0.00 | 85.38±2.44 | 7.83 | **93.21±2.44** | 0.000 | 0.0 |
| 10,000,000 | sort_std | 65.83±0.31 | 16.61±0.05 | 7.82 | **90.27±0.35** | 0.000 | 0.0 |
| 10,000,000 | sort_radix | 21.78±0.05 | 16.60±0.03 | 7.82 | **46.20±0.03** | 0.000 | 0.0 |
| 10,000,000 | sort_ips2ra | 24.99±0.01 | 16.60±0.05 | 7.82 | **49.41±0.05** | 0.000 | 0.0 |
| 10,000,000 | partitioned | 6.21±0.03 | 21.38±0.00 | 7.83 | **35.42±0.03** | 0.000 | 0.0 |
| 100,000,000 | reference | 0.00±0.00 | 79.93±1.17 | 7.83 | **87.76±1.17** | 0.000 | 0.0 |
| 100,000,000 | noprefetch | 0.00±0.00 | 113.80±0.71 | 7.83 | **121.63±0.71** | 0.000 | 0.0 |
| 100,000,000 | sort_std | 73.58±0.19 | 16.66±0.01 | 7.82 | **98.07±0.20** | 0.000 | 0.0 |
| 100,000,000 | sort_radix | 21.73±0.07 | 16.66±0.01 | 7.82 | **46.21±0.09** | 0.000 | 0.0 |
| 100,000,000 | sort_ips2ra | 27.05±0.07 | 16.65±0.01 | 7.82 | **51.52±0.07** | 0.000 | 0.0 |
| 100,000,000 | partitioned | 6.70±0.02 | 21.40±0.04 | 7.83 | **35.92±0.05** | 0.000 | 0.0 |
| 400,000,000 | reference | 0.00±0.00 | 91.71±0.24 | 7.83 | **99.54±0.24** | 0.000 | 0.0 |
| 400,000,000 | noprefetch | 0.00±0.00 | 133.31±0.47 | 7.83 | **141.14±0.47** | 0.000 | 0.0 |
| 400,000,000 | sort_std | 78.16±0.24 | 16.63±0.03 | 7.82 | **102.62±0.22** | 0.000 | 0.0 |
| 400,000,000 | sort_radix | 22.77±0.03 | 16.64±0.00 | 7.83 | **47.23±0.02** | 0.000 | 0.0 |
| 400,000,000 | sort_ips2ra | 26.45±0.03 | 16.65±0.00 | 7.83 | **50.92±0.03** | 0.000 | 0.0 |
| 400,000,000 | partitioned | 8.04±0.02 | 21.31±0.01 | 7.83 | **37.18±0.02** | 0.000 | 0.0 |

## Registered H-E1b-1 evaluation

- Bit-identity across strategies (per n,rep): PASS
- Total false negatives across all runs: 0
- n=100,000,000: miss-recovery nan% (need ≥80%); reorder 6.70 vs best-sort 21.73 ns/key; totals part 35.92 / ref 87.76 / best-sort 46.21 → conditions not all met
- n=400,000,000: miss-recovery nan% (need ≥80%); reorder 8.04 vs best-sort 22.77 ns/key; totals part 37.18 / ref 99.54 / best-sort 47.23 → conditions not all met

**Mixed outcome — apply the amendment's failure threshold per size; log interpretation before any next step.**
