#!/usr/bin/env python3
"""Paper tables for the results by key count and for the window-size sweep, from committed raw
JSON. No new measurement.

Reads results/e1b/phase1/ and results/e1b/window_sweep/; writes paper/tables/e1b_scale.tex.
The same means appear in results/e1b/PHASE1_ANALYSIS.md and PHASE1B_ANALYSIS.md.
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1 = ROOT / "results" / "e1b" / "phase1"
SWEEP = ROOT / "results" / "e1b" / "window_sweep"
SIZES = [10_000_000, 100_000_000, 400_000_000]
SORTS = ["sort_std", "sort_radix", "sort_ips2ra"]


def runs(directory, pattern):
    return [json.loads(f.read_text()) for f in sorted(directory.glob(pattern))]


def mean(rs, field):
    return statistics.mean(r[field] for r in rs)


def main():
    scale = []
    for n in SIZES:
        ref, part = runs(P1, f"reference_{n}_rep*.json"), runs(P1, f"partitioned_{n}_rep*.json")
        sort = min((runs(P1, f"{s}_{n}_rep*.json") for s in SORTS),
                   key=lambda rs: mean(rs, "total_ns_per_key"))
        assert len(ref) == len(part) == len(sort) == 3, n
        t_ref, t_sort, t_part = (mean(rs, "total_ns_per_key") for rs in (ref, sort, part))
        scale.append(
            f"{n // 1_000_000}M & {t_ref:.1f} & {t_sort:.1f} & {t_part:.1f} & "
            f"{t_ref / t_part:.2f}$\\times$ & {t_sort / t_part:.2f}$\\times$ & "
            f"{mean(ref, 'banding_miss_per_key'):.2f} & {mean(sort, 'banding_miss_per_key'):.3f} & "
            f"{mean(part, 'banding_miss_per_key'):.3f} \\\\")
    sweep = []
    for shift in range(13, 21):
        rs = runs(SWEEP, f"shift{shift}_rep*.json")
        assert len(rs) == 2 and all(r["window_shift"] == shift for r in rs), shift
        sweep.append(
            f"$2^{{{shift}}}$ & {mean(rs, 'reorder_ns_per_key'):.1f} & "
            f"{mean(rs, 'banding_ns_per_key'):.1f} & {mean(rs, 'total_ns_per_key'):.1f} & "
            f"{mean(rs, 'banding_miss_per_key'):.3f} \\\\")
    tex = ["% generated-by: experiments/e1b_ribbon_construction/analyze_paper_tables.py — do not hand-edit",
           "\\newcommand{\\eonebscalerows}{%", *scale, "}",
           "\\newcommand{\\eonebsweeprows}{%", *sweep, "}"]
    (ROOT / "paper" / "tables" / "e1b_scale.tex").write_text("\n".join(tex) + "\n")
    print("\n".join(tex))


if __name__ == "__main__":
    main()
