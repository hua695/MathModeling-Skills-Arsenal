# Changelog

## Unreleased

No unreleased changes.

## 0.3.0 - 2026-07-12

Evidence integrity, strict rendering and portable installation release.

Added:

- SHA-256 source manifests and locator-aware evidence verification.
- Separate evidence, inferred and accounted coverage metrics.
- Strict final-render quality gate with explicit `--allow-draft` override.
- `trm ingest` evidence-pack generation and improved `trm init` onboarding.
- Canonical layout/style registry with explicit errors for unsupported identifiers.
- Structural and content-parity QA across PPTX, SVG, Draw.io, Draw.io code, Excalidraw, Mermaid, HTML, Markdown and JSON.
- Deterministic PPTX archives so identical routes produce identical files.
- GitHub CLI `gh skill install` instructions plus a generic explicit-target installer.

Fixed:

- Mainline and A4 renderers no longer truncate stages after three nodes.
- Inferred nodes no longer inflate evidence coverage.
- Unknown layout/style names no longer silently fall back to unrelated templates.
- Generated demos now include real source statements, stable source IDs and verified hashes.
- Chinese output is regenerated from UTF-8 source material and checked across formats.

### Chinese academic route style upgrade

Added:

- Chinese academic presets: `chinese-thesis-proposal`, `chinese-grant-application`, `academic-paper-framework-cn`, and `engineering-project-report-cn`.
- Chinese layout families: `cn-proposal-poster-route`, `cn-grant-application-route`, `cn-research-method-matrix`, `cn-wide-project-map`, and `cn-monochrome-linework-route`.
- Chinese visual styles: `cn-polished-pastel-academic`, `cn-blue-green-proposal`, `cn-soft-grant-report`, `cn-reviewer-linework`, and `cn-defense-poster`.
- `references/local-style-study.md` with distilled academic-route aesthetics from the maintainer-provided local template corpus.
- `examples/chinese-grant-application-demo/` with editable PPTX, SVG, Draw.io, Excalidraw, Mermaid, HTML, Markdown, JSON, and quality report outputs.
- `docs/comparison-before-after.md` comparing old and new generated examples.

Changed:

- Core academic, thesis proposal, and engineering demos now use the new Chinese academic template family.
- PPTX rendering now uses portrait slide size for Chinese proposal/grant route diagrams instead of compressing them into 16:9.
- Draw.io rendering now uses layout-aware page dimensions and dashed stage boundaries.
- `scripts/refresh_demo_assets.py` now delegates to the maintained `scripts/build_v02_demos.py` generator.

## 0.2.0 - 2026-07-02

Research and engineering focus release.

Added:

- Default presets for academic methods, thesis proposals, engineering systems and workflow pipelines.
- `route_version: 0.2.0` schema with structured assumptions, unresolved questions, confidence fields and inference flags.
- `QUALITY_REPORT.md` generation for evidence coverage, inferred nodes, warning checks and manual review guidance.
- Python package entry point with `trm validate`, `trm render`, `trm init` and `trm doctor`.
- Engineering energy system demo for source-grid-load-storage planning.
- Agent workflow demo for converting technical materials into editable route diagrams.
- `docs/schema-migration-v0.2.md` migration guide.

Changed:

- README positioning narrowed from broad cross-domain route diagrams to evidence-grounded research and engineering route diagrams.
- Skill interaction policy now uses default presets instead of forcing long option selection.
- Advertising/campaign examples moved to legacy or experimental status.
- GitHub Actions now validates the four core research and engineering examples.

Validation:

- Python source compile check for `scripts/*.py` and `tech_route_maker/*.py`.
- Example route JSON validation.
- Demo rendering for PPTX, SVG, Draw.io, Excalidraw, Mermaid, HTML, Markdown, JSON and `QUALITY_REPORT.md`.
- CLI validation through `trm --help`, `trm doctor`, `trm validate` and `trm render`.

## 0.1.1 - 2026-06-19

Repository-surface upgrade.

Added:

- Visual GitHub README hero with banner, badges, preview image, gallery, and 30-second start.
- `assets/` visual assets for banner, demo preview, and social preview.
- `docs/` documentation hub with quick start, installation, output formats, agent compatibility, schema, FAQ, and release checklist.
- `examples/README.md` gallery.
- Thesis proposal, software architecture, and campaign route demos with generated editable outputs.
- GitHub Actions validation workflow for route JSON, renderers, and representative outputs.

## 0.1.0 - 2026-06-19

Initial public release of `tech-route-maker`.

Added:

- Portable `SKILL.md` workflow for editable technical route diagrams.
- Cross-agent adapters for Codex/OpenAI-style skills, AGENTS.md readers, Claude-style contexts, Gemini CLI, Cursor, GitHub Copilot coding agent, and Aider-style workflows.
- Structured `tech-route.json` schema guidance.
- Renderers for PPTX, SVG, Draw.io, Excalidraw, Mermaid, HTML, Markdown, and JSON.
- Academic paper-framework guidance and open-source reference notes.
- Complete academic demo with source brief, route JSON, editable outputs, and English/Chinese walkthroughs.
- English and Chinese README files.
