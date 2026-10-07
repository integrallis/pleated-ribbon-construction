# Blog post — DRAFT for Brian to rewrite in his own voice

Status: draft, 2026-10-06. Not published anywhere. Every number is from `CLAIMS.md`; the row is
in brackets and should be removed before publishing. Publish only after the arXiv version is
up, and link to it. One figure: `paper/figures/strategies_100m.pdf`.

---

## Ribbon filters build twice as fast if you group the keys first

A Bloom filter answers "is this key definitely not here?" in a handful of bits per key. A
ribbon filter answers the same question at the same error rate in about 30% less memory. In
RocksDB that is the trade on offer today: Ribbon saves the memory, and costs about four times
the CPU to build. Because every compaction rebuilds its filters, that build cost is the reason
Bloom is still the default.

I spent a few months finding out where that build time goes. The answer was not arithmetic.

### Where the time goes

Building a ribbon filter means solving a large, banded system of linear equations. Each key
picks a start position in a table and is reduced against whatever is already stored there, one
XOR at a time, until it lands in an empty slot. At 100 million keys the table is over a
gigabyte, each key starts somewhere effectively random in it, and each reduction step has to
finish before the next one knows where to look. The processor spends most of its time waiting
for memory: 5.8 cache misses per key, 0.64 instructions per cycle. [C14]

Prefetching helps less than you would hope, because you cannot prefetch an address you have not
computed yet. Bloom construction does not have this problem: each key's memory accesses are
independent, so the hardware overlaps them.

### The fix is one counting pass

If keys arrive in order of start position, the build walks the table front to back and
everything it touches is already in cache. Sorting gets you that, and sorting 100 million keys
costs about as much as it saves.

You do not need a sort. One counting pass that groups keys into windows of start positions,
each window small enough to fit in the L2 cache, recovers 98% of the cache-miss reduction of a
full sort at about a quarter of the cost. [C16, C17, C20] End to end, construction is 2.05×
faster at 100 million keys and 2.24× at 400 million, with the filter that comes out identical
to the one built in arrival order. [C17] It holds on two ARM cores as well, by a wider margin
(2.37× and 2.72×). [C28]

This is not my idea. The ribbon authors' own algorithm for this filter variant says to sort the
keys "at least approximately", for a different reason: a bound on wasted row operations. As far
as I can find, nobody had implemented that step or measured what it does to the cache. The
reference code and RocksDB both insert keys in the order they arrive.

### In RocksDB

The same pass, put in front of RocksDB's shipped ribbon builder, makes filter construction
1.62× faster at 10 million keys per filter and 1.78× at 100 million. [C31] Stock and pleated
builds produced byte-identical filters in every one of 443 filters I compared. [C33]

### What it does not do

- **It does not help small filters.** Below about a million keys the table already fits in
  cache and the extra pass is pure cost: 3% slower at 100K keys per filter. [C31] A real
  integration needs a size threshold.
- **It does not catch Bloom.** At the same error rate in RocksDB's own benchmark, the faster
  ribbon build still costs 2.4× what Bloom costs at 100 million keys per filter, down from
  4.5×. [C26] The gap halves; it does not close.
- **With many threads the gap gets wider, not narrower.** Bloom parallelizes almost for free.
  My parallel ribbon build only parallelizes one of its three phases, and at 16 threads it
  costs about 10× a 16-thread Bloom build. [C27]
- **I could not show a whole-compaction win.** Filter building was about 23% of compaction CPU
  in the one configuration I measured, and the total moved by 9%, which is inside the
  run-to-run noise of three runs. [C32]

Two things I tried first and that failed are in the paper too, because they explain why this
works: batching Bloom probes and batching Bloom construction both lose to the plain versions.
Their cache misses are independent, and the memory system already hides independent misses.
The trick only pays where one miss has to wait for another.

### Try it

Everything is in the repository: raw measurements, the scripts that turn them into every number
above, and the experiment protocols, which were committed before the data was collected.

    git clone <repo URL> && cd ribbon-catches-bloom && ./reproduce.sh

The paper is at <arXiv link>. The Rust implementation is the `pleat` crate.

---

## Notes for Brian (not part of the post)

- The headline "twice as fast" is true at 100M–400M keys against the reference build [C17]. It
  is not true for small filters; the post says so in the first caveat. Keep that caveat near
  the top if the post is shortened.
- "about four times the CPU" and "about 30% less memory" in the opening are RocksDB's own
  published figures as cited in the paper (140 vs 32 ns/key); check the wording against the
  RocksDB blog post before publishing, since that source was read through a summarizer.
- The research on comparable work found that a blog post reached far more readers than the
  bare arXiv link for the same result, and that small, portable code got ported within days.
