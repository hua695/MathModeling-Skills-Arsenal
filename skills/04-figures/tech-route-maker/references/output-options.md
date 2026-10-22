# Output Options

Use this reference when choosing or explaining output formats. Offer preset defaults first, then confirm final formats and target medium in one concise grouped choice.

Primary users are academic and engineering users who need editable paper, thesis, proposal, defense, method-framework, system, workflow, and engineering route diagrams. Campaign diagrams are legacy/experimental and should be used only when the user explicitly asks for them.

## Format menu

| id | File | Editable in | Strength | Constraint |
|---|---|---|---|---|
| pptx | `tech-route.pptx` | PowerPoint, WPS | Best for presentations and defenses | Must use native shapes, text, and lines |
| svg | `tech-route.svg` | Figma, Illustrator, Inkscape, browser | Best for high-resolution vector editing | Keep text/vector elements editable |
| drawio | `tech-route.drawio` | diagrams.net | Best for long-term technical maintenance | Use `mxCell` nodes and edges |
| drawio-code | `tech-route.drawio-code.xml` | diagrams.net XML editor | Best for copy-paste import into draw.io | Paste through Extras > Edit Diagram |
| excalidraw | `tech-route.excalidraw` | Excalidraw | Best for whiteboard review and lightweight edits | Use scene JSON, not an image |
| mermaid | `tech-route.mmd` | Any text editor, GitHub Markdown | Best for version control | Visual control is limited |
| html | `tech-route.html` | Browser and code editor | Best for interactive previews | Include node detail and evidence data |
| markdown | `TECH_ROUTE.md` | Any Markdown editor | Best for README/docs | Include Mermaid and evidence tables |
| json | `tech-route.json` | Any text editor | Best for re-rendering and theme changes | Treat as the source of truth |
| all | all of the above | mixed | Best for archival handoff | Slower and more files |

## Default selection rule

Use these defaults unless the user asks for advanced choices:

- Editable presentation figure: `pptx,svg,json`
- Paper or research figure: `svg,pptx,json`
- Maintainable system diagram: `drawio,svg,json`
- Copy-paste into Draw.io / diagrams.net: `drawio-code,drawio,svg,json`
- Documentation output: `markdown,mermaid,json`
- Long-term maintenance: add `drawio`
- Full archive: `pptx,svg,drawio,drawio-code,excalidraw,mermaid,html,markdown,json`

Ask one clarification question only when the target output is genuinely ambiguous.

## Source patterns

Public roadmap guidance emphasizes editable, reusable, and audience-specific outputs:
- ProductPlan frames technology roadmaps as high-level visual summaries for complex technology work and recommends audience-aware detail levels.
- Smartsheet describes roadmap outputs for migration, unifying systems, continuity, upgrades, and new infrastructure.
- Miro and Canva emphasize template selection, customization, collaboration, milestones, dependencies, and visual communication.
- diagrams.net uses an XML-based editable diagram format and can export SVG/PDF/PNG.
- diagrams.net / Draw.io is available at <https://app.diagrams.net/>. For copy-paste usage, generate `drawio-code`, copy `tech-route.drawio-code.xml`, then paste it through **Extras > Edit Diagram**.

Use these as design patterns, not as copied template assets.
