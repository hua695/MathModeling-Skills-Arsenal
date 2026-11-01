# Harness 逐章批准写作与并行图表

`visual_workflow: chapter_parallel` 是 Harness 新运行的默认写作分支。它只改变 H6 之后的论文与图表时序；H0--H6 的科学证据、H7 的专业制图闭环、H8 的正式整合和 H9 的完整交付验收均不降级。`writer_first_draft` 与未设置该字段的历史控制文件继续按原有协议解释。

## 已批准的全篇计划

H6 的科学证据经用户批准后，固定 H8 论文实例先建立并提交 `writing_plan`。计划不是篇幅配额或段落模板，而是完整章节论证的路线图，至少包含：

- `central_thesis` 与 `reader_journey`；
- `chapter_order`：最终论文/目录中的呈现顺序；
- `writing_order`：实际创作顺序；
- 每个章节的 `chapter_id`、`kind`、`depends_on`、`reader_question`、`expected_answer` 与冻结的 `evidence_refs`。

实际创作必须先完成依赖链中的建模与求解章节，再依次处理验证、评价、结论、问题分析、前置章节和附录；摘要只在所有正文与附录整合后由正式 H8 最后写作。`chapter_order` 因此可以让问题分析、假设和符号说明在读者进入模型前出现，但不决定实际派发顺序。每一项 `depends_on` 必须已在 `writing_order` 中完成。

## 逐章闭环

1. H8 论文实例以不可变输入快照和实际任务收据写出一章完整正文，阶段为 `H8_chapter_draft`。它必须回答本章读者问题，给出本章应有的推导、结果比较、解释与承接，而不是提纲、占位符或待重写草稿。
2. 论文实例登记 `quality_review`，以当前 `draft_sha256` 绑定 `problem_answer`、`model_and_derivation`、`result_comparison`、`interpretation`、`continuity` 和 `evidence_provenance`。不适用项必须写出具体原因，不得伪造通过。
3. 主控生成 `H7_CHAPTER:<chapter_id>` 审查包。只有用户批准当前章节且哈希未变化，才能派发下一章。
4. 批准后，同一论文实例才为该章生成可独立转交的图表提示词，阶段为 `H8_figure_prompt`。提示词必须引用已批准的章节、视觉计划和冻结证据，说明读者问题、应支持的论点、允许数据/关系、禁止虚构内容、图注与正文落位。
5. 用户亲自把提示词交给图表会话。H7 依该提示词对应视觉计划、专业路由和 QA 制作图件；H7 生成任务必须登记 `chapter_id`、`revision_id`、`prompt_sha256` 与 `approved_visual_plan_sha256`。生成或返修可与下一章写作并行。没有用户的明确授权，主控不得自动跨会话转发。

图件返修只新建一个不可变 `visual_prompts` 版本，记录 `revision_id`、`task_id`、`prompt`、`visual_plan`、`prepared_at` 与 `supersedes`。它不修改已批准正文，不撤销 `H7_CHAPTER:<chapter_id>`，也不阻塞下一章。图件与冻结证据不符时，以冻结证据为准修图，不因图件返修自动派发 H5/H6 或重新审阅章节；只有模型、数据或结果本身被授权修改时，才沿既有影响范围做科学证据复核。

## H7、H8 与 H9 的边界

H7 仍负责把被转交的提示词落到已批准视觉计划、正确生成路由、SVG/PNG、可编辑源、登记和 QA；它不得凭提示词创造新结论。最终 H7 汇总计划只能包含每章**最新**提示词对应的槽位，且必须覆盖传统 `slots`、现代 `global_visual_slots` 与各小问 `visual_audit` 中的槽位，不能混入未经论文角色需求的图件。图件登记的每项都绑定 `chapter_id`、`prompt_revision_id` 和真实 `H7_generate` 的 `generation_task_id`。缺图或未完成返修不妨碍下一章正文的批准与派发，但会阻塞最终 H7 图件闭合与后续正式整合。

正式 H8 只整合经 H7 选定的图件版本，完成必要的图前引入、图后解释、图注、排版和跨章连续性编辑，不从头重写已批准正文。随后在全文正文与附录稳定后写最终摘要，并保持原有 H8 审查与批准。H9 仍运行完整交付审计；逐章批准和图件选择不能替代 H9。

## 记录边界

`writing_plan` 可从 `templates/harness_chapter_writing_plan.yaml` 初始化。`nodes.H7.writer_preparation` 保留 `writing_plan: {path, sha256}`、`plan_review_packet`（`H7_WRITING_PLAN`）和 `chapters`。章节条目示例：

```yaml
chapter_id: modeling_q1
task_id: <actual H8_chapter_draft task>
draft: {path: paper/drafts/modeling_q1.tex, sha256: <actual SHA-256>}
draft_completed_at: <timezone-aware actual completion time>
quality_review: {path: paper/reviews/modeling_q1.yaml, sha256: <actual SHA-256>}
review_packet: .contest/reviews/modeling_q1.yaml
visual_prompts:
  - revision_id: r1
    task_id: <actual H8_figure_prompt task>
    prompt: {path: paper/prompts/modeling_q1_r1.md, sha256: <actual SHA-256>}
    visual_plan: {path: paper/visuals/modeling_q1_r1.yaml, sha256: <actual SHA-256>}
    prepared_at: <actual output time after chapter approval>
    supersedes: null
```

`quality_review` 内记录 `status: ready`、当前 `draft_sha256` 和上述六项 `checks`。非本章适用内容可用 `{status: not_applicable, reason: <具体原因>}`，模型章的 `model_and_derivation` 不得省略。此报告是作者自查，不等于独立验证或用户批准，也不能证明文风必然优质。最终质量由用户通读当前完整章节裁决。

用户尚未批准章节时，可以按反馈修改该章。每次实际续作保留新任务卡与派发，旧派发以 `superseded_by` 和真实 `superseded_reason` 指向同章、同阶段的后续任务；不删除历史、也不能拿另一章的任务充当返修。章节记录指向最后提交审阅的正文快照。已批准章节保持不变，图件返修始终只改提示词版本。

视觉计划包含 `chapter_id`、`revision_id`、当前获批 `draft` 引用和非空 `slots`。每个槽位具名并声明 figure/table/text；图件给出 ModelViz 或 TikZ 路由。没有图表需求的章节直接设置 `visuals_required: false` 并保留空 `visual_prompts`，无需制造提示词。修订时保留 r1 文件，r2 的 `supersedes` 指向 r1，不能覆盖旧版本。

连续性包应区别“已完成的写作单元”和“正式整合进度”：准备阶段按 `writing_order` 记录已批章节、术语和承接，正式 H8 按最终 `chapter_order` 整合。最终目录的早晚不能反过来阻止先写模型章节。既有 H8 成稿连续性检查仍用于正式整合，不把已存在的正文重新当作待创作全文。

在 `nodes.H7.writer_preparation` 下保存经批准的 `writing_plan`、计划审查包、章节条目、章节审查包和 `visual_prompts`。各实际派发仍进入全局 `dispatch_records`，使用注册的 H8 身份、模型、推理强度、任务卡哈希和真实回执。不得补填回执、用图件状态伪造章节批准，或用待修图件阻塞一个已批准章节之后的写作。
