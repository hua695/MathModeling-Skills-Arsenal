# Before / After Quality Comparison

Baseline: repository commit `cf5a18d` before the v0.3 reliability work. Current: v0.3.0 candidate outputs regenerated from UTF-8 demo sources.

## Result

The update is a measurable improvement in correctness, traceability and layout reliability. It does not claim that an automatically generated diagram is publication-ready; users still need to edit the deliverable.

| Area | Before | v0.3.0 | Improvement |
|---|---|---|---|
| Evidence coverage | Inferred nodes increased the evidence percentage. | Only hash-verified source evidence counts; inference has a separate percentage. | Removes misleading 100% scores. |
| Source integrity | Demo source hashes were empty. | Every demo source has a stable ID and matching SHA-256. | Detects missing, changed or substituted sources. |
| Evidence locators | Nonempty lists were treated as evidence. | Source IDs, paths, locators and text presence are checked where extractable. | Prevents structurally empty evidence claims. |
| Final rendering | Rendering could proceed without validation. | Strict gate blocks incomplete domain context, source failures, evidence gaps, inference and unresolved questions. | Prevents draft content from looking final. |
| Layout/style names | Unknown names silently used generic fallbacks. | Unsupported identifiers fail explicitly. | Prevents accidental wrong templates. |
| Stage node retention | Mainline and A4 layouts kept only the first three nodes. | All 2-6 allowed nodes receive editable boxes. | Eliminates silent content loss. |
| Chinese text integrity | Generated artifacts were not systematically scanned for mojibake. | UTF-8 and common mojibake signatures are checked in CI. | Reduces corrupted Chinese output risk. |
| Output QA | Representative subsets were parsed. | Every node label is checked across nine formats, plus geometry overlap and PPTX/XML/JSON parsing. | Detects cross-format drift. |
| Agent installation | Adapter files existed, but installation was mostly manual. | Verified `gh skill install` commands plus an explicit-target fallback installer. | Makes the same Skill portable to many hosts. |

## Current Verification Numbers

- 8 demos passed strict validation.
- 103 visible nodes were retained in every generated format.
- 72 demo-format combinations passed content-parity checks: 8 demos x 9 formats.
- Every demo reported complete domain context, verified sources, 100% evidence coverage, 0% inferred coverage and no unresolved questions.
- 8 core unit tests passed, including locator verification, six-node mainline/A4 retention, unknown-layout rejection and deterministic PPTX generation.
- UTF-8/mojibake scanning passed.
- Draft mode was tested separately: strict validation rejected the incomplete template, while `--allow-draft` rendered it with visible blockers.

## Visual Review

| Example | Layout | SVG canvas | Nodes | Review result |
|---|---|---:|---:|---|
| `academic-paper-demo` | `cn-research-method-matrix` | 1380 x 1030 | 14 | Clear matrix hierarchy, readable labels, straight stage flow, no overlap. |
| `thesis-proposal-demo` | `cn-a4-stage-route` | 1240 x 1754 | 13 | Centered blue stage headers, no left phase axis, readable portrait proportions. |
| `engineering-energy-system-demo` | `cn-ppt-mainline-route` | 1920 x 1080 | 15 | 16:9 mainline, explicit final-output bar, straight arrows and balanced five-stage spacing. |
| `biomedical-mechanism-demo` | `cn-a4-stage-route` | 1240 x 1754 | 12 | Domain-specific stages, consistent card widths and no connector/text collision. |

The supplied HGDY reference image remains unchanged; it is only cropped as a documented example. The generated Draw.io XML is a separate editable reconstruction.

## Remaining Limits

- Visual quality still depends on concise labels and correct domain extraction.
- The renderer cannot decide whether a scientific claim is true; it verifies provenance and structure, not scientific validity.
- Institutional, journal and competition templates still require manual fitting.
- PPTX, SVG and Draw.io outputs should be treated as editable first drafts, then revised by the user.
