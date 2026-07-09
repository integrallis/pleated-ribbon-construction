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


def stage_analyze():
    import analyze

    analyze.main()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["phase0", "analyze"])
    args = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).parent))
    if args.stage == "phase0":
        stage_phase0()
    else:
        stage_analyze()
