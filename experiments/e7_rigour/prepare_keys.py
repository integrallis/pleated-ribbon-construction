#!/usr/bin/env python3
"""Fetch and prepare the key sets of E7's `keys` stage. Run on the benchmark box by run.py.

Writes into the given directory, and a manifest (source, counts, sha256) beside them:

  sosd_fb.u64, sosd_osm.u64, sosd_wiki.u64   N distinct keys of each SOSD set (fewer if the set
                                             has fewer: then the largest multiple of N/10), a
                                             seeded random sample in the file's ascending order
  cc_hosts.str                               the first N host names of the pinned Common Crawl
                                             host-level web graph, in the release's order
  synth16.str, synth64.str                   N distinct random strings of 16 and of 64 bytes

.u64: raw little-endian uint64. .str: uint64 count, uint64 offsets[count + 1], bytes.
Usage: prepare_keys.py <dir> <N>
"""
import gzip
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np

OUT, N = Path(sys.argv[1]), int(sys.argv[2])
SEED = 0xE7
DATAVERSE = "https://dataverse.harvard.edu/api/access/datafile/:persistentId?persistentId=doi:10.7910/DVN/JGVF9A/"
SOSD = {"sosd_fb": ("EATHF7", "fb_200M_uint64"), "sosd_osm": ("8FX9BV", "osm_cellids_200M_uint64"),
        "sosd_wiki": ("SVN8PI", "wiki_ts_200M_uint64")}
CC_RELEASE = "cc-main-2025-mar-apr-may"
CC_BASE = "https://data.commoncrawl.org/"
CC_PATHS = f"{CC_BASE}projects/hyperlinkgraph/{CC_RELEASE}/host/{CC_RELEASE}-host-vertices.paths.gz"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


def fetch(url, dest):
    if not dest.exists():
        subprocess.run(["curl", "-sSfL", "--retry", "5", "-o", str(dest) + ".part", url], check=True)
        Path(str(dest) + ".part").rename(dest)
    return dest


def write_strings(path, strings_bytes, lengths):
    offsets = np.zeros(len(lengths) + 1, dtype="<u8")
    np.cumsum(lengths, out=offsets[1:])
    with open(path, "wb") as f:
        f.write(np.array([len(lengths)], dtype="<u8").tobytes())
        f.write(offsets.tobytes())
        f.write(strings_bytes)
    return float(offsets[-1]) / len(lengths)


def sosd(name, file_id, title):
    out = OUT / f"{name}.u64"
    zst = fetch(DATAVERSE + file_id, OUT / f"{title}.zst")
    raw = OUT / title
    if not raw.exists():
        subprocess.run(["zstd", "-d", "-q", "-f", str(zst), "-o", str(raw)], check=True)
    data = np.fromfile(raw, dtype="<u8")
    count, keys = int(data[0]), data[1:]
    assert count == len(keys), (name, count, len(keys))
    distinct = np.unique(keys)
    # A set with fewer than N distinct keys gives the largest multiple of N/10 that it has.
    n = N if len(distinct) >= N else (len(distinct) // (N // 10)) * (N // 10)
    assert n > 0, (name, len(distinct))
    pick = np.sort(np.random.default_rng(SEED).choice(len(distinct), size=n, replace=False))
    distinct[pick].tofile(out)
    raw.unlink()
    return {"file": out.name, "source": DATAVERSE + file_id, "source_title": title,
            "source_sha256": sha256(zst), "keys_in_source": count, "distinct_in_source": len(distinct),
            "keys_written": n, "order": "ascending (the source's order)", "sha256": sha256(out)}


def cc_hosts():
    out = OUT / "cc_hosts.str"
    paths = gzip.decompress(urllib.request.urlopen(CC_PATHS).read()).decode().split()
    hosts, lengths, used, total, seen_dup = [], [], [], 0, 0
    for p in paths:
        part = fetch(CC_BASE + p, OUT / Path(p).name)
        used.append(p)
        previous = None
        with gzip.open(part, "rb") as f:
            for line in f:
                host = line.rstrip(b"\n").split(b"\t")[1]
                if host == previous:
                    seen_dup += 1
                    continue
                previous = host
                hosts.append(host)
                lengths.append(len(host))
                total += 1
                if total == N:
                    break
        part.unlink()
        if total == N:
            break
    assert total == N, f"the release holds only {total} host names"
    assert len(set(hosts)) == N, "host names are not distinct"
    mean = write_strings(out, b"".join(hosts), np.array(lengths, dtype="<u8"))
    return {"file": out.name, "source": CC_PATHS, "release": CC_RELEASE, "parts_used": used,
            "keys_written": N, "adjacent_duplicates_skipped": seen_dup, "mean_bytes": mean,
            "order": "the release's order", "sha256": sha256(out)}


def synth(length):
    out = OUT / f"synth{length}.str"
    rng = np.random.default_rng(SEED + length)
    body = rng.integers(0, 256, size=(N, length), dtype=np.uint8)
    body[:, :8] = np.arange(N, dtype="<u8").view(np.uint8).reshape(N, 8)  # distinct by construction
    mean = write_strings(out, body.tobytes(), np.full(N, length, dtype="<u8"))
    return {"file": out.name, "source": f"numpy default_rng({SEED + length}); first 8 bytes are the index",
            "keys_written": N, "mean_bytes": mean, "sha256": sha256(out)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"n": N, "numpy": np.__version__, "sets": {}}
    for name, (file_id, title) in SOSD.items():
        manifest["sets"][name] = sosd(name, file_id, title)
        print(name, manifest["sets"][name]["distinct_in_source"], flush=True)
    manifest["sets"]["cc_hosts"] = cc_hosts()
    print("cc_hosts", manifest["sets"]["cc_hosts"]["mean_bytes"], flush=True)
    for length in (16, 64):
        manifest["sets"][f"synth{length}"] = synth(length)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")


if __name__ == "__main__":
    main()
