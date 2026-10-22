# 数模军械库 · MathModeling Skills Arsenal

面向数学建模竞赛的 AI Agent 技能集。三十五个技能，串起读题、建模求解、数据可视化、论文写作、终稿评审整条链路。

关键词：数学建模、数模竞赛、全国大学生数学建模竞赛、CUMCM、国赛、美赛、MCM/ICM、华数杯、研赛、论文评审、LaTeX 论文模板、科研绘图、AI Agent Skills

已适配 Claude Code / Codex / WorkBuddy / OpenCode 等支持 `SKILL.md` 约定的宿主。

---

## 快速开始

技能宿主按 `skills/<技能名>/SKILL.md` 的单层结构加载，本仓库用二级分类目录组织。安装时把技能目录拉平即可。

```bash
git clone https://github.com/hua695/MathModeling-Skills-Arsenal.git
cd MathModeling-Skills-Arsenal

# WorkBuddy
cp -r skills/*/* ~/.workbuddy/skills/

# Claude Code
cp -r skills/*/* ~/.claude/skills/

# Codex
cp -r skills/*/* ~/.codex/skills/
```

只装数模相关的六类，跳过创意写作：

```bash
for d in 01-core 02-modeling 03-writing 04-figures 05-toolkit 06-meta; do
  cp -r skills/$d/* ~/.workbuddy/skills/
done
```

装完重启宿主，`contest-orchestrator` 的主控流程即可接管全流程。

---

## 技能目录

### 01 主控流程

| 技能 | 作用 |
|---|---|
| `contest-orchestrator` | 竞赛唯一主控流程。题目解析、选题与模型规划、baseline、求解、图表、论文成稿、评审、交付门禁与 replay 复盘。支持 AUTO / COLLAB / LOCK 三级自主度，按 A 到 G 阶段推进并逐段验收 |

### 02 建模与求解

| 技能 | 作用 |
|---|---|
| `math-model-selector` | 题型到模型的路由器。按题型主类、数据规模、约束特征推荐模型框架与 Python 库，输出子问题与模型的对应表 |
| `data-science-stack` | C 类数据题全链路。EDA、预处理与特征工程、统计推断、机器学习建模、时间序列预测、模型评估 |
| `heuristic-algorithms` | 启发式与数值算法库。遗传算法、模拟退火、粒子群、蒙特卡洛、常微分方程数值解 |
| `pyomo` | Python 优化建模框架封装。线性与整数规划、约束建模、求解器调用 |

### 03 论文写作

| 技能 | 作用 |
|---|---|
| `academic-writing` | 学术表达与结构质量主入口。调用本地化审阅规则，限定只改普通正文，保护公式、引用、数字、三线表与图表引用 |
| `mathmodel-latex-skill` | 竞赛风格 LaTeX 论文工程。模板生成、改编、编译与预检，覆盖 CUMCM 与 COMAP MCM/ICM 格式要求 |
| `bzd-review-paper` | 独立构建百分制评分细则，审计资格与格式，按权重上限打分并给出中文评委反馈 |
| `论文辅助` | 论文 G0 到 G6 节点只读审查。检查符号完整性、元话语、负向回声、模型证据，输出结构化修改清单 |

### 04 图表可视化

| 技能 | 作用 |
|---|---|
| `scipilot-figure-skill` | 可视化顾问定位。先做数据剖析再定图型，按出版级样式出图 |
| `modelviz` | 从自有 CSV/XLSX 数据加一句自然语言绘图需求，产出论文级科学图 |
| `figure-generation` | matplotlib 与 seaborn 出版级配图。查询扩展、代码生成执行、视觉反馈三段流水线 |
| `tikz-scientific-figures` | TikZ 与 PGFPlots 排版级插图。输出 SVG 与 PNG，适合需要矢量精确控制的示意图 |
| `fireworks-tech-graph` | 技术类图示。软件架构、数据流、流程图、时序图、C4 评审、云部署与事件流 |
| `tech-route-maker` | 技术路线图。生成可编辑、有证据支撑的路线图并导出 |
| `drawio-diagram` | 生成标准 `.drawio` 格式图表，可在 diagrams.net 继续编辑 |

### 05 通用工具

| 技能 | 作用 |
|---|---|
| `web-access` | 联网操作统一入口。搜索、网页抓取、需登录的页面访问与网络交互 |
| `markitdown-skill` | 文档转 Markdown。PDF、Word、PowerPoint、Excel、图片 OCR、音频转写、HTML 与网页链接 |
| `browser-cdp` | 通过 Chrome DevTools 协议复用已登录会话控制浏览器 |
| `humanizer-zh` | 中文去 AI 味。检测并清除模板化表达 |

### 06 元技能

| 技能 | 作用 |
|---|---|
| `darwin-skill` | 技能自优化。八维评分准则评估 SKILL.md，爬山式迭代改进 |
| `self-improvement` | 从失败、纠错、用户指正中沉淀可复用经验 |
| `skill-audit-cleanup` | 技能库全量审计。按真实使用记录分高频必留、低频暂存、无用归档，产出报告与归档脚本 |

### 99 创意写作

十二个网文创作技能，与数学建模无关，附在本仓库便于一处取用。

`story` 为总入口，路由到 `story-long-write`、`story-short-write`、`story-long-analyze`、`story-short-analyze`、`story-long-scan`、`story-short-scan`、`story-review`、`story-deslop`、`story-cover`、`story-import`、`story-setup`。

不需要可直接删除该目录，不影响其余技能。

---

## 依赖

核心主控流程只依赖 Python 3.9 以上标准库。各技能的额外依赖见自身 `SKILL.md`，常用组合：

```bash
pip install numpy pandas scipy matplotlib seaborn scikit-learn statsmodels
pip install pyomo pygments reportlab
```

绘图类技能若需中文字体，请自行安装宋体或思源宋体并在 matplotlib 中配置 `font.sans-serif`。

LaTeX 相关技能需要可用的 TeX 发行版，推荐 MiKTeX 或 TeX Live，编译引擎用 `xelatex`。

---

## 设计原则

技能之间通过标准名称直接引用，不做动态发现。`contest-orchestrator` 在 SKILL.md 中显式声明了对 `scipilot-figure-skill`、`mathmodel-latex-skill`、`bzd-review-paper` 的依赖。因此**改名会断链**，二次开发时请保留原始技能名。

阶段推进设门禁。每个阶段结束跑一致性检查，任一检查失败即回退修复，不静默跳过。这套设计牺牲了部分自动化流畅度，换来可审计的推进轨迹。

缺输入就停。题面、附件、文献不足时流程停住并向使用者索要，不虚构数据与结论。

---

## 版权与合规

本仓库只收录技能定义、脚本与流程规范，**不包含任何竞赛论文全文、赛事数据集、获奖作品原文或写作引用素材库**。

上游开发环境中曾用于校准的论文文本、写作经验库与决策日志属于本地私有资产，已在 `.gitignore` 中排除，不会随仓库分发。

论文评审与写作类技能输出的建议由使用者自行判断采纳。使用本仓库任何技能生成的参赛作品，其合规性由使用者负责。

代码示例中的路径统一写作 `C:/Users/USER/...` 或 `/home/USER/...`，请替换为你的实际路径。

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

## License

Apache License 2.0，详见 [LICENSE](LICENSE)。

---

如果这套技能对你的建模或论文写作有帮助，点个 Star 支持一下。有改进建议欢迎提 Issue。
