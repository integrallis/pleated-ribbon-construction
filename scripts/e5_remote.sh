#!/usr/bin/env bash
# Run E5 (experiments/e5_byte_identity) on a benchmark box and pull results back.
# Usage: scripts/e5_remote.sh <host> [ssh_key_path]   Does not create or delete the server.
set -euo pipefail
HOST="$1"
KEY="${2:-$HOME/.ssh/tf_bench_ed25519}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
USER="${SSH_USER:-root}"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 "$USER@$HOST")
ROCKSDB_COMMIT=31b239747

if [ -e "$REPO_ROOT/results/e5" ]; then
  echo "results/e5 already exists locally; refusing to overwrite" >&2; exit 1
fi

echo "== packages =="
"${SSH[@]}" 'cloud-init status --wait >/dev/null 2>&1 || true
  SUDO=""; [ "$(id -u)" -eq 0 ] || SUDO="sudo"
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get update -qq &&
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq build-essential git python3 binutils rsync \
    libgflags-dev libsnappy-dev zlib1g-dev libbz2-dev liblz4-dev libzstd-dev >/dev/null'

echo "== sync experiment and patches =="
"${SSH[@]}" 'mkdir -p ~/ribbon-catches-bloom/experiments ~/ribbon-catches-bloom/results'
rsync -az -e "ssh -i $KEY" "$REPO_ROOT/experiments/e5_byte_identity" "$REPO_ROOT/experiments/e2_rocksdb" \
  "$USER@$HOST:~/ribbon-catches-bloom/experiments/"

echo "== RocksDB at $ROCKSDB_COMMIT + both patches, build filter_bench =="
"${SSH[@]}" "set -e
  [ -d ~/rocksdb ] || git clone --quiet https://github.com/facebook/rocksdb ~/rocksdb
  cd ~/rocksdb && git checkout --quiet -f $ROCKSDB_COMMIT && git checkout --quiet -- .
  git apply ~/ribbon-catches-bloom/experiments/e2_rocksdb/pleat-rocksdb.patch
  git apply ~/ribbon-catches-bloom/experiments/e5_byte_identity/dump-filters.patch
  make -j\"\$(nproc)\" DEBUG_LEVEL=0 filter_bench > ~/rocksdb_build.log 2>&1 || { tail -30 ~/rocksdb_build.log; exit 1; }"

echo "== E5 stages =="
"${SSH[@]}" 'cd ~/ribbon-catches-bloom/experiments/e5_byte_identity &&
  python3 run.py --stage check --rocksdb ~/rocksdb && python3 run.py --stage run --rocksdb ~/rocksdb'

echo "== pull results back =="
mkdir -p "$REPO_ROOT/results/e5"
rsync -az -e "ssh -i $KEY" "$USER@$HOST:~/ribbon-catches-bloom/results/e5/" "$REPO_ROOT/results/e5/"
echo "== done: run experiments/e5_byte_identity/run.py --stage analyze locally =="
