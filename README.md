# Ribbon Catches Bloom: Pleated Construction at Bloom Speed

Research repository for the paper *"Ribbon Catches Bloom: Pleated Construction at Bloom Speed"* —
the paper, its pre-registered experiments, and the raw artifacts every reported number derives
from. The production implementation of the technique lives in a separate crate,
[`pleat`](https://github.com/integrallis/pleat).

## What the paper shows

Ribbon filters match Bloom-filter accuracy in far less memory, but they have not displaced Bloom
in practice because they cost several times more CPU to *build* — and storage engines rebuild
filters constantly as data is compacted. This paper closes most of that gap for homogeneous
ribbon filters.

- **Pleating (partition-instead-of-sort).** A single counting pass groups keys into cache-sized
  start-windows before banding — a weaker, ~4x cheaper form of the full start-position sort used
  in prior work. It makes sequential construction **2.05–2.24x faster** at 100–400M keys and
  recovers 98% of the sort's miss reduction.
- **Order-independence, put to work.** The solved filter is bit-for-bit identical regardless of
  insertion order (proved for linearly independent rows, verified by a solution fingerprint on
  every run). So any reordering — including a slot-range **parallel** build — can verify its own
  correctness with a single checksum. 16 threads build a ribbon filter about as fast as one thread
  inserts into a Bloom filter.
- **Portable across architectures.** Replicated on x86 Raptor Lake (AVX2), Ampere Neoverse-N1
  (NEON), and Google Axion Neoverse-V2 (SVE): pleating wins 2.05x / 2.37x / 2.72x, output
  bit-identical across all three.
- **Transfers to production RocksDB, unchanged.** Patched into RocksDB's shipped Standard128
  (w=128) ribbon builder, one counting pass before the banding call makes construction **1.78x
  faster** at 100M keys/filter with a **bit-for-bit identical** filter (RocksDB's own tests pass,
  FPR unchanged) — 25x fewer banding cache-misses at the same instruction count. In `db_bench`
  the ~2x filter-build speedup survives inside real compaction. See `experiments/e2_rocksdb/`.
- **Two null results that locate the win.** Batched / cross-key SIMD probing does not beat plain
  per-key probing, and a read-free Bloom-construction scheme does not beat partitioned
  read-modify-write. Both fail for the same reason, which becomes the paper's one mechanical rule:
  *layout optimization pays only where memory stalls form data-dependent chains* — ribbon
  construction has them, Bloom probing and construction do not. (One of these nulls is the
  FastLanes-style transposed-layout idea this repository was originally created to test; see
  Provenance.)

## Layout

```
paper/                        the paper (main.tex), figures, refs, self-contained NeurIPS template
src/ribbon_reorder/           C++ construction harness (e1b_phase1.cc) around fastfilter_cpp's
                              UNMODIFIED homogeneous ribbon kernel — the source of the paper's
                              construction numbers
src/lanefilter/               Rust prototype for the probe-side experiments (E0/E1a nulls)
experiments/                  pre-registered protocols + analysis scripts (e0_feasibility,
  e1a_*, e1b_ribbon_construction,   e1a bulk-construction, e1b ribbon construction);
  e2_rocksdb)                 e2_rocksdb: the RocksDB integration (patch + filter_bench/db_bench
                              results + repro commands, RocksDB v10.2.0)
harness/                      pinned third-party suites: fastfilter_cpp (xor/binary-fuse/BuRR),
                              BuRR/ips2ra, FastLanes reference (see harness/README.md)
results/                      raw artifacts: e1b (x86), e1b-arm-n1, e1b-arm-v2, e0a, e1a — every
                              reported number derives from files here
CLAIMS.md                     the claims ledger with provenance and status (incl. refuted claims)
RESEARCH_LOG.md               dated log of hypotheses, decisions, and dead ends
INTEGRITY.md                  fabrication/hallucination-check protocol
scripts/                      analysis, figure generation, integrity checks
```

## Reproduce

```bash
./reproduce.sh   # unit tests + re-derive all analyses from committed raw artifacts + integrity checks
```

Construction results (Table 1/2, Figures 2/3) come from `src/ribbon_reorder/e1b_phase1.cc`;
`experiments/e1b_ribbon_construction/analyze_phase1.py` re-derives the per-phase means and
standard deviations from `results/e1b*/`. The RocksDB results (Table 3, Figure 4) come from
`experiments/e2_rocksdb/` — apply `pleat-rocksdb.patch` to RocksDB v10.2.0 and run the
`filter_bench`/`db_bench` commands in its README; raw CSVs and the figure generator are committed.

## Provenance

This work began as an investigation of whether the FastLanes unified transposed layout
(Afroozeh & Boncz, VLDB 2023) could accelerate approximate-membership-filter probing. A July 2026
literature sweep found no prior work connecting FastLanes-style transposition to AMQ filters; the
survey lives in `docs/`. The transposed-probe idea was then **measured and refuted** (memory-bound,
not compute-bound — see CLAIMS.md C2 and §3 of the paper), and the effort pivoted to the
construction-side win above. The refuted direction is preserved in the ledger and research log
rather than erased, because the negative result is load-bearing for the paper's argument.

The project itself grew out of Bloom-filter work in the barudb LSM-tree project (Harvard CS265),
whose filter benchmarks were audited in July 2026; only claims backed by raw artifacts are carried
forward (see INTEGRITY.md).
