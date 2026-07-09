# E1a — read-free bulk construction of blocked Bloom filters

**Status: FROZEN (2026-07-09), after pre-data revision for the prior-art audit
(docs/prior-art-construction.md). No timing data for the new strategies existed at freeze
time; the bit-identity unit tests were the only code executed.**

## Audit incorporation (pre-freeze revision, 2026-07-09)

The adversarial prior-art audit found the draft's H1 already published: Schmidt, Bandle &
Giceva (PVLDB 2021) demonstrate radix-partitioned filter construction (SWWC + NT stores, up to
9× build speedup, "partitioning pays off past L2"), and fastfilter_cpp has shipped
region-buffered `AddAll` since 2018. Kill criterion K2 therefore PARTIALLY FIRED before data
collection, and the protocol is revised as follows — this is a hypothesis narrowing, done
before any timing run, not a post-hoc reframe:

- The `partitioned` strategy is downgraded from novelty candidate to **prior-art-shaped
  baseline** (Schmidt-style partitioning, but producing a monolithic bit-identical filter).
- The sole novelty candidate is the **read-free apply** (`partitioned_grouped`): partition
  pre-merged (block, mask) pairs, OR-aggregate each block's masks in registers, emit exactly
  one store per block — filter memory is never read (no read-for-ownership traffic). The audit
  found no anticipation of this combination; the closest systems all RMW filter memory, and
  fastfilter's own data shows buffering WITHOUT mask pre-merge yields only ~0–10%.
- fastfilter `AddAll` (ids 43/52) joins the anchors now; Schmidt's tum-db/partitioned-filters
  harness becomes a required baseline for any paper-level claim (pilot may precede its port).
- Claim-framing rule adopted: never present partitioning/buffering/bulk-build as novel.

## Motivation (from measured artifacts + literature)

E0 killed probe-side layout work on OoO x86: probes are bound by memory-level parallelism, and
the compute is already optimal (results/e0a/ANALYSIS.md, CLAIMS C6–C7). Construction is the
surviving candidate because it is *reorderable*: the builder controls the order of bit-setting,
so random read-modify-writes can be converted into streaming writes. The cost is real and
already measured on this machine (CLAIMS C9, results/e0a/anchor/): fastfilter_cpp BlockedBloom
per-key construction degrades from 2.22 ns/key at 1M keys (0.07 misses/key) to 11.48 ns/key at
100M keys (0.96 misses/key, IPC 0.48) — i.e., bulk build at scale is one random RMW miss per
key. The literature names filter (re)construction cost as an open problem (ribbon = 3–4×
Bloom's build CPU; RocksDB gates ribbon adoption on it; every LSM compaction rebuilds filters).

## Hypotheses (pre-registered, post-audit numbering)

- **H1 (replication, NOT novelty — Schmidt et al. PVLDB 2021):** partitioned two-pass
  construction (`partitioned`: L2-sized spans, counting-sort scatter of (block, mask) pairs,
  cache-resident RMW merge) beats per-key insertion by ≥2× at ≥64MB filter sizes on a
  MONOLITHIC filter. Derivation (honest back-of-envelope, not citable): per-key at scale ≈
  11.5 ns/key measured (CLAIMS C9, one random RMW miss/key); partitioned streaming traffic ≈
  ~33B/key ≈ 2–4 ns/key at realistic single-core bandwidth.
- **H2 (the novelty candidate — read-free apply):** `partitioned_grouped` — group each
  partition's pairs by exact block, OR-aggregate each block's full 8×u32 mask in registers,
  emit exactly one store per block, never read filter memory — adds ≥1.2× over `partitioned`
  at ≥64MB, and the x86 non-temporal-store variant adds further by eliminating
  read-for-ownership traffic (RMW moves ~2 lines of traffic per filter line: RFO read +
  writeback; read-free NT moves ~1). If H2 fails, K2 has fully fired: no novelty survives;
  the salvage paths below apply.
- **H3 (portability):** the safe-Rust grouped builder (no NT stores — portable) still clears
  H2's ≥1.2× on ARM NEON (tf-bench-arm, when capacity allows) from the same source; the
  NT-store apply is documented as an x86-specific variant (aarch64 STNP is inline-asm-only and
  out of scope for this experiment).

## Kill criteria (pre-registered)

- **K1:** if per-key insertion ≥ partitioned everywhere (OoO absorbs construction misses as it
  does probe misses), construction-side layout work dies too. The project's deliverable becomes
  the measurement study: "batching/layout tricks for filter operations are obsolete on modern
  OoO cores" (E0 + E1a nulls + cross-ISA), target DaMoN/experiments track.
- **K2 (partially fired 2026-07-09, see Audit incorporation):** the audit killed broad
  partitioning novelty (Schmidt 2021, fastfilter AddAll, Canim 2010, Beamer 2017); it did NOT
  find the read-free (block,mask)-partitioned register-merge apply. K2 fires FULLY if either
  (i) H2's measured gain over `partitioned` is <1.2× everywhere, or (ii) later review
  surfaces anticipation of the read-free apply (residual unknowns listed in the audit doc).
  Salvage paths: (a) ribbon/binary-fuse construction (their scatter is the expensive one),
  (b) the cross-ISA/ARM angle, (c) LSM-compaction end-to-end integration, (d) measurement
  study of E0+E1a nulls.
- **Correctness gate (before any timing is interpreted):** the partitioned builders must produce
  a filter **bit-identical** to per-key construction over the same key set (OR is commutative —
  any deviation is a bug), plus the E0 FPR gate re-applied.

## Fixed design

- Filter: same SBBF geometry as E0 (Parquet spec; 256-bit blocks, 8×u32, k=8, salts,
  fastrange block selection, splitmix64-mixed u64 keys). 10 bits/key.
- Key sets: deterministic KeyStream seeds as E0 (members 0xA11CE). Keys arrive UNSORTED
  (hash-random) — the honest hard case; LSM keys are sorted by key, which is hash-random per
  block, same thing after mixing.
- Sizes: n ∈ {1M, 10M, 53.7M, 100M, 429M} keys → filters ~1.25MB, 12.5MB, 64MB, 125MB, 512MB.
- Strategies:
  1. `perkey` — existing `BlockedFilter::insert` loop (E0 code, unchanged).
  2. `perkey_prefetch` — two-phase batched insert with prefetch (control: is MLP alone enough?
     this is the RocksDB-AddAllEntries shape).
  3. `partitioned` — two-pass radix scatter + cache-resident RMW merge (the Schmidt-shaped
     baseline, monolithic output).
  4. `partitioned_grouped` — per-block register OR-merge, one store per block, filter never
     read (H2 novelty candidate, portable safe Rust).
  5. `partitioned_grouped_nt` — as 4 with non-temporal stores in the apply (x86 only; zero
     RFO traffic).
  P (partition count) chosen so each partition's filter span ≤ 1MB (half of one P-core's L2).
- Metrics: ns/key (criterion, ≥20 samples), plus one `perf stat` run per (strategy × size) for
  cycles/key, misses/key, IPC when perf is available; peak RSS recorded (partitioning costs
  ~20B/key transient memory — report it, don't hide it).
- Anchors: fastfilter_cpp `BlockedBloom` (id 51, per-key add), `BlockedBloom-addAll` (id 52),
  `Bloom8-addAll` (id 43) at the same n, same machine, same session. Paper-level claims
  additionally require the tum-db/partitioned-filters harness (Schmidt et al.) — not required
  for the pilot.
- Machines: local i9-14900HX (AVX2) first; tf-bench-arm (NEON) when available; x86 AVX-512
  deferred per user decision.

## Decision rules

- R1: H1 confirmed at ≥64MB sizes → construction direction alive; E1b = ribbon/binary-fuse
  construction becomes the next protocol.
- R2: H2 confirmed anywhere → the transposition angle specifically is alive; write-up leads
  with it. H2 refuted → drop the FastLanes framing from claims; keep partitioning if R1 held
  and prior-art audit allows.
- R3: K1 fires → pivot to measurement-study write-up (still a paper; nulls published).
- All rule evaluations are mechanical, in analyze.py, from raw artifacts (E0 house style).

## Stages

```bash
python run.py --stage check    # unit tests incl. bit-identity of all builders — no artifacts
python run.py --stage pilot    # 1M & 10M only, local; sanity + variance estimate (NOT citable)
python run.py --stage bench    # full sweep (refuses to run before check+pilot artifacts exist)
python run.py --stage perf     # perf-stat pass (optional; degrades gracefully without perf)
python run.py --stage anchor   # fastfilter_cpp ids 43,51,52 at matching n
python run.py --stage analyze  # derives results/e1a/ANALYSIS.md; evaluates R1-R3
```

## Threats to validity (declared up front)

- Partitioning needs ~20B/key transient buffer — a real memory cost per-key insertion doesn't
  pay; reported alongside every throughput claim.
- Single-threaded first: multicore construction shifts the bandwidth/MSHR math; a follow-up
  protocol, not a silent extension of this one.
- CAX (ARM) is shared-vCPU: report CIs and repeats; label accordingly.
- The 429M point exceeds the 100M anchor's largest n; anchor comparisons stop at 100M.
- fastbloom is excluded here: its insert path hashes internally (asymmetry documented in E0);
  construction comparisons use our own strategies + fastfilter_cpp anchors only.
