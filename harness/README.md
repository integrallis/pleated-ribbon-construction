# Third-party benchmark harnesses (framework-first policy)

These are pinned clones of established, paper-grade frameworks. They are .gitignored; this file
records exact commits so any machine (including the VPS) can reproduce the setup with
`./setup_harnesses.sh`.

| harness | upstream | used by | role here |
|---|---|---|---|
| fastfilter_cpp | https://github.com/FastFilter/fastfilter_cpp | xor filter (JEA 2020), binary fuse (JEA 2022), BuRR (SEA 2022), prefix filter (PVLDB 2022) | canonical cross-filter comparison: all filter-vs-filter numbers |
| FastLanes | https://github.com/cwida/FastLanes | FastLanes (PVLDB 2023) | ground truth for the transposed layout; do not re-derive from paper text |

Pinned commits: see `PINS` (written by setup_harnesses.sh on first clone; update deliberately,
never silently).

Rust-side baselines come from crates.io (pinned in Cargo.lock): `fastbloom` (used in barudb's
benchmarks and widely deployed), `sbbf-rs` / `parquet`'s split-block Bloom (the productionized
SIMD filter design, Apache Parquet spec).

Policy: new benchmark code is written only where no harness covers the question
(e.g., our own prototype's kernels), and its numbers are used only after cross-validating an
overlapping configuration against fastfilter_cpp on the same machine.
