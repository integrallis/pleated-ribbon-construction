generated-by: experiments/e4_parallel_bloom/analyze.py over results/e4/ (machine: AMD EPYC 9R14, x86_64, 16 CPUs, virt: amazon; rustc 1.99.0 (b940084d7 2026-09-28))

# E4 analysis (derived — do not hand-edit)

Topology: {"CPU(s)": "16", "Thread(s) per core": "1", "Core(s) per socket": "16", "Socket(s)": "1", "Hypervisor vendor": "KVM", "L1d cache": "512 KiB (16 instances)", "L2 cache": "16 MiB (16 instances)", "L3 cache": "64 MiB (2 instances)"}

## Gates

- Bloom bit-identity (bench fingerprint gate at 100M, every T): PASS
- Ribbon false negatives == 0 in every run: PASS
- Ribbon parallel fingerprint == sequential partitioned (same rep): PASS
- Cross-validation, prototype `perkey` 21.19 vs fastfilter_cpp BlockedBloom 17.30 ns/key (3 reps): 22.5% apart (tolerance 25%) -> PASS
- Prototype quality at 100M keys: FPR 1.2727% at 10.00 bits/key
- Ribbon quality: FPR 0.8252% at 7.63 bits/key

## Bloom builders, 100M keys (ns/key, Criterion mean ± std dev)

| builder | T=1 | T=2 | T=4 | T=8 | T=16 |
|---|---|---|---|---|---|
| par_range | 20.30±0.06 | 10.16±0.06 | 5.47±0.02 | 3.30±0.02 | 2.45±0.03 |
| par_atomic | 23.29±0.05 | 13.97±0.21 | 7.11±0.04 | 3.76±0.03 | 2.20±0.01 |
| par_scan | 10.01±0.02 | 8.14±0.07 | 8.59±0.03 | 7.64±0.02 | 7.09±0.00 |
| perkey (sequential) | 21.19±0.05 | — | — | — | — |
| perkey_prefetch (sequential) | 10.23±0.02 | — | — | — | — |

## Equal-thread comparison

Sequential pleated ribbon (`partitioned`): 40.30±0.05 ns/key.

| T | best Bloom build | Bloom ns/key | ribbon total ns/key | ribbon / Bloom | Bloom speedup vs T=1 | ribbon speedup vs T=1 |
|---|---|---|---|---|---|---|
| 1 | par_scan_t1 | 10.01 | 40.30±0.05 (sequential) | 4.03x | 1.00x | 1.00x |
| 2 | par_scan_t2 | 8.14 | 33.89±0.22 | 4.16x | 1.23x | 1.19x |
| 4 | par_range_t4 | 5.47 | 27.09±0.15 | 4.95x | 1.83x | 1.49x |
| 8 | par_range_t8 | 3.30 | 23.83±0.03 | 7.22x | 3.03x | 1.69x |
| 16 | par_atomic_t16 | 2.20 | 22.15±0.07 | 10.08x | 4.56x | 1.82x |

- **H-E4-1** (ribbon > 1.5x best Bloom at every T): HOLDS
- **H-E4-2** (ribbon ≤ 1.25x best Bloom at T=16): FAILS — equal-thread ratio must accompany any multi-thread comparison

Scope: one machine, 100M keys; Bloom 10 bits/key vs ribbon ~7.6 (not FPR- or space-matched); Criterion and the C++ driver run back to back; ribbon reorder and back-substitution are sequential.
