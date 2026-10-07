#!/usr/bin/env python3
"""Derive results/ARM_ANALYSIS.md from the committed ARM raw artifacts only: the N1 and V2
(Axion) Phase-1 timing replications, the V2 parallel runs, the cross-architecture fingerprint
comparison against the x86 Phase-1 runs, and the Graviton4 PMU follow-up. No new measurement.
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results"
BOXES = {"x86 (i9-14900HX)": RES / "e1b" / "phase1", "N1 (Ampere Altra)": RES / "e1b-arm-n1" / "phase1",
         "V2 (Google Axion)": RES / "e1b-arm-v2" / "phase1"}
SORTS = ["sort_std", "sort_radix", "sort_ips2ra"]
N = 100_000_000


def load(d):
    rows = {}
    for f in sorted(d.glob("*_rep*.json")):
        r = json.loads(f.read_text())
        rows.setdefault((r["strategy"], r["n"]), []).append(r)
    return rows


def msd(rs, field):
    v = [r[field] for r in rs]
    return statistics.mean(v), (statistics.stdev(v) if len(v) > 1 else 0.0)


def main():
    data = {name: load(d) for name, d in BOXES.items()}
    L = ["generated-by: experiments/e1b_ribbon_construction/analyze_arm.py over results/e1b/phase1/, "
         "results/e1b-arm-n1/phase1/, results/e1b-arm-v2/{phase1,parallel}/, "
         "results/e1b-arm-graviton4-pmu-20260930/e1b-100M.jsonl",
         "", "# ARM replication analysis (derived — do not hand-edit)", "",
         "## Construction total at 100M keys (ns/key, mean ± sample stdev)", "",
         "| machine | reps | reference | best full sort (which) | partitioned | pleating vs reference | pleating vs best sort | reference banding |",
         "|---|---|---|---|---|---|---|---|"]
    for name, rows in data.items():
        ref, part = rows[("reference", N)], rows[("partitioned", N)]
        best = min((s for s in SORTS if (s, N) in rows), key=lambda s: msd(rows[(s, N)], "total_ns_per_key")[0])
        b = rows[(best, N)]
        t = lambda rs: msd(rs, "total_ns_per_key")
        L.append(f"| {name} | {len(ref)} | {t(ref)[0]:.1f}±{t(ref)[1]:.1f} | {t(b)[0]:.1f}±{t(b)[1]:.1f} ({best}) "
                 f"| {t(part)[0]:.1f}±{t(part)[1]:.1f} | {t(ref)[0] / t(part)[0]:.2f}x | {t(b)[0] / t(part)[0]:.2f}x "
                 f"| {msd(ref, 'banding_ns_per_key')[0]:.1f} |")

    L += ["", "## Output checks", ""]
    fn = sum(r["false_negatives"] for rows in data.values() for rs in rows.values() for r in rs)
    L.append(f"- False negatives summed over every x86/N1/V2 Phase-1 run: {fn}")
    for name, rows in data.items():
        groups = {}
        for (strat, n), rs in rows.items():
            for r in rs:
                groups.setdefault((n, r["rep"]), set()).add(r["soln_fnv"])
        ok = sum(len(v) == 1 for v in groups.values())
        L.append(f"- {name}: all strategies share one fingerprint at {ok}/{len(groups)} (n, rep) points")
    fp = {name: {(n, r["rep"]): r["soln_fnv"] for (s, n), rs in rows.items() if s == "partitioned" for r in rs}
          for name, rows in data.items()}
    names = list(fp)
    common = set.intersection(*(set(v) for v in fp.values()))
    same = sum(len({fp[nm][k] for nm in names}) == 1 for k in common)
    L.append(f"- Cross-architecture: partitioned fingerprint identical on all three machines at "
             f"{same}/{len(common)} common (n, rep) points")

    par = {}
    for f in sorted((RES / "e1b-arm-v2" / "parallel").glob("*.json")):
        r = json.loads(f.read_text())
        par.setdefault(r["threads"], []).append(r)
    L += ["", "## V2 (Google Axion) parallel banding, 100M keys", "",
          "| threads | reps | banding ns/key | speedup vs T=1 | total ns/key | deferred % |", "|---|---|---|---|---|---|"]
    b1 = msd(par[1], "banding_ns_per_key")[0]
    for t in sorted(par):
        b = msd(par[t], "banding_ns_per_key")[0]
        L.append(f"| {t} | {len(par[t])} | {b:.2f} | {b1 / b:.2f}x | {msd(par[t], 'total_ns_per_key')[0]:.2f} "
                 f"| {max(r['deferred'] for r in par[t]) / N:.3%} |")

    pmu = {}
    for line in (RES / "e1b-arm-graviton4-pmu-20260930" / "e1b-100M.jsonl").read_text().splitlines():
        r = json.loads(line)
        pmu.setdefault(r["strategy"], []).append(r)
    med = {s: statistics.median(r["banding_l2d_lmiss_rd_per_key"] for r in rs) for s, rs in pmu.items()}
    L += ["", "## Graviton4 (Neoverse-V2) PMU follow-up, 100M keys, banding-scoped l2d_cache_lmiss_rd", "",
          "| strategy | reps | median L2 read misses/key | median total ns/key |", "|---|---|---|---|"]
    for s, rs in pmu.items():
        L.append(f"| {s} | {len(rs)} | {med[s]:.3f} | {statistics.median(r['total_ns_per_key'] for r in rs):.2f} |")
    sort_key = next(s for s in med if s.startswith("sort"))
    rec = (med["reference"] - med["partitioned"]) / (med["reference"] - med[sort_key])
    L.append("")
    L.append(f"Miss-reduction recovery of partitioned vs {sort_key}: {rec:.1%}")
    (RES / "ARM_ANALYSIS.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
