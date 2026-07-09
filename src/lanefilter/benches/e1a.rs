//! E1a construction bench: five builders over identical key sets, sizes per the frozen
//! protocol (experiments/e1a_construction/README.md). Set E1A_SIZES=full for the full sweep;
//! default is the pilot (1M, 10M — sanity + variance only, not citable).
//!
//! iter_with_large_drop excludes filter deallocation from timings; allocation and page
//! faults are INCLUDED for every strategy alike (real construction cost).

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use lanefilter::{BlockedFilter, KeyStream};

const BITS_PER_KEY: f64 = 10.0;

fn sizes() -> Vec<(usize, &'static str)> {
    let pilot = vec![(1_000_000, "1M"), (10_000_000, "10M")];
    let full = vec![
        (1_000_000, "1M"),
        (10_000_000, "10M"),
        (53_700_000, "53.7M_64MBfilter"),
        (100_000_000, "100M"),
        (429_000_000, "429M_512MBfilter"),
    ];
    match std::env::var("E1A_SIZES").as_deref() {
        Ok("full") => full,
        _ => pilot,
    }
}

fn bench_builders(c: &mut Criterion) {
    for (n, label) in sizes() {
        let keys: Vec<u64> = KeyStream::new(0xA11CE).take(n).collect();
        let mut g = c.benchmark_group(format!("construct/{label}"));
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
        g.bench_function(BenchmarkId::from_parameter("partitioned"), |b| {
            b.iter_with_large_drop(|| BlockedFilter::build_partitioned(n, BITS_PER_KEY, &keys))
        });
        g.bench_function(BenchmarkId::from_parameter("partitioned_grouped"), |b| {
            b.iter_with_large_drop(|| {
                BlockedFilter::build_partitioned_grouped(n, BITS_PER_KEY, &keys)
            })
        });
        #[cfg(target_arch = "x86_64")]
        g.bench_function(BenchmarkId::from_parameter("partitioned_grouped_nt"), |b| {
            b.iter_with_large_drop(|| {
                BlockedFilter::build_partitioned_grouped_nt(n, BITS_PER_KEY, &keys)
            })
        });
        g.finish();
    }
}

criterion_group! {
    name = benches;
    config = Criterion::default();
    targets = bench_builders
}
criterion_main!(benches);
