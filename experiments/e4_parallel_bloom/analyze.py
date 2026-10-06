#!/usr/bin/env python3
"""Derive results/e4/ANALYSIS.md from raw E4 artifacts only and evaluate the registered rules of
README.md mechanically (gates, cross-validation, H-E4-1, H-E4-2). Also writes
paper/tables/e4_parallel.tex.
"""
import json
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = Path(os.environ.get("E4_RES", ROOT / "results" / "e4"))
OUT_TEX = Path(os.environ.get("E4_TEX", ROOT / "paper" / "tables" / "e4_parallel.tex"))
sys.path.insert(0, str(ROOT / "experiments" / "e1b_ribbon_construction"))
from analyze import parse as parse_fastfilter  # noqa: E402

N = 100_000_000
THREADS = [1, 2, 4, 8, 16]
PAR = ["par_range", "par_atomic", "par_scan"]
SEQ = ["perkey", "perkey_prefetch"]
XVAL_TOL = 0.25
H1_RATIO, H2_RATIO, H2_T = 1.5, 1.25, 16


def crit(name):
    p = RES / "criterion" / "e4_construct_100M" / name / "new" / "estimates.json"
    if not p.exists():
        sys.exit(f"missing {p}")
    e = json.loads(p.read_text())
    return e["mean"]["point_estimate"] / N, e["std_dev"]["point_estimate"] / N


def main():
    machine = json.loads((RES / "machine.json").read_text())
    bloom = {name: crit(name) for name in SEQ}
    for t in THREADS:
        for b in PAR:
            bloom[f"{b}_t{t}"] = crit(f"{b}_t{t}")
    gate_bloom = "E4 gate: all parallel builders bit-identical" in (
        RES / "criterion_stdout.txt").read_text()

    rib = {}
    for f in sorted((RES / "ribbon").glob("*.json")):
        d = json.loads(f.read_text())
        key = d["threads"] if d["strategy"] == "parallel" else 0
        rib.setdefault(key, []).append(d)
    seq_fnv = {d["rep"]: d["soln_fnv"] for d in rib[0]}
    gate_fn = all(d["false_negatives"] == 0 for rs in rib.values() for d in rs)
    gate_fnv = all(d["soln_fnv"] == seq_fnv[d["rep"]] for t in THREADS for d in rib[t])

    anchor = [parse_fastfilter(f)[0] for f in sorted((RES / "anchor").glob("BlockedBloom_*.txt"))]
    anchor_mean = statistics.mean(anchor)
    xval = abs(bloom["perkey"][0] - anchor_mean) / anchor_mean
    xval_ok = xval <= XVAL_TOL

    def rmean(t):
        return statistics.mean(d["total_ns_per_key"] for d in rib[t])

    def rsd(t):
        v = [d["total_ns_per_key"] for d in rib[t]]
        return statistics.stdev(v) if len(v) > 1 else 0.0

    # Symmetric with Bloom: at T=1 the ribbon figure is the better of the parallel path and
    # the sequential pleated build.
    rib_key = {t: t for t in THREADS}
    if rmean(0) < rmean(1):
        rib_key[1] = 0

    best = {}
    for t in THREADS:
        cands = [f"{b}_t{t}" for b in PAR] + (SEQ if t == 1 else [])
        best[t] = min(cands, key=lambda c: bloom[c][0])

    L = [
        "generated-by: experiments/e4_parallel_bloom/analyze.py over results/e4/ "
        f"(machine: {machine['cpu']}, {machine['arch']}, {machine['nproc']} CPUs, "
        f"virt: {machine['virt']}; {machine['rustc']})",
        "",
        "# E4 analysis (derived — do not hand-edit)",
        "",
        f"Topology: {json.dumps(machine['lscpu'])}",
        "",
        "## Gates",
        "",
        f"- Bloom bit-identity (bench fingerprint gate at 100M, every T): {'PASS' if gate_bloom else 'FAIL'}",
        f"- Ribbon false negatives == 0 in every run: {'PASS' if gate_fn else 'FAIL'}",
        f"- Ribbon parallel fingerprint == sequential partitioned (same rep): {'PASS' if gate_fnv else 'FAIL'}",
        f"- Cross-validation, prototype `perkey` {bloom['perkey'][0]:.2f} vs fastfilter_cpp BlockedBloom "
        f"{anchor_mean:.2f} ns/key ({len(anchor)} reps): {xval:.1%} apart "
        f"(tolerance {XVAL_TOL:.0%}) -> {'PASS' if xval_ok else 'FAIL — ratio claims void'}",
    ]
    fpr = RES / "fpr_100M.json"
    if fpr.exists():
        f = next(x for x in json.loads(fpr.read_text())["filters"] if x["name"] == "lanefilter_sbbf")
        L.append(f"- Prototype quality at 100M keys: FPR {f['measured_fpr'] * 100:.4f}% at "
                 f"{f['bits_per_key']:.2f} bits/key")
    r0 = rib[0][0]
    L.append(f"- Ribbon quality: FPR {r0['fpr'] * 100:.4f}% at {r0['bits_per_key']:.2f} bits/key")

    L += ["", "## Bloom builders, 100M keys (ns/key, Criterion mean ± std dev)", "",
          "| builder | " + " | ".join(f"T={t}" for t in THREADS) + " |",
          "|---|" + "---|" * len(THREADS)]
    for b in PAR:
        L.append(f"| {b} | " + " | ".join(
            f"{bloom[f'{b}_t{t}'][0]:.2f}±{bloom[f'{b}_t{t}'][1]:.2f}" for t in THREADS) + " |")
    for b in SEQ:
        L.append(f"| {b} (sequential) | {bloom[b][0]:.2f}±{bloom[b][1]:.2f} |" + " — |" * (len(THREADS) - 1))

    L += ["", "## Equal-thread comparison", "",
          f"Sequential pleated ribbon (`partitioned`): {rmean(0):.2f}±{rsd(0):.2f} ns/key.", "",
          "| T | best Bloom build | Bloom ns/key | ribbon total ns/key | ribbon / Bloom | Bloom speedup vs T=1 | ribbon speedup vs T=1 |",
          "|---|---|---|---|---|---|---|"]
    ratio = {}
    for t in THREADS:
        bn = bloom[best[t]][0]
        rk = rib_key[t]
        ratio[t] = rmean(rk) / bn
        L.append(f"| {t} | {best[t]} | {bn:.2f} | {rmean(rk):.2f}±{rsd(rk):.2f}"
                 f"{' (sequential)' if rk == 0 else ''} | {ratio[t]:.2f}x "
                 f"| {bloom[best[1]][0] / bn:.2f}x | {rmean(rib_key[1]) / rmean(rk):.2f}x |")

    valid = gate_bloom and gate_fn and gate_fnv and xval_ok
    h1 = all(ratio[t] > H1_RATIO for t in THREADS)
    h2 = ratio[H2_T] <= H2_RATIO
    L += ["",
          f"- **H-E4-1** (ribbon > {H1_RATIO}x best Bloom at every T): "
          + ("HOLDS" if h1 else "DOES NOT HOLD") + ("" if valid else " [VOID: a gate failed]"),
          f"- **H-E4-2** (ribbon ≤ {H2_RATIO}x best Bloom at T={H2_T}): "
          + ("HOLDS — 'matches Bloom' wording permitted for parallel build" if h2
             else "FAILS — equal-thread ratio must accompany any multi-thread comparison")
          + ("" if valid else " [VOID: a gate failed]"),
          "",
          "Scope: one machine, 100M keys; Bloom 10 bits/key vs ribbon ~7.6 (not FPR- or "
          "space-matched); Criterion and the C++ driver run back to back; ribbon reorder and "
          "back-substitution are sequential."]
    (RES / "ANALYSIS.md").write_text("\n".join(L) + "\n")

    tex = ["% generated-by: experiments/e4_parallel_bloom/analyze.py — do not hand-edit",
           f"\\newcommand{{\\efourratiomax}}{{{ratio[max(THREADS)]:.1f}}}",
           f"\\newcommand{{\\efourratioone}}{{{ratio[1]:.1f}}}",
           f"\\newcommand{{\\efourbloommax}}{{{bloom[best[max(THREADS)]][0]:.2f}}}",
           f"\\newcommand{{\\efourribbonmax}}{{{rmean(max(THREADS)):.1f}}}",
           "\\newcommand{\\efourrows}{%"]
    for t in THREADS:
        tex.append(f"{t} & {best[t].replace('_', chr(92) + '_')} & {bloom[best[t]][0]:.2f} & "
                   f"${rmean(rib_key[t]):.2f}\\pm{rsd(rib_key[t]):.2f}$ & {ratio[t]:.1f}$\\times$ \\\\")
    tex.append("}")
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_TEX.write_text("\n".join(tex) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
