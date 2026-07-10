# Ribbon Filter Construction at Bloom-Filter Speed: Partition-Instead-of-Sort, and Where Layout Tricks Cannot Work

Brian Sam-Bodden — Integrallis Software — Draft v0.2 (2026-07-09)

## Abstract

Space-optimal static filters (ribbon, binary fuse) trade construction CPU for space, and that
trade gates their adoption: RocksDB measures ribbon construction at ~4x the cost of Bloom and
ships Bloom by default. We present a systematic study of where memory-layout and batching
techniques can and cannot accelerate filter operations on modern out-of-order x86, built from
three pre-registered experiments with mechanical decision rules. Two are nulls with mechanisms:
point-probe batching is bound by memory-level parallelism that the out-of-order window already
saturates, and blocked-Bloom bulk construction is prefetch-hidable, capping partitioned
construction at 1.7x and refuting read-elimination applies outright. The third localizes the
one construction phase whose misses prefetch *cannot* hide — the data-dependent row-reduction
chains of homogeneous ribbon banding (5.8 misses/key at 100M keys) — and shows that a
single-pass, cache-window *partition* of the insertion stream recovers 98% of the locality
benefit of the full start-position sort used since SGAUSS and BuRR, at one quarter of the
sorting cost, including against BuRR's own radix sorter. Sequential construction improves
2.05–2.24x (49.6 to 24.2 ns/key at 100M keys). We further observe that ribbon banding produces
*bit-identical* solutions under any insertion order, which turns reordering into a provably
output-neutral transformation and makes a boundary-deferring parallel variant trivially
verifiable: banding speeds up 4.25x at 8 threads against the variant's own single-thread run
(3.5x against the best sequential banding), for an 11.9 ns/key total at 16 threads — ribbon
construction at sequential Bloom-insertion speed. Every number derives from committed raw
artifacts; protocols, amendments, and an instrument flaw caught by cross-harness anchoring are
part of the record.

## 1. Introduction

Approximate-membership filters guard nearly every read path in LSM-tree storage engines, and
they are rebuilt on every flush and compaction. Ribbon filters [Dillinger & Walzer 2021]
reduce space overhead below 10% (BuRR below 1% [SEA 2022]) versus Bloom's 44%, but
construction cost blocks adoption: RocksDB's production measurements put ribbon construction
at ~140 ns/key versus ~32 for Bloom [RocksDB blog 2021], and its own hybrid policy exists to
dodge that cost on hot levels. The construction side is an acknowledged open problem: the
parallel-BuRR authors note that "a large portion of the construction time is spent on parallel
sorting" [arXiv:2411.12365], and recent structures concede multi-fold construction slowdowns
against optimized fuse builders [ZOR, arXiv:2602.03525].

This paper asks a narrow question with a broad setup: *which* filter operations still have
memory-layout headroom on modern out-of-order (OoO) CPUs, and which do not? We answer it with
three pre-registered experiments (protocols, thresholds, and kill criteria frozen before data
collection; deviations recorded as amendments), and we find that the answer has a clean
mechanism: layout tricks pay exactly where misses form *data-dependent chains* that neither
the OoO window nor software prefetch can overlap.

**Contributions.**

1. **Two nulls with mechanisms** (§3). Miss-dominated point probes are bound by the per-core
   limit on outstanding misses; software prefetch already reaches ~88% of that ceiling, and
   cross-key SIMD batching *loses* to per-key scalar probing even with all addresses
   L1-resident. Blocked-Bloom bulk construction misses are independent and prefetch-hidable:
   radix-partitioned construction (Schmidt et al., PVLDB 2021) caps at 1.45–1.71x against
   per-key insertion, a software-pipelined prefetch loop (shipped, unevaluated, in RocksDB)
   recovers most of that without transient memory, and a read-free register-aggregated apply
   is 1.5x *slower* than partitioned RMW — partitioning has already converted the target
   misses into L2 hits.
2. **Partition-instead-of-sort for ribbon construction** (§4). Homogeneous ribbon banding at
   scale pays 5.8 DRAM misses/key in dependent row-reduction chains. A single counting pass
   that groups keys by L2-sized start-windows — approximate order only — recovers 98.3–98.4%
   of the miss reduction of the full start-position sort (SGAUSS [ESA 2019], BuRR) at
   5.5–6.1 ns/key versus 23.9–28.1 for BuRR's own ips2ra sorter, yielding end-to-end
   construction 2.05–2.24x faster than the reference prefetch-pipelined build. The choice of
   window size barely matters (totals within 13% across 2^13–2^20 slots).
3. **Order-independence and verifiable parallelism** (§5). Ribbon banding with
   first-coefficient-always-one pivoting produces bit-identical solutions under any insertion
   order (proved for linearly independent rows; observed in 54/54 runs across sizes, orders,
   and thread counts). Reordering is therefore provably output-neutral, and a slot-range
   parallel variant with boundary deferral (≤0.23% of keys) verifies itself by fingerprint:
   banding speeds up 4.25x at 8 threads and 7.56x at 16 against its own single-thread run
   (3.5x and 6.3x against the best sequential banding), total 11.9 ns/key at 100M keys.
4. **A quantified account of construction prefetch** (§6), the first evaluation of the
   pipeline RocksDB ships behind a "TODO: verify/validate" comment: worth 1.5–1.7x on
   unsorted banding, and largely subsumed by partitioning.

All measurements ran on an i9-14900HX (AVX2, no AVX-512) under pinned reference harnesses
(fastfilter_cpp, whose ribbon implementations are the ribbon author's; BuRR; FastLanes), with
raw artifacts, a claims ledger, and automated integrity checks (information-theoretic FPR
bounds, provenance) committed alongside the code. ARM replication is prepared and pending
cloud capacity.

## 2. Background

**Ribbon banding.** A ribbon filter solves a banded GF(2) system: each key hashes to a start
column s and a w-bit coefficient row; insertion XOR-reduces the row against existing rows
until an empty slot absorbs it. Dietzfelbinger and Walzer showed that sorting rows by start
position makes banded elimination linear (SGAUSS); the ribbon paper's contribution was
on-the-fly insertion in *arbitrary* order; BuRR reinstates a bucket sort (ips2ra) plus
bumping. Homogeneous ribbon never fails construction and needs no per-key result rows.

**Binary fuse** construction partially sorts keys by segment explicitly to reduce cache
misses [Graf & Lemire, JEA 2022]; our Phase-0 characterization measures that fix directly
(plain xor: 9.45 misses/key; binary fuse: 1.08).

## 3. Where layout tricks cannot work

### 3.1 Point probes are MLP-bound

Pre-registered experiment E0 compared probe strategies over identical split-block Bloom
filters (Parquet geometry) from 32KiB to 512MiB. A vertical, lane-structured batch probe
written as plain Rust auto-vectorizes (packed-SIMD disassembly committed) yet loses to per-key
scalar probing at *every* size — even with all addresses forced L1-hot (555 vs. 665 Mops/s),
because the split-block check is already horizontally SIMD within one key and AVX2 gathers
cannot beat eight independent scalar loads that the OoO window overlaps for free. At RAM sizes
the same instruction stream runs 5–6x faster when L1-hot: probing is bound by memory-level
parallelism, and software prefetch reaches ~88% of the single-core outstanding-miss ceiling.
There is no compute bottleneck for a layout to remove.

### 3.2 Blocked-Bloom construction is prefetch-hidable

Experiment E1a measured five bulk builders at 1M–429M keys with a bit-identity gate (OR
commutativity). Per-key insertion degrades to one random read-modify-write miss per key at
scale (11.5 ns/key at 100M; IPC 0.48); radix-partitioned construction in the style of Schmidt
et al. reaches only 1.45–1.71x — and a software-pipelined prefetch insert (RocksDB's shape)
achieves 6.1–8.9 ns/key with *zero* transient memory, beating partitioning up to 100M keys. A
read-free apply — partition pre-merged (block, mask) pairs, OR-aggregate each block in
registers, exactly one store per block, never read filter memory — is 1.5x *slower* than
partitioned RMW, with non-temporal stores changing nothing: partitioning already converted the
target misses into L2 hits, so the second grouping pass buys back only L2 latency. Bloom
construction misses are *independent*; the memory system hides them.

## 4. Partition-instead-of-sort for ribbon

### 4.1 The target, measured

Phase-0 characterization (reference fastfilter_cpp binary, 3 reps) shows homogeneous ribbon
construction at 100M keys costs 50.6 ns/key at IPC 0.64 with **5.81 cache-misses/key** —
banding walks a random start per key through a 1.3GB working set, and each row-reduction step
depends on the previous XOR, so prefetch cannot dissolve the chain the way it does Bloom's
independent probes.

### 4.2 Design

We permute only the *input*: a single counting pass buckets keys by floor(s / 2^16) (windows
of 2^16 slots ≈ 768KiB of banding state, under half an L2), recomputing the hash rather than
materializing pairs; a second pass emits keys in window order. The unmodified reference kernel
(its prefetch pipeline included) then consumes the permuted array. Everything downstream —
banding, back-substitution, queries — is the ribbon author's code.

### 4.3 Results

Table 1 (100M keys; 400M in artifacts). The partition pass costs 5.5–6.1 ns/key against
23.9–28.1 for ips2ra in our driver (17.3 inside BuRR's own bench); banding lands within 13% of
banding-after-full-sort (15.2 vs. 13.4 ns/key), i.e., the partition recovers 98.3–98.4% of the
sort's miss reduction (5.75 → 0.17 vs. → 0.075 misses/key). End-to-end: 24.2 vs. 49.6
(reference) and 40.7 (best full sort) — 1.68x over the best full sort at both sizes. As an
anchor, BuRR end-to-end builds at ~70 ns/key at its top recursion level on this machine
(~75.5 across all levels; different structure: r=8, ~1% space overhead, bumping); our
homogeneous configuration is 7.63 bits/key at 0.81% FPR (~9.5% overhead). A window sweep
across 2^13–2^20 slots moves totals only between 23.8 and 26.9 ns/key: the technique has no
tuning cliff, and our registered result (at 2^16) was conservative — 2^14 is mildly better.

**Table 1: Homogeneous ribbon construction, 100M keys, ns/key (mean of 3).**

| strategy | reorder | banding | total | miss/key |
|---|---|---|---|---|
| unsorted, no prefetch | — | 76.9 | 80.8 | 5.81 |
| unsorted + prefetch (ref.) | — | 46.1 | 49.6 | 5.75 |
| full sort (std::sort) | 76.8 | 15.5 | 96.1 | 0.074 |
| full sort (LSD radix) | 23.4 | 14.7 | 41.7 | 0.076 |
| full sort (ips2ra) | 23.9 | 13.4 | 40.7 | 0.075 |
| **partitioned (ours)** | **5.5** | 15.2 | **24.2** | 0.170 |
| parallel, 8T (ours) | 5.5 | 4.3 | 14.6 | — |
| parallel, 16T (ours) | 5.7 | 2.4 | **11.9** | — |

## 5. Order-independence and parallel construction

**Proposition (order-independence).** Let E = {(r_k, b_k)} be equations over GF(2)^m whose
rows are linearly independent, each r_k carrying a leading 1 at its start position. Then
banding (store each reduced row at the slot of its leading position) followed by
back-substitution with all free slots fixed to zero yields the same solution Z under every
insertion order of E.

*Proof sketch.* The occupied-slot set equals the canonical pivot set of V = span{r_k} (the set
of leading positions realized in V), which depends only on V; the stored system is
row-equivalent to E; and pinning the order-independent free coordinates to zero extends E to a
full-rank system with a unique solution. (Full argument in the repository,
docs/order-independence-proof.md; with dependent rows the enforced subset may differ by order,
which the per-run fingerprint gate detects.)

Empirically: across all sequential and parallel runs (sizes to 400M, six orderings, thread
counts to 16), the banded solution is *byte-identical* under an FNV fingerprint. Reordering is
thus provably output-neutral — the linear-algebra analogue of OR-commutativity — and it
converts parallel-construction verification from a distributed-systems problem into a
checksum. Our parallel variant assigns disjoint window ranges (split at equal key counts) to
threads; keys starting within 2^14 slots of a range boundary defer to a sequential tail
(0.015–0.226% of keys), following parallel BuRR's boundary idea. Banding scales
1.81/2.83/4.25/7.56x at 2/4/8/16 threads against its own T=1 (3.5/6.3x at 8/16 threads against
the best sequential banding; the parallel path carries ~20% defer/copy overhead); the residual
is Amdahl's: the sequential counting pass (5.7) and back-substitution (3.8 ns/key at 16
threads) now dominate the 11.9 ns/key total. Both are parallelizable (counting sort trivially;
back-substitution as in parallel BuRR) — future work.

## 6. Construction prefetch, evaluated

RocksDB ships a software-pipelined construction prefetch behind a comment reading "TODO:
verify/validate"; the reference harness enables the same pipeline above 1500 slots. Our
no-prefetch control isolates it: 1.5–1.7x on unsorted banding (76.9 → 46.1 ns/key at 100M).
It attacks the *start-locating* miss but cannot touch the dependent reduction chain, which is
why partitioning strictly dominates it here while the analogous prefetch strategy *wins* for
Bloom construction (§3).

## 7. Related work

Sorted banded elimination: Dietzfelbinger & Walzer (ESA 2019), BuRR (SEA 2022), parallel BuRR
(arXiv:2411.12365). Arbitrary-order banding and production engineering: ribbon
(arXiv:2103.02515), RocksDB. Cache-conscious filter construction: buffered Bloom filters
(Canim et al., ADMS 2010), radix-partitioned filters (Schmidt et al., PVLDB 2021), binary-fuse
segment sort (JEA 2022), xor-filter buffered scatter (JEA 2020); the generic two-phase
partition-then-accumulate pattern appears as propagation blocking (Beamer et al., IPDPS 2017)
with write-combining from Wassenberg & Sanders (Euro-Par 2011). SIMD probe-side layouts:
Polychroniou & Ross (DaMoN 2014), Lang et al. (PVLDB 2019), split-block Bloom
(arXiv:2101.01719). Our delta to BuRR is precise: BuRR sorts fully (ips2ra) to enable
threshold-based bumping and tighter space; we show that for homogeneous ribbon — the variant
RocksDB ships — a counting-pass partition captures 98% of the sort's locality at 4x less
reorder cost, with output-neutrality making the transformation and its parallelization
verifiable.

## 8. Limitations and threats to validity

Single x86 machine so far (AVX2 Raptor Lake); ARM replication is scripted and pending cloud
capacity, and all claims are scoped accordingly. We accelerate *homogeneous* ribbon (~9.5%
space overhead at r=7), not BuRR's sub-1%-overhead structure; the BuRR comparison is an
anchor, not apples-to-apples. Sort baselines include BuRR's own sequential ips2ra but not its
parallel form; our parallel comparison is scoped to banding, and its headline ratios are
against the parallel path's own single-thread run. The order-independence proposition is
proved for linearly independent rows; the dependent case is handled empirically by the
fingerprint gate. LSM end-to-end integration (build-during-compaction) is future work.

## 9. Conclusion

On modern OoO x86, memory-layout optimization for filters pays in exactly one place we could
find — and it is the place that matters: the dependent-miss chains of ribbon construction, the
very cost that keeps space-optimal filters out of production write paths. A one-pass partition
closes 98% of the gap the literature closes with a full sort, at a quarter of the price;
order-independence makes it safe and its parallelization checkable; and 16 threads build
ribbon filters as fast as one thread inserts into a Bloom filter. The two nulls are not
failures of the method but the map that located the win.

**Artifacts.** All protocols, amendments, raw measurements, and integrity tooling are in the
accompanying repository; reproduce.sh re-derives every number in this paper from committed raw
artifacts.
