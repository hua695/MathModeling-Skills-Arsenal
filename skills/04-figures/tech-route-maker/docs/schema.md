# Route Schema

`tech-route.json` is the source of truth for rendering. Edit the JSON first, then rerender PPTX, SVG, Draw.io, Draw.io copy-code XML, Excalidraw, Mermaid, HTML, Markdown, or JSON outputs from the same model.

Current schema version: `0.3.0`.

## Minimal Structure

```json
{
  "route_version": "0.3.0",
  "title": "Project Technical Route",
  "subtitle": "Editable route diagram",
  "selected_preset": "academic-method",
  "layout": "academic-method-framework",
  "style": "academic-blue",
  "domain_context": {
    "discipline": "Computer science",
    "subfield": "Computer vision defect detection",
    "project_type": "paper method figure",
    "research_object": "Photovoltaic module surface defects",
    "method_family": "deep learning object detection",
    "application_area": "PV inspection and operation maintenance",
    "data_or_materials": ["RGB images", "infrared images"],
    "technical_objects": ["dataset annotation", "feature fusion", "YOLO detector", "ablation study"],
    "domain_constraints": ["small targets", "class imbalance", "real-time inference"],
    "evaluation_metrics": ["mAP", "precision", "recall", "FPS"],
    "expected_outputs": ["editable method route", "trained detector", "defect report"],
    "terminology": {},
    "domain_profile": {
      "task_type": "object detection",
      "data_modalities": ["RGB", "infrared"],
      "model_family": ["YOLO", "attention", "feature fusion"]
    },
    "source": "source evidence",
    "confidence": "medium"
  },
  "metadata": {
    "created_by": "tech-route-maker",
    "selected_output_formats": ["pptx", "svg", "json"],
    "source_type": "paper",
    "source_files": [
      {
        "id": "source_1",
        "path": "source.md",
        "kind": "document",
        "description": "Input source material",
        "sha256": "<64-character SHA-256>"
      }
    ],
    "source_hashes": [
      {
        "source_id": "source_1",
        "path": "source.md",
        "algorithm": "sha256",
        "value": "<64-character SHA-256>"
      }
    ],
    "language": "en",
    "audience": "research"
  },
  "stages": [
    {
      "id": "objective",
      "title": "Objective",
      "order": 1,
      "nodes": [
        {
          "id": "objective_goal",
          "label": "Define project goal",
          "detail": "Clarify the problem and expected result.",
          "tag": "objective",
          "node_type": "objective",
          "confidence": "high",
          "is_inferred": false,
          "evidence": [
            {
              "kind": "source",
              "source_id": "source_1",
              "path": "source.md",
              "locator": "Section 1",
              "quote_or_note": "The source describes the project goal."
            }
          ]
        }
      ]
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "from": "objective_goal",
      "to": "next_node",
      "label": "guides",
      "kind": "flow",
      "confidence": "medium",
      "evidence": []
    }
  ],
  "assumptions": [],
  "unresolved_questions": [],
  "quality_report": {},
  "citations": [],
  "renderer_overrides": {
    "show_edge_labels": false,
    "show_node_edges": false
  }
}
```

## Required Fields

- `route_version`: must exist. Current version is `0.3.0`.
- `title`: visible diagram title.
- `selected_preset`: one of `academic-method`, `thesis-proposal`, `engineering-system`, `workflow-pipeline`, `chinese-thesis-proposal`, `chinese-grant-application`, `academic-paper-framework-cn`, `engineering-project-report-cn`, or `custom`.
- `domain_context`: required for final-use diagrams. Drafts may be partial, but missing fields must be shown in `unresolved_questions` and `QUALITY_REPORT.md`.
- `stages`: ordered route stages.
- `nodes[].confidence`: `high`, `medium`, or `low`.
- `nodes[].is_inferred`: boolean inference marker.
- `edges[].confidence`: `high`, `medium`, or `low` when present.

## Evidence And Inference Rules

Every visible node in a final diagram must have at least one evidence item that names a declared source, uses a nonempty locator, and points to a source whose SHA-256 is verified. An inferred node is draft-only: set `is_inferred: true`, link it from `assumptions.node_ids`, and resolve or remove it before final rendering.

Use `unresolved_questions` for missing decisions that would materially affect the route, such as whether a validation step should be a separate stage or whether an inferred branch should remain visible.

## Domain Context Rules

Do not render a final route from a field-agnostic request. First identify the discipline, subfield, project type, research object, method family, application area, data/materials, constraints and evaluation metrics.

Examples:

- Computer vision: keep dataset, annotation, augmentation, model modules, training, ablation and evaluation separate.
- Materials science: keep material design, preparation, characterization, performance testing, mechanism analysis and application validation separate.
- Energy engineering: keep system boundary, source/load data, configuration model, operation strategy, scenario validation and deliverables separate.
- Biomedical research: keep sample/cohort, grouping/intervention, assay/detection, mechanism/statistics, validation and biological or clinical significance separate.
- Social science: keep theory, hypotheses, variables, data collection, empirical model, robustness and implications separate.

## Practical Rules

- Keep the main route to 4 to 7 stages when possible.
- Keep each stage to 2 to 6 nodes when possible.
- Keep visible labels short.
- Keep edge labels in JSON/HTML/Markdown by default; do not render them on the main SVG/PPTX/Draw.io canvas unless `renderer_overrides.show_edge_labels` is explicitly set to `true`.
- Keep node-to-node semantic edges out of the main canvas by default; renderers should use straight stage-to-stage arrows unless `renderer_overrides.show_node_edges` is explicitly set to `true`.
- Put long explanations in `detail`, Markdown, or HTML.
- Use `metadata.selected_output_formats` to record actual rendered outputs, including `drawio-code` when generating copyable Draw.io XML.
- Keep `quality_report` generated by tooling, not manually invented.

## Layout Values

- `academic-method-framework`: default academic template for papers, defenses, and research reports.
- `proposal-matrix-route`: thesis proposal, grant route, and research-plan route.
- `engineering-architecture-route`: engineering systems, energy systems, platform workflow and system handoff.
- `horizontal-stages`: workflow, pipeline, agent/tool process.
- `cn-proposal-poster-route`: Chinese thesis proposal, opening report, topic application, and research-route poster.
- `cn-grant-application-route`: Chinese grant or project application route with reviewer-facing logic.
- `cn-research-method-matrix`: Chinese academic method framework and paper-method matrix.
- `cn-wide-project-map`: Chinese engineering project report, platform map, and energy-system route.
- `cn-ppt-mainline-route`: formal 16:9 PPT main route with stage mainline, support modules, and final-output bar.
- `cn-a4-stage-route`: formal portrait Word/thesis/report route with numbered stage headers and no left phase axis.
- `cn-monochrome-linework-route`: print-safe Chinese proposal/application route.
- `campaign-strategy-map`: legacy/experimental campaign workflow.
- `proposal-phase-axis`: legacy long vertical route with a left phase axis.

## Quality Report

`QUALITY_REPORT.md` is generated from the route model. It reports source-verification status, true evidence coverage, inferred coverage, accounted coverage, unresolved questions, label warnings and manual review suggestions. Inferred nodes never increase evidence coverage.
