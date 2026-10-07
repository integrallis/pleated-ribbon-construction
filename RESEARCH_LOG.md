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
their numbers are used (standing project policy).

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

## 2026-10-06 — Prior-art correction: the approximate sort is in print (C15 corrected)

DRAFT on branch `prior-art-corrections`, uncommitted, pending author review.

The July audit (docs/prior-art-ribbon-construction.md, C15) recorded partition-instead-of-sort
for banding locality as unclaimed. That was wrong as worded. Checked against the PDFs on
2026-10-06:

- BuRR technical report arXiv:2109.01892, Algorithm 3 line 3: "sort S approximately by s(x)".
  Present in v1 (2021-09-04, citing Lemma 9) and v2 (citing Lemma 11). The proof says keys
  "sorted into buckets of b consecutive starting positions each and buckets handled from left
  to right" suffice. The 12-page SEA 2022 version, which is what the July audit and refs.bib
  cited, does not contain it.
- JACM 73(1) Art. 7 (published 2026-02-13), Algorithm 4 line 3: "sort S by s(x) // at least
  approximately, see proof of Theorem 5.3". Not previously in refs.bib.
- The same papers state that the filled-slot set is invariant under insertion order, which is
  the first step of our order-independence proposition.
- Reference code at our pin (fastfilter_cpp 924e560, src/ribbon/ribbon_impl.h and
  ribbon_alg.h) has no sort step; "sort" occurs only in comments. This matches what E1b
  measured as the "reference" baseline (arrival order + prefetch).

Consequence: no measurement changes. H-E1b-1 was registered as a measurement hypothesis and its
result (C16, C17, C20) stands. What changes is the novelty framing: the ordering idea is the
ribbon authors'; ours is the implementation, the dependent-miss mechanism, the measurement, and
the transfer to RocksDB's standard builder. The E1b README's gate decision cites the July audit
and is left as registered; this entry is the correction of record.

Edits: paper/main.tex (lineage paragraph, contribution bullet, "reference" definition,
binary-fuse analogue, proof-sketch credit, parallel-variant distinction, related work; the
parallel-BuRR quotation now matches the source, "A large portion"), paper/refs.bib (+5),
CLAIMS.md C15, docs/prior-art-ribbon-construction.md.

Not done, still open: the JACM bucket-width bound was not compared with our window sizes (the
extracted formula differs between TR and JACM and needs reading in the typeset PDF);
Proposition 1 still fixes free slots to zero and was not reconciled with JACM footnote 19 or
the kernel's actual free-variable assignment; title unchanged; paper/draft.md (v0.2 rendition)
and paper/main.pdf not regenerated.

## 2026-10-06 — Title change and matched Bloom-gap table (C25); DRAFT, uncommitted

Title changed to "Pleated Ribbon Construction: Approximate Sorting Recovers the Locality of a
Full Sort" (paper/main.tex, README.md, CITATION.cff). Reason: the old "Catches Bloom ... at Bloom
Speed" rested on a 16-thread ribbon total against one-thread Bloom.

Added experiments/e1b_ribbon_construction/analyze_bloom_gap.py, which joins existing raw
artifacts (no new runs) into results/e1b/BLOOM_GAP_ANALYSIS.md and paper/tables/bloom_gap.tex.
At 100M keys, one thread: ribbon is 4.42x -> 2.16x fastfilter BlockedBloom and 6.74x -> 3.29x
the fastest Bloom build we measured (prefetch-pipelined, 7.35 ns/key). Published as "narrowed,
not closed". Caveats recorded in the analysis file: two harnesses, not equal space/FPR, no
parallel Bloom measurement. Note the Phase-0 BlockedBloom mean (11.21, 3 reps) differs from the
single E0 anchor run in C9 (11.48); the table uses the 3-rep Phase-0 value.

## 2026-10-06 — Bloom-gap table: caveats resolved where artifacts allow; E3 drafted for the rest

DRAFT, uncommitted. analyze_bloom_gap.py now also reports run-to-run spread, the prototype's
recorded FPR/bits (E0, 1M keys), the space saving on the same-harness pair, and checks C9's single
BlockedBloom run against the 3-rep range (11.48 inside 10.54-12.46). Paper text now leads with
the same-harness, near-equal-FPR pair (4.4x -> 2.2x) and states that the "fastest Bloom" ratio
(6.7x -> 3.3x) is against a weaker filter from a different harness.

Two limits cannot be removed without new data: a prefetching Bloom at matched FPR in an
established harness, and an equal-thread parallel Bloom. experiments/e3_bloom_gap/README.md is a
draft registration for both (Stage A: RocksDB filter_bench, FastLocalBloom vs Standard128 stock
and pleated; Stage B: parallel Bloom, sketch only). Not frozen; the filter_bench -impl value for
Bloom is unverified; run.py/analyze.py not written; no data collected. This session's machine is
not the i9 dev box, so nothing was run.

## 2026-10-06 — E3 Stage A run: matched-FPR Bloom vs ribbon in filter_bench (C26)

Protocol frozen in commit fabfce3 before data. Box: Hetzner CCX33 `rcb-bench-e3` (AMD EPYC-Milan,
8 dedicated vCPU, 32 GB, KVM), RocksDB 31b239747 + E2 patch, gcc 13.3. Build gates passed; 36/36
filter_bench invocations succeeded; raw stdout in results/e3/raw/.

- All four sizes pass the FPR-match criterion; stock and pleated report identical FP at every size.
- pleated/Bloom build cost: 5.18x (100K), 4.13x (1M), 4.10x (10M), 2.43x (100M).
  stock/Bloom: 4.97x, 4.67x, 7.27x, 4.52x.
- H-E3-1 HOLDS. **H-E3-2 FAILS as predicted**: pleated ribbon is 2.43x Bloom at 100M, not within
  1.25x. Null published: pleating narrows the gap and does not close it.
- Bloom's own build cost rises with filter size on this box (15.9 -> 37.1 ns/key), which is part
  of why the ratio is smallest at 100M.
- Stock/pleated on this second x86 machine: 1.77x at 10M, 1.86x at 100M (E2 on the i9: 1.62x and
  1.78x); slightly slower below the crossover at 100K (0.96x), as in E2.

Results and this entry are uncommitted. Paper not yet updated with E3. Server still running at
the time of writing; teardown pending the author's confirmation.

## 2026-10-06 — E3 in the paper; server deleted

`rcb-bench-e3` deleted on the author's instruction after results were verified local (36 raw
files, 36 CSV rows); no servers remain on the account. Paper: new paragraph and Table
(tab:ethree) in the RocksDB section from results/e3/ANALYSIS.md; the standalone Bloom-gap table
now holds only the same-harness rows (prototype rows remain in BLOOM_GAP_ANALYSIS.md and are
mentioned in prose with their caveat); conclusion states the 2.4x remaining gap. The E3 README
is the frozen protocol and is left as committed, including its pre-run status line.

## 2026-10-06 — E4 run: Bloom vs pleated ribbon at equal thread counts (C27)

Protocol frozen in 74de203. Hetzner refused the 16-core CCX43 (dedicated core limit exceeded);
amendment 48fd3f2, committed before any data, moved the run to an AWS c7a.4xlarge (AMD EPYC 9R14,
16 physical cores, one thread per core). All stages ran once, in order, no reruns.

- Gates: all pass. Ribbon fingerprint at 100M (2b882b197876d9a8) also equals the i9's.
- Cross-validation passes narrowly: prototype perkey 21.19 vs fastfilter BlockedBloom 17.30
  ns/key = 22.5% apart, tolerance 25%. Worth knowing: on the i9 the same pair was 8% apart.
- ribbon/Bloom at T=1/2/4/8/16: 4.03x / 4.16x / 4.95x / 7.22x / 10.08x.
  **H-E4-1 HOLDS, H-E4-2 FAILS as predicted.** Null published.
- Why the gap widens: at 16T the ribbon total is 22.15 ns/key of which reorder ~10.8 and
  back-substitution ~9.1 are sequential; banding itself is 2.2. Bloom best-of scales 4.56x.
- Best Bloom builder changes with T: par_scan at 1-2, par_range at 4-8, par_atomic at 16.
- Prototype FPR now measured at 100M keys: 1.2727% at 10.00 bits/key (was only known at 1M).
- This machine is much slower per key than the i9 for the ribbon driver (sequential pleated
  40.3 vs 24.2 ns/key), so E4 numbers are not comparable with C17/C23 and are not mixed.

Per the registered decision rule, the README sentence about 16-thread ribbon vs one-thread
Bloom now carries the equal-thread ratio. Paper: new paragraph and table in the parallel
section; conclusion states the 16-thread ratio. Results and edits uncommitted; instance still
running pending the author's word on termination.

Instance rcb-bench-e4 (i-0d927dbd11038da34) terminated 2026-10-06 on the author's instruction after results were verified local.

## 2026-10-06 — Plan block 1 housekeeping: hand checks, Proposition 1 fix, ledger rows C28-C32

Hand checks done from primary sources:
- SEA 2026 CFP, read directly: "Papers containing content generated by large language models
  (LLMs) ... are not allowed, except for: Generating scientific plots displaying data that the
  authors obtained from experiments ...; Polishing the text that the authors have personally
  written." The clause is about paper content; it does not mention code. Same page: 12 pages
  excluding bibliography and front page plus up to 5 pages appendix, LIPIcs style, anonymized,
  arXiv allowed, software must be linked anonymously.
- SEA 2027 site still shows Submission Deadline: TBD; CFP page: TBD (checked 2026-10-06).
- JACM p. 7:24, read in the typeset PDF: "approximate sorting of keys into buckets of at most
  exp(−Ω(εw))/ε consecutive starting positions is also sufficient" — printed with the minus
  sign (the TR has b ≤ exp(Ω(εw))). The passage is at the end of the proof of Lemma 5.3(b),
  §5.3; the Algorithm 4 comment calls it "proof of Theorem 5.3". The constant is unspecified,
  so our 2^16-slot window cannot be checked against it numerically. Empirically the bound is
  not binding: mean banding instructions/key at 100M are 97.43 (arrival order), 96.15 (full
  ips2ra sort), 97.85 (partitioned) — from results/e1b/phase1/*_100000000_rep*.json field
  banding_instr_per_key. Not yet in the paper.
- JEA closure: NOT verified. dl.acm.org serves a bot-verification page to automated access;
  left for the author to open in a browser.
- arXiv:2109.01892 v1 already contains the approximate-sort line (checked earlier today).

Proposition 1 corrected: the pinned kernel assigns free homogeneous solution rows
i * 0x9E3779B185EBCA87 (ribbon_impl.h LoadRow), not zero; the statement now allows any g(j)
depending only on the slot index. docs/order-independence-proof.md updated, with an UNREVIEWED
note that for homogeneous ribbon (all right-hand sides zero) the independence hypothesis looks
unnecessary. The paper does not claim that.

Ledger gap closed: C28-C32 added for the ARM replications, the Graviton4 PMU run and E2, each
derived by a new script from the committed raw artifacts (analyze_arm.py, e2_rocksdb/analyze.py).
Every ARM and E2 number in the paper reproduces from raw data. One weakness surfaced: the V2
parallel scaling figures are a single run per thread count; the paper now says so.

## 2026-10-06 — Citing-paper sweep and outreach draft

Semantic Scholar citation lists fetched 2026-10-06: 44 papers citing arXiv:2109.01892, 57
citing arXiv:2103.02515, 1 citing the JACM article (DOI 10.1145/3785417); 93 distinct. The API
has no record for parallel BuRR (arXiv:2411.12365). By title, none implements or measures
approximate-sort / partitioned ribbon construction. Abstracts read for the three closest recent
ones (Resizable Retrieval, arXiv:2606.15944; Consensus for Compressed Static Functions,
arXiv:2609.39557; Static Retrieval Revisited, arXiv:2510.18237): none concerns ribbon
construction order. Still unread: the 2022 IEEE "Ribbon Filter: Analysis, Design, and Optimized
Implementation" (paywalled). This is a title-level sweep of one index, not proof of absence.

docs/outreach-email-draft.md: draft email to Dillinger and Walzer (not sent).

## 2026-10-06 — E5 run: pleated RocksDB filters are byte-identical to stock (C33)

Protocol frozen in ebcecdc. Hetzner CCX33 `rcb-bench-e5`; RocksDB 31b239747 + E2 patch + dump
patch; check stage passed; twelve runs, no reruns.

- Control: stock_a == stock_b at every size (filter_bench is deterministic at the default seed).
- **H-E5 HOLDS:** 443/443 filters byte-identical between stock and pleated (396 + 40 + 4 + 3).
- Supplementary, outside the registered protocol: the runner did not record build times, so a
  vacuous pass (pleat pass not active) could not be ruled out from the artifacts alone. One
  extra pair of runs at 10M on the same binary, with the dump directory set, gave 155.8
  (stock) vs 92.2 (pleated) ns/key and identical dumped bytes. Saved as
  results/e5/supplement_pleat_active.txt and labeled as supplementary.

Paper and README now cite E5 where they previously said byte identity was not established.
Server deleted after results were verified local (standing instruction); no servers remain.

## 2026-10-06 — Submission preparation (no measurements)

- scripts/make_lipics.py generates paper/sea/main.tex (LIPIcs v2021, anonymous by default) from
  paper/main.tex; class files are the unmodified Dagstuhl author package v2021.1.3. Anonymous
  build: 15 pages, references from page 14.
- analyze_banding_steps.py: banding instructions/key by insertion order at 100M/400M
  (97.43/97.67 arrival, 96.15/97.67 ips2ra sort, 97.85/97.70 partitioned), now cited in the
  paper via generated macros.
- scripts/make_anonymous_bundle.sh builds a double-blind artifact from the committed tree and
  lists residual identifying strings for hand review (it found references to barudb, CS265 and
  a home-directory path that need a human decision).
- Drafts, none sent or published: docs/outreach-email-draft.md, docs/blog-post-draft.md,
  docs/arxiv-submission-checklist.md; .zenodo.json; README
  how-to-cite block. docs/Ribbon_Publication_Plan.md has a dated status section.
- Every analysis script in reproduce.sh was run (with python3 directly) and leaves the
  committed ANALYSIS files unchanged. cargo test passes (6 tests). reproduce.sh itself was not
  run end to end here.

## 2026-10-06 — Follow-up on the three unverified items

- JEA: dblp (page updated 2026-10-06) shows the last volume as 28 (2023), records 1996-2023.
  ACM's own page still unreachable by automated browser (bot check, not bypassed).
- IEEE 9920402 (Linuwih, Satrya, Mugitama, Maulana; iSemantic 2022): abstract and outline read
  on IEEE Xplore; a restatement/"further study" of the ribbon filter, nothing on construction
  order. Full text not read (sign-in).
- Homogeneous order-independence without the independence hypothesis: scripts/
  check_order_independence.py, 600/600 homogeneous instances with dropped rows identical in
  every order tried (all permutations for 200 tiny instances); negative control
  (non-homogeneous with dependent rows) differs in 583/600. Simulation, not proof.

## 2026-10-06 — Proposition 1 generalized in the paper (drafted at the author's request)

The paper's Proposition 1 now states order-independence for any CONSISTENT system, with no
linear-independence condition; homogeneous ribbon is the always-consistent case and a
successful standard build is consistent by definition. Proof in
docs/order-independence-proof.md ("General statement adopted in the paper"). Simulation
extended with case D (consistent non-homogeneous systems with redundant rows): 600/600
identical in every order; output saved to results/order_independence_check.txt (C34). The
hedges about dependent rows were removed from the abstract, introduction, ARM and RocksDB
sections, conclusion and README. Status of the mathematics: drafted 2026-10-06, simulation-
checked, consistent with the 54 fingerprint matches and E5's 443 byte-identical filters; NOT
yet read by the author or anyone external.

## 2026-10-06 — Double check of the generalized Proposition 1

Three independent checks (details in docs/order-independence-proof.md, "Double check"):
referee read (math valid; wording overclaims found), exhaustive enumeration of small systems
(C36, no violation), and a direct test on the unmodified pinned kernel with overloaded filters
(C35, identical under 25 shuffled orders with up to 24,980 of 50,000 rows dropped).

Corrections made as a result:
- Paper: proposition now says "for one fixed hash seed and table size" and that g must not
  depend on table contents or history; proof sketch step (i) completed; the claim for standard
  ribbon is scoped to kernels that fail only on a zero row with nonzero result, and BuRR-style
  bumping is excluded; the sentence attributing cross-machine identity to the proposition was
  wrong and is fixed; the RocksDB sentence now states the per-seed argument and the dependence
  on where the reorder sits (RocksDB takes the starting seed and filter length from the first
  collected hash; the patch reorders after both).
- Proof doc: step 1 gaps filled, inconsistent-system corollary re-justified, superseded section
  marked, and a hand-typed control count ("17 + 0") that no longer matched the artifact (27 + 0
  after the script gained case D) replaced by a pointer to the artifact. That was a provenance
  slip of mine: a number typed from one run and not regenerated.
- Finding worth keeping: at the benchmark's normal sizing no rows are dropped in a 200K-key
  test, so the paper's 54 fingerprint matches were weak evidence for the redundant-row case.

## 2026-10-06 — Appendix restructuring for the SEA page limit (no content removed)

paper/main.tex now ends with an appendix after the bibliography: A (proof sketch of
Proposition 1 and the three checks), B (E3: RocksDB Bloom vs ribbon at matched FPR, with its
table), C (E4: equal-thread comparison, with its table). The main text keeps a short paragraph
with the headline numbers and a pointer for each. scripts/make_lipics.py carries the appendix
into the LIPIcs build. Anonymous LIPIcs build: 16 pages; main text ends ~40% down page 13,
appendix pages 14-16. NeurIPS-style build: 13 pages. No numbers changed.

## 2026-10-07 — Authorship voice, commit messages, hashes

- The paper is single-author; its text now uses first-person singular throughout (72
  replacements; "(ours)" in table rows became "(this work)").
- The four protocol commits on `prior-art-corrections` were recreated with shorter messages.
  Trees, parents' order, author and commit dates are unchanged; only the messages differ, so
  the hashes changed: 1526465 -> fabfce3 (E3 freeze), 059084f -> 74de203 (E4 freeze),
  cfdbeac -> 48fd3f2 (E4 amendment), 3e1a551 -> ebcecdc (E5 freeze). CLAIMS.md and this log
  cite the new hashes. The branch had not been pushed.
- Language pass on paper/main.tex (2026-10-06): wording only, plus three corrections where the
  RocksDB text disagreed with its own table (pleated and stock build cost by size; banding
  cache misses per key; an imprecise "about 2x" removed).
