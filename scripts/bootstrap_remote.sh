#!/usr/bin/env bash
# Bootstrap a fresh benchmark box and run the full E0 pipeline there.
# Usage: scripts/bootstrap_remote.sh <host> [ssh_key_path] [results_tag]
# Example: scripts/bootstrap_remote.sh 1.2.3.4 ~/.ssh/tf_bench_ed25519 arm-cax31
set -euo pipefail
HOST="$1"
KEY="${2:-$HOME/.ssh/tf_bench_ed25519}"
TAG="${3:-remote}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "root@$HOST")

echo "== wait for cloud-init package install to finish =="
"${SSH[@]}" 'cloud-init status --wait >/dev/null 2>&1 || true; command -v gcc >/dev/null || (apt-get update -qq && apt-get install -y -qq build-essential cmake git python3 binutils curl)'

echo "== machine identity (recorded with results) =="
"${SSH[@]}" 'uname -m; grep -E "model name|Features|flags" /proc/cpuinfo | sort -u | head -3; nproc; free -g | head -2'

echo "== rust toolchain =="
"${SSH[@]}" 'command -v cargo >/dev/null || (curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y -q); . "$HOME/.cargo/env"; rustc --version'

echo "== sync repo (no target/, no harness clones, no .env) =="
rsync -az -e "ssh -i $KEY" \
  --exclude target/ --exclude harness/fastfilter_cpp/ --exclude harness/FastLanes/ \
  --exclude .env --exclude .git/ --exclude results/ \
  "$REPO_ROOT/" "root@$HOST:~/transposed-filters/"

echo "== harnesses (pinned) =="
"${SSH[@]}" 'cd ~/transposed-filters/harness && ./setup_harnesses.sh'

echo "== E0 stages =="
"${SSH[@]}" '. "$HOME/.cargo/env"; cd ~/transposed-filters/experiments/e0_feasibility &&
  python3 run.py --stage check &&
  python3 run.py --stage fpr &&
  python3 run.py --stage bench &&
  python3 run.py --stage asm &&
  python3 run.py --stage anchor'

echo "== pull results back as results/e0a-$TAG =="
rsync -az -e "ssh -i $KEY" "root@$HOST:~/transposed-filters/results/e0a/" "$REPO_ROOT/results/e0a-$TAG/"
echo "done: results in results/e0a-$TAG/ — run analyze locally against that directory"
