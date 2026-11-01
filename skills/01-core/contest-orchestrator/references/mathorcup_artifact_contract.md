# MathorCup 项目证据契约

项目根目录保存 `competition_profile.yaml`、题面、数据、模型、图表、论文和交付文件；`.contest/` 保存控制记录、任务卡、审查包与批准日志。所有文件引用统一使用项目相对 POSIX 路径和当前文件 SHA-256：

```yaml
path: results/Q1.json
sha256: <64位十六进制摘要>
```

路径不得越出项目根目录。文件内容改变后，按 `incremental_validation_policy.md` 只更新受影响的引用、任务卡和审查包；受影响的旧批准不继承，未变的哈希绑定批准继续有效。`competition_profile.yaml` 至少含 `official_rules_source` 文件引用，并由主 agent 根据本届官方规则登记赛程、提交物、格式、AI 使用和数据使用限制。项目 `.contest/approval_log.yaml`：

新运行同时遵循 [execution protocol 2.0](mathorcup_execution_protocol.md)。该协议扩展现有 KPI、模型卡、run manifest、agent registry 和 figure registry；原 schema 与历史记录不追溯迁移。

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

artifact_digests 覆盖审查包的全部 important_artifacts。M1 至 M5 均需独立批准；`chapter_parallel` 的 M4 另需 M4_WRITING_PLAN、每章的 M4_CHAPTER:<chapter_id>、摘要框架 M4_ABSTRACT_FRAMEWORK、最新提示词版本对应的 M4_FIGURE_SELECTION:<chapter_id>:<revision_id> 和 M4_FINAL_PAPER。旧 `writer_first_batches` 记录保留其既有批次门。写作计划批准同时冻结 paper_argument_blueprint.yaml 与 paper_language_profile.yaml。节点批准只允许在本次审查包和证据仍有效时使用。每条真实 agent 调用登记 task_id、node_id、owner_role、agent_instance_id、实际 model、reasoning_effort、带时区 called_at、task_card 与 task_card_sha256。M3 条件辅助调用还须登记 dispatch_kind: conditional_support 和 parent_solver_instance_id；任务卡同步登记上述字段、允许输出类型以及全部三个禁止权限项。

## 授权恢复与批准前预检

`agent_instances` 保留基础身份；节点边界后的替代实例由批准日志的 `instance_recoveries` 追加登记，不重写旧派发。每项必须包含唯一 `id`、`decision: approve`、`approved_by: user`、带时区的真实 `approved_at`、`effective_from_node`（M2–M5）以及 `source_ref`、`context_ref`、`recovery_record_ref` 三个文件引用。授权可按原始证据补录，补录时间不能冒充授权时间。`context_ref` 必须等于前一节点当前审查包引用，不能随意选择一份同哈希格式的文件。

`replacements` 的每项登记 `role`、`previous_agent_instance_id`、`new_agent_instance_id`、`model`、`reasoning_effort`。绑定的恢复记录须有 `authorized_by: user` 和相符的 `replacements`，其中 `previous_instance.agent_instance_id` 与旧身份一致。当前节点的 `runtime_instances_by_node.<node>.<role>` 登记新 ID、固定模型路线和非空 `preloaded` 文件引用；非 data 角色必须预载 `problem_statement.md`。单独写 runtime override 不产生恢复授权。

检查器按生效节点接续身份链，新身份不能复用任何已登记身份，固定模型路线不变，恢复授权须早于实际派发。同一角色每个节点边界最多恢复一次；本契约不支持在同一节点中途切换实例。新身份向后续节点延续，旧节点继续使用旧身份。泄漏或结果审核签署人必须等于对应节点的有效 verifier，不能与 solver 共用实例。不同边界多次恢复须按身份链顺序登记。

对尚未批准但已提交审查包的节点运行：

```text
python scripts/check_mathorcup_control.py <project-root> --preflight-node M2
```

该命令复用产物、哈希、审查包、专业调用、身份与独立性校验，只读检查目标节点及其前序批准。证据有效但缺少节点批准时，整体仍为 `PAUSE`，可单列 `evidence_status: PASS`；任一校验失败为 `BLOCK`。它不改 `review_pending`、不补造批准，也不允许进入下一节点。`--through`、`--preflight-node`、`--preflight-writing` 互斥；原有正式推进与批准要求保持不变。

已被合法后续重试取代的派发保留原任务卡及哈希、原身份和未被采用的错误路线，不能把后续实例或模型倒填到旧记录。后续被采用的派发仍须通过固定路线、身份与批准时序检查。

## M2 与 M3

`literature_request.yaml` 按小问列出方法、数据、参数及验证需求，并附中英文检索提示。`literature_sources.yaml` 由主 agent 读取用户提供的文献 agent 结构化回传后登记：`status: PASS`，非空 `sources`；每条包含唯一 `citation_key`、覆盖小问的 `subproblems`、`user_supplied: true`、可回溯 `locator`、具体 `use` 和 `summary_ref`（项目内回传摘要文件的路径及哈希）。来源用途覆盖全部小问后，方可批准 M2。数量建议不是机器硬门。

`leakage_audit.yaml` 由独立 `verifier` 提交，至少包含 `status: PASS`、`verification_agent_instance_id`、`dataset_sha256`、`feature_pipeline_sha256`、`split_policy`，以及 `checks` 中各自为 `PASS` 的 `split_integrity`、`train_only_preprocessing`、`target_leakage`。每项检查登记 `evidence_ref` 和 `evidence_sha256`，指向可复核的分割、流水线或代码证据。

`run_manifest.yaml` 登记唯一 `solver_instance_id`、整数 `seed`、可执行 `command` 与 `results`。`results` 每个小问一条，含 `subproblem_id`、结果文件路径和 SHA-256。模型/结果解释卡须覆盖每个小问及其 baseline、候选与最终模型、量化指标、来源和适用边界。

`independent_validation.yaml` 登记 `status: PASS`、独立 `verification_agent_instance_id`、`checked_subproblems`，以及 `checks` 中各自为 `PASS` 的 `cross_question_interface`、`data_version`、`units`、`split_integrity`、`numeric_provenance`、`generalization`。每项检查登记 `evidence_ref` 和 `evidence_sha256`。跨问检查逐项核对共享符号、字段、单位、时间尺度、参数与上下游结果；泛化检查核对验证策略与测试集隔离。

## M4 视觉、素材与正文

新建运行启用 `nodes.M4.visual_workflow: chapter_parallel`，其顺序、章节记录和提示词版本以 `mathorcup_chapter_parallel.md` 为准：先批准写作蓝图和科学素材，按依赖完成一章正文并经用户批准；随后 writer 生成提示词，用户转交 figure，图件与下一章并行。下述全局 `M4_VISUAL_PLAN` 前置门只用于未启用此字段的历史运行；新流程不要求初稿前已有正式图，也不以图件返修撤销未改变正文的批准。

`chapter_parallel` 的每章提示词 visual plan 记录 chapter_id、revision_id、精确已批准正文、owner_role: writer 和 slots。slots 逐项登记 slot_id、representation。representation: figure 还需 generation_route、evidence_refs；路由只取 modelviz 或 tikz-scientific-figures。所有非数据图使用 TikZ catalog starter，数据结果图使用 ModelViz 并绑定 SciPilot 决策卡。计划需解释读者问题、证据和落位；正式图与图槽位一一对应。figure_registry.yaml 的每个 figures 项登记 visual_slot_ids、generator、generation_route、formats: [svg, png]、insertion_format: svg、visual_qa: passed、qa_status: reviewed、图注、来源文件及 SVG/PNG 路径和哈希。ModelViz 图还需 SciPilot 的 decision_card、decision_card_sha256、decision_author、semantic_qa；TikZ 图需已批准的 template_id、与 catalog 一致的 template_sha256、starter_source、starter_sha256、script、script_sha256。正式生成任务卡使用 scope.phase: generate，绑定 chapter_id 与 revision_id，在相应 M4_CHAPTER 批准和 writer 提示词任务之后派发，并把精确正文和计划作为输入。

`paper_material_readiness.yaml` 由 `verifier` 签署 `status: PASS`，`evidence_matrix` 对全部小问分别登记以下字段，每格使用 `status: ready`、文件路径和当前哈希：

```text
problem_mapping, assumptions, symbols, data_processing, model_choice,
method_and_parameters, quantitative_results, validation, figures_or_tables,
literature_use, conclusion_and_boundary
```

paper_material_readiness.yaml 的 chapters 为每章登记 chapter_id、capacity 和 material_refs。`chapter_parallel` 的 paper_argument_blueprint.yaml 明确全文主线、官方规则依据的总篇幅区间、章节职责和页数容量、图表/表格落位、主张与证据映射，并分别列出目录 chapter_order 与创建 writing_order。每章写作任务使用 scope.phase: draft 和 chapter_id，输入蓝图、项目术语配置、素材准入、主张覆盖及该章冻结证据。每章均提交用户审查，M4_CHAPTER 仅绑定 immutable draft 与 quality review；图件不是该门的工件。每次局部 论文辅助 审查覆盖术语口径、符号首用定义、主张证据、元话语和负向回响，且模型章还必须审查模型与推导。全体非摘要章批准后，作者单独提交摘要框架并取得 M4_ABSTRACT_FRAMEWORK 批准；摘要章最后完成并走同一审查。最终整合后，全文只读审查还须通过严格摘要检查和全文终检。

## M5 复现与交付

`reproducibility_report.yaml` 至少包含 `status: PASS`、`exit_code: 0`、可执行 `command` 和非空 `result_refs`。记录隔离复跑环境、依赖、随机种子、输出哈希及数值容差。`delivery_report.yaml` 使用 `status: PASS`，并在 `checks` 中逐项登记 `status: PASS`、`evidence_ref`、`evidence_sha256`：

```text
official_rules, paper_format, code_reproduction, numeric_sources,
figures_and_citations, anonymity, ai_disclosure, final_text
```

`final_text` 覆盖符号首次定义、学术语体、元话语及内部过程痕迹；`paper_format` 与 `official_rules` 依本届官方文件核验。PDF 和提交包均需登记当前路径与哈希。任何字段只能凭实际执行与核验结果填写。
