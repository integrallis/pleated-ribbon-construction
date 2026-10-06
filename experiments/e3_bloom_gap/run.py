#!/usr/bin/env python3
"""E3 Stage A runner: RocksDB filter_bench, FastLocalBloom vs Standard128 ribbon (stock, pleated).

Runs on the benchmark box, against a RocksDB checkout already patched and built as in E2.
Stages refuse to run before their prerequisite artifact exists:

  check    build gates + machine identity      -> results/e3/check.json, machine.json
  bench    the registered sweep                -> results/e3/raw/*.txt, sweep_fb.csv
  analyze  derive ANALYSIS.md from the CSV     -> results/e3/ANALYSIS.md (via analyze.py)

Usage: run.py --stage {check,bench,analyze} --rocksdb /path/to/rocksdb
The protocol (sizes, arms, reps, flags) is fixed in README.md; do not change it here after freeze.
"""
import argparse
import csv
import datetime
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = Path(os.environ.get("E3_RES", ROOT / "results" / "e3"))
PATCH = ROOT / "experiments" / "e2_rocksdb" / "pleat-rocksdb.patch"

ROCKSDB_COMMIT = "31b239747"
SIZES = [100_000, 1_000_000, 10_000_000, 100_000_000]
REPS = 3
# arm -> (filter_bench -impl value, extra environment)
ARMS = {
    "bloom": (1, {}),                       # format_version 5 Bloom (FastLocalBloom)
    "stock": (2, {}),                       # Ribbon128, as shipped
    "pleated": (2, {"PLEAT_RIBBON": "1"}),  # Ribbon128 + pleat pass (E2 patch)
}
IMPL_HELP = "1 = format_version 5 Bloom filter, 2 = Ribbon128 filter"
MARKER = b"PLEAT_PROFILE banding"

FIELDS = {
    "build_ns_per_key": re.compile(r"Build avg ns/key:\s*([\d.eE+-]+)"),
    "n_filters": re.compile(r"Number of filters:\s*(\d+)"),
    "total_size_mb": re.compile(r"Total size \(MB\):\s*([\d.eE+-]+)"),
    "bits_per_key": re.compile(r"Bits/key stored:\s*([\d.eE+-]+)"),
    "fp_rate_pct": re.compile(r"Average FP rate %:\s*([\d.eE+-]+)"),
}


def parse(text):
    out = {}
    for name, rx in FIELDS.items():
        m = rx.search(text)
        if not m:
            raise ValueError(f"filter_bench output has no '{name}' line")
        out[name] = float(m.group(1))
    return out


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout.strip()


def stage_check(rocksdb):
    problems = []
    head = sh(["git", "rev-parse", "HEAD"], cwd=rocksdb)
    if not head.startswith(ROCKSDB_COMMIT):
        problems.append(f"RocksDB HEAD is {head[:12]}, protocol pins {ROCKSDB_COMMIT}")
    # the patch is applied iff it reverse-applies cleanly
    if subprocess.run(["git", "apply", "--reverse", "--check", str(PATCH)], cwd=rocksdb,
                      capture_output=True).returncode != 0:
        problems.append("pleat-rocksdb.patch is not applied to this checkout")
    binary = rocksdb / "filter_bench"
    obj = rocksdb / "table" / "block_based" / "filter_policy.o"
    src = rocksdb / "table" / "block_based" / "filter_policy.cc"
    if not binary.exists():
        problems.append("filter_bench binary missing")
    else:
        if MARKER not in binary.read_bytes():
            problems.append("pleat marker string not found in filter_bench (stale binary?)")
        if not obj.exists() or obj.stat().st_mtime < src.stat().st_mtime:
            problems.append("filter_policy.o is missing or older than filter_policy.cc")
        elif binary.stat().st_mtime < obj.stat().st_mtime:
            problems.append("filter_bench is older than filter_policy.o")
        helptext = subprocess.run([str(binary), "-help"], capture_output=True, text=True)
        if IMPL_HELP not in " ".join((helptext.stdout + helptext.stderr).split()):
            problems.append("filter_bench -impl help text does not match the registered meaning")

    def opt(cmd):
        try:
            return sh(cmd)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    cpu = None
    for line in Path("/proc/cpuinfo").read_text().splitlines() if Path("/proc/cpuinfo").exists() else []:
        if line.lower().startswith(("model name", "cpu part")):
            cpu = line.split(":", 1)[1].strip()
            break
    machine = {
        "cpu": cpu,
        "arch": platform.machine(),
        "nproc": os.cpu_count(),
        "mem_total_kb": opt(["awk", "/MemTotal/ {print $2}", "/proc/meminfo"]),
        "kernel": platform.release(),
        "virt": opt(["systemd-detect-virt"]),
        "compiler": (opt(["c++", "--version"]) or "").splitlines()[:1],
        "rocksdb_commit": head,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "machine.json").write_text(json.dumps(machine, indent=2) + "\n")
    (RES / "check.json").write_text(json.dumps(
        {"ok": not problems, "problems": problems, "arms": {a: {"impl": i, "env": e}
                                                            for a, (i, e) in ARMS.items()},
         "sizes": SIZES, "reps": REPS}, indent=2) + "\n")
    for p in problems:
        print("CHECK FAILED:", p)
    if problems:
        sys.exit(1)
    print("check passed;", machine["cpu"], machine["arch"], "virt:", machine["virt"])


def stage_bench(rocksdb):
    chk = RES / "check.json"
    if not chk.exists() or not json.loads(chk.read_text())["ok"]:
        sys.exit("refusing to bench: run --stage check first (and it must pass)")
    out_csv = RES / "sweep_fb.csv"
    if out_csv.exists():
        sys.exit(f"refusing to overwrite {out_csv}; a sweep was already recorded")
    raw = RES / "raw"
    raw.mkdir(exist_ok=True)
    rows = []
    for rep in range(1, REPS + 1):
        for size in SIZES:
            max_m = max(40, size // 1_000_000 * 3)  # same rule as E2
            for arm, (impl, env) in ARMS.items():  # arms interleaved within each (rep, size)
                cmd = [str(rocksdb / "filter_bench"), "-impl", str(impl),
                       "-m_keys_total_max", str(max_m),
                       "-average_keys_per_filter", str(size),
                       "-net_includes_hashing", "-quick"]
                run_env = {k: v for k, v in os.environ.items() if not k.startswith("PLEAT_")}
                run_env.update(env)
                p = subprocess.run(cmd, capture_output=True, text=True, env=run_env)
                (raw / f"{size}_{arm}_rep{rep}.txt").write_text(
                    "$ " + " ".join(f"{k}={v}" for k, v in env.items()) + " " + " ".join(cmd)
                    + "\n" + p.stdout + ("\n[stderr]\n" + p.stderr if p.stderr else ""))
                if p.returncode != 0:
                    sys.exit(f"filter_bench failed ({arm}, {size}, rep {rep}): exit {p.returncode}; "
                             f"see {raw}/{size}_{arm}_rep{rep}.txt. No CSV written.")
                d = parse(p.stdout)
                rows.append({"size": size, "arm": arm, "rep": rep, **d})
                print(f"rep{rep} {size:>11,} {arm:<8} {d['build_ns_per_key']:8.2f} ns/key  "
                      f"FP {d['fp_rate_pct']:.4f}%  {d['bits_per_key']:.2f} bits/key", flush=True)
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote", out_csv)


def stage_analyze():
    if not (RES / "sweep_fb.csv").exists():
        sys.exit("refusing to analyze: results/e3/sweep_fb.csv missing — run --stage bench first")
    subprocess.run([sys.executable, str(Path(__file__).with_name("analyze.py"))], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["check", "bench", "analyze"])
    ap.add_argument("--rocksdb", type=Path)
    a = ap.parse_args()
    if a.stage == "analyze":
        return stage_analyze()
    if not a.rocksdb:
        sys.exit("--rocksdb is required for check and bench")
    (stage_check if a.stage == "check" else stage_bench)(a.rocksdb.resolve())


if __name__ == "__main__":
    main()
