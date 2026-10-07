# arXiv v1 checklist — DRAFT

Status: preparation only, 2026-10-06. Nothing has been uploaded. Plan target: November 2026,
after the prior-art correction is public and an endorser is found.

## Before uploading

- [ ] Read the JACM passage (Algorithm 4 line 3; end of the proof of Lemma 5.3(b), p. 7:24)
      against the lineage paragraph in `paper/main.tex`.
- [ ] Commit and push the `prior-art-corrections` work, so the public repo matches the paper.
- [ ] Tag a release; archive it (Zenodo DOI and a Software Heritage ID); put both in the
      paper's Artifacts paragraph and in `CITATION.cff`. `.zenodo.json` in the repo root holds
      the metadata Zenodo reads on release.
- [x] Rebuild `paper/main.pdf` from source with tectonic (done 2026-10-07; rebuild again after
      any further edit to the paper).
- [ ] Run `./reproduce.sh` once on a machine with the Rust toolchain and `uv`.
- [ ] Endorsement: start the submission to get the endorsement code for cs.DS, then send the
      code to the endorser (see `docs/outreach-email-draft.md`). Since 2026-01-21 an
      institutional email alone does not give automatic endorsement.

## Submission fields

- **Primary category:** cs.DS. **Cross-list:** cs.DB. (Subject to moderation.)
- **Title:** Pleated Ribbon Construction: Approximate Sorting Recovers the Locality of a Full
  Sort
- **Author:** Brian Sam-Bodden (Integrallis Software)
- **Abstract:** the abstract in `paper/main.tex` as it stands is about 1,590 characters with TeX
  markup removed; arXiv's limit is 1,920. Re-count after any edit.
- **Comments:** page count; "Code and data: <repo URL>, <DOI>".
- **License:** the choice is irrevocable for the version. arXiv's perpetual non-exclusive
  licence keeps every later venue open; CC BY 4.0 matches LIPIcs. Decide before uploading.

## Files

- `scripts/make_arxiv_bundle.sh` builds the upload: `dist/arxiv-source.tar.gz` (flat source with
  `main.bbl`, the style file, figures and generated tables; full-line comments stripped from
  `main.tex`), `dist/arxiv-preview.pdf` (compiled with pdfLaTeX from the bundle alone, as arXiv
  will), and `dist/arxiv-metadata.txt` (title, categories, comments line, plain-text abstract
  with its character count). `dist/` is ignored by git; rerun the script after any edit.
- The paper is in a NeurIPS preprint style, which is fine for arXiv. The LIPIcs build with author
  names (`scripts/make_lipics.py --named`) is the alternative if the preprint should look like
  the SEA submission.

## Double-blind interaction (SEA 2026 precedent; 2027 rules unpublished)

- An arXiv version was allowed; the submission may mention that a public version exists but
  must not link or cite it.
- Software must be linked anonymously in the submission (`scripts/make_anonymous_bundle.sh`).
- Do not post a new arXiv version or publicize during review if the 2027 call asks for that.

## After posting

- [ ] Add the arXiv identifier to `README.md`, `CITATION.cff` and the outreach follow-up.
- [ ] Blog post (`docs/blog-post-draft.md`) goes out with the arXiv link, not instead of it.
