# Credit Prior Art, Then Target SEA

The plan is: fix the novelty framing and the ledger first, post to arXiv in November 2026 after securing a personal endorsement, submit to SEA 2027 around its projected early-February deadline, and run an adoption track (fastfilter_cpp, then RocksDB) in parallel. The existing strategy report's dates all check out and its lead venue is right, but three things in it do not survive the research. Its journal fallback, ACM JEA, appears closed to unsolicited submissions (secondary evidence, to be confirmed by hand). The partitioning idea it treats as the contribution is already in print: the 2026 JACM Ribbon paper and its 2022 technical report specify "sort S by s(x), at least approximately" for homogeneous ribbon, and the manuscript says the opposite without citing either. And SEA 2026 prohibited LLM-generated text other than polishing, a rule the report never mentions and that disclosure does not cure. The claim that survives is an implementation, mechanism and measurement claim, not an idea claim, and the paper's most probable reviewers wrote the line it must now credit. The breakout papers in this field succeeded through public code, a maintainer-channel announcement and a place in the shared benchmark harness rather than through venue rank, so the adoption track carries as much weight as the venue choice. Confidence labels below are the research notes' own: confirmed, secondary, precedent, unverified. Venue rankings, sequencing and "what to do" statements are judgments. No acceptance likelihood is stated anywhere.

## The existing report's dates hold; its fallback, novelty stance and scope do not

**Where it holds up.** Every date the report gives matches an official page: SEA 2027 on July 21-23, 2027 in Karlsruhe with the deadline still "TBD" (confirmed, [SEA 2027](https://sea2027.iti.kit.edu/)); PVLDB vol. 20 monthly deadlines through March 1, 2027 with June 1 as the final revision date for presenting in Athens (confirmed, [PVLDB vol. 20 guidelines](https://vldb.org/pvldb/volumes/20/submission/)); ICDE 2027 round 2 on November 11, 2026 with accept/reject only (confirmed, [ICDE 2027 CFP](https://icde2027.github.io/cf-research-papers.html)); SIGMOD 2027 round 4 abstract October 10 and paper October 17, 2026 (confirmed, [SIGMOD 2027 dates](https://2027.sigmod.org/calls_papers_important_dates.shtml)). Its judgments also stand: SEA is the natural audience, the current draft should not be rushed into SIGMOD, arXiv should follow a focused revision, DaMoN is archival, and all seven manuscript fixes are worth doing. The venue lineage supports the SEA call: BuRR appeared at SEA 2022 and PtrHash at SEA 2025, and the SEA 2026 preface lists "hashing and filtering data structures" among accepted topics (confirmed, [LIPIcs vol. 371 front matter](https://drops.dagstuhl.de/storage/00lipics/lipics-vol371-sea2026/LIPIcs.SEA.2026.0/LIPIcs.SEA.2026.0.pdf)).

**Where the research contradicts it.** The table below lists each point.

| Report position | What the research found | Label |
|---|---|---|
| ACM JEA is the first journal choice and the SEA fallback | Search snippets of the JEA page say it "is no longer accepting unsolicited submissions" and point authors to the Empirical Track of ACM TALG, which requires a repository link ([JEA home](https://dl.acm.org/journal/jea), [TALG guidelines](https://dl.acm.org/journal/talg/author-guidelines)). The page itself returned HTTP 403. | secondary |
| A SEA paper extends into JEA | SEA 2026 invited selected papers to a special issue of Algorithmica, by invitation ([LIPIcs vol. 371](https://drops.dagstuhl.de/storage/00lipics/lipics-vol371-sea2026/LIPIcs.SEA.2026.0/LIPIcs.SEA.2026.0.pdf)) | confirmed |
| "Read the JACM paper and identify what partitioning adds" | JACM Algorithm 4 line 3 and the proof of Theorem 5.3 already prescribe approximate sorting into buckets of consecutive start positions ([KIT open-access copy](https://publikationen.bibliothek.kit.edu/1000191446/177619178)) | confirmed |
| Proposition 1's free-coordinate gap is open | JACM footnote 19 gives the reference implementation's assignment (a free variable in row i gets p·i mod 2^r), a function of the slot index only ([KIT copy](https://publikationen.bibliothek.kit.edu/1000191446/177619178)) | confirmed in JACM; not yet checked against this repo's code |
| SEA preprint policy is the only SEA risk | SEA 2026 prohibited LLM-generated content except plots from experimental data and polishing of author-written text, with a mandatory disclosure checkbox ([SEA 2026 CFP](https://sea2026.github.io/cfp)) | precedent; exact wording to be re-read |
| arXiv endorsement "may" be required | Since January 21, 2026 an author without a prior arXiv paper in the domain needs a personal endorsement; an institutional email no longer suffices ([arXiv blog](https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/)) | confirmed |
| Six open venues | It omits SPAA 2027 cycle 2 (paper January 29, 2027; confirmed, [SPAA CFP](https://spaa.acm.org/spaa-2027-call-for-papers/)), ICDE Industry and Applications (December 1, 2026; confirmed, [ICDE dates](https://icde2027.github.io/important-dates.html)), SIGMOD Industrial (November 24, 2026; confirmed), EDBT cycle 3 (October 7, 2026; secondary, [MaDICS repost](https://www.madics.fr/event/conf615/)) and the ESA engineering track | as marked |
| No adoption plan | The report covers venues and arXiv only; the case studies show adoption, not venue, drove the breakouts | judgment |

One smaller correction: the JACM paper has five authors (Dietzfelbinger, Dillinger, Hübschle, Sanders, Walzer), Vol. 73 No. 1 Article 7, DOI 10.1145/3785417, published February 13, 2026 (confirmed, [ACM DL](https://dl.acm.org/doi/10.1145/3785417)). The ESA engineering track is now "Track E", not "Track B" (precedent, [ESA 2026](https://algo-conference.org/2026/esa/)).

## The approximate sort is in print, so the claim must narrow before anything is posted

### What is already published

The repo's ledger row C15 and `docs/prior-art-ribbon-construction.md` call partition-instead-of-sort "audit-verified open". That is inaccurate as worded. The BuRR technical report says "sort S approximately by s(x)" and explains that keys sorted "into buckets of b consecutive starting positions each" keep insertions short ([arXiv:2109.01892](https://arxiv.org/abs/2109.01892)); JACM repeats it. The stated purpose is a step bound for redundant insertions, not cache locality. The same papers state that the filled-slot set is invariant under insertion order, which anticipates part of the manuscript's order-independence proposition. Binary fuse filters already do a single-pass, coarse, cache-motivated partial sort by segment ([arXiv:2201.01174](https://arxiv.org/abs/2201.01174)), and a survey by the neighbouring community states the pattern as common knowledge: "Smaller parts fit better in cache and hence are faster to construct" ([arXiv:2506.06536](https://arxiv.org/abs/2506.06536)).

`paper/main.tex` line 54 currently reads "The ribbon paper's whole pitch was that you don't need the sort". That is accurate for Standard Ribbon, where the 2021 paper lists "no need to pre-sort the keys" as an advantage ([arXiv:2103.02515](https://arxiv.org/abs/2103.02515)), and wrong for Homogeneous Ribbon, the paper's main target. `paper/refs.bib` has no JACM entry.

### What remains new

No source read contains any of the following: an implementation of bucketed ordering for standard or homogeneous ribbon (the reference [fastfilter_cpp ribbon code](https://github.com/FastFilter/fastfilter_cpp/blob/master/src/ribbon/ribbon_impl.h) and [RocksDB's `ribbon_alg.h`](https://github.com/facebook/rocksdb/blob/main/util/ribbon_alg.h) insert in arrival order); a measurement of cache misses in banding; a cache-capacity rule for bucket width; an evaluation of the prefetch pipeline RocksDB ships under "TODO: verify/validate"; reordering in RocksDB's Standard128 builder; or parallel banding for a non-bumped ribbon. This rests on keyword searches and source reads, not a citation-graph crawl.

The honest headline is therefore (judgment): *the first implementation, mechanism-level explanation and cross-architecture measurement of coarse start-position partitioning as a cache-locality optimization for ribbon banding, including on a production builder whose design forgoes sorting.* The ledger supports the measurement half: 98.3%/98.4% recovery of the full sort's miss reduction (CLAIMS.md C16), 2.05×/2.24× over the reference prefetch-pipelined build and 1.68× over the best measured full sort (C17), the result holding against ips2ra (C20), window robustness (C22) and parallel scaling (C23).

### Changes required before posting

**Manuscript.** Cite JACM 2026 and the technical report at line 54 and in related work, quoting the approximate-sort line and stating its step-count rationale. Introduce "pleating" as the name for the cache-sized instance of the authors' approximate sort. State that the "reference" baseline is the reference *implementation*, which deviates from the published *algorithm* by not sorting. Promote binary fuse from background to closest analogue. Present the order-independence result as a corollary of the published invariance plus a deterministic free-variable rule, used as a correctness gate. Add the four missing references a reviewer from this group will expect: JACM, Vigna's ε-cost sharding ([arXiv:2503.18397](https://arxiv.org/abs/2503.18397)), Genuzio et al. (SEA 2016) and Belazzougui et al. ([arXiv:1312.0526](https://arxiv.org/abs/1312.0526)). Fix the parallel-BuRR quotation at line 38: the source says "A large portion", not "a large part" ([arXiv:2411.12365](https://arxiv.org/abs/2411.12365)). Do not imply pleating transfers to BuRR, whose bumping needs full bucket order. Resolve the title: the report's objection to "at Bloom Speed" stands.

**Repo.** CLAIMS.md has no row for the RocksDB experiment or the ARM replication, yet the manuscript and the existing report cite both (the report: "approximately 1.8x faster RocksDB Standard128 filter construction at 100 million keys per filter"). INTEGRITY.md says a claim with no row goes in no document, so these rows come first. C15 needs its status corrected. A byte-for-byte comparison of stock and pleated Standard128 output is the cheapest high-value addition; the manuscript itself says the E2 artifacts do not establish byte identity. Tag a release, mint a Zenodo DOI and a Software Heritage ID, and put them in the paper and `CITATION.cff`; LIPIcs supports a `swhid` field ([LIPIcs author instructions](https://submission.dagstuhl.de/styles/instructions/66)). Prepare an anonymized mirror for double-blind review. The paper directory currently holds a NeurIPS style file; SEA's precedent format is LIPIcs, 12 pages plus up to 5 pages of appendix (precedent, [SEA 2026 CFP](https://sea2026.github.io/cfp)). Per the repo's session rules, the author makes all commits.

## A dated sequence from October 2026 through ALENEX 2028

The sequence below is a judgment built on the dates in the notes. Projected dates are projections from prior editions, not published deadlines.

| When | Step | Basis and label |
|---|---|---|
| Oct 5-18, 2026 | Hand-verify the items in the last section. Apply the prior-art reframing. Add ledger rows and the byte-comparison test. Let EDBT cycle 3 (Oct 7) and SIGMOD round 4 (Oct 10/17) pass. | EDBT secondary; SIGMOD confirmed |
| Oct 19-31, 2026 | Email Dillinger and Walzer: two paragraphs, one figure, repo link, two questions (is this known to you; would a RocksDB PR be welcome). Ask for arXiv endorsement. Run a citing-paper sweep on BuRR and JACM. | judgment; endorsement rule confirmed |
| November 2026 | Post arXiv v1 (cs.DS primary, cs.DB cross-list) with DOI. Let ICDE round 2 (Nov 11) pass unless the database route is chosen. | ICDE confirmed |
| Nov-Dec 2026 | Open the fastfilter_cpp PR. Publish the blog post. Open a RocksDB issue or PR only if the maintainer welcomed it. | judgment |
| Weekly from now | Check the SEA 2027 CFP page for deadline, anonymity and AI rules. | page shows "TBD" (confirmed) |
| Late Jan to about Feb 2, 2027 | Submit to SEA 2027. | precedent: SEA 2025 and 2026 both extended to February 2 ([SEA 2025](https://regindex.github.io/sea2025.github.io/), [SEA 2026](https://sea2026.github.io/)) |
| About Mar 31, 2027 | SEA notification. | precedent |
| About Apr 21-23, 2027 | If rejected: ESA 2027 Track E. | precedent: ESA 2026 abstract Apr 21, paper Apr 23, notification Jun 26 ([ESA 2026](https://algo-conference.org/2026/esa/)) |
| About Jul 20, 2027 | If rejected again: ALENEX 2028. | precedent: ALENEX 2027 deadline Jul 20, 2026 (secondary); 2026 edition Jul 23, 2025 ([ALENEX26 CFP](https://easychair.org/cfp/ALENEX26)) |
| Jul 21-23, 2027 | SEA 2027, Karlsruhe; an author is expected to attend. | dates confirmed; attendance rule precedent |
| Any time | Journal route: TALG Empirical Track, as terminal fallback or extended version. Algorithmica only by SEA invitation. | secondary; confirmed for 2026 |

**Why SEA first.** Scope fit is direct, LIPIcs charges authors nothing (confirmed, [LIPIcs series page](https://www.dagstuhl.de/en/publishing/series/details/LIPIcs)), and lightweight double-blind rules tolerated a public arXiv version (precedent). For context only, and not as a forecast for this paper: SEA 2026 accepted 28 of 60 submissions and SEA 2025 27 of 62 (confirmed, [LIPIcs vol. 371](https://drops.dagstuhl.de/storage/00lipics/lipics-vol371-sea2026/LIPIcs.SEA.2026.0/LIPIcs.SEA.2026.0.pdf), [vol. 338](https://drops.dagstuhl.de/storage/00lipics/lipics-vol338-sea2025/LIPIcs.SEA.2025.0/LIPIcs.SEA.2025.0.pdf)); ALENEX 2027 accepted 24 of 72 (confirmed, [HotCRP](https://alenex2027.hotcrp.com/)). Peter Sanders is a local organiser of SEA 2027; the PC is unannounced. Anyone on the eventual PC who has seen the draft is a conflict to declare.

**The gate on SEA.** SEA 2026 restricted LLM-generated paper text to polishing of text the authors wrote themselves; the 2027 call is unpublished. The author will revise the manuscript text himself (decision of 2026-10-07), so recheck the 2027 wording against the revised text before submitting. ESA Track E, which was single-blind in 2026 (precedent), remains the fallback.

**The database alternative.** PVLDB rounds on December 1, 2026 and January 1, 2027 leave room for a revision before the June 1 cutoff (inference from the confirmed 2.5-month revision window). PVLDB is single-blind, so the public crate and video raise no anonymity issue, and no AI policy text appears in its guidelines (confirmed absence on the pages read). This route requires the report's item 7 first: the existing report itself records that the whole-compaction CPU change is within run-to-run variation in one filter-favourable configuration. A PVLDB rejection carries a one-year resubmission embargo there (confirmed). SIGMOD at a later round adds a $500 member or $750 non-member APC for authors outside ACM Open institutions (confirmed, [SIGMOD 2027 CFP](https://2027.sigmod.org/calls_papers_sigmod_research.shtml)). SPAA cycle 2 fits only if the parallel variant becomes the headline, and FAST needs a storage-system-level benefit the paper does not show.

## Breakout filter papers shipped code and a maintainer's post before the venue

Three papers outperformed their venue, measured against other filter papers at the same venue. Cuckoo Filter (CoNEXT 2014) has 831 Semantic Scholar citations against 274 for the highest SIGMOD filter paper in the sample; Xor Filters (JEA 2020) has 77 on Semantic Scholar and 212 on a co-author's Google Scholar profile; Ribbon has no refereed venue and 57, level with PVLDB filter papers of 2018-2019 (Semantic Scholar counts confirmed via API on 2026-10-04; Google Scholar counts secondary; [S2 API](https://api.semanticscholar.org/graph/v1/paper/arXiv:1912.08258?fields=title,year,venue,citationCount), [GS profile](https://scholar.google.ch/citations?user=OJeXexUAAAAJ&hl=en)). In every case with real adoption, public code existed before or with the paper. Morton Filter, whose code followed a year later, has PVLDB plus a journal version and no adoption found. Prefix Filter used the comparative-title formula at PVLDB and has 14 citations with a repo untouched since 2022 ([GitHub](https://github.com/TomerEven/Prefix-Filter)).

The channel mattered more than the artifact. The same Xor result drew 457 Hacker News points through Lemire's blog and 95 through the ACM link; Ribbon drew 216 through the Engineering at Meta post and 2 through arXiv (confirmed via HN API; [HN 21840821](https://news.ycombinator.com/item?id=21840821), [HN 27792558](https://news.ycombinator.com/item?id=27792558), [HN 26363737](https://news.ycombinator.com/item?id=26363737)). Ports appeared within five days of a post advertising a sub-300-line implementation ([Lemire blog](https://lemire.me/blog/2019/12/19/xor-filters-faster-and-smaller-than-bloom-filters/), [xorf](https://github.com/ayazhafiz/xorf)). Adoption and citations decouple: split-block Bloom is used by seven named systems and has 1 citation ([arXiv:2101.01719](https://arxiv.org/abs/2101.01719)); pdqsort has 2,507 stars and 24 ([GitHub](https://github.com/orlp/pdqsort)). The whole pattern is inferred from about a dozen cases, with no causal evidence.

The adoption track that follows from this (judgment) has four steps, in order.

**First, the maintainers.** Dillinger wrote the Ribbon series in RocksDB and was still committing in September 2026 (confirmed, [commit history](https://github.com/facebook/rocksdb/commits?author=pdillinger)). External Ribbon PRs that arrived cold have sat unreviewed, one since September 2022 (confirmed, [PR #10679](https://github.com/facebook/rocksdb/pull/10679)). Contact first; the same email serves the endorsement request and catches any misreading of their code before it is public.

**Second, fastfilter_cpp.** It is the community's comparison harness, was pushed on 2026-09-21, and already contains the homogeneous ribbon kernel the paper measures (confirmed, [fastfilter_cpp](https://github.com/FastFilter/fastfilter_cpp)). A pleated construction variant there reaches the people who benchmark filters, independent of Meta's review queue. Cuckoo's citation lead plausibly comes from being the baseline later papers must compare against; the harness is the equivalent route.

**Third, RocksDB.** The current patch is a measurement harness gated by environment variables, based on v10.2.0 while the latest release is v11.8.1 (confirmed, [releases](https://github.com/facebook/rocksdb/releases)). An upstreamable version strips the profiling, replaces the environment variable with a size threshold so small filters take the stock path, adds unit tests and the byte-identity test, and reports `db_bench` on a default-like configuration. RocksDB's review guidance states that "performance claims should be backed by empirical evidence" (confirmed, [RocksDB CLAUDE.md](https://github.com/facebook/rocksdb/blob/main/CLAUDE.md)). The size dependence recorded in `experiments/e2_rocksdb/README.md` is the objection to expect. No open RocksDB issue asking for cheaper Ribbon construction was found.

**Fourth, the public post.** Lead with a plain-language blog post carrying one figure, the reproduce command and the size caveat; submit that URL, not the PDF. Put a how-to-cite block in the README and keep a short reference implementation in the `pleat` crate; Hacker News readers objected to Ribbon's opacity and missing standalone library ([HN 27792558](https://news.ycombinator.com/item?id=27792558)). The explainer video is justified by reach: a randomized study found promoted papers downloaded 2.6-3.9 times more with no significant citation gain after three years ([PLOS ONE via PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10954115/)), and that evidence is biomedical, not CS. Realistic success metrics are ports, harness inclusion and an upstream merge; engineering papers with large adoption in the sample sit at 8-80 Semantic Scholar citations.

## Five decisions belong to the author

**Venue family.** SEA-first with adoption work in the gap, or the PVLDB route with a broadened RocksDB evaluation first. The two cannot run concurrently.

**Title and the name "pleating".** Keep the comparative title, which fits the field's convention, or adopt a title the evidence supports. Keep the coined name only if it is introduced as an instance of the published approximate sort.

**Outreach before posting.** Whether to contact the original authors first. The notes found no written norm either way; the benefits are endorsement, error-catching and a route to upstreaming, and the cost is a conflict to declare.

**arXiv licence.** The licence on a version is irrevocable (confirmed, [arXiv licence help](https://info.arxiv.org/help/license/index.html)). The non-exclusive licence is the conservative choice while the venue family is open.

**Budget and travel.** SEA expects an in-person presenter in Karlsruhe (precedent); SEA 2026 regular early registration was 4,200 DKK (precedent, [SEA 2026](https://sea2026.github.io/)). A TALG paper would incur an ACM journal APC whose 2027 amount is unresolved.

## What must be checked by hand

| Item | Why it matters | Where to check |
|---|---|---|
| JEA closed to unsolicited submissions; TALG Empirical Track terms | Decides the journal fallback. Secondary only. | [dl.acm.org/journal/jea](https://dl.acm.org/journal/jea), [TALG guidelines](https://dl.acm.org/journal/talg/author-guidelines) in a browser |
| JACM bucket-width bound | Extracted text differs between TR and JACM; decides whether the paper's windows satisfy it | Typeset PDF, Theorem 5.3 proof |
| Whether arXiv:2109.01892 v1 already had the approximate-sort line | Dating of the prior art | arXiv version history |
| Free-variable assignment in this repo's code versus JACM footnote 19 | Proposition 1 fix | `src/` and the fastfilter_cpp kernel |
| No approximate-sort option in the Dillinger fastfilter fork or `lorenzhs/BuRR` | The "never implemented" claim | Source read, or ask the authors |
| Citing papers of BuRR and JACM; RocksDB PR history; IEEE 9920402 | An implementation could exist that keyword search missed | Google Scholar, GitHub, IEEE Xplore |
| SEA 2026 LLM clause, exact wording, and whether it covers code | Read only through a summariser in one note | [SEA 2026 CFP](https://sea2026.github.io/cfp) |
| SEA 2027 deadline, anonymity, AI rules, PC, artifact evaluation | All unpublished | [SEA 2027 CFP](https://sea2027.iti.kit.edu/call-for-papers/) |
| ESA 2027, ALENEX 2028, DaMoN 2027 calls | Unpublished; fallback dates are projections | Venue sites when live |
| arXiv October 2026 rate limit details; cs endorsement thresholds | Post body could not be opened (unverified) | [arXiv blog](https://blog.arxiv.org/2026/10/01/updated-rate-limit-policy/) |
| ACM journal APC for 2027 | Two conflicting snippets | [ACM Open for authors](https://authors.acm.org/open-access/acm-open-for-authors-home) |
| Google Scholar citation counts | Read by a summarising model | Google Scholar by eye before printing |
| Chucky's "over 70%" write-path figure | Second-hand; its source was not opened | [Chucky PDF](https://nivdayan.github.io/chucky.pdf), reference 58 |
| RocksDB blog figures as quoted in the manuscript | Read through a summariser | [RocksDB blog](https://rocksdb.org/blog/2021/12/29/ribbon-filter.html) |
| Vigna "accepted to STOC 2025" | Unverified; do not repeat | arXiv record |
| ALENEX 2027 deadline of July 20, 2026 | Secondary (search snippet) | SIAM page in a browser |

## Conclusion

The research turns the paper's biggest exposure into its positioning. The people who wrote "at least approximately" are the likely reviewers, the arXiv endorsers and the RocksDB gatekeeper; one honest email to them serves all three purposes, and "we built and measured the step you specified" is a claim they can verify in minutes. An uncited overlap would read as unawareness or concealment to exactly that audience.

The second shift is in what success means. Ribbon itself reached PVLDB-level citations with no venue because it shipped in RocksDB, and split-block Bloom reached seven systems with one citation because it had no refereed record. This paper needs both halves: the SEA-family paper as the citable record, and a harness entry or upstream change as the thing people use. The ledger and published nulls are unusual in this subfield and are an asset only if every claim in the manuscript, the RocksDB and ARM results included, sits under them before the first public version.

## Status as of 2026-10-06 (added after the first work block)

This section records what has been done against the plan above and what has changed. The plan
text above is left as written on 2026-10-04.

### Done

| Plan item | State | Where |
|---|---|---|
| Prior-art reframing; JACM and technical-report citations; four missing references; quotation fix | Drafted, uncommitted | `paper/main.tex`, `paper/refs.bib`, `CLAIMS.md` C15, `docs/prior-art-ribbon-construction.md` |
| Title | Changed to "Pleated Ribbon Construction: Approximate Sorting Recovers the Locality of a Full Sort" | `paper/main.tex`, `README.md`, `CITATION.cff` |
| Ledger rows for the RocksDB and ARM results | Added, each derived by script from committed raw data | `CLAIMS.md` C28–C32 |
| Byte-for-byte comparison of stock and pleated Standard128 output | Run as registered experiment E5: 443 of 443 filters identical | `results/e5/`, C33 |
| Proposition 1 / free-coordinate gap | Statement corrected to match the kernel (free slots get a hash of the slot index, not zero) | `paper/main.tex`, `docs/order-independence-proof.md` |
| Window size versus the published bucket bound | Bound has an unspecified constant; banding instructions per key are the same in every order, now stated in the paper | `results/e1b/BANDING_STEPS_ANALYSIS.md` |
| Citing-paper sweep of BuRR, the 2021 ribbon paper and JACM | 93 distinct citing papers; none implements or measures the partitioned construction (title-level, one index) | `RESEARCH_LOG.md` |
| Outreach email | Drafted, not sent | `docs/outreach-email-draft.md` |
| LIPIcs build and anonymized artifact | Generator and bundle script written and tested | `scripts/make_lipics.py`, `paper/sea/`, `scripts/make_anonymous_bundle.sh` |
| arXiv preparation | Checklist and archive metadata written; nothing uploaded | `docs/arxiv-submission-checklist.md`, `.zenodo.json` |
| Blog post | Drafted, not published | `docs/blog-post-draft.md` |

### Added beyond the plan: the Bloom comparison, measured three ways

The plan treated the "Bloom speed" title as a wording problem. It was measured instead, with
protocols committed before data; the "matches Bloom" hypothesis was registered and failed each
time.

| Comparison | Result | Ledger |
|---|---|---|
| Same harness, one thread, 100M keys (i9) | ribbon goes from 4.4× to 2.2× the cost of blocked Bloom | C25 |
| RocksDB `filter_bench`, matched false-positive rate, one thread (EPYC-Milan) | pleated ribbon is 2.4× Bloom at 100M keys per filter, down from 4.5× stock | C26 |
| Equal thread counts, 100M keys (EPYC 9R14, 16 cores) | 4.0× at one thread, 10.1× at 16; only banding is parallel | C27 |

Consequence for positioning: the paper's claim is a construction-engineering one. It narrows
the single-thread gap to Bloom and does not close it, and parallel banding alone is not enough.

### Facts that changed since 2026-10-04

- **SEA 2026's LLM clause was read directly.** It prohibits LLM-generated paper content except
  plots from data and polishing of text "the authors have personally written". It does not
  mention code. The author will revise the manuscript text himself (decision of 2026-10-07).
- **The approximate-sort line is in v1 of the technical report** (September 2021), not only v2.
- **The JACM passage** is at the end of the proof of Lemma 5.3(b), p. 7:24; the algorithm's
  comment calls it "proof of Theorem 5.3".
- **Page budget.** Resolved on 2026-10-06 by moving the proof of Proposition 1 with its checks
  and the two registered Bloom experiments (E3, E4) into an appendix in the single paper source.
  The anonymous LIPIcs build is 16 pages: main text ends about 40% down page 13, references
  follow, and the appendix is pages 14-16 (three pages). Against SEA 2026's rule (12 pages
  excluding bibliography and front page, plus up to 5 pages of appendix) the main text is about
  11.8 pages if only the title-and-abstract block is excluded. That is inside the limit but
  close, and depends on how "front page" is read; recheck against the 2027 call.
- **Hetzner's dedicated-core quota** on this account stops at 8 cores; 16-core runs went to AWS.
- **SEA 2027** still shows "TBD" for the deadline and the call (checked 2026-10-06).

### Verification follow-up (2026-10-06, later the same day)

- **ACM JEA has stopped publishing: confirmed from dblp.** dblp's JEA page (updated 2026-10-06)
  lists records from 1996 to 2023 and ends at Volume 28, 2023; there is no later volume. That
  independently supports the search-snippet report that JEA ceased after 2023. Still not read
  directly: ACM's own page, which serves a bot check to automated browsers, and therefore the
  exact terms of the TALG Empirical Track that replaces it.
- **The 2022 IEEE ribbon paper (iSemantic 2022, DOI 10.1109/iSemantic55962.2022.9920402), read
  at abstract and outline level on IEEE Xplore.** It presents itself as "a further study" of the
  ribbon filter; its sections are related work, static functions and filters, ribbon retrieval
  and filter, and analysis. Nothing in the abstract or outline concerns sorting, partitioning
  or construction order. The full text is behind sign-in and was not read.
- **Order-independence without the independence condition, for homogeneous ribbon: supported
  by simulation.** An independent model of banding (`scripts/check_order_independence.py`)
  found the solved filter identical under every insertion order in 600 of 600 homogeneous
  instances that drop dependent rows, including all permutations of 200 tiny ones, while the
  non-homogeneous control differed as expected. Not a proof; the short argument in
  `docs/order-independence-proof.md` still wants a second reader, and the paper does not yet
  claim it.

### What only the author can do, in order

1. Read the JACM passage against the lineage paragraph; read the diff of `paper/main.tex`.
2. Revise the manuscript text (the author's own revision, decided 2026-10-07).
3. Commit the branch and push, so the public repository carries the prior-art correction.
4. Send the outreach email; request the arXiv endorsement.
5. Tag a release and archive it (Zenodo, Software Heritage); post arXiv v1 (plan: November).
6. Watch for the SEA 2027 call (projected deadline late January to about 2 February 2027).
7. After a reply from the maintainers: the fastfilter_cpp variant and an upstreamable RocksDB
   patch with a size threshold. Neither has been started; both wait on step 4.
