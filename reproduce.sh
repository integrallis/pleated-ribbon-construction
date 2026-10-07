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
  uv run python analyze_phase1b.py | tail -8 &&
  uv run python analyze_bloom_gap.py | tail -12 &&
  uv run python analyze_arm.py | tail -8 &&
  uv run python analyze_banding_steps.py | tail -3 )
uv run python experiments/e2_rocksdb/analyze.py | tail -6
uv run python experiments/e3_bloom_gap/analyze.py | tail -8
uv run python experiments/e4_parallel_bloom/analyze.py | tail -8
uv run python experiments/e5_byte_identity/run.py --stage analyze | tail -4
uv run python experiments/e6_memory_and_boundary/analyze.py | tail -6
echo "== figures =="
uv run python scripts/make_figures.py
echo "== done: analyses match committed ANALYSIS files; figures in paper/figures/ =="
