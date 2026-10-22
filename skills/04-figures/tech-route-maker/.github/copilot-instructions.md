# GitHub Copilot Instructions

This repository is an agent skill named `tech-route-maker`.

Use `SKILL.md` as the source of truth. The skill creates evidence-grounded editable technical route diagrams for research and engineering projects.

Required behavior:

- Build `tech-route.json` before rendering.
- Establish `domain_context` before final rendering: discipline, subfield, project type, research object, method family, data/materials, constraints and evaluation metrics.
- Read `references/domain-profiles.md` when the discipline is unclear or unfamiliar.
- Inventory local sources and record stable source IDs, locators and SHA-256 hashes.
- Offer a default preset, but confirm missing domain and final delivery choices instead of guessing them.
- Use `trm validate <route> --strict` before final rendering.
- Use `trm render` to generate selected formats; `--allow-draft` is only for explicit drafts.
- Report `QUALITY_REPORT.md` warnings and manual review needs.
- Preserve editability in PPTX, SVG, Draw.io, and Excalidraw outputs.
- Tell the user that generated files require factual and visual revision before formal use.
- If the user asks for copyable Draw.io or diagrams.net code, generate `drawio-code` and mention [diagrams.net / draw.io](https://app.diagrams.net/) with **Extras > Edit Diagram**.
