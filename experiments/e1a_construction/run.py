#!/usr/bin/env python3
"""Staged runner for E1a (frozen protocol, see README.md).
Stages: check | pilot | bench | perf | anchor | analyze.
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
RES = ROOT / "results" / "e1a"
ENV = {**os.environ, "RUSTFLAGS": "-C target-cpu=native"}


def sh(cmd, **kw):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=True, **kw)


def machine_info() -> dict:
    cpu = ""
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.startswith(("model name", "Model name")):
            cpu = line.split(":", 1)[1].strip()
            break
    return {
        "cpu": cpu,
        "arch": platform.machine(),
        "kernel": platform.release(),
        "rustc": subprocess.run(["rustc", "--version"], capture_output=True, text=True).stdout.strip(),
        "rustflags": ENV["RUSTFLAGS"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def copy_criterion(dst: Path):
    src = ROOT / "target" / "criterion"
    if dst.exists():
        shutil.rmtree(dst)
    for est in src.rglob("new/*.json"):
        rel = est.relative_to(src)
        if not rel.parts[0].startswith("construct"):
            continue
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(est, dst / rel)


def stage_check():
    sh(["cargo", "test", "--release", "-p", "lanefilter"], cwd=ROOT, env=ENV)


def stage_pilot():
    sh(["cargo", "bench", "-p", "lanefilter", "--bench", "e1a"], cwd=ROOT, env=ENV)
    copy_criterion(RES / "pilot")
    (RES / "pilot_machine.json").write_text(json.dumps(machine_info(), indent=2))
    print(f"pilot artifacts -> {RES / 'pilot'}")


def stage_bench():
    if not (RES / "pilot").exists():
        sys.exit("prerequisite missing: run --stage pilot first")
    env = {**ENV, "E1A_SIZES": "full"}
    sh(["cargo", "bench", "-p", "lanefilter", "--bench", "e1a"], cwd=ROOT, env=env)
    copy_criterion(RES / "criterion")
    (RES / "bench_machine.json").write_text(json.dumps(machine_info(), indent=2))
    print(f"full-sweep artifacts -> {RES / 'criterion'}")


def stage_perf():
    print("perf stage: optional; not implemented on this box (perf_event_paranoid). "
          "fastfilter anchor provides counter context.")


def stage_anchor():
    exe = ROOT / "harness" / "fastfilter_cpp" / "benchmarks" / "bulk-insert-and-query.exe"
    if not exe.exists():
        sys.exit("prerequisite missing: build harness/fastfilter_cpp first")
    anchor_dir = RES / "anchor"
    anchor_dir.mkdir(parents=True, exist_ok=True)
    # 43 = Bloom8-addAll, 51 = BlockedBloom (per-key add), 52 = BlockedBloom-addAll
    for n in (1_000_000, 10_000_000, 100_000_000):
        out = subprocess.run([str(exe), str(n), "43,51,52"], capture_output=True, text=True, check=True).stdout
        (anchor_dir / f"construction_{n}.txt").write_text(out)
        print(f"n={n}: " + " | ".join(l.strip() for l in out.splitlines() if l.strip().startswith(("Bloom8", "BlockedBloom"))))
    (anchor_dir / "machine.json").write_text(json.dumps(machine_info(), indent=2))


def stage_analyze():
    import analyze

    analyze.main()


STAGES = {
    "check": stage_check,
    "pilot": stage_pilot,
    "bench": stage_bench,
    "perf": stage_perf,
    "anchor": stage_anchor,
    "analyze": stage_analyze,
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=STAGES)
    args = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).parent))
    STAGES[args.stage]()
