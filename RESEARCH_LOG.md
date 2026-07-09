# Research Log

Dated, append-only. Records hypotheses, protocol decisions, dead ends, and integrity findings.
Newest entries at the bottom. Nothing here is a claim; claims live in CLAIMS.md with provenance.

---

## 2026-07-09 — Project start

**Origin.** Investigation of barudb's (`~/Code/hes/barudb`) Bloom filter work concluded it is not
itself publishable (ports + one half-finished idea), but a literature sweep found a genuine gap:
no published work applies FastLanes-style transposed layouts to AMQ filters (verified with 7
search formulations; closest work — split-block Bloom, Lang et al. register-blocking, VQF — is
all cache-line blocking, not cross-lane transposition).

**Audit findings carried as warnings** (documented in INTEGRITY.md): the barudb final report
contained a mathematically impossible memory table (7.8 bits/key @ 1% FPR is below the
9.57-bit Bloom-family bound), crossed benchmark labels (SpeedDB port presented as "our custom",
custom presented as "Standard"), and scalar per-lane loops presented as SIMD. Its criterion
timing data (May 2025) was real. None of the report's claims are carried into this project.

**Core idea to test.** FastLanes (VLDB 2023) shows a fixed transposed data order lets scalar code
auto-vectorize portably (>40 values/cycle decode). Question: can a filter's bit array be laid out
so that a *batch* of W probes becomes lane-parallel scalar code with the same property? Known
tension, to be settled empirically first: filter probes are hash-addressed (random access), unlike
FastLanes' sequential decode — if probe cost is dominated by cache misses at realistic filter
sizes, transposition of the compute cannot matter. That is E0b, and it is the kill criterion.

**Hardware note.** Local dev box: i9-14900HX (Raptor Lake) — AVX2 only, no AVX-512; 32 threads,
94 GB RAM, Linux 7.0.11. AVX-512 and ARM(NEON/SVE) validation deferred to user-provided VPS.

**Framework decision.** Cross-filter comparisons will run in fastfilter_cpp (the suite used by the
xor-filter, binary-fuse, BuRR, and prefix-filter papers). Rust prototype microbenches use
Criterion.rs and must cross-validate against fastfilter_cpp on an overlapping configuration before
their numbers are used (policy in CLAUDE.md).

## 2026-07-09 — E0 protocol frozen; FPR gate passed

- Repo scaffolded (act-context house style). Harnesses pinned: fastfilter_cpp @ 924e560,
  FastLanes @ f0edc10. fastfilter_cpp builds and runs on this machine (BlockedBloom smoke run:
  measured FPR 0.9579% at 10.67 bits/key at 1M keys — theory-consistent).
- E0 protocol written and frozen BEFORE any timing run (experiments/e0_feasibility/README.md):
  three probe strategies over identical SBBF-geometry filters + L1-hot control, five sizes
  32KiB→512MiB, pre-registered decision rules incl. kill criterion.
- Prototype crate `lanefilter` implements Parquet-spec SBBF geometry. Guard tests pass:
  zero false negatives, strategies agree bit-for-bit, FPR within theory.
- FPR gate (results/e0a/summary.json): lanefilter_sbbf 1.2660% at 10.00 bits/key (correctly
  WORSE than ideal-Bloom 0.82%, as split-block theory predicts); fastbloom 0.9: 0.8462%.
  Gate range [0.5%, 2%] → PASS. Timing runs may be interpreted.
- Known asymmetry to carry into analysis: the fastbloom baseline number includes its internal
  hashing; our strategies mix keys with splitmix64 inline. Noted in E0 README.

## 2026-07-09 — E0 run 1: INSTRUMENT FLAW caught by anchor cross-validation; protocol amended

Run 1 completed (artifacts under results/e0a/, superseded). Before interpretation, the
fastfilter_cpp anchor exposed a flaw in our criterion bench: the probe set was a fixed 8192 keys
reused every iteration, so at RAM-scale filter sizes the probed cache lines (~512 KiB) stayed
warm across iterations — the "64MiB/512MiB" rows measured a cached working set, not RAM-resident
probing. Evidence: our scalar strategy showed 2.13 ns/key on a 512 MiB filter while
fastfilter_cpp measures 14.6 ns/key with 1.03 DRAM-misses/key on a *smaller* 133 MB filter
(results/e0a/anchor/blockedbloom_100000000.txt). A ~7× cross-harness discrepancy = artifact.

**Amendment 1 (instrument fix, before any rerun interpretation):** probe pool enlarged to 4M
keys; each criterion iteration advances through the pool so every iteration probes fresh lines
(reuse distance ≥ 4M lines >> L3). Cache-resident rows (≤4MiB) are unaffected by the flaw.
Decision rules are UNCHANGED. Run-1 artifacts are kept under results/e0a_run1_superseded/ for
the record; nothing from run 1 is citable except the cache-resident rows, and those only after
run 2 confirms them.

What run 1 did establish (and run 2 must confirm):
- The lanes kernel auto-vectorizes: 138 packed-SIMD instruction lines (vpgather etc.) from plain
  scalar Rust — RQ1's mechanical half answers YES.
- At cache-resident sizes, per-key scalar SBBF probing (already horizontally SIMD within a
  block) beat the vertical lanes kernel — no headroom from cross-key batching there.
- fastbloom per-key numbers include SipHash-family hashing of the key; not comparable
  head-to-head with our inline-mixed strategies — treat as context only, never as a beat-claim.

## 2026-07-09 — E0 run 2 (amended instrument): Rule 2 fired; probe-side transposition is dead on OoO x86

Artifacts: results/e0a/ (criterion run 2, asm, anchor, summary). Cross-harness sanity now holds
(C8). Pre-registered **Rule 2** fired at 64MiB and 512MiB (hot-control/lanes = 5.08×/6.01×,
lanes never ≥1.3× over prefetch). Verdict and interpretation, logged before any E1 design:

1. **RQ1 splits.** Yes, plain scalar Rust vertical batch code auto-vectorizes (C2's mechanical
   half). No, it does not pay: vertical (cross-key, gather-based) SIMD loses to per-key scalar
   SBBF probing at EVERY size, even with all addresses forced L1-hot (C6, 555 vs 665 Mops/s).
   Two reasons, both structural on big OoO x86: (a) the SBBF block check is already horizontally
   SIMD within one key (8 words = one AVX2 register, ~2-4 hot instructions), and (b) AVX2
   gathers (vpgatherdd) are slower than 8 independent scalar loads that the OoO window overlaps
   for free.
2. **At RAM sizes, the bottleneck is memory-level parallelism + TLB, not compute** (C7): the
   identical instruction stream runs 5-6× faster L1-hot. Software prefetch recovers 1.45-1.66×
   over scalar but plateaus around 148 Mops/s — consistent with the single-core MSHR ceiling
   (~16 outstanding misses / ~95ns ≈ 168M lines/s), i.e., the prefetch strategy is already at
   ~88% of what one core's miss machinery can physically deliver. 4KiB-page TLB misses (512MiB
   = 131K pages >> dTLB) are part of the per-probe latency; hugepages are the obvious next lever
   (fastfilter_cpp ships hugepages.sh for exactly this reason).
3. **Consequence for the research direction:** FastLanes-style transposition accelerates
   *compute*; RAM-resident point probes have no compute bottleneck to remove, and cache-resident
   probes are already optimally served by horizontal SBBF + OoO. The "transposed probe" idea is
   dead on modern out-of-order x86 — this is a real, honest negative with artifacts behind it.
4. **What survives (E1 candidates, in current preference order):**
   a. **Construction side** — bulk filter *build* during LSM compaction: keys can be
      radix-partitioned by block so bit-setting becomes sequential, affine-addressed work — the
      access pattern FastLanes transposition actually targets. Ribbon's 3-4× construction CPU is
      a named open problem (survey); a fast vectorized builder (Bloom first, ribbon stretch) has
      a real customer.
   b. **Non-OoO targets** — in-order/narrow cores (ARM efficiency cores, embedded) and GPUs,
      where the OoO-hides-everything argument breaks. Needs VPS/ARM hardware; no published ARM
      filter study exists (survey gap #3).
   c. **Hugepage/TLB-aware probing study** — measurement-paper material quantifying how much of
      the "filter probe cost" literature is actually TLB artifact on 4K pages.
5. Next concrete step: E1a protocol (construction-side): compare insert-all throughput of
   (i) per-key inserts, (ii) radix-partitioned then per-partition inserts, (iii) partitioned +
   transposed bulk bit-setting, at 16M-1B keys, vs fastfilter_cpp's addAll variants as anchors.
   Freeze protocol before running.

## 2026-07-09 — VPS infrastructure (Hetzner)

- User provided HETZNER_TOKEN via repo-root .env (added to .gitignore before any commit exists).
- Account holds one pre-existing server, `vectors-bench` (CCX33) — another project's; untouched.
- With user approval: dedicated keypair ~/.ssh/tf_bench_ed25519 registered as
  `transposed-filters-bench`.
- ARM CAX capacity sold out in all locations/types at time of writing; an automated retry loop
  is creating `tf-bench-arm` as soon as capacity frees. x86 CCX blocked by the account's
  dedicated-core quota (consumed by vectors-bench); user decision: ARM first, x86 later.
- scripts/bootstrap_remote.sh gives one-command remote E0 runs; run.py asm stage made
  arch-aware (NEON/SVE mnemonics on aarch64) so the ARM vectorization verdict is real, not an
  x86-pattern artifact. Note for interpretation: CAX = Neoverse-N1 (OoO, NEON-only, shared
  vCPU) — it tests ISA portability of the E0 null, not the in-order hypothesis; in-order/GPU
  targets remain future work.
