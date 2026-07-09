#!/usr/bin/env python3
"""Derive results/e1b/PHASE1_ANALYSIS.md from raw phase-1 driver JSON only; evaluate the
registered H-E1b-1 thresholds mechanically (see README.md Phase-1 registration):
  (i)  bit-identity: within each (n, rep), all strategies share soln_fnv;
  (ii) miss-recovery: (miss_ref - miss_part) / (miss_ref - miss_bestsort) >= 0.80 at >=100M;
  (iii) reorder cost: partitioned < both sort variants;
  (iv) total: partitioned < reference (prefetch baseline) and < best full-sort total.
Failure threshold from the amendment: partitioned total must be within 1.3x of best
full-sort total, else H-E1b-1 is refuted.
"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "e1b" / "phase1"
OUT = ROOT / "results" / "e1b" / "PHASE1_ANALYSIS.md"

STRATS = ["reference", "noprefetch", "sort_std", "sort_radix", "sort_ips2ra", "partitioned"]
SIZES = [10_000_000, 100_000_000, 400_000_000]
BIG = [100_000_000, 400_000_000]


def main():
    if not RES.exists():
        sys.exit("missing results/e1b/phase1 — run --stage phase1 first")
    machine = json.loads((RES / "machine.json").read_text())
    rows = {}
    for f in RES.glob("*_rep*.json"):
        d = json.loads(f.read_text())
        rows.setdefault((d["strategy"], d["n"]), []).append(d)

    def mean(strat, n, field):
        rs = rows.get((strat, n))
        return statistics.mean(r[field] for r in rs) if rs else None

    lines = [
        f"generated-by: experiments/e1b_ribbon_construction/analyze_phase1.py over "
        f"results/e1b/phase1/ (machine: {machine['cpu']}, {machine['arch']})",
        "",
        "# E1b Phase-1 analysis (derived — do not hand-edit)",
        "",
        "## Per-phase construction cost (ns/key, mean over reps)",
        "",
        "| n | strategy | reorder | banding | backsubst | TOTAL | banding miss/key | banding cyc/key |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for n in SIZES:
        for s in STRATS:
            if (s, n) not in rows:
                continue
            lines.append(
                f"| {n:,} | {s} | {mean(s,n,'reorder_ns_per_key'):.2f} "
                f"| {mean(s,n,'banding_ns_per_key'):.2f} | {mean(s,n,'backsubst_ns_per_key'):.2f} "
                f"| **{mean(s,n,'total_ns_per_key'):.2f}** | {mean(s,n,'banding_miss_per_key'):.3f} "
                f"| {mean(s,n,'banding_cycles_per_key'):.1f} |"
            )

    # Gate (i): bit-identity within (n, rep).
    fnv_ok, fn_total = True, 0
    for n in SIZES:
        for rep in range(3):
            fnvs = {d["soln_fnv"] for (s, nn), ds in rows.items() if nn == n
                    for d in ds if d["rep"] == rep}
            if len(fnvs) > 1:
                fnv_ok = False
    for ds in rows.values():
        fn_total += sum(d["false_negatives"] for d in ds)

    lines += ["", "## Registered H-E1b-1 evaluation", "",
              f"- Bit-identity across strategies (per n,rep): {'PASS' if fnv_ok else 'FAIL — STOP, timings uninterpretable'}",
              f"- Total false negatives across all runs: {fn_total}"]

    verdict_parts = []
    for n in BIG:
        if ("partitioned", n) not in rows:
            continue
        m_ref = mean("reference", n, "banding_miss_per_key")
        m_part = mean("partitioned", n, "banding_miss_per_key")
        m_sort = min(mean("sort_std", n, "banding_miss_per_key"),
                     mean("sort_radix", n, "banding_miss_per_key"),
                     mean("sort_ips2ra", n, "banding_miss_per_key"))
        recovery = (m_ref - m_part) / (m_ref - m_sort) if m_ref > m_sort else float("nan")
        ro_part = mean("partitioned", n, "reorder_ns_per_key")
        ro_sort = min(mean("sort_std", n, "reorder_ns_per_key"),
                      mean("sort_radix", n, "reorder_ns_per_key"),
                      mean("sort_ips2ra", n, "reorder_ns_per_key"))
        t_part = mean("partitioned", n, "total_ns_per_key")
        t_ref = mean("reference", n, "total_ns_per_key")
        t_sort = min(mean("sort_std", n, "total_ns_per_key"),
                     mean("sort_radix", n, "total_ns_per_key"),
                     mean("sort_ips2ra", n, "total_ns_per_key"))
        ok = (recovery >= 0.80 and ro_part < ro_sort and t_part < t_ref and t_part < t_sort)
        within13 = t_part <= 1.3 * t_sort
        verdict_parts.append((n, ok, within13))
        lines.append(
            f"- n={n:,}: miss-recovery {recovery:.1%} (need ≥80%); reorder {ro_part:.2f} vs "
            f"best-sort {ro_sort:.2f} ns/key; totals part {t_part:.2f} / ref {t_ref:.2f} / "
            f"best-sort {t_sort:.2f} → conditions {'ALL MET' if ok else 'not all met'}"
        )
    lines.append("")
    if verdict_parts and all(ok for _, ok, _ in verdict_parts):
        lines.append("**H-E1b-1 CONFIRMED at all ≥100M sizes.**")
    elif verdict_parts and not any(w13 for _, _, w13 in verdict_parts):
        lines.append("**H-E1b-1 REFUTED (outside the pre-registered 1.3× salvage band).**")
    else:
        lines.append("**Mixed outcome — apply the amendment's failure threshold per size; log interpretation before any next step.**")

    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
