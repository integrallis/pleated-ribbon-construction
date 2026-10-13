#!/usr/bin/env bash
# Run E7 (experiments/e7_rigour) on a fresh Linux box, as root, and pull the results back.
# Usage: scripts/e7_remote.sh <host> <machine-name> <full|replication> [ssh_key_path]
#   machine-name names the results directory: results/e7/<machine-name>/
#   FETCH_ONLY=1  skip everything and only wait for a run that is already going, then pull.
#   E7_SMOKE=1    ship the working tree instead of the committed one, shrink every size, and
#                 write to results/e7-smoke/<machine-name>/ (never under results/e7).
# The run is detached on the box (log in ~/e7_bench.log, exit status in ~/e7_done).
set -euo pipefail
HOST="$1"; MACHINE="$2"; PROFILE="$3"
KEY="${4:-$HOME/.ssh/id_ed25519}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "root@$HOST")
FASTFILTER_PIN=924e5608fb15566bc15913f7cddfeb4a095445b2
BURR_PIN=5f588f4b92da0bc27c3521eac80b43a484583e58
ROCKSDB_COMMIT=31b239747
REMOTE=pleated-ribbon-construction
if [ -n "${E7_SMOKE:-}" ]; then OUT="results/e7-smoke/$MACHINE"; else OUT="results/e7/$MACHINE"; fi

if [ -z "${FETCH_ONLY:-}" ]; then
  if [ -z "${E7_SMOKE:-}" ]; then
    [ -z "$(git -C "$REPO_ROOT" status --porcelain)" ] || { echo "uncommitted changes; commit before a registered run" >&2; exit 1; }
    [ ! -e "$REPO_ROOT/$OUT/check.json" ] || { echo "$OUT already has results; refusing to overwrite" >&2; exit 1; }
  fi

  echo "== packages =="
  "${SSH[@]}" 'cloud-init status --wait >/dev/null 2>&1 || true
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq && apt-get install -y -qq build-essential git cmake python3 python3-numpy libxxhash-dev \
      libtbb-dev numactl zstd curl rsync libgflags-dev libsnappy-dev zlib1g-dev linux-tools-common >/dev/null
    apt-get install -y -qq "linux-tools-$(uname -r)" >/dev/null 2>&1 || apt-get install -y -qq linux-tools-generic >/dev/null 2>&1 || true
    command -v perf >/dev/null || echo "WARNING: no perf tool; named events cannot be resolved on x86"'

  echo "== settings: counters readable, performance governor =="
  "${SSH[@]}" 'sysctl -q -w kernel.perf_event_paranoid=-1
    for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do [ -w "$g" ] && echo performance > "$g" || true; done
    cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "no cpufreq"
    cat /sys/kernel/mm/transparent_hugepage/enabled'

  echo "== ship the tree =="
  "${SSH[@]}" "rm -rf ~/$REMOTE && mkdir -p ~/$REMOTE"
  if [ -n "${E7_SMOKE:-}" ]; then
    rsync -az -e "ssh -i $KEY" --exclude target/ --exclude 'harness/*/' --exclude .env --exclude .git/ \
      --exclude results/ --exclude paper/ --exclude dist/ --exclude 'src/ribbon_reorder/e7_w*' \
      --exclude src/ribbon_reorder/e1b_phase1 "$REPO_ROOT/" "root@$HOST:~/$REMOTE/"
    "${SSH[@]}" "echo smoke-working-tree > ~/$REMOTE/.source-commit"
  else
    git -C "$REPO_ROOT" archive HEAD | "${SSH[@]}" "tar -x -C ~/$REMOTE"
    "${SSH[@]}" "echo $(git -C "$REPO_ROOT" rev-parse HEAD) > ~/$REMOTE/.source-commit"
  fi

  echo "== harnesses at their pins, drivers =="
  "${SSH[@]}" "set -e; cd ~/$REMOTE/harness
    git clone --quiet https://github.com/FastFilter/fastfilter_cpp && git -C fastfilter_cpp checkout --quiet $FASTFILTER_PIN
    git clone --quiet --recursive https://github.com/lorenzhs/BuRR && git -C BuRR checkout --quiet $BURR_PIN
    git -C BuRR submodule update --quiet --init --recursive
    cd ../src/ribbon_reorder && make e1b_phase1 e7 > ~/e7_driver_build.log 2>&1 || { tail -30 ~/e7_driver_build.log; exit 1; }
    ls e1b_phase1 e7_w*"

  ROCKS=""
  if [ "$PROFILE" = full ]; then
    echo "== RocksDB at $ROCKSDB_COMMIT + pleat patch, build db_bench =="
    "${SSH[@]}" "set -e
      [ -d ~/rocksdb ] || git clone --quiet https://github.com/facebook/rocksdb ~/rocksdb
      cd ~/rocksdb && git checkout --quiet $ROCKSDB_COMMIT
      git apply --reverse --check ~/$REMOTE/experiments/e2_rocksdb/pleat-rocksdb.patch 2>/dev/null \
        || git apply ~/$REMOTE/experiments/e2_rocksdb/pleat-rocksdb.patch
      make -j\"\$(nproc)\" DEBUG_LEVEL=0 db_bench > ~/rocksdb_build.log 2>&1 || { tail -30 ~/rocksdb_build.log; exit 1; }"
    ROCKS="--rocksdb /root/rocksdb"
  fi

  if [ "$PROFILE" = full ]; then STAGES="check crosscheck main parallel counters config keys thp compaction"
  else STAGES="check crosscheck main parallel counters"; fi
  ENVV="E7_RES=/root/$REMOTE/$OUT"
  [ -z "${E7_SMOKE:-}" ] || ENVV="$ENVV E7_SMOKE=1"
  echo "== E7 stages: $STAGES (detached; log in ~/e7_bench.log on the box) =="
  "${SSH[@]}" "cd ~/$REMOTE && rm -f ~/e7_done &&
    nohup sh -c 'for s in $STAGES; do $ENVV python3 experiments/e7_rigour/run.py --stage \$s --machine $MACHINE --profile $PROFILE $ROCKS || { echo \$? > ~/e7_done; exit; }; done; echo 0 > ~/e7_done' > ~/e7_bench.log 2>&1 < /dev/null &"
fi

echo "== waiting for the run =="
until "${SSH[@]}" 'test -e ~/e7_done' 2>/dev/null; do sleep 60; done
"${SSH[@]}" 'tail -5 ~/e7_bench.log; echo "exit status: $(cat ~/e7_done)"'

echo "== pull raw results back (prepared key files stay on the box; their manifest comes) =="
mkdir -p "$REPO_ROOT/$OUT"
rsync -az -e "ssh -i $KEY" --exclude 'keys/*.u64' --exclude 'keys/*.str' --exclude 'keys/*.zst' --exclude 'keys/*.gz' \
  "root@$HOST:~/$REMOTE/$OUT/" "$REPO_ROOT/$OUT/"
for log in e7_bench e7_driver_build rocksdb_build; do
  rsync -az -e "ssh -i $KEY" "root@$HOST:~/$log.log" "$REPO_ROOT/$OUT/$log.log" 2>/dev/null || true
done
echo "== done: run experiments/e7_rigour/analyze.py locally =="
