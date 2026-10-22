# FAQ

## Is this only for Codex?

No. It includes adapter files for several agent environments. `SKILL.md` remains the source of truth.

## Is the output editable?

Yes. PPTX uses native shapes, SVG uses vector/text elements, Draw.io uses editable diagram cells, Excalidraw uses scene JSON, Mermaid stays text-editable, and HTML/Markdown keep route data visible.

## Does the skill ask users to choose format, layout and style?

Before final rendering, it confirms the target medium, output formats, layout family and visual style in one concise grouped question. It may offer a preset as the default, but it must not silently guess these preferences from a field-agnostic request.

## What does strict validation check?

It requires complete discipline context, valid layout/style identifiers, existing source files with matching SHA-256 hashes, verified evidence for every visible node, no inferred nodes and no unresolved questions. Draft rendering can bypass final-quality blockers with `--allow-draft`, but not structural errors.

## Can it make paper figures?

Yes. The default `academic-method` preset is designed for paper method frameworks, manuscript figures, experiment routes, review frameworks and defense visuals. Users should still verify journal-specific formatting rules.

## Can it make thesis proposal routes?

Yes. The `thesis-proposal` preset is designed for research objectives, research content, key technologies, experiment validation and expected outcomes.

## Can it make engineering route diagrams?

Yes. The `engineering-system` preset is designed for system boundaries, modules, data or energy flow, validation layers and deliverables.

## Can it make advertising routes?

Only as a legacy or experimental use case. The core project is focused on research and engineering diagrams.

## Does it execute analyzed project code?

No by default. Source files are treated as untrusted evidence.

## Are generated diagrams ready to use directly?

No. They are editable drafts. Users should revise the generated PPTX, SVG or Draw.io files before academic, course, engineering or commercial use.
