#!/usr/bin/env python3
"""Derive results/e1b/ANALYSIS.md from Phase-0 raw harness outputs only; evaluate the frozen
go/no-go gates mechanically where possible.

Parsed per raw file: the 'add    cycles: X/key, instructions: (Y/key, Z/cycle) cache misses:
W/key' perf line, and the summary row (column 2 = add ns/key; also FPR% and bits/item).
"""
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "e1b" / "phase0"
OUT = ROOT / "results" / "e1b" / "ANALYSIS.md"

ALGOS = ["HomogRibbon64_7", "BalancedRibbon64Pack_7", "XorBinaryFuse8",
         "XorBinaryFuse8_4wise", "Xor8", "BlockedBloom", "Bloom12_addAll"]
SIZES = [1_000_000, 10_000_000, 100_000_000]

ADD_RE = re.compile(
    r"add\s+cycles:\s+([\d.]+)/key, instructions: \(\s*([\d.]+)/key,\s+([\d.]+)/cycle\)"
    r" cache misses:\s+([\d.]+)/key"
)


def parse(path: Path):
    text = path.read_text()
    m = ADD_RE.search(text)
    perf = dict(zip(("cycles", "instr", "ipc", "miss"), map(float, m.groups()))) if m else {}
    add_ns = fpr = bits = None
    for line in text.splitlines():
        parts = line.split()
        # summary row: name, add_ns, remove, finds..., ε%, bits/item, ...
        if len(parts) >= 10 and not line.strip().startswith(("1-by-1", "add", "0.", "1.0")):
            try:
                add_ns = float(parts[1])
                fpr = float(parts[-5])
                bits = float(parts[-4])
            except (ValueError, IndexError):
                continue
    return add_ns, perf, fpr, bits


def main():
    if not RES.exists():
        sys.exit("missing results/e1b/phase0 — run --stage phase0 first")
    machine = json.loads((RES / "machine.json").read_text())
    data = {}
    for algo in ALGOS:
        for n in SIZES:
            reps = []
            for f in sorted(RES.glob(f"{algo}_{n}_rep*.txt")):
                add_ns, perf, fpr, bits = parse(f)
                if add_ns is not None:
                    reps.append((add_ns, perf, fpr, bits))
            if reps:
                data[(algo, n)] = reps

    lines = [
        f"generated-by: experiments/e1b_ribbon_construction/analyze.py over results/e1b/phase0/ "
        f"(machine: {machine['cpu']}, {machine['arch']})",
        "",
        "# E1b Phase-0 analysis (derived — do not hand-edit)",
        "",
        "## Construction cost (add-phase; mean over reps, ± half-range)",
        "",
        "| algorithm | n | add ns/key | cycles/key | IPC | misses/key | FPR% | bits/key |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for algo in ALGOS:
        for n in SIZES:
            if (algo, n) not in data:
                continue
            reps = data[(algo, n)]
            adds = [r[0] for r in reps]
            perf = reps[0][1]
            spread = (max(adds) - min(adds)) / 2 if len(adds) > 1 else 0.0
            lines.append(
                f"| {algo} | {n:,} | {statistics.mean(adds):.2f} ± {spread:.2f} "
                f"| {perf.get('cycles','—')} | {perf.get('ipc','—')} | {perf.get('miss','—')} "
                f"| {reps[0][2]} | {reps[0][3]} |"
            )

    lines += ["", "## Frozen go/no-go gates (evaluated at n=100M)", ""]
    go_miss, go_compute = [], []
    for algo in ALGOS:
        reps = data.get((algo, 100_000_000))
        if not reps:
            continue
        perf = reps[0][1]
        if perf.get("miss", 0) >= 0.5:
            go_miss.append((algo, perf["miss"]))
        if perf.get("ipc", 99) <= 1.5 and perf.get("cycles", 0) >= 60:
            go_compute.append((algo, perf["cycles"], perf["ipc"]))
        lines.append(
            f"- {algo}: {perf.get('cycles','?')} cyc/key, IPC {perf.get('ipc','?')}, "
            f"{perf.get('miss','?')} miss/key"
        )
    lines.append("")
    if go_miss:
        lines.append(
            f"Miss-bound candidates (≥0.5 miss/key): {go_miss} — GO only if the missing phase "
            "is NOT already reordering-based (requires audit's code-level findings; judgment "
            "call must be logged before Phase-1 registration)."
        )
    if go_compute:
        lines.append(f"Compute-slack candidates (IPC ≤1.5, ≥60 cyc/key): {go_compute} — same caveat.")
    if not go_miss and not go_compute:
        lines.append("NO-GO: no gate met — E1b terminates as the third null per protocol.")

    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
