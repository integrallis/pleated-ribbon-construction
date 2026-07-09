#!/usr/bin/env python3
"""Staged runner for E0 (see README.md). Stages: check | fpr | bench | asm | anchor | analyze.

Every stage records raw artifacts under results/e0a/; analyze derives ANALYSIS.md from
artifacts only (no benchmark execution inside analyze).
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
RES = ROOT / "results" / "e0a"
CRATE = ROOT / "src" / "lanefilter"
ENV = {**os.environ, "RUSTFLAGS": "-C target-cpu=native"}


def sh(cmd, **kw):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=True, **kw)


def machine_info() -> dict:
    cpu = ""
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.startswith("model name"):
            cpu = line.split(":", 1)[1].strip()
            break
    return {
        "cpu": cpu,
        "kernel": platform.release(),
        "rustc": subprocess.run(["rustc", "--version"], capture_output=True, text=True).stdout.strip(),
        "rustflags": ENV["RUSTFLAGS"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def stage_check():
    sh(["cargo", "test", "--release", "-p", "lanefilter"], cwd=ROOT, env=ENV)


def stage_fpr():
    RES.mkdir(parents=True, exist_ok=True)
    out = subprocess.run(
        ["cargo", "run", "--release", "-p", "lanefilter", "--bin", "e0_fpr", "--", "1000000"],
        cwd=ROOT, env=ENV, capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    data["machine"] = machine_info()
    (RES / "summary.json").write_text(json.dumps(data, indent=2))
    print(f"wrote {RES / 'summary.json'}")
    sh([sys.executable, str(ROOT / "scripts" / "check_integrity.py")])


def stage_bench():
    if not (RES / "summary.json").exists():
        sys.exit("prerequisite missing: run --stage fpr first (FPR gate before timing)")
    sh(["cargo", "bench", "-p", "lanefilter", "--bench", "e0"], cwd=ROOT, env=ENV)
    dst = RES / "criterion"
    if dst.exists():
        shutil.rmtree(dst)
    src = ROOT / "target" / "criterion"
    # Copy only the raw estimates/samples, not the HTML reports.
    for est in src.rglob("new/*.json"):
        rel = est.relative_to(src)
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(est, dst / rel)
    (RES / "bench_machine.json").write_text(json.dumps(machine_info(), indent=2))
    print(f"copied criterion raw JSON -> {dst}")


def stage_asm():
    sh(["cargo", "bench", "-p", "lanefilter", "--bench", "e0", "--no-run"], cwd=ROOT, env=ENV)
    # Find the bench executable.
    meta = subprocess.run(
        ["cargo", "bench", "-p", "lanefilter", "--bench", "e0", "--no-run", "--message-format=json"],
        cwd=ROOT, env=ENV, capture_output=True, text=True, check=True,
    ).stdout
    exe = None
    for line in meta.splitlines():
        try:
            j = json.loads(line)
        except json.JSONDecodeError:
            continue
        if j.get("target", {}).get("name") == "e0" and j.get("executable"):
            exe = j["executable"]
    if not exe:
        sys.exit("could not locate bench executable")
    asm_dir = RES / "asm"
    asm_dir.mkdir(parents=True, exist_ok=True)
    dis = subprocess.run(["objdump", "-d", "--demangle", exe], capture_output=True, text=True, check=True).stdout
    # Extract the lanes kernel's disassembly.
    lines = dis.splitlines()
    kept, capturing = [], False
    for line in lines:
        if "check_batch_lanes_masked" in line and line.endswith(">:"):
            capturing = True
        elif capturing and line.endswith(">:"):
            capturing = False
        if capturing:
            kept.append(line)
    (asm_dir / "check_batch_lanes_masked.s").write_text("\n".join(kept) or dis)
    if platform.machine() in ("aarch64", "arm64"):
        # NEON/SVE: vector registers v0-v31 / z0-z31, structure loads, table ops.
        ops = ("ld1", "st1", "tbl", "cmeq", "mul v", "and v", "ushr v", "shl v",
               " z0", " z1", " z2", " z3", ".4s", ".2d", ".16b")
    else:
        ops = ("vpgather", "vpand", "vpsllvd", "vpmulld", "vpcmpeqd", "ymm", "zmm")
    packed = [l for l in kept if any(op in l for op in ops)]
    (asm_dir / "packed_instructions.txt").write_text("\n".join(packed))
    print(f"kernel disassembly: {len(kept)} lines, packed-SIMD lines: {len(packed)}")
    print(f"wrote {asm_dir}/check_batch_lanes_masked.s and packed_instructions.txt")


def stage_anchor():
    exe = ROOT / "harness" / "fastfilter_cpp" / "benchmarks" / "bulk-insert-and-query.exe"
    if not exe.exists():
        sys.exit("prerequisite missing: build harness/fastfilter_cpp first")
    anchor_dir = RES / "anchor"
    anchor_dir.mkdir(parents=True, exist_ok=True)
    # BlockedBloom (id 51) at sizes bracketing our sweep; seed fixed by the harness itself.
    for n in (1_000_000, 10_000_000, 100_000_000):
        out = subprocess.run([str(exe), str(n), "51"], capture_output=True, text=True, check=True).stdout
        (anchor_dir / f"blockedbloom_{n}.txt").write_text(out)
        print(out.strip().splitlines()[-1])
    (anchor_dir / "machine.json").write_text(json.dumps(machine_info(), indent=2))


def stage_analyze():
    import analyze  # local module

    analyze.main()


STAGES = {
    "check": stage_check,
    "fpr": stage_fpr,
    "bench": stage_bench,
    "asm": stage_asm,
    "anchor": stage_anchor,
    "analyze": stage_analyze,
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=STAGES)
    args = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).parent))
    STAGES[args.stage]()
