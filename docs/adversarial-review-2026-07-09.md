# Adversarial review pass (2026-07-09) — findings of record

Fresh-context reviewer; access to CLAIMS.md, code, raw artifacts only; instructed to refute.
Method: independent re-parsing of every cited artifact; code audit of benches, driver,
harness call paths; cross-harness consistency checks. Full report preserved in session log;
this file records the verdicts and corrections applied.

## Verdicts
- VERIFIED within rep noise: C4, C6, C7, C8, C9 (exact), C10, C11, C13 (exact), C14, C16
  (exact), C17, C18, C20, C21, C22, C23. Fingerprints identical 54/54; FN=0 everywhere;
  deferred fractions match G(T-1)/num_starts to 3 digits; two independent harnesses agree on
  every overlapping quantity; no number violates information-theoretic bounds.
- REFUTED (transcription): C5 — FPR 0.9395% (not 0.9579%, which came from an uncommitted
  smoke run); 10M lookups mean 4.35 ns / 22.2 cyc. Ledger corrected.

## Corrections applied
1. C17: best-full-sort advantage is 1.68x at BOTH sizes (1.73x was vs radix, not best sort).
2. C21: ~70 ns/key is the top recursion level; ~75.5 all levels.
3. C23: scaling ratios are vs the parallel path's own T=1 (~20% defer/copy overhead);
   vs best sequential banding: 3.54x at 8T, 6.28x at 16T (registered >=3x passes either
   way). Backsubst at T=16 is 3.82 ns/key; T=16 rests on 2 reps with ~9% spread.

## Instrument findings (no headline impact)
- results/e1b/parallel/*.json perf-counter fields are INVALID (perf fds opened pid=0,
  no inherit: worker threads unmeasured). Wall-clock fields are the citable ones. Do not
  mine the counter fields.
- Sequential bit-identity is mathematically guaranteed (see docs/order-independence-proof.md)
  so it is weak evidence sequentially — but it is exactly the load-bearing race detector for
  the parallel runs.
- "64MiB" E0 row is a mixed L3/DRAM regime (36MB L3); labels slightly overstate "RAM".
- results/e0a/anchor/ reused from run 1 (same machine; harmless; noted).
- Window-sweep/parallel artifact producing commands live in session history, not run.py;
  bootstrap_remote.sh covers T in {1,2,4,8} rep0 only.

## Paper impact
Section 5 scaling sentence and abstract precision updated (self-relative base disclosed);
no conclusion changed.
