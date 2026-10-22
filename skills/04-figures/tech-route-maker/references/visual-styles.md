# Visual Styles

Use this reference when asking the user to choose a visual style. Ask explicitly. Do not infer style from "paper", "defense", "presentation", or similar words.

## Style menu

1. `academic-blue`
   - White background, blue headers, light blue stage fills.
   - Useful for theses, reports, and general academic diagrams.

2. `blue-green-research`
   - Blue and teal accents with neutral gray text.
   - Useful for science and engineering topics.

3. `monochrome-paper`
   - Black, white, and gray only.
   - Useful for print-safe papers and journals.

4. `defense-color`
   - Stronger multi-color stage palette.
   - Useful for slides and oral presentations.

5. `minimal-gray`
   - Low-saturation gray, white, and one accent.
   - Useful for technical documentation.

6. `nature-editorial`
   - White background, restrained color blocks, high whitespace, crisp labels.
   - Useful for polished academic presentation, without imitating a specific publication template.

7. `accessible-high-contrast`
   - High contrast, colorblind-safe palette, thick connectors.
   - Useful when readability matters more than decoration.

8. `dark-technical`
   - Dark background with bright but restrained accents.
   - Useful for engineering demos and technical talks.

9. `soft-pastel`
   - Soft category colors, low contrast boxes, clear connector lines.
   - Useful for workshop and planning views.

10. `schematic-precision`
   - Exact module boundaries, typed arrows, controlled labels, and clean line-art.
   - Useful for paper method and architecture figures where interfaces matter.

11. `editorial-clarity`
   - Sparse modules, strong hierarchy, low text density, and caption-supported definitions.
   - Useful for intro figures and fast first-glance comprehension.

12. `mechanism-snapshot`
   - Central mechanism, zoom callout, cause-effect arrows, and compact internal motifs.
   - Useful for explaining why a method works.

13. `evidence-infographic`
   - Method route plus small evidence cards, metric badges, or ablation anchors.
   - Useful when a route must connect to results without inventing numbers.

14. `premium-scientific`
   - Restrained color, vector-safe landmarks, high whitespace, and polished academic composition.
   - Useful for publication-style paper figures and high-quality defense slides.

15. `advertising-clean-campaign`
   - Clean brand-neutral campaign map with audience, insight, creative, media, launch, and KPI accents.
   - Legacy/experimental style for explicit advertising strategy and campaign-production route diagrams.

16. `proposal-pastel-route`
   - White canvas, clear title pill, low-saturation pastel logical regions, section labels, dashed group borders when useful, and white editable node cards.
   - Useful for Chinese thesis proposals, grant applications, academic project routes, and research reports where the diagram must look polished but still formal. Use a left-side phase axis only when the user explicitly chooses a long vertical layout.

17. `grant-linework`
   - White canvas, black or gray linework, dashed section boundaries, minimal fills, and strict box-arrow hierarchy.
   - Useful for print-safe proposals, journal supplements, or reviewers who prefer conservative technical-route diagrams.

18. `wide-collaboration-map`
   - Landscape composition with side axes, central collaboration modules, dashed system boundaries, and restrained blue/green emphasis.
   - Useful for project reports, industry-academia collaboration, policy-support diagrams, and operations route maps.

19. `cn-polished-pastel-academic`
   - White canvas, centered title pill, pastel stage regions, left phase axis when vertical, dashed rounded group boundaries, and white editable node cards.
   - Useful for Chinese thesis proposals, opening reports, topic applications, and research-route posters.

20. `cn-blue-green-proposal`
   - White canvas, blue/green academic accents, wide section labels, clean matrix regions, and restrained connector arrows.
   - Useful for Chinese paper method frameworks, engineering project reports, and research-summary diagrams.

21. `cn-soft-grant-report`
   - White or near-white canvas, muted blue headers, soft document-like panels, reviewer-facing note areas, and conservative dashed boundaries.
   - Useful for grants, project applications, and formal research reports.

22. `cn-reviewer-linework`
   - Black/gray linework, minimal fills, dashed boundaries, and print-safe hierarchy.
   - Useful for Word documents, application forms, reviewer-safe PDFs, and low-color printing.

23. `cn-defense-poster`
   - Polished defense-style academic palette with blue, teal, green, cream, and pink stage accents.
   - Useful for academic slides and poster-style route overviews.

## Aesthetic Baseline

Use these style rules when the user asks for a polished technical route diagram:

- Start with a white or near-white canvas. Most high-quality academic route maps rely on clean whitespace, not decorative backgrounds.
- Use a clear title band or title pill; avoid tiny titles floating above dense diagrams.
- Separate structure from skin: first choose the route layout, then apply the visual style.
- Prefer low-saturation pastel regions for academic proposal routes: teal, light blue, pale yellow, pale green, soft pink, and warm cream.
- Use dashed boundaries for logical groups, chapters, work packages, or evidence scopes.
- Keep content nodes white with dark text; use color on stage headers, bands, side labels, or group regions.
- Use matrix or framework sections as the default academic route structure. Use a left-side phase axis only for long vertical research routes explicitly selected by the user.
- Use landscape collaboration maps when the route is about actors, resources, channels, policies, platforms, or operational touchpoints.
- For Chinese thesis/proposal/grant diagrams, use `references/local-style-study.md` and prefer the dedicated `cn-*` styles before generic `presentation-clean`.
- For Chinese text, allocate larger label boxes and fewer words per node than English examples.
- Keep arrowheads visible but not visually heavier than the nodes.
- For GitHub/README previews, prefer large readable SVGs and avoid two-column compression when labels become too small.

## Style rules

- Use color to encode stage category, not decoration.
- Keep connector lines darker than node fills.
- Avoid dense gradients and decorative backgrounds.
- Use enough whitespace to keep every label readable.
- Use one main font family per output.
- For PPTX and SVG, keep labels as editable text.
- For monochrome output, vary borders, fill intensity, or line styles instead of relying on color.
- For academic figures, visible style must serve the reader question and selected figure subtype.
- For legacy campaign diagrams, visual style may be more presentation-oriented, but audience, channel, and measurement logic must stay explicit.
- Do not transfer paper-specific facts, claims, metrics, labels, or symbols from visual references into a new diagram.

## Palette defaults

Render scripts provide default palettes for all style IDs. The user may later ask to change colors; update `theme` in `tech-route.json` and re-render.
