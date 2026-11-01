# 全流程竞赛模式：Harness

`full-contest-harness` 是带人工节点确认的多 agent 全流程。一次运行只能有一个 `active_mode`，并在项目根创建 `.contest/harness_control.yaml`、`.contest/task_cards/`、`.contest/reviews/` 和 `.contest/approval_log.yaml`。使用 `templates/harness_control.yaml`、`templates/harness_task_card.yaml`、`templates/harness_review_packet.yaml` 初始化这些记录。

新运行启用 `visual_workflow: chapter_parallel`，先读取 [逐章批准写作与并行图表](../harness_chapter_parallel.md)：H6 获批后，固定 H8 论文角色先提交全篇计划，再按实际写作顺序完成一章、接受用户批准、为该章准备可转交的图表提示词；用户亲自转交后，H7 的制图可与下一章写作并行。正式 H8 只整合选定图件、完成必要编辑并最后写摘要，H9 保留完整验收。`writer_first_draft` 和未启用该字段的历史记录继续按 [论文主导的图表准备](../harness_writer_preparation.md) 的原顺序解释。

## H0 激活门禁

主 agent 在 H0 必须实际调用 `superpowers:using-superpowers`，将调用的 task ID 和完成状态登记到 `harness_control.yaml.bootstrap.invocations`。仅写出技能名称不构成调用记录。该技能不可用、调用未完成或调用记录缺失时，状态为 `BLOCKED_INPUT` 或 `PAUSE`，不得进入 H1–H9、生成正式论文或交付物。

该调用只负责建立多 agent 编排能力；不要求每个节点机械地产生子 agent。每次实际调度都必须建立一张新的任务卡，并写入唯一 `task_id`、节点、固定角色、输入哈希、范围、输出、验证、禁止动作和回流证据。没有任务卡和 `agent_instance_id` 的节点不得通过。`controller_only` 表示仅由主 agent 执行；`conditional` 仅用于经主 agent 明确判断后才需要的辅助支持，不得替代固定角色的职责。

## 固定角色与职责边界

| 角色 | 唯一职责 | 不得承担 |
|---|---|---|
| 主 agent | 模式选择、范围、输入门、任务卡、文献结构化文件读取、模型路线决策、冲突裁决、冻结、人工批准和最终交付 | 题意解析成品、局部求解、独立验证、制图或论文正文代写 |
| 题意理解 agent | 读取题面和附件，输出统一题意、数据字典、约束、来源索引和不确定项 | 文献检索、模型路线决策、求解 |
| 解题 agent | 指定小问的建模、推导、算法、实现、局部实验和结果 | 改写冻结路线、验证自身结果、图表论点决策 |
| 验证 agent | 在独立上下文复核公式、符号、单位、代码、结果、边界与文献实际使用 | 复用同一实例验证自身解题产物、修改模型路线 |
| 图表 agent | 按冻结数据和 SciPilot 图表决策卡生成 SVG/PNG、源文件、图表登记与图表质量记录 | 产生新数据、新结论或改动模型 |
| 论文 agent | 依据完整冻结素材包组织论文、附录映射和正文质量检查 | 改动冻结的公式、数字、引用键、图表编号或模型逻辑 |

用户之外的文献全文处理由用户指定的外部文献 agent 完成；它不替代上述固定角色。主 agent 和内部子 agent 只读取 `literature_sources.yaml` 中的题名、元数据、摘要、结构化全文总结、可定位证据和适用边界，不读取文献全文。

调度任何外部 skill（academic-writing、SciPilot、ModelViz、tikz-scientific-figures、humanizer-zh 等）前，主 agent 必须读取 `references/external_skill_adapters.md`，按适配器契约执行；外部 skill 只能执行当前任务卡中的专业子任务，不得切换模式、扩大范围或替代主会话决策。

## 子 agent 模型路由

`default_subagent_model` 只作为运行时兜底。每张实际调度的 H1/H5/H6/H7/H8 任务卡必须显式填写 `model` 和 `reasoning_effort`，并与 `harness_control.yaml.agent_runtime_routes` 一致。主 agent 使用原生 `spawn_agent` 时按任务卡传入这两个字段；未按节点路由创建的子 agent 不得通过节点检查。

| 节点 | 模型 | 推理强度 | 适用职责 |
|---|---|---|---|
| H1 | `gpt-5.6-terra` | `medium` | 题意、附件和约束的结构化提取 |
| H5 | `gpt-5.6-sol` | `high` | 模型推导、算法、代码与实验 |
| H6 | `gpt-5.6-sol` | `high` | 独立验证与证据复核 |
| H7 | `gpt-5.6-terra` | `medium` | 图表执行、格式导出与质量检查 |
| H8 | `gpt-5.6-sol` | `high` | 冻结素材组织、论文论证和证据缺口审查 |

`luna` 只允许用于不改变模型、结果、验证结论或论文论证的低风险辅助工作；它不能替代 H5、H6 或 H8。H2、H3、H9 为 `controller_only`，不调度固定子 agent。（H4 节点已取消，其蓝图设计职责并入 H5）

## 统一解题主线与调度留痕

每次 Harness 运行在 `harness_control.yaml.problem_scope.subproblems` 登记完整且不重复的小问清单，并在 `solver_instance_id` 登记唯一 H5 主解题实例。主任务卡的 `covered_subproblems` 必须与该清单完全一致，且 `cross_question_interface: true`；该实例负责全部小问、跨问变量、参数传递、接口和整体结论。H5 节点、主任务卡和对应 `dispatch_record` 的 `solver_instance_id` 必须一致。H6 的 `agent_instance_id` 必须不同于 H5。

`dispatch_records` 记录每次实际 `spawn_agent` 调度，且每条都包含 `task_id`、`node_id`、`owner_role`、`agent_instance_id`、实际 `model`、`reasoning_effort`、调用时间、任务卡相对路径和当前 SHA-256。检查器将记录与任务卡、节点模型路由和节点实例逐项核验。

H5 条件辅助任务使用 `dispatch_kind: conditional_support`，绑定 `parent_solver_instance_id`，输出类型仅限 `local_computation_evidence`、`data_processing_evidence` 或 `code_experiment_evidence`。其权限字段必须禁止改动模型路线、写入最终结果和汇总结论。`primary_solver` 只能有一个，且只能由解题 agent 担任。

H5 结果冻结后必须登记 `run_manifest`，并运行 `scripts/check_h5_result_traceability.py <项目根> --strict`。运行清单登记显式 seed、可执行命令、主结果路径与 SHA-256、正式记录字段及结果文件哈希、正式解释边界和 `model_contract_sha256`；同时登记已核验的 `sensitivity_report.yaml` 或 `robustness_report.yaml`，包含 `canonical_report` 的路径与 SHA-256、方法、同一模型契约哈希和非空扰动结果。缺少证据保持 `PAUSE`，路径、格式或哈希不一致为 `BLOCK`。

H6 的 `global_interface_check.yaml` 对每个结构化接口字段强制登记 `comparison_status`、项目相对 `source_path` 和当前文件的 `source_sha256`。H6 将共享变量、符号、单位、数据版本、上下游字段、时间尺度、参数、跨问约束、结论和来源逐项写入接口矩阵；来源路径或哈希缺失时不签名放行。

H7 生成任务卡必须将 `scope.phase` 设为 `H7_generate` 并登记 `scope.approved_visual_plan_sha256`。检查器只接受与当前 `visual_argument_plan.yaml` 相同且被 `H7_VISUAL_PLAN` 用户批准记录覆盖的哈希，并要求生成任务派发时间晚于该批准时间；计划批准不凭计划自身的状态字段推定。

### 分配即休眠

主 agent 向 H1/H5/H6/H7/H8 分配任务卡后，立即暂停当前轮次，不轮询、不等待、不检查子 agent 进度。子 agent 完成后通过回传消息唤醒主 agent；主 agent 被唤醒后只处理回传内容，不回溯执行期间的中间状态。子 agent 执行期间主 agent 不消耗 token。

## 审查包与批准记录

H2–H9 每个节点完成后都必须：

1. 生成 `review_packet`，包含 `node_id`、摘要、重要产物及 SHA-256、检查结果、待批准决定和下一节点；
2. 向用户提供审查包中的重要文件；
3. 在 `.contest/approval_log.yaml` 写入对应 `user_approval`，并覆盖审查包及其重要产物的当前哈希；
4. 仅在哈希仍一致且用户明确批准时进入下一节点。

用户没有批准、审查包缺失或任一哈希变化时保持 `PAUSE`。节点顺序、角色归属、任务卡、审查包和批准记录用以下命令核验：

```text
python scripts/check_harness_control.py <project-root> --through H<n>
```

### 增量裁决

主 agent 裁决时只读取当前节点的 `review_packet`、子 agent 回传的变更摘要和检查器输出。不重读上游已冻结产物；只有当 `review_packet` 标记 `upstream_changed=true` 时，才重读受影响的特定文件。

### 子 agent 回传格式

子 agent 完成后回传必须包含固定四段：

1. **完成项**：本节点做了什么。
2. **变更摘要**：相对上游冻结状态改了哪些文件、数字或结论。
3. **自检结果**：跑了哪些检查，PASS 或 FAIL。
4. **待裁决项**：需要主 agent 或用户决定的具体问题。

主 agent 基于这四段直接裁决，不自行翻文件对比。

## H0–H9 节点

| 节点 | owner_role / 调度 | 产物与人工审查 | 通过条件 |
|---|---|---|---|
| `H0` | 主 agent / `controller_only` | 运行范围、`harness_control.yaml`、`superpowers:using-superpowers` 调用记录 | Harness 门禁通过 |
| `H1` | 题意理解 agent / `required` | `problem_statement.md`（完整题面翻译 + 题目解读，按 `templates/problem_statement.md` 双结构模板）、`unified_problem_package.yaml`、数据字典、约束、歧义清单和各小问读者问题线索 | 结构化题意可由 H2 冻结 |
| `H2` | 主 agent / `controller_only` | 规格冻结包：题目—数据—接口映射、问题范围和未决项 | 用户批准后进入 H3 |
| `H3` | 主 agent / `controller_only` | 文献需求清单和给外部文献 agent 的提示词：总数硬范围 6–11、推荐 8–10、中文逐小问覆盖、英文不设硬性最低数量但建议覆盖全部小问、方法/数据/参数/基准证据需求、检索词、回传字段及”支持哪个小问和论点”；登记 `literature_request`、`literature_agent_prompt` 和用户回传 `literature_sources` 文件路径；不得在本节点确定模型路线、模型蓝图、baseline 或图表需求清单 | 立即 `PAUSE`；用户检索下载全文并提交 `literature_sources.yaml`。数量、语言与小问覆盖校验通过后，经用户批准进入 H5；每篇须有原文定位与具体用途。英文未覆盖全部小问只记录建议，不阻断 |
| `H5` | 解题 agent / `required` | **（已合并原 H4 蓝图设计职责，内部四阶段：①蓝图设计→②快速验证→③优化迭代→④完善冻结）** 阶段一产出：`method_transfer_map.json`、文献使用登记、模型路线、`model_blueprint.yaml`、baseline、图表需求清单（`chart_requirements.yaml`，只定义正文主张、图号占位、目标小问、所需结果字段和 argument_goal，不定义数据图图型、视觉编码或版式）和 `paper_narrative.yaml`（叙事蓝图）；阶段二-四产出：全题模型契约、统一符号表、完整推导、代码、运行清单、跨问接口、结果与局部实验、`validation_contract.yaml`、`model_summary_cards.yaml`、回填 `paper_narrative.yaml` 的 key_result、`result_interpretation_cards.yaml`、**优化决策类题目必须产出 `sensitivity_report.yaml` 或 `robustness_report.yaml`** | 阶段一（蓝图设计）：必调 `math-model-selector`；每个小问都有 `adopt` 或 `adapt` 方法以及一条数据、参数、测量先例或基准证据，均含 `citation_key`、定位、模型组件/数据字段和实际使用方式；阶段一结束可做轻量方向确认（非硬批准门）。阶段二-四（求解）：唯一 `solver_instance_id` 覆盖全部小问；每问都有假设、原始关系、全链路推导（从问题到最终模型每步有话语解释，禁止跳步黑箱，禁止"易知/显然/经过复杂推导"）、目标/约束、算法、参数、结果和验证；每张模型总结卡都绑定最终可计算表达式、求解接口、来源公式和符号单位；每张结果解释卡不得超出冻结证据；推导链落盘供 H8 取用；`paper_narrative.yaml` 的 key_result 已回填；**优化决策类题目必须生成灵敏度/鲁棒性报告，报告 schema_version=1.0、含 status 和 results 列表**；用户批准后进入 H6 |
| `H6` | 验证 agent / `required` | 独立验证报告、`h6_verification_scope.yaml`、`validation_contract.yaml` 契约核对（关键核对必查 + 深度抽查锚点，不重读 H5 全部推导/代码）、`global_interface_check.yaml`、`model_summary_cards.yaml` 模型总结卡核验、叙事蓝图和结果解释卡核验、冻结清单 | H6 与 H5 实例不同；首次仅由 H5 结果冻结触发，后续仅由模型、数据、关键结果或结果解释卡变化触发定向复核；普通正文、排版、图表美化和附录格式变化不派发 H6。共享变量、单位、数据版本、字段、时间尺度、参数、跨问约束、结论和来源均一致，`paper_narrative.yaml` 的 key_result 与冻结结果一致；每张模型总结卡均核对符号、单位、公式、边界、代码接口和适用范围，并写入 H6 当前实例签名；每张结果解释卡均有真实证据、限定适用范围且解释不越界；契约核对通过；用户批准后进入 H7 |
| `H7` | 图表 agent / `required` | `visual_argument_plan.yaml`、`.contest/reviews/H7_visual_plan_review_packet.yaml`、冻结数据对应的 SciPilot 图表决策卡、SVG、PNG、可编辑源、图表登记、图注、读者应读出的结论和质量记录 | 图表执行前必须读取 `references/modes/figures.md`，按“读者问题→视觉义务→图型/路由→生成→检查”执行。阶段一：H7 图表 agent 只基于冻结模型、结果和 H5 主张清单生成 `visual_argument_plan.yaml`，每个图槽位必须登记 `figure_intent`，逐小问完成 `orientation`、`mechanism`、`model_structure`、`algorithm_process`、`result_evidence`、`validation_robustness` 六类审计；结构化模型、迭代/启发式算法、机理/空间关系和主要结果由检查器从 H5 模型事实推断硬性视觉义务，不能用自由理由降级。多小问或跨问接口还必须登记 `global_story`。阶段一提交 `.contest/reviews/H7_visual_plan_review_packet.yaml`，在 `.contest/approval_log.yaml` 登记 `H7_VISUAL_PLAN` 的当前计划哈希并暂停等用户确认；阶段二才为已批准槽位选择图型和路由：数据结果图运行 SciPilot 决策卡→ModelViz→SciPilot QA，流程图、技术路线图、机制/几何/公式示意图统一运行 `tikz-scientific-figures`；图表确认前不得冻结论文素材，用户肉眼批准后进入 H8。**图表路由是检查器硬约束**：登记中每张图必须含 `kind`（data/flowchart/roadmap/schematic/drawio）且 `generator` 匹配路由（data→modelviz+semantic_qa=scipilot、flowchart/roadmap/schematic→tikz-scientific-figures、drawio→drawio-diagram 且 `user_requested=true`），`formats` 必须精确为 svg+png、`insertion_format=svg`、合法 `layout_mode`、`visual_qa=passed/reviewed`，并通过 `visual_slot_ids` 绑定已批准的视觉槽位；缺计划、缺独立批准、缺硬性槽位、存在计划外图表或未闭合登记即 BLOCK。页面布局由 `mathmodel-latex-skill` 执行，不由 SciPilot 或 ModelViz 改变图表语义。 |
| `H8` | 论文 agent / `required` | `paper_material_readiness.yaml`、`paper_narrative.yaml`、`result_interpretation_cards.yaml`、经 H6 核验的 `model_summary_cards.yaml`、经用户批准的 `visual_argument_plan.yaml`、`paper_argument_blueprint.yaml`、`paper_author_brief.yaml`、`abstract_argument_card.yaml`、`chapter_writing_card.yaml`、`paper_continuity_context.yaml`、`paper_claim_coverage.yaml`、论文草稿和编辑报告 | 素材准入和主张覆盖均为 `PASS` 后进入 H8A：`academic-writing` 先生成论证蓝图、作者简报和摘要论证卡，主 agent 生成写作计划；摘要论证卡固定摘要的读者契约、统一建模主线、逐问方法—结果—意义、验证结论、总评和关键词，逐问绑定冻结证据。简报、摘要论证卡、视觉论证计划和写作计划一并提交用户审查。`paper_narrative.global.paper_spine` 规定唯一章节顺序，`core` 章节承载建模与求解，`support` 章节服务于核心论证；每章登记 `chapter_role`、`reads_from`、`feeds_to`、`new_claims_allowed` 和 `handoff_question`。H8B 由同一论文 agent 按章节写作卡、连续性包、摘要论证卡、视觉论证计划和模型总结卡逐章写作；每张章节卡必须填写 `abstract_contribution`，供 H8C 汇总摘要。建模问题章节先写不编号的问题引入与建模思路，再设“模型建立”和“模型求解与结果分析”两个编号小节，并在模型建立小节末尾呈现最终求解模型框；一级标题采用中文序号，“模型假设”和“符号说明”分设为两个全局一级章节。H8B 只能使用已批准计划中登记的图表，不得新增计划外图表或以图表填充篇幅；H8B 不写最终摘要。H8C 由 `academic-writing` 先通读完整论文、检查读者路径、章节递进和主线承接，再依据摘要论证卡和各章摘要贡献最后写摘要，并运行 `scripts/check_abstract_contract.py --strict` 登记 `abstract_contract_report`；报告未通过不得完成 H8。材料不足回到对应节点补证据，表达问题才形成局部正文补丁。H8 的 `skill_invocations` 还必须实际登记 `academic-writing` 与 `mathmodel-latex-skill`，每项带存在性可校验的 `evidence_ref`；用户批准后进入 H9 |
| `H9` | 主 agent / `controller_only` | 最终交付审计包、门禁报告、交付清单 | 交付前必须运行 `python scripts/delivery_all.py <项目根> --strict`，全部 PASS 后才交付；H9 的 `skill_invocations` 必须实际登记 `bzd-review-paper` 与 `mathmodel-latex-skill`，每项带存在性可校验的 `evidence_ref`；用户最终批准后交付 |

### `chapter_parallel` 的 H7/H8 覆盖时序

当 `visual_workflow: chapter_parallel` 时，上表 H7/H8 的正式图件输入改按以下时序解释，其他科学、路由、QA、H8 整合和 H9 要求不变：

1. H6 获用户批准后，H8 先提交含 `central_thesis`、`reader_journey`、`chapter_order`、`writing_order` 与依赖的全篇计划；用户以 `H7_WRITING_PLAN` 批准。
2. H8 依 `writing_order` 逐章写完整正文并提交绑定草稿哈希的质量审查。用户以 `H7_CHAPTER:<chapter_id>` 批准当前章后，才能派发下一章。
3. 只有当前章获批，H8 才可生成该章图表提示词和视觉计划；用户亲自转交 H7。`visuals_required: false` 表示无图的明确决定。提示词版本可返修，但不会撤销当前章节批准或阻塞下一章。
4. H7 的每一张图必须绑定最新提示词、其视觉计划槽位、`chapter_id`、`prompt_revision_id` 和真实 `H7_generate` 派发。最终汇总计划等于所有最新章节计划的槽位集合，包含 `slots`、`global_visual_slots` 和各小问 `visual_audit`，不得加入未被论文需求覆盖的图件。
5. 所有非摘要章节批准后，未完成的图件或返修只阻塞最终 H7 图件闭合。正式 H8 按 `chapter_order` 接入选定图件、局部编辑与排版，并最后写摘要；不得从头重写已批准正文。

🔴 **CHECKPOINT · H2–H9 人工批准门**：`review_packet` 和 `user_approval` 是逐节点硬门；H1 的题意产物由 H2 的审查包统一提交用户审查。任一硬门未经用户批准不得推进下一节点。

🛑 **STOP 条件**：任一节点 `failures` 非空（如伪造 skill 名、哈希不匹配、越权登记）立即 `BLOCK` 停止，修复前不得继续；`missing` 非空（缺产物、缺批准、缺绑定调用）保持 `PAUSE` 等补齐。

## 节点-子 skill 绑定契约

领域能力已下沉到子 skill，主 skill 不再持有这些知识。每个节点在 `harness_control.yaml` 的节点记录里登记 `skill_invocations`，检查器 `_validate_skill_invocations` 强制校验：

| 节点 | 绑定契约 | 说明 |
|---|---|---|
| `H5` | 阶段一必调 `math-model-selector`；阶段二-四至少调一：`heuristic-algorithms` / `data-science-stack` / `pyomo` | 阶段一（蓝图设计）：模型选择与实现路由由 selector 承接；阶段二-四（求解执行）：纯机理题可加载 `knowledge/cookbooks` 并显式登记 not_applicable+reason；**优化决策类题目（B 题）必须额外调用 `pyomo/scripts/sensitivity_analysis.py`（精确优化模型参数扰动）或 `heuristic-algorithms/scripts/robustness_check.py`（启发式算法随机种子敏感性），产出 `sensitivity_report.yaml` 或 `robustness_report.yaml`** |
| `H6` | 必调 `data-science-stack` | 模型检验方法已迁入其 references |
| `H7` | 至少调一：`scipilot-figure-skill` / `tikz-scientific-figures` | 图表生成；Draw.io 仅显式请求 |
| `H8` | 必调 `academic-writing` + `mathmodel-latex-skill` | `academic-writing` 承接正文/摘要/去 AI 味/自审；`mathmodel-latex-skill` 承接论文源、编译预检和排版约束 |
| `H9` | 必调 `bzd-review-paper` + `mathmodel-latex-skill` | `bzd-review-paper` 承接论文评审；`mathmodel-latex-skill` 承接最终源文件、编译、版式和交付前排版检查 |

登记要求：

- 节点 status 推进后 `skill_invocations` 必须为非空列表，否则 `PAUSE`。
- 必调项缺失 → `PAUSE`；`must_call` 项不得用 `not_applicable` 解除绑定；`at_least_one` 可显式登记 `not_applicable: true` + `reason`（如纯机理题不调 data-science）。
- 每个条目必须含合法 `skill` 名（在 `external_skill_adapters.md` 8 类清单内），带 `evidence_ref`（产物项目相对路径，检查器校验存在性）。伪造 skill 名或路径 → `BLOCK`。
- H0 启动时检查器对登记 skill 名做合法性校验；子 skill 是否安装由 `scripts/skill_health_check.py` 的环境检查覆盖。

### 绑定失败分支（if 失败 → 一线修复 → 仍失败兜底）

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 必调子 skill 未调用（PAUSE） | 节点补登记实际调用 + evidence_ref | 回流主 agent 补齐输入、实际调用和证据；不得用 `not_applicable`、手工豁免或替代记录绕过 `must_call` |
| 子 skill 返回 `BLOCKED_INPUT` | 检查输入契约（task_card/ledger/蓝图）是否齐全 | 回流主 agent 补齐输入或换等价子 skill |
| 子 skill 返回 `FAIL` | 按子 skill 节点包 blockers 定向修复 | 记录失败库，回流主 agent 人工裁决，不静默换路由 |
| 子 skill 未安装（health_check FAIL） | 按环境同步补齐（.agents → workbuddy） | 该节点暂停，先修环境再推进 |
| 检查器 `BLOCK`（伪造/哈希不匹配） | 读 failures 逐条修正登记 | 无法修复则回流主 agent，禁止绕过检查器继续 |

## H8 证据充分性门

H8 素材准入文件（`paper_material_readiness.yaml`、`evidence_gap_matrix.yaml`）由主 agent 生成，`check_harness_control.py --through H8` 负责校验（不生成文件）；主 agent 只读取检查器输出的 PASS/FAIL 和缺口清单，不手工汇总。`paper_material_readiness.yaml` 使用 `schema_version: "2.0"` 时，必须提供 `evidence_matrix`，逐小问登记问题映射、假设、符号、推导、算法与参数、量化结果、验证、图表或表格、文献使用、结论与边界、敏感性或稳健性，并登记 `global.target_length`；`PASS` 时每格必须为 `ready` 或合法的 `not_applicable`。每个小问必须登记问题映射与假设、符号定义、可审计推导、算法与参数依据、量化结果及来源、验证/敏感性/稳健性、冻结图表或表格、文献方法/数据/参数的实际用途、结论与适用边界；同时登记正文目标篇幅各章节的容量与素材覆盖，以及双口径容量预算：正文（正文主体、AI 工具使用声明和参考文献，摘要不计）硬上限 30 页、个人 profile 规划目标 25–30 页；提交论文文件总页数（含摘要、正文、参考文献和附录）硬上限 51 页、推荐区间 35–51 页（优秀论文普遍落在该区间，附录按需扩展但不挤占正文论证容量）。口径与 `references/content_budget_policy.md`、`core/competition_gates.yaml` 一致。每个引用文件均使用项目相对路径和 SHA-256 绑定。

首次准入未通过时，H8 只能输出一份 `evidence_gap_matrix.yaml`。该矩阵必须完整覆盖检查器已检测的缺口，并逐项给出小问、缺口、责任节点、所需产物、验收条件和回流目标。主 agent 一次性协调 H5/H6/H7 补齐矩阵内全部缺口；重新执行准入并通过后再进入写作。写作期间，只有模型、数字、引用或图表来源发生变化时素材包失效并重新准入。

`paper_claim_coverage.yaml` 将每个正文结论、量化数字、图表主张和引用用途绑定到已冻结的结果、验证、图表或文献证据。未登记主张不得进入论文；H8 只组织已冻结证据，不新增模型结论、数字、引用用途或图表解释。论文 agent 不得以重复表述、泛泛背景、空洞评价或文献堆砌补足篇幅。

## 论证中心编辑与红线回流

H8 论文草稿完成后，主 agent 调度 `academic-writing` 执行论证中心编辑，任务卡 `objective` 须注明比赛类型（未注明默认国赛）。`academic-writing` 只改普通正文，输出普通正文补丁和审阅报告；其国赛内容红线标记（【国赛内容红线：xxx】）和摘要专项标记（【摘要专项：xxx】）进入 H8 审查包的 `blockers`，不写入论文正文。

主 agent 逐项判定红线标记：可由 H8 论文 agent 补论证的，回流 H8；需补推导或验证的，回流 H5/H6；用户确认接受带红线交付的，记录在 `approval_log.yaml` 后放行。红线标记未处理且用户未明确接受时，保持 `PAUSE`，不得进入 H9。`academic-writing` 的正文补丁须经 `mathmodel_patch_guard.py` 保护器 PASS 后才合并。

## 增量回流与验证机制

比赛期间项目文件发生变化时，先填写 `.contest/change_impact_card.yaml`，再运行 `scripts/validation_router.py <project-root>`。路由器输出唯一复核计划，主 agent 按计划定向回流；计划外节点不得自动重跑，也不得用局部复核替代 H9 完整交付门禁。字段、哈希、允许文件类型和失败处理以 `references/incremental_validation_policy.md` 为准。

| 等级 | 适用变化 | 复核范围 | 默认视觉检查 |
|---|---|---|---|
| L0 | 正文措辞、普通排版、论文元数据或引用表述，模型和数字保护字段未变 | H8 叙事、主张覆盖、成品过程词检查 | 否 |
| L1 | 单张图件或图表登记变化 | H7 登记、格式、来源和 SciPilot QA | 是 |
| L2 | 单个小问的模型、代码、数据或结果变化 | 该小问 H5，定向 H6，受影响 H7/H8 | 仅受影响图表 |
| L3 | 全局数据、符号、跨问接口、全局假设或多小问关系变化 | 从 `earliest_invalid_node` 到 H8 的完整相关链 | 涉及图表时是 |

`competition_fast` 只减少与变更无关的重复验证：项目文件变化不触发技能全套测试；技能源码或检查器源码变化必须将 `skill_code_changed` 设为 `true` 并执行完整技能测试。H2–H9 的用户批准门、冻结哈希和 `H9` 完整交付门禁始终保留。上游变更后只将引用变更字段的下游产物标记为 `stale`；未受影响的产物不得重新生成。需要描述具体下游影响时，可在同一变更记录中附 `rework_patch.yaml`。

## 信息最小分发

- 题面：H1 读取原题面并按 `templates/problem_statement.md` 双结构模板产出 `problem_statement.md`：上半部分为完整题面翻译（保留背景、小问原文、公式 LaTeX 与全局约束，不丢信息），下半部分为题目解读（每问目标/输入/输出/难点/前后关系）与歧义清单；不含附件数据。主 agent 在 H2/H3/H5 决策时读取该文件；H7、H8 的任务卡 inputs 必须包含该文件。该文件为只读语境参考，结构化事实以 `unified_problem_package.yaml` 为准；发现冲突上报主 agent，不自行裁决。
- 题面预载：H1 产出 `problem_statement.md` 后，主 agent 一次性创建全部固定角色子 agent（H5/H6/H7/H8），创建时把 `problem_statement.md` + 对应角色预热包（`references/warmup/` 下 h5_solver/h6_verifier/h7_figure/h8_writer）作为初始上下文预载，使各角色从出生即建立题目认知和职责边界。H8 额外预载 `references/h8_writer_first_protocol.md`，确保 writer-first 规则在 H8B 生效。superpowers 实例回流复用时上下文完整，题面和预热包已在上下文，不重复注入；只有新 spawn 的实例才重新预载。创建与任务派发分离：实例在 H1 后一次性创建并预热，任务卡按节点派发，派发时机不早于所需上游产物就绪。预热不需要回执，子 agent 创建后即休眠等正式任务卡。**这是检查器硬约束**：`spawn_roles` 调用记录必须登记 `skill=superpowers:using-superpowers`、`completed=true`、`after_node=H1`、`created` 恰好为 H5/H6/H7/H8 且唯一；`agent_instances` 的 preloaded 必须包含题面 + 对应预热包；不满足即 BLOCK。
- 附件：仅 H1 读取原始附件；下游通过统一问题包的数据字典和约束获取附件信息，不直接读取原始附件。
- H3 的用户和外部文献 agent 处理全文；H5 阶段一仅读取结构化文献文件并登记可实际采用的知识、数据、参数或基准。
- H5 接收本问路线、相关文献证据、数据和契约；H6 接收推导、代码、结果、登记和冻结候选；H7 接收冻结数据和图表需求清单，并由 SciPilot 基于真实数据形成决策卡；H8 接收全部冻结的模型、结果、图表、文献使用登记、引用与附录映射。
- 任何上游事实、模型、数字、引用或图表变化都使下游状态变为 `stale`，必须回到对应节点重新审查和批准。

## H5–H7 轻量视觉证据接口

H5 在模型、结果和验证候选冻结后生成 `visual_evidence_packet.yaml`，为每个小问登记独立的信息单元；每个单元必须绑定项目内文件、SHA-256 和定位。该包只传递图表所需的最小事实，不携带全文、完整代码、对话或调试材料。

H6 将该包作为独立核验输入，检查证据新鲜度、模型契约哈希、小问覆盖、单位/范围和重复事实，并以当前 H6 实例签名后写回 `status: verified`。H7 只能读取已核验包：`visual_argument_plan.yaml` 的每个真实图表槽位必须绑定 `information_unit_ids`；`standard` 图至少绑定两个独立单元，单一证据只能使用 `compact` 并说明理由。`figure_registry` 必须同时登记计划单元和实际实现单元，二者完全一致；任一缺失、过期或偷换都保持 `PAUSE`。

## 状态与交付

节点状态为 `not_started → draft → review_pending → approved → frozen`；证据不完整时使用 `evidence_gap` 并回流；输入缺失或用户批准缺失时使用 `PAUSE`。图表默认视觉检查，其他流程默认不做视觉检查，除非用户明确要求。所有交付成品执行负向回声自查，只保留定稿的证据、推导、结果和结论。
