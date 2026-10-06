#!/usr/bin/env python3
"""Staged runner for E4 (frozen protocol, see README.md).
Stages: check | fpr | anchor | bloom | ribbon | analyze. Runs on the benchmark box.
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "e4"
ENV = {**os.environ, "RUSTFLAGS": "-C target-cpu=native"}
EXE = ROOT / "harness" / "fastfilter_cpp" / "benchmarks" / "bulk-insert-and-query.exe"
DRIVER = ROOT / "src" / "ribbon_reorder" / "e1b_phase1"

N = 100_000_000
THREADS = [1, 2, 4, 8, 16]
REPS = 3
WINDOW_SHIFT = 16
SEED = 46  # as E1b Phase 0


def sh(cmd, **kw):
    print(f"$ {' '.join(str(c) for c in cmd)}", flush=True)
    return subprocess.run(cmd, check=True, **kw)


def out(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def need(path, what):
    if not path.exists():
        sys.exit(f"prerequisite missing: {what} ({path.relative_to(ROOT)})")


def machine_info() -> dict:
    cpu = ""
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.startswith(("model name", "Model name")):
            cpu = line.split(":", 1)[1].strip()
            break
    lscpu = {}
    for line in (out(["lscpu"]) or "").splitlines():
        k, _, v = line.partition(":")
        if k.strip() in ("CPU(s)", "Thread(s) per core", "Core(s) per socket", "Socket(s)",
                         "L1d cache", "L2 cache", "L3 cache", "Hypervisor vendor"):
            lscpu[k.strip()] = v.strip()
    return {
        "cpu": cpu,
        "arch": platform.machine(),
        "kernel": platform.release(),
        "nproc": os.cpu_count(),
        "lscpu": lscpu,
        "virt": out(["systemd-detect-virt"]),
        "rustc": out(["rustc", "--version"]),
        "rustflags": ENV["RUSTFLAGS"],
        "cxx": (out(["g++", "--version"]) or "").splitlines()[:1],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def stage_check():
    if os.cpu_count() < max(THREADS):
        sys.exit(f"this machine has {os.cpu_count()} CPUs; the protocol needs {max(THREADS)}")
    sh(["cargo", "test", "--release", "-p", "lanefilter"], cwd=ROOT, env=ENV)
    need(EXE, "build harness/fastfilter_cpp first")
    need(DRIVER, "make -C src/ribbon_reorder")
    smoke = json.loads(out([str(DRIVER), "1000000", "parallel", "0", str(WINDOW_SHIFT), "2"]))
    if smoke["false_negatives"] != 0:
        sys.exit("driver smoke run reported false negatives")
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "machine.json").write_text(json.dumps(machine_info(), indent=2) + "\n")
    (RES / "check.json").write_text(json.dumps(
        {"ok": True, "n": N, "threads": THREADS, "reps": REPS, "window_shift": WINDOW_SHIFT},
        indent=2) + "\n")
    print("check passed")


def stage_fpr():
    need(RES / "check.json", "run --stage check first")
    r = sh(["cargo", "run", "--release", "-p", "lanefilter", "--bin", "e0_fpr", "--", str(N)],
           cwd=ROOT, env=ENV, capture_output=True, text=True)
    json.loads(r.stdout)  # must be valid JSON before it is recorded
    (RES / "fpr_100M.json").write_text(r.stdout)
    print(r.stdout)


def stage_anchor():
    need(RES / "check.json", "run --stage check first")
    d = RES / "anchor"
    d.mkdir(exist_ok=True)
    for rep in range(REPS):
        p = d / f"BlockedBloom_{N}_rep{rep}.txt"
        if p.exists():
            sys.exit(f"refusing to overwrite {p}")
        r = sh([str(EXE), str(N), "51", str(SEED + rep)], capture_output=True, text=True)
        p.write_text(r.stdout)
        print([l.strip() for l in r.stdout.splitlines() if "BlockedBloom" in l][-1])


def stage_bloom():
    need(RES / "check.json", "run --stage check first")
    dst = RES / "criterion"
    if dst.exists():
        sys.exit(f"refusing to overwrite {dst}")
    src = ROOT / "target" / "criterion"
    for stale in src.glob("e4_construct*"):
        shutil.rmtree(stale)
    env = {**ENV, "E4_SIZES": "full", "E4_THREADS": ",".join(map(str, THREADS))}
    r = sh(["cargo", "bench", "-p", "lanefilter", "--bench", "e4"], cwd=ROOT, env=env,
           capture_output=True, text=True)
    (RES / "criterion_stdout.txt").write_text(r.stdout)
    if "E4 gate: all parallel builders bit-identical" not in r.stdout:
        sys.exit("bit-identity gate line missing from bench output; nothing recorded")
    for est in src.rglob("new/*.json"):
        rel = est.relative_to(src)
        if rel.parts[0].startswith("e4_construct"):
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(est, dst / rel)
    print(f"criterion artifacts -> {dst}")


def stage_ribbon():
    need(RES / "check.json", "run --stage check first")
    d = RES / "ribbon"
    if d.exists():
        sys.exit(f"refusing to overwrite {d}")
    d.mkdir()
    for rep in range(REPS):
        runs = [("partitioned", None)] + [("parallel", t) for t in THREADS]
        for strat, t in runs:
            cmd = [str(DRIVER), str(N), strat, str(rep), str(WINDOW_SHIFT)] + ([str(t)] if t else [])
            r = sh(cmd, capture_output=True, text=True)
            rec = json.loads(r.stdout)
            name = f"parallel_t{t}_rep{rep}.json" if t else f"partitioned_rep{rep}.json"
            (d / name).write_text(r.stdout)
            print(f"  {name}: total {rec['total_ns_per_key']} ns/key", flush=True)


def stage_analyze():
    need(RES / "ribbon", "run --stage ribbon first")
    need(RES / "criterion", "run --stage bloom first")
    # run as a script: analyze.py imports E1b's `analyze` module for the fastfilter parser
    sh([sys.executable, str(Path(__file__).with_name("analyze.py"))])


STAGES = {"check": stage_check, "fpr": stage_fpr, "anchor": stage_anchor, "bloom": stage_bloom,
          "ribbon": stage_ribbon, "analyze": stage_analyze}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=STAGES)
    args = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).parent))
    STAGES[args.stage]()
