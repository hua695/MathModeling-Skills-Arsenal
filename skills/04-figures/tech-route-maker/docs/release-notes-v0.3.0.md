# v0.3.0 - Evidence Integrity And Reliable Rendering

`v0.3.0` turns the repository's evidence claims into enforceable behavior.

## Highlights

- Source files receive stable IDs and SHA-256 hashes.
- Evidence locators are checked against extractable source text.
- Evidence coverage excludes inferred nodes.
- Final rendering stops when domain context, sources, evidence, inference or unresolved questions are incomplete.
- `--allow-draft` remains available for clearly unfinished work.
- Mainline and A4 layouts preserve all 2-6 nodes in every stage.
- Unsupported layouts and styles fail explicitly.
- Nine editable output formats receive structural and content-parity checks.
- PPTX archives are deterministic, preventing timestamp-only Git changes.
- GitHub CLI installs the root skill into Codex, Claude Code, Cursor, Gemini CLI, GitHub Copilot and many other hosts.

## Upgrade

```bash
python -m pip install -e .
trm ingest path/to/sources --output-dir evidence-pack
trm validate path/to/tech-route.json --strict
```

Existing `0.2.0` route files must be upgraded to `route_version: 0.3.0`, assign an `id` and SHA-256 to every source record, and resolve inferred nodes before final rendering.

## Manual Editing Still Required

Generated diagrams remain editable drafts. Users must review factual accuracy, terminology, route logic, wording, font sizes, colors, spacing and target-template requirements before submission or publication.
