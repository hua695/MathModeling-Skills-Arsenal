# 技能目录与协议

安装、当前流程与验证范围以[首页](../README.md)为准。本页提供技能导航；可选工具不等于主控默认路由。

## 技能目录

### 01 主控流程

| 技能 | 作用 |
|---|---|
| [contest-orchestrator](../skills/01-core/contest-orchestrator/SKILL.md) | 竞赛唯一主控流程。题目解析、选题与模型规划、baseline、求解、图表、论文成稿、评审、交付门禁与 replay 复盘。支持 AUTO / COLLAB / LOCK 三级自主度，按 A 到 G 阶段推进并逐段验收 |

### 02 建模与求解

| 技能 | 作用 |
|---|---|
| [math-model-selector](../skills/02-modeling/math-model-selector/SKILL.md) | 题型到模型的路由器。按题型主类、数据规模、约束特征推荐模型框架与 Python 库，输出子问题与模型的对应表 |
| [data-science-stack](../skills/02-modeling/data-science-stack/SKILL.md) | C 类数据题全链路。EDA、预处理与特征工程、统计推断、机器学习建模、时间序列预测、模型评估 |
| [heuristic-algorithms](../skills/02-modeling/heuristic-algorithms/SKILL.md) | 启发式与数值算法库。遗传算法、模拟退火、粒子群、蒙特卡洛、常微分方程数值解 |
| [pyomo](../skills/02-modeling/pyomo/SKILL.md) | Python 优化建模框架封装。线性与整数规划、约束建模、求解器调用 |

### 03 论文写作

| 技能 | 作用 |
|---|---|
| [academic-writing](../skills/03-writing/academic-writing/SKILL.md) | 学术表达与结构质量主入口。调用本地化审阅规则，限定只改普通正文，保护公式、引用、数字、三线表与图表引用 |
| [mathmodel-latex-skill](../skills/03-writing/mathmodel-latex-skill/SKILL.md) | 竞赛风格 LaTeX 论文工程。模板生成、改编、编译与预检，覆盖 CUMCM 与 COMAP MCM/ICM 格式要求 |
| [bzd-review-paper](../skills/03-writing/bzd-review-paper/SKILL.md) | 独立构建百分制评分细则，审计资格与格式，按权重上限打分并给出中文评委反馈 |
| [论文辅助](../skills/03-writing/论文辅助/SKILL.md) | 论文 G0 到 G6 节点只读审查。检查符号完整性、元话语、负向回声、模型证据，输出结构化修改清单 |

### 04 图表可视化

| 技能 | 作用 |
|---|---|
| [scipilot-figure-skill](../skills/04-figures/scipilot-figure-skill/SKILL.md) | 可视化顾问定位。先做数据剖析再定图型，按出版级样式出图 |
| [modelviz](../skills/04-figures/modelviz/SKILL.md) | 从自有 CSV/XLSX 数据加一句自然语言绘图需求，产出论文级科学图 |
| [figure-generation](../skills/04-figures/figure-generation/SKILL.md) | matplotlib 与 seaborn 出版级配图。查询扩展、代码生成执行、视觉反馈三段流水线 |
| [tikz-scientific-figures](../skills/04-figures/tikz-scientific-figures/SKILL.md) | TikZ 与 PGFPlots 排版级插图。输出 SVG 与 PNG，适合需要矢量精确控制的示意图 |
| [fireworks-tech-graph](../skills/04-figures/fireworks-tech-graph/SKILL.md) | 技术类图示。软件架构、数据流、流程图、时序图、C4 评审、云部署与事件流 |
| [tech-route-maker](../skills/04-figures/tech-route-maker/SKILL.md) | 技术路线图。历史独立路线图工具；主控现统一使用 tikz-scientific-figures |
| [drawio-diagram](../skills/04-figures/drawio-diagram/SKILL.md) | 生成标准 `.drawio` 格式图表，可在 diagrams.net 继续编辑 |

### 05 通用工具

| 技能 | 作用 |
|---|---|
| [web-access](../skills/05-toolkit/web-access/SKILL.md) | 联网操作统一入口。搜索、网页抓取、需登录的页面访问与网络交互 |
| [markitdown-skill](../skills/05-toolkit/markitdown-skill/SKILL.md) | 文档转 Markdown。PDF、Word、PowerPoint、Excel、图片 OCR、音频转写、HTML 与网页链接 |
| [browser-cdp](../skills/05-toolkit/browser-cdp/SKILL.md) | 通过 Chrome DevTools 协议复用已登录会话控制浏览器 |
| [humanizer-zh](../skills/05-toolkit/humanizer-zh/SKILL.md) | 中文去 AI 味。检测并清除模板化表达 |

### 06 元技能

| 技能 | 作用 |
|---|---|
| [darwin-skill](../skills/06-meta/darwin-skill/SKILL.md) | 技能自优化。技能质量评分准则评估 SKILL.md，爬山式迭代改进 |
| `self-improvement` | 从失败、纠错、用户指正中沉淀可复用经验 |
| [skill-audit-cleanup](../skills/06-meta/skill-audit-cleanup/SKILL.md) | 技能库全量审计。按真实使用记录分高频必留、低频暂存、无用归档，产出报告与归档脚本 |

### 99 创意写作

十二个网文创作技能，与数学建模无关，附在本仓库便于一处取用。

[story](../skills/99-creative-writing/story/SKILL.md) 为总入口，路由到 [story-long-write](../skills/99-creative-writing/story-long-write/SKILL.md)、[story-short-write](../skills/99-creative-writing/story-short-write/SKILL.md)、[story-long-analyze](../skills/99-creative-writing/story-long-analyze/SKILL.md)、[story-short-analyze](../skills/99-creative-writing/story-short-analyze/SKILL.md)、[story-long-scan](../skills/99-creative-writing/story-long-scan/SKILL.md)、[story-short-scan](../skills/99-creative-writing/story-short-scan/SKILL.md)、[story-review](../skills/99-creative-writing/story-review/SKILL.md)、[story-deslop](../skills/99-creative-writing/story-deslop/SKILL.md)、[story-cover](../skills/99-creative-writing/story-cover/SKILL.md)、[story-import](../skills/99-creative-writing/story-import/SKILL.md)、[story-setup](../skills/99-creative-writing/story-setup/SKILL.md)。

不需要可直接删除该目录，不影响其余技能。

---

## 第三方技能与协议

仓库整体采用 Apache-2.0。以下技能沿用原作者协议，优先级高于仓库整体协议：

| 技能 | 协议 | 版权 |
|---|---|---|
| `humanizer-zh` | MIT | 歸藏 |
| `fireworks-tech-graph` | MIT | fireworks-tech-graph contributors |
| `tech-route-maker` | MIT | tech-route-maker contributors |

各技能目录内保留原始 `LICENSE` 文件，分发时请一并保留。

---


仓库整体协议见 [LICENSE](../LICENSE)，分发时保留各技能原始许可证。
