# v0.2.0 - Research and Engineering Focus

This release refocuses `tech-route-maker` on evidence-grounded editable technical route diagrams for research and engineering projects.

## Added

- Default presets for academic methods, thesis proposals, engineering systems and workflow pipelines.
- `route_version: 0.2.0` schema.
- Structured assumptions, unresolved questions and confidence fields.
- Explicit `is_inferred` flags for inferred route nodes.
- `QUALITY_REPORT.md` generation.
- CLI entry point: `trm`.
- Engineering energy system demo.
- Agent workflow demo.
- Schema migration guide.

## Changed

- README positioning narrowed from broad cross-domain diagrams to research and engineering route diagrams.
- User interaction policy now uses default presets instead of forcing long option selection.
- Advertising/campaign examples moved to legacy or experimental status.
- Demo gallery now focuses on academic paper, thesis proposal, engineering energy system and agent workflow routes.

## Validation

- Python source compile check.
- Example route JSON validation.
- Demo rendering for PPTX, SVG, Draw.io, Excalidraw, Mermaid, HTML, Markdown and JSON.
- `QUALITY_REPORT.md` generated for every core demo.
- CLI checks: `trm --help`, `trm doctor`, `trm validate`, `trm render`.