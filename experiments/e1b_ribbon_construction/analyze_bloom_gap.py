#!/usr/bin/env python3
"""Derive the matched Bloom-vs-ribbon construction table from committed raw artifacts only.

No new measurement: this joins three existing artifact sets at n = 100M keys, single thread,
all on the same machine:
  - results/e1b/phase0/BlockedBloom_*, Bloom12_addAll_*  (fastfilter_cpp, same harness and run
    as the ribbon Phase-0 characterization)
  - results/e1a/criterion/construct_100M/{perkey,perkey_prefetch,partitioned}  (our Rust
    SBBF prototype under Criterion; 10 bits/key by protocol)
  - results/e1b/phase1/{reference,partitioned}_100000000_rep*.json  (homogeneous ribbon,
    reference kernel, arrival order vs pleated)
  - results/e0a/summary.json  (the prototype's measured FPR and bits/key, at 1M keys)
  - results/e0a/anchor/blockedbloom_100000000.txt  (the single earlier BlockedBloom run behind
    CLAIMS C9, checked here against the 3-rep Phase-0 range)

Outputs results/e1b/BLOOM_GAP_ANALYSIS.md and paper/tables/bloom_gap.tex (table rows plus
\\newcommand macros for the ratios quoted in prose). Space and false-positive rate are NOT
matched across rows; both are reported where the raw artifact records them.
"""
import json
import statistics
import sys
from pathlib import Path

from analyze import parse  # fastfilter_cpp bench-output parser used for Phase 0

ROOT = Path(__file__).resolve().parents[2]
P0 = ROOT / "results" / "e1b" / "phase0"
P1 = ROOT / "results" / "e1b" / "phase1"
E1A = ROOT / "results" / "e1a" / "criterion" / "construct_100M"
OUT_MD = ROOT / "results" / "e1b" / "BLOOM_GAP_ANALYSIS.md"
OUT_TEX = ROOT / "paper" / "tables" / "bloom_gap.tex"

N = 100_000_000


def fastfilter(algo):
    reps = [parse(f) for f in sorted(P0.glob(f"{algo}_{N}_rep*.txt"))]
    reps = [r for r in reps if r[0] is not None]
    if not reps:
        sys.exit(f"missing results/e1b/phase0/{algo}_{N}_rep*.txt")
    ns = [r[0] for r in reps]
    return {
        "ns": statistics.mean(ns),
        "sd": statistics.stdev(ns) if len(ns) > 1 else 0.0,
        "lo": min(ns), "hi": max(ns),
        "fpr": statistics.mean(r[2] for r in reps),
        "bits": statistics.mean(r[3] for r in reps),
        "reps": len(reps), "note": "",
    }


def prototype_quality():
    """FPR and bits/key of our SBBF prototype as measured in E0 (1M keys, same geometry)."""
    data = json.loads((ROOT / "results" / "e0a" / "summary.json").read_text())
    f = next(x for x in data["filters"] if x["name"] == "lanefilter_sbbf")
    return f["measured_fpr"] * 100, f["bits_per_key"], data["n_keys"]


def criterion(strategy):
    est = E1A / strategy / "new" / "estimates.json"
    if not est.exists():
        sys.exit(f"missing {est.relative_to(ROOT)}")
    e = json.loads(est.read_text())
    fpr, bits, _ = prototype_quality()
    return {"ns": e["mean"]["point_estimate"] / N, "sd": e["std_dev"]["point_estimate"] / N,
            "fpr": fpr, "bits": bits, "reps": None, "note": "$^\\dagger$"}


def ribbon(strategy):
    reps = [json.loads(f.read_text()) for f in sorted(P1.glob(f"{strategy}_{N}_rep*.json"))]
    if not reps:
        sys.exit(f"missing results/e1b/phase1/{strategy}_{N}_rep*.json")
    ns = [r["total_ns_per_key"] for r in reps]
    return {
        "ns": statistics.mean(ns),
        "sd": statistics.stdev(ns) if len(ns) > 1 else 0.0,
        "fpr": statistics.mean(r["fpr"] for r in reps) * 100,
        "bits": statistics.mean(r["bits_per_key"] for r in reps),
        "reps": len(reps), "note": "",
    }


def main():
    # (key, label, harness, data, in_paper_table)
    rows = [
        ("bb", "blocked Bloom, per-key", "fastfilter\\_cpp", fastfilter("BlockedBloom"), True),
        ("b12", "Bloom (12 bits/key), addAll", "fastfilter\\_cpp", fastfilter("Bloom12_addAll"), False),
        ("pk", "blocked Bloom, per-key", "ours (Criterion)", criterion("perkey"), False),
        ("pf", "blocked Bloom, prefetch-pipelined", "ours (Criterion)", criterion("perkey_prefetch"), False),
        ("pt", "blocked Bloom, partitioned", "ours (Criterion)", criterion("partitioned"), False),
        ("ref", "homogeneous ribbon, reference", "fastfilter\\_cpp kernel", ribbon("reference"), True),
        ("pl", "homogeneous ribbon, pleated", "fastfilter\\_cpp kernel", ribbon("partitioned"), True),
    ]
    by = {k: d for k, _, _, d, _ in rows}
    bloom_keys = ["bb", "b12", "pk", "pf", "pt"]
    fastest_key = min(bloom_keys, key=lambda k: by[k]["ns"])
    fastest = by[fastest_key]["ns"]
    anchor = by["bb"]["ns"]
    c9_ns = parse(ROOT / "results" / "e0a" / "anchor" / f"blockedbloom_{N}.txt")[0]
    c9_in_range = by["bb"]["lo"] <= c9_ns <= by["bb"]["hi"]
    space_saving = (1 - by["pl"]["bits"] / by["bb"]["bits"]) * 100
    _, _, proto_n = prototype_quality()

    def cell(v, fmt):
        return "---" if v is None else format(v, fmt)

    machine = json.loads((P1 / "machine.json").read_text())
    md = [
        "generated-by: experiments/e1b_ribbon_construction/analyze_bloom_gap.py over "
        "results/e1b/phase0/, results/e1b/phase1/, results/e1a/criterion/construct_100M/ "
        f"(machine: {machine['cpu']}, {machine['arch']})",
        "",
        "# Bloom-vs-ribbon construction gap at 100M keys (derived — do not hand-edit)",
        "",
        "Single thread, same machine. Rows come from three existing artifact sets and two",
        "harnesses; space and false-positive rate are not matched across rows.",
        "",
        "| build | harness | ns/key (mean ± sd) | FPR% | bits/key | x fastfilter BlockedBloom | x fastest Bloom build |",
        "|---|---|---|---|---|---|---|",
    ]
    for k, label, harness, d, _ in rows:
        md.append(
            f"| {label} | {harness.replace(chr(92), '')} | {d['ns']:.2f} ± {d['sd']:.2f} | {cell(d['fpr'], '.4f')}{'*' if d['note'] else ''} "
            f"| {cell(d['bits'], '.2f')} | {d['ns'] / anchor:.2f} | {d['ns'] / fastest:.2f} |"
        )
    md += [
        "",
        f"\\* FPR and bits/key of the prototype rows are the E0 measurement at {proto_n:,} keys "
        "(results/e0a/summary.json, same SBBF geometry); not re-measured at 100M.",
        "",
        f"Fastest measured Bloom build: `{fastest_key}` at {fastest:.2f} ns/key.",
        "",
        "## Same-harness pair (the comparison to lead with)",
        "",
        f"- fastfilter_cpp BlockedBloom vs homogeneous ribbon, same harness, same machine: FPR "
        f"{by['bb']['fpr']:.2f}% vs {by['pl']['fpr']:.2f}%; ribbon uses {space_saving:.1f}% fewer bits/key "
        f"({by['pl']['bits']:.2f} vs {by['bb']['bits']:.2f}).",
        f"- Earlier single BlockedBloom run behind CLAIMS C9: {c9_ns:.2f} ns/key; Phase-0 3-rep range "
        f"{by['bb']['lo']:.2f}-{by['bb']['hi']:.2f} -> {'inside' if c9_in_range else 'OUTSIDE'} the range.",
        "",
        "## Gap before and after pleating",
        "",
        f"- vs fastfilter BlockedBloom (per-key): reference ribbon {by['ref']['ns'] / anchor:.2f}x, "
        f"pleated ribbon {by['pl']['ns'] / anchor:.2f}x",
        f"- vs fastest measured Bloom build: reference ribbon {by['ref']['ns'] / fastest:.2f}x, "
        f"pleated ribbon {by['pl']['ns'] / fastest:.2f}x",
        "",
        "## Scope and caveats",
        "",
        "- Ribbon rows are reorder + banding + back-substitution from the Phase-1 driver; Bloom",
        "  fastfilter rows are the harness's add phase; Criterion rows are whole-build time / n.",
        "- Criterion rows: our Rust SBBF prototype in a different harness and language. Its FPR is",
        "  higher than both fastfilter BlockedBloom and the ribbon, so the fastest-Bloom ratio compares",
        "  against a weaker filter. A production Bloom build with construction prefetch at matched",
        "  FPR is measured separately in E3 (results/e3/ANALYSIS.md, CLAIMS C26), on another machine.",
        "  Only the same-harness rows go into the paper table.",
        "- Parallel Bloom builds are measured separately in E4 (results/e4/ANALYSIS.md, CLAIMS C27),",
        "  on another machine. The 16-thread ribbon total (CLAIMS C23) is not in this table.",
        "- Not an equal-space or equal-FPR comparison.",
    ]
    OUT_MD.write_text("\n".join(md) + "\n")

    tex = [
        "% generated-by: experiments/e1b_ribbon_construction/analyze_bloom_gap.py — do not hand-edit",
        f"\\newcommand{{\\bloomgaprefanchor}}{{{by['ref']['ns'] / anchor:.1f}}}",
        f"\\newcommand{{\\bloomgapplanchor}}{{{by['pl']['ns'] / anchor:.1f}}}",
        f"\\newcommand{{\\bloomgapreffastest}}{{{by['ref']['ns'] / fastest:.1f}}}",
        f"\\newcommand{{\\bloomgapplfastest}}{{{by['pl']['ns'] / fastest:.1f}}}",
        f"\\newcommand{{\\bloomfastestns}}{{{fastest:.2f}}}",
        f"\\newcommand{{\\bloomgapspacesaving}}{{{space_saving:.0f}}}",
        f"\\newcommand{{\\bloomanchorfpr}}{{{by['bb']['fpr']:.2f}}}",
        f"\\newcommand{{\\ribbonfpr}}{{{by['pl']['fpr']:.2f}}}",
        f"\\newcommand{{\\bloomprotofpr}}{{{by['pf']['fpr']:.2f}}}",
        f"\\newcommand{{\\bloomproton}}{{{proto_n // 1_000_000}M}}",
        "\\newcommand{\\bloomgaptablerows}{%",
    ]
    for k, label, harness, d, in_table in rows:
        if not in_table:
            continue
        if k == "ref":
            tex.append("\\midrule")
        tex.append(
            f"{label} & {harness} & ${d['ns']:.2f}\\pm{d['sd']:.2f}$ & {cell(d['fpr'], '.2f')}{d['note']} "
            f"& {cell(d['bits'], '.2f')}{d['note']} "
            f"& {d['ns'] / anchor:.1f}$\\times$ \\\\"
        )
    tex.append("}")
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_TEX.write_text("\n".join(tex) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
