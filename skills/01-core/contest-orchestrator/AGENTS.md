# contest-orchestrator development rules

## Goal

Maintain a deterministic mathematical-modeling contest orchestrator. The v4.18 stable release provides evidence-bound COLLAB decision gates, claim-driven visual planning, capability-driven appendix coverage, and dedicated provenance for problem-analysis flowcharts, technical-roadmap diagrams and scientific schematics, while preserving scope selection, typed model-blueprint composition, structured per-subproblem modeling evidence, modeling-solution input/derivation contracts, cross-question symbol/interface checks, abstract evidence/numeric provenance, source-level layout/reference checks, formal-delivery drift detection, literature landing, strict LaTeX appendix input/material/minted checks, Windows-safe UTF-8 LaTeX fallback, and reproducible replay.

## Protected state

- Preserve all existing user changes and untracked competition replay data.
- Never run destructive Git cleanup or reset commands.
- Do not write live contest artifacts into this skill directory.
- Use isolated temporary directories for generated test papers and reports.
- Keep secrets and personal identifiers out of source, fixtures, and reports.

## Architecture

- `SKILL.md` is the concise entrypoint and router; `VERSION` is the single version source.
- Detailed operational policy belongs in `references/`.
- Deterministic checks belong in `scripts/` and must return meaningful exit codes.
- Data result figures route through `ModelViz → scipilot-figure-skill`; problem-analysis flowcharts and technical-roadmap diagrams route to `tech-route-maker`; mechanism, force and geometry schematics route to `tikz-scientific-figures`; Draw.io is explicit-request only.
- `scope_router.py` is the read-only scope/evidence planner; `delivery_all.py` is the canonical end-to-end delivery command for FULL_CONTEST.
- Academic prose is routed through the local `academic-writing` adapter; claim-centered editing is opt-in and its `mathmodel_patch_guard.py` must pass before a prose patch is merged into a contest paper.

## Validation

Run these checks before a release:

```text
python -m compileall -q scripts tests planner memory
python -m unittest discover -s tests -p "test_*.py"
python scripts/skill_health_check.py . --strict --smoke
python -X utf8 <skill-creator-root>/scripts/quick_validate.py .
python scripts/replay_profiles.py --strict
```

The current stable release is 4.18. Preserve `full-contest-legacy` as the v4.16 compatibility baseline.
