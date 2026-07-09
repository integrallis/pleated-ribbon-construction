# E1b — ribbon / binary-fuse construction: characterize, then (maybe) optimize

**Status: Phase 0 FROZEN (2026-07-09). Phase 1 is deliberately UNREGISTERED — its hypotheses
may only be registered from Phase 0 evidence plus the E1b prior-art audit, as a documented
amendment. This two-stage structure is the direct lesson of E1a, whose hypotheses were derived
from a cost model that missed the L2-hit interaction and died on contact with data.**

## Motivation (measured + literature)

Space-optimal static filters trade construction CPU for space: RocksDB reports ~140 ns/key for
ribbon vs ~32 ns/key for Bloom and gates ribbon adoption on exactly this (filter rebuild on
every flush/compaction). The E0/E1a results on this machine say: probe-side layout work is
dead (MSHR-bound), blocked-Bloom construction misses are prefetch-hidable, partitioning caps
at ~1.7×, and post-reorder read-elimination is worthless because reordering already converts
the target misses into L2 hits. E1b asks whether ribbon/fuse construction — structurally
different work: banded row reduction + back-substitution (ribbon), counter-scatter + peel +
assign (fuse) — contains a bottleneck that is (a) real at scale and (b) NOT already addressed
by the reordering that BuRR (IPS2Ra bucket sort) and binary fuse (single-pass segment sort)
already ship. If no such target exists, that null completes the measurement-study arc.

## Phase 0 — characterization (this freeze; descriptive, no novelty claims)

Instrument: pinned fastfilter_cpp binary (the field's reference suite; ribbon IDs contributed
by the ribbon author). No new benchmark code. Add-phase ns/key and per-phase perf counters
(cycles/key, instr/key, IPC, cache-misses/key) as printed by the harness.

- Algorithms (≈1%-FPR class + context): HomogRibbon64_7 (1076), BalancedRibbon64Pack_7 (2076),
  XorBinaryFuse8 (116), XorBinaryFuse8-4wise (118), Xor8 (0), BlockedBloom (51),
  Bloom12-addAll (44).
- Sizes: 1M / 10M / 100M keys, three repetitions each (variance), same session, quiet machine.
- Recorded per run: full harness output (raw artifact), machine json.

Pre-registered descriptive questions:
- Q1: construction cost ribbon-vs-Bloom on this machine (does RocksDB's ~4× replicate?), and
  fuse-vs-ribbon.
- Q2: is each construction miss-bound or compute-bound at 100M (misses/key, IPC)?
- Q3: how does each scale 1M → 100M (the blocked-Bloom perkey signature was 2.2 → 11.5 ns/key;
  what's ribbon's)?
- Q4 (best-effort): banding vs back-substitution split for ribbon — only if obtainable without
  modifying the harness beyond a documented, committed patch.

## Phase 0 → Phase 1 go/no-go gates (frozen now)

- **GO** (register Phase-1 optimization hypotheses by amendment) iff at 100M keys some
  construction shows **≥0.5 cache-misses/key in a phase that is not already
  reordering-based**, or a compute profile with clear data-parallel slack (IPC ≤1.5 with
  ≥60 cycles/key in independent-iteration work). Any registered hypothesis must name the
  measured budget it attacks and must beat the strongest existing shape (incl. BuRR's sort and
  software-pipelined prefetch) — not a naive baseline.
- **NO-GO**: constructions are compute-bound in serial row-reduction/peeling with modest
  cycles/key, or miss-bound only in phases already solved by shipped reordering. Then E1b
  terminates as the third null and the measurement paper gains its final section: "space-
  optimal filter construction cost is algorithmic, not memory-layout — there is no layout
  target left."
- Gate evaluation is mechanical where possible (misses/key and IPC thresholds from the raw
  harness output); judgment calls (what counts as "already reordering-based") must quote the
  audit's code-level findings and be logged before Phase 1 registration.

## Prior-art audit (runs alongside Phase 0; gates Phase 1, not Phase 0)

Deep, code-level: BuRR paper+repo (what exactly IPS2Ra sorts; bumping's construction cost);
parallel BuRR (arXiv:2411.12365); RocksDB `ribbon_impl.h` (insertion order, back-substitution
layout, any prefetch); fastfilter_cpp / xor_singleheader binary-fuse construction (segment
sort, counter arrays, peel queue memory behavior); Dietzfelbinger & Walzer ESA 2019
(sorted-Gaussian linearity); Vigna ε-cost sharding (arXiv:2503.18397); Breyer & Liu
arXiv:2312.13541 (unchecked residual from the E1a audit); any SIMD banding/back-substitution
attempt anywhere. Deliverable: docs/prior-art-ribbon-construction.md with a must-cite list and
"what remains unaddressed" verdict.

## Stages

```bash
python run.py --stage phase0    # harness runs -> results/e1b/phase0/ raw outputs
python run.py --stage analyze   # derives results/e1b/ANALYSIS.md; evaluates go/no-go gates
```

## Phase-1 registration (amendment, 2026-07-09 — after Phase-0 data + audit, before any Phase-1 run)

**Gate decision: GO, narrowly.** Phase-0 measured HomogRibbon64_7 construction at 100M keys as
heavily miss-bound (50.6 ns/key, 256 cyc/key, IPC 0.64, **5.81 cache-misses/key** — vs
XorBinaryFuse8's 1.08 after its published segment-sort fix). The audit
(docs/prior-art-ribbon-construction.md) rules on the judgment call: the *sorted* fix is prior
art (SGAUSS 2019, BuRR 2022) and the *unsorted+prefetch* shape is shipped (RocksDB), so
neither is claimable — but three specific angles are audit-verified open: partition-instead-
of-sort, SIMD banding, SIMD/NT back-substitution. Parallel BuRR's own statement that sorting
dominates its construction time is the motivation quote.

**H-E1b-1 (registered):** replacing BuRR's full radix sort with a single-pass, L2-window
partition of (start, hash) tuples — approximate ordering only — recovers ≥80% of full
sorting's construction-miss reduction on homogeneous ribbon at ≥100M keys, at strictly lower
reordering cost, yielding net construction time below BOTH (i) unsorted homogeneous ribbon
(fastfilter reference, measured 50.6 ns/key) and (ii) a full-sort SGAUSS/BuRR-shaped build,
and (iii) the prefetch-pipelined unsorted shape (RocksDB's, to be measured as baseline).
Measured budget attacked: the ~4.7 excess misses/key (5.81 − 1.08 fuse floor). Window-boundary
handling reuses parallel BuRR's boundary-bumping idea (cited, not claimed). Failure threshold:
if partition-only cannot get within 1.3× of full-sort construction time, H-E1b-1 is refuted.
**Note the E1a echo-risk, pre-registered:** if banding-after-partition turns out to be
L2-hit-bound the way E1a's apply was, the sort-vs-partition delta may be small; the
experiment must report the reorder-phase and banding-phase costs separately.

**H-E1b-2 (deferred, NOT registered):** SIMD/NT back-substitution — blocked on a phase-split
measurement (banding vs back-substitution vs hashing) that Phase 0 could not provide without
patching the harness. A documented instrumentation patch is a precondition.

**Unregistered strategic options recorded, no claims:** GPU ribbon construction (fully open;
no GPU provisioned); incremental/mergeable ribbon across LSM compaction (fully open; the
biggest systems prize; a separate project-scale decision); the prefetch/MLP analysis angle
(folds into the measurement paper regardless).

## Threats to validity

- fastfilter_cpp's ribbon uses the author's reference implementation — construction there may
  differ from RocksDB's production builder (different back-substitution layout); both get
  cited, only one measured in Phase 0.
- Shared machine caveats as E0/E1a (i9-14900HX, AVX2, no AVX-512); ARM repeat when capacity
  lands.
- 100M is the ceiling here (harness's own recommended scale); 429M-class runs would need
  harness patches — out of Phase-0 scope.

## Phase-1b registration (amendment, 2026-07-09, before any Phase-1b run)

- **Window-size sweep (descriptive, no threshold):** partitioned strategy with window shift
  2^13–2^20 slots at 100M keys; reports the reorder/banding trade-off curve. The registered
  Phase-1 results used 2^16; the sweep tests whether that choice was lucky or robust.
- **H-E1b-2p (parallel windows, registered):** slot-range parallel banding — T threads own
  disjoint slot ranges; keys whose start lies within G=2^14 slots of a range boundary are
  deferred to a sequential tail pass (analogous to parallel BuRR's boundary bumping, made
  trivially verifiable by the measured order-independence of the solution). Conditions:
  (a) solution remains BIT-IDENTICAL to the sequential partitioned build (the fingerprint
  gate catches any cross-range write), (b) deferred fraction <0.5%, (c) banding-phase
  speedup ≥3× at 8 threads on 100M keys. Failure of (a) at any run invalidates that run's
  timing and the variant until diagnosed.
- ARM replication of Phase 1 remains queued on Hetzner CAX capacity (persistent watcher);
  bootstrap_remote.sh gains the e1b build/run so the replication is one command when
  capacity lands.
