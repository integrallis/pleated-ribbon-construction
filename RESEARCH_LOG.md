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

## 2026-07-09 — E1a: prior-art audit landed; K2 partially fired; protocol revised and FROZEN

- Adversarial audit (docs/prior-art-construction.md) killed the draft H1 as novelty:
  Schmidt/Bandle/Giceva (PVLDB 2021) published radix-partitioned filter construction (SWWC +
  NT stores, up to 9× build gains); fastfilter_cpp has shipped buffered AddAll since 2018;
  Canim 2010 and Beamer 2017 anticipate the deferred-grouped-update pattern. All revisions
  made BEFORE any timing data existed.
- Surviving novelty candidate (audit-verified absence): the READ-FREE apply — partition
  pre-merged (block, mask) pairs, register OR-aggregation per block, exactly one
  (non-temporal) store per block, filter memory never read, bit-identical monolithic output.
  Every located prior system RMWs filter memory; fastfilter's own numbers (buffered blocked
  AddAll ≈ 0–10%) show buffering without mask pre-merge underperforms — our differentiation
  argument if H2 confirms.
- Protocol revised accordingly (H1 = replication claim; H2 = read-free apply ≥1.2× over
  Schmidt-shaped baseline; K2 fires fully if H2 <1.2× everywhere) and FROZEN.
- Implemented strategy 5 `build_partitioned_grouped_nt` (x86 _mm256_stream_si256 apply +
  sfence); all five builders pass the bit-identity gate at three sizes.
- Required baselines recorded: fastfilter AddAll ids 43/52 (pilot), tum-db/partitioned-filters
  (paper-level). Framing rule: never claim partitioning/buffering/bulk-build as novel.

## 2026-07-09 — E1a full sweep: H1 short, H2 REFUTED; K2 fires; structural post-mortem

Artifacts: results/e1a/ (criterion full sweep 1M–429M, anchors ids 43/51/52, ANALYSIS.md).
Mechanical outcomes (all ≥64MB sizes): partitioned/perkey = 1.45–1.71× (H1's ≥2× NOT met);
grouped/partitioned = 0.63–0.65× (H2 catastrophically refuted — the read-free apply is ~1.5×
SLOWER than partitioned RMW); NT stores change nothing (±2%).

Structural post-mortem (written before any rerun decision, per protocol):
1. **Partitioning and the read-free apply attack the same misses, so they don't compose.**
   Once pairs are partitioned to L2-sized spans, the RMW reads the apply would eliminate are
   L2 HITS; the DRAM read-for-ownership happens once per filter line and is already amortized
   over ~26 keys/line. The second counting sort that grouping needs costs ~4.5 ns/key against
   an eliminated-read benefit of ~1 L2 hit/key. fastfilter's historical ~0–10% for buffered
   AddAll and our 0.63× agree with this accounting from opposite directions.
2. **Software-pipelined prefetch is the sleeper finding**: perkey_prefetch = 6.08/7.35/8.90
   ns/key at 53.7M/100M/429M — it BEATS partitioned at 53.7M and 100M and needs no transient
   memory; partitioned only pulls ahead at 429M (7.71 vs 8.90). RocksDB has shipped this shape
   (AddAllEntries) since 2019. Any partitioned-construction claim must now also beat this
   baseline, which Schmidt et al. did not evaluate against.
3. H1's miss at ≥2× is partly implementation (pass 1 materializes pairs then scatters:
   ~16B/key of avoidable staging traffic; a fused SWWC scatter would plausibly reach ~2×) —
   but H1 is a REPLICATION claim; optimizing to reach it creates no paper. Not pursuing an
   amendment round; recording the estimate instead.
4. **K2 fires in full.** Per the frozen protocol, salvage paths: (a) ribbon/binary-fuse
   construction (structurally different — sort/peel over large arrays; partial prior art),
   (b) cross-ISA/ARM, (c) LSM end-to-end integration, (d) measurement study of the E0+E1a
   nulls. Recommendation to user: (d) as the paper backbone — two pre-registered nulls with
   perf-counter mechanisms, cross-harness validation, and a methodology story (anchor-caught
   instrument flaw), plus ARM confirmation when capacity lands; (a) as the only remaining
   novelty-bearing thread if hypothesis-hunting continues.

## 2026-07-09 — E1b Phase 0 + audit: GO (narrow); H-E1b-1 registered

- Phase 0 (reference harness, 3 reps, results/e1b/phase0/): homogeneous ribbon construction is
  the outlier — 5.81 misses/key at 100M (256 cyc/key, IPC 0.64) while binary fuse sits at 1.08
  after its published segment-sort fix; Xor8's 9.45 vs fuse's 1.08 measures that fix directly.
  BalancedRibbon (bump machinery) costs 677 cyc/key. RocksDB's ~4.4× Bloom-vs-ribbon build gap
  replicates on this machine.
- Code-level audit (docs/prior-art-ribbon-construction.md): sorted banding = SGAUSS/BuRR
  (dead); unsorted+prefetch = RocksDB shipped (dead as claim, open as analysis); AUDIT-OPEN:
  SIMD banding, partition-instead-of-sort, SIMD/NT back-substitution, GPU ribbon construction,
  incremental/mergeable ribbon for LSM. Parallel BuRR names sorting as its dominant
  construction cost without attacking it — the motivation quote.
- Gate decision GO; H-E1b-1 registered by amendment (partition-instead-of-sort, ≥80% of full
  sort's miss reduction at lower reorder cost, must beat unsorted + full-sort + prefetch
  baselines; E1a echo-risk pre-registered: report reorder and banding phases separately).
  H-E1b-2 (SIMD/NT backsub) deferred pending a documented harness instrumentation patch.
- Strategic note for the user: the fully-open incremental/mergeable-ribbon-for-LSM thread is
  the largest prize surfaced by either audit, but is project-scale; H-E1b-1 is the tractable
  next experiment.

## 2026-07-09 — E1b Phase 1: H-E1b-1 CONFIRMED (first surviving novel result)

Artifacts: results/e1b/phase1/ (45 runs), PHASE1_ANALYSIS.md. All registered conditions met at
both ≥100M sizes; integrity checks pass.

- **Result (C17):** L2-window partitioning (single counting pass, 5.5–6.1 ns/key) recovers
  98.3–98.4% of full sorting's banding-miss reduction (5.75→0.17 vs →0.075 miss/key) and makes
  homogeneous ribbon construction 2.05×/2.24× faster than the reference prefetch-pipelined
  build at 100M/400M (24.2/24.7 vs 49.6/55.3 ns/key), 1.68–1.73× faster than our best full
  sort. The ribbon-vs-BlockedBloom construction gap on this machine shrinks from ~4.4× to
  ~2.2×.
- **Output-neutrality (the correctness centerpiece):** the banded solution is BIT-IDENTICAL
  across all insertion orders (45/45 runs, FNV fingerprints match per (n,rep)) — reordering is
  provably a pure performance transformation. Zero false negatives; FPR ~0.81% at 7.63
  bits/key (floor 6.97).
- **Why the E1a echo did not materialize:** unsorted banding pays ~5.8–6.1 misses/key that
  prefetch cannot fully hide because row reductions are data-dependent chains (unlike Bloom's
  independent probes — noprefetch control: prefetch worth only 1.5–1.7× here, C18). The
  partition converts those to L2-resident work WITHOUT trying to eliminate the L2 RMWs
  (E1a's mistake), and costs 4× less than our radix sort.
- **Declared limitation (C19):** sort baselines are std::sort and our LSD radix; BuRR's ips2ra
  would narrow the totals margin (banding-phase numbers are sort-independent). Paper-grade
  comparison must add ips2ra, ideally BuRR's own construction end-to-end.
- Next candidates (user to prioritize): ips2ra/BuRR head-to-head; window-size sweep (2^14–2^18);
  ARM repeat (watch still finds CAX sold out); multithreaded variant (windows are
  embarrassingly parallel with boundary handling — parallel-BuRR comparison); LSM integration
  (build-during-compaction); write-up.

## 2026-07-09 — ips2ra + BuRR head-to-head: C19 resolved, verdict unchanged (C20, C21)

- `sort_ips2ra` strategy added to the driver using BuRR's own vendored ips2ra (sequential; the
  TBB-parallel path is gated behind _REENTRANT — our first build failed because -pthread set
  it; documented). Fingerprints bit-identical, as required.
- Measured: ips2ra reorder 22.3/23.9/28.1 ns/key at 10M/100M/400M in our driver (includes
  pair materialization + key extraction); 17.3 ns/key inside BuRR's own bench at 100M
  (in-place MHC sort). Either way, ~3–5× the partition pass (5.5–6.1 ns/key). H-E1b-1's
  conditions remain ALL MET with ips2ra in the best-sort minimum; best full-sort totals
  40.7/41.5 vs partitioned 24.2/24.7 at 100M/400M.
- BuRR end-to-end anchor (pinned 5f588f4; 2-bit, w=64, interleaved, ε=−0.005; -Werror dropped
  via CLI CFLAGS, source untouched; TBB/ninja/xxhash installed user-space): ~70 ns/key at 100M
  items = MHC 3.3 + ips2ra 17.3 + banding-with-bumping 46.0 + backsubst 3.5. Cited as anchor
  only — different structure (r=8, ~1% space overhead vs our homogeneous r=7 at ~9.5%).
- Process note: an earlier `make bench | tail` pipe masked BuRR's build failure (notification
  showed the pipe's exit 0); caught when the binary was missing. Rule reinforced: never pipe a
  build whose exit code matters.
- Paper positioning after this: the honest comparison set is complete on x86 — unsorted,
  prefetch-pipelined, three full sorts incl. the field's best, and BuRR itself. Remaining
  before write-up: window-size sweep, ARM replication, and (optional) parallel windows.

## 2026-07-09 — Phase-1b: window robustness + H-E1b-2p CONFIRMED; ARM still blocked

- Window sweep (C22): totals flat at 23.8-26.9 ns/key across 2^13-2^20 windows; 2^14 best.
  The Phase-1 headline was measured at 2^16 — conservative. Banding misses grow gently past
  L2 (0.146->0.306/key); reorder cheapens slightly with fewer windows. Robustness, not a
  cliff: the technique does not depend on tuning the window.
- Parallel windows (C23): all three registered conditions PASS. Banding 4.25x at 8T, 7.56x at
  16T; deferred max 0.226%; bit-identity in every run including 400M. Total 11.93 ns/key at
  16T = ribbon built as fast as sequential BlockedBloom per-key insertion on this machine.
  Amdahl: sequential reorder (5.7) + backsubst (3.4) now dominate; parallelizing the counting
  pass is trivial future work, backsubst parallelization = parallel-BuRR's approach (cite).
  Honest overhead note: T=1 parallel banding (18.3) > sequential partitioned (15-16) — the
  filter/defer copy costs ~2-3 ns/key.
- ARM: Hetzner CAX sold out all day across all types/locations; persistent watcher keeps
  trying; bootstrap_remote.sh now carries the full e1b pipeline for one-command replication.

## 2026-07-10 — ARM replication (OCI Neoverse-N1): pleating holds, output identical cross-ISA

Box: OCI Always-Free A1.Flex, 4 OCPU/24GB, Ampere Altra Neoverse-N1 (CPU part 0xd0c, NEON,
no SVE), Ubuntu 24.04, gcc 13.3, rustc 1.97. Artifacts: results/e1b-arm-n1/.

- **Instrument caveat (declared):** hardware perf counters read zero in this VM (perf_event
  blocked by the hypervisor). So fastfilter_cpp's phase-0 add-timing and all cache-miss/IPC
  fields on this box are INVALID and not used. The e1b_phase1 driver's wall-clock ns/key
  (steady_clock) is independent of perf and is what we report; its banding_*_per_key counter
  fields are likewise zeroed and ignored.
- **Wall-clock, 100M keys:** reference (unsorted+prefetch) 122.8 ns/key, best full sort 64.6,
  **partitioned (pleated) 51.7** — pleating 2.37x over reference, 1.25x over the best full
  sort. Reorder pass 15.9 ns/key vs 36.5 (radix) / 39.4 (ips2ra). The reference banding is far
  more punished on N1 than on x86 (113.8 vs 46.1 ns/key), consistent with a narrower core
  hiding the dependent-chain misses even less — the pleating win is LARGER on N1 (2.37x vs
  2.05x reference on x86), though we cannot cite the miss mechanism from this box (no counters).
- **Correctness centerpiece, cross-ISA:** per-(n,rep) solution fingerprints identical across
  all six strategies, 9/9 groups; and x86-vs-ARM partitioned fingerprints identical 9/9 matched
  (n,rep) pairs. The proven order-independence extends to architecture-independence: same bits
  on AVX2 x86 and NEON ARM. Zero false negatives on every run.
- Parallel points (T=1,2,4) finishing on the box; N1 has 4 cores so no 8/16T data here.
- ACTION: pull remaining parallel, terminate OCI instance. SVE data point still wants GCP
  Axion / AWS Graviton (both pending). N1 duplicates Hetzner CAX silicon but is the first ARM
  numbers we have.

## 2026-07-10 — ARM #2 (GCP Axion, Neoverse-V2/SVE): pleating replicates, 3-way bit-identity

Box: GCP c4a-standard-8, Ampere/Google Axion Neoverse-V2 (CPU part 0xd4f, SVE+SVE2+bf16+i8mm,
8 cores, 31GB), Ubuntu 24.04. Artifacts: results/e1b-arm-v2/. Same VM perf caveat as OCI:
GCE does NOT virtualize the PMU (perf stat -> <not supported> even at paranoid=0 with sudo),
so cache-miss/IPC fields are invalid on this box and omitted; wall-clock ns/key is the report.

- 100M keys, wall-clock: reference 93.7 ns/key, best full sort 44.8, **partitioned (pleated)
  34.4** -> 2.72x over reference, 1.30x over best full sort. Reorder pass 6.5 vs 21.8 (radix)
  / 26.9 (ips2ra). Reference banding 86.3 ns/key (vs 46.1 x86, 113.8 N1) — V2 sits between.
- **Parallel scaling to 8 cores (first full curve; N1 capped at 4):** banding 24.5 -> 12.6 /
  6.5 / 3.46 ns/key at T=1/2/4/8 = 1.94x/3.78x/7.07x; total 17.28 ns/key at 8T; deferred
  <=0.105%; zero false negatives. Near-linear to 8 threads.
- **3-way cross-ISA bit-identity:** V2 partitioned fingerprints == x86 9/9 AND == N1 9/9 at
  every (n,rep). The solved filter is byte-identical across AVX2 Raptor Lake, NEON N1, and
  SVE V2. Order-independence => architecture-independence, now on three microarchitectures.

Cross-arch pleating summary (reference-speedup): x86 2.05x, N1 2.37x, V2 2.72x. The weaker a
core hides dependent-chain misses, the more pleating helps — but it helps materially on all
three. ARM miss-MECHANISM still unmeasured (no cloud ARM exposes counters); optional
bare-metal closer (GH200=V2, or phoenixNAP=N1, or AWS metal) noted, not load-bearing.
ACTION: terminate OCI + GCP instances now.
