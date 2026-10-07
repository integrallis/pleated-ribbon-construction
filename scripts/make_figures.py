#!/usr/bin/env python3
"""Regenerate paper figures from raw artifacts only (no ANALYSIS files). Print-friendly:
lightness-separated colors (grayscale- and CVD-safe), direct labels, single axis per plot.
Outputs paper/figures/*.pdf.
"""
import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
P1 = ROOT / "results" / "e1b" / "phase1"
PAR = ROOT / "results" / "e1b" / "parallel"
OUT = ROOT / "paper" / "figures"
OUT.mkdir(exist_ok=True)

# Lightness-separated, print-safe: dark blue / mid gray / light gray.
C_REORDER, C_BAND, C_BACK = "#9db2d8", "#2c4a8c", "#c9c9c9"
INK, MUTED = "#222222", "#666666"

plt.rcParams.update({"font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "figure.dpi": 300})


def load(d, pattern):
    rows = {}
    for f in d.glob(pattern):
        j = json.loads(f.read_text())
        rows.setdefault((j["strategy"], j["n"], j.get("threads", 0)), []).append(j)
    return rows


def mean(rs, f):
    return statistics.mean(r[f] for r in rs)


def fig_strategies():
    rows = load(P1, "*_100000000_rep*.json")
    order = [("noprefetch", "unsorted"), ("reference", "unsorted+prefetch"),
             ("sort_std", "full sort (std::sort)"), ("sort_radix", "full sort (radix)"),
             ("sort_ips2ra", "full sort (ips2ra)"), ("partitioned", "partitioned (this work)")]
    labels, re_, ba, bs = [], [], [], []
    for key, label in order:
        rs = rows.get((key, 100_000_000, 0)) or rows.get((key, 100_000_000, 8))
        if not rs:
            continue
        labels.append(label)
        re_.append(mean(rs, "reorder_ns_per_key"))
        ba.append(mean(rs, "banding_ns_per_key"))
        bs.append(mean(rs, "backsubst_ns_per_key"))
    fig, ax = plt.subplots(figsize=(3.4, 2.25))
    y = range(len(labels))
    ax.barh(y, re_, height=0.62, color=C_REORDER, label="reorder")
    ax.barh(y, ba, height=0.62, left=re_, color=C_BAND, label="banding")
    left2 = [a + b for a, b in zip(re_, ba)]
    ax.barh(y, bs, height=0.62, left=left2, color=C_BACK, label="back-subst.")
    for i, t in enumerate(t1 + bs[i] for i, t1 in enumerate(left2)):
        ax.text(t + 1, i, f"{t:.1f}", va="center", fontsize=7, color=INK)
    ax.set_yticks(list(y), labels)
    ax.invert_yaxis()
    ax.set_xlabel("construction cost (ns/key), 100M keys")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=7, loc="upper center",
              bbox_to_anchor=(0.5, -0.28), ncol=3, columnspacing=1.2, handletextpad=0.5)
    fig.tight_layout()
    fig.savefig(OUT / "strategies_100m.pdf")


def fig_scaling():
    rows = load(PAR, "t*_100M_rep*.json")
    ts = sorted({k[2] for k in rows})
    band = [mean(rows[("parallel", 100_000_000, t)], "banding_ns_per_key") for t in ts]
    tot = [mean(rows[("parallel", 100_000_000, t)], "total_ns_per_key") for t in ts]
    fig, ax = plt.subplots(figsize=(3.4, 2.0))
    ax.plot(ts, tot, "-o", color=C_BAND, ms=4, lw=2, label="total")
    ax.plot(ts, band, "-s", color=MUTED, ms=4, lw=2, label="banding phase")
    for t, v in zip(ts, tot):
        ax.annotate(f"{v:.1f}", (t, v), textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=7, color=INK)
    ax.set_xscale("log", base=2)
    ax.set_xticks(ts, [str(t) for t in ts])
    ax.set_xlabel("threads")
    ax.set_ylabel("ns/key, 100M keys")
    ax.set_ylim(0, None)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "parallel_scaling.pdf")


def fig_rocksdb():
    """Banding ns/key vs per-filter size for RocksDB's Standard128 ribbon, stock vs pleated.
    Reads the committed sweep CSV (experiments/e2_rocksdb/results/sweep_fb.csv)."""
    import csv
    from collections import defaultdict
    src = ROOT / "experiments" / "e2_rocksdb" / "results" / "sweep_fb.csv"
    if not src.exists():
        print(f"skip fig_rocksdb: {src} not found")
        return
    vals = defaultdict(list)  # (mode, size) -> [banding_ns_per_key]
    with src.open() as fh:
        for row in csv.DictReader(fh):
            try:
                vals[(row["mode"], int(row["size"]))].append(float(row["banding_ns_per_key"]))
            except (ValueError, KeyError):
                continue
    sizes = sorted({s for _, s in vals})
    if not sizes:
        print("skip fig_rocksdb: no rows")
        return
    stock = [statistics.mean(vals[("stock", s)]) for s in sizes]
    pleat = [statistics.mean(vals[("pleated", s)]) for s in sizes]
    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    ax.plot(sizes, stock, "-o", color=MUTED, ms=4, lw=2, label="stock (arrival order)")
    ax.plot(sizes, pleat, "-s", color=C_BAND, ms=4, lw=2, label="pleated")
    ax.set_xscale("log")
    ax.set_xlabel("keys per filter")
    ax.set_ylabel("banding ns/key")
    ax.set_ylim(0, None)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "rocksdb_scale.pdf")


if __name__ == "__main__":
    fig_strategies()
    fig_scaling()
    fig_rocksdb()
    print(f"figures -> {OUT}")
