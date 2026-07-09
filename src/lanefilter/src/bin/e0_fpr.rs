//! Measures FPR + bits/key for our SBBF-geometry filter and fastbloom at the same memory
//! budget, printing a JSON summary to stdout. Run by experiments/e0_feasibility/run.py;
//! output is the raw artifact behind results/e0a/summary.json.

use fastbloom::BloomFilter;
use lanefilter::{BlockedFilter, KeyStream};

fn main() {
    let n: usize = std::env::args()
        .nth(1)
        .and_then(|s| s.parse().ok())
        .unwrap_or(1_000_000);
    let bits_per_key = 10.0f64;
    let total_bits = (n as f64 * bits_per_key) as usize;

    let members: Vec<u64> = KeyStream::new(0xA11CE).take(n).collect();
    let mut ours = BlockedFilter::with_bits_per_key(n, bits_per_key);
    let mut fb = BloomFilter::with_num_bits(total_bits).expected_items(n);
    for &k in &members {
        ours.insert(k);
        fb.insert(&k);
    }

    // Absent probes: disjoint deterministic stream (xor keeps it out of the member stream).
    let n_probes = 4_000_000usize;
    let absent = || {
        KeyStream::new(0xD15EA5E)
            .take(n_probes)
            .map(|k| k ^ 0x5555_5555_5555_5555)
    };

    // False negatives are a correctness bug, not a statistic — verify zero.
    assert!(members.iter().all(|k| ours.check(*k)), "our filter: false negative");
    assert!(members.iter().all(|k| fb.contains(k)), "fastbloom: false negative");

    let (fp_ours, tot) = ours.measure_fpr(absent());
    let fp_fb = absent().filter(|k| fb.contains(k)).count();

    let ours_bpk = ours.size_bytes() as f64 * 8.0 / n as f64;
    let fb_bpk = total_bits as f64 / n as f64;

    println!(
        concat!(
            "{{\"n_keys\": {}, \"n_probes\": {}, \"filters\": [\n",
            "  {{\"name\": \"lanefilter_sbbf\", \"family\": \"bloom\", \"bits_per_key\": {:.3}, ",
            "\"measured_fpr\": {:.6}, \"false_positives\": {}}},\n",
            "  {{\"name\": \"fastbloom_0.9\", \"family\": \"bloom\", \"bits_per_key\": {:.3}, ",
            "\"measured_fpr\": {:.6}, \"false_positives\": {}}}\n",
            "]}}"
        ),
        n,
        tot,
        ours_bpk,
        fp_ours as f64 / tot as f64,
        fp_ours,
        fb_bpk,
        fp_fb as f64 / n_probes as f64,
        fp_fb,
    );
}
