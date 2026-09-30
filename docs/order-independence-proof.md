# Order-independence of homogeneous ribbon banding: proposition and proof

Backs the paper's §5 claim (empirically: 54/54 runs bit-identical). Reviewed status: draft
argument, to be checked by an external reader before submission.

## Setting

Banding maintains an m-slot table. Each key contributes an equation r·Z = b over GF(2), where
r is a w-bit coefficient row with leading 1 at start position s(r) (kFirstCoeffAlwaysOne).
Insertion reduces r (and b) by XOR against stored rows at the current leading position until
either (i) the leading position i has an empty slot — store the reduced (row, b) there — or
(ii) r reduces to zero — the key is dropped (homogeneous ribbon accepts this; it is the source
of its FPR/space trade). Back-substitution then computes Z with every empty (free) slot's
value fixed to zero.

## Proposition

Let E = {(r_k, b_k)} be the multiset of equations, and suppose the rows {r_k} are linearly
independent over GF(2). Then the solution Z produced by banding followed by zero-free-slot
back-substitution is the same for every insertion order of E.

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
3. **The output is the unique canonical element of S.** Zero-free-slot back-substitution
   outputs the Z ∈ S with Z_j = 0 for all j ∈ F. The extended system E ∪ {Z_j = 0 : j ∈ F}
   has full rank |P(V)| + |F| = m, hence a unique solution. Both the constraint set and the
   pinned coordinate set are order-independent, so Z is. ∎

## The dependent case (why it can matter, and why it did not here)

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
