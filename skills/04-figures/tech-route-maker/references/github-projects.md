# Open Source Project Notes

Use this reference to decide what can be reused or cited. Prefer dependencies and design patterns over copied code.

## Directly useful projects

| Project | License observed | Use in this skill |
|---|---:|---|
| `oh-my-mermaid/oh-my-mermaid` | MIT | Reference multi-perspective codebase scan and recursive architecture documentation patterns |
| `humbledshuttler/repodiagram` | MIT | Reference local repository to Mermaid/HTML pipeline design |
| `cedric-albeke/llm-diagrams` | MIT | Reference analyze -> reason -> layout -> render pipeline and multi-format targets |
| `mermaid-js/mermaid` | MIT | Use Mermaid as a text diagram target and Markdown-compatible representation |
| `excalidraw/excalidraw` | MIT | Use `.excalidraw` scene JSON as an editable whiteboard output target |
| `jgraph/drawio` | Apache-2.0 | Use `.drawio` XML as an editable diagrams.net output target |
| `gitbrent/PptxGenJS` | MIT | Reference PowerPoint generation concepts; this skill includes a stdlib fallback renderer |
| `c-narcissus/paper-framework-figure-studio-pro` | README states MIT-0 | Adapt paper-grounded figure workflow, subtype taxonomy, reader-first candidate planning, edge-label-first variables, density budgets, and figure-caption co-design |

## Limited-use projects

| Project | License observed | Use in this skill |
|---|---:|---|
| `alexanderop/walkthrough` | No clear GitHub license found during review | Study the user experience idea of clickable Mermaid plus node details, but do not copy code |

## Reuse policy

- If a project has MIT or Apache-2.0, it may be used as a dependency or inspiration when compatible with the user's repository license.
- Do not paste or vendor code from projects without a clear compatible license.
- Do not copy online roadmap template images or proprietary visual assets.
- Convert public design patterns into original editable shapes and JSON schema rules.

## Useful patterns to integrate

- Codebase scan first, diagram second.
- Keep a structured intermediate representation before rendering.
- Make rendered diagrams navigable or traceable.
- Support Mermaid for Markdown and a richer format for editing.
- Validate syntax and completeness after generation.
- For academic diagrams, deep-read the source before drawing and separate semantic audit graphs from visible render graphs.
- Plan caption/legend support and visible text budgets instead of putting paragraph text inside boxes.
