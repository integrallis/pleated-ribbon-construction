#!/usr/bin/env python3
"""E5 runner: byte-level comparison of stock and pleated Standard128 ribbon filters built by
RocksDB filter_bench. Stages: check | run | analyze (see README.md; frozen protocol).
"""
import argparse
import datetime
import filecmp
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "e5"
PATCHES = [ROOT / "experiments" / "e2_rocksdb" / "pleat-rocksdb.patch",
           Path(__file__).with_name("dump-filters.patch")]
ROCKSDB_COMMIT = "31b239747"
SIZES = [100_000, 1_000_000, 10_000_000, 100_000_000]
RUNS = {"stock_a": {}, "stock_b": {}, "pleated": {"PLEAT_RIBBON": "1"}}
PAIRS = [("stock_a", "stock_b"), ("stock_a", "pleated")]
MARKERS = [b"PLEAT_PROFILE banding", b"PLEAT_DUMP_DIR write failed"]


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw).stdout.strip()


def stage_check(rocksdb):
    problems = []
    head = sh(["git", "rev-parse", "HEAD"], cwd=rocksdb)
    if not head.startswith(ROCKSDB_COMMIT):
        problems.append(f"RocksDB HEAD is {head[:12]}, protocol pins {ROCKSDB_COMMIT}")
    # both patches applied iff, taken in reverse order, they reverse-apply cleanly
    probe = Path(tempfile.mkdtemp())
    try:
        sh(["git", "worktree", "add", "--detach", str(probe), "HEAD"], cwd=rocksdb)
        for p in PATCHES:
            if subprocess.run(["git", "apply", str(p)], cwd=probe, capture_output=True).returncode:
                problems.append(f"{p.name} does not apply to the pinned commit in order")
        for rel in ("table/block_based/filter_policy.cc", "util/ribbon_impl.h"):
            if (probe / rel).read_bytes() != (rocksdb / rel).read_bytes():
                problems.append(f"{rel} in the checkout is not pin + both patches")
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(probe)], cwd=rocksdb,
                       capture_output=True)
    binary = rocksdb / "filter_bench"
    obj = rocksdb / "table" / "block_based" / "filter_policy.o"
    src = rocksdb / "table" / "block_based" / "filter_policy.cc"
    if not binary.exists():
        problems.append("filter_bench binary missing")
    else:
        blob = binary.read_bytes()
        for m in MARKERS:
            if m not in blob:
                problems.append(f"marker {m!r} not in filter_bench (stale binary?)")
        if not obj.exists() or obj.stat().st_mtime < src.stat().st_mtime:
            problems.append("filter_policy.o is missing or older than filter_policy.cc")
        elif binary.stat().st_mtime < obj.stat().st_mtime:
            problems.append("filter_bench is older than filter_policy.o")
    cpu = None
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.lower().startswith("model name"):
            cpu = line.split(":", 1)[1].strip()
            break
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "machine.json").write_text(json.dumps({
        "cpu": cpu, "arch": platform.machine(), "kernel": platform.release(),
        "rocksdb_commit": head,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}, indent=2) + "\n")
    (RES / "check.json").write_text(json.dumps(
        {"ok": not problems, "problems": problems, "sizes": SIZES, "runs": RUNS}, indent=2) + "\n")
    for p in problems:
        print("CHECK FAILED:", p)
    if problems:
        sys.exit(1)
    print("check passed")


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stage_run(rocksdb):
    chk = RES / "check.json"
    if not chk.exists() or not json.loads(chk.read_text())["ok"]:
        sys.exit("refusing to run: --stage check must pass first")
    if (RES / "compare.json").exists():
        sys.exit("refusing to overwrite results/e5/compare.json")
    work = Path(tempfile.mkdtemp(prefix="e5_dump_"))
    compare = []
    for size in SIZES:
        max_m = max(40, size // 1_000_000 * 3)  # E2's rule
        dirs = {}
        for run, env in RUNS.items():
            d = work / f"{size}_{run}"
            d.mkdir()
            dirs[run] = d
            run_env = {k: v for k, v in os.environ.items() if not k.startswith("PLEAT_")}
            run_env.update(env)
            run_env["PLEAT_DUMP_DIR"] = str(d)
            p = subprocess.run([str(rocksdb / "filter_bench"), "-impl", "2",
                                "-m_keys_total_max", str(max_m),
                                "-average_keys_per_filter", str(size),
                                "-net_includes_hashing", "-quick"],
                               capture_output=True, text=True, env=run_env)
            if p.returncode != 0:
                sys.exit(f"filter_bench failed ({size}, {run}): {p.stderr[-400:]}")
            files = sorted(d.glob("filter_*.bin"))
            (RES / f"{size}_{run}.sha256").write_text(
                "".join(f"{f.name} {f.stat().st_size} {digest(f)}\n" for f in files))
            print(f"{size:>11,} {run:<8} {len(files)} filters", flush=True)
        for a, b in PAIRS:
            fa = sorted(x.name for x in dirs[a].glob("filter_*.bin"))
            fb = sorted(x.name for x in dirs[b].glob("filter_*.bin"))
            differing = [n for n in fa if n in set(fb)
                         and not filecmp.cmp(dirs[a] / n, dirs[b] / n, shallow=False)]
            compare.append({"size": size, "a": a, "b": b, "count_a": len(fa), "count_b": len(fb),
                            "same_names": fa == fb, "differing": differing})
            print(f"            {a} vs {b}: {len(differing)} differing of {len(fa)}", flush=True)
        for d in dirs.values():
            shutil.rmtree(d)
    (RES / "compare.json").write_text(json.dumps(compare, indent=2) + "\n")


def stage_analyze():
    cmp_path = RES / "compare.json"
    if not cmp_path.exists():
        sys.exit("refusing to analyze: results/e5/compare.json missing")
    compare = json.loads(cmp_path.read_text())
    machine = json.loads((RES / "machine.json").read_text())

    def digests(size, run):
        return [tuple(l.split()) for l in (RES / f"{size}_{run}.sha256").read_text().splitlines()]

    L = ["generated-by: experiments/e5_byte_identity/run.py --stage analyze over results/e5/ "
         f"(machine: {machine['cpu']}, {machine['arch']}; RocksDB {machine['rocksdb_commit'][:9]})",
         "", "# E5 analysis (derived — do not hand-edit)", "",
         "| keys/filter | pair | filters | byte-compare differing | SHA-256 lists equal |",
         "|---|---|---|---|---|"]
    ok = {"control": True, "h": True}
    total = 0
    for c in compare:
        sha_equal = digests(c["size"], c["a"]) == digests(c["size"], c["b"])
        same = c["same_names"] and not c["differing"] and sha_equal and c["count_a"] > 0
        key = "control" if c["b"] == "stock_b" else "h"
        ok[key] &= same
        if key == "h":
            total += c["count_a"]
        L.append(f"| {c['size']:,} | {c['a']} vs {c['b']} | {c['count_a']} / {c['count_b']} "
                 f"| {len(c['differing'])} | {'yes' if sha_equal else 'NO'} |")
    L += ["",
          f"- Control (stock_a == stock_b at every size): {'PASS' if ok['control'] else 'FAIL — experiment void'}",
          f"- **H-E5** (pleated byte-identical to stock at every size): "
          + ("VOID (control failed)" if not ok["control"] else
             f"HOLDS — {total} filters compared, all identical" if ok["h"] else "FAILS — see table")]
    (RES / "ANALYSIS.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["check", "run", "analyze"])
    ap.add_argument("--rocksdb", type=Path)
    a = ap.parse_args()
    if a.stage == "analyze":
        stage_analyze()
    elif not a.rocksdb:
        sys.exit("--rocksdb is required for check and run")
    else:
        (stage_check if a.stage == "check" else stage_run)(a.rocksdb.resolve())
