generated-by: experiments/e1b_ribbon_construction/analyze.py over results/e1b/phase0/ (machine: , aarch64)

# E1b Phase-0 analysis (derived — do not hand-edit)

## Construction cost (add-phase; mean over reps, ± half-range)

| algorithm | n | add ns/key | cycles/key | IPC | misses/key | FPR% | bits/key |
|---|---|---|---|---|---|---|---|
| HomogRibbon64_7 | 1,000,000 | 58.02 ± 0.83 | — | — | — | 0.9297 | 7.63 |
| HomogRibbon64_7 | 10,000,000 | 78.13 ± 0.54 | — | — | — | 0.8085 | 7.63 |
| HomogRibbon64_7 | 100,000,000 | 90.35 ± 0.98 | — | — | — | 0.8142 | 7.63 |
| BalancedRibbon64Pack_7 | 1,000,000 | 124.94 ± 1.53 | — | — | — | 0.7842 | 7.05 |
| BalancedRibbon64Pack_7 | 10,000,000 | 125.06 ± 0.82 | — | — | — | 0.7816 | 7.05 |
| BalancedRibbon64Pack_7 | 100,000,000 | 170.31 ± 0.41 | — | — | — | 0.7777 | 7.04 |
| XorBinaryFuse8 | 1,000,000 | 35.04 ± 0.42 | — | — | — | 0.3932 | 9.04 |
| XorBinaryFuse8 | 10,000,000 | 50.96 ± 0.29 | — | — | — | 0.393 | 9.02 |
| XorBinaryFuse8 | 100,000,000 | 104.83 ± 0.26 | — | — | — | 0.3916 | 9.01 |
| XorBinaryFuse8_4wise | 1,000,000 | 38.49 ± 0.41 | — | — | — | 0.397 | 8.62 |
| XorBinaryFuse8_4wise | 10,000,000 | 47.83 ± 0.32 | — | — | — | 0.3909 | 8.61 |
| XorBinaryFuse8_4wise | 100,000,000 | 74.69 ± 1.46 | — | — | — | 0.3924 | 8.6 |
| Xor8 | 1,000,000 | 78.68 ± 0.98 | — | — | — | 0.391 | 9.84 |
| Xor8 | 10,000,000 | 84.04 ± 1.55 | — | — | — | 0.3935 | 9.84 |
| Xor8 | 100,000,000 | 98.19 ± 0.49 | — | — | — | 0.3912 | 9.84 |
| BlockedBloom | 1,000,000 | 3.01 ± 0.08 | — | — | — | 0.6318 | 12.8 |
| BlockedBloom | 10,000,000 | 11.87 ± 0.19 | — | — | — | 0.6373 | 12.8 |
| BlockedBloom | 100,000,000 | 13.17 ± 0.07 | — | — | — | 0.633 | 12.8 |
| Bloom12_addAll | 1,000,000 | 19.39 ± 0.07 | — | — | — | 0.3198 | 12.0 |
| Bloom12_addAll | 10,000,000 | 25.18 ± 0.11 | — | — | — | 0.3146 | 12.0 |
| Bloom12_addAll | 100,000,000 | 32.61 ± 0.07 | — | — | — | 0.3155 | 12.0 |

## Frozen go/no-go gates (evaluated at n=100M)

- HomogRibbon64_7: ? cyc/key, IPC ?, ? miss/key
- BalancedRibbon64Pack_7: ? cyc/key, IPC ?, ? miss/key
- XorBinaryFuse8: ? cyc/key, IPC ?, ? miss/key
- XorBinaryFuse8_4wise: ? cyc/key, IPC ?, ? miss/key
- Xor8: ? cyc/key, IPC ?, ? miss/key
- BlockedBloom: ? cyc/key, IPC ?, ? miss/key
- Bloom12_addAll: ? cyc/key, IPC ?, ? miss/key

NO-GO: no gate met — E1b terminates as the third null per protocol.
