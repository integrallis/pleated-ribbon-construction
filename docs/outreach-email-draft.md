# Outreach email to the Ribbon authors — DRAFT, not sent

Status: draft for Brian to edit and send himself. Nothing here has been sent to anyone.
Every number is from `CLAIMS.md` (row given in brackets in the notes below, not in the email).

**To:** Peter Dillinger, Stefan Walzer
**Consider cc:** Peter Sanders (see the note on conflicts below before adding him)
**Attach:** `paper/figures/strategies_100m.pdf` (one figure), and the PDF once it is rebuilt

---

**Subject:** Measuring the "sort S approximately" step of homogeneous ribbon — is this known to you?

Dear Peter, dear Stefan,

Algorithm 4 of your JACM paper (and Algorithm 3 of the BuRR technical report) sorts the keys by
s(x) "at least approximately" before insertion, with the row-operation bound for redundant
insertions as the reason. As far as I can tell, neither the fastfilter_cpp ribbon code nor
RocksDB does this: both band in arrival order behind the prefetch pipeline. I implemented the
step as a single counting-sort pass into cache-sized windows of start positions and measured
it around the unmodified fastfilter_cpp kernel. At 100M–400M keys on one x86 machine it
recovers 98.3–98.4% of the cache-miss reduction a full sort gives, at about a quarter of the
sort's cost, and homogeneous ribbon construction ends up 2.05–2.24× faster than the reference
build. The gain comes from the dependent row-reduction chains, which the prefetch pipeline
cannot hide; the same pass in front of RocksDB's Standard128 builder gives 1.62× at 10M keys
per filter and 1.78× at 100M, and nothing below about 1M.

I would be grateful for your view on two things before I post a preprint:

1. Is this already known to you, or implemented somewhere I have missed? I credit the
   approximate sort to your papers and claim only the implementation, the locality explanation
   and the measurement. I would rather be corrected now than in review.
2. Would a change along these lines be welcome in RocksDB, behind a size threshold so small
   filters take the existing path? What I have today is a measurement patch against v10.2.0,
   not something reviewable, and I would only do the work to make it so if you think it is
   worth your time.

The results come with their limits: against Bloom the build-cost gap narrows but does not
close (in RocksDB's filter_bench at matched false-positive rate, the pleated builder still
costs 2.4× the Bloom builder at 100M keys per filter), and the whole-compaction CPU change I
measured in db_bench is within run-to-run variation. The repository has the raw data, the
analysis scripts and a ledger tying each number to its artifact:
https://github.com/integrallis/ribbon-catches-bloom

One practical request. I am an independent author without a prior arXiv paper in cs.DS, so the
preprint needs an endorsement. If, after looking, either of you were comfortable endorsing it,
I would be grateful; if not, I understand entirely.

Thank you for the ribbon work, and for any time you can give this.

Best regards,
Brian Sam-Bodden
Integrallis Software

---

## Notes for Brian (not part of the email)

- **Numbers and their ledger rows:** 98.3–98.4% [C16]; 2.05–2.24× and "a quarter of the sort's
  cost" (reorder 5.5–6.1 vs 23.9–28.1 ns/key) [C17, C20]; RocksDB 1.62× / 1.78× and no gain
  below ~1M [C31]; 2.4× Bloom at 100M in filter_bench [C26]; compaction CPU within variation
  [C32].
- **Before sending:** read the JACM passage yourself (Algorithm 4 line 3; end of the proof of
  Lemma 5.3(b), p. 7:24) and the corrected lineage paragraph in `paper/main.tex`. The email's
  first sentence stands or falls on that reading.
- **Repository state:** the public repo should contain the prior-art correction before this
  goes out; at the time of writing those changes are uncommitted on `prior-art-corrections`.
  The public README still carries the old title until that branch is merged and pushed.
- **Conflicts:** Peter Sanders is a local organiser of SEA 2027. Anyone who has seen the draft
  and later sits on the PC is a conflict to declare at submission. That is a reason to be
  deliberate about the cc line, not a reason to avoid contact.
- **Open question worth raising if they reply:** for homogeneous ribbon every right-hand side
  is zero, so the solved filter looks order-independent with no independence condition at all
  (`docs/order-independence-proof.md`, last section). They can confirm or refute that in a
  line.
- **Endorsement mechanics:** arXiv issues an endorsement code when you start a submission in
  the category; the endorser enters it. Have the code ready to send in a follow-up.
