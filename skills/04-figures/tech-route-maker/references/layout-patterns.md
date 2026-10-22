# Supported Layout Patterns

Only the identifiers in this document are accepted by the validator. Unknown or aspirational layout names fail explicitly; the renderer never silently substitutes a generic flowchart.

## Recommended Research And Engineering Layouts

| Layout | Best use | Rendering grammar |
|---|---|---|
| `academic-method-framework` | Paper method figures and defense overviews | Side-labeled matrix with objective, evidence, method, validation and output regions. |
| `proposal-matrix-route` | Thesis proposals and research plans | Matrix emphasizing objective, research content, key technology, validation and deliverables. |
| `cn-research-method-matrix` | Chinese paper and thesis method figures | Wide Chinese academic matrix with concise editable node cards. |
| `cn-paper-framework-canvas` | Chinese paper framework variants | Same audited matrix family with a paper-first canvas. |
| `engineering-architecture-route` | Engineering systems and platforms | Layered system regions, flows, validation and deliverables. |
| `software-system-route` | Software architecture and data/service routes | System-oriented layers rather than a thesis-proposal chain. |
| `cn-wide-project-map` | Chinese engineering reports and energy systems | Wide project map with work packages and explicit system boundary. |
| `cn-ppt-mainline-route` | Defense PPT and formal project presentations | 16:9 five-stage mainline, up to six support nodes per stage and a final-output bar. |
| `cn-a4-stage-route` | Word, thesis and portrait report figures | Centered vertical stage sections without a left phase axis; up to six nodes per stage. |
| `cn-proposal-poster-route` | Chinese opening reports and long research routes | Top-to-bottom proposal poster with a visible phase axis. |
| `cn-grant-application-route` | Chinese grants and project applications | Dense reviewer-facing stages for questions, content, methods, validation and outputs. |
| `cn-monochrome-linework-route` | Print-safe grant or report figures | Proposal route rendered with restrained monochrome linework. |
| `horizontal-stages` | Tool, agent and general workflow pipelines | Left-to-right stages with vertically stacked support nodes. |

## Supported Aliases And Specialized Variants

- Mainline aliases: `ppt-mainline-route`, `research-ppt-mainline`.
- Portrait alias: `a4-stage-route`.
- System aliases: `engineering-architecture`, `layered-architecture`, `wide-collaboration-map`.
- Vertical variants: `vertical-research-route`, `proposal-phase-axis`.
- Horizontal variants: `timeline-swimlane`, `campaign-funnel`, `creative-production-pipeline`.
- Legacy advertising layout: `campaign-strategy-map`.

The specialized names above currently share a documented renderer family. Use them only when that family matches the requested reading direction. Do not claim that they implement a distinct closed-loop, evidence-centered, hub-and-spoke, baseline comparison or case-walkthrough algorithm.

## Selection Rules

1. Confirm the target medium: PPT, Word/paper, engineering handoff, Draw.io maintenance or web documentation.
2. Confirm the discipline and project type before selecting a route grammar.
3. Use `cn-ppt-mainline-route` for a readable presentation main figure.
4. Use `cn-a4-stage-route` for a portrait document figure.
5. Use matrix layouts when the reader must compare objective, content, method and validation sections.
6. Use system layouts when modules, layers, data, energy or material flows matter more than research phases.
7. Use a phase-axis route only when the user explicitly requests a long vertical structure.

## Structural Rules

- Keep the main route to 4-7 stages.
- Keep each stage to 2-6 visible nodes.
- Keep labels to short noun phrases; put explanations in `detail`, HTML, Markdown or the quality report.
- Every JSON node must receive a rendered box. Truncating nodes to fit a template is a validation failure.
- Keep semantic edge labels in the route model, but hide them on the main canvas by default.
- Prefer a few straight stage-to-stage arrows. Avoid curved, elbowed or densely auto-routed connectors unless explicitly requested.
- Keep final deliverables visually explicit.
- Use feedback arrows only when supported by source evidence.
- Generated PPTX, SVG and Draw.io files remain editable drafts and require user revision before formal use.
