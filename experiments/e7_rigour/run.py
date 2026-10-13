#!/usr/bin/env python3
"""E7 runner (protocol: README.md in this directory). Runs on the benchmark box as root.

Stages refuse to run before their prerequisite's artifact exists:

  check       build gates, machine identity and settings   -> check.json, machine.json
  crosscheck  e7_driver against e1b_phase1                 -> crosscheck.json
  main        ordering strategies by key count             -> raw/main/, main.done
  parallel    thread scaling of the parallel build         -> raw/parallel/, parallel.done
  counters    named cache-miss events, banding only        -> raw/counters/, counters.done
  config      band width, result bits, slot overhead       -> raw/config/, config.done
  keys        real and string key sets                     -> keys/manifest.json, raw/keys/, keys.done
  thp         transparent huge pages                       -> raw/thp/, thp.done
  compaction  RocksDB db_bench, stock and pleated          -> raw/compaction/, compaction.done

Usage: run.py --stage <stage> --machine <name> [--rocksdb /path/to/rocksdb]
Results go to results/e7/<name>/. E7_RES and E7_SMOKE are for smoke tests: E7_SMOKE shrinks
every size and repetition count and is refused when writing under results/e7.
The protocol (cells, repetitions, settings) is fixed in README.md; do not change it here after
it is committed.
"""
import argparse
import datetime
import hashlib
import json
import os
import platform
import random
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "ribbon_reorder"
PATCH = ROOT / "experiments" / "e2_rocksdb" / "pleat-rocksdb.patch"
REGISTERED = (ROOT / "results" / "e7").resolve()
SMOKE = bool(os.environ.get("E7_SMOKE"))
ORDER_SEED = 0xE7

M = 1_000_000
SIZES = [10 * M, 100 * M, 400 * M]
BIG = 100 * M
if SMOKE:
    SIZES, BIG = [1 * M, 2 * M], 2 * M

MAIN_STRATEGIES = ["reference", "noprefetch", "sort_std", "sort_radix", "sort_ips2ra", "partitioned"]
E7_STRATEGIES = ["reference", "sort_ips2ra", "partitioned"]
COUNTER_STRATEGIES = ["reference", "sort_radix", "sort_ips2ra", "partitioned"]
THREADS = [1, 2, 4, 8, 16]
REPS = {"main": 10, "parallel": 10, "counters": 5, "config": 5, "keys": 5, "thp": 5,
        "compaction": 20, "compaction_sst": 5, "crosscheck": 3}
if SMOKE:
    REPS = {k: 2 for k in REPS}
CONFIGS = [(64, 7, "default"), (64, 8, "default"), (64, 16, "default"), (128, 7, "default"),
           (128, 8, "default"), (128, 16, "default"), (64, 7, "1.05"), (64, 7, "1.15")]
KEY_SETS = [("sosd_fb", "u64", False), ("sosd_osm", "u64", False), ("sosd_wiki", "u64", False),
            ("cc_hosts", "str", False), ("cc_hosts", "str", True),
            ("synth16", "str", False), ("synth16", "str", True),
            ("synth64", "str", False), ("synth64", "str", True)]
THP_MODES = ["madvise", "always", "never"]
E7_BINS = ["e7_w64_r7", "e7_w64_r8", "e7_w64_r16", "e7_w128_r7", "e7_w128_r8", "e7_w128_r16",
           "e7_w64_r7_str"]

# Named events for the counters stage, by CPU vendor. Resolved to raw codes in the check stage;
# an event the machine does not have is recorded as missing and left out.
EVENTS = {
    "GenuineIntel": ["mem_load_retired.l2_miss", "mem_load_retired.l3_miss",
                     "dtlb_load_misses.walk_completed"],
    "AuthenticAMD": ["l2_cache_req_stat.dc_access_in_l2", "l2_cache_req_stat.ic_dc_miss_in_l2",
                     "ls_dmnd_fills_from_sys.dram_io_near", "ls_l1_d_tlb_miss.all"],
    "ARM": ["l2d_cache_lmiss_rd", "ll_cache_miss_rd", "dtlb_walk"],
}

ROCKSDB_COMMIT = "31b239747"
MARKER = b"PLEAT_PROFILE banding"
DB_KEYS = 300_000 if SMOKE else 30_000_000
SST_MAIN, SST_SWEEP = 256 << 20, [64 << 20, 1 << 30]
CPU_MICROS = re.compile(r"rocksdb\.compaction\.total\.time\.cpu_micros COUNT : (\d+)")
COMPACT_MICROS = re.compile(r"rocksdb\.compaction\.times\.micros P50 : \S+ P95 : \S+ P99 : \S+ P100 : \S+ COUNT : (\d+) SUM : (\d+)")
FILLRANDOM = re.compile(r"fillrandom\s*:\s*([\d.]+) micros/op")


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, **kw)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def need(res, artifact, stage):
    if not (res / artifact).exists():
        sys.exit(f"stage {stage} refuses to run: {artifact} is missing")


def done(res, stage, extra=None):
    (res / f"{stage}.done").write_text(json.dumps({"finished_utc": now(), **(extra or {})}) + "\n")


# ---- machine --------------------------------------------------------------------------------

def topology():
    """Logical CPUs of NUMA node 0, one per physical core, in core order."""
    rows = [l.split(",") for l in sh("lscpu -p=CPU,CORE,SOCKET,NODE").stdout.splitlines()
            if l and not l.startswith("#")]
    seen, cpus = set(), []
    for cpu, core, socket, node in rows:
        if (node or "0") == "0" and (socket, core) not in seen:
            seen.add((socket, core))
            cpus.append(int(cpu))
    return cpus


def vendor():
    if platform.machine() == "aarch64":
        return "ARM"
    m = re.search(r"vendor_id\s*:\s*(\S+)", Path("/proc/cpuinfo").read_text())
    return m.group(1) if m else "unknown"


def resolve_events():
    """Raw code of each named event on this machine, or None."""
    out = {}
    for name in EVENTS.get(vendor(), []):
        code = None
        if vendor() == "ARM":
            spec = read(f"/sys/bus/event_source/devices/armv8_pmuv3_0/events/{name}")
            m = re.match(r"event=(0x[0-9a-fA-F]+)$", spec or "")
            code = m.group(1) if m else None
        else:
            r = sh(["perf", "stat", "-vv", "-e", name, "true"])
            m = re.search(r"^\s*config\s+(0x[0-9a-fA-F]+)", r.stderr + r.stdout, flags=re.M)
            typ = re.search(r"^\s*type\s+(\d+)", r.stderr + r.stdout, flags=re.M)
            # The driver opens PERF_TYPE_RAW (type 4) events only.
            code = m.group(1) if m and typ and typ.group(1) == "4" and r.returncode == 0 else None
        out[name] = code
    return out


def machine_info(cpus):
    cpuinfo = Path("/proc/cpuinfo").read_text()
    model = re.search(r"model name\s*:\s*(.+)", cpuinfo)
    micro = re.search(r"microcode\s*:\s*(\S+)", cpuinfo)
    pin = cpus[2]
    return {
        "timestamp_utc": now(), "arch": platform.machine(), "vendor": vendor(),
        "cpu": model.group(1) if model else sh("lscpu | grep 'Model name'").stdout.strip(),
        "microcode": micro.group(1) if micro else None,
        "kernel": platform.release(), "virt": sh("systemd-detect-virt").stdout.strip(),
        "lscpu": sh("lscpu").stdout, "numactl_hardware": sh("numactl --hardware").stdout,
        "memory_kb": int(re.search(r"MemTotal:\s*(\d+)", Path("/proc/meminfo").read_text()).group(1)),
        "node0_physical_cpus": cpus, "pinned_cpu": pin,
        "smt_active": read("/sys/devices/system/cpu/smt/active"),
        "pinned_cpu_siblings": read(f"/sys/devices/system/cpu/cpu{pin}/topology/thread_siblings_list"),
        "governor": read(f"/sys/devices/system/cpu/cpu{pin}/cpufreq/scaling_governor"),
        "cpufreq_driver": read(f"/sys/devices/system/cpu/cpu{pin}/cpufreq/scaling_driver"),
        "intel_no_turbo": read("/sys/devices/system/cpu/intel_pstate/no_turbo"),
        "cpufreq_boost": read("/sys/devices/system/cpu/cpufreq/boost"),
        "thp_enabled": read("/sys/kernel/mm/transparent_hugepage/enabled"),
        "thp_defrag": read("/sys/kernel/mm/transparent_hugepage/defrag"),
        "aslr": read("/proc/sys/kernel/randomize_va_space"),
        "perf_event_paranoid": read("/proc/sys/kernel/perf_event_paranoid"),
        "gcc": sh("g++ --version").stdout.splitlines()[0],
        "source_commit": read(ROOT / ".source-commit"),
        "harness_pins": read(ROOT / "harness" / "PINS"),
        "fastfilter_cpp_head": sh("git -C harness/fastfilter_cpp rev-parse HEAD", cwd=ROOT).stdout.strip(),
        "burr_head": sh("git -C harness/BuRR rev-parse HEAD", cwd=ROOT).stdout.strip(),
        "events": resolve_events(),
    }


def pinned(cpus, mem_node=0):
    """Command prefix: these logical CPUs, memory from node 0."""
    return ["numactl", f"--membind={mem_node}", "taskset", "-c", ",".join(map(str, cpus))]


def set_thp(mode):
    Path("/sys/kernel/mm/transparent_hugepage/enabled").write_text(mode)
    assert f"[{mode}]" in read("/sys/kernel/mm/transparent_hugepage/enabled")


# ---- running cells --------------------------------------------------------------------------

def run_cells(res, stage, cells, reps):
    """cells: name -> (command, env). Each repetition runs every cell once, in an order shuffled
    with a fixed seed; the order is recorded. A cell that fails stops the stage."""
    raw = res / "raw" / stage
    raw.mkdir(parents=True, exist_ok=True)
    rng, order_log = random.Random(ORDER_SEED), []
    for rep in range(reps):
        names = sorted(cells)
        rng.shuffle(names)
        for name in names:
            out = raw / f"{name}_rep{rep}.json"
            order_log.append({"rep": rep, "cell": name, "started_utc": now()})
            if out.exists():
                continue
            make_cmd, env = cells[name]
            r = subprocess.run(make_cmd(rep), capture_output=True, text=True,
                               env={**os.environ, **env})
            if r.returncode != 0:
                (raw / f"{name}_rep{rep}.FAILED.txt").write_text(
                    f"{make_cmd(rep)}\nexit {r.returncode}\n{r.stdout}\n{r.stderr}")
                sys.exit(f"{stage}: {name} rep {rep} failed with exit {r.returncode}: {r.stderr[-400:]}")
            json.loads(r.stdout)
            out.write_text(r.stdout)
            print(f"{stage} {name} rep {rep}: {r.stdout.strip()[:150]}", flush=True)
    (raw / "order.json").write_text(json.dumps(order_log, indent=0) + "\n")


def one(path):
    return json.loads(Path(path).read_text())


# ---- stages ---------------------------------------------------------------------------------

def stage_check(res, args):
    res.mkdir(parents=True, exist_ok=True)
    gates = {}
    for b in ["e1b_phase1", *E7_BINS]:
        gates[f"binary {b}"] = (SRC / b).exists() and (SRC / b).stat().st_mtime >= (
            SRC / ("e1b_phase1.cc" if b == "e1b_phase1" else "e7_driver.cc")).stat().st_mtime
    gates["root"] = os.geteuid() == 0
    gates["perf_event_paranoid <= -1"] = int(read("/proc/sys/kernel/perf_event_paranoid") or 9) <= -1
    cpus = topology()
    gates["node 0 has at least 18 physical cores"] = len(cpus) >= 18 or SMOKE
    info = machine_info(cpus)
    gov = info["governor"]
    gates["governor is performance (or no cpufreq)"] = gov in ("performance", None)
    gates["source commit recorded"] = bool(info["source_commit"]) or SMOKE
    if args.profile == "full":
        gates["THP default is madvise"] = "[madvise]" in (info["thp_enabled"] or "")
    if args.rocksdb:
        rdb = Path(args.rocksdb)
        head = sh("git rev-parse HEAD", cwd=rdb).stdout.strip()
        gates["rocksdb at the pin"] = head.startswith(ROCKSDB_COMMIT)
        gates["rocksdb patch applied"] = sh(["git", "apply", "--reverse", "--check", str(PATCH)], cwd=rdb).returncode == 0
        db_bench = rdb / "db_bench"
        gates["db_bench built after the patched source"] = db_bench.exists() and db_bench.stat().st_mtime >= (
            rdb / "table" / "block_based" / "filter_policy.cc").stat().st_mtime
        gates["db_bench contains the patch"] = db_bench.exists() and MARKER in db_bench.read_bytes()
        info["rocksdb_head"] = head
    info["profile"], info["smoke"] = args.profile, SMOKE
    (res / "machine.json").write_text(json.dumps(info, indent=1) + "\n")
    ok = all(gates.values())
    (res / "check.json").write_text(json.dumps({"passed": ok, "gates": gates, "utc": now()}, indent=1) + "\n")
    for g, v in gates.items():
        print(("ok   " if v else "FAIL ") + g)
    print("events:", info["events"])
    if not ok:
        sys.exit("check failed")


def checked(res):
    need(res, "check.json", "this")
    if not one(res / "check.json")["passed"]:
        sys.exit("check.json records a failed check")
    return one(res / "machine.json")


def stage_crosscheck(res, args):
    """On w=64, r=7, synthetic keys, default overhead: same fingerprint as e1b_phase1 in every
    run, and median totals within 5% of e1b_phase1's (10% for the sorts)."""
    info = checked(res)
    pin = pinned([info["pinned_cpu"]])
    rows, ok = [], True
    for n in ([SIZES[0], BIG] if not SMOKE else SIZES[:1]):
        for strat in E7_STRATEGIES:
            pair = {"e1b": [], "e7": []}
            for rep in range(REPS["crosscheck"]):
                for which, cmd in (("e1b", [str(SRC / "e1b_phase1"), str(n), strat, str(rep)]),
                                   ("e7", [str(SRC / "e7_w64_r7"), str(n), strat, str(rep), "synth"])):
                    r = subprocess.run(pin + cmd, capture_output=True, text=True, check=True)
                    pair[which].append(json.loads(r.stdout))
            med = {w: sorted(x["total_ns_per_key"] for x in pair[w])[len(pair[w]) // 2] for w in pair}
            same = all(a["soln_fnv"] == b["soln_fnv"] and a["fpr"] == b["fpr"]
                       for a, b in zip(pair["e1b"], pair["e7"]))
            ratio = med["e7"] / med["e1b"]
            tol = 0.05 if strat in ("reference", "partitioned") else 0.10
            within = abs(ratio - 1) <= tol or SMOKE
            ok = ok and same and within
            rows.append({"n": n, "strategy": strat, "fingerprints_equal": same, "median_total_e1b": med["e1b"],
                         "median_total_e7": med["e7"], "ratio": ratio, "tolerance": tol, "within": within,
                         "runs": pair})
            print(f"crosscheck n={n} {strat}: fingerprints {'equal' if same else 'DIFFER'}, "
                  f"e7/e1b median total {ratio:.3f}", flush=True)
    (res / "crosscheck.json").write_text(json.dumps({"passed": ok, "rows": rows, "utc": now()}, indent=1) + "\n")
    if not ok:
        sys.exit("crosscheck failed: e7_driver numbers must not be used")


def crosschecked(res):
    info = checked(res)
    need(res, "crosscheck.json", "this")
    if not one(res / "crosscheck.json")["passed"]:
        sys.exit("crosscheck.json records a failure")
    return info


def stage_main(res, args):
    info = checked(res)
    pin = pinned([info["pinned_cpu"]])
    cells = {}
    for n in SIZES:
        for s in MAIN_STRATEGIES:
            cells[f"{s}_{n}"] = ((lambda rep, n=n, s=s: pin + [str(SRC / "e1b_phase1"), str(n), s, str(rep)]), {})
    run_cells(res, "main", cells, REPS["main"])
    done(res, "main")


def stage_parallel(res, args):
    info = checked(res)
    need(res, "main.done", "parallel")
    cpus = info["node0_physical_cpus"][2:]
    cells = {}
    for t in ([1, 2] if SMOKE else THREADS):
        cells[f"parallel_t{t}"] = ((lambda rep, t=t: pinned(cpus[:t]) + [
            str(SRC / "e1b_phase1"), str(BIG), "parallel", str(rep), "16", str(t)]), {})
    cells["partitioned_seq"] = ((lambda rep: pinned(cpus[:1]) + [
        str(SRC / "e1b_phase1"), str(BIG), "partitioned", str(rep)]), {})
    run_cells(res, "parallel", cells, REPS["parallel"])
    done(res, "parallel")


def stage_counters(res, args):
    info = crosschecked(res)
    pin = pinned([info["pinned_cpu"]])
    codes = [c for c in info["events"].values() if c]
    modes = {"generic": "generic"} if info["vendor"] != "ARM" else {}
    if codes:
        modes["raw"] = "raw:" + ",".join(codes)
    if not modes:
        sys.exit("counters: this machine exposes neither the generic nor the named events")
    cells = {}
    for n in ([BIG, SIZES[-1]] if not SMOKE else [BIG]):
        for s in COUNTER_STRATEGIES:
            for mode, env in modes.items():
                cells[f"{s}_{n}_{mode}"] = ((lambda rep, n=n, s=s: pin + [
                    str(SRC / "e7_w64_r7"), str(n), s, str(rep), "synth"]), {"E7_COUNTERS": env})
    run_cells(res, "counters", cells, REPS["counters"])
    done(res, "counters", {"modes": modes})


def stage_config(res, args):
    info = crosschecked(res)
    pin = pinned([info["pinned_cpu"]])
    cells = {}
    for w, r, overhead in CONFIGS:
        for s in E7_STRATEGIES:
            cells[f"w{w}_r{r}_o{overhead}_{s}"] = ((lambda rep, w=w, r=r, o=overhead, s=s: pin + [
                str(SRC / f"e7_w{w}_r{r}"), str(BIG), s, str(rep), "synth", o]), {})
    run_cells(res, "config", cells, REPS["config"])
    done(res, "config")


def stage_keys(res, args):
    info = crosschecked(res)
    keys = res / "keys"
    if not (keys / "manifest.json").exists():
        subprocess.run([sys.executable, str(Path(__file__).with_name("prepare_keys.py")), str(keys), str(BIG)],
                       check=True)
    manifest = one(keys / "manifest.json")
    assert manifest["n"] == BIG
    pin = pinned([info["pinned_cpu"]])
    cells = {}
    for name, kind, direct in KEY_SETS:
        binary = "e7_w64_r7_str" if direct else "e7_w64_r7"
        n = manifest["sets"][name]["keys_written"]  # 100M, or fewer for a set that has fewer
        for s in E7_STRATEGIES:
            cells[f"{name}_{'direct' if direct else 'hashed'}_{s}"] = ((lambda rep, b=binary, s=s, k=kind, nm=name, n=n: pin + [
                str(SRC / b), str(n), s, str(rep), f"{k}:{keys / (nm + '.' + k)}"]), {})
    run_cells(res, "keys", cells, REPS["keys"])
    done(res, "keys")


def stage_thp(res, args):
    info = crosschecked(res)
    pin = pinned([info["pinned_cpu"]])
    raw = res / "raw" / "thp"
    try:
        for mode in THP_MODES:
            set_thp(mode)
            cells = {f"{mode}_{s}": ((lambda rep, s=s: pin + [str(SRC / "e7_w64_r7"), str(BIG), s, str(rep), "synth"]), {})
                     for s in E7_STRATEGIES}
            run_cells(res, "thp", cells, REPS["thp"])
            (raw / f"order_{mode}.json").write_text((raw / "order.json").read_text())
    finally:
        set_thp("madvise")
    done(res, "thp")


def stage_compaction(res, args):
    info = checked(res)
    if not args.rocksdb or "rocksdb_head" not in info:
        sys.exit("compaction needs --rocksdb here and in the check stage")
    raw = res / "raw" / "compaction"
    raw.mkdir(parents=True, exist_ok=True)
    cpus = info["node0_physical_cpus"][2:6]
    db = Path("/dev/shm/e7_db")

    def run(arm, sst, rep):
        out = raw / f"{arm}_sst{sst >> 20}_rep{rep}.json"
        if out.exists():
            return
        sh(["rm", "-rf", str(db)])
        cmd = pinned(cpus) + [
            str(Path(args.rocksdb) / "db_bench"), "--benchmarks=fillrandom,waitforcompaction,stats",
            f"--num={DB_KEYS}", "--key_size=16", "--value_size=8", "--use_ribbon_filter=1",
            "--bloom_bits=10", "--compression_type=none", f"--write_buffer_size={128 << 20}",
            f"--target_file_size_base={sst}", "--disable_wal=1", "--threads=1", "--statistics=1",
            "--stats_level=4", "--seed=1", f"--db={db}"]
        env = {**os.environ, **({"PLEAT_RIBBON": "1"} if arm == "pleated" else {})}
        env.pop("PLEAT_PROFILE", None)
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
        wall = time.time() - t0
        text = r.stdout + r.stderr
        (raw / f"{arm}_sst{sst >> 20}_rep{rep}.log").write_text(text)
        cpu, comp, fill = CPU_MICROS.search(text), COMPACT_MICROS.search(text), FILLRANDOM.search(text)
        if r.returncode != 0 or not cpu or not comp or not fill:
            sys.exit(f"compaction: {arm} sst {sst >> 20} MiB rep {rep} failed or could not be parsed")
        ssts = sh(f"ls {db}/*.sst | wc -l").stdout.strip()
        out.write_text(json.dumps({
            "arm": arm, "sst_target_bytes": sst, "rep": rep, "keys": DB_KEYS,
            "compaction_cpu_micros": int(cpu.group(1)), "compactions": int(comp.group(1)),
            "compaction_wall_micros": int(comp.group(2)), "fillrandom_micros_per_op": float(fill.group(1)),
            "sst_files_at_end": int(ssts), "process_wall_s": round(wall, 2)}) + "\n")
        print(f"compaction {arm} sst {sst >> 20} MiB rep {rep}: cpu {int(cpu.group(1)) / 1e6:.2f} s", flush=True)

    rng = random.Random(ORDER_SEED)
    for rep in range(REPS["compaction"]):
        for arm in rng.sample(["stock", "pleated"], 2):
            run(arm, SST_MAIN, rep)
    for sst in SST_SWEEP:
        for rep in range(REPS["compaction_sst"]):
            for arm in rng.sample(["stock", "pleated"], 2):
                run(arm, sst, rep)
    sh(["rm", "-rf", str(db)])
    done(res, "compaction")


STAGES = {"check": stage_check, "crosscheck": stage_crosscheck, "main": stage_main,
          "parallel": stage_parallel, "counters": stage_counters, "config": stage_config,
          "keys": stage_keys, "thp": stage_thp, "compaction": stage_compaction}
PROFILES = {"full": list(STAGES), "replication": ["check", "crosscheck", "main", "parallel", "counters"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=list(STAGES))
    ap.add_argument("--machine", required=True)
    ap.add_argument("--profile", default="full", choices=list(PROFILES))
    ap.add_argument("--rocksdb")
    args = ap.parse_args()
    res = Path(os.environ.get("E7_RES", REGISTERED / args.machine)).resolve()
    if SMOKE and REGISTERED in [res, *res.parents]:
        sys.exit("E7_SMOKE is for smoke tests: set E7_RES outside results/e7")
    if args.stage not in PROFILES[args.profile]:
        sys.exit(f"stage {args.stage} is not part of the {args.profile} profile")
    STAGES[args.stage](res, args)


if __name__ == "__main__":
    main()
