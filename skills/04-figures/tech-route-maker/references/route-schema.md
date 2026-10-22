# Route Schema Reference

Use this schema for `tech-route.json`. The file is the single source of truth for every rendered format.

Current schema version: `0.3.0`.

## Top-level fields

| Field | Required | Notes |
|---|---|---|
| `route_version` | yes | Current version is `0.3.0`. |
| `title` | yes | Visible diagram title. |
| `subtitle` | no | Optional visible subtitle. |
| `selected_preset` | yes | `academic-method`, `thesis-proposal`, `engineering-system`, `workflow-pipeline`, or `custom`. |
| `layout` | recommended | Renderer layout ID. |
| `style` | recommended | Renderer visual style ID. |
| `domain_context` | recommended for drafts; required for final diagrams | Discipline, subfield, project type, research object, method family, constraints and metrics. |
| `metadata` | recommended | Source files, selected outputs, language and audience. |
| `stages` | yes | Ordered stage list. |
| `edges` | recommended | Semantic links between node IDs. |
| `assumptions` | recommended | Explains inferred content. |
| `unresolved_questions` | recommended | Questions requiring user or source-owner review. |
| `quality_report` | generated | Filled by validator/render tooling. |
| `citations` | optional | External citation records when needed. |
| `renderer_overrides` | optional | Format-specific render hints. |

## Metadata fields

- `created_by`: normally `tech-route-maker`.
- `selected_output_formats`: actual rendered outputs.
- `source_type`: `paper`, `proposal`, `engineering`, `workflow`, `legacy-campaign`, or `custom`.
- `source_files`: list of source files with stable `id`, `path`, `kind`, `description`, and SHA-256.
- `source_hashes`: structured SHA-256 records with `source_id`, `path`, `algorithm`, and `value`.
- `language`: route language.
- `audience`: `research`, `engineering`, `technical`, or another target audience.

## Domain context fields

Use `domain_context` to prevent generic, field-agnostic diagrams.

- `discipline`: broad field, such as computer science, materials science, energy engineering, biomedical science, mechanical engineering, environmental science, agriculture, or social science.
- `subfield`: narrower direction.
- `project_type`: paper method figure, thesis proposal, grant application, engineering report, system architecture, experiment workflow, review framework, or course design.
- `research_object`: concrete object being studied.
- `method_family`: main method type.
- `application_area`: intended use context.
- `data_or_materials`: source data, samples, materials, devices, documents, or field records.
- `technical_objects`: core modules, variables, devices, algorithms, experiments, interventions, or mechanisms.
- `domain_constraints`: conditions that shape the route.
- `evaluation_metrics`: measurable success criteria.
- `expected_outputs`: papers, models, prototypes, datasets, reports, mechanisms, standards, plans, or application deliverables.
- `terminology`: optional domain-specific preferred terms.
- `domain_profile`: optional field-specific object, such as computer-vision task type or biomedical sample design.
- `confidence`: `high`, `medium`, or `low`.

## Node fields

- `id`: stable node identifier.
- `label`: visible node label.
- `detail`: longer explanation for HTML/Markdown.
- `tag`: category such as `objective`, `input`, `method`, `implementation`, `validation`, `output`, `risk`, or `feedback`.
- `node_type`: optional semantic type.
- `confidence`: `high`, `medium`, or `low`.
- `is_inferred`: boolean. Use `true` only when the node is not directly stated in the source.
- `evidence`: source-grounding list.

## Evidence fields

- `kind`: use `source` for node-grounding records.
- `source_id`: required source record ID.
- `path`: source path when available.
- `locator`: section, page, paragraph, function, table, figure, or row locator.
- `quote_or_note`: short evidence note. Keep it concise.
- `symbol`: function/class/config key when available.

## Edge fields

- `id`: stable edge identifier.
- `from`: source node ID.
- `to`: target node ID.
- `label`: semantic transition. Keep it in the route model for audit, HTML and Markdown; renderers should not display it on the main canvas unless `renderer_overrides.show_edge_labels` is explicitly enabled.
- `kind`: `flow`, `feedback`, `dependency`, `validation`, or `evidence`.
- `confidence`: `high`, `medium`, or `low`.
- `evidence`: optional edge-level support.

## Renderer overrides

- `show_edge_labels`: optional boolean, default `false`. When `false`, SVG, PPTX, Draw.io and Excalidraw outputs render clean connector arrows without transition text on the line. Keep the semantic edge labels in JSON, HTML, Markdown or quality reports instead.
- `show_node_edges`: optional boolean, default `false`. When `false`, visual renderers draw only straight stage-to-stage arrows. When `true`, renderers may draw the semantic node-to-node graph for debugging or highly technical diagrams.

## Validation rules

- `route_version` must exist.
- `selected_preset` must be valid.
- Final diagrams require complete `domain_context`; missing or partial context blocks final rendering.
- Stages should usually be 4 to 7.
- Each stage should usually contain 2 to 6 nodes.
- Every final visible node must have evidence from a declared, hash-verified source.
- Inferred nodes must be linked from an assumption by `node_ids`, are counted separately from evidence, and block final rendering.
- Evidence locators must be present in extractable source text when applicable.
- Unresolved questions block final rendering.
- Edge endpoints must point to existing nodes.
- Confidence values must be `high`, `medium`, or `low`.
