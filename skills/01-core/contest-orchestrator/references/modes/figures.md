# 图表模式

只处理视觉论证计划、图表计划、数据映射、生成脚本、来源登记和导出。

- H7 先生成 `visual_argument_plan.yaml`：从读者问题、模型结构和结果证据出发，逐小问完成六类视觉审计，并登记 `required/recommended/table_justified/text_sufficient/not_applicable` 的 disposition、证据和读者收获。复杂度硬义务由上游模型总结卡推断，不能用自由理由降低。
- 每个有图的视觉槽位必须登记 `figure_intent`：读者问题、解释关系、必须出现/禁止出现的内容、正文落位、图前/图后论证功能、唯一生成路由和模板状态。H5→H6→H7 的 `visual_evidence_packet.yaml` 只提供轻量、已核验的信息单元，不承载这份设计契约。
- H7 必须先读取经 H6 核验的 `visual_evidence_packet.yaml`。每个真实视觉槽位登记 `information_unit_ids` 和 `density_profile`；标准图至少绑定两个独立信息单元，单一信息单元只能使用 `compact` 并给出理由。生成后的 registry 同时登记计划单元和实际实现单元，二者必须完全一致。
- 视觉论证计划必须单独提交 `.contest/reviews/H7_visual_plan_review_packet.yaml`，并在 `.contest/approval_log.yaml` 写入 `gate: H7_VISUAL_PLAN` 的用户批准及当前计划哈希；该批准缺失时不得进入图型选择、模板检索、生成和登记。
- 阶段一批准期间 H7 保持 `draft`；完成生成、质量检查和登记后才转为 `review_pending`，由普通 H7 审查包承载最终图表验收。
- 通过视觉审计后，数据图再生成 SciPilot 决策卡。决策卡先于模板检索和批量生成，明确每张图服务的正文主张、数据源、数据结构、推荐图型、备选图型、排除图型、坐标、单位、图注和文件名；必要时记录图内画布比例，但不决定论文页面布局。
- H7 图表 agent 负责完整视觉论证计划和非数据图的图型/路由判定；SciPilot 只为数据结果图生成决策卡并执行数据图语义、技术、视觉检查，不替代 H7 规划流程图、技术路线图或示意图。
- 图表生成完成后，由论文排版层为每张登记图补齐唯一 `layout_mode`；页面布局只从 `single`、`side_by_side`、`wrap_short`、`tall_constrained` 四种入口选择，并与 `figure_policy.md` 保持一致。
- 数据结果图严格执行 `SciPilot discovery → ModelViz generation → SciPilot QA → contest-orchestrator registry`；问题分析流程图和技术路线图使用 `tech-route-maker`；原理、机制、受力和几何示意图使用 `tikz-scientific-figures`；Draw.io 仅在用户明确要求时使用。登记规则以 `references/figure_policy.md` 为准。
- 最终 registry 中每张图必须登记 `visual_slot_ids`，只能闭合到 `visual_argument_plan.yaml` 的已批准槽位；计划外图表不得进入论文。
- 图片输出只保留 SVG 和 PNG，LaTeX 正式插入 SVG；编辑源文件单独保留，图片 PDF 不生成、不登记、不交付。
- 绘图默认完成技术检查、渲染复核和视觉质检；用户肉眼确认作为最终补充。
- 图表确认前不得冻结论文素材；确认后才进入论文生成。
