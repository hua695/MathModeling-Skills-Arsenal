# 数学建模 LaTeX 论文 Skill

版本：1.0.8。此版本在 1.0.7 的终校验基础上，修复 CUMCM 中文图表题名冒号和附录编号显示；同时保留 1.0.5 的 ref.bib 与交叉引用修复基础上，进一步移除 CUMCM 模板中的“总体思路”小节，并新增关键词约束：关键词必须优先选用数学建模教材和竞赛论文中常见的模型、方法、算法、评价或检验术语，避免把题目对象或行业场景直接作为关键词。

这是一个给 Codex 和 Claude Code 使用的 skill，用来生成和检查美赛 MCM/ICM、国赛 CUMCM 的 LaTeX 数学建模论文项目。

它不是一个单独发布的 LaTeX 模板包，而是一组给 AI 编程助手读取的工作规则、模板和检查脚本。安装后，你可以直接让 Codex 或 Claude Code 按比赛类型生成论文项目，并让它处理模板选择、引用方式、匿名信息检查和编译前检查。

## 适合做什么

- 生成 MCM/ICM 英文论文项目。
- 生成 CUMCM 中文论文项目，并默认采用优秀论文常见章节命名与写法，避免教学式或说明文式章节。
- 在 `mcmthesis`、`cumcmthesis` 兼容类、`ctexart` fallback 之间做稳定选择。
- 默认使用 `ref.bib` / BibTeX 管理参考文献，并提供引用键检查；模板不再放置活动的手写参考文献块。
- 检查摘要关键词是否为数学建模相关术语，避免使用“农作物种植策略”等题目对象词作为关键词。
- 避免默认写入学校、队员、导师、赛区等真实身份信息。
- 提供 PDF 页数、大小和身份关键词风险的提交前检查脚本，默认预警，最终提交前可切到严格模式。

## 安装

把整个 `mathmodel-latex-skill` 文件夹复制到对应助手的 skills 目录下。文件夹名建议保持为 `mathmodel-latex-skill`。

### Codex

Windows PowerShell 示例：

```powershell
$skills = "$env:USERPROFILE\.codex\skills"
New-Item -ItemType Directory -Force $skills | Out-Null
Copy-Item -Recurse -Force . "$skills\mathmodel-latex-skill"
```

WSL / macOS / Linux 示例：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R . "${CODEX_HOME:-$HOME/.codex}/skills/mathmodel-latex-skill"
```

### Claude Code / cc-switch

如果你使用 `cc-switch` 管理 Claude Code skills，放到 `.cc-switch/skills`。

Windows PowerShell 示例：

```powershell
$skills = "$env:USERPROFILE\.cc-switch\skills"
New-Item -ItemType Directory -Force $skills | Out-Null
Copy-Item -Recurse -Force . "$skills\mathmodel-latex-skill"
```

WSL / macOS / Linux 示例：

```bash
mkdir -p "$HOME/.cc-switch/skills"
cp -R . "$HOME/.cc-switch/skills/mathmodel-latex-skill"
```

如果你的 Claude Code 使用其他 skills 目录，请复制到你实际配置的 skills 路径。

安装后建议开启一个新会话，让新 skill 被重新发现。

## 如何触发

在 Codex 或 Claude Code 里直接描述你的数学建模论文任务即可。可以显式提到 skill 名，也可以只描述比赛类型。

示例：

```text
使用 mathmodel-latex-skill，给我创建一份 MCM/ICM A 题论文项目，启用 ref.bib。
```

```text
使用 mathmodel-latex-skill，生成国赛 CUMCM 电子版论文模板；如果没有 cumcmthesis，就用 ctexart fallback。
```

```text
用这个 skill 检查我的 CUMCM 论文 PDF，确认页数、大小和身份信息风险。
```

## 推荐工作流

1. 复制整个 `mathmodel-latex-skill` 文件夹到 Codex 或 Claude Code 的 skills 目录。
2. 新建一个空论文项目目录，让助手按比赛类型复制对应模板。
3. 检查 LaTeX 环境：

```bash
python scripts/check_latex_env.py --contest mcm-icm
python scripts/check_latex_env.py --contest cumcm
python scripts/check_latex_env.py --contest cumcm --strict-class
python scripts/check_latex_env.py --contest mcm-icm --use-ref-bib
python scripts/check_latex_refs.py main.tex --bib ref.bib
python scripts/check_latex_keywords.py main.tex
```

4. 根据检查结果选择 `mcmthesis`、内置轻量 `cumcmthesis` 兼容类，或 CUMCM 的 `ctexart` fallback。
5. 编译：MCM/ICM 使用 `latexmk -pdf -shell-escape main.tex`；CUMCM 中文模板使用 `latexmk -xelatex -shell-escape main.tex`，或在携带本 skill 的 `latexmkrc` 时使用 `latexmk -shell-escape main.tex`。不要用 `latexmk -pdf` 编译 CUMCM 中文模板，因为它会强制走 pdfLaTeX。
6. 运行 PDF preflight：

```bash
python scripts/check_pdf.py main.pdf --identity-mode warn
python scripts/check_pdf.py main.pdf --identity-mode strict
python scripts/check_pdf.py main.pdf --ignore-keyword University --ignore-keyword 大学
```

7. 人工核查匿名信息、当年官方规则、页数/大小限制、AI 使用说明和支撑材料清单。

## 使用时可以指定的关键选项

`contest`：比赛类型。常用值是 `MCM/ICM` 或 `CUMCM`。

参考文献模式：默认且推荐使用 `ref.bib`。正文用 `\cite{...}` 引用，文献信息统一写入 `ref.bib`；若用户明确要求不用 BibTeX，再由助手另行生成手写 `thebibliography`，不要在同一主文件中混用两套模式。

`strict_class`：是否严格要求类文件。CUMCM 模板目录内置一个轻量 `cumcmthesis.cls` 兼容类；如果项目中删除或替换了它，仍可回退到 `ctexart` fallback。若你要求使用第三方/官方风格的完整 `cumcmthesis`，应自行提供并核验其授权、字体依赖和当年格式适配。

`identity-mode`：PDF 身份关键词检查模式。默认 `warn` 只提示风险；真正提交前可以改成 `strict`，让关键词命中直接失败。

`ignore-keyword`：对已经人工确认的误报关键词做临时忽略，例如参考文献或数据来源里的 `University`、`大学`。

## 内置内容

- `SKILL.md`：AI 助手实际读取的工作规则。
- `templates/mcm-icm/`：MCM/ICM 模板，优先使用 `mcmthesis`。
- `templates/cumcm/`：CUMCM 模板，包含轻量 `cumcmthesis.cls` 兼容类、`cumcmthesis` 入口和 `ctexart` fallback。
- `scripts/check_latex_env.py`：按比赛类型检查本机 LaTeX 类文件、fallback 和 BibTeX 环境。
- `scripts/check_pdf.py`：检查 PDF 页数、文件大小和身份关键词风险，支持 `warn` / `strict` 模式。
- `scripts/check_latex_refs.py`：检查 `\ref` / `\eqref` / `\cite` 是否存在未定义标签或未定义文献键。
- `scripts/check_latex_keywords.py`：检查摘要关键词是否属于数学建模方法、模型、算法、评价或检验术语。
- `latexmkrc`：默认使用 XeLaTeX 的构建配置。

## 注意事项

- 本仓库现在内置一个轻量 `cumcmthesis.cls` 兼容类，目的是保证 CUMCM 默认入口可离线编译；它不是上游 CUMCMThesis 模板的逐字复制，也不包含字体文件。
- `mcmthesis` 通常由 TeX Live / MiKTeX 管理。
- 若需要第三方完整 `cumcmthesis` 模板，请自行提供或安装，并核验许可证、字体依赖和当年格式规则；不要假设 `tlmgr` 一定能安装。
- CUMCM 模板新增 `templates/cumcm/STYLE_GUIDE.md`，用于约束“数据预处理”“模型假设：解释”等优秀论文风格写法。
- 最终比赛提交前，应以当年官方规则为准。
- 任何由 AI 生成的论文内容都需要人工核验。


## 1.0.5 引用管理约定

- 默认使用 `ref.bib` 作为唯一参考文献数据库。
- 正文文献引用只使用 `\cite{key}`，不要用 `\ref{key}` 引用文献。
- 图、表、公式引用只使用 `\ref{label}` 或 `\eqref{label}`，不要用 `\cite{label}`。
- 不主动使用 `\nocite{...}`；没有被正文引用的 `.bib` 条目不应出现在最终参考文献中。
- 交付前运行：`python scripts/check_latex_refs.py main.tex --bib ref.bib`；若为 CUMCM 项目，再运行 `python scripts/check_latex_keywords.py main.tex`。


## 1.0.8 CUMCM 结构与关键词约定

- CUMCM 正文不单独设置“总体思路”小节；问题分析节按小问展开，例如 `2.1 问题一的分析`、`2.2 问题二的分析`。
- 若需要展示模型路线，优先使用“模型流程图”并放入问题分析或模型建立部分的自然段中，不另起 `2.4 总体思路`。
- 关键词必须优先选择数学建模教材和竞赛论文中常见的术语，例如：优化模型、线性规划、混合整数规划、目标规划、动态规划、蒙特卡洛模拟、回归分析、聚类分析、主成分分析、层次分析法、综合评价、风险决策、灵敏度分析、敏感性分析、鲁棒性分析、时间序列、灰色预测等。
- 关键词不要直接使用题目对象、行业背景或宽泛任务词，例如：农作物种植策略、乡村农业、蔬菜销售、企业生产、交通问题、研究方法。
- 交付前运行：`python scripts/check_latex_keywords.py main.tex`。

## 1.0.8 终校验修正

- 在 `templates/cumcm/` 和 `templates/mcm-icm/` 内分别加入模板本地 `latexmkrc`，使用户单独复制模板目录时也能使用 BibTeX fallback，不依赖 skill 根目录的 `latexmkrc`。
- CUMCM 模板本地 `latexmkrc` 默认 XeLaTeX；MCM/ICM 模板本地 `latexmkrc` 仅处理 BibTeX fallback，保留 `latexmk -pdf main.tex` 工作流。
- BibTeX 检测从“命令存在”升级为“命令存在且可执行 `--version`”，避免损坏的 `bibtex` 替代项导致编译失败。


## 1.0.8 图表题名与附录编号修正

- CUMCM 模板现在默认将图表题名渲染为 `表 1 标题`、`图 1 标题`，去掉 `表 1: 标题` 中的英文冒号。
- 附录一级标题渲染为 `附录A 支撑材料文件列表`、`附录B 源程序代码说明`；国赛 2026 的 `AI工具使用详情.pdf` 放入支撑材料压缩包，正文声明位于参考文献前。
- 该修正已同时应用到 `main.tex`、`main-cumcmthesis.tex` 和 `main-ctexart-fallback.tex`。
