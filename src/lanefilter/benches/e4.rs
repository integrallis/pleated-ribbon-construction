//! E4 construction bench: parallel blocked-Bloom builders at equal thread counts, per the
//! frozen protocol (experiments/e4_parallel_bloom/README.md). Set E4_SIZES=full for the
//! registered 100M-key run; default is a 1M pilot (sanity only, not citable). Thread counts
//! come from E4_THREADS (default 1,2,4,8,16).
//!
//! Same timing convention as e1a: iter_with_large_drop excludes filter deallocation;
//! allocation, page faults and thread spawn/join are INCLUDED for every strategy alike.

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use lanefilter::{BlockedFilter, KeyStream};

const BITS_PER_KEY: f64 = 10.0;

fn sizes() -> Vec<(usize, &'static str)> {
    match std::env::var("E4_SIZES").as_deref() {
        Ok("full") => vec![(100_000_000, "100M")],
        _ => vec![(1_000_000, "1M")],
    }
}

fn threads() -> Vec<usize> {
    std::env::var("E4_THREADS")
        .unwrap_or_else(|_| "1,2,4,8,16".into())
        .split(',')
        .map(|t| t.trim().parse().expect("E4_THREADS: comma-separated integers"))
        .collect()
}

fn bench_builders(c: &mut Criterion) {
    for (n, label) in sizes() {
        let keys: Vec<u64> = KeyStream::new(0xA11CE).take(n).collect();

        // Bit-identity gate, outside any timing: a builder that differs from per-key
        // insertion aborts the bench before a single number is produced.
        let want = BlockedFilter::build_perkey(n, BITS_PER_KEY, &keys).fingerprint();
        for &t in &threads() {
            let r = BlockedFilter::build_par_range(n, BITS_PER_KEY, &keys, t).fingerprint();
            let a = BlockedFilter::build_par_atomic(n, BITS_PER_KEY, &keys, t).fingerprint();
            assert_eq!(r, want, "par_range differs from per-key at n={n}, threads={t}");
            assert_eq!(a, want, "par_atomic differs from per-key at n={n}, threads={t}");
            let c = BlockedFilter::build_par_scan(n, BITS_PER_KEY, &keys, t).fingerprint();
            assert_eq!(c, want, "par_scan differs from per-key at n={n}, threads={t}");
        }
        println!("E4 gate: all parallel builders bit-identical to per-key at n={n} ({want:016x})");

        let mut g = c.benchmark_group(format!("e4_construct/{label}"));
        g.throughput(Throughput::Elements(n as u64));
        g.sample_size(if n > 50_000_000 { 10 } else { 20 });

        g.bench_function(BenchmarkId::from_parameter("perkey"), |b| {
            b.iter_with_large_drop(|| BlockedFilter::build_perkey(n, BITS_PER_KEY, &keys))
        });
        g.bench_function(BenchmarkId::from_parameter("perkey_prefetch"), |b| {
            b.iter_with_large_drop(|| {
                BlockedFilter::build_perkey_prefetch(n, BITS_PER_KEY, &keys)
            })
        });
        for &t in &threads() {
            g.bench_function(BenchmarkId::from_parameter(format!("par_range_t{t}")), |b| {
                b.iter_with_large_drop(|| {
                    BlockedFilter::build_par_range(n, BITS_PER_KEY, &keys, t)
                })
            });
            g.bench_function(BenchmarkId::from_parameter(format!("par_atomic_t{t}")), |b| {
                b.iter_with_large_drop(|| {
                    BlockedFilter::build_par_atomic(n, BITS_PER_KEY, &keys, t)
                })
            });
            g.bench_function(BenchmarkId::from_parameter(format!("par_scan_t{t}")), |b| {
                b.iter_with_large_drop(|| {
                    BlockedFilter::build_par_scan(n, BITS_PER_KEY, &keys, t)
                })
            });
        }
        g.finish();
    }
}

criterion_group! {
    name = benches;
    config = Criterion::default();
    targets = bench_builders
}
criterion_main!(benches);
