#!/usr/bin/env python3
"""Derive results/e1b/PHASE1B_ANALYSIS.md from window_sweep/ and parallel/ raw JSON only.
Evaluates registered H-E1b-2p conditions: (a) bit-identity vs the sequential partitioned
fingerprint for the same (n, rep); (b) deferred fraction <0.5% at 100M; (c) banding speedup
≥3x at 8 threads on 100M keys. Window sweep is descriptive (no thresholds).
"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WS = ROOT / "results" / "e1b" / "window_sweep"
PAR = ROOT / "results" / "e1b" / "parallel"
P1 = ROOT / "results" / "e1b" / "phase1"
OUT = ROOT / "results" / "e1b" / "PHASE1B_ANALYSIS.md"


def load(d):
    rows = []
    for f in sorted(d.glob("*.json")):
        rows.append(json.loads(f.read_text()))
    return rows


def main():
    ws, par = load(WS), load(PAR)
    if not ws or not par:
        sys.exit("missing window_sweep or parallel artifacts")
    # Sequential fingerprints per (n, rep) from phase1 partitioned runs.
    seq_fnv = {}
    for f in P1.glob("partitioned_*_rep*.json"):
        d = json.loads(f.read_text())
        seq_fnv[(d["n"], d["rep"])] = d["soln_fnv"]

    lines = ["generated-by: experiments/e1b_ribbon_construction/analyze_phase1b.py over "
             "results/e1b/{window_sweep,parallel}/",
             "", "# E1b Phase-1b analysis (derived — do not hand-edit)", "",
             "## Window-size sweep (partitioned, n=100M, mean over reps, ns/key)", "",
             "| shift | window slots | reorder | banding | TOTAL | banding miss/key |",
             "|---|---|---|---|---|---|"]
    by_shift = {}
    for d in ws:
        by_shift.setdefault(d["window_shift"], []).append(d)
    for shift in sorted(by_shift):
        rs = by_shift[shift]
        m = lambda f: statistics.mean(r[f] for r in rs)
        lines.append(f"| {shift} | 2^{shift} | {m('reorder_ns_per_key'):.2f} "
                     f"| {m('banding_ns_per_key'):.2f} | **{m('total_ns_per_key'):.2f}** "
                     f"| {m('banding_miss_per_key'):.3f} |")

    lines += ["", "## Parallel windows (H-E1b-2p; shift=16)", "",
              "| n | threads | banding ns/key | TOTAL ns/key | banding speedup vs T=1 | deferred % | bit-identity |",
              "|---|---|---|---|---|---|---|"]
    by_tn = {}
    for d in par:
        by_tn.setdefault((d["n"], d["threads"]), []).append(d)
    base = {}
    for (n, t), rs in sorted(by_tn.items()):
        if t == 1:
            base[n] = statistics.mean(r["banding_ns_per_key"] for r in rs)
    cond_a = True
    for (n, t), rs in sorted(by_tn.items()):
        m = lambda f: statistics.mean(r[f] for r in rs)
        ident = all(seq_fnv.get((r["n"], r["rep"])) == r["soln_fnv"] for r in rs)
        cond_a = cond_a and ident
        sp = f"{base[n] / m('banding_ns_per_key'):.2f}×" if n in base else "—"
        lines.append(f"| {n:,} | {t} | {m('banding_ns_per_key'):.2f} | **{m('total_ns_per_key'):.2f}** "
                     f"| {sp} | {100 * m('deferred') / n:.3f}% | {'PASS' if ident else 'FAIL'} |")

    t8 = by_tn.get((100_000_000, 8))
    cond_b = t8 and statistics.mean(r["deferred"] for r in t8) / 1e8 < 0.005
    cond_c = t8 and (100_000_000 in base) and \
        base[100_000_000] / statistics.mean(r["banding_ns_per_key"] for r in t8) >= 3.0
    lines += ["", "## H-E1b-2p registered conditions",
              f"- (a) bit-identity everywhere: {'PASS' if cond_a else 'FAIL — affected timings uninterpretable'}",
              f"- (b) deferred <0.5% at 100M/T=8: {'PASS' if cond_b else 'FAIL'}",
              f"- (c) banding speedup ≥3× at T=8/100M: {'PASS' if cond_c else 'FAIL'}",
              "", f"**H-E1b-2p {'CONFIRMED' if (cond_a and cond_b and cond_c) else 'NOT confirmed as registered'}.**"]

    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
