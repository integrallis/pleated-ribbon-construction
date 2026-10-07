#!/usr/bin/env bash
# Run E6 (experiments/e6_memory_and_boundary) on a benchmark box and pull results back.
# Usage: scripts/e6_remote.sh <host> [ssh_key_path]   Does not create or delete the server.
set -euo pipefail
HOST="$1"
KEY="${2:-$HOME/.ssh/tf_bench_ed25519}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
USER="${SSH_USER:-root}"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 "$USER@$HOST")
ROCKSDB_COMMIT=31b239747
R='~/pleated-ribbon-construction'

if [ -e "$REPO_ROOT/results/e6" ]; then
  echo "results/e6 already exists locally; refusing to overwrite" >&2; exit 1
fi

echo "== packages =="
"${SSH[@]}" 'cloud-init status --wait >/dev/null 2>&1 || true
  SUDO=""; [ "$(id -u)" -eq 0 ] || SUDO="sudo"
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get update -qq &&
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq build-essential cmake git python3 binutils curl rsync time util-linux \
    libtbb-dev libgflags-dev libsnappy-dev zlib1g-dev libbz2-dev liblz4-dev libzstd-dev >/dev/null'

echo "== machine identity =="
"${SSH[@]}" 'uname -m; grep -m1 "model name" /proc/cpuinfo; nproc; free -g | head -2'

echo "== sync repo (code and protocol only) =="
rsync -az -e "ssh -i $KEY" \
  --exclude target/ --exclude 'harness/*/' --exclude .env --exclude .git/ --exclude results/ \
  --exclude research_notes/ --exclude reports/ --exclude docs/ --exclude paper/ --exclude dist/ \
  --exclude e1b_phase1 --exclude .DS_Store --exclude .venv/ \
  "$REPO_ROOT/" "$USER@$HOST:pleated-ribbon-construction/"

echo "== harnesses (pinned) and driver =="
"${SSH[@]}" "set -e; cd $R/harness && bash setup_harnesses.sh >/dev/null
  [ -d BuRR ] || git clone --quiet --recursive https://github.com/lorenzhs/BuRR
  git -C BuRR checkout -q \"\$(awk '/^BuRR /{print \$2}' PINS)\" && git -C BuRR submodule update --init --recursive -q
  cd $R/src/ribbon_reorder && make clean >/dev/null 2>&1
  make CXXFLAGS='-O3 -march=native -std=c++17 -Wall -Wextra -pthread -I../../harness/fastfilter_cpp/src/ribbon -I../../harness/fastfilter_cpp/benchmarks -I../../harness/BuRR/ips2ra/include' >/dev/null"

echo "== RocksDB at $ROCKSDB_COMMIT + pleat patch =="
"${SSH[@]}" "set -e
  [ -d ~/rocksdb ] || git clone --quiet https://github.com/facebook/rocksdb ~/rocksdb
  cd ~/rocksdb && git checkout --quiet -f $ROCKSDB_COMMIT && git checkout --quiet -- .
  git apply $R/experiments/e2_rocksdb/pleat-rocksdb.patch
  make -j\"\$(nproc)\" DEBUG_LEVEL=0 filter_bench > ~/rocksdb_build.log 2>&1 || { tail -30 ~/rocksdb_build.log; exit 1; }"

echo "== E6 stages =="
"${SSH[@]}" "cd $R/experiments/e6_memory_and_boundary &&
  python3 run.py --stage check --rocksdb ~/rocksdb && python3 run.py --stage spill &&
  python3 run.py --stage memory --rocksdb ~/rocksdb && python3 run.py --stage concurrent"

echo "== pull raw results back =="
mkdir -p "$REPO_ROOT/results/e6"
rsync -az -e "ssh -i $KEY" "$USER@$HOST:pleated-ribbon-construction/results/e6/" "$REPO_ROOT/results/e6/"
echo "== done: run experiments/e6_memory_and_boundary/run.py --stage analyze locally =="
