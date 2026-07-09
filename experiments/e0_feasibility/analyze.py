#!/usr/bin/env python3
"""Derive results/e0a/ANALYSIS.md from committed raw artifacts ONLY (criterion JSON + summary.json
+ asm artifacts). Never runs a benchmark. Evaluates the pre-registered decision rules from
README.md mechanically.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "e0a"

SIZE_ORDER = ["32KiB_l1", "256KiB_l2", "4MiB_l3", "64MiB_ram", "512MiB_ram"]
STRATS = ["scalar", "prefetch", "lanes", "lanes_hot_CONTROL", "fastbloom_perkey"]
BATCH = 8192


def load_estimates():
    """criterion layout: criterion/probe_miss_<size>/<strategy>/new/estimates.json"""
    out = {}
    base = RES / "criterion"
    if not base.exists():
        sys.exit("missing results/e0a/criterion — run --stage bench first")
    for d in base.iterdir():
        if not d.name.startswith("probe_miss"):
            continue
        size = d.name.split("_", 2)[2]
        for strat_dir in d.iterdir():
            est = strat_dir / "new" / "estimates.json"
            if est.exists():
                j = json.loads(est.read_text())
                ns = j["mean"]["point_estimate"]
                lo = j["mean"]["confidence_interval"]["lower_bound"]
                hi = j["mean"]["confidence_interval"]["upper_bound"]
                out[(size, strat_dir.name)] = (ns, lo, hi)
    return out


def main():
    est = load_estimates()
    summary = json.loads((RES / "summary.json").read_text())
    machine = json.loads((RES / "bench_machine.json").read_text())

    lines = [
        f"generated-by: experiments/e0_feasibility/analyze.py over results/e0a/ artifacts "
        f"(bench machine: {machine['cpu']}, {machine['rustc']}, RUSTFLAGS={machine['rustflags']})",
        "",
        "# E0 analysis (derived — do not hand-edit)",
        "",
        "## FPR gate (raw: summary.json)",
        "",
        "| filter | bits/key | measured FPR |",
        "|---|---|---|",
    ]
    for f in summary["filters"]:
        lines.append(f"| {f['name']} | {f['bits_per_key']:.2f} | {f['measured_fpr']*100:.4f}% |")
    fpr_ok = all(0.005 <= f["measured_fpr"] <= 0.02 for f in summary["filters"] if f["name"] == "lanefilter_sbbf")
    lines.append("")
    lines.append(f"FPR gate (pre-registered [0.5%, 2%]): {'PASS' if fpr_ok else 'FAIL — timings below are not interpretable'}")

    lines += ["", "## Batch-miss probe throughput (raw: criterion/, mean over 30 samples, batch = 8192 keys)", ""]
    header = "| size | " + " | ".join(STRATS) + " |"
    lines += [header, "|" + "---|" * (len(STRATS) + 1)]
    mops = {}
    for size in SIZE_ORDER:
        row = [size]
        for s in STRATS:
            if (size, s) in est:
                ns = est[(size, s)][0]
                m = BATCH / ns * 1e3  # Mops/s
                mops[(size, s)] = m
                row.append(f"{m:,.0f} Mops/s ({ns/BATCH:.2f} ns/key)")
            else:
                row.append("—")
        lines.append("| " + " | ".join(row) + " |")

    lines += ["", "## Pre-registered decision rules", ""]

    def ratio(size, a, b):
        if (size, a) in mops and (size, b) in mops and mops[(size, b)] > 0:
            return mops[(size, a)] / mops[(size, b)]
        return None

    realistic = [s for s in ("4MiB_l3", "64MiB_ram", "512MiB_ram") if (s, "lanes") in mops]
    r1_hits = [s for s in realistic if (r := ratio(s, "lanes", "prefetch")) and r >= 1.3]
    r2_hits = [s for s in realistic if (r := ratio(s, "lanes_hot_CONTROL", "lanes")) and r >= 3.0]
    r3_all = realistic and all(
        (r := ratio(s, "lanes_hot_CONTROL", "lanes")) and r <= 1.15
        and (rp := ratio(s, "lanes", "prefetch")) and 1 / 1.15 <= rp <= 1.15
        for s in realistic
    )
    for s in realistic:
        lines.append(
            f"- {s}: lanes/prefetch = {ratio(s, 'lanes', 'prefetch'):.2f}×, "
            f"hot-control/lanes = {ratio(s, 'lanes_hot_CONTROL', 'lanes'):.2f}×"
        )
    lines.append("")
    if r1_hits:
        lines.append(f"**Rule 1 met** at {r1_hits}: lanes ≥1.3× over prefetch → proceed to E1 layout design.")
    if r2_hits and not r1_hits:
        lines.append(f"**Rule 2 met** at {r2_hits}: ≥3× compute headroom but lanes not winning → redesign probe before layout work.")
    if r3_all:
        lines.append("**Rule 3 (KILL) met**: memory-latency-bound at all realistic sizes; point-probe layout direction dies. Write up negative result; pivot to construction/sorted-probe workloads.")
    if not (r1_hits or r2_hits or r3_all):
        lines.append("**No pre-registered rule fired cleanly** — intermediate regime; log interpretation in RESEARCH_LOG.md before any next step.")

    asm = RES / "asm" / "packed_instructions.txt"
    if asm.exists():
        n_packed = len([l for l in asm.read_text().splitlines() if l.strip()])
        lines += ["", f"## Auto-vectorization (raw: asm/): {n_packed} packed-SIMD instruction lines in lanes kernel "
                      f"({'vectorized' if n_packed > 10 else 'NOT meaningfully vectorized'})"]

    out = RES / "ANALYSIS.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
