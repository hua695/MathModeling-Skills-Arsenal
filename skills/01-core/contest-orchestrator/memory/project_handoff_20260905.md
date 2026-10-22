# Contest Orchestrator + 论文辅助 Skill 项目交接文档

> 生成时间：2026-09-05
> 适用：新会话接手本项目时阅读，包含所有已确认规则、已完成工作、硬约束和下一步。



***

## 一、最终目标

维护一套国赛数学建模竞赛的多 Agent 编排系统，包含：



1. **主控 skill**：`contest-orchestrator`（v4.18）—— 全流程 A–G 主流程 + H0–H9 Harness 半自动模式，负责从题意理解到论文交付的完整编排。

2. **外部审查 skill**：`论文辅助`—— 独立于主 agent 的外部审查助手，主 agent 不知道其存在，审查结果只给用户，由用户判定是否交付。

3. **LaTeX 排版 skill**：`mathmodel-latex-skill`—— 国赛论文模板、编译、格式规范。

核心诉求：**主 agent 每个节点交付的材料都有外部对比基准，确保质量可控；所有硬约束可溯源、不可伪造。**



***

## 二、关键背景

### 2.1 目录与规范元



| 角色           | 路径                                                                                                        | 说明                |
| ------------ | --------------------------------------------------------------------------------------------------------- | ----------------- |
| 规范元（唯一权威）    | `C:\Users\USER\.agents\skills\`                                                                          | 所有修改以此为准          |
| workbuddy 镜像 | `C:\Users\USER\.workbuddy\skills\`                                                                       | 每次修改后必须同步并 commit |
| 论文辅助 skill   | `C:\Users\USER\AppData\Local\Doubao\User Data\Profile 1\.doubao\agent_mode\workspace\.user_skills\论文辅助\` | 不在 git 仓库，需手动同步   |
| 项目工作区        | `C:\Users\USER\Workspace\Project_01_数模空间\`                                                               | 复审报告、审计文件存放处      |

### 2.2 三端同步规则



* **豆包 /codex/workbuddy 三端**，以 `.agents\skills\` 为规范元。

* 每次修改 `.agents\skills\` 后，必须复制到 `.workbuddy\skills\`，并分别在两个 git 仓库 commit。

* 论文辅助 skill 不在 git 中，修改后需手动复制到 workbuddy（`C:\Users\USER\.workbuddy\skills\论文辅助\`）。

* 豆包 `.skills` 托管区持久写入做不通，需用户自行导入。

### 2.3 用户身份



* 数学专业大一升大二学生，备战国赛（CUMCM）和美赛（MCM/ICM），当前聚焦国赛。

* 使用 codex（superpowers 多 agent 调度）和 workbuddy 执行主流程。

* 论文辅助 skill 是用户在豆包端的外部审查工具。



***

## 三、主 Skill 节点定义（v4.18 Harness 模式）



| 节点 | 角色                        | 核心职责                                                                                                      | 模型 / 推理强度              |
| -- | ------------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------- |
| H0 | 初始化                       | 项目结构、harness\_control.yaml 初始化                                                                            | —                      |
| H1 | 题意理解 agent                | 读题面 + 附件，产出 problem\_statement.md、unified\_problem\_package.yaml；**创建 H5/H6/H7/H8 四个子 agent 并预载题面 + 预热包** | gpt-5.6-terra / medium |
| H2 | 主 agent（controller\_only） | 规格冻结，审查包等用户确认                                                                                             | —                      |
| H3 | 主 agent + 外部文献 agent      | 文献阅读，产出 literature\_sources.yaml                                                                          | —                      |
| H4 | 主 agent                   | 建模完整性门，调用 math-model-selector，产出 model\_blueprint.yaml、model\_contract.yaml                               | —                      |
| H5 | 解题 agent                  | **唯一 solver\_instance\_id**，全链路推导、代码、结果、回填 paper\_narrative.yaml key\_result                              | gpt-5.6-sol / high     |
| H6 | 验证 agent                  | 独立验证（实例不同于 H5），global\_interface\_check.yaml 九项检查                                                         | gpt-5.6-sol / high     |
| H7 | 图表 agent                  | 图表决策卡（阶段一暂停等用户确认）→ 四类路由生成 → 登记                                                                            | gpt-5.6-terra / medium |
| H8 | 论文 agent                  | 写作计划（暂停等用户确认）→ 正文→附录→摘要固定顺序 → academic-writing 链路                                                         | gpt-5.6-sol / high     |
| H9 | 主 agent                   | 交付审计，delivery\_all.py --strict                                                                            | —                      |

### 3.1 绑定 skill 契约（检查器强制）



| 节点 | 约束类型           | 必须 / 至少调用                                                          |
| -- | -------------- | ------------------------------------------------------------------ |
| H4 | must\_call     | math-model-selector                                                |
| H5 | at\_least\_one | heuristic-algorithms / data-science-stack / pyomo                  |
| H6 | must\_call     | data-science-stack                                                 |
| H7 | at\_least\_one | scipilot-figure-skill / tech-route-maker / tikz-scientific-figures |
| H8 | must\_call     | academic-writing                                                   |
| H9 | must\_call     | bzd-review-paper                                                   |

### 3.2 图表路由契约（figure\_policy.md，检查器 BLOCK 级）



| 图类型             | 路由                             | generator               | formats            |
| --------------- | ------------------------------ | ----------------------- | ------------------ |
| 数据结果图           | SciPilot → ModelViz → SciPilot | modelviz                | \[svg, png]        |
| 问题分析流程图 / 技术路线图 | tech-route-maker               | tech-route-maker        | \[svg, png]        |
| 机理 / 受力 / 几何示意图 | tikz-scientific-figures        | tikz-scientific-figures | \[svg, png]        |
| Draw.io         | 仅用户显式请求                        | drawio-diagram          | \[svg, png] + 可编辑源 |



* formats 必须**精确等于** `["svg", "png"]`，禁止 pdf/json 混入。

* insertion\_format 必须为 svg。

* 每张图必须有 caption\_claim 和 paper\_location。

* 数据图必须有 decision\_author=scipilot-figure-skill 和 decision\_card。

* pipeline\_audit 三阶段：scipilot\_decision → modelviz\_generation → scipilot\_qa，每阶段 status=passed。



***

## 四、硬性规则（不可随意修改）

### 4.1 页数口径（用户锁定，不能删）



* **正文硬上限 30 页**，规划目标 25–30 页。

* **总 PDF 硬上限 51 页**，推荐区间 35–51 页（推荐区间不是低于 35 页自动失败）。

* 正文定义（湖南赛区口径）：摘要不计入，正文从正文主体起计，包含正文主体、参考文献前的 AI 工具使用声明和参考文献。

* PDF ≤ 20 MB。

* 35–51 页推荐区间、正文建议、附录建议等**不能删除**，这是优秀论文的经验区间。

### 4.2 图片与浮动



* 图片只允许 SVG 与 PNG；LaTeX 正式插入 SVG，PNG 仅预览。

* 浮动用 `[!htbp]`，**禁止&#x20;**`[H]`（锁浮动会推后续文本到新页）。

* 两图间至少一段正文，不许多图连排无文字。

* 图随文走不跨章，章末放 `\FloatBarrier`。

* 图宽 0.6–0.85 `\textwidth`。

* 浮动参数：topnumber=3, bottomnumber=2, totalnumber=4, topfraction=0.85, bottomfraction=0.7, textfraction=0.1, floatpagefraction=0.7。

### 4.3 H5 解题



* **唯一 solver\_instance\_id**，覆盖全部小问，禁止多个并行。

* validation\_contract 必须 status=verified，禁止 draft。

* 全链路推导：从问题到最终模型每步有话语解释，禁止跳步黑箱，禁止 "易知 / 显然 / 经过复杂推导"。

* 推导链落盘，供 H8 取用。

* 随机算法固定 seed。

### 4.4 H6 验证



* agent\_instance\_id 必须不同于 H5（独立验证原则）。

* global\_interface\_check.yaml 九项检查：shared\_symbols、units、data\_versions、upstream\_downstream\_fields、time\_scales、parameters、cross\_question\_constraints、conclusions、provenance。

* 必须有 task\_card\_sha256 绑定 H6 任务卡。

* per\_subproblem 逐问接口明细覆盖全部小问。

* 九项有 false 则 status 不能为 PASS。

### 4.5 H7 图表



* 阶段一：SciPilot 生成决策卡和清单，**暂停等用户确认**后才生成。

* 阶段二：用户确认后 ModelViz 执行生成，再经 SciPilot 三重检查。

### 4.6 H8 论文



* 素材准入（paper\_material\_readiness.yaml=PASS）和主张覆盖（paper\_claim\_coverage.yaml=PASS）必须齐全。

* **写作计划门禁**：writing\_started=true 时必须有 writing\_plan（文件存在 + 哈希匹配）、plan\_review\_packet（存在）、plan\_approved=true。

* **固定写作顺序**：先正文各章 → 再附录 → 最后写摘要。摘要必须等正文和附录定稿后撰写。

* **摘要禁公式**；每问必须有方法名 + 创新 + 量化结果；7 段结构完整。

* 主张覆盖表禁止重复 claim\_id。

* 写哪章读哪章：通过 paper\_material\_readiness.yaml 章节素材索引逐章取用，禁止一次性读所有原始数据（任务卡 inputs 原始数据文件 >3 个即 BLOCK）。

* 建模与求解章节必须全链路推导；非建模章节（摘要 / 问题分析 / 模型检验 / 模型评价 / 结论）禁公式堆砌。

### 4.7 H9 交付



* delivery\_report 防伪造：command 必须为真实 python 执行（禁止 echo），project\_root 匹配当前项目，input\_sha256 为 64 位 hex，artifacts 有 path+sha256 且文件存在。

* 调用 bzd-review-paper。

### 4.8 论文辅助 skill 规则



* **只读审查，不动手改主 skill**。

* 审查结果只给用户，由用户判定是否交付，**不直接给主 agent**。

* 主 agent 不知道论文辅助 skill 的存在。

* 三个角色：独立审查助手（默认）、H3 文献阅读子 agent、节点交接提示词生成器。

* 用户说 "通过 Hx" 时生成下一节点提示词，用户复制给主 agent。



***

## 五、已完成的工作

### 5.1 codex 复审 21 项修复（四批全部完成，双仓库 commit）



| 批次  | 项数 | 核心内容                                                                                                                                                                                        | commit（.agents / workbuddy） |
| --- | -- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| 第一批 | 6  | H-01 移除 BOM；H-04 figure formats 精确等于；D-02 嵌套推荐区间兼容；S-01 TikZ 统一 SVG+PNG；S-02 tech-route 默认加 PNG；S-04 外部适配器拆 4 行互斥路由                                                                         | b01d0a8 / 2e8f980           |
| 第二批 | 8  | H-07 H6 强制 verified；H-08 spawn 去重 + agent\_ids 来源分离 + 预热包校验；H-09 dispatch 实例注册表；H-12 H1 原始题面输入；D-01 文档路径补全；S-03 ModelViz 别名；S-05 data-science 输入改 unified\_problem\_package；S-06 移除空 notice | d2abb52 / 8e510dc           |
| 第三批 | 4  | H-02 H9 交付防伪造；H-05 H8 写作计划门禁；H-10 H6 接口报告 task\_card\_sha256+per\_subproblem；H-13 缺口矩阵 gap\_id 唯一                                                                                           | 0b2cac6 / a850a7e           |
| 第四批 | 3  | H-03 H7 图表 pipeline\_audit+decision\_author+caption\_claim；H-06 --through 前置节点 not\_started 检查；H-11 主张重复 claim\_id 拒绝                                                                       | 87260b6 / ce60527           |

### 5.2 论文辅助 skill 同步修改



* 修正节点编号偏移（H5 = 解题、H6 = 验证、H7 = 图表，之前错位一位）。

* 同步第三 / 四批新增强约束到 harness\_node\_focus.yaml。

* 核心审查节点扩展为 H4/H5/H6/H7/H8/H9。

* 新增**节点交接提示词生成器**（角色三）：用户说 "通过 Hx" 时生成下一节点完整提示词，模板在 `templates/node_handoff_prompts.yaml`（H0–H8 共 9 节点）。

* 同步到 workbuddy 并 commit。

### 5.3 mathmodel-latex-skill 吸收 ModelingPaperKit



* 新增 `templates/cumcm/cumcm-extras.sty`（可选加载，默认在 main-cumcmthesis.tex 中启用）：


  * 数学符号快捷命令：`\mat \vb \trans \R \N \Z \E \Var \Cov \argmin \argmax \upcite`

  * 13 种中文定理环境：definition/theorem/lemma/corollary/assumption/conjecture/axiom/principle/problem/example/solution/remark/property

  * 算法伪代码环境（algorithm+algpseudocode，中文关键字汉化）

  * cleveref 中文智能引用（`\cref{fig:1}`→"图 1"）

  * 表格增强：`\topline\midline\bottomline`、Y/J 列类型、longtable

  * 改造版 `\figplot`（用 `[!htbp]` 而非 `[H]`，自动搜索路径，文件不存在时占位框）

  * 脱敏占位 `\email \phone`→`[已脱敏]`

  * 代码列表 listings、浮动参数与 figure\_policy 一致、placeins（`\FloatBarrier`）

* 所有可能冲突的命令用 `\providecommand`（已定义则不覆盖）。

* SKILL.md 新增「CUMCM Extras Macros」小节，STYLE\_GUIDE.md 新增第 9 节详细用法。

* H8 预热包（h8\_writer\_warmup.md）明确列出 cumcm-extras 快捷命令并要求 "写作时优先使用"。

* 编译验证通过（5 页 PDF 无错误）。

* 双仓库 commit：4a05b27 / 97bc240（初版），6237e44 / 24c48ac（SKILL.md 补文档），8b16c80 /d74e179（providecommand + 预热包）。

### 5.4 防 "建模手写" 机制加强



* H8 预热包角色定位改为按章节区分公式密度：建模章全链路推导，非建模章禁公式堆砌。

* H8 节点定义补充 "建模与求解章节必须全链路推导"。

* `check_math_behavior.py` 新增**非建模章节公式密度检查**：摘要公式 > 0 即警告，其他非建模章节 >2 个 / 500 字即警告。

* `check_harness_control.py` 新增 **H8 任务卡 inputs 约束**：原始数据文件（.csv/.xlsx/.json 等）>3 个即 BLOCK（写哪章读哪章验证）。

* H8 自查清单建模项改为 "全链路推导从问题到最终模型每步有依据？无跳步无黑箱？"

### 5.5 H5 全链路推导从源头遏制黑箱



* H5 预热包新增「全链路推导铁律」6 条：禁止跳步、禁止纯公式罗列、推导链结构、话语解释要求、关键变换必解释、推导产物落盘。

* H5 禁止越界新增 "禁止黑箱推导"。

* H5 节点定义从 "中间推导" 改为 "全链路推导（每步有话语解释，禁止跳步黑箱，禁止易知 / 显然 / 经过复杂推导）"。

* `check_math_behavior.py` 新增 MDS-M6「黑箱推导」词汇检查：扫描易知 / 易得 / 显然 / 不难看出 / 经过复杂推导 / 直接得到 / 无需赘述 / 推导略 / 过程省略。



***

## 六、重要决策及其理由



| 决策                                                                     | 理由                                                      |
| ---------------------------------------------------------------------- | ------------------------------------------------------- |
| 不替换 cumcmthesis.cls，新增 cumcm-extras.sty                                | 现有 cls 是刻意做的轻量兼容版（原版有许可证风险），新增宏包零风险、可选加载                |
| cumcm-extras 用 \providecommand 而非 \newcommand                          | 防止与其他宏包命令冲突，已定义则不覆盖                                     |
| \figplot 用 \[!htbp] 而非 ModelingPaperKit 原版的 \[H]                       | \[H] 锁浮动与 figure\_policy"禁止 \[H]" 直接冲突，会导致图片浮动问题        |
| 不吸收 personqianduixue/CUMCMThesis/mmstyles 三个老项目                        | 均为 2021 年前停更项目，ModelingPaperKit（2026 年活跃）已覆盖其所有有价值点且更完善 |
| 摘要最后写                                                                  | 先写摘要必然空泛或公式化，等正文定稿后概括才能写清方法 + 创新 + 结果                   |
| H5 唯一 solver\_instance\_id                                             | 多实例并行会导致跨问接口不一致、符号冲突                                    |
| H6 实例必须不同于 H5                                                          | 独立验证原则，自己验证自己没有意义                                       |
| 论文辅助 skill 对主 agent 不可见                                                | 确保主 agent 的判断有外部对比基准，用户才能评估主 agent 完成质量                 |
| H1 创建时即创建 H5/H6/H7/H8 子 agent 并预载题面                                    | 后创建的子 agent 重读上下文浪费 tokens；创建即预载题面 + 预热包，到节点直接执行        |
| paper\_narrative.yaml 只收 method/innovation/problem\_solved/key\_result | 防止论文 agent 被大量原始数据淹没变成 "建模手写"；完整推导在单独的推导文件里             |



***

## 七、被否定的方案



| 方案                                          | 否定原因                                                     |
| ------------------------------------------- | -------------------------------------------------------- |
| 用主 agent 直接写论文                              | 主 agent 接收全量上下文，容易变成建模手写；改用独立 H8 论文 agent + 预热包 + 写哪章读哪章 |
| 论文 agent 一次性读取所有素材                          | 被大量数据淹没，公式堆砌；改为逐章取用                                      |
| 摘要先写                                        | 必然空泛；改为正文→附录→摘要固定顺序                                      |
| H6 验证 agent 头（独立的验证管理层）                     | 多余，H6 直接做验证即可                                            |
| 替换 cumcmthesis.cls 为 ModelingPaperKit 的完整引擎 | 风险大，现有轻量版够用                                              |
| 吸收三个老 GitHub 项目                             | 价值低，已被 ModelingPaperKit 覆盖                               |
| 低配置模型预热后手动切换                                | 不必要，不省那些 tokens                                          |
| H-06 完整状态转移表                                | 与测试 fixture 冲突大，暂缓                                       |
| H-11 LaTeX 反向扫描主张                           | 解析复杂度高，暂缓                                                |



***

## 八、当前进度



* ✅ contest-orchestrator v4.18 核心可用，245 项测试全部通过。

* ✅ codex 复审 21 项问题全部修复，双仓库 commit。

* ✅ 论文辅助 skill 同步完成（节点修正 + 硬约束 + 交接提示词），同步到 workbuddy。

* ✅ mathmodel-latex-skill 吸收 ModelingPaperKit（cumcm-extras.sty），编译验证通过。

* ✅ H8 防 "建模手写" 机制：非建模章节公式密度检查 + 任务卡 inputs 约束 + 预热包按章节区分公式密度。

* ✅ H5 全链路推导：预热包铁律 + 节点定义 + 黑箱词汇检查。

* ✅ 所有修改双仓库 commit（.agents 和 workbuddy）。



***

## 九、尚未完成的任务



1. **暂缓项**（已知但未做，有明确原因）：

* H-06 完整状态转移表（与测试 fixture 冲突大）

* H-11 LaTeX 反向扫描主张重复（解析复杂度高）

* 豆包 .skills 托管区持久写入（做不通，需用户自行导入论文辅助 skill）

1. **待验证项**：

* 实际跑一次完整 harness 流程，确认 H1 创建子 agent、H5 全链路推导、H7 阶段一暂停、H8 写作计划暂停 + 固定写作顺序等所有硬约束在真实执行中生效。

* cumcm-extras.sty 在真实论文（含大量公式、算法、表格）中的编译验证。

1. **美赛适配**：当前所有修改聚焦国赛，美赛模板（mcm-icm）未同步 cumcm-extras 和相关硬约束。用户明确 "美赛先不管"。



***

## 十、不能随意修改的内容



1. **页数口径**：正文 30 页硬上限、总 PDF 51 页硬上限、35–51 页推荐区间 —— 用户明确锁定，不能删。

2. **图片格式契约**：formats 精确等于 \[svg, png]，禁止 PDF—— 检查器 BLOCK 级。

3. **H5 唯一 solver\_instance\_id**—— 多实例会破坏跨问接口。

4. **H6 独立验证（实例不同于 H5）**—— 独立验证原则。

5. **H8 固定写作顺序（正文→附录→摘要）**—— 摘要最后写是防摘要公式堆砌的核心机制。

6. **论文辅助 skill 对主 agent 不可见**—— 外部审查的存在意义。

7. **cumcmthesis.cls 不替换**—— 轻量兼容版刻意保留。

8. **\figplot 用 \[!htbp] 不用 \[H]**—— 与 figure\_policy 一致。

9. **三端同步以 .agents\skills 为规范元**——workbuddy 是镜像，不能反过来改 workbuddy 不同步 .agents。



***

## 十一、新会话接下来应该先做什么



1. **读取本文件**，确认对项目结构、硬约束、已完成工作的理解。

2. **读取关键文件**建立真实认知（禁止凭记忆操作）：

* `contest-orchestrator/SKILL.md`

* `contest-orchestrator/references/modes/full-contest-harness.md`

* `contest-orchestrator/scripts/check_harness_control.py`（检查器是硬约束的权威来源）

* `contest-orchestrator/references/figure_policy.md`

* `论文辅助/SKILL.md`

* `mathmodel-latex-skill/templates/cumcm/cumcm-extras.sty`

1. **如果用户提出新修改**：

* 先确认修改范围，只改被点名的部分。

* 修改 `.agents\skills\` 后，**必须**同步到 `.workbuddy\skills\` 并分别 commit。

* 修改检查器后必须跑 `python -m unittest tests.test_harness_control tests.test_harness_hardening -q`（45 项）确认不破坏现有测试。

* 修改 LaTeX 模板后必须用 xelatex 编译验证。

1. **如果用户要求审查主 agent 产出**：切换到论文辅助 skill 的角色一（独立审查），只读不改，结果只给用户。

2. **如果用户说 "通过 Hx"**：切换到论文辅助 skill 的角色三（节点交接提示词生成器），读取 `templates/node_handoff_prompts.yaml` 生成下一节点提示词。



***

## 十二、常用命令速查



```
\# 测试（contest-orchestrator 目录下）

python -m unittest tests.test\_harness\_control tests.test\_harness\_hardening -q

python -m unittest discover -s tests -q

\# 健康检查

python scripts/skill\_health\_check.py .

\# LaTeX 编译（模板目录下）

xelatex -interaction=nonstopmode main-cumcmthesis.tex

\# 数学行为检查（含非建模章节公式密度+黑箱词汇）

python scripts/check\_math\_behavior.py \<paper.tex或.md>

\# 交付审计

python scripts/delivery\_all.py <项目根> --strict
```



***

*本文档为项目交接用，所有规则以实际文件内容为准。修改文件前必须先 Read 确认当前状态，禁止凭记忆操作。*