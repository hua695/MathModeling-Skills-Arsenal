#!/usr/bin/env bash
# preview.sh — render a PDF to PNG so the model can visually self-check.
# usage: bash preview.sh figure.pdf [dpi]
set -euo pipefail
pdf="${1:?usage: preview.sh figure.pdf [dpi]}"
dpi="${2:-200}"
out="${pdf%.pdf}.preview"
pdftoppm -png -r "$dpi" -singlefile "$pdf" "$out"
echo "$out.png"
