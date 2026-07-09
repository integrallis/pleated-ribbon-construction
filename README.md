# Transposed Filters: Can FastLanes-Style Layouts Accelerate Approximate Membership Queries?

Working repository for a systems paper investigating whether the FastLanes unified transposed
layout (Afroozeh & Boncz, VLDB 2023) — which lets plain scalar code auto-vectorize across SIMD
generations and ISAs — can be applied to the bit/fingerprint arrays of membership filters
(Bloom-family and successors), where all published SIMD designs instead use cache-line blocking
(split-block Bloom, register-blocked Bloom, vector quotient filter).

**Status: hypothesis-hunting.** No claims yet. A July 2026 literature sweep (~40 papers,
2014–2026) found zero published work connecting FastLanes-style transposition to any AMQ filter;
the survey and gap analysis live in `docs/`.

## Research questions (v0, subject to pre-registration before any registered run)

- **RQ1 (feasibility):** Does a transposed batch-probe loop written as plain Rust/C++ actually
  auto-vectorize, and is the batch-probe hot path compute-bound enough for layout to matter?
- **RQ2 (throughput):** At matched bits/key and *measured* FPR, does a transposed-layout filter
  beat split-block/register-blocked Bloom and `fastbloom` on batch-probe throughput, on AVX2,
  AVX-512, and ARM?
- **RQ3 (portability):** Does the same scalar source hit those wins across ISAs without
  intrinsics — the FastLanes portability thesis, restated for filters?
- **Kill criterion:** if probes at realistic filter sizes (≥ L2-resident) are memory-bound to the
  point that layout is irrelevant (E0b), the direction dies and the negative result is written up.

## Layout

```
paper/                    LaTeX (skeleton until there are results worth writing)
src/lanefilter/           Rust crate: the prototype filter(s) under study
experiments/
  e0_feasibility/         E0a auto-vectorization check + E0b memory/compute-bound characterization
harness/                  established third-party benchmark frameworks (see harness/README.md):
                          fastfilter_cpp (xor/binary-fuse/BuRR/prefix-filter papers' suite),
                          FastLanes reference implementation
results/                  raw artifacts (criterion JSON, harness CSV, perf logs, disassembly) —
                          every reported number derives from files here
scripts/                  analysis + figure generation + integrity checks
CLAIMS.md                 the claims ledger (see INTEGRITY.md)
RESEARCH_LOG.md           dated log of hypotheses, decisions, and dead ends
INTEGRITY.md              fabrication/hallucination-check protocol
```

## Reproduce

```bash
./reproduce.sh   # unit tests + re-derive all analyses from committed raw artifacts + integrity checks
```

## Provenance

Grew out of Bloom-filter work in the barudb LSM-tree project (Harvard CS265). That codebase's
filter benchmarks were audited in July 2026; only claims backed by raw criterion output are
carried forward, and none of its report's headline filter claims survived the audit (see
INTEGRITY.md). This repo starts from zero claims.
