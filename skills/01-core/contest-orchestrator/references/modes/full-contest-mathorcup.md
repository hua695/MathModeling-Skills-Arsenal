# MathorCup 大数据竞赛：M1–M5

`active_mode: full-contest-mathorcup`。本模式面向当前 Codex 中的 MathorCup 数学应用挑战赛大数据竞赛全流程。赛期、题目、提交格式、页数、代码和 AI 使用要求只从本届官方规则及题面建立项目 `competition_profile.yaml`；未核实的要求不得写成硬门。模式执行文件位于独立项目工作区，不写入技能目录。

使用 `templates/mathorcup_control.yaml`、`templates/mathorcup_task_card.yaml` 和 `templates/mathorcup_review_packet.yaml` 建立 `.contest/` 控制记录，字段遵循 `references/mathorcup_artifact_contract.md`。主 agent 负责模式、任务卡、路线裁决、冻结、向用户提交审查包和最终交付；专业产物由固定角色在授权范围内完成。每次只推进一个节点。当前节点的审查包与重要产物均获得用户的当前 SHA-256 批准后才能进入下一节点；用户未批准时保持 `PAUSE`。执行门禁：

```text
python scripts/check_mathorcup_control.py <project-root> --through M<n>
python scripts/check_mathorcup_control.py <project-root> --preflight-writing
```

`--through` 检查截至指定节点的批准、任务卡、调度、子 skill 和证据；`--preflight-writing` 检查 M4 正文写作前的视觉计划、论证蓝图、素材准入和主张覆盖。检查器只核对项目登记与文件内容；主 agent 必须凭实际调用回执登记 `dispatch_records` 和 `skill_invocations`，不得代填未发生的调用或批准。

## 固定角色和模型

| 角色键 | 职责 | 模型 | 推理强度 |
|---|---|---|---|
| `data` | 全题数据字典、EDA、特征与泄漏排查 | `gpt-6-luna` | `max` |
| `solver` | 全部小问的统一建模、baseline、实验、参数与跨问接口 | `gpt-6.1-sol` | `max` |
| `verifier` | 独立检查数据泄漏、实验设计、结果、泛化与论文素材 | `gpt-6.1-sol` | `max` |
| `figure` | 图表计划、按冻结数据成图、语义/技术/视觉检查 | `gpt-6-luna` | `max` |
| `writer` | 基于冻结素材组织论证、正文、摘要和附录 | `gpt-6.1-sol` | `max` |

主 agent 使用当前会话模型，不擅自更换。五个固定角色均禁止 `gpt-6-astra` 和自动升档。每个角色在一次运行中登记唯一 `agent_instance_id`，后续节点用同一实例继续对话和派发新任务卡。`solver_instance_id` 唯一并覆盖全部小问；`verifier` 与 `solver` 必须是不同实例且独立审阅，不验证自身产物。辅助 agent 只按 `conditional` 做局部计算、数据处理或代码实验，回传可复核证据，不得更改模型路线、汇总最终结论或替代固定角色。实例无法续用时暂停，向用户说明上下文衔接与额度影响，获得确认后从冻结产物恢复；不得默认为同一实例。

M1 的 `data` 从题面及附件建立 `problem_statement.md`。题面冻结后，主 agent 为其余固定角色创建实例并预载该文件与角色任务卡；只在对应节点派发执行任务。预载不构成节点完成或专业调用。`agent_instances` 登记预载文件与哈希；每次真实派发新增 `dispatch_records`，包含任务卡路径与哈希、实际模型、推理强度、实例 ID 和时间。任务卡只给当前节点必要的冻结输入及哈希，不反复灌入全项目上下文。

M3 如需 `conditional_support`，辅助实例使用 `gpt-6-luna/max`，任务卡绑定唯一 `solver_instance_id`；`allowed_output_kinds` 仅可为 `local_computation_evidence`、`data_processing_evidence` 或 `code_experiment_evidence`，并显式禁止更改模型路线、写最终结果或汇总结论。

每个子 agent 回传四段：完成项、变更摘要、自检结果、待裁决项。主 agent 依据回传、审查包和检查器裁决；不让任一子 agent 替用户批准。

## 节点契约

| 节点 | 主责与产物 | 必调子 skill | 人工确认 |
|---|---|---|---|
| `M1` 题意与数据边界 | `data` 建立 `problem_statement.md`、`data_overview.yaml`、`task_kpi.yaml`，逐问声明输入、输出、评价指标、数据来源及题面歧义；主 agent 建立官方规则证据和 `literature_request.yaml` | `math-model-selector` | 确认题意、任务划分、指标和官方规则范围 |
| `M2` EDA 与特征 | `data` 产出 `eda_report.md`、`features.yaml`、分割/预处理协议；`verifier` 独立签署 `leakage_audit.yaml`；主 agent 纳入用户回传的 `literature_sources.yaml`；需要 EDA 图时由 `figure` 处理 | `data-science-stack`；成图时 `scipilot-figure-skill` → `modelviz` → `scipilot-figure-skill` | 确认数据理解、特征、文献用途和泄漏审查，肉眼查看图表 |
| `M3` 统一建模与实验 | 单一 `solver` 完成全部小问的 baseline、候选模型、公平对比、调参和泛化验证；输出 `run_manifest.yaml`、模型/结果解释卡；`verifier` 独立签署 `independent_validation.yaml` | `math-model-selector`、`data-science-stack`；成图时同 M2 数据图路由 | 确认统一路线、跨问接口、模型选择和量化结果 |
| `M4` 图表与论文 | `figure` 先提交 `visual_argument_plan.yaml`；`writer` 建立 `paper_argument_blueprint.yaml`、`paper_material_readiness.yaml`、`paper_claim_coverage.yaml`，逐章写作并通读，摘要最后写；论文源、PDF 和附录按官方要求生成 | `academic-writing`、`mathmodel-latex-skill`；最终成图按图表路由 | 先分别批准图表计划与写作蓝图，再逐章审查，最后批准全文 |
| `M5` 复现与交付 | 主 agent 核查隔离目录复现、随机种子、相对路径、依赖、论文、引用、匿名、AI 说明、官方格式及交付包；输出 `reproducibility_report.yaml` 和 `delivery_report.yaml` | `mathmodel-latex-skill`；评审 skill 可按题型适配后调用 | 用户核对正式提交包并批准最终版本 |

子 skill 的调用必须真实发生，并登记完成状态、证据路径和当前哈希。`modelviz` 是任务卡中的规范名称。画图前读取 `references/external_skill_adapters.md` 和 `references/figure_policy.md`：数据图由 SciPilot 给出图表决策卡，ModelViz 检索模板、适配真实数据和导出，SciPilot 完成语义、技术、视觉检查；问题分析流程图、技术路线图和算法流程图由 `tech-route-maker` 制作，机理、模型结构和几何示意图由 `tikz-scientific-figures` 制作。每个图位的 `generation_route` 和 `template_id` 必须与 `references/figure_template_catalog.yaml` 一致。图像交付只登记 SVG、PNG 和可编辑源；LaTeX 插入 SVG。画图默认做视觉检查，其他工作默认不做，除非用户要求。

文献由用户检索、下载并委托其文献 agent 汇总。主 agent 先交付逐问覆盖、中文/英文数量建议与可复制检索提示词，再读取用户回传的题录、摘要、方法、数据、适用边界和原文定位。`literature_sources.yaml` 必须覆盖全部小问、登记实际用途并绑定回传摘要的路径与哈希；M2 未通过时保持暂停，不能进入 M3 正式建模。实际引用须对应模型、数据、参数、验证或解释用途；禁止凭空补文献或把固定篇数当作本届官方规则。

## M2/M3 证据门

先按题目类型确定分类、回归、预测、评价或混合任务，再选择指标和分割方式。所有填补、编码、标准化、特征选择、目标编码及调参只在训练折内拟合；时间序列按时间切分，实体相关样本按组隔离。测试集不参与任何预处理拟合或选择。`leakage_audit.yaml` 绑定数据与特征流水线哈希、分割策略、检查项及 `verifier` 实例，`status: PASS` 才能批准 M2。

M3 对每个小问登记 baseline、候选模型、同一数据切分与指标、参数范围、固定种子、实验命令、结果路径与哈希。`run_manifest.yaml` 支持在隔离目录重跑；`independent_validation.yaml` 对跨问字段、单位、数据版本、训练/验证/测试边界、泛化、结果来源与结论逐项签署。任何高分但存在泄漏或不可复现的结果不得冻结。最终建模路线与关键结论由用户确认，AI 只作竞赛规则允许的辅助。

## M4 写作准入与审查

在图型选择及正式成图前，`figure` 依据已验证结果提交 `visual_argument_plan.yaml`：每个槽位写明读者问题、冻结证据、生成路由、正文落位、图注主张和视觉收益。用户批准 `M4_VISUAL_PLAN` 且哈希仍一致后才制作正式图。图表计划不设固定数量；只有证据和读者任务支持的图才保留。

M4 图表任务卡以 `scope.phase: plan` 和 `scope.phase: generate` 分开；生成派发时间必须晚于视觉计划批准。论文任务卡以 `scope.phase: plan` 和 `scope.phase: write` 分开；正文派发时间必须晚于写作蓝图批准，并输入当前素材准入与主张覆盖哈希。`figure_registry.yaml` 将每个正式图绑定到已批准槽位，登记真实来源、决策卡、SVG/PNG 哈希、SVG 插入格式和视觉检查结果。计划外图和提前派发均不得过门。

`writer` 使用 `templates/mathorcup_paper_argument_blueprint.yaml` 在写正文前提出 `paper_argument_blueprint.yaml`：全文主张、逐问论证路线、章节职责、篇幅容量、证据与图表落位。用户批准 `M4_WRITING_PLAN` 后，还须通过 `paper_material_readiness.yaml` 的逐问素材准入和 `paper_claim_coverage.yaml` 的主张证据覆盖。素材准入逐问检查题目映射、假设、符号定义、数据处理、模型选择、方法与参数、量化结果、独立验证、图表或表格、文献实际用途、结论与边界，并由 `verifier` 签署。任一缺口集中写入一份 `evidence_gap_matrix.yaml`，主 agent 一次性分派到 M2/M3/图表补齐；不靠填充性文字凑篇幅。

正文按 `chapter_writing_card.yaml` 一章一章取用冻结证据；每章审查包经用户批准 `M4_CHAPTER:<chapter-id>` 后再写下一章。H8 的符号首次定义、公式可审计、数字/引用/图表来源绑定、摘要最后写、元话语与负向回响清理同样适用。经典模型公式可以引用并解释其本题变量与使用条件，不能省略关键适配、参数和推导依据。论文结构由本题证据与官方格式决定，数据预处理和实验结果应有清晰的独立论证空间，不强制固定章节比例。

## M5 交付

代码、数据处理、配置、环境、固定种子、运行命令和输出映射必须足以复现主要数字。`reproducibility_report.yaml` 记录隔离目录复跑命令、退出码、结果哈希及允许的数值容差。`delivery_report.yaml` 将官方格式、论文编译、代码复现、数字/图表/引用一致性、匿名与 AI 使用说明、元话语/负向回响检查、交付文件逐项绑定证据；全部为 `PASS` 才提交 M5 审查包。国赛专属页数和格式检查不得套用到本模式。

只保留最终定稿内容在论文、提交包和第三方报告中。主会话—fork 回流沿用主技能契约：fork 交付可验证的文件与哈希，主会话逐项审核后吸收；未确认经验不进入技能规则。
