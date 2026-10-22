#!/usr/bin/env bash
# edit_svg.sh — open one SVG in a local Method Draw with save-back.
# usage: bash edit_svg.sh [figure.svg]   (no arg => newest *.svg in cwd)
# Set EDIT_DRY_RUN=1 to print the resolved absolute path and exit (used by tests).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
svg="${1:-}"
if [ -z "$svg" ]; then
  svg="$(ls -t ./*.svg 2>/dev/null | head -1 || true)"
  [ -n "$svg" ] || { echo "no .svg found in $(pwd)" >&2; exit 1; }
fi
[ -f "$svg" ] || { echo "no such svg: $svg" >&2; exit 1; }
abs="$(cd "$(dirname "$svg")" && pwd)/$(basename "$svg")"
if [ "${EDIT_DRY_RUN:-}" = "1" ]; then echo "$abs"; exit 0; fi
exec python3 "$here/edit_server.py" "$abs"
