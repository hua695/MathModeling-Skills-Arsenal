# Examples And Gallery

This gallery shows the core research and engineering scenarios supported by `tech-route-maker`. Each demo includes a source brief, `tech-route.json`, editable outputs, and a quality report. SVG, PPTX, Draw.io, Draw.io copy-code XML, HTML, Markdown and JSON are generated from the same route model.

The optional `assets/github-visual-preview.png` image on the repository homepage is a generated visual preview only. It is not used as the editable diagram source.

| Demo | Audience | Layout | Style | Preview |
|---|---|---|---|---|
| [Academic paper method route](academic-paper-demo/) | Chinese paper or defense | Chinese research method matrix | Blue-green proposal | [SVG](academic-paper-demo/outputs/tech-route.svg) |
| [Thesis proposal technical route](thesis-proposal-demo/) | Chinese thesis, opening report, research plan | Chinese proposal poster route | Polished pastel academic | [SVG](thesis-proposal-demo/outputs/tech-route.svg) |
| [Chinese grant application route](chinese-grant-application-demo/) | Grant, project application, reviewer-facing route | Chinese grant application route | Soft grant report | [SVG](chinese-grant-application-demo/outputs/tech-route.svg) |
| [Engineering energy system route](engineering-energy-system-demo/) | Engineering report or course design | Chinese wide project map | Blue-green proposal | [SVG](engineering-energy-system-demo/outputs/tech-route.svg) |
| [Biomedical mechanism route](biomedical-mechanism-demo/) | Biomedical proposal or paper | Chinese proposal poster route | Polished pastel academic | [SVG](biomedical-mechanism-demo/outputs/tech-route.svg) |
| [Draw.io copy-code HGDY route](drawio-copy-code-demo/) | Project application / Draw.io handoff | Chinese grant application route | Soft grant report | [XML](drawio-copy-code-demo/outputs/tech-route.drawio-code.xml) |
| [Agent workflow route](agent-workflow-demo/) | Skill/tool documentation | Horizontal stages | Minimal gray | [SVG](agent-workflow-demo/outputs/tech-route.svg) |

## Legacy / Experimental

`legacy-campaign-route-demo/` is retained for users who explicitly need campaign or advertising route diagrams. It is not part of the default gallery.

## Render All Demo Outputs

```bash
python scripts/render_all.py examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs --formats pptx,svg,drawio,drawio-code,html,markdown,json
python scripts/render_all.py examples/thesis-proposal-demo/outputs/tech-route.json examples/thesis-proposal-demo/outputs --formats pptx,svg,drawio,drawio-code,html,markdown,json
python scripts/render_all.py examples/chinese-grant-application-demo/outputs/tech-route.json examples/chinese-grant-application-demo/outputs --formats pptx,svg,drawio,drawio-code,html,markdown,json
python scripts/render_all.py examples/engineering-energy-system-demo/outputs/tech-route.json examples/engineering-energy-system-demo/outputs --formats pptx,svg,drawio,drawio-code,html,markdown,json
python scripts/render_all.py examples/biomedical-mechanism-demo/outputs/tech-route.json examples/biomedical-mechanism-demo/outputs --formats pptx,svg,drawio,drawio-code,html,markdown,json
python scripts/render_all.py examples/drawio-copy-code-demo/outputs/tech-route.json examples/drawio-copy-code-demo/outputs --formats pptx,svg,drawio,drawio-code,html,markdown,json
python scripts/render_all.py examples/agent-workflow-demo/outputs/tech-route.json examples/agent-workflow-demo/outputs --formats pptx,svg,drawio,drawio-code,html,markdown,json
```

## What To Compare

- PPTX: editable slide shapes.
- SVG: vector preview and design-tool editing.
- Draw.io: long-term technical maintenance.
- Draw.io code: copy `tech-route.drawio-code.xml` into [diagrams.net / draw.io](https://app.diagrams.net/) through **Extras > Edit Diagram**.
- HTML: interactive reading and evidence inspection.
- JSON: source of truth for rerendering.
- `QUALITY_REPORT.md`: warnings and manual review checklist.
