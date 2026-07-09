#!/usr/bin/env python3
"""Integrity checks per INTEGRITY.md.

Checks implemented so far (grow as the project grows):
  1. theory-bound check: any (bits_per_key, measured_fpr) pair recorded in results/**/summary.json
     must respect log2(1/fpr) (any filter) and, when family == "bloom", 1.44*log2(1/fpr).
  2. ledger check: CLAIMS.md rows with status `measured`/`derived` must reference artifact paths
     that exist.
  3. analysis-header check: results/**/ANALYSIS.md must start with a generated-by header.

Exit nonzero on any violation. Run by reproduce.sh.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
failures: list[str] = []


def check_theory_bounds() -> None:
    for summary in ROOT.glob("results/**/summary.json"):
        data = json.loads(summary.read_text())
        for entry in data if isinstance(data, list) else data.get("filters", []):
            fpr = entry.get("measured_fpr")
            bpk = entry.get("bits_per_key")
            if fpr is None or bpk is None or fpr <= 0:
                continue
            info_bound = math.log2(1 / fpr)
            if bpk < info_bound - 1e-9:
                failures.append(
                    f"{summary}: {entry.get('name')} claims {bpk} bits/key at FPR {fpr} — "
                    f"below the {info_bound:.2f}-bit information-theoretic bound. "
                    "Measurement bug or fabrication."
                )
            if entry.get("family") == "bloom" and bpk < 1.44 * info_bound - 1e-9:
                failures.append(
                    f"{summary}: {entry.get('name')} (bloom family) claims {bpk} bits/key at "
                    f"FPR {fpr} — below the Bloom bound of {1.44 * info_bound:.2f} bits/key."
                )


def check_claims_ledger() -> None:
    claims = (ROOT / "CLAIMS.md").read_text()
    for line in claims.splitlines():
        if not line.startswith("|") or line.startswith("| id") or set(line) <= {"|", "-", " "}:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 7:
            continue
        cid, _claim, artifacts, _cmd, _machine, _date, status = cols[:7]
        if status in ("measured", "derived"):
            for ref in re.split(r"[,;]\s*", artifacts):
                ref = ref.split()[0].strip() if ref.strip() else ""
                if ref and ref != "—" and not (ROOT / ref).exists():
                    failures.append(f"CLAIMS.md {cid}: artifact '{ref}' does not exist")


def check_analysis_headers() -> None:
    for analysis in ROOT.glob("results/**/ANALYSIS.md"):
        first = analysis.read_text().splitlines()[:3]
        if not any("generated-by:" in line for line in first):
            failures.append(f"{analysis}: missing 'generated-by:' header (hand-edited?)")


def main() -> int:
    check_theory_bounds()
    check_claims_ledger()
    check_analysis_headers()
    if failures:
        print("INTEGRITY CHECK FAILURES:")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    print("integrity checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
