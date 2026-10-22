# Editing guide — how users revise a figure

Three editing paths, layered from lowest to highest skill. Always deliver the
**`.tex` source + data file** alongside the PDF so any of these stays open.

## Path 1 — ask the model (default, zero TikZ knowledge)
User says "make series 2 a red dashed line", "set x-range to 0–100", "move the
capacitor left". Edit the existing `.tex`/`.csv` in place, recompile, re-preview.
NEVER redraw from scratch when a source file already exists — modify it.

## Path 2 — user edits the source by hand (for power users)
Every template has a `TUNABLES` block at the top (figure width, axis ranges,
colours). Point users there first — it covers ~80% of tweaks without reading TikZ.
For data plots, the real "edit" is **editing `data.csv`** and recompiling.

## Path 3 — visual editing (drag-and-drop, when source editing is not enough)
Export to SVG and open in a visual editor:
```bash
bash scripts/export_svg.sh figure.tex   # -> figure.svg (+ figure.svg.frozen marker)
```
- General diagrams / node graphs: **TikZiT** (round-trips clean `.tikz`) or **Inkscape**.
- Any figure: **Inkscape** / web canvas — free dragging of every element.
- Final export from the editor as PDF/SVG keeps vectors (still publication-grade).

## THE RULE — authoritative source switching (do not violate)
A figure lives in exactly ONE of two states. Track it; tell the user which one.

| state | authoritative source | who edits | how to tell |
|-------|----------------------|-----------|-------------|
| **TeX branch** (default) | `figure.tex` (+ csv) | model or user, recompile | no `.frozen` file |
| **SVG branch** (forked) | `figure.svg` | user in Inkscape only | `figure.svg.frozen` exists |

Once `export_svg.sh` has run and the user has hand-edited the SVG, the figure has
**forked to the SVG branch**: the `.tex` is now a frozen generator archive. Do NOT
re-edit the `.tex` and recompile — that silently discards the user's manual SVG work.
If the user wants further model-driven/parametric edits after forking, say so
explicitly and let them choose: keep editing the SVG, or abandon SVG edits and
return to the `.tex` branch.

Forking is one-way and intended for **final polish** (nudging an arrow, adding a
hand annotation). Do all structural/data/colour changes on the TeX branch first.

For interactive visual polish, run `bash scripts/edit_svg.sh figure.svg`: it
serves a bundled Method Draw at a local URL, auto-loads the SVG, and saves edits
straight back to `figure.svg` on Ctrl/Cmd+S. The figure stays on the SVG branch —
do not recompile the frozen `.tex` over these edits.
