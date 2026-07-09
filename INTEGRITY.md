# Integrity Protocol — fabrication/hallucination checks

Every claim that could appear in the paper passes through this pipeline. This file defines the
checks; `CLAIMS.md` is the ledger. The protocol is a response to documented AI-generated
fabrications in this project's predecessor (see `~/Code/hes/claude_code_off_the_rails.md` and the
July 2026 audit of barudb's final report: an impossible 7.8-bits/key-at-1%-FPR table, crossed
benchmark labels, and scalar code presented as SIMD).

## The claims ledger (CLAIMS.md)

Every quantitative or comparative claim gets a row:

| id | claim | raw artifact(s) | producing command | machine | date | status |

Status is one of: `measured` (raw artifact committed), `derived` (script over measured artifacts,
script committed), `literature` (exact citation + page/table), `hypothesis` (explicitly unproven).
Nothing else exists. A claim with no row does not go in any document.

## Automated checks (`scripts/check_integrity.py`)

Run by `reproduce.sh` and before any results write-up:

1. **Provenance check** — every number in `results/**/ANALYSIS.md` files must be regenerable by
   the analysis scripts from raw artifacts; ANALYSIS files carry a generated-by header with the
   producing command and input hashes. Hand-edited ANALYSIS files fail the check.
2. **Theory-bound check** — measured (bits/key, FPR) pairs are validated against
   log2(1/ε) (any filter) and 1.44·log2(1/ε) (Bloom-family). Violations flag as measurement bugs.
3. **Baseline-fairness check** — benchmark configs for baselines are diffed against the upstream
   harness defaults; any deviation (smaller size, fewer hashes, debug build) must be declared in
   the experiment README.
4. **SIMD-honesty check** — any claim of vectorization must reference a committed disassembly
   artifact (`results/**/asm/*.s`) showing packed instructions on the hot path.

## Human/model checklist (before each results write-up)

- [ ] Did every number come from a file in `results/`? (No memory, no "approximately", no filling gaps.)
- [ ] Are baselines at their strongest documented configuration?
- [ ] Is anything labeled as ours that is a port? Is anything labeled SIMD that is scalar?
- [ ] Does the write-up report the pre-registered decision rule's outcome, including nulls?
- [ ] Were any goalposts moved after seeing data? If a protocol changed, is the change and its
      reason logged in RESEARCH_LOG.md *before* the rerun?
- [ ] Do FPR/space numbers respect information-theoretic bounds?
- [ ] Are run-to-run variance and machine specs reported?

## Adversarial review

Before any external write-up, an independent review pass (fresh agent context, no access to the
narrative, only code + raw artifacts) attempts to refute each ledger claim. Findings are logged in
RESEARCH_LOG.md whether or not they kill the claim.
