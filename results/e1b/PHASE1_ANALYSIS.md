generated-by: experiments/e1b_ribbon_construction/analyze_phase1.py over results/e1b/phase1/ (machine: Intel(R) Core(TM) i9-14900HX, x86_64)

# E1b Phase-1 analysis (derived — do not hand-edit)

## Per-phase construction cost (ns/key, mean over reps)

| n | strategy | reorder | banding | backsubst | TOTAL | banding miss/key | banding cyc/key |
|---|---|---|---|---|---|---|---|
| 10,000,000 | reference | 0.00 | 38.89 | 3.40 | **42.29** | 3.776 | 203.1 |
| 10,000,000 | noprefetch | 0.00 | 57.20 | 3.28 | **60.48** | 4.160 | 305.8 |
| 10,000,000 | sort_std | 58.77 | 13.27 | 3.30 | **75.35** | 0.077 | 71.8 |
| 10,000,000 | sort_radix | 24.61 | 13.59 | 3.36 | **41.56** | 0.073 | 71.4 |
| 10,000,000 | partitioned | 5.15 | 15.24 | 3.47 | **23.86** | 0.164 | 79.9 |
| 100,000,000 | reference | 0.00 | 46.06 | 3.53 | **49.58** | 5.750 | 243.2 |
| 100,000,000 | noprefetch | 0.00 | 76.92 | 3.84 | **80.76** | 5.814 | 347.6 |
| 100,000,000 | sort_std | 76.77 | 15.47 | 3.88 | **96.12** | 0.074 | 69.0 |
| 100,000,000 | sort_radix | 23.35 | 14.69 | 3.70 | **41.73** | 0.076 | 70.6 |
| 100,000,000 | partitioned | 5.54 | 15.20 | 3.43 | **24.17** | 0.170 | 81.4 |
| 400,000,000 | reference | 0.00 | 51.87 | 3.41 | **55.28** | 6.126 | 271.5 |
| 400,000,000 | noprefetch | 0.00 | 86.80 | 3.38 | **90.18** | 6.487 | 465.5 |
| 400,000,000 | sort_std | 72.51 | 13.31 | 3.77 | **89.59** | 0.076 | 71.5 |
| 400,000,000 | sort_radix | 24.20 | 13.86 | 3.42 | **41.48** | 0.075 | 70.4 |
| 400,000,000 | partitioned | 6.14 | 15.11 | 3.41 | **24.66** | 0.170 | 81.3 |

## Registered H-E1b-1 evaluation

- Bit-identity across strategies (per n,rep): PASS
- Total false negatives across all runs: 0
- n=100,000,000: miss-recovery 98.3% (need ≥80%); reorder 5.54 vs best-sort 23.35 ns/key; totals part 24.17 / ref 49.58 / best-sort 41.73 → conditions ALL MET
- n=400,000,000: miss-recovery 98.4% (need ≥80%); reorder 6.14 vs best-sort 24.20 ns/key; totals part 24.66 / ref 55.28 / best-sort 41.48 → conditions ALL MET

**H-E1b-1 CONFIRMED at all ≥100M sizes.**
