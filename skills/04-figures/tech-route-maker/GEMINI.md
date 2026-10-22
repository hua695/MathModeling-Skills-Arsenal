# Gemini Adapter

Use `SKILL.md` as the primary instruction file for `tech-route-maker`.

This project is a portable skill for generating evidence-grounded editable technical route diagrams for research and engineering workflows.

Mandatory flow:

1. Read `SKILL.md`.
2. Use `references/route-schema.md` for `tech-route.json`.
3. Establish `domain_context` before final rendering: discipline, subfield, project type, research object, method family, data/materials, constraints and evaluation metrics.
4. Read `references/domain-profiles.md` when the discipline is unclear or unfamiliar.
5. Run `trm ingest` for local sources and record source IDs, locators and SHA-256 hashes.
6. Offer the closest preset, then confirm missing domain and final delivery choices instead of guessing them.
7. Render selected formats with:

```bash
trm render <route-json> <output-dir> --formats <formats>
```

8. Validate with:

```bash
trm validate <route-json> --strict
```

Use one concise grouped question rather than a long interview. Keep PPTX, SVG, Draw.io and Excalidraw outputs editable, and explain that they require manual revision.

When the user asks for copyable Draw.io or diagrams.net code, include `drawio-code` and explain that `tech-route.drawio-code.xml` can be pasted into [diagrams.net / draw.io](https://app.diagrams.net/) with **Extras > Edit Diagram**.
