#!/usr/bin/env bash
# Build an anonymized artifact bundle for double-blind review (SEA-style: software must be
# linked anonymously). Writes anonymous-artifact.tar.gz in the current directory from the
# COMMITTED tree (git archive), with identifying files dropped and identifying strings replaced.
# Usage: scripts/make_anonymous_bundle.sh [git-ref, default HEAD]
# It then lists any remaining matches for the patterns below; read that list before uploading.
set -euo pipefail
REF="${1:-HEAD}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$PWD/anonymous-artifact.tar.gz"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
git -C "$ROOT" archive --prefix=artifact/ "$REF" | tar -x -C "$WORK"
cd "$WORK/artifact"
# files that identify the author or are not needed by a reviewer
rm -rf CITATION.cff LICENSE .zenodo.json CLAUDE.md docs/outreach-email-draft.md \
       docs/blog-post-draft.md docs/arxiv-submission-checklist.md \
       docs/Ribbon_Publication_Plan.md docs/Ribbon_2027_Publication_Strategy.pdf docs/vps-runbook.md \
       paper/main.pdf scripts/launch_aws_arm.sh scripts/bootstrap_remote.sh scripts/e*_remote.sh
PATTERN='Sam-Bodden|Brian|Integrallis|integrallis|bsbodden|barudb|CS265|/home/[a-z]+|/Users/[A-Za-z-]+|~/Code/[A-Za-z_/-]+'
grep -rIlE "$PATTERN" . | while read -r f; do
  perl -pi -e 's/Brian Sam-Bodden/Anonymous Author/g; s/Sam-Bodden/Anonymous/g; s/Integrallis Software/Anonymous Affiliation/g;
               s#https://github.com/integrallis/[A-Za-z_-]+#[link withheld for review]#g; s/integrallis/anonymous/gi;
               s/bsbodden/anonymous/g; s#/Users/[A-Za-z-]+#/home/user#g; s#/home/[a-z]+#/home/user#g' "$f"
done
echo "== remaining matches (review each by hand) =="
grep -rInE "$PATTERN" . | cut -c1-160 || echo "none"
cd "$WORK" && tar -czf "$OUT" artifact
echo "wrote $OUT ($(du -h "$OUT" | cut -f1)) from $REF"
