---
name: academic-writing
description: |
  数学建模论文的学术表达与结构质量控制主入口。调用本地化论文审阅规则，
  只允许修改普通正文，并在交付前保护公式、引用、数字、三线表、图表编号和模型逻辑。
  不负责模型建立、数据计算或竞赛交付门禁。
allowed-tools:
  - Read
  - Write
  - Edit
  - AskUserQuestion
metadata:
  mode: local-adapter
  upstream: youngze0016/thesis-polish-agent
  guard: scripts/mathmodel_patch_guard.py
---

# 数学建模论文写作适配层

本技能是本地维护的稳定入口。上游 `thesis-polish-agent` 只作为 `modules/` 下的规则和审阅资源，不能直接接管数学建模论文，也不能绕过本地差异门禁。

## Contest-Orchestrator Adapter

本技能在主控中的固定位置是“论证中心编辑”：接收当前任务卡、论文快照、冻结的模型/结果/引用证据，输出普通正文补丁和可回流节点包。`contest-orchestrator` 负责范围、模型、数字、图表、引用和交付裁决；本技能不得越权修改这些内容。

- 节点包包含 `status`、`active_mode`、`task_card`、`artifacts`、`evidence`、`checks`、`blockers`、`next_node`，所有路径均为项目工作区相对路径。
- 每个新符号必须在正文首用处给出含义、单位/量纲、取值域和变量类型；缺少定义时报告 `FAIL`，不通过补写猜测修复。
- 交付文本只保留面向读者的最终论证，不得出现元话语、内部交流、评审过程、修改轮次、agent、提示词、调试或旧内容等负回响。
- 非绘图论文任务的视觉检查默认关闭；文本层、公式、引用、数字和结构检查照常执行，只有用户明确要求时才启用视觉检查。
- 国赛 2026 论文：正文不设目录；正文从正文主体起计（摘要不计入），包含正文主体、参考文献前的 AI 工具使用声明和参考文献，最多 30 页，附录不计入；提交论文文件总页数（含摘要、正文、参考文献和附录）硬上限 51 页，推荐区间 35–51 页；论文提交为含文本层的非图片 PDF，文件不超过 20 MB。
- AI 声明只写实际使用范围的必要信息，但必须真实；不得隐瞒已使用工具或填写未使用。使用 AI 时，支撑材料提供 `AI工具使用详情.pdf`，说明工具版本、用途环节、关键交互摘要、采纳、人工修改和核验，突出参赛队主导核心建模与分析；不要求把 AI 工具列入参考文献。

## 职责边界

- `contest-orchestrator`：题目解析、模型建立、代码求解、结果、图表、引用和正式交付。
- `academic-writing`：章节结构、学术表达、术语统一、审阅报告和 LaTeX 编译建议。
- `humanizer-zh`：最后的语言去痕，只处理普通正文。
- `mathmodel_patch_guard.py`：检查润色前后的数学内容是否发生未授权变化。

## 论证中心编辑

当用户要求“论证中心编辑”“按主张—证据—结论审阅”“防御性写作清理”或等价处理时，必须先读取 [claim-centered-editing](modules/claim-centered-editing/MODULE.md)。该模块只负责普通正文的主张组织、证据绑定和结论范围；不建立模型、不重算结果、不改变引用和图表。

## 强制输入

执行修改前必须有：

1. 论文项目根目录和明确的目标章节；
2. 比赛类型（国赛 CUMCM / 美赛 MCM-ICM，未指定默认国赛）；
3. 已冻结的模型、代码、结果和图表；
4. 当前 `.tex`、`.bib` 及其来源文件；
5. 修改前快照目录，或由本技能先创建隔离快照。

缺少模型结果来源、引用数据库或修改前快照时，只能输出审阅意见，不得直接改写文件。

## 允许与禁止

允许修改：普通正文中的句式、段落衔接、冗余表达、术语一致性和章节组织建议。

默认禁止修改：

- 公式、公式编号、公式标签、变量、单位和约束；
- `\cite`、`\ref`、`\label`、参考文献数据库及引用顺序；
- 数字、误差、成本、厚度、百分比和结果值；
- `table`、`tabular`、三线表命令、图表编号和图片路径；
- 代码、数据、模型参数、目标函数和算法实现。

如确实需要改动上述内容，必须退出普通润色模式，交回 `contest-orchestrator` 的模型/结果一致性流程，并由用户明确授权。

## 固定执行流程

1. 读取 [references/mathmodel_rules.md](references/mathmodel_rules.md) 和 [references/upstream_map.md](references/upstream_map.md)。
2. 国赛任务额外读取 [references/cumcm_content_redlines.md](references/cumcm_content_redlines.md)，编辑前先扫描目标章节，命中红线时输出【国赛内容红线：xxx】标记，不自行修复内容层问题；目标章节包含摘要时，额外读取 [references/cumcm_abstract_check.md](references/cumcm_abstract_check.md) 执行摘要专项检查，并读取 [references/abstract-writing.md](references/abstract-writing.md) 的实例写法（含信贷/ RGV 等非机理题型示范）；**B 题（优化决策类）任务必须读取其中的"B 题专属摘要模板"章节**，包含 6 大核心要素、2023B 标杆实例、AI 生成提示词和自查清单；**目标章节包含"模型建立与求解"（建模求解章节）时，必须读取 [references/b_chapter_templates/README.md](references/b_chapter_templates/README.md)（模板库入口，含形态判定表），再按问题编号和形态读取对应模板文件（如 problem1_modeling.md、problem2/form_A_extension.md 等），B 题任务必须使用该模板库的骨架结构和必选项清单**；**所有论文写作任务必须读取 [references/anti-defensive-writing.md](references/anti-defensive-writing.md)（防防御性写作指南，数学建模竞赛版），核心原则：论文是学术发布会不是项目总结，只围绕优势组织叙事，不写工作汇报，禁用自我削弱表达，每个结果必须有论证职责，结论只强化记忆点，不给评委递刀子**；目标章节含图表时，额外读取 [references/figure-placement-rules.md](references/figure-placement-rules.md) 执行图表位置纪律扫描（连续浮动体、图前后缺文字、[H] 无 float 包、图先于引用），命中输出【图表位置：xxx】标记，不自动改位置参数或插入文字。
3. 需要论证中心编辑时，再读取 [modules/claim-centered-editing/MODULE.md](modules/claim-centered-editing/MODULE.md)。
4. 只读运行审阅模块，选择 `review-chapter`、`style-check`、`terminology`、`consistency` 等必要角色；不自动并行调用全部子模块。
5. 在隔离副本中生成正文修改，保留原项目不变。
6. 运行：

   ```text
   python scripts/mathmodel_patch_guard.py <before_dir> <after_dir> --strict --out patch_guard.json
   ```

7. 只有保护器 PASS，才允许将普通正文补丁合并回论文项目；随后运行 LaTeX 编译、引用检查和 `contest-orchestrator` 的交付门禁。
8. 写作风格客观检查：读取 [references/style_guide.md](references/style_guide.md)（写作风格规范，含句长变化、段落长度变化、避免列表堆砌、自然过渡、避免套话、跨章节差异化），并运行 `python scripts/style_check.py <paper.tex> --out style_report.json` 进行六项客观指标检查（句长均匀度、段落长度均匀度、列表堆砌、机械过渡词、跨章节短语重复、套话密度），WARN 项需要针对性修改。
9. 最后按需执行自然化去痕：读取 [modules/humanizer/MODULE.md](modules/humanizer/MODULE.md)（humanizer-zh 能力本地模块，作为本技能固定后编辑器），并再次运行保护器。

## 写作素材（按需加载）

- 常用表达与句式库（正文写作/润色参考）：[references/common-phrases.md](references/common-phrases.md)
- 题型策略（按题面类型选表达与结构策略）：[references/problem-type-strategies.md](references/problem-type-strategies.md)
- 去 AI 味完整清单（8 类痕迹 + 数模禁用词/结果铁律，与 modules/deai 互补）：[references/de-ai-writing.md](references/de-ai-writing.md)
- 摘要写作实例（3 个完整示范，覆盖机理/数据/优化三类）：[references/abstract-writing.md](references/abstract-writing.md)
- 图表位置纪律（防浮动/防连图/防错位，写作阶段与编译后扫描规则）：[references/figure-placement-rules.md](references/figure-placement-rules.md)
- 写作风格规范（降低AI生成感：句长变化、段落长度变化、避免列表堆砌、自然过渡、避免套话）：[references/style_guide.md](references/style_guide.md)
- **B题建模求解章节模板库**（五层结构：题型判定+骨架+必选项+写作要点+特色空间，覆盖问题一至四共8种形态，含反机械硬约束和自查清单）：[references/b_chapter_templates/README.md](references/b_chapter_templates/README.md)，写建模求解章节时必须读取并使用
- **防防御性写作指南**（数学建模竞赛版，核心原则：论文是学术发布会不是项目总结，只围绕优势组织叙事，不写工作汇报，禁用自我削弱表达，每个结果必须有论证职责，结论只强化记忆点，不给评委递刀子）：[references/anti-defensive-writing.md](references/anti-defensive-writing.md)，所有论文写作任务必须读取并使用

## 上游更新

上游版本由 [UPSTREAM_LOCK.yaml](UPSTREAM_LOCK.yaml) 锁定。禁止自动拉取上游更新；升级必须在隔离目录中进行，并通过技能结构检查、保护器负面测试和至少一次数学建模论文 replay。

## 交付物

- 修改前后差异报告；
- `patch_guard.json`；
- 学术表达问题清单；
- 编译和一致性检查结果。

没有差异报告或保护器结果时，不得声称论文已完成润色。
