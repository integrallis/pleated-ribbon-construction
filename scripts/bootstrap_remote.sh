#!/usr/bin/env bash
# Bootstrap a fresh benchmark box and run the full E0 pipeline there.
# Usage: scripts/bootstrap_remote.sh <host> [ssh_key_path] [results_tag]
# Example: scripts/bootstrap_remote.sh 1.2.3.4 ~/.ssh/tf_bench_ed25519 arm-cax31
set -euo pipefail
HOST="$1"
KEY="${2:-$HOME/.ssh/tf_bench_ed25519}"
TAG="${3:-remote}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
USER="${SSH_USER:-root}"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$USER@$HOST")

echo "== wait for cloud-init package install to finish =="
"${SSH[@]}" 'cloud-init status --wait >/dev/null 2>&1 || true; command -v gcc >/dev/null || (sudo apt-get update -qq && sudo apt-get install -y -qq build-essential cmake git python3 python3-pip binutils curl rsync)'

echo "== machine identity (recorded with results) =="
"${SSH[@]}" 'uname -m; grep -E "model name|Features|flags" /proc/cpuinfo | sort -u | head -3; nproc; free -g | head -2'

echo "== rust toolchain =="
"${SSH[@]}" 'command -v cargo >/dev/null || (curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y -q); . "$HOME/.cargo/env"; rustc --version'

echo "== sync repo (no target/, no harness clones, no .env) =="
rsync -az -e "ssh -i $KEY" \
  --exclude target/ --exclude harness/fastfilter_cpp/ --exclude harness/FastLanes/ \
  --exclude .env --exclude .git/ --exclude results/ --exclude "e1b_phase1" \
  "$REPO_ROOT/" "$USER@$HOST:~/ribbon-catches-bloom/"

echo "== harnesses (pinned) =="
"${SSH[@]}" 'cd ~/ribbon-catches-bloom/harness && bash setup_harnesses.sh'

echo "== E1b phase-1 driver (ribbon reorder) =="
"${SSH[@]}" 'sudo apt-get install -y -qq libtbb-dev 2>/dev/null || true
  cd ~/ribbon-catches-bloom/harness && [ -d BuRR ] || git clone --quiet --recursive https://github.com/lorenzhs/BuRR
  cd ~/ribbon-catches-bloom/src/ribbon_reorder && make clean >/dev/null 2>&1; make CXXFLAGS="-O3 -march=native -std=c++17 -Wall -Wextra -pthread -I../../harness/fastfilter_cpp/src/ribbon -I../../harness/fastfilter_cpp/benchmarks -I../../harness/BuRR/ips2ra/include" && ./e1b_phase1 1000000 partitioned 0'

echo "== E1b phase 1 (full sweep incl. parallel) =="
"${SSH[@]}" 'cd ~/ribbon-catches-bloom/experiments/e1b_ribbon_construction &&
  python3 run.py --stage phase0 && python3 run.py --stage analyze &&
  python3 run.py --stage phase1 &&
  cd ../../src/ribbon_reorder &&
  for T in 1 2 4 8; do ./e1b_phase1 100000000 parallel 0 16 $T > ../../results/e1b/parallel/t${T}_100M_rep0.json || true; done'

echo "== E0 stages =="
"${SSH[@]}" '. "$HOME/.cargo/env"; cd ~/ribbon-catches-bloom/experiments/e0_feasibility &&
  python3 run.py --stage check &&
  python3 run.py --stage fpr &&
  python3 run.py --stage bench &&
  python3 run.py --stage asm &&
  python3 run.py --stage anchor'

echo "== pull results back as results/e0a-$TAG =="
rsync -az -e "ssh -i $KEY" "root@$HOST:~/ribbon-catches-bloom/results/e0a/" "$REPO_ROOT/results/e0a-$TAG/"
echo "done: results in results/e0a-$TAG/ — run analyze locally against that directory"
