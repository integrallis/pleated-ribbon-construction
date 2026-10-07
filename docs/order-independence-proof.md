# Order-independence of homogeneous ribbon banding: proposition and proof

Backs the paper's §5 claim (empirically: 54/54 runs bit-identical). Reviewed status: draft
argument, to be checked by an external reader before submission.

## Setting

Banding maintains an m-slot table. Each key contributes an equation r·Z = b over GF(2), where
r is a w-bit coefficient row with leading 1 at start position s(r) (kFirstCoeffAlwaysOne).
Insertion reduces r (and b) by XOR against stored rows at the current leading position until
either (i) the leading position i has an empty slot — store the reduced (row, b) there — or
(ii) r reduces to zero — the key is dropped (homogeneous ribbon accepts this; it is the source
of its FPR/space trade). Back-substitution then computes Z with every empty (free) slot j
assigned a value g(j) that depends only on the slot index j.

CORRECTED 2026-10-06: this document and the paper previously said free slots are fixed to zero.
The pinned reference kernel does not do that for homogeneous ribbon: `LoadRow` in
fastfilter_cpp (924e560) `src/ribbon/ribbon_impl.h` returns
`static_cast<ResultRow>(i * 0x9E3779B185EBCA87ULL)` for an unconstrained row during
back-substitution, matching JACM 73(1) Art. 7 footnote 19 ("a free variable in row i is
assigned p · i mod 2^r for some fixed large odd number p"). The argument below needs only that
the assignment is a function of the slot index; zero is the special case g ≡ 0.

## Proposition

Let E = {(r_k, b_k)} be the multiset of equations, and suppose the rows {r_k} are linearly
independent over GF(2). Then the solution Z produced by banding followed by back-substitution
with free slot j set to g(j) is the same for every insertion order of E.

## Proof

1. **Pivot set is canonical.** For a subspace V ⊆ GF(2)^m and the fixed coordinate order
   1..m, define P(V) = { i : ∃ v ∈ V with leading position i }. P(V) depends only on V (it is
   the column matroid's lexicographic basis, equivalently the pivot set of the reduced row
   echelon form). Banding stores exactly one row per element of P(span{r_k}): a stored row at
   slot i has leading position i by construction, so stored rows are linearly independent;
   with all inserted rows independent, none reduces to zero, so |stored| = |E| = dim V =
   |P(V)|. Hence the OCCUPIED SLOT SET equals P(V) regardless of order.
2. **The solved system is canonical.** The stored (row, b) pairs are order-dependent as
   vectors, but each stored pair is an XOR of a subset of the original equations, so the
   stored system is EQUIVALENT to E: both have exactly the solution set S = {Z : r_k·Z = b_k
   ∀k}, an affine subspace of dimension m − |P(V)| whose free coordinates can be taken to be
   the complement F = [m] \ P(V) (order-independent by step 1).
3. **The output is the unique canonical element of S.** Back-substitution outputs the Z ∈ S
   with Z_j = g(j) for all j ∈ F. The extended system E ∪ {Z_j = g(j) : j ∈ F}
   has full rank |P(V)| + |F| = m, hence a unique solution. Both the constraint set and the
   pinned coordinate set are order-independent, so Z is. ∎

## The dependent case — SUPERSEDED 2026-10-06

This section is kept for the record and is WRONG for homogeneous ribbon: it says dropped keys can
change Z. They cannot, because a homogeneous system is always consistent; see "General statement
adopted in the paper" below. What follows is the original text.

If rows are dependent, WHICH key reduces to zero depends on insertion order; a dropped key's
equation is not enforced, so two orders can enforce different equation subsets and produce
different Z (they differ only if the dropped equations are inconsistent with the enforced
span — precisely the case homogeneous ribbon tolerates). Therefore bit-identity is guaranteed
only up to the first dependent row. At ribbon's operating point the expected number of
dependent rows among n keys in m ≈ 1.09n slots is small but nonzero; our 45/45 bit-identical
runs at n up to 4×10^8 indicate dependencies were either absent or resolved identically
across our specific orders — the paper states the proposition for the independent case and
reports the empirical result separately. Engineering corollary: the per-run fingerprint
comparison against an arrival-order build detects any dependent-drop divergence when it
occurs, and the zero-false-negative gate over the full key set independently verifies filter
semantics; a reordered build is therefore never accepted on faith.

## Consequences used in the paper

- Reordering (full sort, partition, window-parallel with deferral) is output-neutral whenever
  the independence condition holds — verified per run by fingerprint, at no extra cost.
- Parallel construction correctness reduces to a checksum comparison instead of a concurrency
  argument.

## General statement adopted in the paper (2026-10-06)

Status: argument drafted 2026-10-06, checked by simulation (below), adopted in the paper's
Proposition 1 at the author's request. It has not had an external reader. The independent-rows
proposition and proof above are the special case and are kept for the record; the "dependent
case" section above is superseded where it says dependent rows can change Z for homogeneous
ribbon. They cannot, because a homogeneous system is consistent.

**Proposition.** Let E = {(r_k, b_k)} be a CONSISTENT system over GF(2), each r_k with a leading
1 at its start position. Banding (drop a row that reduces to zero) followed by
back-substitution with free slot j set to g(j) yields the same Z under every insertion order.

**Proof.**

1. *Pivot set.* In any order, a stored row at slot i has leading position i, so stored rows are
   independent, and a stored row is never modified afterwards. A stored row equals its original
   row plus rows stored before it, so every original row that was stored lies in the final span;
   a row is dropped only when it reduces to zero against stored rows, i.e. when it is already in
   their span. So after all insertions the stored rows span V = span{r_k} and form a basis of
   it. Every occupied slot is the leading position of a vector of V, so the occupied set is a
   subset of P(V); it has dim V elements and |P(V)| = dim V, so it equals P(V). (Credited: the ribbon papers state this invariance — JACM 73(1) Art. 7, §3, "On (M1)".)
2. *Solution set.* Each stored (row, result) pair is a GF(2) sum of equations of E, so every
   solution of E solves the stored system. Conversely take a dropped equation (r, b): r is a
   combination of stored rows. Because E is consistent, pick any solution Z0 of E; it solves the
   stored equations and (r, b), so b equals the same combination of the stored results.
   Hence (r, b) is implied by the stored system. The stored system and E have the same solution
   set S, in every order.
3. *Uniqueness.* The free set F = [m] \ P(V) is order-independent. Adding Z_j = g(j) for j in F
   to the stored system gives m independent equations (the stored rows are in echelon form on
   P(V)), so exactly one element of S is selected, and it is what back-substitution computes. ∎

**Corollaries.**

- *Homogeneous ribbon* (all b_k = 0) is always consistent: the filter is order-independent with
  no condition on the keys. This is why every reordered build matched its arrival-order
  fingerprint. Identity across architectures needs one more fact that is not part of this
  proposition: hashing and GF(2) arithmetic are deterministic, with the same m, seed and g.
- *Standard ribbon:* if E is inconsistent, every order fails. Directly (not via step 2, which
  assumed consistency): a dropped equation satisfies (r, b) = (sum of stored pairs) + (0, b'),
  where b' is its reduced result. If some order had b' = 0 for every dropped equation, each
  would be implied by the stored system, which is independent and therefore solvable, so E
  would be consistent. So success is
  order-independent, and on success the output is too. E5 measured this: 443 of 443 RocksDB
  Standard128 filters byte-identical between stock and pleated builds.
- *What does depend on order:* which redundant keys are dropped. JACM notes that the set of
  successfully inserted keys is not order-invariant; that is compatible with the above.

## Earlier note: the homogeneous case (2026-10-06; superseded by the general statement above)

Step 1 is credited: the ribbon papers already state that the filled-slot set is invariant under
insertion order (JACM §3, "On (M1): The order of keys is irrelevant").

For homogeneous ribbon every right-hand side is zero (the kernel asserts `rr == 0` in
`StoreRow`). That appears to remove the independence hypothesis altogether:

- Whatever the order, the stored rows have distinct leading positions, each in P(V), and they
  span V = span{r_k} (a row is dropped only when it reduces to zero against stored rows, i.e.
  it already lies in their span). So the occupied set is P(V) with or without dependent rows.
- A dropped row's equation is r·Z = 0 with r in the span of the stored rows, so it is implied
  by them. The enforced solution set is therefore V^⊥ (per result column) in every order.
- Pinning Z_j = g(j) on the order-independent free set picks one element of that set.

If this is right, the solved homogeneous filter is identical under every insertion order with
no condition on the rows, which would explain the 54/54 matching fingerprints and the
cross-architecture identity directly, and the paper's "dependent rows may be dropped
differently" caveat would apply only to non-homogeneous (standard) ribbon. This needs the
author's check, and ideally the ribbon authors' confirmation, before the paper claims it.

### Computational check (2026-10-06)

`scripts/check_order_independence.py` is an independent small-scale model of banding and
back-substitution over GF(2) with the kernel's free-slot rule g(i) = i · 0x9E3779B185EBCA87. It
does not use the benchmarked kernel. One run (fixed seeds) gave:

| case | instances | orders tried per instance | identical in every order |
|---|---|---|---|
| A. homogeneous, dependent rows present | 200 | all permutations (m=10, w=4, 5–7 keys) | 200 |
| A. homogeneous, dependent rows present | 400 | 40 random (m up to 200, w up to 32) | 400 |
| B. non-homogeneous, rows independent (Proposition 1) | 200 + 400 | as above | 200 + 400 |
| C. non-homogeneous, dependent rows present, arbitrary results (control) | 200 + 400 | as above | see `results/order_independence_check.txt` |

Case C is the negative control (arbitrary right-hand sides, so most such systems are
inconsistent); most instances differ between orders, which shows the check can detect order
dependence. The counts in this table were first typed by hand from one run and the control
count later changed when the script gained case D; the artifact file is the authority. Case A never differed, including under every permutation of the tiny instances, in
instances chosen because they do drop dependent rows. This supports the strengthening; it is a
test over small random instances, not a proof. The three-line argument above is the proof
candidate and still wants a second reader.

Extended the same day with case D, the general statement: non-homogeneous systems that contain
redundant rows but are consistent (results generated from a hidden solution). 200 of 200 tiny
instances under all permutations and 400 of 400 larger ones under 40 random orders were
identical in every order. Full output: `results/order_independence_check.txt`.

## Double check (2026-10-06)

Three further checks, none of which found a problem with the mathematics.

1. **Independent referee read** (a separate automated review pass instructed to break the claim).
   Verdict: all three steps valid. It identified two facts step 1 left unstated (now added), a
   circular-looking justification of the inconsistent-system corollary (now replaced), and the
   observation that the hypothesis is tight: for an inconsistent system under "drop and
   continue", Z is always order-dependent. It also flagged wording in the paper that claimed
   more than the proposition gives; those sentences were corrected.
2. **Exhaustive enumeration**, written by the referee from the abstract setting without
   reference to `scripts/check_order_independence.py`: `scripts/enumerate_order_independence.c`,
   outputs in `results/order_independence_enumeration/`, totals in its `ANALYSIS.md`. Every
   multiset of up to five equations (six in two runs) for m ≤ 7, window ≤ 3, 1- and 2-bit
   results, every insertion order, three free-slot rules; no violation of the proposition or
   of the corollaries.
3. **The real kernel**: `src/ribbon_reorder/order_check.cc` against the unmodified pinned
   fastfilter_cpp kernel, output in `results/order_independence_kernel_check.txt`. Homogeneous
   filters deliberately under-provisioned so that thousands of rows are dropped were identical
   under 25 shuffled orders at every load; standard builds either succeeded identically in
   every order or failed in every order. At the benchmark's own sizing the same test dropped no
   rows, so the paper's earlier fingerprint matches did not exercise the redundant-row case;
   this test does.

Conditions the result depends on, which an implementation must meet (from the referee):

- One fixed system: same keys, table size, hash seed and result width. A reorder must not
  change anything that feeds seed or size selection. RocksDB derives the starting seed and the
  filter length from the first collected hash; the E2 patch reorders after both are computed.
  An upstream version must keep that placement.
- Failure for a seed means only "a row reduced to zero with a nonzero result", and the seed
  sequence is fixed. Then the selected seed is order-independent.
- Free-slot values depend only on the slot index (zero for RocksDB's standard builder, a hash
  of the index for the homogeneous kernel).
- Reduction is exact and unbounded. Schemes that bump keys by position in the order, such as
  BuRR, are not covered.
- The parallel build counts as "some insertion order" only because each thread loads and stores
  slots in its own range and a spilled key writes nothing. The referee checked this by reading
  the driver and did not confirm that every key a thread processes starts at or above its
  lower boundary; that follows from the window partition but has not been separately tested.

Still not done: a machine-checked proof; a reading by the author or by the ribbon authors.
Known stale text elsewhere: the comment inside `experiments/e2_rocksdb/pleat-rocksdb.patch`
still describes the older, weaker result. The patch is a recorded experiment artifact and was
left unchanged; fix the comment in any upstream version.

