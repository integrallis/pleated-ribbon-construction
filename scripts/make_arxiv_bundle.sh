#!/usr/bin/env bash
# Build the arXiv source bundle for the paper into dist/arxiv/ and dist/arxiv-source.tar.gz.
# The bundle is flat and self-contained: main.tex (full-line comments stripped), main.bbl,
# neurips_2026.sty, figures/*.pdf, tables/*.tex. It is then compiled from a clean copy with
# pdfLaTeX alone, the way arXiv will, and the result is checked for undefined references.
# Requires latexmk/pdflatex/bibtex and pandoc. Does not upload anything.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/dist/arxiv"
rm -rf "$OUT" "$ROOT/dist/arxiv-source.tar.gz" "$ROOT/dist/arxiv-check"
mkdir -p "$OUT/figures" "$OUT/tables"

# 1. sources (strip full-line comments from main.tex: arXiv source is public)
grep -v '^[[:space:]]*%' "$ROOT/paper/main.tex" > "$OUT/main.tex"
cp "$ROOT/paper/neurips_2026.sty" "$OUT/"
cp "$ROOT"/paper/figures/*.pdf "$OUT/figures/"
cp "$ROOT"/paper/tables/*.tex "$OUT/tables/"

# 2. bibliography: build main.bbl once, ship the .bbl and not the .bib
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
cp -R "$OUT/." "$WORK/"; cp "$ROOT/paper/refs.bib" "$WORK/"
( cd "$WORK" && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex >/dev/null 2>&1 )
cp "$WORK/main.bbl" "$OUT/main.bbl"

# 3. clean-room check: pdfLaTeX only, from the bundle alone
mkdir -p "$ROOT/dist/arxiv-check"; cp -R "$OUT/." "$ROOT/dist/arxiv-check/"
( cd "$ROOT/dist/arxiv-check" && for i in 1 2 3; do pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null; done )
if grep -qE "undefined|^! " "$ROOT/dist/arxiv-check/main.log"; then
  echo "bundle does not compile cleanly; see dist/arxiv-check/main.log" >&2; exit 1
fi
cp "$ROOT/dist/arxiv-check/main.pdf" "$ROOT/dist/arxiv-preview.pdf"
PAGES=$(pdfinfo "$ROOT/dist/arxiv-preview.pdf" | awk '/Pages/ {print $2}')
rm -rf "$ROOT/dist/arxiv-check"

# 4. tarball and metadata
( cd "$OUT" && tar -czf "$ROOT/dist/arxiv-source.tar.gz" . )
ABSTRACT=$(sed -n '/\\begin{abstract}/,/\\end{abstract}/p' "$ROOT/paper/main.tex" | sed '1d;$d' \
  | pandoc -f latex -t plain --wrap=none | tr '\n' ' ' | sed 's/  */ /g; s/^ //; s/ $//')
TITLE=$(awk '/\\title\{/,/\}$/' "$ROOT/paper/main.tex" | tr '\n' ' ' | sed 's/\\title{//; s/}[[:space:]]*$//; s/\\\\/ /g; s/  */ /g')
cat > "$ROOT/dist/arxiv-metadata.txt" <<META
Title:      $TITLE
Authors:    Brian Sam-Bodden
Categories: cs.DS (primary), cs.DB (cross-list)
Comments:   $PAGES pages, 4 figures, 6 tables. Code, raw measurements and registered protocols: https://github.com/integrallis/pleated-ribbon-construction
Abstract ($(printf '%s' "$ABSTRACT" | wc -c | tr -d ' ') characters; arXiv limit 1920):

$ABSTRACT
META
echo "bundle:   dist/arxiv-source.tar.gz ($(du -h "$ROOT/dist/arxiv-source.tar.gz" | cut -f1), $(tar -tzf "$ROOT/dist/arxiv-source.tar.gz" | grep -vc '/$') files)"
echo "preview:  dist/arxiv-preview.pdf ($PAGES pages, pdfLaTeX from the bundle alone)"
echo "metadata: dist/arxiv-metadata.txt"
