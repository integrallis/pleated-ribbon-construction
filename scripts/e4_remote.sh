#!/usr/bin/env bash
# Run E4 (experiments/e4_parallel_bloom) on a fresh benchmark box and pull results back.
# Usage: scripts/e4_remote.sh <host> [ssh_key_path]
# Does not create or delete the server.
set -euo pipefail
HOST="$1"
KEY="${2:-$HOME/.ssh/tf_bench_ed25519}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
USER="${SSH_USER:-root}"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 "$USER@$HOST")

if [ -e "$REPO_ROOT/results/e4" ]; then
  echo "results/e4 already exists locally; refusing to overwrite" >&2; exit 1
fi

echo "== packages =="
"${SSH[@]}" 'cloud-init status --wait >/dev/null 2>&1 || true
  SUDO=""; [ "$(id -u)" -eq 0 ] || SUDO="sudo"
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get update -qq &&
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq build-essential cmake git python3 binutils curl rsync libtbb-dev >/dev/null'

echo "== machine identity =="
"${SSH[@]}" 'uname -m; grep -m1 "model name" /proc/cpuinfo; nproc; free -g | head -2; systemd-detect-virt || true'

echo "== rust toolchain =="
"${SSH[@]}" 'command -v cargo >/dev/null || (curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y -q); . "$HOME/.cargo/env"; rustc --version'

echo "== sync repo (code and protocol only) =="
rsync -az -e "ssh -i $KEY" \
  --exclude target/ --exclude 'harness/*/' --exclude .env --exclude .git/ --exclude results/ \
  --exclude research_notes/ --exclude reports/ --exclude docs/ --exclude paper/ \
  --exclude e1b_phase1 --exclude .DS_Store \
  "$REPO_ROOT/" "$USER@$HOST:~/ribbon-catches-bloom/"

echo "== harnesses (pinned) and E1b driver =="
"${SSH[@]}" 'set -e; cd ~/ribbon-catches-bloom/harness && bash setup_harnesses.sh >/dev/null
  [ -d BuRR ] || git clone --quiet --recursive https://github.com/lorenzhs/BuRR
  git -C BuRR checkout -q "$(awk "/^BuRR /{print \$2}" PINS)" && git -C BuRR submodule update --init --recursive -q
  cd ~/ribbon-catches-bloom/src/ribbon_reorder && make clean >/dev/null 2>&1
  make CXXFLAGS="-O3 -march=native -std=c++17 -Wall -Wextra -pthread -I../../harness/fastfilter_cpp/src/ribbon -I../../harness/fastfilter_cpp/benchmarks -I../../harness/BuRR/ips2ra/include" >/dev/null'

echo "== E4 stages =="
"${SSH[@]}" '. "$HOME/.cargo/env"; cd ~/ribbon-catches-bloom/experiments/e4_parallel_bloom &&
  python3 run.py --stage check && python3 run.py --stage fpr && python3 run.py --stage anchor &&
  python3 run.py --stage bloom && python3 run.py --stage ribbon'

echo "== pull raw results back =="
mkdir -p "$REPO_ROOT/results/e4"
rsync -az -e "ssh -i $KEY" "$USER@$HOST:~/ribbon-catches-bloom/results/e4/" "$REPO_ROOT/results/e4/"
echo "== done: run experiments/e4_parallel_bloom/run.py --stage analyze locally =="
