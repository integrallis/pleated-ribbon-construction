#!/usr/bin/env bash
# Clone + build the third-party harnesses at pinned commits. Idempotent.
set -e
cd "$(dirname "$0")"

PINS_FILE="PINS"

clone_pin() {
  local dir="$1" url="$2"
  if [ ! -d "$dir/.git" ]; then
    git clone --recursive "$url" "$dir"
  fi
  if [ -f "$PINS_FILE" ] && grep -q "^$dir " "$PINS_FILE"; then
    local pin
    pin=$(grep "^$dir " "$PINS_FILE" | awk '{print $2}')
    git -C "$dir" checkout -q "$pin"
    git -C "$dir" submodule update --init --recursive -q 2>/dev/null || true
  else
    echo "$dir $(git -C "$dir" rev-parse HEAD)" >> "$PINS_FILE"
  fi
}

clone_pin fastfilter_cpp https://github.com/FastFilter/fastfilter_cpp
clone_pin FastLanes      https://github.com/cwida/FastLanes

echo "== building fastfilter_cpp benchmark =="
make -C fastfilter_cpp/benchmarks -j"$(nproc)" || {
  echo "fastfilter_cpp build failed — check compiler requirements in its README"; exit 1;
}
echo "== harnesses ready; pins: =="
cat "$PINS_FILE"
