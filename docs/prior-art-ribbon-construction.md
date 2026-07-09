# Prior-art audit: ribbon / binary-fuse construction (2026-07-09)

Code-level adversarial audit (BuRR master + parallel branch, RocksDB main, FastFilter repos
read at source level; papers verified from PDFs). Backs the E1b Phase-1 gate decision and
CLAIMS C15. Companion to docs/prior-art-construction.md.

## What is already taken (claims that die)

- **Sort-then-eliminate banded GF(2)**: Dietzfelbinger & Walzer ESA 2019 (SGAUSS,
  arXiv:1907.04750 — "sorting the rows according to the positions of the blocks transforms
  the matrix into a kind of band matrix"); implemented with ips2ra radix sort in BuRR
  (construction.hpp:79-106, sorts (permuted-start, index) pairs, bucket-ascending /
  start-descending via XOR trick); parallelized via thread-boundary bumping in parallel BuRR
  (arXiv:2411.12365, 14× on 32 cores).
- **Arbitrary-order on-the-fly banding with backtracking**: the ribbon paper's selling point
  ("there is no need to pre-sort", arXiv:2103.02515) + RocksDB production
  (ribbon_alg.h:546-596; BacktrackStorage rollback; up to 256 seed retries).
- **Construction prefetch pipelining**: RocksDB ribbon_alg.h:650-678 (pipelined w/prefetch,
  gated by num_starts>1500, comment "TODO: verify/validate"); BuRR input prefetch 32 ahead
  (construction.hpp:212-215); RocksDB Bloom 8-deep pipeline; ribbonGo. Exists in CODE —
  no published analysis anywhere.
- **Segment reordering for fuse-family scatter locality**: binary fuse JEA 2022, explicitly
  cache-motivated single counting-sort pass (binaryfusefilter.h:327-343); lowmem variants are
  the recommended defaults.
- **Buffered/deferred scatter**: xor filter applyBlock (fastfilter_cpp xorfilter.h:100-162),
  acknowledged in print.
- **Sharded/parallel construction**: BuRR §11.3, parallel BuRR, Vigna ε-cost sharding
  (arXiv:2503.18397, ~60 ns/key at trillion-key scale), Genuzio–Ottaviano–Vigna SEA 2016.
- **Streaming block back-substitution to interleaved output**: RocksDB/BuRR both do
  register-buffered column-major per-block back-substitution (scalar).

## Live territory (audit-verified absences)

1. **SIMD/vectorized banded elimination** — nothing exists (M4RI is dense-only; both ribbon
   papers leave construction vectorization unaddressed; the "not generally workable" dismissal
   was query-side only).
2. **Eliminating/fusing the sort** — parallel BuRR states "a large portion of the construction
   time is spent on parallel sorting" but does not attack it. Partition-instead-of-sort
   (approximate ordering) for banding locality is unclaimed.
3. **SIMD/NT-store back-substitution beyond the existing block structure** — no attempt.
4. **GPU ribbon construction** — fully open (nearest: GPU BDZ-peeling in a 2023 master's
   thesis; GPU PHF constructions avoid linear algebra entirely per the 2025 MPHF survey).
5. **Quantified prefetch/MLP analysis of filter construction** — code-only, unevaluated in
   print (RocksDB's own TODO).
6. **Incremental/mergeable ribbon across LSM compaction** — fully open. Frame with Kuszmaul
   et al. SODA 2025 (dynamic-retrieval bounds), IXOR/IBIF (TNSM 2024, bolt-on updatability),
   RocksDB blog (rebuild-per-SST status quo).

## Published construction numbers (hardware-attributed)

| source | hardware | ns/key (construction) |
|---|---|---|
| BuRR Table 2 (SEA 2022) | EPYC 7702, clang 11 | n=10⁶/10⁸: BlockedBloom 3/17 · Xor8 91/159 · StdRibbon w64 32/70 · Homog w64 28/67 · BuRR2bit w64 110/115 |
| RocksDB blog (Dillinger 2021-12-29) | unstated | Bloom 32 vs Ribbon 140 (~4.4×); temp mem 230 vs 75 bits/key |
| binary fuse JEA 2022 | i7-6700 Skylake | plots only; fuse >2× faster than xor to build; fuse≈ribbon (Intel), fuse<ribbon (AMD) |
| xor_singleheader README | unstated | ~36 ns/entry, ~24 B/entry temp |
| Vigna 2503.18397 | per paper | ~60 ns/key sharded at 10¹² keys |

Downstream evidence construction cost matters: ShockHash/SicHash report BuRR construction
dominating their builds; ZOR (arXiv:2602.03525) admits building "several-fold slower than
highly optimized fuse builders".

## Must-cite

DW ESA 2019; ribbon arXiv:2103.02515; BuRR SEA 2022 + repo; parallel BuRR arXiv:2411.12365 +
parallel branch; RocksDB ribbon_alg.h/ribbon_impl.h/filter_policy.cc + 2021 blog; binary fuse
JEA 2022 + FastFilter repos; Walzer SODA 2021; Genuzio et al. SEA 2016; Vigna 2503.18397;
Kuszmaul SODA 2025 + IXOR/IBIF (if incremental); ShockHash/SicHash; ZOR; AMAC/Chen ICDE 2004
(if prefetch claims); MPHF survey arXiv:2506.06536.

## Residual unknowns

IEEE 9920402 (paywalled ribbon reimplementation, retrieve pre-submission); parallel-BuRR full
PDF phase breakdown; FXLT (arXiv:2312.13541) internals; ribbon paper §6's own construction
table; Vigna per-shard kernel details (read vigna/sux); ZOR revisions near submission.
