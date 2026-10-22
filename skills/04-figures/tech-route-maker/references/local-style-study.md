# Local Academic Route Style Study

Use this reference when the user asks for Chinese thesis, proposal, grant, project-application, or research-report technical route diagrams. The rules here are distilled from a private local corpus of editable PPTX, DOCX, VSDX, VSD, JPG, and PNG technical-route templates. The original template images are not bundled in this open-source repository.

## Corpus Findings

- Most high-quality academic route diagrams are white or near-white canvases with restrained color, not decorative backgrounds.
- Portrait/poster layouts are common for Chinese thesis proposals and project applications.
- Landscape layouts are common for defense slides, project reports, platform maps, and engineering systems.
- The most reusable visual language is: centered title, clear stage regions, colored stage tabs or side labels, white node cards, dashed group boundaries, and visible but lightweight arrows.
- Dense proposal diagrams work only when repeated content is compressed into grouped cards, panels, or small tables. A raw long process chain looks weak.
- PPTX, Draw.io, and SVG examples should preserve editable native shapes and text. Do not use screenshots as the main diagram.

## Preferred Template Families

### Chinese Thesis Proposal Poster

Use for opening reports, thesis proposals, topic applications, and research plans.

- Canvas: tall portrait poster.
- Structure: 4 to 7 macro stages, usually research objective, research content, key technology, experimental validation, expected outputs.
- Left side: colored phase axis when the diagram is long.
- Main area: dashed rounded stage regions with white cards.
- Style: pastel teal, blue, green, cream, pink, and warm gray.

Recommended layout/style:

- `layout`: `cn-proposal-poster-route`
- `style`: `cn-polished-pastel-academic`

### Chinese Grant / Project Application Route

Use for grant applications, project reports, and reviewer-facing technical routes.

- Canvas: portrait or balanced document page.
- Structure: proposal objective, research contents, scientific questions, key methods, validation, deliverables.
- Include optional note panels only when they help distinguish research content, objectives, methods, and scientific questions.
- Keep reviewer-facing logic explicit; avoid over-decorating.

Recommended layout/style:

- `layout`: `cn-grant-application-route`
- `style`: `cn-soft-grant-report`

### Chinese Academic Method Matrix

Use for paper method framework diagrams, thesis method chapters, and defense method slides.

- Canvas: balanced or landscape.
- Structure: matrix rows or work packages rather than a simple sequence.
- Side labels: objective, data, method, training/implementation, validation, output.
- Main cards: white nodes inside lightly tinted regions.
- Use edge labels for data flow, training, validation, or output transitions.

Recommended layout/style:

- `layout`: `cn-research-method-matrix`
- `style`: `cn-blue-green-proposal`

### Chinese Engineering Project Map

Use for engineering systems, energy systems, platform construction, and project reports.

- Canvas: landscape.
- Structure: system boundary, evidence/data, configuration/model, operation/control, validation/output.
- Use side labels and wide section regions.
- Do not force engineering projects into a thesis-proposal poster unless the user asks for a proposal figure.

Recommended layout/style:

- `layout`: `cn-wide-project-map`
- `style`: `cn-blue-green-proposal`

### Reviewer-Safe Linework

Use for conservative reviewers, black-white printing, Word documents, journal supplements, or low-color application forms.

- Canvas: white.
- Structure: same semantic route as the color version.
- Visuals: black or gray outlines, dashed boundaries, minimal fills.
- Use line thickness and spacing rather than color to show hierarchy.

Recommended layout/style:

- `layout`: `cn-monochrome-linework-route`
- `style`: `cn-reviewer-linework`

## Rendering Rules

- Prefer `poster-portrait` PPTX page size for `cn-proposal-poster-route` and `cn-grant-application-route`.
- Prefer 16:9 landscape for `cn-wide-project-map`.
- Keep title, subtitle, reader path, stage labels, and node labels from overlapping.
- Use larger Chinese text than English examples.
- Use white cards for visible nodes; use color on regions and tabs.
- Use dashed boundaries for stages, scopes, work packages, and evidence groups.
- Use curved or dashed connectors only for feedback, cross-stage dependency, or non-linear relation.
- Report density warnings when a stage has too many visible nodes for the selected layout.

## Asset Policy

- Do not copy private or third-party template images into generated outputs or public repository files.
- Recreate reusable visual grammar as original editable vector shapes.
- If a user explicitly provides a template they own, use it as an optional local input template and preserve its license boundary.

