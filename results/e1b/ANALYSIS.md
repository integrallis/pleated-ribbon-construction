generated-by: experiments/e1b_ribbon_construction/analyze.py over results/e1b/phase0/ (machine: Intel(R) Core(TM) i9-14900HX, x86_64)

# E1b Phase-0 analysis (derived — do not hand-edit)

## Construction cost (add-phase; mean over reps, ± half-range)

| algorithm | n | add ns/key | cycles/key | IPC | misses/key | FPR% | bits/key |
|---|---|---|---|---|---|---|---|
| HomogRibbon64_7 | 1,000,000 | 24.20 ± 0.63 | 122.9 | 1.33 | 0.21 | 0.9297 | 7.63 |
| HomogRibbon64_7 | 10,000,000 | 45.95 ± 0.12 | 229.5 | 0.71 | 4.47 | 0.8085 | 7.63 |
| HomogRibbon64_7 | 100,000,000 | 50.61 ± 0.28 | 256.0 | 0.64 | 5.81 | 0.8142 | 7.63 |
| BalancedRibbon64Pack_7 | 1,000,000 | 99.05 ± 5.04 | 416.4 | 1.44 | 0.89 | 0.7842 | 7.05 |
| BalancedRibbon64Pack_7 | 10,000,000 | 93.56 ± 2.82 | 476.5 | 1.32 | 2.19 | 0.7816 | 7.05 |
| BalancedRibbon64Pack_7 | 100,000,000 | 133.82 ± 1.01 | 676.6 | 1.16 | 6.17 | 0.7777 | 7.04 |
| XorBinaryFuse8 | 1,000,000 | 26.69 ± 0.41 | 118.4 | 1.65 | 0.49 | 0.3891 | 9.04 |
| XorBinaryFuse8 | 10,000,000 | 42.43 ± 2.35 | 179.5 | 1.09 | 0.75 | 0.3902 | 9.02 |
| XorBinaryFuse8 | 100,000,000 | 50.48 ± 0.88 | 247.6 | 0.78 | 1.08 | 0.3901 | 9.01 |
| XorBinaryFuse8_4wise | 1,000,000 | 29.55 ± 0.67 | 136.2 | 1.7 | 0.45 | 0.3888 | 8.62 |
| XorBinaryFuse8_4wise | 10,000,000 | 43.85 ± 4.18 | 174.6 | 1.31 | 0.68 | 0.3912 | 8.61 |
| XorBinaryFuse8_4wise | 100,000,000 | 48.08 ± 1.11 | 230.1 | 1.0 | 0.92 | 0.3899 | 8.6 |
| Xor8 | 1,000,000 | 58.10 ± 3.61 | 237.2 | 1.46 | 2.1 | 0.3898 | 9.84 |
| Xor8 | 10,000,000 | 71.58 ± 0.07 | 313.0 | 1.1 | 6.67 | 0.3895 | 9.84 |
| Xor8 | 100,000,000 | 87.61 ± 3.92 | 377.2 | 0.9 | 9.45 | 0.3902 | 9.84 |
| BlockedBloom | 1,000,000 | 2.61 ± 0.72 | 10.3 | 2.81 | 0.07 | 0.9589 | 10.67 |
| BlockedBloom | 10,000,000 | 5.00 ± 2.17 | 17.9 | 1.62 | 0.15 | 0.9451 | 10.67 |
| BlockedBloom | 100,000,000 | 11.21 ± 0.96 | 57.0 | 0.51 | 1.06 | 0.9455 | 10.67 |
| Bloom12_addAll | 1,000,000 | 16.19 ± 0.22 | 82.6 | 3.78 | 0.07 | 0.3131 | 12.0 |
| Bloom12_addAll | 10,000,000 | 17.82 ± 1.00 | 89.7 | 3.48 | 0.59 | 0.3168 | 12.0 |
| Bloom12_addAll | 100,000,000 | 21.57 ± 0.34 | 111.6 | 2.8 | 1.68 | 0.3144 | 12.0 |

## Frozen go/no-go gates (evaluated at n=100M)

- HomogRibbon64_7: 256.0 cyc/key, IPC 0.64, 5.81 miss/key
- BalancedRibbon64Pack_7: 676.6 cyc/key, IPC 1.16, 6.17 miss/key
- XorBinaryFuse8: 247.6 cyc/key, IPC 0.78, 1.08 miss/key
- XorBinaryFuse8_4wise: 230.1 cyc/key, IPC 1.0, 0.92 miss/key
- Xor8: 377.2 cyc/key, IPC 0.9, 9.45 miss/key
- BlockedBloom: 57.0 cyc/key, IPC 0.51, 1.06 miss/key
- Bloom12_addAll: 111.6 cyc/key, IPC 2.8, 1.68 miss/key

Miss-bound candidates (≥0.5 miss/key): [('HomogRibbon64_7', 5.81), ('BalancedRibbon64Pack_7', 6.17), ('XorBinaryFuse8', 1.08), ('XorBinaryFuse8_4wise', 0.92), ('Xor8', 9.45), ('BlockedBloom', 1.06), ('Bloom12_addAll', 1.68)] — GO only if the missing phase is NOT already reordering-based (requires audit's code-level findings; judgment call must be logged before Phase-1 registration).
Compute-slack candidates (IPC ≤1.5, ≥60 cyc/key): [('HomogRibbon64_7', 256.0, 0.64), ('BalancedRibbon64Pack_7', 676.6, 1.16), ('XorBinaryFuse8', 247.6, 0.78), ('XorBinaryFuse8_4wise', 230.1, 1.0), ('Xor8', 377.2, 0.9)] — same caveat.
