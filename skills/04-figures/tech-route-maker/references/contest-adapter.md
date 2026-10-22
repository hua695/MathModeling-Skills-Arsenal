# Contest-Orchestrator Adapter

## Scope

Use this adapter only for a mathematical-modeling contest project. The skill owns two figure roles:

- `problem_analysis_flowchart`: problem goals, inputs, constraints, subproblem relationships and required outputs;
- `technical_roadmap`: assumptions, symbols, model structure, algorithm/solver, validation and result output.

## Evidence boundary

Read only the project artifacts needed for the selected role. Preferred inputs are:

- `problem_condition_ledger.yaml`;
- the relevant subproblem task card;
- `model_blueprint.yaml`;
- `model_contract.yaml`;
- `symbol_table.md`;
- `result_registry` when results are shown.

Every visible node and edge requires a source locator. A derived node must identify the source relation and remain marked as derived. An unresolved or inferred node blocks final paper output.

## Output contract

For paper use, write the route source and outputs under the project figure directory:

```yaml
kind: flowchart
generator: tech-route-maker
diagram_role: technical_roadmap
source_files: ["02_模型/model_blueprint.yaml", "02_模型/model_contract.yaml", "figures/model_framework/tech-route.json"]
formats: [svg, png]
qa_status: reviewed
visual_qa: passed
```

`tech-route.json` is the semantic source of truth (listed in source_files, not in formats). `SVG + PNG` are the default paper deliverables. Draw.io, PPTX and HTML are optional outputs and require an explicit user request.

## Handoff

Return the project-relative output paths, source locators, validation command, validation status and visual review result to `contest-orchestrator`. Run visual review by default and check spacing, alignment, clipping, overlap, hierarchy, text legibility and clean composition. Do not copy the route-building discussion into the paper.
