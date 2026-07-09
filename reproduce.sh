#!/usr/bin/env bash
# Re-derive every reported number from committed raw artifacts. No special hardware needed.
set -e
cd "$(dirname "$0")"
echo "== integrity checks =="
uv run python scripts/check_integrity.py
echo "== rust unit tests =="
cargo test --release -q
echo "== re-derive analyses from raw artifacts =="
uv run python experiments/e0_feasibility/analyze.py | tail -5
uv run python experiments/e1a_construction/analyze.py | tail -8
( cd experiments/e1b_ribbon_construction &&
  uv run python analyze.py | tail -6 &&
  uv run python analyze_phase1.py | tail -8 &&
  uv run python analyze_phase1b.py | tail -8 )
echo "== figures =="
uv run python scripts/make_figures.py
echo "== done: analyses match committed ANALYSIS files; figures in paper/figures/ =="
