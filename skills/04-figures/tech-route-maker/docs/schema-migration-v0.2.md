# Schema Migration To v0.2.0

This guide migrates older `tech-route.json` files to the v0.2.0 evidence-grounded schema.

## Required additions

Add these top-level fields:

```json
{
  "route_version": "0.2.0",
  "selected_preset": "academic-method",
  "assumptions": [],
  "unresolved_questions": [],
  "quality_report": {},
  "citations": [],
  "renderer_overrides": {}
}
```

Add these metadata fields when available:

```json
{
  "metadata": {
    "created_by": "tech-route-maker",
    "source_type": "paper",
    "source_files": [],
    "source_hashes": [],
    "selected_output_formats": ["pptx", "svg", "json"]
  }
}
```

For every node, add:

```json
{
  "confidence": "medium",
  "is_inferred": false
}
```

For every edge, add:

```json
{
  "confidence": "medium",
  "evidence": []
}
```

## Evidence rule

A visible node must have `evidence` or be marked with `is_inferred: true`. If it is inferred, add an assumption that links back to the node:

```json
{
  "id": "assumption_1",
  "node_ids": ["method_core"],
  "text": "The method block is inferred from the project structure.",
  "reason": "The source does not state the route explicitly.",
  "impact": "medium"
}
```

## Validation

Run:

```bash
python scripts/validate_route.py examples/academic-paper-demo/outputs/tech-route.json
```

A successful result should print `Validation OK` and include route version, preset, stage count, node count, edge count and evidence coverage.