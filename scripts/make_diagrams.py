#!/usr/bin/env python3
"""Schematic figures (not data-derived): banding access order, before/after the partition
pass. Print-safe, lightness-separated palette. Output: paper/figures/banding_order.pdf"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

OUT = Path(__file__).resolve().parent.parent / "paper" / "figures"
BLUE, LIGHT, MID, INK, MUTED = "#2c4a8c", "#e8ebf2", "#9db2d8", "#222222", "#666666"

fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.4))
plt.rcParams.update({"font.size": 7})

def table(ax, windows=False, hot=None):
    ax.add_patch(Rectangle((0, 0), 10, 0.7, fc=LIGHT, ec=MUTED, lw=0.8))
    if windows:
        for i in range(1, 8):
            ax.plot([i * 10 / 8] * 2, [0, 0.7], color=MUTED, lw=0.5)
        if hot is not None:
            ax.add_patch(Rectangle((hot * 10 / 8, 0), 10 / 8, 0.7, fc=MID, ec=BLUE, lw=1.2))
    ax.text(-0.15, 0.35, "banding\ntable\n(1.3 GB)", ha="right", va="center",
            fontsize=6, color=MUTED)

def key_row(ax, xs, y=2.6):
    for i, x in enumerate(xs):
        ax.add_patch(Rectangle((x - 0.16, y - 0.16), 0.32, 0.32, fc=BLUE, ec="none"))
        ax.text(x, y + 0.35, f"k{i+1}", ha="center", fontsize=6, color=INK)
    return y

# ---- (a) arrival order ----
ax = axes[0]
xs = [0.8, 2.2, 3.6, 5.0, 6.4, 7.8]
targets = [7.4, 1.2, 8.9, 3.4, 0.5, 5.8]
y = key_row(ax, xs)
for x, t in zip(xs, targets):
    ax.add_patch(FancyArrowPatch((x, y - 0.22), (t, 0.75), arrowstyle="-|>",
                                 mutation_scale=6, color=BLUE, lw=0.9,
                                 connectionstyle="arc3,rad=0.08"))
table(ax, windows=True)  # same windowed table as (b); only the access pattern differs
# dependent chain zoom under the table
for i in range(3):
    ax.add_patch(FancyArrowPatch((3.6 + i * 0.9, -0.55), (4.3 + i * 0.9, -0.55),
                                 arrowstyle="-|>", mutation_scale=5, color=MUTED, lw=0.9))
ax.text(5.0, -1.05, "…and each XOR step waits on the previous one",
        ha="center", fontsize=6, color=MUTED)
ax.set_title("(a) arrival order: every key a far jump", fontsize=7.5, color=INK)
ax.text(5.0, -1.6, "banding 46.1 ns/key · 5.75 misses/key", ha="center",
        fontsize=7, color=INK)

# ---- (b) window order ----
ax = axes[1]
y = key_row(ax, xs)
ax.add_patch(Rectangle((2.75, 1.44), 4.5, 0.54, fc="white", ec=BLUE, lw=1.0))
ax.text(5.0, 1.71, "counting pass (5.5 ns/key)", ha="center", va="center",
        fontsize=6.0, color=INK)
for x in xs:
    ax.add_patch(FancyArrowPatch((x, y - 0.22), (min(max(x, 3.6), 6.4), 1.98),
                                 arrowstyle="-", color=MID, lw=0.8,
                                 connectionstyle="arc3,rad=0.05"))
hot = 2
for i, t in enumerate([2.7, 2.9, 3.2, 3.4, 3.6, 3.55]):
    ax.add_patch(FancyArrowPatch((4.2 + (i - 2.5) * 0.35, 1.43), (t, 0.75),
                                 arrowstyle="-|>", mutation_scale=6, color=BLUE, lw=0.9,
                                 connectionstyle="arc3,rad=-0.05"))
table(ax, windows=True, hot=hot)
ax.annotate("one window ≈ 768 KB — fits in L2;\nprocessed one at a time, left to right",
            xy=(hot * 10 / 8 + 0.6, 0.02), xytext=(6.9, -1.05), fontsize=6, color=MUTED,
            ha="center", arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.7))
ax.set_title("(b) window order: same keys, grouped first", fontsize=7.5, color=INK)
ax.text(5.0, -1.6, "banding 15.2 ns/key · 0.17 misses/key", ha="center",
        fontsize=7, color=INK)

for ax in axes:
    ax.set_xlim(-1.6, 10.4)
    ax.set_ylim(-1.9, 3.3)
    ax.axis("off")
fig.tight_layout()
fig.savefig(OUT / "banding_order.pdf")
print("wrote", OUT / "banding_order.pdf")
