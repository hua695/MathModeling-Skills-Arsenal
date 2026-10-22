# MathorCup 项目证据契约

项目根目录保存 `competition_profile.yaml`、题面、数据、模型、图表、论文和交付文件；`.contest/` 保存控制记录、任务卡、审查包与批准日志。所有文件引用统一使用项目相对 POSIX 路径和当前文件 SHA-256：

```yaml
path: results/Q1.json
sha256: <64位十六进制摘要>
```

路径不得越出项目根目录。文件内容改变后，更新所有引用、任务卡、审查包和批准摘要；旧批准不继承。`competition_profile.yaml` 至少含 `official_rules_source` 文件引用，并由主 agent 根据本届官方规则登记赛程、提交物、格式、AI 使用和数据使用限制。项目 `.contest/approval_log.yaml`：

```yaml
approvals:
  - gate: M1
    decision: approve
    approved_by: user
    approved_at: 2026-10-16T09:00:00+08:00
    artifact_digests:
      .contest/reviews/M1.yaml: <审查包SHA-256>
      problem_statement.md: <题面映射SHA-256>
```

`artifact_digests` 覆盖审查包的全部 `important_artifacts`。`M1` 至 `M5` 均需独立批准；M4 另需 `M4_VISUAL_PLAN`、`M4_WRITING_PLAN` 与逐章 `M4_CHAPTER:<chapter_id>`。节点批准只允许在本次审查包和证据仍有效时使用。每条真实 agent 调用登记 `task_id`、`node_id`、`owner_role`、`agent_instance_id`、实际 `model`、`reasoning_effort`、带时区 `called_at`、`task_card` 与 `task_card_sha256`。M3 条件辅助调用还须登记 `dispatch_kind: conditional_support` 和 `parent_solver_instance_id`；任务卡同步登记上述字段、允许输出类型以及全部三个禁止权限项。

## M2 与 M3

`literature_request.yaml` 按小问列出方法、数据、参数及验证需求，并附中英文检索提示。`literature_sources.yaml` 由主 agent 读取用户提供的文献 agent 结构化回传后登记：`status: PASS`，非空 `sources`；每条包含唯一 `citation_key`、覆盖小问的 `subproblems`、`user_supplied: true`、可回溯 `locator`、具体 `use` 和 `summary_ref`（项目内回传摘要文件的路径及哈希）。来源用途覆盖全部小问后，方可批准 M2。数量建议不是机器硬门。

`leakage_audit.yaml` 由独立 `verifier` 提交，至少包含 `status: PASS`、`verification_agent_instance_id`、`dataset_sha256`、`feature_pipeline_sha256`、`split_policy`，以及 `checks` 中各自为 `PASS` 的 `split_integrity`、`train_only_preprocessing`、`target_leakage`。每项检查登记 `evidence_ref` 和 `evidence_sha256`，指向可复核的分割、流水线或代码证据。

`run_manifest.yaml` 登记唯一 `solver_instance_id`、整数 `seed`、可执行 `command` 与 `results`。`results` 每个小问一条，含 `subproblem_id`、结果文件路径和 SHA-256。模型/结果解释卡须覆盖每个小问及其 baseline、候选与最终模型、量化指标、来源和适用边界。

`independent_validation.yaml` 登记 `status: PASS`、独立 `verification_agent_instance_id`、`checked_subproblems`，以及 `checks` 中各自为 `PASS` 的 `cross_question_interface`、`data_version`、`units`、`split_integrity`、`numeric_provenance`、`generalization`。每项检查登记 `evidence_ref` 和 `evidence_sha256`。跨问检查逐项核对共享符号、字段、单位、时间尺度、参数与上下游结果；泛化检查核对验证策略与测试集隔离。

## M4 视觉、素材与正文

`visual_argument_plan.yaml` 的 `slots` 逐项登记 `slot_id`、`representation`。`representation: figure` 还需 `generation_route`、`evidence_refs`；路由只取 `modelviz`、`tech-route-maker` 或 `tikz-scientific-figures`。流程/技术路线选择 `tech-route-maker` 的 catalog starter；机理/模型结构/几何选择 TikZ 的 catalog starter。计划需解释读者问题、证据和落位；正式图与图槽位一一对应。`figure_registry.yaml` 的每个 `figures` 项登记 `visual_slot_ids`、`generator`、`generation_route`、`formats: [svg, png]`、`insertion_format: svg`、`visual_qa: passed`、`qa_status: reviewed`、图注、来源文件及 SVG/PNG 路径和哈希。ModelViz 图还需 SciPilot 的 `decision_card`、`decision_card_sha256`、`decision_author`、`semantic_qa`；`tech-route-maker` 与 TikZ 图需已批准的 `template_id`、与 catalog 一致的 `template_sha256`、`starter_source`、`starter_sha256`、`script`、`script_sha256`。正式生成任务卡使用 `scope.phase: generate`，必须在 `M4_VISUAL_PLAN` 批准后派发，并把批准的计划作为输入。

`paper_material_readiness.yaml` 由 `verifier` 签署 `status: PASS`，`evidence_matrix` 对全部小问分别登记以下字段，每格使用 `status: ready`、文件路径和当前哈希：

```text
problem_mapping, assumptions, symbols, data_processing, model_choice,
method_and_parameters, quantitative_results, validation, figures_or_tables,
literature_use, conclusion_and_boundary
```

`chapters` 为每章登记 `chapter_id`、`capacity` 和 `material_refs`。`paper_claim_coverage.yaml` 登记 `status: PASS`、`readiness_sha256` 和 `claims`；每项主张有唯一 `id`、`paper_anchor` 与非空 `evidence_refs`。正文结论、数字、图表解释和引用用途都纳入主张覆盖。`paper_argument_blueprint.yaml` 明确全文主线、章节职责、篇幅容量与证据落位；正式写作任务卡使用 `scope.phase: write`、当前 `chapter_id`，并输入蓝图、素材准入和主张覆盖。每章只有一个写作派发；后一章派发必须晚于前一章用户批准，章节批准必须晚于本章派发。

## M5 复现与交付

`reproducibility_report.yaml` 至少包含 `status: PASS`、`exit_code: 0`、可执行 `command` 和非空 `result_refs`。记录隔离复跑环境、依赖、随机种子、输出哈希及数值容差。`delivery_report.yaml` 使用 `status: PASS`，并在 `checks` 中逐项登记 `status: PASS`、`evidence_ref`、`evidence_sha256`：

```text
official_rules, paper_format, code_reproduction, numeric_sources,
figures_and_citations, anonymity, ai_disclosure, final_text
```

`final_text` 覆盖符号首次定义、学术语体、元话语及内部过程痕迹；`paper_format` 与 `official_rules` 依本届官方文件核验。PDF 和提交包均需登记当前路径与哈希。任何字段只能凭实际执行与核验结果填写。
