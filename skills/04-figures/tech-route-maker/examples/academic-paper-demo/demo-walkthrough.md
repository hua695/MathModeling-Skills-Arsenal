# Demo Walkthrough: Academic Paper Method Route

Detailed guides:

- [English](demo-walkthrough.en.md)
- [中文](demo-walkthrough.zh-CN.md)

## User Request

```text
Use $tech-route-maker to turn examples/academic-paper-demo/brief.md into an editable academic technical route diagram.
```

## Confirmed Choices

- Discipline: computer science and renewable-energy engineering.
- Subfield: multimodal photovoltaic defect detection.
- Target: paper/defense method figure.
- Preset: `academic-paper-framework-cn`.
- Layout: `cn-research-method-matrix`.
- Style: `research-ppt-blue`.
- Formats: PPTX, SVG, Draw.io, Draw.io code, Excalidraw, Mermaid, HTML, Markdown and JSON.

## Commands

```bash
python -m pip install -e .
trm ingest examples/academic-paper-demo/brief.md --output-dir evidence-pack
trm validate examples/academic-paper-demo/outputs/tech-route.json --strict
trm render examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs --formats pptx,svg,drawio,drawio-code,excalidraw,mermaid,html,markdown,json
python scripts/verify_outputs.py examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs
```

The strict report should show complete domain context, verified source hashes, 100% evidence coverage, 0% inferred coverage and no unresolved questions.

## Required User Revision

The generated files are editable drafts. Review terminology, evidence locators, route logic, node wording, font sizes, colors and target-journal or defense-template requirements before formal use.
