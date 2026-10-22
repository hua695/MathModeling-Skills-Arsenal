# Project memory

## Stable decisions

- The canonical data-figure workflow is `ModelViz → scipilot-figure-skill`; register `generator: modelviz` and `semantic_qa: scipilot-figure-skill`.
- Problem-analysis flowcharts and technical-roadmap diagrams use `tech-route-maker` and register `generator: tech-route-maker`; mechanism, force and geometry schematics use `tikz-scientific-figures` and register `generator: tikz-scientific-figures`; Draw.io is explicit-request only.
- `COLLAB` pauses only at G0–G6 decision packages and binds approvals to artifact SHA-256 hashes. Routine writing and formatting remain continuous.
- `full-contest-harness` uses H0–H9 with fixed roles, explicit per-node model routes, task cards, review packets and SHA-256-bound user approvals; H8 `evidence_gap` returns to H5/H6/H7 and keeps the run paused.
- Appendix planning is coverage-first: each subproblem maps body material to real derivation, core code, and/or verification modules instead of manufacturing fixed appendix labels.
- Citation counts use unique citation keys actually referenced by the paper; repeated citation commands never increase the count.
- A final PDF must be newer than every source that can affect it and must have a usable Unicode text layer.
- Blank-page, large-whitespace, duplicate-heading, and body-overflow checks are delivery gates; code-appendix warnings use separate thresholds.
- Formal deliverables must live in a stable project workspace, never in the installed skill directory or an operating-system temporary directory.
- Existing dirty-worktree changes and competition replay artifacts belong to the user and must be preserved.

## Release policy

- A version is released only after scope-router tests, structure validation, unit and regression tests, health checks, isolated end-to-end testing, citation-count regression, modeling-chapter/appendix/code/anonymity checks, Windows-output regression, and a non-mutating real-project replay pass.
