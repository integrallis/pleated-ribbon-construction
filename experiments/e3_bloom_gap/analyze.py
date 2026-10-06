#!/usr/bin/env python3
"""Derive results/e3/ANALYSIS.md from results/e3/sweep_fb.csv only, and evaluate the registered
rules of README.md mechanically:

  FPR match   per size: |FP(ribbon) - FP(bloom)| / FP(bloom) <= 0.10, else that size is reported
              as not FPR-matched and excluded from the ratio claim.
  gate        per size: stock and pleated ribbon report the same FP rate (E2's correctness gate).
  H-E3-1      at every size >= 10M: pleated/bloom build-cost ratio > 1.5 (expected to hold).
  H-E3-2      at 100M: pleated/bloom <= 1.25 (expected to FAIL; gates "matches Bloom" wording).

Also writes paper/tables/e3_bloom_gap.tex.
"""
import csv
import json
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = Path(os.environ.get("E3_RES", ROOT / "results" / "e3"))
OUT_TEX = Path(os.environ.get("E3_TEX", ROOT / "paper" / "tables" / "e3_bloom_gap.tex"))

ARMS = ["bloom", "stock", "pleated"]
FPR_TOL = 0.10
H1_MIN_SIZE, H1_RATIO = 10_000_000, 1.5
H2_SIZE, H2_RATIO = 100_000_000, 1.25


def main():
    src = RES / "sweep_fb.csv"
    if not src.exists():
        sys.exit("missing results/e3/sweep_fb.csv — run --stage bench first")
    machine = json.loads((RES / "machine.json").read_text())
    data = {}
    for r in csv.DictReader(src.open()):
        data.setdefault((int(r["size"]), r["arm"]), []).append(
            {k: float(r[k]) for k in ("build_ns_per_key", "bits_per_key", "fp_rate_pct")})
    sizes = sorted({s for s, _ in data})
    if not sizes:
        sys.exit("results/e3/sweep_fb.csv has no rows")
    missing = [(s, a) for s in sizes for a in ARMS if (s, a) not in data]
    if missing:
        sys.exit(f"incomplete sweep, missing arms: {missing}")

    def mean(s, a, f):
        return statistics.mean(x[f] for x in data[(s, a)])

    def sd(s, a, f):
        v = [x[f] for x in data[(s, a)]]
        return statistics.stdev(v) if len(v) > 1 else 0.0

    lines = [
        "generated-by: experiments/e3_bloom_gap/analyze.py over results/e3/sweep_fb.csv "
        f"(machine: {machine['cpu']}, {machine['arch']}, virt: {machine['virt']}; "
        f"RocksDB {machine['rocksdb_commit'][:9]})",
        "",
        "# E3 Stage A analysis (derived — do not hand-edit)",
        "",
        "## Build cost, filter_bench \"Build avg ns/key\" (mean ± sample stdev over reps)",
        "",
        "| keys/filter | arm | reps | build ns/key | FP rate % | bits/key stored |",
        "|---|---|---|---|---|---|",
    ]
    for s in sizes:
        for a in ARMS:
            lines.append(
                f"| {s:,} | {a} | {len(data[(s, a)])} | {mean(s, a, 'build_ns_per_key'):.2f}"
                f"±{sd(s, a, 'build_ns_per_key'):.2f} | {mean(s, a, 'fp_rate_pct'):.4f} "
                f"| {mean(s, a, 'bits_per_key'):.2f} |")

    lines += ["", "## Ratios and registered rules", "",
              "| keys/filter | stock/Bloom | pleated/Bloom | stock/pleated | FPR-matched | ribbon bits vs Bloom | stock FP == pleated FP |",
              "|---|---|---|---|---|---|---|"]
    res = {}
    for s in sizes:
        b, st, pl = (mean(s, a, "build_ns_per_key") for a in ARMS)
        fb, fs, fp = (mean(s, a, "fp_rate_pct") for a in ARMS)
        matched = abs(fp - fb) / fb <= FPR_TOL and abs(fs - fb) / fb <= FPR_TOL
        gate = abs(fs - fp) < 1e-6
        space = mean(s, "pleated", "bits_per_key") / mean(s, "bloom", "bits_per_key")
        res[s] = {"stock": st / b, "pleated": pl / b, "matched": matched, "gate": gate}
        lines.append(f"| {s:,} | {st / b:.2f}x | {pl / b:.2f}x | {st / pl:.2f}x "
                     f"| {'yes' if matched else 'NO'} | {(space - 1) * 100:+.1f}% "
                     f"| {'yes' if gate else 'NO'} |")

    h1_sizes = [s for s in sizes if s >= H1_MIN_SIZE and res[s]["matched"]]
    h1 = bool(h1_sizes) and all(res[s]["pleated"] > H1_RATIO for s in h1_sizes)
    h2_ok = H2_SIZE in res and res[H2_SIZE]["matched"]
    h2 = h2_ok and res[H2_SIZE]["pleated"] <= H2_RATIO
    lines += [
        "",
        f"- FPR-match criterion (≤{FPR_TOL:.0%} relative): "
        + ", ".join(f"{s:,}: {'matched' if res[s]['matched'] else 'NOT matched (excluded from ratio claims)'}" for s in sizes),
        f"- Correctness gate (stock FP == pleated FP): "
        + ("PASS at every size" if all(r["gate"] for r in res.values()) else "FAIL — investigate before using any number"),
        f"- **H-E3-1** (pleated/Bloom > {H1_RATIO} at every FPR-matched size ≥ {H1_MIN_SIZE:,}): "
        + ("HOLDS" if h1 else "DOES NOT HOLD" if h1_sizes else "NOT EVALUABLE (no FPR-matched size)"),
        f"- **H-E3-2** (pleated/Bloom ≤ {H2_RATIO} at {H2_SIZE:,}): "
        + ("HOLDS — 'matches Bloom' wording permitted for single-thread build" if h2
           else "FAILS — the paper says 'narrows the gap', with the measured ratios" if h2_ok
           else "NOT EVALUABLE (size missing or not FPR-matched)"),
        "",
        "Scope: one thread, RocksDB's own harness and builders, build time as filter_bench reports "
        "it (AddKey + Finish, hashing included). Not an equal-thread parallel comparison.",
    ]
    (RES / "ANALYSIS.md").write_text("\n".join(lines) + "\n")

    tex = ["% generated-by: experiments/e3_bloom_gap/analyze.py — do not hand-edit",
           "\\newcommand{\\ethreerows}{%"]
    for s in sizes:
        b, st, pl = (mean(s, a, "build_ns_per_key") for a in ARMS)
        tex.append(f"{s:,} & {b:.1f} & {st:.1f} & {pl:.1f} & {st / b:.1f}$\\times$ & "
                   f"{pl / b:.1f}$\\times$ & {mean(s, 'bloom', 'fp_rate_pct'):.2f} / "
                   f"{mean(s, 'pleated', 'fp_rate_pct'):.2f} \\\\")
    tex.append("}")
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_TEX.write_text("\n".join(tex) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
