#!/usr/bin/env python3
"""Derive results/e1a/ANALYSIS.md from committed raw artifacts only. Mechanically evaluates
the frozen decision rules (R1-R3 / H1-H2 thresholds) from README.md.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "e1a"

SIZE_ORDER = ["1M", "10M", "53.7M_64MBfilter", "100M", "429M_512MBfilter"]
SIZE_N = {"1M": 1e6, "10M": 1e7, "53.7M_64MBfilter": 5.37e7, "100M": 1e8, "429M_512MBfilter": 4.29e8}
STRATS = ["perkey", "perkey_prefetch", "partitioned", "partitioned_grouped", "partitioned_grouped_nt"]
BIG = ["53.7M_64MBfilter", "100M", "429M_512MBfilter"]  # the ≥64MB-filter regime


def load(base: Path):
    out = {}
    for d in base.iterdir() if base.exists() else []:
        if not d.name.startswith("construct"):
            continue
        size = d.name.split("_", 1)[1]
        for sd in d.iterdir():
            est = sd / "new" / "estimates.json"
            if est.exists():
                out[(size, sd.name)] = json.loads(est.read_text())["mean"]["point_estimate"]
    return out


def main():
    est = load(RES / "criterion")
    if not est:
        sys.exit("missing results/e1a/criterion — run --stage bench first")
    machine = json.loads((RES / "bench_machine.json").read_text())

    lines = [
        f"generated-by: experiments/e1a_construction/analyze.py over results/e1a/ artifacts "
        f"(machine: {machine['cpu']}, {machine['arch']}, {machine['rustc']})",
        "",
        "# E1a analysis (derived — do not hand-edit)",
        "",
        "## Construction throughput (mean ns/key; raw: criterion/)",
        "",
        "| size | " + " | ".join(STRATS) + " |",
        "|" + "---|" * (len(STRATS) + 1),
    ]
    nskey = {}
    for size in SIZE_ORDER:
        row = [size]
        for s in STRATS:
            if (size, s) in est:
                v = est[(size, s)] / SIZE_N[size]
                nskey[(size, s)] = v
                row.append(f"{v:.2f}")
            else:
                row.append("—")
        lines.append("| " + " | ".join(row) + " |")

    def ratio(size, num, den):
        if (size, num) in nskey and (size, den) in nskey and nskey[(size, num)] > 0:
            return nskey[(size, den)] / nskey[(size, num)]  # speedup of num over den
        return None

    lines += ["", "## Frozen decision rules", ""]
    h1 = [s for s in BIG if (r := ratio(s, "partitioned", "perkey")) and r >= 2.0]
    h2 = [s for s in BIG if (r := ratio(s, "partitioned_grouped", "partitioned")) and r >= 1.2]
    h2nt = [s for s in BIG if (r := ratio(s, "partitioned_grouped_nt", "partitioned")) and r >= 1.2]
    k1 = all((r := ratio(s, "partitioned", "perkey")) and r <= 1.0 for s in BIG if (s, "partitioned") in nskey)

    for s in BIG:
        if (s, "partitioned") not in nskey:
            continue
        parts = [f"partitioned/perkey = {ratio(s, 'partitioned', 'perkey'):.2f}x"]
        if (s, "partitioned_grouped") in nskey:
            parts.append(f"grouped/partitioned = {ratio(s, 'partitioned_grouped', 'partitioned'):.2f}x")
        if (s, "partitioned_grouped_nt") in nskey:
            parts.append(f"grouped_nt/partitioned = {ratio(s, 'partitioned_grouped_nt', 'partitioned'):.2f}x")
        lines.append(f"- {s}: " + ", ".join(parts))
    lines.append("")
    lines.append(f"H1 (replication, partitioned ≥2× perkey at ≥64MB): {'CONFIRMED at ' + str(h1) if h1 else 'NOT met'}")
    lines.append(f"H2 (novelty, grouped ≥1.2× over partitioned at ≥64MB): {'CONFIRMED at ' + str(h2) if h2 else 'NOT met'}")
    lines.append(f"H2-NT (grouped_nt ≥1.2× over partitioned at ≥64MB): {'CONFIRMED at ' + str(h2nt) if h2nt else 'NOT met'}")
    if k1:
        lines.append("K1 (kill: per-key ≥ partitioned everywhere at ≥64MB): FIRED — construction direction dies; pivot per protocol.")
    if not h2 and not h2nt and not k1:
        lines.append("K2 status: H2 unmet as implemented — full K2 unless an amendment (logged before rerun) improves the apply; see README kill criteria.")

    out = RES / "ANALYSIS.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
