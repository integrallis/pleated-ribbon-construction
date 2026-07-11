# VPS / remote-machine runbook

For larger and cross-ISA runs (AVX-512, ARM NEON/SVE). The local dev box (i9-14900HX) has AVX2
only — every RQ3 portability claim needs at least one AVX-512 x86 machine and one ARM machine
(Graviton3/4 for SVE/SVE2, or Ampere/Grace).

## Hetzner specifics (this project's provider)

- API token: `HETZNER_TOKEN` in the repo-root `.env` (git-ignored — never commit; never echo).
- SSH: dedicated keypair `~/.ssh/tf_bench_ed25519`, registered in the account as
  `transposed-filters-bench` (2026-07-09, user-approved).
- Benchmark servers are named `rcb-bench-*`, labeled `project=ribbon-catches-bloom`. The
  pre-existing `vectors-bench` (CCX33) belongs to another project — do not touch.
- ARM = CAX line (shared-vCPU Ampere Altra, Neoverse-N1: NEON only, no SVE; note that N1 is
  out-of-order, so it tests ISA portability, not the in-order hypothesis). Capacity is often
  sold out — retry across fsn1/hel1/nbg1.
- x86 dedicated = CCX line; the account's dedicated-core quota is fully used by `vectors-bench`
  as of 2026-07-09 (user decision: ARM first, x86 later).
- Shared-vCPU boxes (CAX included): report criterion CIs and repeat runs; label results
  shared-vCPU. Citable single-thread latency numbers prefer dedicated/metal.
- One-command remote run: `scripts/bootstrap_remote.sh <ip> ~/.ssh/tf_bench_ed25519 <tag>` —
  installs toolchain, syncs repo, builds pinned harnesses, runs all E0 stages, pulls results
  back to `results/e0a-<tag>/`.
- **Teardown when idle** (billing): `DELETE /v1/servers/<id>` — confirm with user first.

## Setup (any Linux box)

```bash
# toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
sudo apt-get install -y build-essential cmake git python3 binutils   # objdump for asm stage
git clone <this-repo> && cd ribbon-catches-bloom
harness/setup_harnesses.sh          # clones + builds pinned fastfilter_cpp, FastLanes

# run E0 (stages refuse to outrun prerequisites)
cd experiments/e0_feasibility
python3 run.py --stage check
python3 run.py --stage fpr
python3 run.py --stage bench
python3 run.py --stage asm
python3 run.py --stage anchor
python3 run.py --stage analyze
```

## Per-machine notes

- Results are per-machine: run.py stamps CPU/rustc/RUSTFLAGS into the artifacts; keep each
  machine's results under `results/e0a-<machine-tag>/` (adjust RES in run.py or move after).
- On ARM, the asm stage's packed-instruction grep must look for NEON/SVE mnemonics
  (`ld1`, `tbl`, `and v`, `cmeq`, `z0`–`z31`) — update `stage_asm` patterns before trusting its
  vectorization verdict there.
- Pin CPU frequency if possible (`cpupower frequency-set -g performance`) and record whether the
  box is shared/virtualized — cloud steal time inflates variance; prefer metal or dedicated
  instances for citable numbers.
- fastfilter_cpp needs AVX2 for some algorithms on x86; on ARM it builds the portable paths.

## What to run where (current plan)

| machine | purpose |
|---|---|
| local i9-14900HX (AVX2) | E0 development runs (done), pilot numbers |
| x86 with AVX-512 (e.g., Sapphire Rapids / Zen4+) | rerun E0; VQF becomes runnable; gather width doubles |
| ARM Graviton3/4 | rerun E0; the NEON/SVE data point that no published filter study has |
