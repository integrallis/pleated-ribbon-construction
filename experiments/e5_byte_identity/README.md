# E5 — Are pleated and stock RocksDB ribbon filters byte-identical?

**Status: protocol complete 2026-10-06, awaiting freeze (the author's commit). No data
collected.** Nothing in this directory is a result.

## Question

E2 shows that pleating RocksDB's Standard128 builder leaves the measured false-positive rate
unchanged to six digits, and the paper says plainly that this does not establish byte-for-byte
identity of the filters. E5 checks identity directly: build the same filters with and without
the pleat pass and compare the bytes.

## Method

- RocksDB v10.2.0, commit `31b239747`, with `../e2_rocksdb/pleat-rocksdb.patch` and, on top,
  `dump-filters.patch` (this directory). The second patch adds one block to
  `Standard128RibbonBitsBuilder::Finish`: if `PLEAT_DUMP_DIR` is set, each finished ribbon
  filter (solution bytes and metadata, exactly the bytes RocksDB would store) is written to
  `filter_<sequence>.bin` in build order. Without the variable the block is inert. It does not
  touch banding, the pleat pass or back-substitution.
- `filter_bench -impl 2 -quick -net_includes_hashing`, default seed, at 100K, 1M, 10M and 100M
  keys per filter with E2's `-m_keys_total_max` rule. `filter_bench` seeds its key generator
  from `-seed`, so repeated runs build the same filters from the same keys.
- Three runs per size: `stock_a`, `stock_b` (both without `PLEAT_RIBBON`) and `pleated`
  (`PLEAT_RIBBON=1`).
- On the box, each dumped file's length and SHA-256 are recorded, and the files of each pair
  of runs are also compared byte by byte (`filecmp.cmp(shallow=False)`). The dumps themselves
  are deleted after comparison; the per-file digest lists are the committed artifacts.

## Hypothesis (registered before data collection)

- **H-E5:** at every size, `pleated` produces the same number of filters as `stock_a`, and
  every filter is byte-identical to its `stock_a` counterpart. Expected to hold: a standard
  ribbon build succeeds only when no inserted row is dependent, which is the case the
  order-independence proposition covers, and a failed seed fails in every order.

## Decision rule

- **Control first.** `stock_a` and `stock_b` must be identical at every size. If they are not,
  the harness is not deterministic and the experiment is void: no identity claim either way.
- If H-E5 holds, the paper may say that stock and pleated Standard128 filters were
  byte-identical for every filter built in this experiment (stating the sizes and the filter
  count), and the E2 wording "does not establish byte-for-byte identity" is replaced by a
  pointer to E5. The claim is for these configurations, not a proof for all inputs.
- If H-E5 fails, the paper reports how many filters differed and at which sizes, keeps E2's
  current wording, and the cause is investigated before any further claim. A difference is a
  result, not something to tune away.
- Small filters below the pleat threshold (4096 keys in the E2 patch) take the stock path; no
  size in this protocol is below it, and the analysis reports the filter counts so that is
  visible.

## Stages (each refuses to run before its prerequisite artifact exists)

1. `run.py --stage check --rocksdb <path>` — pinned commit, both patches applied, binary built
   after the patched source, dump code present in the binary; writes `results/e5/machine.json`
   and `check.json`.
2. `run.py --stage run --rocksdb <path>` — the twelve runs; writes
   `results/e5/<size>_<run>.sha256` and `results/e5/compare.json`.
3. `run.py --stage analyze` — writes `results/e5/ANALYSIS.md`.

`scripts/e5_remote.sh <host>` builds on the box, runs stages 1–2 and pulls `results/e5/` back.
Timing is irrelevant here, so any x86-64 Linux box with enough memory for a 100M-key filter
and about 2 GB of scratch disk will do; the machine is recorded.

The dump patch was checked to apply cleanly to the E2-patched source tree. It has not been
compiled or run.
