#!/usr/bin/env bash
set -euo pipefail
SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/edit_svg.sh"
tmp="$(mktemp -d)"; cd "$tmp"
fail=0

# newest *.svg is picked when no arg is given (DRY_RUN prints resolved abs path)
printf '<svg/>' > old.svg; sleep 1; printf '<svg/>' > new.svg
got="$(EDIT_DRY_RUN=1 bash "$SCRIPT")"
[ "$got" = "$tmp/new.svg" ] || { echo "FAIL newest: got '$got'"; fail=1; }

# explicit arg wins
got="$(EDIT_DRY_RUN=1 bash "$SCRIPT" old.svg)"
[ "$got" = "$tmp/old.svg" ] || { echo "FAIL explicit: got '$got'"; fail=1; }

# error when no svg present
empty="$(mktemp -d)"; cd "$empty"
if EDIT_DRY_RUN=1 bash "$SCRIPT" >/dev/null 2>&1; then echo "FAIL empty: expected nonzero"; fail=1; fi

[ "$fail" = 0 ] && echo "ALL PASS" || exit 1
