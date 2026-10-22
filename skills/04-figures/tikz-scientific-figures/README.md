# tikz-scientific-figures

A **Skill** (for Claude Code / Codex and compatible agents) that generates
**publication-grade scientific figures** with TikZ / PGFPlots — reproducible,
vector (PDF), and re-editable. You describe the figure in plain language; the
agent writes the `.tex`, compiles it, visually self-checks the result, and hands
back a PDF plus the editable source.

## What it can draw

- **Data plots** — line, scatter, bar (grouped/stacked), histogram, box/violin, log axis, heatmap, contour, 3D surface/scatter
- **Circuits** — resistors, capacitors, op-amps, RC/RLC (circuitikz)
- **Schematics** — flowcharts, block/signal diagrams, free-body & geometry
- **Biology** — immunofluorescence/tissue, cells, signaling pathways, plasmid/gene maps
- **Chemistry** — molecules, reaction schemes, energy profiles, lattices
- **Physics** — ray optics, Feynman diagrams, vector fields
- **Math** — commutative diagrams, Venn, number lines
- **CS / ML** — neural networks, system architecture, automata, trees, graphs, UML, ER, Gantt
- **Composition** — multi-panel (a)(b)(c), insets, significance markers, fit + CI bands, and annotating real microscopy/photo images

## Publication-grade by default

Vector output · colour-blind-safe palettes (Okabe–Ito / viridis) · journal sizing
(89 mm single / 183 mm double column, 7–9 pt) · units on every axis · LaTeX math ·
source always shipped alongside the PDF.

## Install

1. Copy the `tikz-scientific-figures/` folder into your agent's skills directory
   (e.g. `~/.claude/skills/`).
2. Install a LaTeX toolchain once. Run the bundled check for OS-specific hints:
   ```bash
   bash scripts/check_env.sh
   ```
   Needs: a LaTeX engine (`pdflatex`), `poppler` (preview); for SVG export
   `dvisvgm` + `mutool`. On Windows, **MiKTeX** auto-installs missing LaTeX
   packages on first compile.

## Use

Just ask the agent, e.g. *"draw a publication line chart from this data"* or
*"make an RC low-pass circuit diagram"*. See [`使用说明.md`](使用说明.md) for a
plain-language guide (Chinese).

## Editing

1. **Ask the agent** to change colours/ranges/data — it edits the `.tex`/`.csv` in place.
2. **Edit the source** — each `.tex` has a `TUNABLES` block; data plots read a `data.csv`.
3. **Visual polish** — `bash scripts/export_svg.sh figure.tex` then
   `bash scripts/edit_svg.sh figure.svg` opens a bundled local **Method Draw**
   editor; `Ctrl/Cmd+S` saves back to the SVG. (Once forked to SVG, the `.tex` is
   frozen — see `references/editing-guide.md`.)

## Layout

```
SKILL.md            workflow + publication rules + editing rules
assets/             preamble.tex, template, bundled Method Draw editor
scripts/            check_env · compile · preview · export_svg · edit_svg
references/         per-domain recipes + editing guide + error table
```

## License

The bundled Method Draw editor (`assets/method-draw/`) retains its own license
(see `assets/method-draw/LICENSE`).
