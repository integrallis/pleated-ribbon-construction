//! E0 criterion bench: probe-strategy comparison over identical SBBF-geometry filters,
//! across filter sizes spanning L1 → RAM. See experiments/e0_feasibility/README.md for the
//! pre-registered protocol. Raw criterion JSON is the artifact; analysis derives from it.

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use fastbloom::BloomFilter;
use lanefilter::{BlockedFilter, KeyStream};

const PROBE_BATCH: usize = 8192;
/// Amendment 1 (see RESEARCH_LOG 2026-07-09): probes are drawn from a large pool, advancing
/// each iteration, so no cache line is re-probed within any realistic reuse distance. A fixed
/// reused batch let RAM-size rows measure a warmed 512KiB working set in run 1.
const PROBE_POOL: usize = 4 << 20; // 4M keys × 8B = 32MiB pool, ≥4M distinct filter lines

struct SizePoint {
    label: &'static str,
    target_bytes: usize,
}

// i9-14900HX cache sizes: L1d 48K(P)/32K(E), L2 2M(P-core), L3 36M shared.
const SIZES: &[SizePoint] = &[
    SizePoint { label: "32KiB_l1", target_bytes: 32 << 10 },
    SizePoint { label: "256KiB_l2", target_bytes: 256 << 10 },
    SizePoint { label: "4MiB_l3", target_bytes: 4 << 20 },
    SizePoint { label: "64MiB_ram", target_bytes: 64 << 20 },
    SizePoint { label: "512MiB_ram", target_bytes: 512 << 20 },
];

const BITS_PER_KEY: f64 = 10.0;

fn bench_probes(c: &mut Criterion) {
    for sp in SIZES {
        let n_keys = (sp.target_bytes * 8) as f64 / BITS_PER_KEY;
        let n_keys = n_keys as usize;

        // Build our filter and fastbloom at the same bits/key budget, same member set.
        let members = KeyStream::new(0xA11CE).take(n_keys);
        let mut ours = BlockedFilter::with_bits_per_key(n_keys, BITS_PER_KEY);
        let mut fb = BloomFilter::with_num_bits(sp.target_bytes * 8).expected_items(n_keys);
        for k in members {
            ours.insert(k);
            fb.insert(&k);
        }

        // Probe workload: absent keys (miss-dominated, the LSM point-lookup case), drawn from
        // a rotating pool so every iteration touches fresh cache lines (Amendment 1).
        let pool: Vec<u64> = KeyStream::new(0xD15EA5E)
            .take(PROBE_POOL)
            .map(|k| k ^ 0x5555_5555_5555_5555)
            .collect();
        let n_windows = PROBE_POOL / PROBE_BATCH;
        let mut out = vec![false; PROBE_BATCH];

        let mut g = c.benchmark_group(format!("probe_miss/{}", sp.label));
        g.throughput(Throughput::Elements(PROBE_BATCH as u64));

        macro_rules! bench_strategy {
            ($name:literal, $w:ident, $probes:ident, $body:expr) => {{
                let mut $w = 0usize;
                g.bench_function(BenchmarkId::from_parameter($name), |b| {
                    b.iter(|| {
                        let $probes =
                            &pool[$w * PROBE_BATCH..($w + 1) * PROBE_BATCH];
                        $w = ($w + 1) % n_windows;
                        $body
                    })
                });
            }};
        }

        bench_strategy!("scalar", w, probes, {
            ours.check_batch_scalar(std::hint::black_box(probes), &mut out)
        });
        bench_strategy!("prefetch", w, probes, {
            ours.check_batch_prefetch(std::hint::black_box(probes), &mut out)
        });
        bench_strategy!("lanes", w, probes, {
            ours.check_batch_lanes(std::hint::black_box(probes), &mut out)
        });
        // E0b control: same instruction stream as `lanes`, all addresses forced L1-hot.
        // NOT a filter (results are wrong by construction) — throughput ceiling only.
        bench_strategy!("lanes_hot_CONTROL", w, probes, {
            ours.check_batch_lanes_masked(std::hint::black_box(probes), &mut out, 0)
        });
        // External baseline: fastbloom 0.9 per-key API (includes its own hashing — context
        // anchor only, not a head-to-head claim; see E0 README).
        bench_strategy!("fastbloom_perkey", w, probes, {
            let mut acc = 0u32;
            for k in std::hint::black_box(probes) {
                acc += fb.contains(k) as u32;
            }
            std::hint::black_box(acc)
        });
        g.finish();
    }
}

criterion_group! {
    name = benches;
    config = Criterion::default().sample_size(30);
    targets = bench_probes
}
criterion_main!(benches);
