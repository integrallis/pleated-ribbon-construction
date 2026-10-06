# E3 — Bloom vs ribbon build cost at matched false-positive rate, in RocksDB's own harness

**Status: protocol complete 2026-10-06, awaiting freeze (the author's commit). No data
collected.** Nothing in this directory is a result. Stage A must not be run before this file,
`run.py` and `analyze.py` are committed. Stage B is a design sketch only.

## Why this experiment exists

The matched table in the paper (`results/e1b/BLOOM_GAP_ANALYSIS.md`, CLAIMS C25) is joined from
existing artifacts and carries three limits that no script can remove:

1. **Quality is not matched.** The fastest Bloom build we measured is our own Rust prototype,
   which has a higher false-positive rate (1.27% at 10 bits/key, measured at 1M keys) than both
   fastfilter_cpp BlockedBloom (0.94%) and the ribbon (0.82%).
2. **Two harnesses.** That prototype runs under Criterion; the ribbon and BlockedBloom rows run
   under fastfilter_cpp. They overlap on one configuration only.
3. **No equal-thread comparison.** The 16-thread ribbon total (C23) has no parallel Bloom
   counterpart.

E3 Stage A removes 1 and 2 with an established harness and no new benchmark code. Stage B would
remove 3 and does need new code.

## Stage A — filter_bench: FastLocalBloom vs Standard128 ribbon (stock and pleated)

RocksDB's `filter_bench` builds both of its production filters from the same key stream at the
same configured bits/key, and RocksDB sizes its ribbon to the false-positive rate of the Bloom
filter at that setting. Its Bloom builder ships its own construction prefetch. So one harness
gives a production Bloom baseline, at matched target FPR, against the exact ribbon builder E2
already measured.

### Hypotheses (registered before data collection)

- **H-E3-1 (descriptive, expected):** at ≥10M keys/filter, pleated Standard128 build cost is
  lower than stock by the factor E2 measured, and remains **more than 1.5× the FastLocalBloom
  build cost**. Prior: RocksDB's blog reports ribbon at about 4× Bloom's build CPU.
- **H-E3-2 (the claim gate):** pleated Standard128 build cost is **≤ 1.25× FastLocalBloom** at
  100M keys/filter. We expect this to FAIL.

### Decision rule

- The paper reports the three build costs and the two ratios (stock/Bloom, pleated/Bloom) at
  every size, whatever they are, with the measured FP rate of each arm.
- Wording such as "matches", "catches" or "at Bloom speed" may be used for single-thread
  construction **only if H-E3-2 holds**. Otherwise the paper says "narrows the gap from X× to
  Y×" with the measured X and Y. The decision is made by `analyze.py` from the raw CSV.
- **Kill criterion for the comparison itself:** if the Bloom and ribbon arms' measured FP rates
  differ by more than 10% relative at any size, that size is reported as "not FPR-matched" and
  excluded from the ratio claim. No retuning of bits/key after seeing data.

### Setup

- RocksDB v10.2.0, commit `31b239747`, with `../e2_rocksdb/pleat-rocksdb.patch`, built exactly
  as in E2 (same gates: patched object rebuilt, `PLEAT_PROFILE banding` marker present).
- Machine: a Hetzner CCX33 (8 dedicated x86 vCPUs, 32 GB), named `rcb-bench-e3`, labeled
  `project=ribbon-catches-bloom` (author's decision 2026-10-06: run on a VPS). This is **not**
  the i9-14900HX box E2 ran on. All three arms run there in one session; the result is labeled
  with that machine and E2's numbers are not mixed into its table. It is virtualized: the CPU
  model, core count and `systemd-detect-virt` output are recorded in `machine.json`.
- `filter_bench` flags as in E2 (`-net_includes_hashing -quick`, `-m_keys_total_max` rule from
  E2). `-impl` values read from `util/filter_bench.cc` at the pinned commit on 2026-10-06:
  "0 = legacy full Bloom filter, 1 = format_version 5 Bloom filter, 2 = Ribbon128 filter".
  Bloom arm = `-impl 1`; both ribbon arms = `-impl 2`. The `check` stage re-confirms this text
  against the built binary's `-help`. `-bits_per_key` is left at the harness default (10.0)
  for all arms; the bits/key actually stored is recorded per run.
- Build: `make DEBUG_LEVEL=0 filter_bench` with RocksDB's default flags on that machine; the
  build log is pulled back with the results. No CPU pinning (as E2).
- Sizes: 100K, 1M, 10M, 100M keys/filter (E2's table sizes). 3 repetitions. Arms interleaved
  within each repetition (Bloom, stock, pleated) so drift affects all three alike.
- Recorded per run: build ns/key ("Build avg ns/key": AddKey + Finish, hashing included), the
  measured "Average FP rate %", "Bits/key stored", total filter size, and the full raw stdout.

### Stages (each refuses to run before its prerequisite artifact exists)

1. `run.py --stage check` — build gates above plus the `-impl` help-text check; writes
   `results/e3/machine.json` and `check.json`.
2. `run.py --stage bench` — refuses without a passing `check.json`, and refuses to overwrite an
   existing sweep. Writes `results/e3/raw/<size>_<arm>_rep<r>.txt` and `results/e3/sweep_fb.csv`.
   Any failed `filter_bench` invocation aborts the stage with no CSV written.
3. `run.py --stage analyze` (`analyze.py`) — writes `results/e3/ANALYSIS.md` (generated-by
   header), evaluates the FPR-match criterion, the stock-vs-pleated FP gate and H-E3-1/2
   mechanically, and emits `paper/tables/e3_bloom_gap.tex`.

`scripts/e3_remote.sh <host>` builds RocksDB at the pin with the E2 patch on the box, runs
`check` and `bench` there and pulls `results/e3/` back; `analyze` runs locally.

The parser and analysis were exercised once on synthetic text outside the repository (never
written to `results/`); no real `filter_bench` output has been produced under this protocol.

One addition to the decision rule, fixed here before any data: H-E3-1 and H-E3-2 are evaluated
only on sizes that pass the FPR-match criterion; if 100M fails it, H-E3-2 is reported as not
evaluable, not as failed or passed.

## Stage B — equal-thread parallel Bloom (NOT STARTED; design sketch only)

Needs a parallel Bloom builder, which no pinned harness provides, so by the framework-first
policy it must be cross-validated against fastfilter_cpp BlockedBloom at one thread before any
of its numbers are used. Bloom insertion is order-free (OR is commutative), so the build can be
gated on bit-identical output with the sequential build, as E1a was. This stage gets its own
registration and is out of scope until Stage A is done.

## What would change in the paper

Stage A replaces the "fastest Bloom" row of the current table (our prototype) with a production
Bloom build at matched FPR, or sits beside it. The current table and its caveats stay as they
are until E3 data exists.
