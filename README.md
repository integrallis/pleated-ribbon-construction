# Pleated Ribbon Construction: Approximate Sorting Recovers the Locality of a Full Sort

Research repository for the paper *"Pleated Ribbon Construction: Approximate Sorting Recovers the Locality of a Full Sort"*:
the paper, its pre-registered experiments, and the raw artifacts every reported number derives
from. The production implementation of the technique lives in a separate crate,
[`pleat`](https://github.com/integrallis/pleat).

## What the paper shows

Ribbon filters match Bloom-filter accuracy in about 30% less memory, but they have not displaced
Bloom in practice because they cost several times more CPU to *build*, and storage engines
rebuild filters constantly as data is compacted. This paper makes homogeneous ribbon construction
about twice as fast at large sizes, which roughly halves the build-cost gap to Bloom. It does not
close it.

- **Pleating: the approximate sort, implemented and measured.** The ribbon authors' own algorithm
  for homogeneous ribbon sorts keys by start position "at least approximately" (J. ACM 2026;
  arXiv:2109.01892), but the reference implementation and RocksDB insert keys in arrival order.
  This work implements that step as one counting pass into cache-sized windows of start
  positions. It makes sequential construction **2.05–2.24x faster** at 100–400M keys and
  recovers 98% of a full sort's cache-miss reduction at about a quarter of the sort's cost.
- **Order-independence.** For a fixed hash seed and table size, and any consistent system,
  insertion order does not change the solved filter; a homogeneous ribbon system is always
  consistent. Which redundant keys are dropped can differ by order; the filter does not. Every
  measured build is still compared with the arrival-order fingerprint and checked for false
  negatives, and the reported outputs matched. A slot-range **parallel** build uses the same
  checks.
- **Portable across architectures.** Replicated on x86 Raptor Lake (AVX2), Ampere Neoverse-N1
  (NEON), and Google Axion Neoverse-V2 (SVE): pleating is 2.05x / 2.37x / 2.72x faster than the
  reference build, with matching solution fingerprints on all three. A separate Graviton4 run
  measures the mechanism on ARM: partitioning recovers 96.8% of the full sort's L2 read-miss
  reduction.
- **Transfers to RocksDB.** One counting pass in front of RocksDB's shipped Standard128 (w=128)
  ribbon builder makes filter construction **1.78x faster** at 100M keys per filter, with 25x
  fewer banding cache misses at the same instruction count. It gives almost nothing at 1M keys
  per filter (1.03x) and is 3% slower at 100K. RocksDB's tests pass, measured false-positive rates match
  stock to six digits, and a separate registered check (E5) found all 443 stock and pleated
  filters it compared byte-identical. In `db_bench`, banding inside compaction drops from 77.6 to
  44.2 ns/key, but the 9% change in whole-compaction CPU is within run-to-run variation.
- **Against Bloom, measured three ways.** The first joins existing measurements; the other two
  were registered before data, each with a "matches Bloom" hypothesis that failed.
  - Same harness, one thread, 100M keys: ribbon goes from 4.4x to 2.2x the cost of blocked Bloom.
  - RocksDB `filter_bench` at a matched false-positive rate, one thread (E3): pleated ribbon is
    2.4x Bloom at 100M keys per filter, down from 4.5x for stock.
  - Equal thread counts on a 16-core machine (E4): 4.0x at one thread and 10.1x at 16, because
    only the banding phase of the ribbon build is parallel.
- **Two null results that locate the gain.** Batched and cross-key SIMD probing do not beat
  per-key probing, and a read-free Bloom-construction scheme does not beat partitioned
  read-modify-write. Both fail for the same reason: reordering pays only where memory stalls form
  data-dependent chains. Ribbon construction has them; Bloom probing and construction do not.
  (One of these nulls is the FastLanes-style transposed-layout idea this repository was
  originally created to test; see Provenance.)

## Layout

```
paper/                        main.tex (single source), refs.bib, figures/, tables/ (generated),
                              main.pdf, main.md (generated Markdown), sea/ (generated LIPIcs build)
src/ribbon_reorder/           C++ construction driver (e1b_phase1.cc) around fastfilter_cpp's
                              UNMODIFIED homogeneous ribbon kernel, the source of the paper's
                              construction numbers; order_check.cc tests order-independence on
                              that kernel
src/lanefilter/               Rust blocked-Bloom prototype: probe strategies (E0), bulk builders
                              (E1a) and parallel builders (E4)
experiments/                  registered protocols, runners and analysis scripts:
  e0_feasibility/             probe strategies
  e1a_construction/           blocked-Bloom bulk construction
  e1b_ribbon_construction/    ribbon construction, ARM replication, Bloom-gap analysis
  e2_rocksdb/                 RocksDB patch, filter_bench and db_bench results (v10.2.0)
  e3_bloom_gap/               RocksDB Bloom vs ribbon at a matched false-positive rate
  e4_parallel_bloom/          Bloom vs pleated ribbon at equal thread counts
  e5_byte_identity/           byte-level comparison of stock and pleated RocksDB filters
  e6_memory_and_boundary/     peak memory, concurrent builds, parallel boundary fallback
harness/                      pinned third-party suites (see harness/README.md)
results/                      raw artifacts and generated analyses: e0a, e1a, e1b (x86), e1b-arm-*,
                              e3, e4, e5, e6, order-independence checks
docs/                         prior-art audits, the order-independence proof, the VPS runbook
CLAIMS.md                     the claims ledger with provenance and status (incl. refuted claims)
RESEARCH_LOG.md               dated log of hypotheses, decisions, and dead ends
INTEGRITY.md                  provenance and validation rules
scripts/                      figures, integrity checks, paper builds, remote runners
```

## Reproduce the paper

```bash
./reproduce.sh   # integrity checks + re-derive analyses and figures from committed measurements
```

The script checks integrity, runs the Rust unit tests, re-derives every experiment analysis
(E0 through E6), and regenerates the figures from committed raw measurements. It does not rerun
the hardware benchmarks. To rerun an experiment, use its protocol and runner in `experiments/`
and the setup notes in `harness/README.md`.

| Paper result | Committed raw data | Re-derivation |
|---|---|---|
| Probe and blocked-Bloom experiments | `results/e0a/`, `results/e1a/` | `experiments/e0_feasibility/analyze.py`, `experiments/e1a_construction/analyze.py` |
| Ribbon construction, x86 | `results/e1b/` | `experiments/e1b_ribbon_construction/analyze.py`, `analyze_phase1.py`, `analyze_phase1b.py`, `analyze_banding_steps.py` |
| Same-harness gap to Bloom | `results/e1b/phase0/`, `results/e1b/phase1/` | `experiments/e1b_ribbon_construction/analyze_bloom_gap.py` |
| Ribbon construction, ARM (N1, V2, Graviton4 counters) | `results/e1b-arm-n1/`, `results/e1b-arm-v2/`, `results/e1b-arm-graviton4-pmu-20260930/` | `experiments/e1b_ribbon_construction/analyze_arm.py` |
| RocksDB construction and compaction (E2) | `experiments/e2_rocksdb/results/sweep_fb.csv`, `dbbench_reps.csv` | `experiments/e2_rocksdb/analyze.py` |
| RocksDB Bloom vs ribbon (E3) | `results/e3/` | `experiments/e3_bloom_gap/analyze.py` |
| Equal-thread Bloom vs ribbon (E4) | `results/e4/` | `experiments/e4_parallel_bloom/analyze.py` |
| Byte identity in RocksDB (E5) | `results/e5/` | `experiments/e5_byte_identity/run.py --stage analyze` |
| Peak memory, concurrent builds, boundary fallback (E6) | `results/e6/` | `experiments/e6_memory_and_boundary/analyze.py` |
| Order-independence checks | `results/order_independence_*` | `scripts/check_order_independence.py`, `scripts/enumerate_order_independence.c`, `src/ribbon_reorder/order_check.cc` |

See `CLAIMS.md` for each claim's artifact paths and status, and `INTEGRITY.md` for the provenance
and validation rules applied to measurements.

To rebuild the paper: `cd paper && latexmk -pdf main.tex` (or `tectonic main.tex`).
`scripts/make_lipics.py` regenerates the LIPIcs build in `paper/sea/`, and
`scripts/make_markdown.py` regenerates `paper/main.md`; both read `paper/main.tex`.

## Scope and limitations

- The order-independence argument (any consistent system, for a fixed seed and table size) agrees
  with every measured fingerprint, with a test on the unmodified kernel using overloaded filters,
  and with an exhaustive enumeration of small systems, but it has not had an external reader. It
  is in [`docs/order-independence-proof.md`](docs/order-independence-proof.md).
- The gap to Bloom narrows but does not close. The equal-thread comparison (E4) is not matched
  on space or false-positive rate, and the ribbon build parallelizes only banding.
- BuRR is a mechanistic anchor, not a like-for-like performance baseline: it uses a bumped
  structure with tighter space overhead than the homogeneous ribbon configuration studied here,
  and bumping needs a full sort, so pleating is not claimed to transfer to it.
- The cache-miss mechanism is measured with x86 hardware counters and, separately, with one
  Neoverse-V2 event on Graviton4. The two events are not comparable in absolute terms. The N1
  and Axion timing replications ran on cloud hosts without counter access.
- The partition pass is not in place: it needs 8 bytes per key of transient memory in the
  standalone driver (measured) and 12 in the RocksDB patch. With 4 and 8 builders running at
  once it stays about 2.2x faster per process, measured on one machine with separate processes.
- The RocksDB gain is measured on its shipped Standard128 builder and appears only above about
  1M keys per filter. Byte identity with stock is shown for the 443 filters compared in E5, not
  for all inputs. The compaction result comes from one configuration that favors filters and is
  directional only.

## How to cite

Until the paper has an arXiv identifier or a venue, cite the repository (see `CITATION.cff`):

```bibtex
@misc{sambodden2026pleated,
  author = {Sam-Bodden, Brian},
  title  = {Pleated Ribbon Construction: Approximate Sorting Recovers the Locality of a Full Sort},
  year   = {2026},
  note   = {Research repository with raw measurements and registered protocols},
  howpublished = {\url{https://github.com/integrallis/pleated-ribbon-construction}},
}
```

The approximate-sort step for homogeneous ribbon is due to Dietzfelbinger, Dillinger, Hübschle,
Sanders and Walzer (J. ACM 73(1), 2026; arXiv:2109.01892). This work implements and measures it.

## Provenance

This work began as an investigation of whether the FastLanes unified transposed layout
(Afroozeh & Boncz, VLDB 2023) could accelerate approximate-membership-filter probing. A July 2026
literature sweep found no prior work connecting FastLanes-style transposition to AMQ filters; the
survey lives in `docs/`. The transposed-probe idea was then **measured and refuted** (memory-bound,
not compute-bound; see CLAIMS.md C2 and §3 of the paper), and the effort moved to the
construction-side result above. The refuted direction is kept in the ledger and research log
because the paper's argument depends on the negative result.

The project itself grew out of Bloom-filter work in the barudb LSM-tree project (Harvard CS265),
whose filter benchmarks were audited in July 2026; only claims backed by raw artifacts are carried
forward (see INTEGRITY.md).
