---
name: claim-centered-editing
description: Use when editing mathematical-modeling paper prose around claims, evidence, defensive wording, conclusion scope, or paragraph-level argument structure.
---

# Claim-Centered Editing

Use this module only for ordinary prose. Keep the model, formulas, symbols, units, numbers, citations, tables, figures, code and result sources unchanged.

## Required input

Before editing, confirm:

- the target manuscript and exact editable chapters;
- frozen model, data, results, citations and figure registry;
- evidence paths for the claims under review;
- an isolated before-copy for `mathmodel_patch_guard.py`.

If evidence is missing, do not fill the gap with cautious wording. Return one of:

- `【需要作者补充证据】` when the gap does not invalidate the core claim;
- `【需要作者重审主张】` when the gap can change the core claim or its conclusion.

## Editing contract

Build an internal claim table for core claims only:

```yaml
claims:
  - claim_id: claim-01
    claim: "原文核心主张"
    evidence: ["项目相对路径或公式/结果/图表/引用定位"]
    supported_scope: "证据直接支持的任务、数据和设置范围"
    boundary_location: "方法、结果或讨论中的唯一边界位置"
```

Process each paragraph in this order:

0. 国赛内容红线扫描：按 `references/cumcm_content_redlines.md` 检查目标段落，命中时在作者确认项中追加【国赛内容红线：xxx】，不自行改写内容层问题。
1. Keep claims that are supported and advance the paper's main line.
2. Remove sentences that add no fact, evidence, reasoning or necessary boundary.
3. Merge repeated background, conclusions and boundary statements.
4. Narrow conclusions to the scope directly supported by evidence.
5. Preserve genuine local negative results; do not generalize them into a global limitation or delete them.
6. Ensure each paragraph has one primary argumentative task.

The editor may restructure the abstract, introduction, result order, discussion and conclusion when no new fact is introduced. Real boundaries appear once, in the section where the reader needs them.

## Output contract

When this module is requested, output only:

1. the complete revised prose;
2. the author confirmation items using only the two required labels above.

Do not output line-by-line change logs, scores, generic review commentary or editor dialogue. Never place the claim table or author confirmation items in the manuscript, PDF, appendix or formal delivery package.
