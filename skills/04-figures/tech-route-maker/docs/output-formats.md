# Output Formats

| Format | File | Editable in | Use when |
|---|---|---|---|
| PPTX | `tech-route.pptx` | PowerPoint, WPS | The user needs slides, defense material, teaching material or report edits. |
| SVG | `tech-route.svg` | Figma, Illustrator, Inkscape, browser | The user needs high-resolution vector editing. |
| Draw.io | `tech-route.drawio` | diagrams.net | The diagram must be maintained as a technical diagram. |
| Draw.io code | `tech-route.drawio-code.xml` | diagrams.net XML editor | The user wants XML code that can be copied into draw.io. |
| Excalidraw | `tech-route.excalidraw` | Excalidraw | The team wants a whiteboard-style editable scene. |
| Mermaid | `tech-route.mmd` | Text editor, GitHub Markdown | Version control and simple docs matter more than precise layout. |
| HTML | `tech-route.html` | Browser and code editor | The user wants an interactive preview with details. |
| Markdown | `TECH_ROUTE.md` | Markdown editor | The route belongs in README or docs. |
| JSON | `tech-route.json` | Text editor | The user wants to rerender or change themes later. |
| Quality report | `QUALITY_REPORT.md` | Markdown editor | Evidence coverage, inferred content and warnings need manual review. |

## Default Selection Rule

Offer the nearest preset, then confirm final output formats and target medium in one concise grouped choice. Allow single or multiple selections and do not silently guess delivery preferences.

Recommended defaults:

- Editable presentation figure: `pptx,svg,json`
- Paper or research figure: `svg,pptx,json`
- Maintainable system diagram: `drawio,svg,json`
- Copy-paste into Draw.io: `drawio-code,drawio,svg,json`
- Documentation output: `markdown,mermaid,json`
- Long-term maintenance: add `drawio`
- Full archive: `pptx,svg,drawio,drawio-code,excalidraw,mermaid,html,markdown,json`

## Manual Review

Generated outputs are editable drafts. Users should revise facts, terminology, visual hierarchy, spacing, color, and evidence wording before final use.
