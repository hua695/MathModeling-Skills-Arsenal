#!/usr/bin/env bash
# check_env.sh — verify the TikZ toolchain is present; print install hints.
# Run this FIRST when the skill is invoked on a fresh machine.
set -u
ok=1
check() { # name  cmd  hint  [optional]
  if command -v "$2" >/dev/null 2>&1; then
    printf '  [ok]   %-10s %s\n' "$1" "$(command -v "$2")"
  elif [ "${4:-}" = "optional" ]; then
    printf '  [opt]  %-10s %s\n' "$1" "$3"
  else
    printf '  [MISS] %-10s %s\n' "$1" "$3"; ok=0
  fi
}

echo "TikZ scientific-figures toolchain:"
check "pdflatex" pdflatex "LaTeX engine (required; or lualatex)"
check "dvisvgm"  dvisvgm  "TikZ -> SVG export (visual-edit channel)"
check "mutool"   mutool   "PDF reader dvisvgm --pdf needs (mupdf-tools)"
check "pdftoppm" pdftoppm "PDF -> PNG self-check preview (poppler)"
check "latexmk"  latexmk  "optional — scripts fall back to running the engine twice" optional
check "lualatex" lualatex "optional engine (pdflatex used if absent)" optional

echo
if [ "$ok" -eq 1 ]; then
  echo "Core packages (required by most recipes):"
  for p in pgfplots.sty circuitikz.sty standalone.cls chemfig.sty siunitx.sty; do
    if kpsewhich "$p" >/dev/null 2>&1; then echo "  [ok]   $p"; else echo "  [MISS] $p  -> tlmgr install ${p%.*}"; fi
  done
  echo "Optional packages (nicer variants; recipes have core-TikZ fallbacks):"
  for p in tikz-cd.sty pgfgantt.sty forest.sty tikz-feynman.sty mhchem.sty; do
    if kpsewhich "$p" >/dev/null 2>&1; then echo "  [ok]   $p"; else echo "  [opt]  $p  -> tlmgr install ${p%.*}"; fi
  done
  echo "  (to unlock all: sudo tlmgr install tikz-cd pgfgantt forest tikz-feynman mhchem)"
else
  case "$(uname -s)" in
    Darwin) cat <<'EOF'
Missing tools. macOS install (Homebrew):
  brew install --cask basictex      # ~130MB LaTeX
  brew install mupdf-tools poppler  # mutool (SVG export) + pdftoppm (preview)
  eval "$(/usr/libexec/path_helper)" # or open a new terminal
  sudo tlmgr update --self
  sudo tlmgr install pgfplots circuitikz standalone chemfig siunitx dvisvgm
  # optional (nicer variants): sudo tlmgr install tikz-cd pgfgantt forest tikz-feynman mhchem
  # full alternative (~4GB): brew install --cask mactex-no-gui
EOF
      ;;
    MINGW*|MSYS*|CYGWIN*) cat <<'EOF'
Missing tools. Windows install — run these scripts from Git Bash or WSL.
  Recommended (MiKTeX auto-installs LaTeX packages on first use — no tlmgr needed):
    choco install miktex git poppler     # (or download MiKTeX installer + Git for Windows)
    choco install mupdf                   # provides mutool (for SVG export)
  Then reopen Git Bash so the tools are on PATH. dvisvgm ships with MiKTeX.
  No Chocolatey? Use scoop:  scoop install latex git poppler mupdf
  TeX Live for Windows is an alternative to MiKTeX (bundles dvisvgm too).
EOF
      ;;
    *) cat <<'EOF'
Missing tools. Linux install (Debian/Ubuntu):
  sudo apt-get install texlive-latex-extra texlive-pictures dvisvgm \
                       mupdf-tools poppler-utils latexmk
  # optional (nicer variants):
  sudo apt-get install texlive-science   # tikz-cd, pgfgantt, etc.
  # Fedora: sudo dnf install texlive-scheme-medium dvisvgm mupdf poppler-utils
EOF
      ;;
  esac
fi
