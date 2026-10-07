#!/usr/bin/env python3
"""Derive results/e6/ANALYSIS.md and paper/tables/e6.tex from raw E6 artifacts only, and evaluate
H-E6-1, H-E6-2 and H-E6-3 of README.md mechanically."""
import json
import os
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = Path(os.environ.get("E6_RES", ROOT / "results" / "e6"))
OUT_TEX = Path(os.environ.get("E6_TEX", ROOT / "paper" / "tables" / "e6.tex"))
N = 100_000_000


def mean(v):
    return statistics.mean(v)


def main():
    machine = json.loads((RES / "machine.json").read_text())
    L = ["generated-by: experiments/e6_memory_and_boundary/analyze.py over results/e6/ "
         f"(machine: {machine['cpu']}, {machine['arch']}, {machine['nproc']} CPUs)",
         "", "# E6 analysis (derived — do not hand-edit)", "",
         f"Topology: {json.dumps(machine['lscpu'])}", ""]

    # ---- spill
    sp = RES / "spill"
    seq = {json.loads(f.read_text())["rep"]: json.loads(f.read_text()) for f in sp.glob("sequential_rep*.json")}
    rows = [json.loads(f.read_text()) for f in sorted(sp.glob("parallel_*.json"))]
    L += ["## Boundary fallback (parallel banding with reduced margins)", "",
          "| threads | margin (slots) | runs | spilled (min-max) | deferred (max) | fingerprint == sequential | false negatives |",
          "|---|---|---|---|---|---|---|"]
    h1, exercised, max_spill = True, False, 0
    for t in sorted({r["threads"] for r in rows}):
        for g in sorted({r["margin"] for r in rows}, reverse=True):
            rs = [r for r in rows if r["threads"] == t and r["margin"] == g]
            same = all(r["soln_fnv"] == seq[r["rep"]]["soln_fnv"] for r in rs)
            fn = sum(r["false_negatives"] for r in rs)
            spl = [r["spilled"] for r in rs]
            h1 &= same and fn == 0
            exercised |= max(spl) > 0
            max_spill = max(max_spill, max(spl))
            L.append(f"| {t} | {g} | {len(rs)} | {min(spl)}-{max(spl)} | {max(r['deferred'] for r in rs)} "
                     f"| {'yes' if same else 'NO'} | {fn} |")
    L += ["", f"- **H-E6-1** (identical output and no false negatives at every setting): "
          + ("HOLDS" if h1 else "FAILS"),
          f"- Fallback exercised (some run with spilled > 0): {'yes, up to ' + format(max_spill, ',') + ' keys in one run' if exercised else 'NO — not exercised'}",
          ""]

    # ---- memory
    mem = {}
    for f in sorted((RES / "memory").glob("*_rep*.json")):
        r = json.loads(f.read_text())
        mem.setdefault(r["strategy"], []).append(r)
    ref = mean([r["peak_rss_kb"] for r in mem["reference"]])
    L += ["## Peak resident memory, standalone driver, 100M keys (whole process)", "",
          "| strategy | runs | peak RSS MB (mean, min-max) | delta vs reference MB | delta bytes/key | total ns/key |",
          "|---|---|---|---|---|---|"]
    delta_bpk = {}
    for s in ["reference", "sort_radix", "sort_ips2ra", "partitioned", "parallel"]:
        v = [r["peak_rss_kb"] for r in mem[s]]
        d = (mean(v) - ref) * 1024
        delta_bpk[s] = d / N
        L.append(f"| {s}{' (16 threads)' if s == 'parallel' else ''} | {len(v)} | {mean(v) / 1024:.0f} "
                 f"({min(v) / 1024:.0f}-{max(v) / 1024:.0f}) | {d / 2**20:+.0f} | {d / N:+.2f} "
                 f"| {mean([r['total_ns_per_key'] for r in mem[s]]):.1f} |")
    h2 = 6.0 <= delta_bpk["partitioned"] <= 10.0
    L += ["", f"- **H-E6-2** (partitioned exceeds reference by 8 bytes/key ±25%): "
          + ("HOLDS" if h2 else "FAILS") + f" — measured {delta_bpk['partitioned']:+.2f} bytes/key", ""]

    fb = {}
    for f in sorted((RES / "memory").glob("fb_*_rep*.txt")):
        arm = f.name.split("_")[1]
        t = f.read_text()
        fb.setdefault(arm, []).append((int(re.search(r"PEAK_RSS_KB (\d+)", t).group(1)),
                                       float(re.search(r"Build avg ns/key:\s*([\d.]+)", t).group(1))))
    L += ["## Peak resident memory, RocksDB filter_bench, 100M keys per filter (whole process)", "",
          "| arm | runs | peak RSS MB (mean, min-max) | build ns/key |", "|---|---|---|---|"]
    for arm in ("stock", "pleated"):
        v = [x[0] for x in fb[arm]]
        L.append(f"| {arm} | {len(v)} | {mean(v) / 1024:.0f} ({min(v) / 1024:.0f}-{max(v) / 1024:.0f}) "
                 f"| {mean([x[1] for x in fb[arm]]):.1f} |")
    fb_delta_mb = (mean([x[0] for x in fb["pleated"]]) - mean([x[0] for x in fb["stock"]])) / 1024
    L += ["", f"Pleated minus stock peak: {fb_delta_mb:+.0f} MB (descriptive; filter_bench varies keys "
          "per filter by up to 40% and holds its finished filters).", ""]

    # ---- concurrent
    conc = {}
    for f in sorted((RES / "concurrent").glob("k*_rep*.json")):
        r = json.loads(f.read_text())
        conc.setdefault((r["k"], r["strategy"]), []).extend(x["total_ns_per_key"] for x in r["runs"])
    L += ["## Concurrent builders (K pinned processes, 100M keys each; per-process total ns/key)", "",
          "| K | reference (mean, min-max) | partitioned (mean, min-max) | reference / partitioned |",
          "|---|---|---|---|"]
    ratio = {}
    for k in sorted({k for k, _ in conc}):
        a, b = conc[(k, "reference")], conc[(k, "partitioned")]
        ratio[k] = mean(a) / mean(b)
        L.append(f"| {k} | {mean(a):.1f} ({min(a):.1f}-{max(a):.1f}) | {mean(b):.1f} ({min(b):.1f}-{max(b):.1f}) "
                 f"| {ratio[k]:.2f}x |")
    h3 = all(ratio[k] >= 1.5 for k in ratio if k > 1)
    L += ["", f"- **H-E6-3** (partitioned ≥ 1.5x faster per process at K=4 and K=8): "
          + ("HOLDS" if h3 else "FAILS"), "",
          "Scope: one machine; whole-process peak RSS includes the input keys and the verification "
          "pass, so only differences between strategies are attributed to the reorder; concurrent "
          "builders are separate processes."]
    (RES / "ANALYSIS.md").write_text("\n".join(L) + "\n")

    def m(name, val):
        return f"\\newcommand{{\\{name}}}{{{val}}}"
    ks = sorted(ratio)
    tex = ["% generated-by: experiments/e6_memory_and_boundary/analyze.py — do not hand-edit",
           m("esixrefrss", f"{ref / 2**20:.1f}"),
           m("esixpartrss", f"{mean([r['peak_rss_kb'] for r in mem['partitioned']]) / 2**20:.1f}"),
           m("esixpartdelta", f"{delta_bpk['partitioned']:.1f}"),
           m("esixsortdelta", f"{delta_bpk['sort_ips2ra']:.1f}"),
           m("esixpardelta", f"{delta_bpk['parallel']:.1f}"),
           m("esixfbstock", f"{mean([x[0] for x in fb['stock']]) / 2**20:.1f}"),
           m("esixfbpleated", f"{mean([x[0] for x in fb['pleated']]) / 2**20:.1f}"),
           m("esixmaxspill", f"{max_spill:,}".replace(",", "{,}")),
           m("esixratioone", f"{ratio[ks[0]]:.2f}"),
           m("esixratiomid", f"{ratio[ks[1]]:.2f}"),
           m("esixratiomax", f"{ratio[ks[-1]]:.2f}")]
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_TEX.write_text("\n".join(tex) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
