#!/usr/bin/env python3
"""Sum the per-run outputs of scripts/enumerate_order_independence.c into
results/order_independence_enumeration/ANALYSIS.md. Runs overlap (larger k contains smaller k;
narrower windows sit inside wider ones), so totals are run totals, not distinct systems."""
import re
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "results" / "order_independence_enumeration"
KEYS = ["systems", "consistent", "inconsistent", "orders", "orders_on_consistent",
        "Z_differs", "occ_differs", "consistent_but_zero_row_nonzero_b",
        "inconsistent_order_without_failure", "Z_not_solution", "free_slot_not_g",
        "consistent_with_drops", "consistent_dropped_eq_multiset_differs"]
tot = dict.fromkeys(KEYS, 0)
runs = sorted(D.glob("m*_mode*.txt"))
maxrun = ("", 0)
for f in runs:
    t = f.read_text()
    for k in KEYS:
        v = int(re.search(rf"\b{k}=(\d+)", t).group(1))
        tot[k] += v
        if k == "systems" and v > maxrun[1]:
            maxrun = (f.name, v)
L = ["generated-by: scripts/summarize_order_enumeration.py over "
     "results/order_independence_enumeration/*.txt (outputs of scripts/enumerate_order_independence.c)",
     "", "# Exhaustive order-independence enumeration (derived — do not hand-edit)", "",
     f"Runs: {len(runs)}. Largest run: {maxrun[0]} ({maxrun[1]:,} systems).", "",
     "| quantity | total over runs |", "|---|---|"]
L += [f"| {k} | {tot[k]:,} |" for k in KEYS]
viol = ["Z_differs", "occ_differs", "consistent_but_zero_row_nonzero_b",
        "inconsistent_order_without_failure", "Z_not_solution", "free_slot_not_g"]
L += ["", "Violations of the proposition or its corollaries: "
      + ("NONE" if all(tot[k] == 0 for k in viol) else "PRESENT — see rows above") + ".",
      "Scope: every multiset of up to 5 equations (6 in two runs) for m ≤ 7, window ≤ 3, 1- and "
      "2-bit results, every insertion order, three free-slot rules; plus arbitrary nonzero rows "
      "for m ≤ 5. Small parameters only; not a proof."]
(D / "ANALYSIS.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
