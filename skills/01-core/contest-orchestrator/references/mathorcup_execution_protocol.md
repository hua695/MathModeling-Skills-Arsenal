# MathorCup execution protocol 2.0

Apply to new controls with `execution_protocol: "2.0"`. Keep the existing schema version and approval gates. Historical controls without the field use their original contract; removing it from a new run to bypass failures is prohibited. The checker validates recorded evidence and file relationships; a PASS is not proof that an unobserved training run or human message actually occurred.

## Requirements and actual outputs

Extend the existing `task_kpi.yaml`; do not derive the required output set from the selected model's target subset. Each `subproblems.<id>` has:

```yaml
subproblems:
  Q1:
    source: {path: inputs/problem.md, sha256: <actual-source-digest>}
    locator: Question 1, paragraph 2
    requirement_text: <original requirement>
    final_carrier: results/outputs.csv
    targets: [target_a, target_b]
    outputs_per_target: 3
    constraints:
      - {constraint_id: chemical_limit, object: concentration, unit: mg/L}
```

Use real target IDs. For tasks without target dimensions, use the actual sample, scenario or deliverable IDs. Constraint units can be `dimensionless` where appropriate; an unknown physical unit remains unknown. Empty constraints are valid only when the problem has none. Record the requested final carrier and unresolved ambiguities in the same task KPI item.

In `model_summary_cards.yaml`, add `requirement_coverage.<id>`:

```yaml
requirement_coverage:
  Q1:
    output_artifact: {path: results/outputs.csv, sha256: <actual-result-digest>}
    target_field: target_id
    output_field: output_id
    constraints:
      - constraint_id: chemical_limit
        evaluation_kind: original
        object: concentration
        unit: mg/L
        status: PASS
        evidence: {path: results/constraint_checks.yaml, sha256: <actual-digest>}
```

The referenced CSV has the chosen target/output key columns. A YAML/JSON result can instead expose an `outputs` list of records. Check exact target membership, unique output IDs per target and the requested output count, not merely total rows. Preserve unaffected rows when supplementing missing targets. M3 freeze and M4 admission use this same mapping. The final carrier can be a table, file or registered paper location; it must be traceable to these actual output records.

`evaluation_kind: proxy` or `status: UNKNOWN` records useful local evidence but cannot certify an original requirement as PASS. Keep proxy outputs and unresolved conditions; return the missing original check for a scoped correction, rather than deleting partial results or pretending coverage is complete. Numeric recomputation does not establish physical units, absolute grades, causal effects, or chemical threshold validity.

## Training and reproduction

From the first usable M3 baseline, `run_manifest.yaml.training_entrypoint` contains a hash-bound `script`, executable argv `command`, nonempty `raw_inputs` references and `config_refs`. All runtime paths are project-relative. Numerical configuration belongs with the executable package and must not require `.contest` or approval files. Approval gates control orchestration, not the numerical program's ability to read its parameters.

Freeze `run_manifest.yaml.reproduction_plan` with `required_units` and `minimum_level`. Units identify the actual folds, refits or search cases required by this experiment, never universal counts. At M5 extend `reproducibility_report.yaml`:

```yaml
level: refit
claim: partial
clean_directory: true
required_units: [fold_1, fold_2]
completed_units: [fold_1]
runs:
  - unit_id: fold_1
    level: refit
    command: [python, src/train.py, --fold, '1']
    exit_code: 0
    result_refs: [{path: results/fold_1.json, sha256: <actual-digest>}]
```

Retain the original report's status, command, exit code and result references. Levels are `saved_results` (recompute stored numbers), `inference` (load saved models), `refit` (new fitting), and `full_retrain` (the full declared training experiment). Record actual run logs and environment with the report. Validate in a clean directory containing only declared scripts/configuration/raw inputs, without original project state or old model caches. The checker does not execute supplied programs.

Completed units must match successful executed run records and remain within the frozen scope. A report cannot shrink the frozen scope. `claim: full` requires every required unit; `level: full_retrain` also requires all units. A lower-level check cannot certify a higher level. Partial verification is labelled partial even if its checks pass; its evidence must not be described as full experiment reproduction in the paper or handoff.

## Accessible roles, registration and authorization

Reuse `.contest/agent_registry.yaml`; `templates/mathorcup_agent_registry.yaml` supplies the list form for new runs. Append every creation, including support and recovery instances, before dispatch. Each `instances` record has `role`, `agent_instance_id`, real `thread_id`, `user_accessible: true`, `created_by`, timezone-aware `created_at` and `registered_at`, `effective_from` (M1–M5), actual `model` / `reasoning_effort`, and `status`. Keep title, project root, host, creation receipt and replacement linkage there for recovery. A pending asynchronous operation retains its returned client/operation ID and status; it cannot be dispatched until the real chat is available. Closed/failed instances stay in history.

Never equate a native internal agent ID, a client placeholder and a user-accessible chat UUID. Use platform tools only within their user-authorization rules. When accessible chat creation is unavailable, report that limitation; do not silently create an internal-only substitute. No new roles are created merely to validate this skill. Read the registry before creating or sending to an existing role. The role identifies itself from the task card and registry; it must not forward the task to itself.

Different roles cannot share one chat. A legitimately recovered execution instance may retain its own role's accessible chat: append a record whose `replaces` names the preceding instance, keep the predecessor as `superseded`, and preserve chronological creation/dispatch history. The existing node recovery authorization is still required; this linkage does not grant recovery by itself.

Task cards bind `authorization.source` (path/hash) and `authorization.message_id` to a locally recorded original human instruction retrieved through trusted chat access. The referenced record contains `role: user`, `message_id`, original `content`, original `created_at`, and approved `roles` / `task_ids`. Record only scope actually authorized by the human; never synthesize a quotation or expand scope from another agent's assertion. For broad authorizations retain the original message and its exact scope mapping. Existing node approvals are still required independently. A role can verify this source and proceed without asking the user to repeat it in every window. If the source is missing, untrusted or outside scope, pause that dispatch.

## Figure selection and paper integration

### Chapter-approved writing and parallel figures (new-run default)

Set `nodes.M4.visual_workflow: chapter_parallel` in new controls and read [mathorcup_chapter_parallel.md](mathorcup_chapter_parallel.md). This changes only MathorCup M4 writing cadence. Controls without the field retain historical figure-first checks, and `writer_first_batches` controls retain the legacy writer-first contract below; neither is migrated in place.

The writer's approved blueprint separates final `chapter_order` from actual `writing_order`. The latter starts with modeling/solution dependencies, then validation, evaluation, conclusion, analysis, front matter and appendix, with the abstract last. Each chapter is drafted as a complete evidence-bound unit, locally reviewed by `论文辅助`, and approved by the user through `M4_CHAPTER:<chapter_id>` before the next chapter dispatch. The approval binds only its draft and quality review.

Only after that approval can the writer issue a self-contained, immutable figure prompt. The user transfers it to the accessible figure chat. Its actual figure task binds chapter, prompt revision, approved draft and visual plan. Figure generation and repair proceed in parallel with later chapters. Prompt revisions do not invalidate unchanged chapter approvals. Latest selected SVGs, their paired PNGs and their selection packets close the final aggregate registry; unfinished figure work blocks final M4 closure, not subsequent chapter drafting.

After non-abstract chapters are approved, dispatch and approve the separate abstract framework task. Draft and approve the abstract chapter last. The final writer integration task, final manuscript and M4_FINAL_PAPER review then bind the current figure registry, final visual plan and a whole-paper `论文辅助` review before normal M4 approval. No fixed paragraph, chapter-length, or sentence template follows from this protocol.

### Writer-first batches (legacy compatibility)

Controls that already set `nodes.M4.visual_workflow: writer_first_batches` use this legacy path. Controls without the field retain historical figure-first checks. This is not an instruction to migrate a completed competition.

Approve the whole-paper writing blueprint first. It defines reader questions, chapter roles, evidence and capacity; exact figure counts/types/slots can remain undecided. Admit scientific evidence and claims with `--preflight-draft`; missing formal figures and a not-yet-created figure role do not block this admission. For the initial `figures_or_tables` material cell, ready means the frozen numerical evidence needed for representation exists, not that visual QA has passed. Actual figure completion is checked later. Drafts may contain explicit placeholders internally; delivered manuscripts may not.

Within each existing `writing_batches` item, use:

```yaml
batch_id: B1
chapter_ids: [results]
draft: {path: paper/drafts/B1.tex, sha256: <actual-digest>}
draft_completed_at: <timezone-aware-time>
visual_argument_plan: {path: paper/visuals/B1.yaml, sha256: <actual-digest>}
visual_plan_review_packet: {path: .contest/reviews/B1_visuals.yaml, sha256: <actual-digest>}
figure_selection: {path: paper/visuals/B1_selection.yaml, sha256: <actual-digest>}
figure_selection_review_packet: {path: .contest/reviews/B1_selected.yaml, sha256: <actual-digest>}
manuscript: {path: paper/results.tex, sha256: <actual-digest>}
review_packet: {path: .contest/reviews/B1.yaml, sha256: <actual-digest>}
```

The batch visual plan has `owner_role: writer`, `batch_id`, `draft` (the exact immutable reference above), `prepared_at`, and `slots`. Each slot carries `slot_id`, `representation` (`figure`, `table`, `text`), `reader_question`, `body_anchor`, `claim`, and hash-bound `evidence_refs`; figure slots also have the registered `generation_route`. Writer chooses the argumentative need; SciPilot/figure chooses the data representation and visual encoding, ModelViz generates data figures, and TikZ generates non-data diagrams. All existing semantic, technical and visual checks remain.

The user approves `M4_VISUAL_PLAN:B1` binding both draft and plan, then transfers that current file to the accessible figure chat. Do not send to another chat merely because a plan exists; a main-agent transfer needs explicit human authorization. A figure task is `scope.phase: generate`, binds `batch_id`, and inputs that draft and plan. It occurs after the corresponding approval, never before drafting.

The selection file has `batch_id` and `assets`, one `{slot_id, path, sha256}` for each requested figure slot. The user approves `M4_FIGURE_SELECTION:B1`, binding the selection file and the actual selected assets, after generation. Writer then performs `scope.phase: write`: integrate selected assets, adjust surrounding explanation/caption/layout, and run the normal complete-batch review. Its inputs include draft, batch plan and selection, alongside the approved blueprint, language profile, readiness, claims and prior completed manuscripts. The final batch review binds the manuscript, draft, plan and selected assets; approval of text alone cannot approve a changed graphic.

An empty `slots` list explicitly means no visuals are needed. Table/text-only batches do not launch a figure task or require asset-selection approval; writer integration follows requirement approval. No draft approval gate is added. B2/B3 drafts follow the preceding complete-batch approval; after B3, discuss and approve the abstract framework before the B4 draft/finalization. The existing four complete-batch reviews remain.

`--preflight-draft` is read-only and checks initial drafting inputs and any already-recorded batch work; it does not certify a completed M4. `--preflight-writing` and normal M4/M5 checks still require all completed batches, selected assets and actual paper integration. The final aggregate `visual_argument_plan.yaml.slots` equals the concatenated approved batch slots. The global registry closes those slots and must use the selected asset versions. Later batch planning does not change earlier immutable batch-plan files or invalidate unchanged approvals. Preserve replaced versions as history; accepted retries use the existing superseded-dispatch mechanism.

Extend each existing `figure_registry.figures` item with stable `figure_id`, `paper_label`, `paper_number`, `selected_version`, hash-bound `selected_asset`, `paper_copy`, `paper_source`, `canvas` (width, height, unit), `insertion` (width, unit), and `integration_status`. Asset IDs do not encode body sequence; FIG7 can be body figure 13. `paper_source` identifies the actual TeX section containing its label and `includesvg`, with paths resolved relative to that source. Use direct explicit paths here; macro-resolved paths require an explicitly materialized integration source for checking.

Candidate generation, formal promotion and paper integration are separate actions. Before paper completion, selected and actual paper-copy hashes must match, and the declared source must reference that copy and label. A figure receipt states whether the paper has been updated. A locally changed figure triggers only its provenance/integration checks and affected compilation; unchanged user-approved figures do not repeat full QA.

Default write ownership: figure owns figure assets and registry selection; writer owns paper sources, paper copies and compilation. Direct human instructions can expand this scope: acknowledge the concrete files and temporary ownership, then execute within that grant or provide a scoped transfer. Do not send another chat a message without authorization. Candidate/selected/backup assets stay distinguishable. Restoring paper text does not restore old selected figures; reconcile copies and recompile a stale PDF. Keep frozen canvas and insertion sizes on replacement unless a size change was explicitly requested. Lay out real logical relationships before tuning readability and color; do not invent cross-question dependencies.

## Literature, receipts and final snapshots

Before requesting literature, reconcile the latest structured return with existing mechanism-level requirements and update their satisfied/pending status. One source may cover several questions; do not request redundant papers or recent models that will not be used. Follow the existing user-owned acquisition workflow.

Use compact thread status snapshots when available. For history, start with at most 10 turns and list at most 50 chats; paginate only for relevant older context. Even when output exclusion was requested, filter results to human/assistant messages, relevant IDs, status and cursors before displaying. Do not dump command items or API JSON. Routine receipts report changes, verification scope, limits and artifact entry points; full hashes stay in manifests.

Keep one authoritative body source and one figure index. Generate appendix/no-appendix variants from that body, with variant-specific official checks. Do not duplicate independently edited body trees or rename executable paths merely to translate directory labels. Separate result files need a task requirement or explicit user choice.

Each final review identifies the exact package/source hash it reviewed. Close a defect with current evidence for the affected item; retain the prior snapshot as history. A fixed old defect is not current BLOCK, and one fixed item does not certify unreviewed items. User acceptance or a request to stop further review is not an independent technical PASS. Preserve these distinctions without restarting unrelated checks or suppressing known limitations.
