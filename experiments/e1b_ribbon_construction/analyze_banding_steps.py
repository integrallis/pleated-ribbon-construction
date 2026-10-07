#!/usr/bin/env python3
"""Derive banding instructions per key by insertion order from the committed Phase-1 raw JSON.

Purpose: the ribbon authors motivate approximate sorting by a bound on the row operations spent
on redundant insertions. This reports whether insertion order changes the work done in banding
at all in our runs (instructions/key scoped to the banding call). No new measurement.
Writes results/e1b/BANDING_STEPS_ANALYSIS.md and paper/tables/banding_steps.tex.
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1 = ROOT / "results" / "e1b" / "phase1"
ORDERS = [("reference", "arrival order"), ("sort_ips2ra", "full sort (ips2ra)"),
          ("partitioned", "partitioned, 2^16-slot windows")]
SIZES = [100_000_000, 400_000_000]


def main():
    val = {}
    for strat, _ in ORDERS:
        for n in SIZES:
            v = [json.loads(f.read_text())["banding_instr_per_key"]
                 for f in sorted(P1.glob(f"{strat}_{n}_rep*.json"))]
            val[(strat, n)] = (statistics.mean(v), len(v))
    L = ["generated-by: experiments/e1b_ribbon_construction/analyze_banding_steps.py over "
         "results/e1b/phase1/ (field banding_instr_per_key)",
         "", "# Banding work by insertion order (derived — do not hand-edit)", "",
         "| insertion order | " + " | ".join(f"instr/key at {n:,} (reps)" for n in SIZES) + " |",
         "|---|" + "---|" * len(SIZES)]
    for strat, label in ORDERS:
        L.append(f"| {label} | " + " | ".join(
            f"{val[(strat, n)][0]:.2f} ({val[(strat, n)][1]})" for n in SIZES) + " |")
    spread = {n: max(val[(s, n)][0] for s, _ in ORDERS) / min(val[(s, n)][0] for s, _ in ORDERS) - 1
              for n in SIZES}
    L += ["", "Largest relative difference between orders: "
          + ", ".join(f"{spread[n]:.1%} at {n:,}" for n in SIZES)
          + ". Insertion order changes where banding touches memory, not how much work it does."]
    (ROOT / "results" / "e1b" / "BANDING_STEPS_ANALYSIS.md").write_text("\n".join(L) + "\n")
    n = SIZES[0]
    tex = ["% generated-by: experiments/e1b_ribbon_construction/analyze_banding_steps.py — do not hand-edit",
           f"\\newcommand{{\\bandinstrarrival}}{{{val[('reference', n)][0]:.1f}}}",
           f"\\newcommand{{\\bandinstrsorted}}{{{val[('sort_ips2ra', n)][0]:.1f}}}",
           f"\\newcommand{{\\bandinstrpleated}}{{{val[('partitioned', n)][0]:.1f}}}"]
    (ROOT / "paper" / "tables" / "banding_steps.tex").write_text("\n".join(tex) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
