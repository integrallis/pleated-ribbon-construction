#!/usr/bin/env python3
"""E1b Phase-0 staged runner (frozen protocol, see README.md). Stages: phase0 | analyze.

phase0 runs the pinned fastfilter_cpp binary one (algorithm, size, rep) at a time and stores
each raw output; no new benchmark code — the reference harness is the instrument.
"""
import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "e1b" / "phase0"
EXE = ROOT / "harness" / "fastfilter_cpp" / "benchmarks" / "bulk-insert-and-query.exe"

ALGOS = {
    1076: "HomogRibbon64_7",
    2076: "BalancedRibbon64Pack_7",
    116: "XorBinaryFuse8",
    118: "XorBinaryFuse8_4wise",
    0: "Xor8",
    51: "BlockedBloom",
    44: "Bloom12_addAll",
}
SIZES = [1_000_000, 10_000_000, 100_000_000]
REPS = 3
SEED = 46  # harness default seed convention; fixed for reproducibility


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
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def stage_phase0():
    if not EXE.exists():
        sys.exit("prerequisite missing: build harness/fastfilter_cpp first")
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "machine.json").write_text(json.dumps(machine_info(), indent=2))
    for n in SIZES:
        for aid, name in ALGOS.items():
            for rep in range(REPS):
                out_path = RES / f"{name}_{n}_rep{rep}.txt"
                if out_path.exists():
                    print(f"skip (exists): {out_path.name}")
                    continue
                r = subprocess.run(
                    [str(EXE), str(n), str(aid), str(SEED + rep)],
                    capture_output=True, text=True, check=True,
                )
                out_path.write_text(r.stdout)
                summary = [l for l in r.stdout.splitlines() if name.split("_")[0] in l and "cycles" not in l]
                print(f"{name} n={n} rep={rep}: {summary[-1].strip() if summary else 'written'}")
    print(f"phase0 artifacts -> {RES}")


RES1 = ROOT / "results" / "e1b" / "phase1"
DRIVER = ROOT / "src" / "ribbon_reorder" / "e1b_phase1"
P1_STRATEGIES = ["reference", "noprefetch", "sort_std", "sort_radix", "partitioned"]
P1_SIZES = [10_000_000, 100_000_000, 400_000_000]
P1_REPS = 3


def stage_phase1():
    if not DRIVER.exists():
        sys.exit("prerequisite missing: make -C src/ribbon_reorder")
    if not (ROOT / "results" / "e1b" / "ANALYSIS.md").exists():
        sys.exit("prerequisite missing: phase-0 analysis (gate decision) must exist")
    RES1.mkdir(parents=True, exist_ok=True)
    (RES1 / "machine.json").write_text(json.dumps(machine_info(), indent=2))
    for n in P1_SIZES:
        for strat in P1_STRATEGIES:
            for rep in range(P1_REPS):
                out_path = RES1 / f"{strat}_{n}_rep{rep}.json"
                if out_path.exists():
                    print(f"skip (exists): {out_path.name}")
                    continue
                r = subprocess.run(
                    [str(DRIVER), str(n), strat, str(rep)],
                    capture_output=True, text=True,
                )
                if r.returncode != 0:
                    print(f"FAILED {strat} n={n} rep={rep}: {r.stderr.strip()[:200]}")
                    sys.exit(1)
                out_path.write_text(r.stdout)
                print(r.stdout.strip())
    print(f"phase1 artifacts -> {RES1}")


def stage_analyze1():
    import analyze_phase1

    analyze_phase1.main()


def stage_analyze():
    import analyze

    analyze.main()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                    choices=["phase0", "analyze", "phase1", "analyze1"])
    args = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).parent))
    {"phase0": stage_phase0, "analyze": stage_analyze,
     "phase1": stage_phase1, "analyze1": stage_analyze1}[args.stage]()
