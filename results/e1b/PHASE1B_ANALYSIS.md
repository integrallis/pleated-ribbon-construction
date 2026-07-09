generated-by: experiments/e1b_ribbon_construction/analyze_phase1b.py over results/e1b/{window_sweep,parallel}/

# E1b Phase-1b analysis (derived — do not hand-edit)

## Window-size sweep (partitioned, n=100M, mean over reps, ns/key)

| shift | window slots | reorder | banding | TOTAL | banding miss/key |
|---|---|---|---|---|---|
| 13 | 2^13 | 6.63 | 14.25 | **24.34** | 0.146 |
| 14 | 2^14 | 6.06 | 14.37 | **23.82** | 0.149 |
| 15 | 2^15 | 5.76 | 14.79 | **24.05** | 0.147 |
| 16 | 2^16 | 5.70 | 16.02 | **25.46** | 0.171 |
| 17 | 2^17 | 5.32 | 16.02 | **24.87** | 0.182 |
| 18 | 2^18 | 5.34 | 16.86 | **25.64** | 0.207 |
| 19 | 2^19 | 5.14 | 17.64 | **26.18** | 0.255 |
| 20 | 2^20 | 5.22 | 18.23 | **26.86** | 0.306 |

## Parallel windows (H-E1b-2p; shift=16)

| n | threads | banding ns/key | TOTAL ns/key | banding speedup vs T=1 | deferred % | bit-identity |
|---|---|---|---|---|---|---|
| 100,000,000 | 1 | 18.26 | **27.26** | 1.00× | 0.000% | PASS |
| 100,000,000 | 2 | 10.11 | **19.55** | 1.81× | 0.015% | PASS |
| 100,000,000 | 4 | 6.45 | **16.08** | 2.83× | 0.045% | PASS |
| 100,000,000 | 8 | 4.29 | **14.64** | 4.25× | 0.105% | PASS |
| 100,000,000 | 16 | 2.42 | **11.93** | 7.56× | 0.226% | PASS |
| 400,000,000 | 8 | 3.43 | **13.24** | — | 0.026% | PASS |

## H-E1b-2p registered conditions
- (a) bit-identity everywhere: PASS
- (b) deferred <0.5% at 100M/T=8: PASS
- (c) banding speedup ≥3× at T=8/100M: PASS

**H-E1b-2p CONFIRMED.**
