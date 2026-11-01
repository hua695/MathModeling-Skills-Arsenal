# MathorCup 大数据竞赛：M1–M5

`active_mode: full-contest-mathorcup`。本模式面向当前 Codex 中的 MathorCup 数学应用挑战赛大数据竞赛全流程。赛期、题目、提交格式、页数、代码和 AI 使用要求只从本届官方规则及题面建立项目 `competition_profile.yaml`；未核实的要求不得写成硬门。模式执行文件位于独立项目工作区，不写入技能目录。

使用 `templates/mathorcup_control.yaml`、`templates/mathorcup_task_card.yaml` 和 `templates/mathorcup_review_packet.yaml` 建立 `.contest/` 控制记录，字段遵循 `references/mathorcup_artifact_contract.md`。主 agent 负责模式、任务卡、路线裁决、冻结、向用户提交审查包和最终交付；专业产物由固定角色在授权范围内完成。每次只推进一个节点。当前节点的审查包与重要产物均获得用户的当前 SHA-256 批准后才能进入下一节点；用户未批准时保持 `PAUSE`。执行门禁：

新运行使用模板中的 `execution_protocol: "2.0"`，并读取 `references/mathorcup_execution_protocol.md`；该契约补充题意集合、真实复现等级、用户可访问角色登记和论文图件接入。历史控制记录未启用该字段时保持原解释，不追溯补造登记或批准。

```text
python scripts/check_mathorcup_control.py <project-root> --through M<n>
python scripts/check_mathorcup_control.py <project-root> --preflight-writing
python scripts/check_mathorcup_control.py <project-root> --preflight-draft
```

`--through` 检查截至指定节点的批准、任务卡、调度、子 skill 和证据；`--preflight-writing` 检查 M4 正文写作前的视觉计划、论证蓝图、素材准入和主张覆盖。检查器只核对项目登记与文件内容；主 agent 必须凭实际调用回执登记 `dispatch_records` 和 `skill_invocations`，不得代填未发生的调用或批准。

新建运行采用 `nodes.M4.visual_workflow: chapter_parallel`，并读取 `references/mathorcup_chapter_parallel.md`：先按依赖完成并批准一章，再生成该章图表提示词；图件与下一章并行，摘要最后写。`--preflight-draft` 仍只读检查写作准入，正式 M4 节点门仍检查全部图件、整合和终审。历史 `writer_first_batches` 或未设置字段的控制记录保持原顺序，不追溯迁移。

## 固定角色和模型

| 角色键 | 职责 | 模型 | 推理强度 |
|---|---|---|---|
| `data` | 全题数据字典、EDA、特征与泄漏排查 | `gpt-6-luna` | `max` |
| `solver` | 全部小问的统一建模、baseline、实验、参数与跨问接口 | `gpt-6.1-sol` | `max` |
| `verifier` | 独立检查数据泄漏、实验设计、结果、泛化与论文素材 | `gpt-6.1-sol` | `max` |
| `figure` | 按用户确认的论文图表需求选择视觉表达、成图和检查 | `gpt-6-luna` | `max` |
| `writer` | 基于冻结素材出批次初稿、选择所需图表、接图并完成论文 | `gpt-6.1-sol` | `max` |

主 agent 使用当前会话模型，不擅自更换。五个固定角色均禁止 `gpt-6-astra` 和自动升档。每个角色在一次运行中登记唯一 `agent_instance_id`，后续节点用同一实例继续对话和派发新任务卡。`solver_instance_id` 唯一并覆盖全部小问；`verifier` 与 `solver` 必须是不同实例且独立审阅，不验证自身产物。辅助 agent 只按 `conditional` 做局部计算、数据处理或代码实验，回传可复核证据，不得更改模型路线、汇总最终结论或替代固定角色。实例无法续用时暂停，向用户说明上下文衔接与额度影响，获得确认后从冻结产物恢复；不得默认为同一实例。

M1 的 `data` 从题面及附件建立 `problem_statement.md`。其余固定角色在 M1 获批后按首次执行时点初始化；尚未需要的角色不创建、不填占位实例 ID、不反复预载。固定角色、临时辅助角色和恢复实例，首次创建就必须是用户可以直接进入并持续沟通的会话；仅创建者能访问的原生内部实例不满足此要求。用户已授权建立角色会话时，使用当前平台实际提供的用户可访问会话创建与续用工具；工具不可用或授权不足时报告缺口，不静默降级。创建后立即在项目现有 `.contest/agent_registry.yaml` 登记真实 `thread_id` 和执行 `agent_instance_id`，返回会话入口，再派发工作；异步创建仅取得客户端占位 ID 时登记为 pending，不能当真实 thread ID 使用。后续先查 registry 并复用原会话，恢复保留旧身份与派发历史。`agent_instances` 只保存已创建固定角色的运行绑定及最小预载引用，不另造第三份身份台账。每次真实派发新增 `dispatch_records`，包含任务卡路径与哈希、实际模型、推理强度、实例 ID 和时间；创建和预载不构成节点批准。

M3 如需 `conditional_support`，辅助实例使用 `gpt-6-luna/max`，任务卡绑定唯一 `solver_instance_id`；`allowed_output_kinds` 仅可为 `local_computation_evidence`、`data_processing_evidence` 或 `code_experiment_evidence`，并显式禁止更改模型路线、写最终结果或汇总结论。

每个子 agent 回传四段：完成项、变更摘要、自检结果、待裁决项。主 agent 依据回传、审查包和检查器裁决；不让任一子 agent 替用户批准。

## 节点契约

| 节点 | 主责与产物 | 必调子 skill | 人工确认 |
|---|---|---|---|
| `M1` 题意与数据边界 | `data` 建立 `problem_statement.md`、`data_overview.yaml`、`task_kpi.yaml`，逐问声明输入、输出、评价指标、数据来源及题面歧义；主 agent 建立官方规则证据和 `literature_request.yaml` | `math-model-selector` | 确认题意、任务划分、指标和官方规则范围 |
| `M2` EDA 与特征 | `data` 产出 `eda_report.md`、`features.yaml`、分割/预处理协议；`verifier` 独立签署 `leakage_audit.yaml`；主 agent 纳入用户回传的 `literature_sources.yaml`；需要 EDA 图时由 `figure` 处理 | `data-science-stack`；成图时 `scipilot-figure-skill` → `modelviz` → `scipilot-figure-skill` | 确认数据理解、特征、文献用途和泄漏审查，肉眼查看图表 |
| `M3` 统一建模与实验 | 单一 `solver` 完成全部小问的 baseline、候选模型、公平对比、调参和泛化验证；输出 `run_manifest.yaml`、模型/结果解释卡；`verifier` 独立签署 `independent_validation.yaml` | `math-model-selector`、`data-science-stack`；成图时同 M2 数据图路由 | 确认统一路线、跨问接口、模型选择和量化结果 |
| `M4` 图表与论文 | `writer` 先提交写作蓝图，按依赖逐章完成正文；用户批准该章后 writer 生成图表提示词，用户转交 `figure` 成图。图件与后续章节并行，摘要最后写，最终统一接图并终审 | `academic-writing`、`mathmodel-latex-skill`；最终成图按图表路由 | 批准写作蓝图、每章正文、实际选定图件、摘要框架、最终全文 |
| `M5` 复现与交付 | 主 agent 核查隔离目录复现、随机种子、相对路径、依赖、论文、引用、匿名、AI 说明、官方格式及交付包；输出 `reproducibility_report.yaml` 和 `delivery_report.yaml` | `mathmodel-latex-skill`；评审 skill 可按题型适配后调用 | 用户核对正式提交包并批准最终版本 |

子 skill 的调用必须真实发生，并登记完成状态、证据路径和当前哈希。modelviz 是任务卡中的规范名称。画图前读取 references/external_skill_adapters.md 和 references/figure_policy.md：数据图由 SciPilot 给出图表决策卡，ModelViz 检索模板、适配真实数据和导出，SciPilot 完成语义、技术、视觉检查；所有非数据图由 tikz-scientific-figures 根据批准图位和模板目录制作。每个图位的 generation_route 和 template_id 必须与 references/figure_template_catalog.yaml 一致。图像交付只登记 SVG、PNG 和可编辑 .tex 源；LaTeX 插入 SVG。画图默认做视觉检查，其他工作默认不做，除非用户要求。

文献由用户检索、下载并委托其文献 agent 汇总。主 agent 先交付逐问覆盖、中文/英文数量建议与可复制检索提示词，再读取用户回传的题录、摘要、方法、数据、适用边界和原文定位。`literature_sources.yaml` 必须覆盖全部小问、登记实际用途并绑定回传摘要的路径与哈希；M2 未通过时保持暂停，不能进入 M3 正式建模。实际引用须对应模型、数据、参数、验证或解释用途；禁止凭空补文献或把固定篇数当作本届官方规则。

## M2/M3 证据门

实例恢复须按 `references/mathorcup_artifact_contract.md` 的 `instance_recoveries` 登记真实用户授权、冻结上下文、旧/新身份和生效节点；原始历史派发保留。检查器按节点核对有效实例及 verifier 签署，不因全局基础登记仍保留旧 ID 而把新旧实例混为一个执行体。仅填写运行时替代 ID 不能代替授权。

节点审查包提交后、用户批准前，可用 `python scripts/check_mathorcup_control.py <project-root> --preflight-node M2` 检查证据。该只读预检不会修改节点状态或批准日志；证据通过但未获批准仍为 `PAUSE`，任一失败仍为 `BLOCK`。禁止为预检把真实节点临时改成 `approved`，禁止用人工说明豁免身份、哈希或独立核验失败。

先按题目类型确定分类、回归、预测、评价或混合任务，再选择指标和分割方式。所有填补、编码、标准化、特征选择、目标编码及调参只在训练折内拟合；时间序列按时间切分，实体相关样本按组隔离。测试集不参与任何预处理拟合或选择。`leakage_audit.yaml` 绑定数据与特征流水线哈希、分割策略、检查项及 `verifier` 实例，`status: PASS` 才能批准 M2。

M3 对每个小问登记 baseline、候选模型、同一数据切分与指标、参数范围、固定种子、实验命令、结果路径与哈希。`run_manifest.yaml` 支持在隔离目录重跑；`independent_validation.yaml` 对跨问字段、单位、数据版本、训练/验证/测试边界、泛化、结果来源与结论逐项签署。任何高分但存在泄漏或不可复现的结果不得冻结。最终建模路线与关键结论由用户确认，AI 只作竞赛规则允许的辅助。

## M4 写作准入与审查

新运行按“写作蓝图批准 → 当前完整章节 → 章节局部审阅 → 用户批准该章 → writer 图表提示词 → 用户转交 figure → 图件选定或返修，同时写下一章 → 摘要框架 → 摘要章 → 全文整合终审”推进。正式成图在相应章节批准后；M2/M3 的探索图和科学证据检查照常进行。论文 agent 决定哪些读者问题需要图、表或文字，图表 agent 负责专业表达，并可提出合并、替换或证据缺口。默认由用户把需求交给图表会话；只有用户明确委托时主控才代为发送。

论文任务卡使用 `plan`、`draft`、`figure_prompt`、`abstract_framework` 和最终 `write`；图表制作使用 `generate`。`draft` 和 `figure_prompt` 都绑定 `chapter_id`，制图还绑定不可变 `revision_id`。章节记录存入 `writing_chapters`，使用 `M4_CHAPTER:<chapter_id>` 只绑定正文与局部质量审查，不绑定图。图件选定版本使用 `M4_FIGURE_SELECTION:<chapter_id>:<revision_id>`。无图章节声明 `visuals_required: false`，不派发提示词或制图。提示词返修形成新版本，不撤销正文批准、不阻塞后续章节。写作蓝图区分最终目录 `chapter_order` 与实际 `writing_order`，后者先完成建模/求解依赖，摘要最后写。最终 `visual_argument_plan.yaml` 汇总各章最新提示词槽位，`figure_registry.yaml` 登记实际选定资产及论文副本。字段、顺序和检查见 `references/mathorcup_chapter_parallel.md`。

`writer` 使用 `templates/mathorcup_paper_argument_blueprint.yaml` 在写正文前提出 `paper_argument_blueprint.yaml`：全文主张、逐问论证路线、章节职责、篇幅容量、证据与图表落位。用户批准 `M4_WRITING_PLAN` 后，还须通过 `paper_material_readiness.yaml` 的逐问素材准入和 `paper_claim_coverage.yaml` 的主张证据覆盖。素材准入逐问检查题目映射、假设、符号定义、数据处理、模型选择、方法与参数、量化结果、独立验证、图表或表格、文献实际用途、结论与边界，并由 `verifier` 签署。任一缺口集中写入一份 `evidence_gap_matrix.yaml`，主 agent 一次性分派到 M2/M3/图表补齐；不靠填充性文字凑篇幅。

写作蓝图必须列出全篇章节职责、章节篇幅容量、图表/表格落位和素材覆盖，并经用户单独批准。蓝图批准后按实际依赖顺序逐章写作，每章只组织已冻结证据；用户批准其完整正文后才能开始下一章。全部非摘要章节批准后，单独提交摘要框架供用户讨论确认；摘要章最后完成并接受相同章节批准。随后统一接图、完成全文衔接和终审。符号首次定义、公式可审计、数字/引用/图表来源绑定、元话语与负向回响清理始终适用。经典模型公式可以引用并解释其本题变量与使用条件，不能省略关键适配、参数和推导依据。论文结构由本题证据与官方格式决定，不强制固定章节比例，不用填充文字补足推荐篇幅。

## M5 交付

代码、数据处理、配置、环境、固定种子、运行命令和输出映射必须足以复现主要数字。`reproducibility_report.yaml` 记录隔离目录复跑命令、退出码、结果哈希及允许的数值容差。`delivery_report.yaml` 将官方格式、论文编译、代码复现、数字/图表/引用一致性、匿名与 AI 使用说明、元话语/负向回响检查、交付文件逐项绑定证据；全部为 `PASS` 才提交 M5 审查包。国赛专属页数和格式检查不得套用到本模式。

只保留最终定稿内容在论文、提交包和第三方报告中。主会话—fork 回流沿用主技能契约：fork 交付可验证的文件与哈希，主会话逐项审核后吸收；未确认经验不进入技能规则。
