# Common errors — LaTeX/TikZ log → fix

When `compile.sh` fails, read `figure.log` and match the message here. The real
error is usually the FIRST `!` line, not the last line of output.

| log message | cause | fix |
|-------------|-------|-----|
| `! LaTeX Error: File 'pgfplots.sty' not found` | package missing | `tlmgr install pgfplots` (or circuitikz/chemfig/standalone) |
| `Package pgfplots Warning: running in backwards compatibility mode` | `compat` unset | already set `compat=1.18` in preamble; bump if features missing |
| `! Package pgfplots Error: Sorry, the requested ... type 'table'` | CSV header/columns mismatch | check column names match `x=`/`y=` keys; `col sep=comma` if comma-separated |
| `! Undefined control sequence. \addplot` | drew outside `axis` env, or forgot `\usepackage{pgfplots}` | wrap in `\begin{axis}`; check preamble |
| `! Dimension too large` | coordinates explode (often log of ≤0, or huge range) | clamp data; set explicit `xmin/xmax/ymin/ymax` |
| `! Package tikz Error: Giving up on this path. Did you forget a semicolon?` | missing `;` ending a `\draw`/`\node` | add the `;` |
| `Runaway argument` / `Paragraph ended before ...` | unbalanced `{ }` or `[ ]` | match brackets in the offending line |
| circuitikz: `Unknown bipole` | wrong `to[X]` key | check key in circuitikz-recipes.md table |
| compiles but PDF is huge/blank margins | not using `standalone` crop | use `\documentclass[border=2pt]{standalone}` |
| `dvisvgm ERROR: can't retrieve number of pages from file` | `--pdf` route needs mutool | `brew install mupdf-tools` |
| `! LaTeX Error: File 'luatex85.sty' not found` | engine is lualatex on BasicTeX | use pdflatex (scripts default to it); or `tlmgr install luatex85` |

## Self-check loop (always do this)
1. `compile.sh figure.tex` → if it errors, read `figure.log`, fix, repeat.
2. `preview.sh figure.pdf` → open the PNG and actually LOOK: axes labelled?
   units present? legend correct? colours distinguishable? nothing clipped?
3. Only then deliver.
