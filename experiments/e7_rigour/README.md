# E7: the construction results on controlled hardware, with more repetitions, named miss events, other configurations and real keys

Status: **protocol written; this file is committed before any registered run.** Smoke runs
(`E7_SMOKE=1`, shrunken sizes, results outside `results/e7`) were used to test the tooling and
are not data.

## Why

A referee-style reading of the paper (RESEARCH_LOG, 2026-10-13) found five weaknesses in how
the construction results were measured. None of them is a known error; each is a way the
numbers could be less general or less exact than the text suggests.

1. The headline numbers come from a laptop CPU with two kinds of cores (i9-14900HX). The runner
   did not pin the process and `machine.json` recorded only the CPU model and kernel, so which
   cores ran the measurements is not known. Three repetitions per cell.
2. The parallel rows have two repetitions; ARM thread scaling has one.
3. "98.3–98.4% of the miss reduction" is computed from Linux's generic cache-miss event, whose
   meaning differs by CPU, and is quoted to three digits.
4. One filter configuration (band width 64, 7 result bits, one slot overhead).
5. Synthetic 64-bit integer keys only. The partition pass recomputes the hash in each of its
   two passes, which costs more for keys that are expensive to hash.
6. The compaction result (about 9% less CPU) is within run-to-run variation at three
   repetitions.

E7 measures each point again under controlled conditions. It does not replace E1b to E6; their
results stay as recorded.

## Machines

| name | instance | role | profile |
|---|---|---|---|
| `x86-intel` | AWS c7i.metal-24xl (bare metal) | primary: every hypothesis is decided here | full |
| `arm-graviton4` | AWS c8g.metal-24xl (bare metal, Neoverse V2) | replication | replication |
| `x86-amd` | AWS c7a.metal-48xl (bare metal, Zen 4) | replication | replication |

Bare metal, so that there is no hypervisor between the benchmark and the cores and the
performance counters are the processor's own. The CPU model, microcode, kernel, compiler and
every setting below are recorded in `machine.json` by the check stage; the table above names
what was ordered, not what was verified.

After E7 the paper's headline construction numbers are the primary machine's, whatever they
are. The laptop's numbers remain in the paper as a second, uncontrolled machine.

Settings, the same on every machine:

- Ubuntu 24.04, its `g++`, `-O3 -march=native`, harnesses at the commits in `harness/PINS`.
- Single-thread runs are pinned (`taskset`) to the third physical core of NUMA node 0, with
  memory bound to node 0 (`numactl --membind=0`). Thread-scaling runs use T physical cores of
  node 0 from the third on, one thread per core. Nothing else runs on the machine.
- `performance` frequency governor where the machine has one. Turbo and SMT are left as
  shipped and recorded; the SMT sibling of a pinned core is idle.
- Transparent huge pages at the distribution default (`madvise`) except in the stage that
  varies it.
- Timing runs have no counters attached. Counter runs are separate runs.

## Stages (`run.py`; each refuses to run before its prerequisite's artifact exists)

Every stage runs its repetitions as blocks: block k runs every cell of the stage once, in an
order shuffled with a fixed seed and recorded, so that slow drift does not favour a cell.

| stage | driver | cells | repetitions |
|---|---|---|---|
| `check` | | binaries newer than their source, root, counters readable, governor, core count, THP default; resolves the named events | |
| `crosscheck` | both | `e7_driver` against `e1b_phase1` at 10M and 100M keys, three strategies | 3 |
| `main` | `e1b_phase1`, unchanged | 10M, 100M, 400M keys × reference, no-prefetch, std::sort, LSD radix, ips2ra, partitioned | 10 |
| `parallel` | `e1b_phase1`, unchanged | 100M keys; parallel build at 1, 2, 4, 8, 16 threads; sequential partitioned | 10 |
| `counters` | `e7_driver` | 100M and 400M keys × reference, LSD radix, ips2ra, partitioned × {generic events, named events} | 5 |
| `config` | `e7_driver` | 100M keys × reference, ips2ra, partitioned × eight configurations (below) | 5 |
| `keys` | `e7_driver` | 100M keys (90M for one set) × reference, ips2ra, partitioned × nine key sets (below) | 5 |
| `thp` | `e7_driver` | 100M keys × reference, ips2ra, partitioned × THP `madvise`, `always`, `never` | 5 |
| `compaction` | RocksDB `db_bench` | stock and pleated at 256 MiB SST target (20 repetitions), and at 64 MiB and 1 GiB (5 each) | 20 / 5 |

The replication profile is `check`, `crosscheck`, `main`, `parallel`, `counters`.

**New code and its cross-check.** `main` and `parallel` use the driver of E1b unchanged.
`src/ribbon_reorder/e7_driver.cc` is new: the same strategies around the same unmodified kernel,
with band width and result bits as compile-time parameters, the slot overhead as an argument,
keys from files, and named raw events. Before any of its numbers are used, `crosscheck` requires,
for band width 64, 7 result bits, synthetic keys and the default overhead, that it produces the
same solution fingerprint and measured false-positive rate as `e1b_phase1` in every run, and
that its median total is within 5% of `e1b_phase1`'s for the reference and partitioned builds
and within 10% for the sort. If it fails, no stage that uses `e7_driver` runs.

**Configurations** (`config`): band width 64 and 128, each with 7, 8 and 16 result bits, at the
reference suite's sizing rule for homogeneous ribbon (`1 + (4 + r/4)/w` slots per key); and
band width 64 with 7 result bits at 1.05 and 1.15 slots per key. The partition window is 2^16
slots at band width 64 and 2^15 at 128 (a slot's banding state is 12 and 20 bytes).

**Key sets** (`keys`; prepared by `prepare_keys.py`, which records sources, counts and
checksums in `keys/manifest.json`):

- `sosd_fb`, `sosd_osm`, `sosd_wiki`: 100M distinct 64-bit keys sampled (fixed seed) from the
  200M-key Facebook user-id, OpenStreetMap cell-id and Wikipedia edit-timestamp sets of the SOSD
  benchmark (Harvard Dataverse, doi:10.7910/DVN/JGVF9A), in ascending order as distributed. A
  set with fewer than 100M distinct keys gives the largest multiple of 10M that it has. The
  smoke run found 90,437,011 distinct keys in the Wikipedia set, so that set is measured at 90M.
- `cc_hosts`: the first 100M host names of Common Crawl's host-level web graph, release
  `cc-main-2025-mar-apr-may`, in the release's order.
- `synth16`, `synth64`: 100M distinct random strings of 16 and of 64 bytes.

String sets are measured two ways. *Hashed once*: each string is hashed to 64 bits with XXH3,
timed as its own phase and counted in the total, and construction then proceeds on the 64-bit
values; this is what RocksDB does. *Direct*: the filter's key is the string and its hash
function is XXH3 over the bytes, so the hash is recomputed in each partition pass and again in
banding, and reordering permutes references to strings that stay where they are.

**Named events** (`counters`), resolved on the machine by the check stage and recorded with
their raw codes; an event the machine lacks is recorded as missing:

- Intel: `mem_load_retired.l2_miss`, `mem_load_retired.l3_miss`,
  `dtlb_load_misses.walk_completed`. These count retired load instructions, not cache lines.
- Arm: `l2d_cache_lmiss_rd`, `ll_cache_miss_rd`, `dtlb_walk`.
- AMD: `l2_cache_req_stat.dc_access_in_l2`, `l2_cache_req_stat.ic_dc_miss_in_l2`,
  `ls_dmnd_fills_from_sys.dram_io_near`, `ls_l1_d_tlb_miss.all`.

**Compaction.** RocksDB at the E2 pin with the E2 patch, `db_bench`
`fillrandom,waitforcompaction,stats`, 30M keys of 16 bytes with 8-byte values, ribbon filter at
10 bits per key, no compression, 128 MiB write buffer, WAL off, one writer thread, statistics
on, database on tmpfs, pinned to four cores. Stock and pleated are the same binary with
`PLEAT_RIBBON` unset or set, run alternately in a recorded random order. Measured: the
`rocksdb.compaction.total.time.cpu_micros` ticker. Differences from E2's compaction run: E2's
command line was not recorded and this one is rebuilt from its description; the database is on
tmpfs; the time spent in banding inside compaction is not measured, because the committed patch
has no timer for it.

## Statistics

A cell's value is the **median** of its repetitions, reported with the minimum and maximum. A
speedup is a **ratio of medians** with a 95% percentile bootstrap interval: 10,000 resamples,
fixed seed, each arm's repetitions resampled independently. Miss recovery is
`(reference − partitioned) / (reference − best sort)` on medians, with the same bootstrap, where
the best sort is the sort with the fewest misses. No repetition is dropped.

## Hypotheses and decision rules

Decided on the primary machine. The same rules are evaluated on the replication machines and
reported beside them, labelled as replication.

- **H1 (headline).** At 100M and at 400M keys, the reference build's median total is at least
  1.5 times the partitioned build's, and the interval's lower end is above 1.
- **H1b.** At 100M and at 400M keys, the partitioned build's median total is below that of
  every full sort, with the interval of the ratio to the best sort excluding 1.
- **H2 (miss recovery).** At 100M and at 400M keys, partitioning recovers at least 90% of the
  best sort's reduction in the machine's L2-miss event (`mem_load_retired.l2_miss` on Intel,
  `l2d_cache_lmiss_rd` on Arm, `l2_cache_req_stat.ic_dc_miss_in_l2` on AMD). Recovery on the generic event and on the other named events is
  reported without a threshold. If the L2-miss event cannot be resolved, H2 is undecided.
- **H3 (configurations).** In each of the eight configurations, the reference build's median
  total is at least 1.3 times the partitioned build's.
- **H4 (keys).** For the three SOSD sets and for each string set hashed once, the reference
  build's median total, hashing included, is at least 1.5 times the partitioned build's. The
  direct variants are reported without a threshold. Expectation, not a rule: direct gains less,
  because banding then reads strings in an order that follows the table, not the string storage.
- **H5 (compaction).** At the 256 MiB target, the pleated arm's median compaction CPU is below
  the stock arm's and the interval of their ratio excludes 1.
- **H6 (parallel).** At 16 threads, parallel banding is at least 3 times as fast as sequential
  partitioned banding (median banding time), as registered in E1b.

Transparent huge pages have no hypothesis. The stage reports the reference-to-partitioned ratio
under each setting, so that a reader can see how much of the gain depends on the page size.

Checks on every run, any failure of which is reported as a failure of the run and not of a
hypothesis: zero false negatives (the driver exits nonzero); within a stage, repetition and
configuration, every strategy has the same solution fingerprint; bits per key at least
`log2(1 / measured false-positive rate)`.

## What each outcome does to the paper

- H1 holds: the abstract's construction numbers are replaced by the primary machine's. H1
  fails: the claim of a twofold gain is withdrawn to "on the laptop measured"; the abstract
  states the primary machine's ratio.
- H1b fails at a size: the paper says the partition is not faster than a full sort at that size.
- H2 holds: the paper states recovery on the named event, to two digits, with its interval. H2
  fails or is undecided: the "98%" sentence is removed, and what was measured is stated.
- H3, H4: every cell is tabulated. Cells below the threshold are named as limits of the
  technique in the text, not only in the table.
- H5 holds: the compaction sentence states the measured reduction with its interval. H5 fails:
  it says no effect on total compaction CPU was measurable in this configuration.
- H6 fails: the parallel claim is restated with the measured ratio.

## Kill criteria

- `crosscheck` fails: no number from `e7_driver` is used.
- A stage that aborts is reported as aborted and none of its cells is used. It may be run again
  in full on a fresh machine of the same type after the cause is written in the research log.
- No stage is run again because its result was unfavourable, and no cell, repetition or
  threshold above changes after this file is committed. Anything that has to change is an
  amendment, written and committed before the run it affects.

## Artifacts

`results/e7/<machine>/`: `machine.json`, `check.json`, `crosscheck.json`, `raw/<stage>/` (one
JSON per run, the run order, and for compaction the full `db_bench` output),
`keys/manifest.json`, the logs, and `ANALYSIS.md` generated by `analyze.py`. The prepared key
files (several gigabytes) are not committed; the manifest gives their sources and checksums and
`prepare_keys.py` rebuilds them.
