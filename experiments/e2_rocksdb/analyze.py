#!/usr/bin/env python3
"""Derive experiments/e2_rocksdb/results/ANALYSIS.md from the committed per-repetition CSVs
(sweep_fb.csv, dbbench_reps.csv). No new measurement; this gives the E2 numbers quoted in the
README and the paper a script-derived source.
"""
import csv
import statistics
from pathlib import Path

RES = Path(__file__).resolve().parent / "results"


def msd(v):
    return statistics.mean(v), (statistics.stdev(v) if len(v) > 1 else 0.0)


def main():
    fb = {}
    for r in csv.DictReader((RES / "sweep_fb.csv").open()):
        fb.setdefault((int(r["size"]), r["mode"]), []).append(r)
    L = ["generated-by: experiments/e2_rocksdb/analyze.py over experiments/e2_rocksdb/results/"
         "{sweep_fb.csv,dbbench_reps.csv} (machine: Intel i9-14900HX per README; RocksDB v10.2.0)",
         "", "# E2 analysis (derived — do not hand-edit)", "",
         "## filter_bench sweep (means over reps)", "",
         "| keys/filter | reps | stock total ns/key | pleated total ns/key | speedup | stock banding | pleated banding | stock miss/key | pleated miss/key | FP stock == pleated |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for size in sorted({s for s, _ in fb}):
        st, pl = fb[(size, "stock")], fb[(size, "pleated")]
        def m(rows, f):
            v = [float(x[f]) for x in rows if x[f] != "NA"]  # counters unrecorded for some rows
            return statistics.mean(v) if v else float("nan")
        same_fp = {x["fp_rate"] for x in st} == {x["fp_rate"] for x in pl}
        L.append(f"| {size:,} | {len(st)}/{len(pl)} | {m(st, 'total_ns_per_key'):.2f} "
                 f"| {m(pl, 'total_ns_per_key'):.2f} | {m(st, 'total_ns_per_key') / m(pl, 'total_ns_per_key'):.2f}x "
                 f"| {m(st, 'banding_ns_per_key'):.2f} | {m(pl, 'banding_ns_per_key'):.2f} "
                 f"| {m(st, 'cache_miss_per_key'):.3f} | {m(pl, 'cache_miss_per_key'):.3f} "
                 f"| {'yes' if same_fp else 'NO'} |")

    db = {}
    for r in csv.DictReader((RES / "dbbench_reps.csv").open()):
        db.setdefault(r["mode"], []).append(r)
    L += ["", "## db_bench (mean ± sample stdev over reps)", "",
          "| mode | reps | banding ns/key | filter banding s | compaction CPU s | banding share of compaction CPU |",
          "|---|---|---|---|---|---|"]
    cpu = {}
    for mode in ("stock", "pleated"):
        rows = db[mode]
        ns = [float(x["banding_ms"]) * 1e6 / float(x["banding_keys"]) for x in rows]
        bs = [float(x["banding_ms"]) / 1e3 for x in rows]
        cs = [float(x["compaction_cpu_us"]) / 1e6 for x in rows]
        cpu[mode] = cs
        L.append(f"| {mode} | {len(rows)} | {msd(ns)[0]:.1f}±{msd(ns)[1]:.1f} | {msd(bs)[0]:.2f}±{msd(bs)[1]:.2f} "
                 f"| {msd(cs)[0]:.2f}±{msd(cs)[1]:.2f} | {statistics.mean(bs) / statistics.mean(cs):.1%} |")
    d = statistics.mean(cpu["stock"]) - statistics.mean(cpu["pleated"])
    L += ["", f"Compaction CPU difference of means: {d:.2f} s ({d / statistics.mean(cpu['stock']):.1%}); "
          f"sample stdevs are {msd(cpu['stock'])[1]:.2f} s (stock) and {msd(cpu['pleated'])[1]:.2f} s (pleated), "
          f"so with n=3 the difference is {'within' if abs(d) < msd(cpu['stock'])[1] + msd(cpu['pleated'])[1] else 'outside'} "
          "one combined stdev."]
    # ---- prefetch control and instruction counts, parsed from the recorded raw output
    import re
    raw = (RES / "filter_bench.md").read_text()

    def pair(label):
        m = re.search(rf"^{re.escape(label)}\s+([\d.]+)\s+([\d.]+)\s*$", raw, re.M)
        return float(m.group(1)), float(m.group(2))
    cfg = {k: pair(k) for k in ("stock", "no-prefetch", "pleated", "pleated+noPF")}
    slow_stock = statistics.mean(cfg["no-prefetch"]) / statistics.mean(cfg["stock"]) - 1
    slow_pleat = statistics.mean(cfg["pleated+noPF"]) / statistics.mean(cfg["pleated"]) - 1
    instr = re.search(r"stock\s*:\s*cache_misses/key=[\d., ]+instr/key=([\d.]+)\s*\n"
                      r"pleated:\s*cache_misses/key=[\d., ]+instr/key=([\d.]+)", raw)
    L += ["", "## Construction-prefetch control, 20M keys/filter (2 runs each; raw: filter_bench.md)", "",
          "| configuration | run 1 ns/key | run 2 ns/key | mean |", "|---|---|---|---|"]
    for k, v in cfg.items():
        L.append(f"| {k} | {v[0]:.2f} | {v[1]:.2f} | {statistics.mean(v):.2f} |")
    L += ["", f"Disabling the prefetch slows the stock build by {slow_stock:.1%} and the pleated build by "
          f"{slow_pleat:.1%} (two runs each; no variance estimate).",
          "", f"Banding instructions per key at 100M keys/filter (raw: filter_bench.md): stock "
          f"{instr.group(1)}, pleated {instr.group(2)}."]
    (RES / "ANALYSIS.md").write_text("\n".join(L) + "\n")
    tex = Path(__file__).resolve().parents[2] / "paper" / "tables" / "e2.tex"
    tex.write_text("% generated-by: experiments/e2_rocksdb/analyze.py — do not hand-edit\n"
                   f"\\newcommand{{\\etwonopfstock}}{{{slow_stock * 100:.0f}}}\n"
                   f"\\newcommand{{\\etwonopfpleated}}{{{slow_pleat * 100:.0f}}}\n"
                   f"\\newcommand{{\\etwoinstr}}{{{float(instr.group(1)):.0f}}}\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
