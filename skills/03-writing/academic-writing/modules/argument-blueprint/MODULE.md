---
name: argument-blueprint
description: Use when a Harness or MathorCup paper needs a prewriting argument blueprint that binds reader questions, claims, result meanings, figures, and frozen evidence before drafting.
---

# Argument Blueprint

Use this module before drafting a mathematical-modeling paper. Its purpose is to turn frozen technical material into a reader-oriented argument plan. It does not write manuscript prose and does not change any model, number, formula, citation, figure, or evidence file.

## Required input

For Harness with `visual_workflow: chapter_parallel`, H6-approved model/result evidence and the problem statement first produce an approved writing plan before any formal figures. Follow `contest-orchestrator/references/harness_chapter_parallel.md`: state the central thesis and reader journey, keep final `chapter_order` separate from actual `writing_order`, put modeling/solution dependencies first, and reserve the abstract for formal H8 last. Each chapter plan binds its reader question, expected answer and frozen evidence; its exact visual requirement is decided only after that chapter is complete and approved. Do not make figures, an aggregate visual plan or a closed registry circular prerequisites for the first chapter. Preparation never certifies H8 completion. `writer_first_draft` remains governed by `harness_writer_preparation.md`.

- Harness H8: `paper_narrative.yaml` with verified key results; H6-verified `result_interpretation_cards.yaml`; `paper_material_readiness.yaml`, `paper_claim_coverage.yaml`, frozen figure registry, and the problem statement.
- MathorCup M4: `problem_statement.md`, `task_kpi.yaml`, M3 `run_manifest.yaml`, `result_interpretation_cards.yaml` and `independent_validation.yaml`, verified `literature_sources.yaml`, and the current `competition_profile.yaml`. Historical figure-first runs also require the approved visual plan. With `nodes.M4.visual_workflow: chapter_parallel`, the initial blueprint does not require a visual plan or formal figures; separate final `chapter_order` from dependency-led `writing_order`, reserve the abstract for last, and keep exact slots/counts/types undecided until the corresponding chapter approval. Writer selects exact needs only after the approved chapter draft. Bind material-readiness and claim-coverage files to the approved blueprint before drafting; do not require them as inputs to the initial blueprint. Legacy `writer_first_batches` keeps its batch interpretation.
- hashes for every evidence reference.
- `contest-orchestrator/references/paper_author_evidence_protocol.md` when the reader-evidence protocol is enabled.

If a core result has no verified meaning, reason, scope, or evidence, return `evidence_gap` to the responsible node. Do not create explanatory language from unverified inference.

## Produce the blueprint

Create `paper_argument_blueprint.yaml` using the contest-orchestrator template for the active mode: `templates/paper_argument_blueprint.yaml` for Harness H8 and `templates/mathorcup_paper_argument_blueprint.yaml` for MathorCup M4.

1. State one evidence-bounded `central_thesis` and a `reader_journey` for the whole paper.
2. For every planned chapter, record the reader question, the chapter answer, argument IDs, evidence references, figure roles when known, and material that does not serve that chapter. In Harness or MathorCup `chapter_parallel`, also record `kind` and `depends_on`; do not turn this into a fixed paragraph or length template.
3. For each core argument, bind one result interpretation card, its evidence, why it matters, and its supported scope. Preserve the chain from problem need through model choice, derivation, result, decision meaning, and boundary.
4. Treat every figure, table, or text-only presentation as evidence with a named argumentative role and reader takeaway. In Harness or MathorCup `chapter_parallel`, choose exact figure slots only after the corresponding chapter approval; use `visuals_required: false` when none is needed. The final aggregate plan must equal the latest chapter-prompt slots. For Harness, include modern `global_visual_slots` and per-subproblem `visual_audit` slots. Do not list a visual merely because it is available.
5. Keep technical derivation available only to the modeling chapters that need it. Non-modeling chapters organize the argument and results without reproducing derivations.
6. For every chapter, record an `authoring_arc` with `opening_tension`, `evidence_sequence`, `interpretive_move`, and `transition_question`; these are author inputs, not manuscript headings.

## Output contract

Output only the populated `paper_argument_blueprint.yaml` and an `evidence_gap` record when required. The blueprint is an internal control artifact and must not be inserted into the paper, appendix, PDF, or delivery package.
