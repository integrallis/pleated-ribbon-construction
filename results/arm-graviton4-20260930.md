# Graviton4 benchmark rerun (2026-09-30)

The source was `main` at `2a352a2`. The rebuilt paper is [main.pdf](../paper/main.pdf).

## Run setup

- E1b phase 0 and the 10M/100M E1b phase 1 cases ran on AWS `c8g.2xlarge` (8 vCPUs, 16 GiB).
- The 400M E1b phase 1 cases needed more memory, so the same VPS was resized to `r8g.2xlarge` (8 vCPUs, 64 GiB). The 100M parallel cases and E0 suite ran after the resize.
- The instance is stopped. Raw artifacts and derived analyses are in [E1b results](e1b-arm-graviton4-20260930/) and [E0 results](e0a-arm-graviton4-20260930/).

## Paper comparison at 100M keys

The paper's Neoverse-V2 rows report 93.7 ns/key for reference, 44.8 for the best full sort, and 34.4 for partitioned construction. This run measured 87.76 ± 1.17, 46.21 ± 0.09 (radix, best full sort), and 35.92 ± 0.05 ns/key, respectively. The measured times are within 3–6% of the paper's values.

At 400M, the Graviton4 reference and partitioned totals were 99.54 and 37.18 ns/key (2.68×). Separately, the paper reports a 2.72× reference-to-partitioned speedup at 100M on Neoverse V2.

## Counter and correctness notes

The initial runs on this instance had `kernel.perf_event_paranoid=4`; generic cycle and
cache-miss fields were zero. A follow-up enabled user-space PMU access and directly measured the
Neoverse-V2 L2 read-miss mechanism. See the [PMU-enabled reproduction report](e1b-arm-graviton4-pmu-20260930/REPORT.md)
and its raw JSON. The E1b fingerprints matched across strategies and all runs had zero false
negatives. The E0 analysis and raw Criterion samples are in its results directory.
