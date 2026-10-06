#!/usr/bin/env bash
# Run E3 Stage A (experiments/e3_bloom_gap) on a fresh benchmark box and pull results back.
# Usage: scripts/e3_remote.sh <host> [ssh_key_path]
# Builds RocksDB at the E2 pin with the E2 patch, then runs the staged runner. Does not create
# or delete the server.
set -euo pipefail
HOST="$1"
KEY="${2:-$HOME/.ssh/tf_bench_ed25519}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
USER="${SSH_USER:-root}"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$USER@$HOST")
ROCKSDB_COMMIT=31b239747

if [ -e "$REPO_ROOT/results/e3/sweep_fb.csv" ]; then
  echo "results/e3/sweep_fb.csv already exists locally; refusing to overwrite" >&2; exit 1
fi

echo "== packages =="
"${SSH[@]}" 'cloud-init status --wait >/dev/null 2>&1 || true
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq && apt-get install -y -qq build-essential git python3 binutils rsync \
    libgflags-dev libsnappy-dev zlib1g-dev libbz2-dev liblz4-dev libzstd-dev >/dev/null'

echo "== machine identity =="
"${SSH[@]}" 'uname -m; grep -m1 "model name" /proc/cpuinfo; nproc; free -g | head -2; systemd-detect-virt || true'

echo "== sync experiment (protocol, runner, patch) =="
"${SSH[@]}" 'mkdir -p ~/ribbon-catches-bloom/experiments ~/ribbon-catches-bloom/results'
rsync -az -e "ssh -i $KEY" "$REPO_ROOT/experiments/e3_bloom_gap" "$REPO_ROOT/experiments/e2_rocksdb" \
  "$USER@$HOST:~/ribbon-catches-bloom/experiments/"

echo "== RocksDB at $ROCKSDB_COMMIT + pleat patch, build filter_bench =="
"${SSH[@]}" "set -e
  [ -d ~/rocksdb ] || git clone --quiet https://github.com/facebook/rocksdb ~/rocksdb
  cd ~/rocksdb && git checkout --quiet $ROCKSDB_COMMIT
  git apply --reverse --check ~/ribbon-catches-bloom/experiments/e2_rocksdb/pleat-rocksdb.patch 2>/dev/null \
    || git apply ~/ribbon-catches-bloom/experiments/e2_rocksdb/pleat-rocksdb.patch
  make -j\"\$(nproc)\" DEBUG_LEVEL=0 filter_bench > ~/rocksdb_build.log 2>&1 || { tail -30 ~/rocksdb_build.log; exit 1; }"

echo "== E3 stages =="
"${SSH[@]}" 'cd ~/ribbon-catches-bloom/experiments/e3_bloom_gap &&
  python3 run.py --stage check --rocksdb ~/rocksdb &&
  python3 run.py --stage bench --rocksdb ~/rocksdb'

echo "== pull raw results back =="
mkdir -p "$REPO_ROOT/results/e3"
rsync -az -e "ssh -i $KEY" "$USER@$HOST:~/ribbon-catches-bloom/results/e3/" "$REPO_ROOT/results/e3/"
rsync -az -e "ssh -i $KEY" "$USER@$HOST:~/rocksdb_build.log" "$REPO_ROOT/results/e3/rocksdb_build.log"
echo "== done: run experiments/e3_bloom_gap/run.py --stage analyze locally =="
