# Complete English Walkthrough

## 1. Request

```text
Use $tech-route-maker to create an editable method-route figure from examples/academic-paper-demo/brief.md.
```

## 2. Source And Domain Confirmation

The agent inventories the source, extracts only explicit facts, and confirms the remaining delivery choices in one grouped question. This example uses:

- Computer science and renewable-energy engineering.
- Computer vision for photovoltaic defect detection.
- Multimodal RGB and infrared data.
- Deep-learning object detection and feature fusion.
- Paper/defense use.
- Chinese academic matrix layout with a restrained blue research style.

## 3. Evidence Model

Every visible node in `outputs/tech-route.json` references `source_1`, a locator that appears in `brief.md`, and the SHA-256 stored in `metadata.source_files` and `metadata.source_hashes`. Inference and evidence are never merged.

## 4. Validate And Render

```bash
python -m pip install -e .
trm ingest examples/academic-paper-demo/brief.md --output-dir evidence-pack
trm validate examples/academic-paper-demo/outputs/tech-route.json --strict
trm render examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs --formats pptx,svg,drawio,drawio-code,excalidraw,mermaid,html,markdown,json
python scripts/verify_outputs.py examples/academic-paper-demo/outputs/tech-route.json examples/academic-paper-demo/outputs
```

## 5. Editable Deliverables

- `tech-route.pptx`: native PowerPoint/WPS shapes.
- `tech-route.svg`: editable vector text and geometry.
- `tech-route.drawio`: editable diagrams.net cells.
- `tech-route.drawio-code.xml`: XML for **Extras > Edit Diagram** in [draw.io](https://app.diagrams.net/).
- `tech-route.excalidraw`: editable whiteboard scene.
- `tech-route.mmd`: text-editable Mermaid.
- `tech-route.html`: evidence-aware browser preview.
- `TECH_ROUTE.md`: documentation view.
- `tech-route.json`: canonical route source.
- `QUALITY_REPORT.md`: evidence, inference and manual-review report.

## 6. Human Revision

Do not submit the first render unchanged. Edit the appropriate output to fit the actual paper, defense deck or institutional template, and verify every claim against the authoritative source.
