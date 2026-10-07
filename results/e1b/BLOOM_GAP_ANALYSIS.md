generated-by: experiments/e1b_ribbon_construction/analyze_bloom_gap.py over results/e1b/phase0/, results/e1b/phase1/, results/e1a/criterion/construct_100M/ (machine: Intel(R) Core(TM) i9-14900HX, x86_64)

# Bloom-vs-ribbon construction gap at 100M keys (derived — do not hand-edit)

Single thread, same machine. Rows come from three existing artifact sets and two
harnesses; space and false-positive rate are not matched across rows.

| build | harness | ns/key (mean ± sd) | FPR% | bits/key | x fastfilter BlockedBloom | x fastest Bloom build |
|---|---|---|---|---|---|---|
| blocked Bloom, per-key | fastfilter_cpp | 11.21 ± 1.08 | 0.9428 | 10.67 | 1.00 | 1.52 |
| Bloom (12 bits/key), addAll | fastfilter_cpp | 21.57 ± 0.34 | 0.3148 | 12.00 | 1.92 | 2.93 |
| blocked Bloom, per-key | ours (Criterion) | 12.12 ± 0.16 | 1.2660* | 10.00 | 1.08 | 1.65 |
| blocked Bloom, prefetch-pipelined | ours (Criterion) | 7.35 ± 0.13 | 1.2660* | 10.00 | 0.66 | 1.00 |
| blocked Bloom, partitioned | ours (Criterion) | 7.69 ± 0.10 | 1.2660* | 10.00 | 0.69 | 1.05 |
| homogeneous ribbon, reference | fastfilter_cpp kernel | 49.58 ± 1.43 | 0.8202 | 7.63 | 4.42 | 6.74 |
| homogeneous ribbon, pleated | fastfilter_cpp kernel | 24.17 ± 0.21 | 0.8202 | 7.63 | 2.16 | 3.29 |

\* FPR and bits/key of the prototype rows are the E0 measurement at 1,000,000 keys (results/e0a/summary.json, same SBBF geometry); not re-measured at 100M.

Fastest measured Bloom build: `pf` at 7.35 ns/key.

## Same-harness pair (the comparison to lead with)

- fastfilter_cpp BlockedBloom vs homogeneous ribbon, same harness, same machine: FPR 0.94% vs 0.82%; ribbon uses 28.5% fewer bits/key (7.63 vs 10.67).
- Earlier single BlockedBloom run behind CLAIMS C9: 11.48 ns/key; Phase-0 3-rep range 10.54-12.46 -> inside the range.

## Gap before and after pleating

- vs fastfilter BlockedBloom (per-key): reference ribbon 4.42x, pleated ribbon 2.16x
- vs fastest measured Bloom build: reference ribbon 6.74x, pleated ribbon 3.29x

## Scope and caveats

- Ribbon rows are reorder + banding + back-substitution from the Phase-1 driver; Bloom
  fastfilter rows are the harness's add phase; Criterion rows are whole-build time / n.
- Criterion rows: our Rust SBBF prototype in a different harness and language. Its FPR is
  higher than both fastfilter BlockedBloom and the ribbon, so the fastest-Bloom ratio compares
  against a weaker filter. A production Bloom build with construction prefetch at matched
  FPR is measured separately in E3 (results/e3/ANALYSIS.md, CLAIMS C26), on another machine.
  Only the same-harness rows go into the paper table.
- Parallel Bloom builds are measured separately in E4 (results/e4/ANALYSIS.md, CLAIMS C27),
  on another machine. The 16-thread ribbon total (CLAIMS C23) is not in this table.
- Not an equal-space or equal-FPR comparison.
