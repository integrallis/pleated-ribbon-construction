#!/usr/bin/env python3
"""Derive results/e7/<machine>/ANALYSIS.md from that machine's raw files, by the rules of
README.md. Usage: analyze.py [results-dir ...]   (default: every directory under results/e7)

Median, minimum and maximum per cell; ratio of medians with a 95% percentile bootstrap
(10,000 resamples, fixed seed, arms resampled independently).
"""
import json
import math
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOT, SEED = 10_000, 0xE7
L2_EVENT = {"GenuineIntel": "mem_load_retired.l2_miss", "ARM": "l2d_cache_lmiss_rd",
            "AuthenticAMD": "l2_cache_req_stat.ic_dc_miss_in_l2"}
SORTS = ["sort_std", "sort_radix", "sort_ips2ra"]


def load(directory):
    return [json.loads(f.read_text()) for f in sorted(directory.glob("*_rep*.json"))]


def med(xs):
    return statistics.median(xs)


def cell(xs, digits=1):
    return f"{med(xs):.{digits}f} ({min(xs):.{digits}f}–{max(xs):.{digits}f})"


def boot(f, *arms):
    """Point estimate of f(medians) and its 95% bootstrap interval."""
    rng = random.Random(SEED)
    point = f(*[med(a) for a in arms])
    draws = sorted(f(*[med(rng.choices(a, k=len(a))) for a in arms]) for _ in range(BOOT))
    return point, draws[int(0.025 * BOOT)], draws[int(0.975 * BOOT) - 1]


def ratio(a, b):
    return boot(lambda x, y: x / y if y else float("nan"), a, b)


def fmt(triple, digits=2, suffix="×"):
    p, lo, hi = triple
    return f"{p:.{digits}f}{suffix} [{lo:.{digits}f}, {hi:.{digits}f}]"


def verdict(ok):
    return "HOLDS" if ok else "FAILS"


def by(rows, *fields):
    out = {}
    for r in rows:
        out.setdefault(tuple(r[f] for f in fields), []).append(r)
    return out


def run_checks(rows, group_fields, problems, stage):
    """Zero false negatives, equal fingerprints within a group, bits/key above the bound."""
    for r in rows:
        if r["false_negatives"]:
            problems.append(f"{stage}: false negatives in {r['strategy']} n={r['n']} rep={r['rep']}")
        if r["fpr"] > 0 and r["bits_per_key"] < math.log2(1 / r["fpr"]) - 1e-9:
            problems.append(f"{stage}: {r['bits_per_key']} bits/key at FPR {r['fpr']} is below the bound")
    for key, group in by(rows, *group_fields).items():
        if len({r["soln_fnv"] for r in group}) != 1:
            problems.append(f"{stage}: fingerprints differ within {dict(zip(group_fields, key))}")


def analyze(res):
    machine = json.loads((res / "machine.json").read_text())
    L, rules, problems = [], [], []
    head = (f"generated-by: experiments/e7_rigour/analyze.py over {res.relative_to(ROOT)}/raw/ "
            f"(machine: {machine['cpu']}, {machine['arch']}, kernel {machine['kernel']}, "
            f"virt: {machine['virt']}, profile: {machine['profile']}, source {machine['source_commit']})")
    L += [head, "", f"# E7 analysis, {res.name} (derived; do not hand-edit)", "",
          f"Pinned CPU {machine['pinned_cpu']} (siblings {machine['pinned_cpu_siblings']}), governor "
          f"{machine['governor']}, intel no_turbo {machine['intel_no_turbo']}, boost {machine['cpufreq_boost']}, "
          f"SMT active {machine['smt_active']}, THP {machine['thp_enabled']}, {machine['gcc']}.", "",
          "Cells are median (minimum–maximum) over the repetitions; ratios are ratios of medians "
          "with a 95% bootstrap interval.", ""]

    # ---- crosscheck
    if (res / "crosscheck.json").exists():
        cc = json.loads((res / "crosscheck.json").read_text())
        L += ["## Cross-check of e7_driver against e1b_phase1", "",
              "| keys | strategy | fingerprints equal | median total e1b_phase1 | median total e7_driver | ratio | tolerance |",
              "|---|---|---|---|---|---|---|"]
        for r in cc["rows"]:
            L.append(f"| {r['n']:,} | {r['strategy']} | {'yes' if r['fingerprints_equal'] else 'NO'} | "
                     f"{r['median_total_e1b']:.2f} | {r['median_total_e7']:.2f} | {r['ratio']:.3f} | ±{r['tolerance']:.0%} |")
        L += ["", f"Cross-check {'passed' if cc['passed'] else 'FAILED'}.", ""]

    # ---- main
    if (res / "main.done").exists():
        rows = load(res / "raw" / "main")
        run_checks(rows, ("n", "rep"), problems, "main")
        g = by(rows, "n", "strategy")
        L += ["## Construction by key count and strategy (ns/key)", "",
              "| keys | strategy | reps | reorder | banding | back-substitution | total |", "|---|---|---|---|---|---|---|"]
        for (n, s), rs in sorted(g.items()):
            L.append(f"| {n:,} | {s} | {len(rs)} | {cell([r['reorder_ns_per_key'] for r in rs])} | "
                     f"{cell([r['banding_ns_per_key'] for r in rs])} | {cell([r['backsubst_ns_per_key'] for r in rs])} | "
                     f"{cell([r['total_ns_per_key'] for r in rs])} |")
        L += ["", "| keys | reference / partitioned | best full sort | best sort / partitioned |", "|---|---|---|---|"]
        h1 = h1b = True
        for n in sorted({k[0] for k in g}):
            tot = lambda s: [r["total_ns_per_key"] for r in g[(n, s)]]
            best = min(SORTS, key=lambda s: med(tot(s)))
            a, b = ratio(tot("reference"), tot("partitioned")), ratio(tot(best), tot("partitioned"))
            L.append(f"| {n:,} | {fmt(a)} | {best} | {fmt(b)} |")
            if n >= 100_000_000:
                h1 = h1 and a[0] >= 1.5 and a[1] > 1
                h1b = h1b and b[0] > 1 and b[1] > 1
        L.append("")
        rules += [f"- **H1** (reference at least 1.5× partitioned at 100M and 400M, interval above 1): {verdict(h1)}",
                  f"- **H1b** (partitioned below every full sort at 100M and 400M, interval excluding 1): {verdict(h1b)}"]

    # ---- parallel
    if (res / "parallel.done").exists():
        rows = load(res / "raw" / "parallel")
        run_checks(rows, ("n", "rep"), problems, "parallel")
        seq = [r["banding_ns_per_key"] for r in rows if r["strategy"] == "partitioned"]
        par = by([r for r in rows if r["strategy"] == "parallel"], "threads")
        t1 = [r["banding_ns_per_key"] for r in par.get((1,), [])]
        L += ["## Parallel build, 100M keys (ns/key)", "",
              "| threads | reps | banding | total | banding vs its own 1 thread | banding vs sequential partitioned | deferred keys |",
              "|---|---|---|---|---|---|---|"]
        h6 = None
        for (t,), rs in sorted(par.items()):
            b = [r["banding_ns_per_key"] for r in rs]
            own = fmt(ratio(t1, b)) if t1 else "-"
            vs = ratio(seq, b)
            if t == 16:
                h6 = vs[0] >= 3
            L.append(f"| {t} | {len(rs)} | {cell(b)} | {cell([r['total_ns_per_key'] for r in rs])} | {own} | {fmt(vs)} | "
                     f"{med([r['deferred'] for r in rs]) / rs[0]['n']:.4%} |")
        L += ["", f"Sequential partitioned banding: {cell(seq)} ns/key.", ""]
        rules.append("- **H6** (16-thread banding at least 3× sequential partitioned banding): "
                     + ("not measured" if h6 is None else verdict(h6)))

    # ---- counters
    if (res / "counters.done").exists():
        rows = load(res / "raw" / "counters")
        run_checks(rows, ("n", "rep"), problems, "counters")
        names = {int(code, 16): name for name, code in machine["events"].items() if code}
        series = {}  # (n, event) -> strategy -> values
        for r in rows:
            if "banding_miss_per_key" in r:
                for label, field in (("generic cache-misses", "banding_miss_per_key"),
                                     ("instructions", "banding_instr_per_key"), ("cycles", "banding_cycles_per_key")):
                    series.setdefault((r["n"], label), {}).setdefault(r["strategy"], []).append(r[field])
            for code, v in r.get("banding_raw_per_key", {}).items():
                name = names.get(int(code, 16), code)
                series.setdefault((r["n"], name), {}).setdefault(r["strategy"], []).append(v)
        L += ["## Counters scoped to banding, per key", "",
              "Events resolved on this machine: " + ", ".join(f"`{n}` = {c or 'missing'}" for n, c in machine["events"].items()) + ".", "",
              "| keys | event | reference | LSD radix | ips2ra | partitioned | recovery of the best sort's reduction |",
              "|---|---|---|---|---|---|---|"]
        l2, h2 = L2_EVENT.get(machine["vendor"]), None
        for (n, event), s in sorted(series.items()):
            if not all(k in s for k in ("reference", "sort_radix", "sort_ips2ra", "partitioned")):
                continue
            best = min(("sort_radix", "sort_ips2ra"), key=lambda k: med(s[k]))
            rec = "-"
            if event not in ("instructions", "cycles") and med(s["reference"]) > med(s[best]):
                triple = boot(lambda a, b, c: (a - c) / (a - b), s["reference"], s[best], s["partitioned"])
                rec = fmt((triple[0] * 100, triple[1] * 100, triple[2] * 100), 1, "%")
                if event == l2:
                    h2 = (h2 is None or h2) and triple[0] >= 0.90
            L.append(f"| {n:,} | {event} | {cell(s['reference'], 3)} | {cell(s['sort_radix'], 3)} | "
                     f"{cell(s['sort_ips2ra'], 3)} | {cell(s['partitioned'], 3)} | {rec} |")
        L.append("")
        rules.append(f"- **H2** (at least 90% recovery on `{l2}` at 100M and 400M): "
                     + ("UNDECIDED, the event was not measured" if h2 is None else verdict(h2)))

    def ratio_table(stage, title, key_fields, label, threshold, rule_name, rule_text):
        rows = load(res / "raw" / stage)
        run_checks(rows, (*key_fields, "rep"), problems, stage)
        g = by(rows, *key_fields, "strategy")
        L.extend([f"## {title}", "",
                  "| " + label + " | reference total | ips2ra total | partitioned total | reference / partitioned | ips2ra / partitioned | FPR | bits/key |",
                  "|---|---|---|---|---|---|---|---|"])
        ok = True
        for key in sorted({k[:-1] for k in g}, key=str):
            tot = lambda s: [r["total_ns_per_key"] for r in g[(*key, s)]]
            first = g[(*key, "partitioned")]
            a = ratio(tot("reference"), tot("partitioned"))
            ok = ok and a[0] >= threshold
            L.append(f"| {' / '.join(str(k) for k in key)} | "
                     f"{cell(tot('reference'))} | {cell(tot('sort_ips2ra'))} | {cell(tot('partitioned'))} | {fmt(a)} | "
                     f"{fmt(ratio(tot('sort_ips2ra'), tot('partitioned')))} | {med([r['fpr'] for r in first]):.6f} | "
                     f"{first[0]['bits_per_key']:.2f} |")
        L.append("")
        if rule_name:
            rules.append(f"- **{rule_name}** ({rule_text}): {verdict(ok)}")

    if (res / "config.done").exists():
        ratio_table("config", "Configurations, 100M synthetic keys (total ns/key)", ("w", "r", "overhead"),
                    "band width / result bits / slots per key", 1.3, "H3",
                    "reference at least 1.3× partitioned in each of the eight configurations")
    if (res / "keys.done").exists():
        # The key set's name is in the file name, not in the driver's output.
        raw = res / "raw" / "keys"
        named = []
        for f in sorted(raw.glob("*_rep*.json")):
            r = json.loads(f.read_text())
            r["set"] = f.name.rsplit("_" + r["strategy"] + "_rep", 1)[0]
            named.append(r)
        g = by(named, "set", "strategy")
        run_checks(named, ("set", "rep"), problems, "keys")
        manifest = json.loads((res / "keys" / "manifest.json").read_text())
        L += ["## Key sets (total ns/key, hashing included)", "",
              "| key set | keys | mean key bytes | hashing | reference total | ips2ra total | partitioned total | reference / partitioned | ips2ra / partitioned |",
              "|---|---|---|---|---|---|---|---|---|"]
        h4 = True
        for name in sorted({k[0] for k in g}):
            tot = lambda s: [r["total_ns_per_key"] for r in g[(name, s)]]
            first = g[(name, "partitioned")]
            a = ratio(tot("reference"), tot("partitioned"))
            if not name.endswith("_direct"):
                h4 = h4 and a[0] >= 1.5
            L.append(f"| {name} | {first[0]['n']:,} | {first[0]['mean_key_bytes']:.1f} | {med([r['hash_ns_per_key'] for r in first]):.1f} | "
                     f"{cell(tot('reference'))} | {cell(tot('sort_ips2ra'))} | {cell(tot('partitioned'))} | {fmt(a)} | "
                     f"{fmt(ratio(tot('sort_ips2ra'), tot('partitioned')))} |")
        L += ["", "`_hashed`: strings hashed once with XXH3, then 64-bit values (integer sets are used as they are). "
              "`_direct`: the string is the filter's key and is hashed again in every pass.", "",
              "Sources: " + "; ".join(f"{k}: {v['source']}" for k, v in manifest["sets"].items()) + ".", ""]
        rules.append(f"- **H4** (reference at least 1.5× partitioned, hashing included, for every integer set and "
                     f"every string set hashed once): {verdict(h4)}")
    if (res / "thp.done").exists():
        raw = res / "raw" / "thp"
        named = []
        for f in sorted(raw.glob("*_rep*.json")):
            r = json.loads(f.read_text())
            r["thp"] = f.name.split("_", 1)[0]
            named.append(r)
        run_checks(named, ("thp", "rep"), problems, "thp")
        g = by(named, "thp", "strategy")
        L += ["## Transparent huge pages, 100M synthetic keys (total ns/key; no hypothesis)", "",
              "| THP | reference | ips2ra | partitioned | reference / partitioned |", "|---|---|---|---|---|"]
        for mode in ("madvise", "always", "never"):
            tot = lambda s: [r["total_ns_per_key"] for r in g[(mode, s)]]
            L.append(f"| {mode} | {cell(tot('reference'))} | {cell(tot('sort_ips2ra'))} | {cell(tot('partitioned'))} | "
                     f"{fmt(ratio(tot('reference'), tot('partitioned')))} |")
        L.append("")
    if (res / "compaction.done").exists():
        rows = load(res / "raw" / "compaction")
        g = by(rows, "sst_target_bytes", "arm")
        L += ["## Compaction in db_bench (CPU seconds of compaction)", "",
              "| SST target | reps per arm | stock | pleated | pleated / stock | SST files at end (stock, pleated) |", "|---|---|---|---|---|---|"]
        h5 = None
        for sst in sorted({k[0] for k in g}):
            cpu = lambda arm: [r["compaction_cpu_micros"] / 1e6 for r in g[(sst, arm)]]
            a = ratio(cpu("pleated"), cpu("stock"))
            if sst == 256 << 20:
                h5 = a[0] < 1 and a[2] < 1
            L.append(f"| {sst >> 20} MiB | {len(cpu('stock'))} | {cell(cpu('stock'), 2)} | {cell(cpu('pleated'), 2)} | {fmt(a, 3)} | "
                     f"{med([r['sst_files_at_end'] for r in g[(sst, 'stock')]]):.0f}, {med([r['sst_files_at_end'] for r in g[(sst, 'pleated')]]):.0f} |")
        L.append("")
        rules.append("- **H5** (pleated compaction CPU below stock at 256 MiB, interval excluding 1): "
                     + ("not measured" if h5 is None else verdict(h5)))

    role = "primary machine: these decide" if res.name == "x86-intel" else "replication machine: reported, not deciding"
    L += [f"## Registered rules ({role})", "", *rules, "",
          "## Checks on every run", "",
          *([f"- PROBLEM: {p}" for p in problems] or
            ["- No false negatives; equal fingerprints across strategies in every repetition; every bits/key figure "
             "at or above log2(1/FPR)."]), ""]
    (res / "ANALYSIS.md").write_text("\n".join(L))
    print(f"wrote {res / 'ANALYSIS.md'}")
    print("\n".join(rules + [f"PROBLEM: {p}" for p in problems]))


if __name__ == "__main__":
    dirs = [Path(a).resolve() for a in sys.argv[1:]] or sorted(d for d in (ROOT / "results" / "e7").iterdir() if d.is_dir())
    for d in dirs:
        analyze(d)
