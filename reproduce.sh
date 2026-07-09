#!/usr/bin/env bash
# Re-derive every reported number from committed raw artifacts. No special hardware needed.
set -e
cd "$(dirname "$0")"
echo "== integrity checks =="
uv run python scripts/check_integrity.py
echo "== rust unit tests =="
cargo test --release -q
echo "== re-derive analyses from raw artifacts =="
for exp in experiments/*/analyze.py; do
  [ -f "$exp" ] && uv run python "$exp" --from-artifacts
done
echo "== done =="
