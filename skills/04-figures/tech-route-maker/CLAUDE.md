# Claude Adapter

Use this repository as a Claude-compatible project context or skill folder.

Read `SKILL.md` first. It is the source of truth for when to use `tech-route-maker`, how to select default presets, when to ask necessary questions, and how to render editable outputs.

When a user asks for a technical route diagram, paper framework figure, engineering route, project roadmap, method flowchart, workflow, pipeline, or editable diagram:

1. Inspect source evidence.
2. Establish `domain_context`: discipline, subfield, project type, research object, method family, data/materials, constraints and evaluation metrics.
3. Read `references/domain-profiles.md` when the discipline is unclear or unfamiliar.
4. Build `tech-route.json`.
5. Inventory local sources with `trm ingest` and record stable source IDs and SHA-256 hashes.
6. Offer the closest preset, then confirm missing domain and final delivery choices instead of guessing them.
7. Run `trm validate <route> --strict`.
8. Render selected formats with `trm render` only after final blockers are resolved.
9. Report `QUALITY_REPORT.md` findings and required manual revision.

If the user asks for copyable Draw.io or diagrams.net code, render `drawio-code` and tell them to paste `tech-route.drawio-code.xml` into [diagrams.net / draw.io](https://app.diagrams.net/) through **Extras > Edit Diagram**.

Use `--allow-draft` only for an explicitly unfinished draft. Do not render screenshots as the main editable output, and do not present inferred nodes as evidence.
