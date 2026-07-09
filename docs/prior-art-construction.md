# Prior-art audit: bulk construction of membership filters (2026-07-09)

Adversarial sweep (8 threads, primary-source verified — PDFs/code, not snippets) against the
E1a claim: (a) radix-partition (block-index, mask) pairs to L2-sized spans, (b) per-block
register OR-merge, one store per block, filter memory never read. Backs CLAIMS C12 and the E1a
protocol's freeze revision. Two fetch results were caught fabricating during verification and
discarded — quotes below were re-verified against extracted text.

## Killers of the broad claims (must cite and differentiate)

1. **Schmidt, Bandle, Giceva, "A Four-Dimensional Analysis of Partitioned Approximate
   Filters," PVLDB 14(11), 2021** (https://www.vldb.org/pvldb/vol14/p2355-schmidt.pdf,
   code https://github.com/tum-db/partitioned-filters). Radix partitioning for filter BUILD
   and probe, "boosts the build and lookup throughput for large filters by up to 9x and 5x";
   single-pass partitioning with software write-combine buffers + non-temporal stores; "as
   soon as the filter size exceeds the L2 cache, partitioning pays off." Source-verified
   deltas: partitions RAW KEYS (not masks); per-partition build is per-key gather→OR→scatter
   (reads filter memory every insert); output is a PHYSICALLY PARTITIONED filter (lookup
   routes by partition), not a bit-identical monolithic one. **Mandatory baseline.**
2. **fastfilter_cpp buffered `AddAll`** (in-repo since Oct 2018; acknowledged in Graf &
   Lemire JEA 2022). Region-buffered bulk build for classic AND blocked Bloom (256–512KB
   regions), scalar/AVX2 RMW apply per key. Their own measurement: blocked-Bloom AddAll is
   ~10% faster at 100M and SLOWER at 10M — direct evidence that buffering WITHOUT mask
   pre-merge underperforms. **Mandatory baseline + motivation data point.**
3. **Canim, Mihaila, Bhattacharjee, Lang, Ross, "Buffered Bloom Filters on Solid State
   Storage," ADMS@VLDB 2010.** Deferred, grouped bit-setting per cache-sized sub-filter,
   explicit cache-miss amortization argument, notes in-memory applicability. Buffers raw bit
   offsets; mandatory read-modify-write page flushes.
4. **Beamer, Asanović, Patterson, IPDPS 2017 (propagation blocking).** The generic two-phase
   pattern — radix-partition (payload, destination) pairs into cache-sized bins with SWWC+NT
   stores, then bin-local accumulate — published for scatter-reduce (+= not |=); phase 2 is
   still cache-resident RMW.
5. **Wassenberg & Sanders, Euro-Par 2011.** The exact store discipline ("consecutive
   non-temporal writes ... combined into a single burst", "avoids ... Read-For-Ownership") —
   for radix-sort permutation, no aggregation, no filters.
6. **GPU:** McCoy et al. PPoPP 2023 (Bulk TCF: sort-by-block + shared-memory build + coalesced
   write-out; NOT applied to their Bloom baseline); cuSBF arXiv:2606.24417 (warp-level
   register OR-merge of block masks before one atomicOr per run — nearest (b) analog, but
   RMW atomics, minimizer-driven locality, domain-specific).
7. **Shipped engine code:** Arrow Acero partitions blocked-Bloom build input by block-ID high
   bits (for lock-free parallelism; RMW apply). RocksDB `FastLocalBloomBitsBuilder`
   AddAllEntries: 8-deep software-pipelined prefetch RMW (hides, doesn't eliminate, reads).
   Parquet/Kudu/Impala/DuckDB/ClickHouse/Pebble: per-key RMW builds.
8. Also: Putze/Sanders/Singler 2007/09 (per-element construction; precomputed per-key SIMD
   bit patterns — one element at a time); Polychroniou & Ross 2014 / Polychroniou et al. 2015
   (partitioning machinery; probe-only Bloom; in-register conflict serialization for RMW
   correctness); Balkesen et al. 2013; binary-fuse JEA 2022 (single-pass segment-sort of keys
   for peeling); BuRR SEA 2022 (IPS2Ra sort of (hash,value) by bucket); parallel BuRR
   arXiv:2411.12365 (thread sharding); Roaring construction engineering (sort by high bits,
   materialize container once).

## What no located work does (the surviving narrow claim)

Partition payload = precomputed OR-able (block, mask) pairs; apply = register OR-aggregation
per block emitting EXACTLY ONE (non-temporal) store per block/line, so filter memory is NEVER
read (zero RFO traffic); output bit-identical monolithic blocked Bloom (lookup semantics
unchanged, unlike Schmidt's partitioned structure). Every located build-side system reads
filter memory. Expected reviewer attack: "engineering synthesis" of Wassenberg + Beamer +
fastfilter + Putze; counter: none eliminates the filter-memory read for colliding updates —
that requires the mask pre-aggregation step none has — and the one system that buffered
blocked-Bloom builds without it (fastfilter) measured ~0–10%.

## Residual unknowns (declared)

Putze JEA 2009 journal delta (paywalled); SAP FiRe (closed source); patents US10915576,
US10572260 (unexamined); Breyer & Liu arXiv:2312.13541; unpublished industrial engines.

## Consequences applied to the E1a protocol

- H1 reframed: replication/extension of Schmidt-style partitioned build on a MONOLITHIC
  filter (not novelty). H2 (read-free grouped apply) is the sole novelty candidate.
- tum-db/partitioned-filters and fastfilter AddAll (ids 43/52) become required baselines for
  any paper claim; fastfilter anchors suffice for the local pilot.
- Framing rule: never claim "partitioned/bulk/buffered filter construction" as new.
