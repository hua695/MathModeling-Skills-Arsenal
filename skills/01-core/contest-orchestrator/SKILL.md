---
name: contest-orchestrator
description: 数学建模竞赛唯一主控流程：题目解析、选题与模型规划、baseline、求解、图表、论文、评审、交付门禁和 replay；支持 AUTO/COLLAB/LOCK 与主会话—fork 分支协作。
metadata:
  version: "4.19"
  changelog: |
    v4.19 (2026-09-27): H4 节点取消，其蓝图设计职责并入 H5（建模与求解）；H3 直接到 H5，H6-H9 编号不变；H5 内部四阶段迭代（蓝图设计→快速验证→优化迭代→完善冻结）
    v4.18: 稳定版
---

# contest-orchestrator

数学建模竞赛唯一主控入口。稳定版本为 `4.19`（H4已并入H5）；版本发布必须完成静态检查、负例、replay、真实项目闭环和安全审计。

主会话负责范围、事实、权限、冻结、节点裁决和最终交付；fork 分支负责获得授权的赛题求解、实验、图表或论文工作。正式项目、数据、replay 和交付包写入项目工作区，不写入 skill 安装目录。

## 1. 启动与模式

先确定任务范围，再按需读取一个工作模式。未指定模式时，使用范围路由器识别最小任务范围；不读取未选模式的完整规则。

```text
python scripts/mode_router.py --mode <mode> [--variant <variant>]
python scripts/scope_router.py --prompt "用户原话" --workspace <项目根>
```

选择 `full-contest-mathorcup` 时，范围路由器加 `--mode full-contest-mathorcup`，使阶段与门禁输出采用 M1–M5。

可用模式：

- `full-contest-legacy`：完整竞赛流程，兼容 v4.16 稳定基线规则。
- `full-contest-4-18`：稳定协作流程，使用 G0–G6 节点门禁。
- `full-contest-harness`：受控自动化测试流程，使用 H0–H9。
- `full-contest-mathorcup`：MathorCup 大数据竞赛流程，使用 M1–M5；逐节点人工确认，固定子 agent 使用 Luna/Sol 且推理强度均为 `max`，详见 `references/modes/full-contest-mathorcup.md`。
- `subproblem`、`paper`、`figures`、`delivery-audit`、`skills-optimization`：分别处理单问、论文、图表、交付审计和技能优化。

单次任务只能有一个 `active_mode`。模式文件只规定边界和阶段；题型、专业写作和图表工作由对应 skill 执行。调用外部 skill 前必须读取 `references/external_skill_adapters.md`；外部 skill 只能执行当前任务卡中的专业子任务，不得切换模式、扩大范围或替代主会话决策。

### Harness 硬门禁

仅当 `active_mode=full-contest-harness` 时，主 agent 必须在 H0 前实际调用 `superpowers:using-superpowers`，并按 `references/modes/full-contest-harness.md` 登记固定角色、节点任务卡和调用记录。题意理解、解题、验证、图表、论文由各自固定角色在其节点实际调度；主 agent 不代做这些专业产物。未调用、调用记录缺失、任务卡缺失或以单 agent 流程替代时，状态必须为 `BLOCKED_INPUT` 或 `PAUSE`。H8 必须实际调用 `academic-writing` 与 `mathmodel-latex-skill`；H9 必须实际调用 `bzd-review-paper` 与 `mathmodel-latex-skill`，每项都要登记可存在性校验的 `evidence_ref`，缺失即不得过门。

Harness 的 H2–H9 均为人工批准门：节点完成后先提交 `review_packet` 中的重要文件，再由用户明确批准；审查包或产物哈希变化即暂停。每张实际子 agent 任务卡还必须显式指定节点绑定的 `model` 与 `reasoning_effort`，不得只依赖运行时默认值。使用 `templates/harness_control.yaml` 初始化项目控制记录；比赛期间使用 `validation.profile=competition_fast` 和 `.contest/change_impact_card.yaml` 选择增量复核范围。进入下一节点或完成变更复核前运行：

```text
python scripts/check_harness_control.py <project-root> --through H<n>
```

H5 结果冻结后还必须登记 `run_manifest` 并运行 `python scripts/check_h5_result_traceability.py <project-root> --strict`。运行清单绑定 seed、可执行命令、主结果哈希、正式记录边界、模型契约哈希和敏感性/鲁棒性报告；敏感性/鲁棒性报告还必须登记 `canonical_report` 的路径与 SHA-256。缺少记录保持 `PAUSE`，路径、文件或哈希不一致为 `BLOCK`。该检查不替代 H6 独立验证、H8 素材准入或 H9 严格交付。

启用 `reader_evidence_protocol: "1.0"` 后，读者证据链成为 H5–H8 的机器门禁：H5 的每个小问模型卡必须登记问题需求、数据范围、假设可追溯性、推导链、最终求解模型和有证据的模型评价；结果解释卡必须登记观察模式、比较基准、决策含义和边界；H7 的每个视觉槽位必须明确 `figure`、`table` 或 `text` 及其读者职责；H8 的作者简报和章节卡必须登记“开篇张力—证据序列—解释动作—过渡问题”。H8 先读取 `references/paper_author_evidence_protocol.md`，将这些卡片转化为面向读者的论证与自然段；缺少证据链时返回 `evidence_gap`，回到对应上游节点补证，不得用格式性段落补齐正文。

H8 论文 agent 必须先审查冻结素材是否覆盖目标篇幅和每个小问的推导、结果、验证、图表、引用依据。`paper_material_readiness.yaml` 使用 `schema_version: "2.0"` 时，必须提供 `evidence_matrix`：逐小问登记问题映射、假设、符号、推导、算法与参数、量化结果、验证、图表或表格、文献使用、结论与边界、敏感性或稳健性，并登记 `global.target_length`；状态为 `PASS` 时每格只能是 `ready` 或合法的 `not_applicable`。H5 必须为每个小问生成唯一的 `model_summary_cards.yaml`，集中登记最终可计算模型、求解接口、来源公式和模型契约哈希，并由 H6 核验为 `verified`。H5 还必须为核心结果生成含事实、意义、依据和适用范围的 `result_interpretation_cards.yaml`，并由 H6 核验。H8A 必须调用 `academic-writing` 生成哈希绑定的 `paper_argument_blueprint.yaml`、经用户批准的 `paper_author_brief.yaml` 和 `abstract_argument_card.yaml`；摘要论证卡固定读者契约、全文主张、统一建模主线、逐问方法—结果—意义、验证结论、总评和关键词，逐问绑定冻结证据。作者简报固定全文主张、读者问题、章节目的、问题引入段、双小节结构、论证、证据和图表职责。H8B 的论文 agent 每次只接收一个 `chapter_writing_card.yaml`、一个哈希绑定的 `paper_continuity_context.yaml`、已核验的 `model_summary_cards.yaml`、摘要论证卡和对应冻结材料；每张章节卡必须填 `abstract_contribution`。它遵循 `references/h8_writer_first_protocol.md` 与 `references/model_summary_protocol.md`：先回答读者问题、组织论证和自然段，再做硬性检查；按“问题引入与建模思路段—模型建立—模型求解与结果分析”写作，把最终模型框放在模型建立小节末尾；一级标题使用中文序号，“模型假设”和“符号说明”分设为两个全局一级章节；不将建模材料按产生顺序转写为论文，也不把质量门禁当作正文任务。H8B 不写最终摘要。H8C 由 `academic-writing` 先通读完整论文、检查读者路径和章节递进，再依据摘要论证卡和各章摘要贡献最后写摘要，并运行 `scripts/check_abstract_contract.py --strict` 登记 `abstract_contract_report`；报告未通过不得完成 H8。素材不足时返回 `evidence_gap` 并回到 H5/H6/H7 补足，不得用重复表述、泛泛背景、空洞评价或文献堆砌填充篇幅。

Harness 每次运行只有一个 H5 `solver_instance_id`。同一解题实例负责所有小问、跨问接口和整体结论；条件辅助 agent 仅能回传局部计算、数据处理或代码实验的可验证证据。每次实际 `spawn_agent` 必须写入 `dispatch_records`，并与任务卡、节点角色、模型、推理强度、实例 ID 和任务卡 SHA-256 一致；H6 必须使用不同于 H5 的实例。

H6 的 `global_interface_check.yaml` 中，每条结构化接口字段必须登记 `comparison_status`、项目相对 `source_path` 和当前文件的 `source_sha256`。H7 生成任务卡的 `scope.phase` 为 `H7_generate` 时，必须登记 `scope.approved_visual_plan_sha256`；检查器将其与当前视觉计划及对应 `H7_VISUAL_PLAN` 批准记录配对，并要求生成派发时间晚于批准时间。

H8 开始写作前，主 agent 汇总并由 H6 核验 `paper_material_readiness.yaml`、`global_interface_check.yaml`、`result_interpretation_cards.yaml` 和 `paper_claim_coverage.yaml`。`academic-writing` 生成的 `paper_argument_blueprint.yaml` 与 `abstract_argument_card.yaml` 必须绑定叙事和解释卡哈希，并经用户与写作计划一并批准。每个 H8B 章节还必须生成与作者简报、当前章节卡绑定的 `paper_continuity_context.yaml`，只提供压缩后的全文主张、已完成章节收束、术语口径和前后章节衔接；章节卡的 `abstract_contribution` 必须提供方法、结果、意义和证据引用。素材准入必须为 `PASS`；首次预检未通过时只提交一份完整 `evidence_gap_matrix.yaml`，由主 agent 一次性协调 H5/H6/H7 补齐。H8 只组织已冻结且已登记证据，不新增模型结论、数字、引用用途或图表解释；摘要只能在正文与附录定稿后由 H8C 最后写作，并以严格摘要报告闭环。

`paper_narrative.global.paper_spine` 是全文唯一章节主线，必须同步进入论证蓝图、作者简报、章节卡和连续性包。`core` 章节集中承载建模与求解，`support` 章节只为核心论证提供铺垫、连接、解释或收束；每章必须声明 `chapter_role`、`reads_from`、`feeds_to`、`new_claims_allowed` 和 `handoff_question`。检查器阻断孤立章节、角色错配、前后承接断裂和章节间主张漂移。

H6 仅按 `h6_verification_scope.yaml` 派发：首次在 H5 结果冻结后执行关键核验与登记的深度抽样；后续仅在模型、数据、关键结果或结果解释卡变化时定向复核。普通正文、排版、图表美化和附录格式变化不触发 H6。

### 增量回流与验证

比赛期间项目文件发生变化时，先填写 `.contest/change_impact_card.yaml`，再运行 `scripts/validation_router.py <project-root>`。路由器根据变更卡输出唯一复核计划；计划外节点不得自动重跑，也不得以局部复核替代 H9 完整交付门禁。完整字段、允许文件类型、哈希和失败处理见 `references/incremental_validation_policy.md`。

| 等级 | 适用变化 | 复核范围 | 默认视觉检查 |
|---|---|---|---|
| L0 | 正文措辞、普通排版、论文元数据或引用表述，模型和数字保护字段未变 | H8 叙事、主张覆盖、成品过程词检查 | 否 |
| L1 | 单张图件或图表登记变化 | H7 登记、格式、来源和 SciPilot QA | 是 |
| L2 | 单个小问的模型、代码、数据或结果变化 | 该小问 H5，定向 H6，受影响 H7/H8 | 仅受影响图表 |
| L3 | 全局数据、符号、跨问接口、全局假设或多小问关系变化 | 从 `earliest_invalid_node` 到 H8 的完整相关链 | 涉及图表时是 |

`competition_fast` 只减少与变更无关的重复验证：项目文件变化不触发技能全套测试；技能源码或检查器源码变化时，将 `skill_code_changed` 设为 `true` 并执行完整技能测试。H2–H9 的用户批准门、冻结哈希和 H9 完整交付门禁始终保留。上游变更后只将引用变更字段的下游产物标记为 `stale`；未受影响的产物不得重新生成。需要描述具体下游影响时，可在同一变更记录中附 `rework_patch.yaml`。

范围类型：

| 范围 | 行为 |
|---|---|
| `PLAN_ONLY` | 只生成题目理解、方案、风险和写作计划 |
| `SUBPROBLEM` | 只处理指定小问，明确输入、输出和时间边界 |
| `FULL_CONTEST` | 执行 A–G 全流程，正式交付使用 `STRICT` |
| `DELIVERY_AUDIT` | 只审计项目，不修改源项目 |

权限模式：

- `AUTO`：在已授权范围内自主推进；时间、证据或模型风险达到止损条件时进入收敛。
- `COLLAB`：G0–G6 关键节点暂停，等待用户确认后继续；确认包包括目标、证据、风险、影响、最小修改和回滚点。
- `LOCK`：冻结模型、数据、参数、结果和提交版本，只允许排版、可验证修复、图表美化和交付检查。

## 2. 全流程：FULL_CONTEST + STRICT

### A. 题目理解

建立条件台账、问题图、复杂度画像、数据审计、符号表和模型假设。每条假设记录简化内容、数据或题面依据、误差边界和适用范围。A 阶段通过：

```text
python scripts/check_core_execution.py <replay> --phase A
```

### B. 方案与 baseline

文献流程固定为“需求卡与检索提示词 → 用户检索并下载全文 → 用户的文献 agent 阅读全文并回传摘要、方法、数据和适用边界 → 主 Agent 摘要级整合与引用登记”。主 Agent 不主动联网检索、不替用户下载、不直接读取或解析文献全文。进入正式文献分析前，先生成 `literature_request.md` 与 `literature_request.yaml`，明确各小问覆盖、检索关键词和回传字段；用户回传 `literature_sources.yaml` 后，系统只读取题名、作者、来源、年份、DOI/官方链接、摘要和外部 agent 的结构化总结。所有 Harness profile 的文献总数硬范围为 6–11 篇，推荐 8–10 篇；中文文献必须逐小问覆盖，每个小问至少 1 篇；英文文献不设硬性最低数量，但建议覆盖全部小问。英文覆盖建议和推荐数量不阻断节点。每篇计入总数的文献均须有 `citation_key`、原文定位及在 H5 落位的模型、数据、参数、验证或结论用途。任一硬条件不通过时保持 `PAUSE`。

正式建模前必须收到并校验本题用户返回的 `literature_sources.yaml`；语言数量、总量或小问覆盖任一不通过，状态保持 `PAUSE`，不得进入建模或求解。该文件由用户检索下载文献后，交给指定文献 agent 生成结构化摘要、方法、数据、适用边界和证据定位。

文献证据通过后，才能使用题型 profile、选题评分和风险探针确定候选路线，形成 `method_transfer_map.json`、文献使用登记、`model_blueprint.yaml`、`model_contract.yaml`、接口契约和图表需求清单。需求清单仅登记正文主张、图号占位、目标小问、所需结果字段和候选来源，不得确定数据图的图型、视觉编码或版式。每个小问至少登记一条可落地的方法迁移（`adopt` 或 `adapt`）和一条实际数据、参数、测量先例或基准证据，并绑定 `citation_key`、证据定位、模型组件或数据字段及使用方式；登记不完整时不得确定模型路线、baseline 或图表需求清单。用户确认路线、文献用途和图表需求清单后，才进入正式建模。

机器门禁同步检查顺序：H3 必须登记需求清单、全文分析 agent 提示词和用户回传的 `literature_sources.yaml`；H5（建模与求解，已合并原 H4 蓝图设计职责）必须登记 `method_transfer_map.json`、`model_blueprint.yaml`、只含论证需求的 `chart_requirements.yaml` 以及完整求解产物；H5 的实际派发时间不得早于 H3 的批准时间。缺任一项保持 `PAUSE`，不得以补写节点记录替代真实文件。

先运行最简 baseline，只判断问题是否可解；未达到目标时才在已登记文献证据和路线约束下升级模型。

求解前必须完成：

- 变量、参数、中间量三集合及符号表闭环；
- 目标函数、约束、可行域、模型类别和规模量级；
- 求解方法、初始化、边界、终止条件和异常处理；
- 至少一项理论性质或可靠性说明；
- 结果文件、代码、数据和图表的源关系。

B 阶段通过：

```text
python scripts/check_core_execution.py <replay> --phase B
```

### C. 求解与图表

结果只能由代码、推导或可审计数据源生成，并即时写入 `results/`、CSV/JSON、敏感性结果和运行清单。记录随机算法的 seed、参数、环境、收敛或间隙；每个关键数字进入数字源登记或冻结表。

图表路由固定为：

| 图表类型 | 路由与登记 |
|---|---|
| 数据结果图 | `SciPilot → ModelViz → SciPilot`；登记 `generator=modelviz`、`semantic_qa=scipilot-figure-skill`、`formats=[svg,png]`、`insertion_format=svg`；页面排版另登记 `layout_mode` |
| 问题分析流程图、技术路线图、原理/机制/受力/几何和公式示意图 | Harness 按 H7 登记的路由执行；MathorCup 的问题分析与技术路线图用 `tech-route-maker`，机理/几何图用 `tikz-scientific-figures`。均须选择与路由一致的目录 `template_id`，保留可编辑源与 SVG/PNG，登记 starter 来源与哈希 |
| Draw.io 编辑图 | 仅用户明确要求时使用，登记 `user_requested=true`，输出 SVG/PNG 并保留 `.drawio` 源文件 |

画图默认做视觉检查，确认图片美观、整洁、可读、层级清楚、标注完整；非画图默认不做视觉检查，只有用户明确要求或命令显式提供 `--visual-check` 时才渲染和检查。视觉检查不能替代公式、数字、引用、来源和结构门禁。

数据结果图的图表决策卡必须由 `scipilot-figure-skill` 基于冻结数据生成；未登记 `decision_card` 和 `decision_author=scipilot-figure-skill` 时，禁止调用 ModelViz、确定图型或生成图像。每张图必须满足：先有完整图表决策卡；数据同源；图号与题注对应；坐标轴/单位/符号与符号表一致；来源登记真实；输出包含 SVG、PNG 和可编辑源；LaTeX 使用 SVG 插入。禁止饼图、双 Y 轴、彩虹色图、无单位坐标轴和把分类点连成无意义折线。

H7 图表 agent 在调用任何图表生成 skill 前，必须汇总生成 `visual_argument_plan.yaml`（`prepared_by=h7-figure-agent`）。该计划先回答“读者在这里需要理解什么、什么证据能降低理解成本、没有图会遗漏什么”，再决定是否需要视觉表达、每个槽位的表示方式和采用哪条路由。每个有图槽位还必须填写 `figure_intent`，明确读者问题、解释关系、必须出现/禁止出现内容、正文落位、图前/图后论证功能、唯一生成路由、模板状态、精确 `template_id`、`visible_element_map` 和 `canvas_profile`；H5→H6→H7 的 `visual_evidence_packet.yaml` 仍保持轻量证据接口。每个小问必须审计 `orientation`、`mechanism`、`model_structure`、`algorithm_process`、`result_evidence`、`validation_robustness` 六类视觉义务；结构化模型、迭代/启发式算法、机理/空间关系和主要结果的硬性义务由 H5 模型总结卡推断，不能用“文字已足够”规避。数据结果槽位才交由 `scipilot-figure-skill` 生成数据图决策卡；流程图、技术路线图和示意图分别交由对应专业 skill。多小问或存在跨问接口时必须增加 `global_story` 槽位。该计划不设脱离论证的固定总图数，但必须重新计算必需视觉槽位、必需图槽位和计划图数，且一张图不得同时填充多个槽位。

阶段一只提交视觉论证计划及 `.contest/reviews/H7_visual_plan_review_packet.yaml` 供用户审查；用户批准必须以 `.contest/approval_log.yaml` 中 `gate: H7_VISUAL_PLAN` 且覆盖当前计划 SHA-256 的记录为准。独立批准缺失时，H7 不得进入图型选择、模板检索、生成和登记；计划审查期间 H7 保持 `status: draft`，完成图表生成、质量检查和登记后才转为 `review_pending` 并提交普通 H7 最终审查包。批准后，阶段二才由 SciPilot 形成数据图决策卡或指定流程图、路线图和示意图路由。最终 `figure_registry` 的每张图必须用 `visual_slot_ids` 绑定已批准槽位，并复制计划的 `generation_route` 为 `generator`、登记 `template_status`、`template_id`、`visible_element_map`、`canvas_profile`、`template_sha256`、`template_fixture`、`visual_qa`、`claim` 和 `reader_takeaway`；流程图和 TikZ 图还必须登记 `starter_source`，并在可编辑源中保留模板来源标记。对应 starter fixture 未通过、视觉检查缺失、模板哈希不一致、计划外图表、必需槽位未闭合或注册表与计划不一致时 H7/H8 均 BLOCK。H8 只读取批准计划，不得新增图表来增加篇幅。

页面排版由 `mathmodel-latex-skill` 按登记的 `layout_mode` 执行，不由 SciPilot 或 ModelViz 改变图表语义。允许的入口只有 `single`、`side_by_side`、`wrap_short` 和 `tall_constrained`；具体宏与尺寸规则以 `references/figure_policy.md` 和 `mathmodel-latex-skill` 的布局契约为准。

H5→H6→H7 使用 `visual_evidence_packet.yaml` 传递最小图表证据：H5 生成，H6 以当前实例核验，H7 将信息单元绑定到视觉槽位和 `figure_registry`；标准图至少两个独立信息单元，单一证据只能使用带理由的 `compact`。

C 阶段通过：

```text
python scripts/check_core_execution.py <replay> --phase C
```

### D. 论文写作

写作前生成 `paper_outline.md` 与 `appendix_plan.yaml`，覆盖摘要、问题重述、问题分析、模型假设、符号说明、问题引入、模型建立、模型求解与结果分析、灵敏度分析、模型评价与改进、结论、参考文献和附录；摘要另由 H8A 生成 `abstract_argument_card.yaml`，由 H8C 在正文和附录定稿后最后写作。一级标题使用中文序号；“模型假设”和“符号说明”是两个独立一级章节；建模问题统一置于“模型建立与求解”一级章节下。建模问题章节必须读取 `references/model_summary_protocol.md`，按“问题引入与建模思路段 → 模型建立 → 模型求解与结果分析”的读者路径组织正文。

正文要求：

- 全文只设置一次“符号说明”章节；局部符号在正文首次出现处给出含义、单位或量纲、取值域和变量类型，全文符号、单位、上下标一致；
- “模型假设”和“符号说明”分别设置为全局一级章节；不得合并成“模型假设与统一符号”，也不得在每个小问重复生成独立符号章节；
- 每个问题标题后先写不编号的问题引入与建模思路段，交代任务、已知条件、关键困难、输出目标和前后小问关系；
- 每个问题默认只设“模型建立”和“模型求解与结果分析”两个编号小节；小节内使用无编号加粗引导词，不把任务卡字段变成目录；
- 建模与求解章节是正文论证中心；问题分析、模型评价、结论等支撑章节必须明确承接或回收核心章节主张，不得与建模章节割裂成独立文章；
- 推导完成后在“模型建立”小节末尾给出唯一的“最终求解模型”框，集中绑定决策变量、参数、目标/状态关系、约束/边界、来源公式和求解接口；
- “模型求解与结果分析”必须同时包含算法依据、实现条件、主要结果和结果意义；灵敏度或稳健性仅在有独立证据时单独成节，否则并入结果分析；
- 每个公式标注来源、推导链、含义、单位和边界条件；
- 每个算法说明选择理由、参数依据、终止条件和异常处理；
- 每个结论绑定结果文件、图表、表格或引用；
- 模型建立与求解保持全文核心体量，不能用空白页、重复公式或强制分页填充；
- 附录只放真实触发且支撑正文的内容；程序题默认在论文附录展示核心代码，完整源码登记到支撑材料，
  由 `appendix_plan.yaml` 的 `appendix_code_mode`、`core_source_files`、`full_source_files` 和
  `support_source_files` 统一管理；推导、数据验证和 AI 工具说明按附录计划登记；
- 数字只从权威结果源或冻结表进入论文，禁止手工改写未核验数字。

国赛 2026 规则：电子版不设目录；按湖南赛区确认口径，摘要不计入正文页数，正文页数从正文主体起计，包含正文主体、参考文献前的 AI 工具使用声明和参考文献，最多 30 页。提交论文文件总页数最多 51 页。当前国赛个人 profile 将总 PDF 35–51 页作为推荐区间，用于内容容量规划和人工复核；不得以重复或无效材料达到推荐下限。论文 PDF 必须是含文本层的非图片 PDF，论文文件不超过 20 MB；支撑材料使用 ZIP 或 RAR，文件不超过 20 MB，附录列出文件清单。全国规则与赛区口径存在差异时，以当前参赛赛区正式通知为准。

使用 AI 时，正文在参考文献前放置“AI工具使用声明”，支撑材料提供 `AI工具使用详情.pdf`，说明实际使用的工具名称与版本、用途与环节、关键提示/交互摘要、采纳、人工修改和核验情况。不要求把 AI 工具列入参考文献；声明可以简洁，但必须真实覆盖实际使用范围，突出参赛队主导核心建模、分析和结论，不得隐瞒使用或虚构未使用。

论文写作链固定为：`academic-writing` 数模学术写作适配层 → 必要时 `humanizer-zh`。两者只能处理允许的普通正文表达，不得改动公式、数字、引用、专业术语、表格、图表编号、模型逻辑和受保护结构。修改后重新运行一致性检查。

成品必须删除元话语、内部交流、提示词、评审过程、交接信息、用户信息、修改轮次、调试信息和未确认内容，只保留定稿事实、推导、证据、结果与结论。摘要按 profile 检查字数、逐问结论、数字溯源、独立总评和关键词格式；正文和摘要必须通过防 AI 痕迹硬性质控。

D 阶段通过：

```text
python scripts/check_core_execution.py <replay> --phase D
python scripts/check_math_contract.py <paper.md>
```

### E. Critic 评审

逐小问检查题面覆盖、假设、符号、公式推导、模型—代码—数据—图表一致性、结果可靠性、摘要、AI 痕迹、匿名、页数、引用和附录。每条问题记录位置、证据、影响、最小修改和修复后的验证状态；没有证据时不得把推测写成缺陷结论。

### F. 交付门禁

```text
python scripts/delivery_all.py <项目根> --strict
python scripts/delivery_all.py <项目根> --strict --research-evidence-strict
```

交付前必须通过模型、数据、结果、引用、图表、符号、推导、算法、摘要、附录、代码可复现、匿名、AI 工具说明、PDF 文本层、PDF 大小、LaTeX 警告、版面源规则、正式交付漂移和文件哈希检查。任何 `FAIL`、严格模式 `WARN` 或 `UNKNOWN` 均不得宣称交付完成。正式 PDF 必须由当前源文件生成并与交付清单一致。

### G. replay 与经验沉淀

保存决策、快照、经验使用、证据索引、运行清单和回放记录。只将已经验证、可复用且不依赖特定对话过程的规则写入经验库；不把未确认材料、临时数据、原始日志或内部交流写入长期规则。新版本完成静态、单元/回归、负例、隔离 replay、真实项目闭环和安全审计后，才可登记为稳定版；未通过时保留当前稳定版。

## 3. 主会话—fork 协作

主会话控制范围、事实、权限、冻结、冲突和最终交付；fork 分支执行授权的赛题、实验、图表或论文节点。分支回流必须提供：

1. 当前阶段和完成目标；
2. 可验证证据及相对路径；
3. 可复现命令、环境和验证状态；
4. 阻塞项、风险、禁止动作和未授权事项；
5. 下一节点首个状态报告。

回流前检查源文件、结果文件、登记表和当前 PDF 的新鲜度、SHA-256、来源关系与版本状态。节点产物只能进入授权工作区；论文交付物不得含内部日志、过程轨迹或未定稿内容。

## 4. 权威文件与按需加载

- 范围与模式：`references/task_scope_routing.md`、`references/mode_state_machine.md`、`references/collab_gate_policy.md`。
- 规划与证据：`references/evidence_first_planning.md`、`references/evidence_integrity.md`、`references/modeling_contract_hardening.md`、`references/research_evidence_contract.md`。
- 图表与论文：`references/figure_policy.md`、`references/figure_template_catalog.yaml`、`references/citation_policy.md`、`references/paper_review_and_absorption_lessons.md`、`references/paper_replay_lessons.md`、`references/appendix_coverage_policy.md`、`references/layout_and_delivery_drift.md`。
- H8 写作：`references/h8_chapter_execution.md`、`references/h8_writer_first_protocol.md`、`references/paper_author_evidence_protocol.md`；前者定义阶段路由，后两者定义读者优先的正文生成方式与证据转写契约。
- 增量复核：`references/incremental_validation_policy.md`；机器执行入口为 `scripts/validation_router.py`，项目模板为 `templates/competition_run_profile.yaml`、`templates/change_impact_card.yaml`，卡片结构为 `schemas/change_impact_card.schema.json`。
- 外部 skill：`references/external_skill_adapters.md`。其中的路由、输入输出、证据登记和视觉检查策略是唯一适配契约。
- 建模契约：`core/universal_modeling_contract.md`、`core/modeling_chapter_contract.md`、`core/appendix_contract.md`、`core/paper_hard_requirements.md`、`planner/modeling_profiles.yaml`。
- 机器可读路由：`manifest.yaml`、`scripts/script_registry.yaml`；版本唯一来源为 `VERSION`；范围唯一入口为 `scripts/scope_router.py`；增量复核入口为 `scripts/validation_router.py`；完整交付入口为 `scripts/delivery_all.py`；项目只读审计入口为 `scripts/audit_project.py`。

只在命中任务范围时加载对应参考材料；历史归档和 `scripts/archive/` 不参与运行时路由。

## 5. B 题项目模板与初始化（优化决策类）

B 题（优化决策类）项目配置复杂，包含 30+ 个 YAML 配置文件。为避免每次从零搭建，提供完整模板和一键初始化脚本。

### 5.1 快速初始化

```bash
python scripts/init_b_project.py <项目目录> --name "项目名称" --date "2026-09-XX"
```

示例：
```bash
python scripts/init_b_project.py "C:\Users\me\Workspace\2026国赛B题" --name "2026国赛B题"
```

初始化脚本会：
- 从 `templates/b_project_template/` 复制 43 个配置文件与目录结构
- 自动填充项目名称、日期
- 生成 README.md（含项目结构和快速开始指南）

### 5.2 模板目录结构

```
templates/b_project_template/
├── .contest/                    # 主控配置
│   ├── harness_control.yaml     # 节点状态、dispatch_records、skill_invocations
│   ├── approval_log.yaml        # 用户批准日志
│   ├── status_history.yaml      # 状态转移历史（P1-01 校验）
│   ├── reviews/                 # 各节点审查包（H2-H9）
│   └── task_cards/              # 各节点任务卡（H1, H5-H8）
├── paper/                       # 论文素材目录
├── figures/                     # 图表目录
├── results/                     # 结果文件
│   ├── input_manifest.yaml      # H9 输入清单（P0-06 校验）
│   └── sensitivity_report.yaml  # 灵敏度/鲁棒性报告（P0-02 校验）
├── run_manifest.yaml             # H5 可复现运行、正式记录与结果哈希
├── problem_profile.yaml         # 题型画像（方向三：题型差异化）
├── model_blueprint.yaml         # 模型蓝图
├── model_contract.yaml          # 模型契约
├── validation_contract.yaml     # 验证契约
├── h6_verification_scope.yaml   # H6 触发原因与定向验证范围
├── appendix_plan.yaml            # H8 附录覆盖与双层代码计划
├── paper_material_readiness.yaml # 论文素材准入（P0-03 新增 sensitivity_or_robustness）
├── evidence_gap_matrix.yaml     # 证据缺口矩阵
├── global_interface_check.yaml  # 全局接口检查（P1-02 校验）
├── paper_claim_coverage.yaml    # 主张覆盖表（P1-05 校验）
├── paper_narrative.yaml         # 论文叙事蓝图
├── visual_argument_plan.yaml    # H7 读者优先视觉论证计划
├── visual_evidence_packet.yaml  # H5→H6→H7 轻量视觉证据单元包
├── result_interpretation_cards.yaml # 核心结果解释卡（H5 产出，H6 核验）
├── paper_argument_blueprint.yaml # 读者问题—论证—证据蓝图（H8 阶段一）
├── paper_author_brief.yaml      # H8A 读者问题与章节目的简报
├── abstract_argument_card.yaml  # H8A 摘要读者契约与逐问证据卡
├── abstract_contract_report.json # H8C 严格摘要检查报告
├── chapter_writing_card.yaml    # H8B 当前章节写作卡
├── paper_continuity_context.yaml # H8B 全文连续性包
├── chart_requirements.yaml      # H5 图表需求清单（原H4职责，已并入H5）
├── model_summary_cards.yaml      # 每个小问的唯一最终求解模型卡（H5→H6→H8）
└── figure_registry.yaml         # 图表登记（P0-05 校验 SVG/PNG 存在性）
```

### 5.3 轻量视觉证据包

H5 以 `templates/visual_evidence_packet.yaml` 为模板，为每个小问登记可追溯的信息单元及哈希绑定证据；不得嵌入全文、完整代码、对话或调试材料。H6 核验来源文件、哈希、定位、模型契约绑定和信息单元完整性，并把当前验证实例写入包。H7 的视觉槽位与 `figure_registry` 必须绑定这些单元：`standard` 图至少包含两个独立单元，只有单一证据时才可使用 `compact`，并写明原因。该包是 H5→H6→H7 的最小证据接口，不能替代模型、结果、验证和图表登记文件。

### 5.4 B 题特有硬门禁

B 题（优化决策类）相比 A/C 题有额外硬门禁：

| 门禁 | 位置 | 要求 |
|------|------|------|
| 结果与灵敏度追溯 | H5 → check_h5_result_traceability.py + check_model_evidence.py | 运行清单登记 seed、命令、结果哈希、正式记录边界和模型契约哈希；optimization 能力子问题还必须有 sensitivity/robustness 报告，status=verified，扰动点数值完整（P0-02） |
| 灵敏度素材准入 | H8 → paper_material_readiness.yaml | 每个子问题必须登记 sensitivity_or_robustness 字段，文件存在且哈希匹配（P0-03） |
| 图表产物存在 | H7 → check_harness_control.py | 每张图必须有 SVG 和 PNG 文件，路径字段名为 svg/png（不是 svg_path/png_path）（P0-05） |
| 模板执行闭环 | H7/H8 → check_visual_evidence.py | 每张图必须登记精确 `template_id`、`visible_element_map`、`canvas_profile`、`template_sha256`、fixture 报告和视觉检查；流程图/TikZ 图还必须绑定 catalog starter、来源标记与哈希 |
| 视觉论证覆盖 | H7 → check_visual_evidence.py / check_harness_control.py | 每个小问完成六类视觉审计，硬性槽位必须有独立图并闭合到 `figure_registry.visual_slot_ids`；计划外图表 BLOCK |
| 输入哈希重算 | H9 → check_harness_control.py | input_manifest.yaml 中每个文件的 SHA-256 必须与实际文件一致，总哈希按路径排序的 path:sha256 列表计算（P0-06） |

### 5.5 常见问题与经验

详细的配置坑点、字段格式、调试经验见：
`references/b_project_gotchas.md`

该文档记录了实施过程中发现的所有"坑"，包括：
- H7 图表字段名（svg/png 而非 svg_path/png_path）
- paper_material_readiness verified_by 必须为 "H6"
- target_length sections 中 evidence 和 appendix 类型都需要 material_refs
- H9 input_sha256 重算逻辑
- user_approval 循环依赖问题
- 等等
