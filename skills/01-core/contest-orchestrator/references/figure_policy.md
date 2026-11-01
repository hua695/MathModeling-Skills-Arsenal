# Figure Route Contract

This is the single active figure-routing and visual-argument contract for `contest-orchestrator`.

**Route table is enforced by `check_harness_control.py` (BLOCK-level)**: every registry entry must carry `kind` matching `generator` per the table below, `formats: [svg, png]`, `insertion_format: svg`, a valid `layout_mode`, and `visual_qa` passed/reviewed. Draw.io requires `user_requested=true`.

## Route table

| Figure role | Generation route | Registry generator | Image outputs | LaTeX insertion | Visual QA |
|---|---|---|---|---|---|
| Data result figure | `SciPilot → ModelViz → SciPilot` | `modelviz` with `semantic_qa=scipilot-figure-skill` | `svg`, `png` | `svg` | On by default |
| Problem-analysis flowchart | `tikz-scientific-figures` | `tikz-scientific-figures` | `svg`, `png` | `svg` | On by default |
| Technical-roadmap diagram | `tikz-scientific-figures` | `tikz-scientific-figures` | `svg`, `png` | `svg` | On by default |
| Mechanism/principle/force/geometry schematic | `tikz-scientific-figures` | `tikz-scientific-figures` | `svg`, `png` | `svg` | On by default |
| Draw.io editing artifact | `drawio-diagram` | `drawio-diagram` | `svg`, `png` plus editable source | `svg` | On by default after explicit Draw.io request |

The registry contract is `formats: [svg, png]` and `insertion_format: svg`. `formats` lists only rendered image outputs and must be exactly `["svg", "png"]`. Editable sources such as `.tex` and `.drawio` are recorded in `script` or `source_files`, not mixed into `formats`. A single-image PDF is not a permitted output.

For every mode, all non-data diagrams use tikz-scientific-figures with the matching catalog starter; measured data figures use the SciPilot → ModelViz → SciPilot route. MathorCup and Harness retain their existing approval gates.

## Reader-first visual argument gate

`chart_requirements.yaml` records the claims and frozen evidence fields identified at H5 (stage 1, formerly H4). It does not choose a chart type. After H6 freezes the model and results, the H7 figure agent creates `visual_argument_plan.yaml` before any template search or image generation. This plan is the authoritative record of what the reader needs to understand and why a visual artifact earns space in the paper. `scipilot-figure-skill` is invoked after the plan only for data-figure decision cards and data-figure semantic/technical/visual QA; it does not own the whole visual plan.

Each subproblem must contain exactly one audit entry for each category: `orientation`, `mechanism`, `model_structure`, `algorithm_process`, `result_evidence`, and `validation_robustness`. Every entry records `reader_question`, `reader_gain`, `evidence_refs`, and one disposition:

| Disposition | Use | Hard requirement |
|---|---|---|
| `required` | A visual artifact is needed to answer the reader question | `planned_figure_ids` is mandatory and must close in the registry |
| `recommended` | A visual artifact materially improves the reading path | Plan a candidate or record a concrete `deferred_reason` |
| `table_justified` | A small discrete result is directly comparable in a table | Only `result_evidence`; requires structured `table_justification` and `table_refs` |
| `text_sufficient` | Prose and equations fully answer the reader question | `rationale` and evidence are mandatory; cannot replace a hard obligation |
| `not_applicable` | The category has no corresponding relation in the model | `rationale` and evidence are mandatory; cannot be the default for complex models |

The checker derives hard obligations from the H5 model-summary facts. Structured models require model-structure and validation/robustness visuals in addition to result evidence; iterative or heuristic solvers require an algorithm-process visual; mechanism, spatial, geometric, ODE and simulation relations require a mechanism visual. Multiple subproblems or cross-question interfaces require a `global_story` visual slot. This is a coverage contract, not a fixed total figure count.

The plan checker recomputes `required_visual_slots`, `required_figure_slots`, `planned_figure_count`, and table-justified slots. A single planned figure cannot satisfy multiple slots. The plan phase must submit `.contest/reviews/H7_visual_plan_review_packet.yaml`; the approval log gate is `H7_VISUAL_PLAN`, and its artifact digests must cover the current plan. Until this independent user approval exists, H7 cannot enter the generation/registration phase. At finalization, every registry entry must carry `visual_slot_ids`, every planned figure must be registered and QA-passed, and every registry figure must belong to an approved slot. An unplanned figure is a relevance failure. A missing mandatory slot is a completeness failure. H8 reads the approved plan and may place only its registered figures; it cannot add a plan-free figure to increase page count.

### Template execution closure

Reading a template description is not template use. Every figure slot with a planned figure must
select an exact `template_id`, provide a `visible_element_map` and a `canvas_profile`, and carry
these fields into the registry. `visible_element_map` is a list of visible elements, each bound to
one or more evidence locators; `canvas_profile` records `orientation`, `target_layout`, and
`top_level_node_limit`. Standard-density figures must map at least two visible elements.

For tikz-scientific-figures, the selected ID must resolve to
`references/figure_template_catalog.yaml`. The generator must copy the catalog's `starter_source`,
adapt that editable source, and register the catalog SHA-256 as `template_sha256`. The generated
TikZ source must carry the three contest-template source markers. A final registry entry must also contain:

```yaml
template_id: algorithm-iteration-flow
starter_source: tikz-scientific-figures/assets/contest-starters/algorithm-iteration-flow.tex
template_sha256: <starter SHA-256>
template_fixture:
  fixture_id: tikz-scientific-figures/algorithm-iteration-flow
  status: passed
  report: figures/q1-algorithm/template_fixture.yaml
visible_element_map: [{element: 输入, role: node, evidence_refs: [<source locator>]}, {element: 输出, role: node, evidence_refs: [<source locator>]}]
canvas_profile: {orientation: horizontal, target_layout: single, top_level_node_limit: 7}
visual_qa: passed
```

The fixture report must be a project-relative file whose `status` is `passed`, whose template ID
and hash equal the registry, and whose `visual_qa` is `passed` or `reviewed`. A missing, failed or
hash-mismatched starter fixture blocks H7/H8. Data figures use the exact selected ModelViz catalog
ID in the same fields; their template source/hash are reported by the ModelViz execution handoff.

## Figure-intent contract

Every slot with a non-empty `planned_figure_ids` or `representation.mode: figure` must contain a `figure_intent` object. This is the figure's argument brief, not a second evidence packet. The H5→H6→H7 `visual_evidence_packet.yaml` remains indexed and minimal; it supplies verified information-unit IDs, while `figure_intent` explains how one figure will turn those units into a reader-facing explanation.

`figure_intent` must contain:

| Field | Required meaning |
|---|---|
| `reader_question` | The one question this figure answers for the reader |
| `explanatory_relation` | The relationship that becomes easier to understand visually |
| `must_show` | Objects, links, evidence or labels that must be visible; at least one |
| `must_not_show` | Unrelated formulas, values, branches, decoration or other content excluded from the canvas; an empty list is allowed only when justified by the figure type |
| `body_anchor` | The concrete chapter/section position where the figure is explained |
| `pre_text_function` | The argumentative job of the paragraph before the figure |
| `post_text_function` | The interpretation and boundary job of the paragraph after the figure |
| `generation_route` | Exactly one of `modelviz`, `tikz-scientific-figures` or explicitly requested `drawio-diagram` |
| `template_status` | `native`, `external_adapted` or `custom_required` |
| `template_id` | Exact selected catalog/template ID; never a prose description or placeholder |
| `visible_element_map` | Non-empty element-to-evidence map; standard figures expose at least two mapped elements |
| `canvas_profile` | `orientation`, `target_layout`, and `top_level_node_limit` used by the generator |

For data figures, `generation_route: modelviz` is intentional: SciPilot is recorded in the decision
and QA fields, while ModelViz is the executing generator. `scipilot-figure-skill` must not be used as
the registry `generator` or as a substitute for the H7 visual plan.

`template_id` is the exact selected catalog ID, not a prose template name. `visible_element_map`
and `canvas_profile` are the execution brief consumed by the generator; they are not optional
description fields.

The figure agent chooses the template only after writing this brief. The route is then copied to the registry as `generator`; the final checker blocks a route or `template_status` mismatch. Recommended local templates are:

| Reader need | Visual archetype | Route | Content policy |
|---|---|---|---|
| Understand the whole contest task | Subproblem dependency map | `tikz-scientific-figures` | Show inputs, subproblem links and outputs; no derivation or result values |
| Understand the paper's main line | Data–model–solver–result route | `tikz-scientific-figures` | Show the evidence flow and handoffs; no invented agent steps |
| Understand a model's composition | Variable–objective–constraint frame or model-summary frame | `tikz-scientific-figures` | Show named objects and relations; do not reproduce the full derivation |
| Reproduce a solver | Algorithm iteration flow | `tikz-scientific-figures` | Show input, core steps, decision/loop, stop condition and output; no decorative pseudocode or unsupported parameters |
| Understand reliability | Validation or sensitivity loop | `modelviz` for measured results; otherwise `tikz-scientific-figures` | Show the verified baseline, perturbation/validation condition and response; no unsupported robustness claim |
| Understand spatial or geometric reasoning | Coordinate, angle, coverage or path schematic | `tikz-scientific-figures` | Show the necessary geometry and local quantities only; every symbol and relation is source-bound |
| Understand a mechanism | Free-body or mechanism schematic | `tikz-scientific-figures` | Show forces, directions, interfaces and causal relations; no full result table or unrelated formula block |
| Read the final computable model | Final model-summary frame | `tikz-scientific-figures` | Present the frozen objective, constraints and essential definitions in one frame; do not add new equations or values |

Type-specific content rules are hard: orientation, task-route and algorithm figures are prose/relationship-first; mechanism and geometry figures may show necessary local formulas or quantities; result and validation figures may show frozen data and metrics; no figure may display a formula, value or relation that is not bound to the approved evidence.

## Minimal visual evidence packet

`visual_evidence_packet.yaml` is the H5→H6→H7 evidence interface. It is an indexed summary, not a replacement for model, result, validation or registry artifacts. H5 creates one or more independent `information_units` for every subproblem; each unit contains `unit_id`, `unit_type`, `statement`, `meaning`, `scope`, `unit` and structured `evidence_refs` with a project-relative path, SHA-256 and locator. The packet must not embed raw data, full code, full literature, chat history, prompts or debug logs.

H6 verifies the source hashes, locators, model-contract digest, subproblem coverage and duplicate statements, then records `status: verified`, `verified_by: H6` and the current verification instance. A stale hash or `evidence_gap` blocks H7. H7 reads the verified packet before visual planning. Every planned figure slot records `information_unit_ids` and `density_profile`; `standard` requires at least two distinct units, while `compact` permits exactly one only with `compact_figure_reason`. Every registry entry repeats `information_unit_ids`, records `realized_information_unit_ids`, and must match the approved slot set exactly. This binds figure information density to reader value without imposing a fixed total figure count.

## Data-figure pipeline

The data-figure route has one owner per phase:

1. **SciPilot discovery**: profile the approved data and create one decision card per figure. This is the sole stage that selects a data figure's chart type, visual encoding and figure-canvas shape; it does not decide the paper page layout.
2. **ModelViz generation**: consume the approved decision card, retrieve compatible templates, adapt them to real data, execute the plotting script, and export SVG and PNG.
3. **SciPilot QA**: perform semantic, technical, and visual checks on the generated SVG and PNG. A failed check returns a targeted repair request to ModelViz.
4. **contest-orchestrator registry**: register only the final passed artifacts, source mapping, caption claim, paper location, and QA evidence.

ModelViz must not redefine the claim or recommended chart. SciPilot must not replace the selected template or rewrite the model result. The loop ends only when the same artifact set passes all three SciPilot checks.

## Decision card

Before ModelViz is called, each figure must have a complete decision card containing `decision_author: scipilot-figure-skill` and:

| Field | Requirement |
|---|---|
| `figure_id` | Unique figure identifier |
| `subproblem` | Q1, Q2, Q3, Q4, or the applicable task identifier |
| `claim` | One core conclusion supported by the figure |
| `source_files` | Registered result files and necessary parameter files |
| `data_fields` | Fields used and their meanings |
| `data_shape` | Continuous, categorical, matrix, interval, network, or other structure |
| `recommended_chart` | Preferred chart type and reason |
| `alternatives` | One or two acceptable alternatives |
| `rejected_chart_types` | Chart types that would mislead this data |
| `axes_units` | Axes, units, scales, and transformations |
| `caption_claim` | Scope, conditions, and limitations required in the caption |
| `paper_location` | Body or appendix target section; page layout is recorded only after the paper layout is planned |

## Evidence and source rules

- Data figures read only registered result files or approved raw data; the plotting script records the mapping from source columns to visual marks.
- `tikz-scientific-figures` reads the problem condition ledger, task cards, model blueprint/contract, symbol table, derivation registry and source/result files as applicable. Every visible node, edge, symbol, unit, relation and geometric object needs a source locator.
- Missing evidence, unresolved inferred nodes, invented variables, unsupported relations, missing source files or stale registry entries block paper use.
- Keep every non-data diagram's semantic source editable as `.tex`; retain `.drawio` only for explicitly requested Draw.io artifacts.

## Registry examples

```json
{"kind":"data","generator":"modelviz","generation_route":"modelviz","template_status":"native","template_id":"<selected ModelViz catalog ID>","template_source":"<selected ModelViz template source>","template_sha256":"<template source SHA-256>","template_fixture":{"fixture_id":"modelviz/<selected-template-id>","status":"passed","report":"figures/q1/template_fixture.yaml"},"visible_element_map":[{"element":"<result metric>","role":"mark","evidence_refs":["results/result.json#/result"]},{"element":"<comparison relation>","role":"relation","evidence_refs":["results/result.json#/comparison"]}],"canvas_profile":{"orientation":"horizontal","target_layout":"single","top_level_node_limit":7},"semantic_qa":"scipilot-figure-skill","source_files":["results/result.json"],"script":"figures/q1/plot.py","formats":["svg","png"],"insertion_format":"svg","layout_mode":"single","qa_status":"reviewed","visual_qa":"passed"}
```

```json
{"kind":"flowchart","generator":"tikz-scientific-figures","generation_route":"tikz-scientific-figures","template_status":"native","template_id":"model-structure-roadmap","starter_source":"tikz-scientific-figures/assets/contest-starters/model-structure-roadmap.tex","template_sha256":"<starter SHA-256>","template_fixture":{"fixture_id":"tikz-scientific-figures/model-structure-roadmap","status":"passed","report":"figures/model_framework/template_fixture.yaml"},"visible_element_map":[{"element":"变量与目标","role":"node","evidence_refs":["02_模型/model_contract.yaml#/formulation"]},{"element":"约束与求解接口","role":"edge","evidence_refs":["02_模型/model_contract.yaml#/solver_interface"]}],"canvas_profile":{"orientation":"horizontal","target_layout":"single","top_level_node_limit":7},"diagram_role":"model_structure","source_files":["02_模型/model_blueprint.yaml","02_模型/model_contract.yaml"],"script":"figures/model_framework/figure.tex","formats":["svg","png"],"insertion_format":"svg","layout_mode":"single","qa_status":"reviewed","visual_qa":"passed"}
```

```json
{"kind":"schematic","generator":"tikz-scientific-figures","generation_route":"tikz-scientific-figures","template_status":"native","template_id":"model-summary-frame","starter_source":"tikz-scientific-figures/assets/contest-starters/model-summary-frame.tex","template_sha256":"<starter SHA-256>","template_fixture":{"fixture_id":"tikz-scientific-figures/model-summary-frame","status":"passed","report":"figures/mechanism/template_fixture.yaml"},"visible_element_map":[{"element":"冻结目标与变量","role":"node","evidence_refs":["02_模型/model_contract.yaml#/formulation"]},{"element":"约束与求解接口","role":"edge","evidence_refs":["02_模型/model_contract.yaml#/solver_interface"]}],"canvas_profile":{"orientation":"horizontal","target_layout":"single","top_level_node_limit":7},"source_files":["02_模型/model_contract.yaml","02_模型/symbol_table.md"],"script":"figures/mechanism/figure.tex","formats":["svg","png"],"insertion_format":"svg","layout_mode":"single","qa_status":"reviewed","visual_qa":"passed"}
```

Draw.io is valid only when the user explicitly requests a Draw.io editing artifact. It never becomes the default route for a paper figure.

## Availability gate

The route names must resolve to installed or otherwise explicitly available skills before generation. If tikz-scientific-figures, ModelViz or scipilot-figure-skill is unavailable, stop at the figure input gate and report the missing dependency. Do not silently substitute a different generator.

## Page-layout metadata

Page layout is a paper-production decision made after the figure has passed generation and QA. Every registered image must record exactly one `layout_mode`; this field never changes the generator, chart type, visual encoding, or SVG/PNG assets.

| `layout_mode` | Required companion fields | Approved LaTeX entry | Use |
|---|---|---|---|
| `single` | none | `\PaperFigure` | Regular single figure |
| `side_by_side` | `layout_group`, `layout_variant` (`table_text`, `figure_text`, or `algorithm_flow`) | `\PaperTwoColumn` | Top-aligned table/text, text/figure, or algorithm/flowchart block |
| `wrap_short` | `wrap_side` (`left` or `right`) | `\PaperWrapFigure` | Small figure beside a short plain-text paragraph only |
| `tall_constrained` | `max_height` | `\PaperTallFigure` | Vertical figure with an explicit height bound |

`layout_group` identifies one two-column block and must be unique within the paper. Use `minipage`-based pair layouts for stable alignment. Do not use `wrap_short` around lists, displayed equations, tables, or long argument sections.

## LaTeX insertion and layout contract

All registered figures must comply with the following layout rules when inserted into the paper. These are source-file-level rules; `check_tex_layout_patterns.py --strict` enforces the hard subset.

| Rule | Requirement |
|---|---|
| Float specifier | Use `[!htbp]` by default. `[H]` is forbidden — it locks the float and pushes subsequent text onto a new page. |
| Preamble tuning | Load `placeins` and set: `topnumber=3`, `bottomnumber=2`, `totalnumber=4`, `topfraction=0.85`, `bottomfraction=0.7`, `textfraction=0.1`, `floatpagefraction=0.7`. |
| Text-figure interleaving | At least one body paragraph must appear between two consecutive `figure` environments. No more than two figures in a row within the same subsection; if more are needed, insert result analysis or split across subsections. |
| Figure follows reference | A figure must appear within 1–2 paragraphs after its first `\ref` in the text. It must not appear before its first reference, and must not float across chapter boundaries. Place `\FloatBarrier` at the end of each chapter. |
| Image size | Standard figures use the approved layout macros. Direct `\includesvg` must not use full `\textwidth`; standard width is 0.60–0.85 `\textwidth`, and height is at most 0.40 `\textheight`. Side panels use `\linewidth` inside a bounded `minipage`. |
| Output format | LaTeX insertion uses SVG only. PNG is for preview and delivery registry; single-image PDF is not permitted. |

The detailed anti-pattern rules and examples are in `references/layout_and_delivery_drift.md`.
