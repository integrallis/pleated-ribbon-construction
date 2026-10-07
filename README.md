# Pleated Ribbon Construction: Approximate Sorting Recovers the Locality of a Full Sort

Research repository for the paper *"Pleated Ribbon Construction: Approximate Sorting Recovers the Locality of a Full Sort"* —
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
- **Order-independence, put to work.** For any consistent system, insertion order does not change
  the solved filter, and a homogeneous ribbon system is always consistent. Which redundant keys
  are dropped can differ by order; the filter does not. Each measured build is still compared with
  the arrival-order fingerprint and checked for false negatives; the reported outputs matched. The slot-range **parallel** build uses the same
  checks. At 16 threads its measured construction time is about one thread's Bloom insertion time
  on the i9, but that is not an equal-thread comparison: against a 16-thread Bloom build on a
  16-core machine, pleated ribbon costs about 10x as much (experiment E4, `results/e4/ANALYSIS.md`),
  because only the banding phase is parallel.
- **Portable across architectures.** Replicated on x86 Raptor Lake (AVX2), Ampere Neoverse-N1
  (NEON), and Google Axion Neoverse-V2 (SVE): pleating wins 2.05x / 2.37x / 2.72x, output
  bit-identical across all three.
- **Transfers to production RocksDB.** Patched into RocksDB's shipped Standard128 (w=128) ribbon
  builder, one counting pass before the banding call makes construction **1.78x faster** at 100M
  keys/filter, with 25x fewer banding cache misses at the same instruction count. RocksDB's tests
  pass and the measured false-positive rates match stock to six digits. A separate
  registered check (E5, `results/e5/ANALYSIS.md`) compared 443 stock and pleated filters byte by
  byte at four sizes; all were identical. In
  `db_bench` the ~2x filter-build speedup survives inside real compaction. See
  `experiments/e2_rocksdb/`.
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

## Reproduce the paper

```bash
./reproduce.sh   # integrity checks + re-derive analyses and figures from committed measurements
```

The script checks integrity, runs the Rust unit tests, re-derives the experiment analyses, and
regenerates the figures from committed raw measurements. It does not rerun the hardware
benchmarks. To rerun the experiments, use the protocols and setup notes in `experiments/` and
`harness/README.md`; E2's RocksDB version, patch, configuration, raw CSVs, and recorded commands
are documented in `experiments/e2_rocksdb/README.md`.

| Paper result | Committed raw data | Re-derivation or experiment guide |
|---|---|---|
| Probe and blocked-Bloom experiments | `results/e0a/`, `results/e1a/` | `experiments/e0_feasibility/`, `experiments/e1a_construction/` |
| Ribbon construction, x86 | `results/e1b/` | `experiments/e1b_ribbon_construction/analyze.py`, `analyze_phase1.py`, `analyze_phase1b.py` |
| Ribbon construction, ARM N1 and V2 | `results/e1b-arm-n1/`, `results/e1b-arm-v2/` | `experiments/e1b_ribbon_construction/` protocols and analysis scripts |
| RocksDB construction and compaction | `experiments/e2_rocksdb/results/sweep_fb.csv`, `dbbench_reps.csv` | `experiments/e2_rocksdb/README.md` |

See `CLAIMS.md` for each paper claim's artifact paths and status, and `INTEGRITY.md` for the
provenance and validation rules applied to measurements.

## Scope and limitations

- The order-independence argument (any consistent system; no independence condition) was drafted
  on 2026-10-06 and checked on a small independent model (`scripts/check_order_independence.py`),
  but it has not had an external reader. The measured outputs matched across the reported runs.
  The argument is in [`docs/order-independence-proof.md`](docs/order-independence-proof.md).
- BuRR is a mechanistic anchor, not a like-for-like performance baseline: it uses a bumped
  structure with tighter space overhead than the homogeneous ribbon configuration studied here.
- Timing replication covers x86 AVX2 and two ARM microarchitectures, but ARM cloud hosts do not
  expose PMU counters. The cache-miss mechanism is measured on x86 only.
- The RocksDB filter-construction gain is measured on its shipped Standard128 builder. E2 records
  passing RocksDB tests and matching false-positive rates to six digits; byte identity is shown
  only for the 443 filters compared in E5, not for all inputs. The end-to-end compaction result comes from a filter-favorable configuration
  and is directional; its whole-workload impact depends on per-SST filter size and run-to-run
  compaction variation.

## How to cite

Until the paper has an arXiv identifier or a venue, cite the repository (see `CITATION.cff`):

```bibtex
@misc{sambodden2026pleated,
  author = {Sam-Bodden, Brian},
  title  = {Pleated Ribbon Construction: Approximate Sorting Recovers the Locality of a Full Sort},
  year   = {2026},
  note   = {Research repository with raw measurements and registered protocols},
  howpublished = {\url{https://github.com/integrallis/ribbon-catches-bloom}},
}
```

The approximate-sort step for homogeneous ribbon is due to Dietzfelbinger, Dillinger, Hübschle,
Sanders and Walzer (J. ACM 73(1), 2026; arXiv:2109.01892). This work implements and measures it.

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
