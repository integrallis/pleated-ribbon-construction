# AMQ Filter Literature Survey (compiled 2026-07-09)

Compiled via a multi-source web sweep (~290 searches/fetches across arXiv, ACM DL, VLDB.org,
USENIX, Dagstuhl, vendor docs) by a research agent, with two spot-verifications rerun
independently (Lang et al. "<2 cycles" abstract claim; the FastLanes-absence finding). Numbers
below are as stated by the cited sources; unreviewed preprints and blog-sourced numbers flagged.
This document backs CLAIMS.md C1.

## Thread 1 — Point-query filters

Two frontiers. Static: Bloom (44% overhead over the −log₂ε bound) → xor (JEA 2020) → binary fuse
(JEA 2022, 8–13% overhead) → ribbon (arXiv:2103.02515, <10%) → BuRR (SEA 2022 best paper, <1%) →
ZOR (arXiv:2602.03525, 2026, preprint). Dynamic: cuckoo (CoNEXT 2014) → Morton (PVLDB 2018) →
CQF (SIGMOD 2017) → vector quotient filter (SIGMOD 2021, AVX-512-native, O(1) inserts at any
load) → prefix filter (PVLDB 2022, insert-only niche) → InfiniFilter (SIGMOD 2023) → Aleph
(PVLDB 2024) → Zeno (SIGMOD 2026, in-place sub-2× expansion). Syntheses: "Beyond Bloom" tutorial
(SIGMOD 2024); "Bloom Filters at Fifty" (Algorithms 18(12):767, 2025); "maplets" position paper
(arXiv:2510.05518).

Key sources:
- Lang, Neumann, Kemper, Boncz, PVLDB 2019: https://www.vldb.org/pvldb/vol12/p502-lang.pdf
  (register-blocked/cache-sectorized Bloom, "<2 cycles/lookup" low-k; repro:
  https://github.com/peterboncz/bloomfilter-repro)
- Cuckoo: https://www.cs.cmu.edu/~dga/papers/cuckoo-conext2014.pdf
- VQF: https://dl.acm.org/doi/10.1145/3448016.3452841
- Xor: https://dl.acm.org/doi/10.1145/3376122 · Binary fuse: https://arxiv.org/abs/2201.01174
- Ribbon: https://arxiv.org/abs/2103.02515 · BuRR: https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SEA.2022.4 (code: https://github.com/lorenzhs/BuRR)
- Prefix filter: https://www.vldb.org/pvldb/vol15/p1311-even.pdf (code: https://github.com/TomerEven/Prefix-Filter)
- InfiniFilter: https://dl.acm.org/doi/10.1145/3589285 · Aleph: https://arxiv.org/abs/2404.04703 · Zeno: https://nivdayan.github.io/zeno_filter.pdf
- Wormhole (EuroSys 2024, PM): https://dl.acm.org/doi/10.1145/3627703.3629590

## Thread 2 — SIMD / layout (the gap this project targets)

- Vectorized Bloom probing: Polychroniou & Ross, DaMoN 2014. Register-blocking for AVX2/512:
  Lang et al. 2019 (above).
- **Split Block Bloom Filter (SBBF)** — the productionized SIMD design: 256-bit blocks, 8×32-bit
  words, k=8, one bit/word (arXiv:2101.01719). Shipped in Parquet
  (https://parquet.apache.org/docs/file-format/bloomfilter/), Impala/Kudu
  (https://kudu.apache.org/2021/01/15/bloom-filter-predicate.html), Arrow, DuckDB, StarRocks.
- Ribbon is deliberately scalar; authors call special-case SIMD "not generally workable"
  (https://users.cs.utah.edu/~pandey/courses/cs6968/spring23/papers/ribbon.pdf). No vectorized
  ribbon follow-up exists (verified absence).
- GPU filters (active subfield, all non-adaptive): GQF/TCF PPoPP 2023
  (https://dl.acm.org/doi/10.1145/3572848.3577507); Bloom-on-B200 ICS 2026 preprint
  (https://arxiv.org/abs/2512.15595); Cuckoo-GPU (https://arxiv.org/abs/2603.15486, preprint);
  cuSBF (https://arxiv.org/abs/2606.24417, preprint).
- **FastLanes** (Afroozeh & Boncz, PVLDB 2023,
  https://www.vldb.org/pvldb/vol16/p2132-afroozeh.pdf): unified transposed layout
  ("04261537" order, virtual 1024-bit register), scalar auto-vectorized decode >40 values/cycle.
- **Absence finding (C1): seven search formulations found zero papers/preprints/repos applying
  FastLanes-style transposition to any AMQ filter.** All existing SIMD filter layouts are
  cache-line blocking, not cross-lane bit transposition. Name collisions to avoid citing wrongly:
  bioinformatics "Interleaved Bloom Filter" (multi-set indexing, SeqAn/HIBF), ribbon's
  "Interleaved Column-Major Layout" (query locality), "Interleaved Multi-Vectorizing"
  (PVLDB 2019, prefetch hiding).
- Also absent: ARM NEON/SVE filter-specific studies; documented SIMD layouts for ClickHouse
  token/ngram Bloom indexes.

## Thread 3 — Filters in LSM-trees

- Monkey (SIGMOD 2017): optimal per-level FPR allocation, 50–80% lookup-latency reduction.
- ElasticBF (ATC 2019): hotness-aware filter units, 1.94–2.24× read throughput.
- Chucky (SIGMOD 2021): one cuckoo filter with Huffman-coded level IDs replacing all Blooms;
  can't operate below ~8 bits/entry.
- Endure (PVLDB 2022): robust tuning under workload uncertainty.
- CAMAL (SIGMOD 2024): active-learning tuning, +28% avg.
- **Mnemosyne/Mnemosyne+ (SIGMOD 2025, https://dl.acm.org/doi/10.1145/3725327): dynamic BF
  reallocation from per-file statistics — closes barudb's half-finished idea.** Open: changing
  skew.
- Value-of-adaptivity (arXiv:2606.18138, 2026, preprint): compaction-time reallocation captures
  96–99% of continuous tracking's benefit.
- RocksDB production: ribbon since 6.15, ~30% space for 3–4× construction CPU, hybrid policy
  recommended (https://rocksdb.org/blog/2021/12/29/ribbon-filter.html). Bloom remains default.
- SpeedB paired Bloom (https://docs.speedb.io/speedb-features/paired-bloom-filter): pairs
  emptiest/fullest blocks, ~30% memory at ~2× cost. Redis acquired SpeedB 2024-03-21.

## Thread 4 — Learned filters

Kraska SIGMOD 2018 → Mitzenmacher NeurIPS 2018 (sandwiching) → Ada-BF NeurIPS 2020 → PLBF ICLR
2021 → Fast PLBF NeurIPS 2023 (233–778× faster construction) → Cascaded LBF arXiv:2502.03696.
Theory: Daisy Bloom (SWAT 2024); adversary-resilient LBF (ASIACRYPT 2025). Reality check:
2026 benchmark (arXiv:2602.13484) — up to 10² lower FPR but up to 10⁴× slower queries; single
verified production deployment (Roblox Spark joins, 2023). No storage engine ships them.

## Thread 5 — Adaptive filters (FP-feedback)

Broom filter FOCS 2018 (defines adaptivity; impossibility without remote representation) → ACF
ALENEX 2018/JEA 2020 (heuristic) → Cuckooing ACF WADS 2021 (support-optimal, zero metadata) →
Telescoping AF ESA 2021 (first practical provably adaptive, 0.875 extra bits) → **Adaptive
Quotient Filter (PACMMOD/SIGMOD 2024, arXiv:2405.10253): monotone adaptivity, ~100× FPR cut for
<1/1000 bit/item; authors: prior adaptive filters have "no adoption in real-world systems."**
Attacks: perpetual-adaptation DoS (IEEE TNSM 2022); membership leakage (IEEE TIFS 2024).
Note: Aleph is growth-adaptive, NOT FP-feedback-adaptive — do not conflate.

## Thread 6 — Range filters

SuRF SIGMOD 2018 → Rosetta 2020 → Proteus 2022 → SNARF 2022 → Grafite SIGMOD 2024 (space-optimal,
correlation-robust) → Oasis+ PVLDB 2024 → GRF SIGMOD 2024 (global) → Memento SIGMOD 2025 (first
dynamic+robust) → Diva PVLDB 2025 best paper (var-len keys) → Hourglass PACMMOD 2025, Aeris
SIGMOD 2026 (temporal adaptivity). Lower bound: Goswami et al. SODA 2015.

## Open problems named in the literature

1. Dynamic + space-optimal simultaneously (Grafite leaves in-place inserts open).
2. Correlation/adversarial robustness (multiple threads).
3. Temporal-skew adaptivity theory (just opening: Aeris/Hourglass).
4. Concurrency of dynamic/adaptive filters (AQF/Memento use spinlocks).
5. **Filter reconstruction cost during compaction** (ribbon 3–4× worse; relevant to any
   construction-side win we find).
6. Cheap adaptivity (O(n) remote representation reuse).
7. Learned-filter dynamism/robustness/cost accounting.
8. Sub-8-bits/entry allocation regime.
9. Portably-fast in-place filter expansion.

## Under-explored niches (evidence = verified search absence, 2026-07)

1. FastLanes-style transposed layouts for AMQ filters ← **this project (RQ1–RQ3)**
2. Wide-SIMD ribbon (authors' dismissal unrevisited; construction side esp. relevant to LSM)
3. ARM NEON/SVE filter study
4. {adaptive ∩ SIMD ∩ resizable} has no representative
5. Adaptive/expandable filters on GPU
6. Learned filters in a real storage engine
7. Var-length keys in point filters
8. Filter/columnar-layout co-design in analytical engines (Parquet SBBF ∧ FastLanes ecosystems
   never co-designed)
