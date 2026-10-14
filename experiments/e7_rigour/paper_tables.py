#!/usr/bin/env python3
"""Paper macros and table rows from E7's committed raw files, by analyze.py's rules (median,
ratio of medians, bootstrap interval). Writes paper/tables/e7.tex. No new measurement.

The primary machine is results/e7/x86-intel; the replication machines are added to the
cross-machine table when their results are present.
"""
import importlib.util
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("e7analyze", Path(__file__).with_name("analyze.py"))
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)

E7 = ROOT / "results" / "e7"
P = E7 / "x86-intel"
M100, M400 = 100_000_000, 400_000_000
SORTS = ["sort_std", "sort_radix", "sort_ips2ra"]
LABEL = {"noprefetch": "unsorted, no prefetch", "reference": "unsorted + prefetch (ref.)",
         "sort_std": "full sort (std::sort)", "sort_radix": "full sort (LSD radix)",
         "sort_ips2ra": "full sort (ips2ra)", "partitioned": "\\textbf{partitioned (this work)}"}
MACHINES = [("x86-intel", "Xeon 8488C (Intel)"), ("x86-amd", "EPYC 9R14 (AMD)"),
            ("arm-graviton4", "Graviton4 (Arm)")]
out = ["% generated-by: experiments/e7_rigour/paper_tables.py — do not hand-edit"]


def macro(name, value):
    out.append(f"\\newcommand{{\\{name}}}{{{value}}}")


def rows(name, lines):
    out.append(f"\\newcommand{{\\{name}}}{{%")
    out.extend(lines)
    out.append("}")


def mmm(xs, d=1):
    return f"{A.med(xs):.{d}f} ({min(xs):.{d}f}--{max(xs):.{d}f})"


def by_n_strategy(res):
    return A.by(A.load(res / "raw" / "main"), "n", "strategy")


def tot(g, n, s, field="total_ns_per_key"):
    return [r[field] for r in g[(n, s)]]


def best_sort(g, n):
    return min(SORTS, key=lambda s: A.med(tot(g, n, s)))


# ---- main table (primary machine, 100M keys) and parallel rows
g = by_n_strategy(P)
main = []
for s in ["noprefetch", "reference", "sort_std", "sort_radix", "sort_ips2ra", "partitioned"]:
    reorder = "---" if s in ("noprefetch", "reference") else mmm(tot(g, M100, s, "reorder_ns_per_key"))
    main.append(f"{LABEL[s]} & {reorder} & {mmm(tot(g, M100, s, 'banding_ns_per_key'))} & "
                f"{mmm(tot(g, M100, s))} \\\\")
par = A.by([r for r in A.load(P / "raw" / "parallel") if r["strategy"] == "parallel"], "threads")
seq_band = [r["banding_ns_per_key"] for r in A.load(P / "raw" / "parallel") if r["strategy"] == "partitioned"]
main.append("\\midrule")
for t in (8, 16):
    rs = par[(t,)]
    main.append(f"parallel, {t} threads (this work) & {A.med([r['reorder_ns_per_key'] for r in rs]):.1f} & "
                f"{mmm([r['banding_ns_per_key'] for r in rs])} & {mmm([r['total_ns_per_key'] for r in rs])} \\\\")
rows("esevenmainrows", main)

# ---- by key count
scale = []
for n in (10_000_000, M100, M400):
    b = best_sort(g, n)
    a, c = A.ratio(tot(g, n, "reference"), tot(g, n, "partitioned")), A.ratio(tot(g, n, b), tot(g, n, "partitioned"))
    scale.append(f"{n // 1_000_000}M & {A.med(tot(g, n, 'reference')):.1f} & {A.med(tot(g, n, b)):.1f} & "
                 f"{A.med(tot(g, n, 'partitioned')):.1f} & {a[0]:.2f}$\\times$ & {c[0]:.2f}$\\times$ \\\\")
rows("esevenscalerows", scale)
for n, tag in ((M100, "cent"), (M400, "four")):
    b = best_sort(g, n)
    a, c = A.ratio(tot(g, n, "reference"), tot(g, n, "partitioned")), A.ratio(tot(g, n, b), tot(g, n, "partitioned"))
    macro(f"esevenrefpart{tag}", f"{a[0]:.2f}")
    macro(f"esevenrefpart{tag}ci", f"{a[1]:.2f}--{a[2]:.2f}")
    macro(f"esevensortpart{tag}", f"{c[0]:.2f}")
    macro(f"esevenparttotal{tag}", f"{A.med(tot(g, n, 'partitioned')):.1f}")
    macro(f"esevenreftotal{tag}", f"{A.med(tot(g, n, 'reference')):.1f}")
    macro(f"esevensorttotal{tag}", f"{A.med(tot(g, n, b)):.1f}")
    macro(f"esevenpartreorder{tag}", f"{A.med(tot(g, n, 'partitioned', 'reorder_ns_per_key')):.1f}")
    macro(f"esevenipsreorder{tag}", f"{A.med(tot(g, n, 'sort_ips2ra', 'reorder_ns_per_key')):.1f}")
macro("esevenrefparttenm", f"{A.ratio(tot(g, 10_000_000, 'reference'), tot(g, 10_000_000, 'partitioned'))[0]:.2f}")
macro("esevenbandpart", f"{A.med(tot(g, M100, 'partitioned', 'banding_ns_per_key')):.1f}")
macro("esevenbandsort", f"{A.med(tot(g, M100, 'sort_ips2ra', 'banding_ns_per_key')):.1f}")
macro("esevenbandref", f"{A.med(tot(g, M100, 'reference', 'banding_ns_per_key')):.1f}")
macro("esevenbandnopf", f"{A.med(tot(g, M100, 'noprefetch', 'banding_ns_per_key')):.1f}")
macro("esevenprefetchgain", f"{A.ratio(tot(g, M100, 'noprefetch', 'banding_ns_per_key'), tot(g, M100, 'reference', 'banding_ns_per_key'))[0]:.2f}")
t1 = [r["banding_ns_per_key"] for r in par[(1,)]]
macro("esevenparbandsixteen", f"{A.ratio(seq_band, [r['banding_ns_per_key'] for r in par[(16,)]])[0]:.1f}")
macro("esevenparbandeight", f"{A.ratio(seq_band, [r['banding_ns_per_key'] for r in par[(8,)]])[0]:.1f}")
macro("esevenparownsixteen", f"{A.ratio(t1, [r['banding_ns_per_key'] for r in par[(16,)]])[0]:.1f}")
macro("esevenpartotalsixteen", f"{A.med([r['total_ns_per_key'] for r in par[(16,)]]):.1f}")
macro("esevenpardeferred", f"{100 * max(A.med([r['deferred'] for r in rs]) / rs[0]['n'] for rs in par.values()):.2f}")

macro("esevenparreorder", f"{A.med([r['reorder_ns_per_key'] for r in par[(16,)]]):.1f}")
macro("esevenparbacksub", f"{A.med([r['backsubst_ns_per_key'] for r in par[(16,)]]):.1f}")
macro("esevenparoverhead", f"{(A.med(t1) / A.med(seq_band) - 1) * 100:.0f}")
for name, tag in (("arm-graviton4", "arm"), ("x86-amd", "amd")):
    if (E7 / name / "main.done").exists():
        ga = by_n_strategy(E7 / name)
        macro(f"esevenprefetchgain{tag}", f"{A.ratio(tot(ga, M100, 'noprefetch', 'banding_ns_per_key'), tot(ga, M100, 'reference', 'banding_ns_per_key'))[0]:.2f}")
        for n, nt in ((M100, "cent"), (M400, "four")):
            macro(f"esevenrefpart{tag}{nt}", f"{A.ratio(tot(ga, n, 'reference'), tot(ga, n, 'partitioned'))[0]:.2f}")
            b2 = best_sort(ga, n)
            macro(f"esevensortpart{tag}{nt}", f"{A.ratio(tot(ga, n, b2), tot(ga, n, 'partitioned'))[0]:.2f}")

# ---- counters (recovery of the best sort's reduction)
mach = json.loads((P / "machine.json").read_text())
names = {int(c, 16): n for n, c in mach["events"].items() if c}
series = {}
for r in A.load(P / "raw" / "counters"):
    if "banding_miss_per_key" in r:
        series.setdefault((r["n"], "generic"), {}).setdefault(r["strategy"], []).append(r["banding_miss_per_key"])
    for code, v in r.get("banding_raw_per_key", {}).items():
        series.setdefault((r["n"], names[int(code, 16)]), {}).setdefault(r["strategy"], []).append(v)


def recovery(n, event):
    s = series[(n, event)]
    b = min(("sort_radix", "sort_ips2ra"), key=lambda k: A.med(s[k]))
    return 100 * (A.med(s["reference"]) - A.med(s["partitioned"])) / (A.med(s["reference"]) - A.med(s[b]))


for event, tag in (("mem_load_retired.l2_miss", "ltwo"), ("mem_load_retired.l3_miss", "lthree"),
                   ("generic", "generic"), ("dtlb_load_misses.walk_completed", "tlb")):
    macro(f"esevenrec{tag}cent", f"{recovery(M100, event):.1f}")
    macro(f"esevenrec{tag}four", f"{recovery(M400, event):.1f}")
gen = {}
for r in A.load(P / "raw" / "counters"):
    if r["n"] == M100 and r["strategy"] == "reference" and "banding_cycles_per_key" in r:
        gen.setdefault("c", []).append(r["banding_cycles_per_key"])
        gen.setdefault("i", []).append(r["banding_instr_per_key"])
macro("esevenrefcycles", f"{A.med(gen['c']):.0f}")
macro("esevenrefinstr", f"{A.med(gen['i']):.1f}")
macro("esevenrefipc", f"{A.med(gen['i']) / A.med(gen['c']):.2f}")
macro("esevengenericpart", f"{A.med(series[(M100, 'generic')]['partitioned']):.2f}")
s = series[(M100, "mem_load_retired.l2_miss")]
macro("esevenltworef", f"{A.med(s['reference']):.2f}")
macro("esevengenericref", f"{A.med(series[(M100, 'generic')]['reference']):.1f}")
arm = E7 / "arm-graviton4"
if (arm / "counters.done").exists():
    aser = {}
    for r in A.load(arm / "raw" / "counters"):
        for code, v in r.get("banding_raw_per_key", {}).items():
            if int(code, 16) == 0x4009:
                aser.setdefault(r["n"], {}).setdefault(r["strategy"], []).append(v)
    for n, tag in ((M100, "cent"), (M400, "four")):
        s = aser[n]
        b = min(("sort_radix", "sort_ips2ra"), key=lambda k: A.med(s[k]))
        macro(f"esevenarmrec{tag}", f"{100 * (A.med(s['reference']) - A.med(s['partitioned'])) / (A.med(s['reference']) - A.med(s[b])):.1f}")

amd = E7 / "x86-amd"
if (amd / "counters.done").exists():
    dser = {}
    for r in A.load(amd / "raw" / "counters"):
        for code, v in r.get("banding_raw_per_key", {}).items():
            if int(code, 16) == 0x964:  # l2_cache_req_stat.ic_dc_miss_in_l2
                dser.setdefault(r["n"], {}).setdefault(r["strategy"], []).append(v)
    for n, tag in ((M100, "cent"), (M400, "four")):
        s = dser[n]
        b = min(("sort_radix", "sort_ips2ra"), key=lambda k: A.med(s[k]))
        macro(f"esevenamdrec{tag}", f"{100 * (A.med(s['reference']) - A.med(s['partitioned'])) / (A.med(s['reference']) - A.med(s[b])):.1f}")

# ---- cross-machine table (100M keys)
cross = []
for name, label in MACHINES:
    res = E7 / name
    if not (res / "main.done").exists():
        continue
    gm = by_n_strategy(res)
    b = best_sort(gm, M100)
    cross.append(f"{label} & {A.med(tot(gm, M100, 'reference')):.1f} & {A.med(tot(gm, M100, b)):.1f} & "
                 f"{A.med(tot(gm, M100, 'partitioned')):.1f} & "
                 f"{A.ratio(tot(gm, M100, 'reference'), tot(gm, M100, 'partitioned'))[0]:.2f}$\\times$ & "
                 f"{A.ratio(tot(gm, M100, b), tot(gm, M100, 'partitioned'))[0]:.2f}$\\times$ \\\\")
p1 = ROOT / "results" / "e1b" / "phase1"
lap = {s: [json.loads(f.read_text())["total_ns_per_key"] for f in sorted(p1.glob(f"{s}_{M100}_rep*.json"))]
       for s in ["reference", "partitioned", *SORTS]}
lb = min(SORTS, key=lambda s: statistics.median(lap[s]))
cross.append(f"i9-14900HX laptop (3 reps, not pinned) & {A.med(lap['reference']):.1f} & {A.med(lap[lb]):.1f} & "
             f"{A.med(lap['partitioned']):.1f} & {A.med(lap['reference']) / A.med(lap['partitioned']):.2f}$\\times$ & "
             f"{A.med(lap[lb]) / A.med(lap['partitioned']):.2f}$\\times$ \\\\")
rows("esevencrossrows", cross)

# ---- configurations
cfg = A.by(A.load(P / "raw" / "config"), "w", "r", "overhead", "strategy")
crow, cratios = [], []
for (w, r, o) in sorted({k[:3] for k in cfg}, key=lambda k: (k[0], k[1], k[2])):
    t = lambda s: [x["total_ns_per_key"] for x in cfg[(w, r, o, s)]]
    first = cfg[(w, r, o, "partitioned")][0]
    a = A.ratio(t("reference"), t("partitioned"))
    cratios.append(a[0])
    crow.append(f"{w} & {r} & {o:.3f} & {A.med([x['fpr'] for x in cfg[(w, r, o, 'partitioned')]]) * 100:.4f} & "
                f"{first['bits_per_key']:.2f} & {A.med(t('reference')):.1f} & {A.med(t('sort_ips2ra')):.1f} & "
                f"{A.med(t('partitioned')):.1f} & {a[0]:.2f}$\\times$ \\\\")
rows("esevenconfigrows", crow)
macro("esevenconfigmin", f"{min(cratios):.2f}")
macro("esevenconfigmax", f"{max(cratios):.2f}")

# ---- key sets
krows, hashed = [], []
named = []
for f in sorted((P / "raw" / "keys").glob("*_rep*.json")):
    r = json.loads(f.read_text())
    r["set"] = f.name.rsplit("_" + r["strategy"] + "_rep", 1)[0]
    named.append(r)
kg = A.by(named, "set", "strategy")
SETS = [("sosd_fb_hashed", "SOSD Facebook ids"), ("sosd_osm_hashed", "SOSD OSM cell ids"),
        ("sosd_wiki_hashed", "SOSD Wikipedia timestamps"), ("cc_hosts_hashed", "Common Crawl hosts, hashed once"),
        ("synth16_hashed", "16-byte strings, hashed once"), ("synth64_hashed", "64-byte strings, hashed once"),
        ("cc_hosts_direct", "Common Crawl hosts, string key"), ("synth16_direct", "16-byte strings, string key"),
        ("synth64_direct", "64-byte strings, string key")]
for key, label in SETS:
    t = lambda s: [x["total_ns_per_key"] for x in kg[(key, s)]]
    first = kg[(key, "partitioned")][0]
    a = A.ratio(t("reference"), t("partitioned"))
    if key.endswith("_hashed"):
        hashed.append(a[0])
    krows.append(f"{label} & {first['n'] // 1_000_000}M & {first['mean_key_bytes']:.1f} & "
                 f"{A.med([x['hash_ns_per_key'] for x in kg[(key, 'partitioned')]]):.1f} & {A.med(t('reference')):.1f} & "
                 f"{A.med(t('partitioned')):.1f} & {a[0]:.2f}$\\times$ \\\\")
    if key == "cc_hosts_hashed":
        macro("esevenkeyshosts", f"{a[0]:.2f}")
    if key.endswith("_direct"):
        macro("esevendirect" + key.split("_")[0].replace("cc", "hosts").replace("synth", "s").replace("16", "sixteen").replace("64", "sixtyfour"), f"{a[0]:.2f}")
krows.insert(6, "\\midrule")
rows("esevenkeyrows", krows)
macro("esevenkeysmin", f"{min(hashed):.2f}")
macro("esevenkeysmax", f"{max(hashed):.2f}")

# ---- huge pages
thp = []
for f in sorted((P / "raw" / "thp").glob("*_rep*.json")):
    r = json.loads(f.read_text())
    r["thp"] = f.name.split("_", 1)[0]
    thp.append(r)
tg = A.by(thp, "thp", "strategy")
tr = [A.ratio([x["total_ns_per_key"] for x in tg[(m, "reference")]],
              [x["total_ns_per_key"] for x in tg[(m, "partitioned")]])[0] for m in ("madvise", "always", "never")]
macro("eseventhpmin", f"{min(tr):.2f}")
macro("eseventhpmax", f"{max(tr):.2f}")

# ---- compaction
cg = A.by(A.load(P / "raw" / "compaction"), "sst_target_bytes", "arm")
comp = []
for sst in sorted({k[0] for k in cg}):
    cpu = lambda arm: [x["compaction_cpu_micros"] / 1e6 for x in cg[(sst, arm)]]
    a = A.ratio(cpu("pleated"), cpu("stock"))
    comp.append(f"{sst >> 20} MiB & {len(cpu('stock'))} & {mmm(cpu('stock'), 2)} & {mmm(cpu('pleated'), 2)} & "
                f"{a[0]:.3f} [{a[1]:.3f}, {a[2]:.3f}] \\\\")
    if sst == 256 << 20:
        macro("esevencompstock", f"{A.med(cpu('stock')):.2f}")
        macro("esevencomppleated", f"{A.med(cpu('pleated')):.2f}")
        macro("esevencompreduction", f"{(1 - a[0]) * 100:.0f}")
        macro("esevencompci", f"{a[1]:.3f}--{a[2]:.3f}")
        macro("esevencompreps", str(len(cpu("stock"))))
rows("esevencomprows", comp)

(ROOT / "paper" / "tables" / "e7.tex").write_text("\n".join(out) + "\n")
print("\n".join(out))
