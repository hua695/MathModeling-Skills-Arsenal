#!/usr/bin/env bash
# export_svg.sh — TikZ -> SVG for visual editing (Inkscape / web canvas).
# Crossing into SVG forks the figure: see references/editing-guide.md
# (the .svg becomes the authoritative source; .tex is frozen).
# usage: bash export_svg.sh figure.tex
set -euo pipefail
src="${1:?usage: export_svg.sh figure.tex}"
dir="$(cd "$(dirname "$src")" && pwd)"
base="$(basename "${src%.tex}")"
cd "$dir"

# engine -> PDF, then dvisvgm reads the PDF (--pdf) into SVG.
#
# --no-fonts traces text to path outlines instead of emitting SVG <font>/<glyph>
# elements. SVG fonts are a deprecated feature that browser editors (Method Draw /
# svg-edit) cannot import — they silently drop the glyphs, mangling the figure and
# losing labels. Outlined text renders identically everywhere and round-trips
# losslessly through the editor. The trade-off: labels become paths, not editable
# text — but text edits belong in the .tex anyway (which stays the text source).
engine="${TIKZ_ENGINE:-pdflatex}"; command -v "$engine" >/dev/null 2>&1 || engine="pdflatex"
if command -v latexmk >/dev/null 2>&1; then
  latexmk -"$engine" -interaction=nonstopmode -halt-on-error "$base.tex" >/dev/null
  latexmk -c "$base.tex" >/dev/null 2>&1 || true
else
  "$engine" -interaction=nonstopmode -halt-on-error "$base.tex" >/dev/null
  rm -f "$base.aux" "$base.log" "$base.out" "$base.fls" "$base.fdb_latexmk" 2>/dev/null || true
fi
dvisvgm --pdf --no-fonts --output="$base.svg" "$base.pdf" >/dev/null 2>&1
touch "$base.svg.frozen"   # marker: this figure has forked to the SVG branch
echo "$dir/$base.svg"
