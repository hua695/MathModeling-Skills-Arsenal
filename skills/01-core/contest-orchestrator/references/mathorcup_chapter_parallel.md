# MathorCup M4 chapter-approved writing and parallel figures

Apply this contract only when a new control sets `nodes.M4.visual_workflow: chapter_parallel`. It replaces the new-run `writer_first_batches` sequence. Historical controls with no workflow field or `writer_first_batches` retain their original interpretation and records. This contract changes M4 writing cadence only: M1–M5 approval, user-accessible role registration, M3 independent validation, figure provenance and M5 delivery obligations remain in force.

## Sequence

1. The writer submits `paper_argument_blueprint.yaml` and the language profile. The user approves `M4_WRITING_PLAN` after material readiness and claim coverage are bound.
2. The blueprint preserves final `global.chapter_order`, but its `global.writing_order` starts with modeling/solution chapters in dependency order, then validation, evaluation, conclusion, analysis, front matter and appendix; the abstract is last. Each order contains every chapter exactly once. Maintain hypotheses and symbols before and during core writing; assemble their reader-facing presentation later.
3. The writer produces one complete chapter. It answers its planned reader question with frozen evidence and required derivation, comparison, interpretation and continuity. It is not an outline, a placeholder or a promise to rewrite later.
4. `论文辅助` makes a local, read-only chapter review. The user approves `M4_CHAPTER:<chapter_id>`, which binds only the immutable chapter draft and that review. The next chapter cannot be dispatched until the immediately preceding chapter in `writing_order` has this approval.
5. After the chapter approval, the writer may issue a self-contained figure prompt. The user transfers the prompt to the accessible figure role; no automatic cross-chat transfer follows from this contract. Figure work and the next chapter may proceed concurrently.
6. Figure repairs create a later immutable prompt revision for the same chapter. They do not revoke an unchanged chapter approval, rerun its review, or block the next chapter. A substantive change to model, data or result evidence follows the existing impact-scoped scientific verification path.
7. After all non-abstract chapters are approved, `nodes.M4.abstract_framework_task_id` identifies the actual separate writer task that submits the abstract framework for `M4_ABSTRACT_FRAMEWORK`. The abstract chapter is drafted last and receives its own chapter approval. Formal integration then produces the final manuscript and whole-paper review. M4 node approval follows that review.

Paragraph form follows the argument; this contract sets no sentence, paragraph, or section-length template. The chapter approval is the human quality decision. Record checks provide evidence and sequencing, but do not prove prose quality.

## Blueprint schema

Use `templates/mathorcup_paper_argument_blueprint.yaml`. `global` contains nonempty `central_thesis`, `reader_journey`, official-rule-based `target_length`, `chapter_order` and `writing_order`. Each `chapters` item has:

```yaml
chapter_id: Q1_model
kind: modeling
depends_on: []
reader_question: How is the decision model formed from the verified inputs?
expected_answer: The frozen model and derivation establish the feasible decision rule.
role: Q1 model and solution
page_capacity: 3-5
figure_ids: []
table_ids: []
claim_ids: [C-Q1-1]
evidence_refs: [{path: results/Q1.json, sha256: <digest>}]
```

Allowed `kind` values are `modeling`, `validation`, `evaluation`, `conclusion`, `analysis`, `front_matter`, `appendix`, and `abstract`. `modeling` is first in `writing_order`; kinds are nondecreasing in that order; each dependency occurs earlier; and `abstract` is last. A chapter can have no visual prompt only when its chapter record declares `visuals_required: false`.

## Chapter records and approvals

`nodes.M4.writing_chapters` contains one entry per blueprint chapter:

```yaml
chapter_id: Q1_model
task_id: MC-M4-CHAPTER-Q1-001
draft: {path: paper/drafts/Q1_model.tex, sha256: <digest>}
draft_completed_at: 2026-10-30T10:00:00+08:00
quality_review: {path: .contest/reviews/Q1_model_quality.yaml, sha256: <digest>}
review_packet: {path: .contest/reviews/Q1_model.yaml, sha256: <digest>}
visual_prompts: []
```

The review has `status: ready`, the exact `draft_sha256`, and `checks` for `problem_answer`, `model_and_derivation`, `result_comparison`, `interpretation`, `continuity`, `evidence_provenance`, `language_profile_terms`, `first_use_symbol_definitions`, `claim_evidence_coverage`, `metadiscourse`, and `negative_echo`. Scientific argument checks may use `{status: not_applicable, reason: ...}` where justified. Evidence provenance and the five prose checks must be `PASS`; `model_and_derivation` must also pass for a modeling chapter. The chapter approval packet records `review_type: paper_chapter_review` and `reviewer_skill: 论文辅助`. The chapter record's actual `论文辅助` skill invocation binds this report through `evidence_ref` and `evidence_sha256`; it is a local review, not a repeated whole-paper audit.

The `M4_CHAPTER:<chapter_id>` review packet contains exactly the draft and quality review as important artifacts. Its approval timestamp is strictly later than `draft_completed_at`. It never binds a mutable figure prompt or figure asset.

## Writer and figure task cards

Writer phases are `plan`, `draft`, `figure_prompt`, `abstract_framework`, and `write`. `draft` and `figure_prompt` bind `scope.chapter_id`; the latter can occur only after the matching chapter approval and must input that exact approved draft and the approved whole-paper plan. Writer draft calls input the approved plan and all planned chapter evidence references. The final `write` is the integration call named by `nodes.M4.integration_task_id`.

Each `visual_prompts` item is immutable:

```yaml
revision_id: Q1_model-r2
task_id: MC-M4-FIGURE-PROMPT-Q1-R2
prompt: {path: paper/visuals/Q1_model-r2.md, sha256: <digest>}
visual_plan: {path: paper/visuals/Q1_model-r2.yaml, sha256: <digest>}
prepared_at: 2026-10-30T11:00:00+08:00
supersedes: Q1_model-r1
generation_task_id: MC-M4-FIGURE-GEN-Q1-R2
figure_selection: {path: paper/visuals/Q1_model-r2_selection.yaml, sha256: <digest>}
figure_selection_review_packet: {path: .contest/reviews/Q1_model-r2_selected.yaml, sha256: <digest>}
```

The visual plan records `owner_role: writer`, `chapter_id`, `revision_id`, the approved `draft`, and nonempty `slots` where visuals are requested. A slot has a unique `slot_id`, `representation` of `figure`, `table`, or `text`, reader question, body anchor, claim and hash-bound evidence. Figure slots also declare the permitted generation route. The figure `generate` task binds `chapter_id` and `revision_id`, and inputs that exact draft, prompt and visual plan. Its selection file has matching `chapter_id`, `revision_id`, and `assets: [{slot_id, path, sha256}]`, where each selected asset is SVG. The `M4_FIGURE_SELECTION:<chapter_id>:<revision_id>` packet binds both that selection and every selected SVG/PNG pair. Table/text-only prompts do not dispatch figure generation or selection but remain subject to their existing content checks. No extra approval is required merely to issue or revise a prompt.

At final M4 closure, aggregate `visual_argument_plan.yaml` equals the latest visual-plan slots of all requested chapters. Each registry figure binds `chapter_id`, `prompt_revision_id`, `generation_task_id` and the latest selection's SVG `selected_asset`; it also retains the existing paper copy, source, label, SVG/PNG, editable-source, QA, provenance and paper-integration fields. Existing route, SVG/PNG, editable-source, QA, provenance and paper-integration checks apply. Unfinished figure work blocks this final closure, not subsequent chapter drafting.

## Final integration

After the abstract chapter approval, `nodes.M4.integration_task_id` identifies the writer `write` task. `nodes.M4.final_manuscript` is its immutable output. `nodes.M4.final_review_packet` requests `M4_FINAL_PAPER` and binds the final manuscript, PDF, all approved chapter drafts, the current figure registry and the final visual plan. It records the whole-paper read-only `论文辅助` review. Its actual skill invocation binds that review using `evidence_ref` and `evidence_sha256`. The review includes the ordinary chapter checks plus `abstract_contract` and `whole_paper_final`. Only then may the normal M4 node review and M5 delivery proceed.
