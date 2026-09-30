# ARM cache-miss mechanism reproduction (2026-09-30)

## Result

The cache-miss mechanism is now measured on AWS Graviton4 (Neoverse-V2). At 100M keys, the
banding-scoped Neoverse L2 read-miss counter falls from **1.770 misses/key** for arrival-order
construction to **0.058** for partitioned construction and **0.001** for LSD radix sort (medians
of three runs). Partitioning therefore recovers about **96.8%** of the L2-miss reduction achieved
by the full sort. The direction and scale agree with the paper's x86 result: 5.75 to 0.17 misses/key
for partitioning, recovering 98.3–98.4% of the full-sort reduction. These absolute counts are
architecture-specific and should not be compared one-for-one.

All three strategies had zero false negatives. For every repetition, partitioned and radix
construction produced the same solution fingerprint as the reference strategy.

## Measurements

| Strategy | Reorder ns/key | Banding ns/key | Total ns/key | Neoverse L2 read misses/key |
|---|---:|---:|---:|---:|
| Reference | 0.000 | 74.058 | 81.891 | 1.770 |
| LSD radix sort | 21.285 | 16.721 | 45.828 | 0.001 |
| Partitioned | 6.693 | 21.466 | 35.993 | 0.058 |

These are medians over three 100M-key runs. The total is reorder + banding + back-substitution.
The paper's Google Axion/Neoverse-V2 means are 93.7, 44.8, and 34.4 ns/key, respectively. The
radix and partitioned timings are within 2.3% and 4.6%; the reference measurement is 12.6% lower,
so this run's end-to-end reference-to-partitioned ratio is 2.28x versus 2.72x in the paper. The
older generic-counter timing rerun is recorded in [the initial Graviton4 run notes](../arm-graviton4-20260930.md).

## How the counter was enabled

The existing instance had an ARM PMU (`armv8_pmuv3_0`) but Linux denied access with
`kernel.perf_event_paranoid=4`, which made earlier counter fields silently zero. Setting the
runtime value to `-1` enabled user-space perf access. The generic ARM `cache-misses` event did
count, but it is not a documented DRAM-miss equivalent and is not directly comparable to the
paper's x86 measurements.

For the mechanism run, the driver measured the Neoverse-V2 PMU event `l2d_cache_lmiss_rd`
(`config=0x4009`) alone and only around the banding call. A first attempt grouped multiple raw
events with the generic event group; the pinned wrapper does not scale multiplexed counters, so
that attempt was discarded. The final driver reports unsupported generic counters as JSON `null`
on ARM and records the dedicated L2 read-miss field separately.

## Run configuration and artifacts

- AWS `r8g.2xlarge`, 8 vCPUs, 64 GiB; Ubuntu 24.04, Linux 7.0.0-1013-aws, Neoverse-V2.
- 100M deterministic keys; `window_shift=16`; eight threads; three repetitions per strategy.
- `perf_event_paranoid=-1`; the instance was stopped after the artifacts were retrieved.
- Raw output: [e1b-100M.jsonl](e1b-100M.jsonl).
- The counter instrumentation is in [`src/ribbon_reorder/e1b_phase1.cc`](../../src/ribbon_reorder/e1b_phase1.cc).

The event is specific to the Neoverse-V2 PMU. Do not interpret it as the same event on other ARM
cores; check the machine's PMU event table before using the field there.
