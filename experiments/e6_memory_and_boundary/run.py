#!/usr/bin/env python3
"""Staged runner for E6 (frozen protocol, see README.md).
Stages: check | spill | memory | concurrent | analyze. Runs on the benchmark box.
"""
import argparse
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "e6"
DRIVER = ROOT / "src" / "ribbon_reorder" / "e1b_phase1"
E3_RUN = ROOT / "experiments" / "e3_bloom_gap" / "run.py"

N = 100_000_000
SHIFT = 16
REPS = 3
MARGINS = [16384, 1024, 64, 8, 0]
SPILL_THREADS = [2, 16]
MEM_STRATEGIES = [("reference", None), ("sort_radix", None), ("sort_ips2ra", None),
                  ("partitioned", None), ("parallel", 16)]
CONCURRENCY = [1, 4, 8]
CONC_STRATEGIES = ["reference", "partitioned"]
RSS_RE = re.compile(r"Maximum resident set size \(kbytes\):\s*(\d+)")


def need(path, what):
    if not path.exists():
        sys.exit(f"prerequisite missing: {what}")


def fresh(d):
    if d.exists():
        sys.exit(f"refusing to overwrite {d}")
    d.mkdir(parents=True)
    return d


def driver_cmd(strategy, rep, threads=None):
    return [str(DRIVER), str(N), strategy, str(rep), str(SHIFT)] + ([str(threads)] if threads else [])


def run_json(cmd, env=None):
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if p.returncode != 0:
        sys.exit(f"failed ({p.returncode}): {' '.join(cmd)}\n{p.stderr[-400:]}")
    return json.loads(p.stdout), p


def stage_check(rocksdb):
    if os.cpu_count() < 16:
        sys.exit(f"this machine has {os.cpu_count()} CPUs; the protocol needs 16")
    need(DRIVER, "make -C src/ribbon_reorder")
    need(Path("/usr/bin/time"), "GNU time (apt-get install time)")
    smoke, _ = run_json([str(DRIVER), "1000000", "parallel", "0", str(SHIFT), "2"],
                        {**os.environ, "PLEAT_PARALLEL_G": "0"})
    if smoke["false_negatives"] != 0 or "spilled" not in smoke:
        sys.exit("driver smoke run failed or does not report 'spilled'")
    RES.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "E3_RES": str(RES / "rocksdb_check")}
    if subprocess.run([sys.executable, str(E3_RUN), "--stage", "check", "--rocksdb", str(rocksdb)],
                      env=env).returncode != 0:
        sys.exit("RocksDB build gates failed")
    cpu = next((l.split(":", 1)[1].strip() for l in Path("/proc/cpuinfo").read_text().splitlines()
                if l.startswith("model name")), "")
    lscpu = subprocess.run(["lscpu"], capture_output=True, text=True).stdout
    topo = {k.strip(): v.strip() for k, _, v in (l.partition(":") for l in lscpu.splitlines())
            if k.strip() in ("CPU(s)", "Thread(s) per core", "Core(s) per socket", "L2 cache", "L3 cache")}
    (RES / "machine.json").write_text(json.dumps({
        "cpu": cpu, "arch": platform.machine(), "kernel": platform.release(),
        "nproc": os.cpu_count(), "lscpu": topo,
        "mem_total_kb": next(l.split()[1] for l in Path("/proc/meminfo").read_text().splitlines()
                             if l.startswith("MemTotal")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
    (RES / "check.json").write_text(json.dumps(
        {"ok": True, "n": N, "margins": MARGINS, "spill_threads": SPILL_THREADS, "reps": REPS,
         "concurrency": CONCURRENCY, "rocksdb": str(rocksdb)}, indent=2) + "\n")
    print("check passed")


def stage_spill(_):
    need(RES / "check.json", "run --stage check first")
    d = fresh(RES / "spill")
    for rep in range(REPS):
        rec, p = run_json(driver_cmd("partitioned", rep))
        (d / f"sequential_rep{rep}.json").write_text(p.stdout)
        for t in SPILL_THREADS:
            for g in MARGINS:
                rec, p = run_json(driver_cmd("parallel", rep, t), {**os.environ, "PLEAT_PARALLEL_G": str(g)})
                rec["margin"] = g
                (d / f"parallel_t{t}_g{g}_rep{rep}.json").write_text(json.dumps(rec) + "\n")
                print(f"rep{rep} T={t} G={g}: spilled={rec['spilled']} deferred={rec['deferred']} "
                      f"fn={rec['false_negatives']} fnv={rec['soln_fnv']}", flush=True)


def timed(cmd, env=None):
    p = subprocess.run(["/usr/bin/time", "-v", *cmd], capture_output=True, text=True, env=env)
    m = RSS_RE.search(p.stderr)
    if p.returncode != 0 or not m:
        sys.exit(f"failed ({p.returncode}): {' '.join(cmd)}\n{p.stderr[-400:]}")
    return p, int(m.group(1))


def stage_memory(rocksdb):
    need(RES / "check.json", "run --stage check first")
    d = fresh(RES / "memory")
    for rep in range(REPS):
        for strat, t in MEM_STRATEGIES:
            p, rss = timed(driver_cmd(strat, rep, t))
            rec = json.loads(p.stdout)
            rec["peak_rss_kb"] = rss
            (d / f"{strat}_rep{rep}.json").write_text(json.dumps(rec) + "\n")
            print(f"rep{rep} {strat:<12} peak RSS {rss / 1024:.0f} MB", flush=True)
    fb = [str(Path(rocksdb) / "filter_bench"), "-impl", "2", "-m_keys_total_max", "300",
          "-average_keys_per_filter", str(N), "-net_includes_hashing", "-quick"]
    for rep in range(REPS):
        for arm, extra in (("stock", {}), ("pleated", {"PLEAT_RIBBON": "1"})):
            env = {k: v for k, v in os.environ.items() if not k.startswith("PLEAT_")}
            env.update(extra)
            p, rss = timed(fb, env)
            (d / f"fb_{arm}_rep{rep}.txt").write_text(p.stdout + f"\nPEAK_RSS_KB {rss}\n")
            print(f"rep{rep} filter_bench {arm:<8} peak RSS {rss / 1024:.0f} MB", flush=True)


def stage_concurrent(_):
    need(RES / "check.json", "run --stage check first")
    d = fresh(RES / "concurrent")
    for rep in range(REPS):
        for k in CONCURRENCY:
            for strat in CONC_STRATEGIES:
                procs = [subprocess.Popen(["taskset", "-c", str(c), *driver_cmd(strat, rep)],
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                         for c in range(k)]
                outs = [p.communicate() for p in procs]
                if any(p.returncode != 0 for p in procs):
                    sys.exit(f"a concurrent run failed (K={k}, {strat}, rep {rep})")
                recs = [json.loads(o[0]) for o in outs]
                (d / f"k{k}_{strat}_rep{rep}.json").write_text(json.dumps(
                    {"k": k, "strategy": strat, "rep": rep, "runs": recs}) + "\n")
                tot = [r["total_ns_per_key"] for r in recs]
                print(f"rep{rep} K={k} {strat:<12} total ns/key per process: "
                      f"min {min(tot):.1f} max {max(tot):.1f}", flush=True)


def stage_analyze(_):
    need(RES / "concurrent", "run the measurement stages first")
    subprocess.run([sys.executable, str(Path(__file__).with_name("analyze.py"))], check=True)


STAGES = {"check": stage_check, "spill": stage_spill, "memory": stage_memory,
          "concurrent": stage_concurrent, "analyze": stage_analyze}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=STAGES)
    ap.add_argument("--rocksdb", type=Path)
    a = ap.parse_args()
    if a.stage in ("check", "memory") and not a.rocksdb:
        sys.exit("--rocksdb is required for check and memory")
    STAGES[a.stage](a.rocksdb.resolve() if a.rocksdb else None)
