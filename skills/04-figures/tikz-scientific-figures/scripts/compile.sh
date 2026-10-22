#!/usr/bin/env bash
# compile.sh — build a standalone .tex into a cropped PDF.
# usage: bash compile.sh figure.tex
set -euo pipefail
src="${1:?usage: compile.sh figure.tex}"
dir="$(cd "$(dirname "$src")" && pwd)"
base="$(basename "${src%.tex}")"

# pdflatex is the publication default; override with TIKZ_ENGINE=xelatex|lualatex
# (e.g. for CJK/Unicode). pdflatex avoids the luatex85.sty dependency.
engine="${TIKZ_ENGINE:-pdflatex}"; command -v "$engine" >/dev/null 2>&1 || engine="pdflatex"
cd "$dir"
if command -v latexmk >/dev/null 2>&1; then
  # -halt-on-error so failures surface immediately; latexmk handles reruns.
  latexmk -"$engine" -interaction=nonstopmode -halt-on-error "$base.tex" >/dev/null
  latexmk -c "$base.tex" >/dev/null 2>&1 || true   # clean aux, keep the PDF
else
  # no latexmk (e.g. BasicTeX): run twice so references/labels settle.
  "$engine" -interaction=nonstopmode -halt-on-error "$base.tex" >/dev/null
  "$engine" -interaction=nonstopmode -halt-on-error "$base.tex" >/dev/null
  rm -f "$base.aux" "$base.log" "$base.out" "$base.fls" "$base.fdb_latexmk" 2>/dev/null || true
fi
echo "$dir/$base.pdf"
