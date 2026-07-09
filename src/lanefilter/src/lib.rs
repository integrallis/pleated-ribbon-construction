//! Prototype blocked filter + batch-probe strategies for experiment E0.
//!
//! The filter geometry deliberately matches the Apache Parquet split-block Bloom filter
//! (SBBF; arXiv:2101.01719, Parquet format spec): 256-bit blocks of eight 32-bit words,
//! k = 8, one bit per word, per-word salt multipliers. Matching a specified, productionized
//! design lets us cross-validate correctness/FPR against independent implementations and
//! against fastfilter_cpp's BlockedBloom rather than trusting generated code.
//!
//! What E0 varies is NOT the filter — only the *probe strategy* over the same bit array:
//!   - `check_batch_scalar`     one key at a time (how per-key APIs work)
//!   - `check_batch_prefetch`   two-phase address-compute + prefetch, then probe
//!                              (RocksDB MultiGet / barudb batch style)
//!   - `check_batch_lanes`      vertical, lane-structured: W=8 keys advance together through
//!                              hash → address → gather → test, written as plain scalar Rust
//!                              shaped for auto-vectorization (the FastLanes-inspired question)
//!
//! `check_batch_lanes_masked` additionally forces all block addresses through an AND mask so
//! the identical instruction stream can run L1-hot (mask = 0) or full-range (mask = !0):
//! the E0b memory-vs-compute control.

/// Parquet SBBF per-word salt constants (format spec / arXiv:2101.01719).
const SALT: [u32; 8] = [
    0x47b6137b, 0x44974d91, 0x8824ad5b, 0xa2b7289d, 0x705495c7, 0x2df1424b, 0x9efc4947,
    0x5c6bfb31,
];

/// Lanes processed together by the vertical strategies. 8 × u32 = one AVX2 register.
pub const LANES: usize = 8;

/// splitmix64 finalizer (Stafford variant 13) — the standard published 64-bit mixer.
/// Used to hash raw u64 keys before probing; identical cost in every strategy.
#[inline(always)]
pub fn mix64(mut z: u64) -> u64 {
    z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    z ^ (z >> 31)
}

/// Deterministic key stream for tests/benches (splitmix64 sequence from a fixed seed).
pub struct KeyStream(u64);

impl KeyStream {
    pub fn new(seed: u64) -> Self {
        Self(seed)
    }
}

impl Iterator for KeyStream {
    type Item = u64;
    fn next(&mut self) -> Option<u64> {
        self.0 = self.0.wrapping_add(0x9e37_79b9_7f4a_7c15);
        Some(mix64(self.0))
    }
}

#[repr(align(32))]
#[derive(Clone, Copy)]
pub struct Block(pub [u32; 8]);

pub struct BlockedFilter {
    blocks: Vec<Block>,
}

impl BlockedFilter {
    /// Filter sized to `bits_per_key * n_keys` bits, rounded up to whole 256-bit blocks.
    pub fn with_bits_per_key(n_keys: usize, bits_per_key: f64) -> Self {
        let bits = (n_keys as f64 * bits_per_key).ceil() as usize;
        let n_blocks = bits.div_ceil(256).max(1);
        Self {
            blocks: vec![Block([0u32; 8]); n_blocks],
        }
    }

    pub fn num_blocks(&self) -> usize {
        self.blocks.len()
    }

    pub fn size_bytes(&self) -> usize {
        self.blocks.len() * 32
    }

    /// Parquet SBBF block selection: fastrange on the high 32 bits of the mixed hash.
    #[inline(always)]
    fn block_index(&self, h: u64) -> usize {
        ((((h >> 32) as u64).wrapping_mul(self.blocks.len() as u64)) >> 32) as usize
    }

    /// Parquet SBBF mask: in word w, set bit (x * SALT[w]) >> 27 (top 5 bits → 0..31).
    #[inline(always)]
    fn mask(x: u32) -> [u32; 8] {
        let mut m = [0u32; 8];
        for w in 0..8 {
            m[w] = 1u32 << (x.wrapping_mul(SALT[w]) >> 27);
        }
        m
    }

    pub fn insert(&mut self, key: u64) {
        let h = mix64(key);
        let b = self.block_index(h);
        let m = Self::mask(h as u32);
        let blk = &mut self.blocks[b].0;
        for w in 0..8 {
            blk[w] |= m[w];
        }
    }

    #[inline(always)]
    pub fn check(&self, key: u64) -> bool {
        let h = mix64(key);
        let b = self.block_index(h);
        let m = Self::mask(h as u32);
        let blk = &self.blocks[b].0;
        let mut ok = true;
        for w in 0..8 {
            ok &= (blk[w] & m[w]) == m[w];
        }
        ok
    }

    /// Strategy 1: per-key probing, the way single-key APIs are used in a loop.
    pub fn check_batch_scalar(&self, keys: &[u64], out: &mut [bool]) {
        assert_eq!(keys.len(), out.len());
        for (k, o) in keys.iter().zip(out.iter_mut()) {
            *o = self.check(*k);
        }
    }

    /// Strategy 2: two-phase batch — compute all addresses and prefetch, then probe.
    /// This is the RocksDB-MultiGet / barudb approach.
    pub fn check_batch_prefetch(&self, keys: &[u64], out: &mut [bool]) {
        assert_eq!(keys.len(), out.len());
        const STRIDE: usize = 64;
        let mut hashes = [0u64; STRIDE];
        let mut idx = [0usize; STRIDE];
        for (kc, oc) in keys.chunks(STRIDE).zip(out.chunks_mut(STRIDE)) {
            let n = kc.len();
            for i in 0..n {
                hashes[i] = mix64(kc[i]);
                idx[i] = self.block_index(hashes[i]);
                #[cfg(target_arch = "x86_64")]
                unsafe {
                    core::arch::x86_64::_mm_prefetch(
                        self.blocks.as_ptr().add(idx[i]) as *const i8,
                        core::arch::x86_64::_MM_HINT_T0,
                    );
                }
            }
            for i in 0..n {
                let m = Self::mask(hashes[i] as u32);
                let blk = &self.blocks[idx[i]].0;
                let mut ok = true;
                for w in 0..8 {
                    ok &= (blk[w] & m[w]) == m[w];
                }
                oc[i] = ok;
            }
        }
    }

    /// Strategy 3: vertical / lane-structured batch probe. W = LANES keys move together
    /// through hash → address → load → test; every inner loop is over independent lanes,
    /// no early exit, written to be auto-vectorizable from plain scalar Rust.
    pub fn check_batch_lanes(&self, keys: &[u64], out: &mut [bool]) {
        self.check_batch_lanes_masked(keys, out, usize::MAX)
    }

    /// E0b control: identical instruction stream, block addresses forced through `addr_mask`.
    /// `addr_mask == usize::MAX` → normal full-range probing.
    /// `addr_mask == 0`          → every probe lands in block 0 (permanently L1-hot),
    /// bounding what the same code could do if memory were free.
    pub fn check_batch_lanes_masked(&self, keys: &[u64], out: &mut [bool], addr_mask: usize) {
        assert_eq!(keys.len(), out.len());
        let chunks = keys.chunks_exact(LANES);
        let ochunks = out.chunks_exact_mut(LANES);
        let rem = chunks.remainder();
        let orem_start = keys.len() - rem.len();

        for (kc, oc) in chunks.zip(ochunks) {
            let mut h = [0u64; LANES];
            let mut x = [0u32; LANES];
            let mut idx = [0usize; LANES];
            for l in 0..LANES {
                h[l] = mix64(kc[l]);
            }
            for l in 0..LANES {
                x[l] = h[l] as u32;
                idx[l] = self.block_index(h[l]) & addr_mask;
            }
            // Accumulate misses per lane across the 8 words; branch-free.
            let mut ok = [true; LANES];
            for w in 0..8 {
                for l in 0..LANES {
                    let m = 1u32 << (x[l].wrapping_mul(SALT[w]) >> 27);
                    ok[l] &= (self.blocks[idx[l]].0[w] & m) == m;
                }
            }
            for l in 0..LANES {
                oc[l] = ok[l];
            }
        }
        // Scalar tail.
        for (i, k) in rem.iter().enumerate() {
            out[orem_start + i] = self.check(*k);
        }
    }

    // ---------------- E1a bulk-construction strategies ----------------
    // All builders MUST produce bit-identical output to per-key insertion over the same key
    // set (OR is commutative); the unit tests enforce this before any timing is meaningful.

    /// E1a strategy 1: per-key insertion (the baseline; identical to insert() in a loop).
    pub fn build_perkey(n_keys: usize, bits_per_key: f64, keys: &[u64]) -> Self {
        let mut f = Self::with_bits_per_key(n_keys, bits_per_key);
        for &k in keys {
            f.insert(k);
        }
        f
    }

    /// E1a strategy 2: per-key insertion with two-phase prefetch batches (control: does
    /// memory-level parallelism alone close the gap?).
    pub fn build_perkey_prefetch(n_keys: usize, bits_per_key: f64, keys: &[u64]) -> Self {
        let mut f = Self::with_bits_per_key(n_keys, bits_per_key);
        const STRIDE: usize = 64;
        let mut hashes = [0u64; STRIDE];
        let mut idx = [0usize; STRIDE];
        for kc in keys.chunks(STRIDE) {
            let n = kc.len();
            for i in 0..n {
                hashes[i] = mix64(kc[i]);
                idx[i] = f.block_index(hashes[i]);
                #[cfg(target_arch = "x86_64")]
                unsafe {
                    core::arch::x86_64::_mm_prefetch(
                        f.blocks.as_ptr().add(idx[i]) as *const i8,
                        core::arch::x86_64::_MM_HINT_T0,
                    );
                }
            }
            for i in 0..n {
                let m = Self::mask(hashes[i] as u32);
                let blk = &mut f.blocks[idx[i]].0;
                for w in 0..8 {
                    blk[w] |= m[w];
                }
            }
        }
        f
    }

    /// Partition count such that each partition's filter span is ~1 MiB (≤ half of one
    /// P-core L2 on the dev box); always a power of two so partition = high bits of block.
    fn partition_shift(n_blocks: usize) -> u32 {
        const TARGET_BLOCKS_PER_PART: usize = (1 << 20) / 32; // 1 MiB of 32-byte blocks
        let parts = n_blocks.div_ceil(TARGET_BLOCKS_PER_PART).next_power_of_two();
        // shift applied to block index to get partition id
        (n_blocks.next_power_of_two().trailing_zeros()).saturating_sub(parts.trailing_zeros())
    }

    /// E1a strategy 3 (`partitioned`, H1): two-pass construction. Pass 1 scatters
    /// (block, hash32) pairs into partitions whose filter span is L2-resident; pass 2 replays
    /// each partition, doing cache-resident merges. Each filter line goes to RAM once, on
    /// natural eviction.
    pub fn build_partitioned(n_keys: usize, bits_per_key: f64, keys: &[u64]) -> Self {
        let mut f = Self::with_bits_per_key(n_keys, bits_per_key);
        let shift = Self::partition_shift(f.blocks.len());
        let n_parts = ((f.blocks.len() - 1) >> shift) + 1;

        // Pass 1a: count keys per partition (streaming read of keys).
        let mut counts = vec![0usize; n_parts + 1];
        let mut pairs: Vec<u64> = Vec::with_capacity(keys.len());
        for &k in keys {
            let h = mix64(k);
            let b = f.block_index(h) as u64;
            counts[(b as usize >> shift) + 1] += 1;
            pairs.push((b << 32) | (h & 0xffff_ffff));
        }
        for p in 1..counts.len() {
            counts[p] += counts[p - 1];
        }
        // Pass 1b: scatter pairs into partition order (counting sort by partition id).
        let mut ordered: Vec<u64> = vec![0; pairs.len()];
        let mut cursor = counts.clone();
        for &pair in &pairs {
            let p = (pair >> 32) as usize >> shift;
            ordered[cursor[p]] = pair;
            cursor[p] += 1;
        }
        drop(pairs);
        // Pass 2: per partition, merge into the (now cache-resident) filter span.
        for p in 0..n_parts {
            for &pair in &ordered[counts[p]..counts[p + 1]] {
                let b = (pair >> 32) as usize;
                let m = Self::mask(pair as u32);
                let blk = &mut f.blocks[b].0;
                for w in 0..8 {
                    blk[w] |= m[w];
                }
            }
        }
        f
    }

    /// E1a strategy 4 (`partitioned_grouped`, H2): as strategy 3, but pass 2 additionally
    /// groups each partition's pairs by exact block (second-level counting sort, streaming),
    /// then accumulates each block's full 8-word mask in registers and issues ONE store per
    /// block — the filter array is written exactly once and never read. The accumulate loop
    /// is lane-structured plain code (the transposition candidate).
    pub fn build_partitioned_grouped(n_keys: usize, bits_per_key: f64, keys: &[u64]) -> Self {
        let mut f = Self::with_bits_per_key(n_keys, bits_per_key);
        let shift = Self::partition_shift(f.blocks.len());
        let n_parts = ((f.blocks.len() - 1) >> shift) + 1;

        let mut counts = vec![0usize; n_parts + 1];
        let mut pairs: Vec<u64> = Vec::with_capacity(keys.len());
        for &k in keys {
            let h = mix64(k);
            let b = f.block_index(h) as u64;
            counts[(b as usize >> shift) + 1] += 1;
            pairs.push((b << 32) | (h & 0xffff_ffff));
        }
        for p in 1..counts.len() {
            counts[p] += counts[p - 1];
        }
        let mut ordered: Vec<u64> = vec![0; pairs.len()];
        let mut cursor = counts.clone();
        for &pair in &pairs {
            let p = (pair >> 32) as usize >> shift;
            ordered[cursor[p]] = pair;
            cursor[p] += 1;
        }
        drop(pairs);

        let part_blocks = 1usize << shift;
        let mut bcounts = vec![0usize; part_blocks + 1];
        let mut bordered: Vec<u64> = Vec::new();
        for p in 0..n_parts {
            let slice = &ordered[counts[p]..counts[p + 1]];
            let base = p << shift;
            let span = part_blocks.min(f.blocks.len() - base);
            // Group by exact block within the partition (counting sort, L2-resident data).
            bcounts[..=span].fill(0);
            for &pair in slice {
                bcounts[((pair >> 32) as usize - base) + 1] += 1;
            }
            for b in 1..=span {
                bcounts[b] += bcounts[b - 1];
            }
            bordered.clear();
            bordered.resize(slice.len(), 0);
            let mut bcursor: Vec<usize> = bcounts[..=span].to_vec();
            for &pair in slice {
                let b = (pair >> 32) as usize - base;
                bordered[bcursor[b]] = pair;
                bcursor[b] += 1;
            }
            // Register-resident merge: one store per block, never a read of the filter.
            for b in 0..span {
                let group = &bordered[bcounts[b]..bcounts[b + 1]];
                if group.is_empty() {
                    continue;
                }
                let mut acc = [0u32; 8];
                for &pair in group {
                    let x = pair as u32;
                    for w in 0..8 {
                        acc[w] |= 1u32 << (x.wrapping_mul(SALT[w]) >> 27);
                    }
                }
                f.blocks[base + b].0 = acc;
            }
        }
        f
    }

    /// Measured FPR on `probes` keys known to be absent. Returns (false_positives, probes).
    pub fn measure_fpr(&self, absent_keys: impl Iterator<Item = u64>) -> (usize, usize) {
        let mut fp = 0usize;
        let mut n = 0usize;
        for k in absent_keys {
            fp += self.check(k) as usize;
            n += 1;
        }
        (fp, n)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn build(n: usize, bpk: f64) -> (BlockedFilter, Vec<u64>) {
        let keys: Vec<u64> = KeyStream::new(0xA11CE).take(n).collect();
        let mut f = BlockedFilter::with_bits_per_key(n, bpk);
        for &k in &keys {
            f.insert(k);
        }
        (f, keys)
    }

    #[test]
    fn no_false_negatives_all_strategies() {
        let (f, keys) = build(100_000, 10.0);
        let mut out = vec![false; keys.len()];
        f.check_batch_scalar(&keys, &mut out);
        assert!(out.iter().all(|&b| b), "scalar strategy false negative");
        f.check_batch_prefetch(&keys, &mut out);
        assert!(out.iter().all(|&b| b), "prefetch strategy false negative");
        f.check_batch_lanes(&keys, &mut out);
        assert!(out.iter().all(|&b| b), "lanes strategy false negative");
    }

    #[test]
    fn strategies_agree_bit_for_bit() {
        let (f, _) = build(50_000, 10.0);
        // Mix of members and non-members, including a non-multiple-of-8 length tail.
        let probes: Vec<u64> = KeyStream::new(0xBEEF).take(10_003).collect();
        let mut a = vec![false; probes.len()];
        let mut b = vec![false; probes.len()];
        let mut c = vec![false; probes.len()];
        f.check_batch_scalar(&probes, &mut a);
        f.check_batch_prefetch(&probes, &mut b);
        f.check_batch_lanes(&probes, &mut c);
        assert_eq!(a, b, "prefetch disagrees with scalar");
        assert_eq!(a, c, "lanes disagrees with scalar");
    }

    #[test]
    fn masked_hot_variant_is_same_code_different_addresses() {
        let (f, _) = build(50_000, 10.0);
        let probes: Vec<u64> = KeyStream::new(0xBEEF).take(8_000).collect();
        let mut full = vec![false; probes.len()];
        let mut hot = vec![false; probes.len()];
        f.check_batch_lanes_masked(&probes, &mut full, usize::MAX);
        f.check_batch_lanes_masked(&probes, &mut hot, 0);
        // Hot variant probes block 0 only — results differ; it exists only as a
        // throughput control and must never be reported as a filter result.
        let _ = (full, hot);
    }

    /// E1a correctness gate: every bulk builder must produce output bit-identical to
    /// per-key insertion over the same keys. OR is commutative — any deviation is a bug.
    #[test]
    fn builders_bit_identical() {
        for n in [10_000usize, 300_000, 1_000_000] {
            let keys: Vec<u64> = KeyStream::new(0xA11CE).take(n).collect();
            let a = BlockedFilter::build_perkey(n, 10.0, &keys);
            let b = BlockedFilter::build_perkey_prefetch(n, 10.0, &keys);
            let c = BlockedFilter::build_partitioned(n, 10.0, &keys);
            let d = BlockedFilter::build_partitioned_grouped(n, 10.0, &keys);
            for (name, other) in [("prefetch", &b), ("partitioned", &c), ("grouped", &d)] {
                assert_eq!(a.blocks.len(), other.blocks.len(), "{name}: block count differs");
                for i in 0..a.blocks.len() {
                    assert_eq!(
                        a.blocks[i].0, other.blocks[i].0,
                        "{name}: block {i} differs at n={n}"
                    );
                }
            }
        }
    }

    /// Honesty guard: measured FPR must sit near the SBBF design point and must NOT
    /// beat information-theoretic bounds. SBBF at 16 bytes/32 keys ≈ 10.7 bits/key is
    /// specified around ~1% FPR; block imbalance makes it worse than ideal Bloom, never better.
    #[test]
    fn fpr_within_theory() {
        let n = 1_000_000;
        let (f, _) = build(n, 10.0);
        let absent = KeyStream::new(0xD15EA5E).skip(0).take(1_000_000).map(|k| k ^ 0x5555_5555_5555_5555);
        let (fp, total) = f.measure_fpr(absent);
        let fpr = fp as f64 / total as f64;
        let bits_per_key = f.size_bytes() as f64 * 8.0 / n as f64;
        // Any filter bound: fpr >= 2^-bits_per_key.
        let info_floor = 2f64.powf(-bits_per_key);
        assert!(
            fpr >= info_floor,
            "measured FPR {fpr} beats the information-theoretic floor {info_floor} — measurement bug"
        );
        // Sanity ceiling: at ~10 bits/key SBBF should be low single-digit percent.
        assert!(
            fpr > 0.001 && fpr < 0.05,
            "measured FPR {fpr} implausible for SBBF at ~10 bits/key"
        );
    }
}
