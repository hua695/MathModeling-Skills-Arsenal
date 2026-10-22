# Contest-Orchestrator Adapter

## Scope

Use this adapter only for mathematical-modeling paper schematics:

- mechanism and principle diagrams;
- free-body, geometry, coordinate and vector figures;
- curves, angles and formula illustrations.

Data result plots and technical-roadmap diagrams belong to other dedicated routes.

## Evidence boundary

Before drawing, read the relevant `model_contract.yaml`, `symbol_table.md`, derivation registry and source/result files. Each visible symbol, unit, relation and geometric object must map to a source locator. A missing locator pauses the figure.

## Output contract

Keep the `.tex` source authoritative and deliver SVG + PNG (PDF is intermediate only, not a deliverable):

```yaml
kind: schematic
generator: tikz-scientific-figures
source_files: ["02_模型/model_contract.yaml", "02_模型/symbol_table.md"]
script: figures/mechanism/figure.tex
formats: [svg, png]
qa_status: reviewed
visual_qa: passed
```

Use XeLaTeX for Chinese text when required by the project. Keep data in an external file for data-driven panels. SVG is the primary vector deliverable; PNG is the raster companion.

## Handoff

Return the project-relative `.tex`, SVG, PNG, data sources, compilation result and visual review result to `contest-orchestrator`. Do not return or register PDF. Run visual review by default and check clipping, overlap, alignment, legibility, whitespace, color/gray-scale readability and clean composition; the user performs a final visual inspection as an additional check.
