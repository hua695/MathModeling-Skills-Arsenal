# Harness writer-driven visual preparation

This document applies only when a control explicitly sets `visual_workflow: writer_first_draft`. New Harness controls use `chapter_parallel` and must read [逐章批准写作与并行图表](harness_chapter_parallel.md). Historical controls without either value retain their old interpretation. This changes Harness only. It does not import MathorCup batch numbers, page rules or model routes.

## Sequence

H0-H6 retain their requirements. After genuine H6 user approval, the registered H8 paper agent prepares an initial body draft from frozen scientific evidence, then chooses figure/table/text needs. This is preparation for H7, not formal H8 completion. H7 remains figure execution and selected-version review. H8 integrates selected figures through its existing chapter cards, edits the full paper and writes the final abstract. H9 retains the complete final delivery gate.

The initial draft can cover the body or the related sections needed to establish visual requirements. Harness retains chapter-granular formal writing; it does not adopt MathorCup's four-batch schedule. Draft placeholders are internal, with no fabricated trends or visual-QA claims.

Writer proposes a whole-paper writing plan from H6-verified model/interpretation cards and frozen results. Formal figures and visual-plan approval are not prerequisites for this first plan. User approves `H7_WRITING_PLAN` before drafting. The draft has no extra approval gate. Writer then selects visual needs; user approves `H7_VISUAL_PLAN`, binding both draft and visual plan, and transfers the requirements to the figure chat. Main-agent transfer requires explicit user authorization. Figure owns professional visual expression and may report evidence gaps.

Reuse the approved writing decisions in the formal H8 author brief and chapter cards. Do not ask for the same unchanged plan again merely because the node label changes. Material changes to chapter purpose, scientific claims or scope require targeted review; ordinary figure placement is reconciled against the already selected assets. Formal H8 node approval remains required. Figure-version selection and final H7 approval may be confirmed in one user review, with truthful separate gate records bound to the current files.

## Records

Reuse the existing global dispatch list, registered H8 identity and review/approval files. `nodes.H7.writer_preparation` contains:

```yaml
writing_plan: {path: paper/writing_plan.yaml, sha256: <actual-digest>}
plan_review_packet: .contest/reviews/H7_writing_plan.yaml
task_id: <actual-preparation-task-id>
draft: {path: paper/draft.tex, sha256: <actual-digest>}
draft_completed_at: <timezone-aware-time>
```

The actual dispatch has `node_id: H8`, `owner_role: 论文 agent`, `dispatch_kind: writer_preparation`, the registered H8 instance/model/effort and normal task path/hash, timestamp, run identity and actual receipt. Its task card uses `scope.phase: H8_draft_preparation` and inputs the approved plan plus frozen scientific sources. This narrowly identified dispatch follows H6 and writing-plan approval; every other H8 dispatch still follows formal H7 approval. Formal H8 uses a different integration task card/dispatch. Do not backfill receipts, change H8 status or invent node approvals to justify preparation.

`visual_argument_plan.yaml` adds `prepared_by_role: 论文 agent`, the exact `draft` path/hash and `prepared_at`. Preserve all existing visual-slot, evidence, template, mechanism and cross-question contracts. H7 generation occurs after draft completion and `H7_VISUAL_PLAN`, using the existing approved-plan hash binding. Scientific visual obligations are retained.

`nodes.H7.figure_selection_review_packet` points to a `H7_FIGURE_SELECTION` packet binding the current registry and actual selected SVG/PNG files. User selection follows generation and precedes final H7 approval. H8 uses these selected versions; changing them invalidates selection. Existing provenance, QA and paper-integration checks remain.

## Read-only admission

`python scripts/check_harness_control.py <project-root> --preflight-draft` performs the real H6 checks, then checks writing-plan approval and any recorded preparation work. Before dispatch, draft and figures are not required. It reports `through: H7-draft`; PASS is readiness for authorized drafting, not H7/H8 completion. No state or approval file is written.

Normal `--through H7/H8/H9` retains all formal checks plus preparation/selection binding. Initial drafting relies on H6-frozen science, not a false final H8 readiness signoff. Final H8 still validates complete paper materials, author brief, chapter cards, continuity and claim coverage against selected figures. Scientific gaps return to H5/H6, representation gaps to H7. Models, bootstrap capability policy, literature ownership and G0-G6 remain unchanged.
