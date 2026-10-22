---
name: mathmodel-latex-skill
description: Generate stable and competition-style LaTeX mathematical modeling paper projects for MCM/ICM and CUMCM. Use when creating, adapting, compiling, or preflighting competition paper templates for COMAP MCM/ICM, Chinese Undergraduate Mathematical Contest in Modeling (CUMCM), or similar mathematical modeling submissions, including mcmthesis, cumcmthesis, XeLaTeX, latexmk, PDF page/size checks, identity-info checks, references, appendices, and AI-use disclosure sections. 触发：国赛/美赛/中文论文/LaTeX模板/论文排版/模板编译/数学建模论文。
---

# Mathematical Modeling LaTeX Projects

Use this skill to create reproducible LaTeX paper projects for MCM/ICM and CUMCM. Prefer the templates in this skill, keep dependencies explicit, and avoid embedding real identity information.

## Contest-Orchestrator Adapter

在 `contest-orchestrator` 中，本技能只负责中文竞赛论文的模板、排版、编译和结构预检。输入是项目工作区中的论文入口、已冻结模型/结果/引用、`appendix_plan.yaml`、AI 工具说明要求和交付约束；不得生成不存在的数字、公式、符号、引用、图表或结论。

- 保护公式、符号、单位、数字、引用键、图表编号、模型逻辑和附录证据；新符号定义缺失时回流，不在排版层猜测。
- 输出节点包包含 `status`、`active_mode`、`task_card`、`artifacts`、`evidence`、`checks`、`blockers`、`next_node`，所有生成文件只写项目工作区。
- Formal figure insertion format is SVG（图表正式插入格式为 SVG）；正文使用 `\\includesvg{figures/<figure_id>}`。PNG 仅作预览和兼容性副本，不使用图片 PDF；论文最终交付 PDF 仍按竞赛要求生成。
- 默认只做文本层、结构、引用、编译和交付约束检查；不截图、不渲染复核，视觉检查由用户肉眼完成，除非用户明确要求。
- 论文、附录和报告不得出现元话语、内部交流、评审记录、调试、失败、旧版本或其他负回响；AI 工具说明按竞赛规则单独生成，不把内部过程写入正文。

## Competition Recognition

- Treat prompts mentioning MCM, ICM, COMAP, Meritorious/Winner papers, team control number, problem A-F, or "Report on Use of AI" as MCM/ICM.
- Treat prompts mentioning CUMCM, National Undergraduate Mathematical Contest in Modeling, 国赛, 全国大学生数学建模竞赛, 承诺书, 编号专用页, 支撑材料, or 中文摘要 as CUMCM.
- If the contest is unclear, infer from language and required fields: English + team control number usually means MCM/ICM; Chinese + 摘要页/支撑材料 usually means CUMCM.
- If official rules for the current year are provided, follow them over these defaults.

## Reference Mode

- Decide `use_ref_bib` before generating or editing a project.
- Default to `use_ref_bib = true` for newly generated projects because this skill ships `ref.bib` and competition papers benefit from citation-key based reference management. The bundled templates use `ref.bib` directly and do not include an active inline `thebibliography` fallback. Use inline `thebibliography` only when the user explicitly asks not to use BibTeX or the local environment lacks BibTeX, and generate that as a separate edit rather than mixing both modes.
- Set `use_ref_bib = true` when the user asks for `ref.bib`, BibTeX, citation-key based references, Zotero/JabRef/BibDesk exports, or a reusable bibliography database.
- When `use_ref_bib = true`, keep `ref.bib` beside `main.tex`, cite entries with `\cite{...}`, and let `latexmk` run BibTeX automatically. For CUMCM, prefer `gbt7714` with `gbt7714-numerical` and `\citestyle{numbers}` so references render as numeric entries instead of author-year labels. Replace the sample `placeholder-ref` entry before final submission. Do not use `\nocite{...}` unless the user explicitly wants uncited sources listed.
- Do not mix active `thebibliography` and active `\bibliography{ref}` in the same generated paper.
- Separate literature citations from cross references: use `\cite{bib-key}` only for literature/software/data sources in `ref.bib`; use `\label{...}` plus `\ref{...}` or `\eqref{...}` only for figures, tables, equations, algorithms, appendices, or sections.
- Avoid gratuitous placeholder cross references. Add `\ref` only when the referenced `\label` exists and the sentence genuinely needs a numbered table/figure/equation. Keep `hypertexnames=false` in CUMCM templates to avoid duplicate PDF anchors when counters reset in appendices.
- Before delivering a project, run `python scripts/check_latex_refs.py main.tex --bib ref.bib` when `ref.bib` mode is active, and fix all missing labels or missing citation keys.

## Figure Insertion Contract

- Load the `svg` package in every bundled paper template and use `\\includesvg{figures/<figure_id>}` for formal figure insertion.
- Treat the SVG as the authoritative figure asset. Keep the matching PNG beside it for preview and visual QA; do not register or deliver an image PDF, EPS, TIFF, or JPEG.
- Before compilation, verify that the SVG exists, is non-empty, has the expected figure identifier, and is paired with the registered PNG. Preserve the editable source and the source-to-figure mapping in the project workspace.
- Compile with shell escape when the local `svg` package requires conversion support, for example `latexmk -xelatex -shell-escape main.tex` for CUMCM or `latexmk -pdf -shell-escape main.tex` for MCM/ICM. Use only local tools; if SVG conversion is unavailable, block compilation instead of silently replacing the figure with a PDF image.
- This contract applies to figure assets only. The compiled paper PDF remains the formal paper deliverable.

## MCM/ICM Generation Rules

- Start from `templates/mcm-icm/main.tex`.
- Use the official LaTeX package class when available:

```tex
\documentclass{mcmthesis}
```

- Treat `mcmthesis` as a formal LaTeX package normally managed by TeX Live or MiKTeX. Do not copy `mcmthesis.cls` into the project by default.
- Include placeholders for team control number, problem letter, title, summary, keywords, model sections, references, appendices, and `Report on Use of AI`.
- Support `use_ref_bib` with `templates/mcm-icm/ref.bib`; the bundled template uses BibTeX directly.
- Include a table of contents after `\maketitle` for MCM/ICM by default, matching the `mcmthesis` demo pattern. Remove it only if the current official rules or user request say not to include it.
- Keep all identity fields generic. Use placeholders such as `0000000`, `A`, and `Paper Title Placeholder`.
- Do not add school names, author names, adviser names, regions, email addresses, phone numbers, or acknowledgements that reveal the team.

## CUMCM Generation Rules

- Prefer `templates/cumcm/main-cumcmthesis.tex` when `cumcmthesis.cls` is available:

```tex
\documentclass[withoutpreface,bwprint]{cumcmthesis}
```

- This skill includes a lightweight `templates/cumcm/cumcmthesis.cls` compatibility class so the default CUMCM entry can compile offline. Treat it as a portable compatibility layer, not as a guarantee of official current-year formatting. Do not assume third-party `cumcmthesis` variants can be installed with `tlmgr`.
- Also provide `templates/cumcm/main.tex` for the default cumcmthesis-compatible entry point and `templates/cumcm/main-ctexart-fallback.tex` as a no-class fallback.
- Use XeLaTeX for all Chinese templates.
- Default to electronic version options `withoutpreface,bwprint`.
- Include a dedicated abstract page, keywords, body sections, references, appendices, and a supporting-material file list. For CUMCM 2026, place the AI declaration before the references and put `AI工具使用详情.pdf` in the supporting-material package.
- For CUMCM 2026 electronic submission, use a text-layer PDF, omit the table of contents. Body page count starts from the main body (abstract NOT included), covering main body, AI-use declaration before references, and references, at most 30 pages; appendix is outside the 30-page body limit. Total submission PDF (abstract + body + references + appendix) hard cap is 51 pages, recommended range 35–51 pages. Keep the PDF at or below 20 MB.
- The declaration and detail must be truthful and concise about actual use, and explicit about human verification and team ownership of core modeling and analysis.
- Support `use_ref_bib` with `templates/cumcm/ref.bib`; the bundled template uses BibTeX directly.
- Do not generate a table of contents in CUMCM electronic submissions by default. Keep only commented optional `\tableofcontents` lines for years or local rules that explicitly require it.
- For the user's Hunan regional workflow, submit PDF rather than Word; total submission PDF hard cap is 51 pages (recommended 35–51 pages), not a local 50-page recommendation.
- Do not generate school, team member, adviser, instructor, campus, province, or regional identity information. Leave identity-related class commands absent or blank unless the user explicitly supplies non-sensitive placeholders required by official rules.

## CUMCM Extras Macros (cumcm-extras.sty)

国赛模板默认加载 `templates/cumcm/cumcm-extras.sty`，提供建模论文常用快捷命令。不用可在 `main.tex` 中注释掉 `\usepackage{cumcm-extras}`。

- **数学符号**：`\mat{A}`（矩阵粗体正体）、`\vb{x}`（向量粗体斜体）、`\trans`（转置上标）、`\R`（实数集）、`\argmin`/`\argmax`（自动下标）、`\Var`/`\Cov`、`\upcite{key}`（上标引用）
- **定理环境**：`definition`、`theorem`、`lemma`、`corollary`、`assumption`、`remark`、`property`、`example` 等 13 种，中文，按 section 编号
- **算法伪代码**：`algorithm` + `algorithmic` 环境，中文关键字自动汉化（输入、输出、当、则、遍历、返回等）
- **智能引用**：`\cref{fig:1}` 输出"图1"，`\cref{tab:1,eq:2}` 输出"表1和式(2)"，支持 `\crefrange`
- **表格增强**：`\topline`/`\midline`/`\bottomline` 三线表快捷命令，`Y`（居中 X 列）/`J`（左对齐 X 列）列类型，`longtable` 跨页表格
- **插图宏**：`\figplot{题注}{label}{文件名}{制图说明}`，自动搜索路径，文件不存在时显示占位框，用 `[!htbp]` 浮动（禁止 `[H]`），图宽 0.76\textwidth
- **脱敏占位**：`\email{...}`/`\phone{...}` 编译输出 `[已脱敏]`
- **写作标记**：`\todo{...}`（橙色）、`\draftnote{...}`（红色），终稿前必须清除
- **浮动参数**：与 contest-orchestrator `figure_policy.md` 一致（topfraction=0.85, textfraction=0.1, topnumber=3），支持 `\FloatBarrier` 章末防跨章

详细用法见 `templates/cumcm/STYLE_GUIDE.md` 第 9 节。

### CUMCM Excellent-Paper Style Rules

- For CUMCM, follow `templates/cumcm/STYLE_GUIDE.md` when generating paper structure or examples.
- Use the default section order: 摘要, 问题重述, 问题分析, 模型假设, 符号说明, 数据预处理, 模型建立与求解, 模型检验, 模型评价与推广, 参考文献, 附录.
- Render level-one CUMCM sections as Chinese numerals with a dunhao, such as `一、问题重述`; render subsections as `1.1 问题背景`.
- Do not create a standalone subsection named `总体思路`, `总体模型思路`, `整体思路`, or similar in CUMCM final-style papers. In excellent-paper style, `问题分析` should normally be organized by subproblem, such as `2.1 问题一的分析`, `2.2 问题二的分析`, and `2.3 问题三的分析`. If a route explanation is needed, write it as a short paragraph inside the relevant analysis section or use a `模型流程图`; do not add `2.4 总体思路`.
- CUMCM keywords must be mathematical-modeling terms, preferably terms found in mathematical modeling textbooks or common contest papers. Use model/method/algorithm/evaluation terms such as `优化模型`, `线性规划`, `混合整数规划`, `目标规划`, `动态规划`, `蒙特卡洛模拟`, `回归分析`, `聚类分析`, `主成分分析`, `层次分析法`, `综合评价`, `风险决策`, `敏感性分析`, `鲁棒性分析`, `时间序列`, and `灰色预测`. Avoid using research objects, industry scenarios, or题目背景词 as keywords, such as `农作物种植策略`, `乡村农业`, `蔬菜销售`, or `交通问题`, unless they are paired with a recognized modeling method and the user explicitly requires a domain keyword.
- Before delivering a CUMCM project, run `python scripts/check_latex_keywords.py main.tex` and revise keywords that fail the modeling-term check.

- Standardize the data section title as `数据预处理`. Do not use `数据读取与预处理`, `数据剔写`, `数据说明与读取`, or other ad-hoc titles in final-style CUMCM papers.
- Write model assumptions as a numbered list. Each item must follow the pattern `假设 n：...。解释：...` so the assumption and its modeling justification are both visible.
- Do not add non-paper chapters such as `编译测试结果`, `LaTeX 测试说明`, or standalone `算法实现说明` to CUMCM example PDFs. Put run commands, compile notes, and code explanations in README or appendices.
- In the abstract and result sections, never invent numerical results. Use explicit placeholders when no solver output exists.


### Reference and Cross-Reference Hygiene

- Use `ref.bib` for references by default. Keep all bibliographic metadata in `ref.bib`; do not leave a live `thebibliography` block in final-style examples.
- Cite data sources, papers, and software with `\cite{...}` when they are genuine sources used by the paper. For CUMCM 2026, disclose AI tools in the paper declaration and `AI工具使用详情.pdf` in supporting materials; do not add an AI tool bibliography entry solely to record AI use. If an AI tool is independently used as a software or research source, cite only the specific technical claim it supports.
- Reference figures, tables, formulas, and appendices with `\label{...}` and `\ref{...}` / `\eqref{...}`. The label must exist in the same project.
- Do not cite tables with `\cite` and do not cite papers with `\ref`.
- Do not use `\nocite{placeholder-ref}` in final examples, because it creates references that are not grounded in the text.
- Run `scripts/check_latex_refs.py` before compiling final deliverables; then compile and ensure the log has no `undefined references` or `Citation ... undefined` warnings.

### Layout Reference（精细排版速查）

遇到图文混排、复杂表格、彩色框、页面布局、公式间距、子图、算法伪代码等精细排版需求时，读取 `references/latex_layout_cheatsheet.md`（数学建模论文 LaTeX 精细排版速查表），覆盖15个大类：图文混排（wrapfig/floatrow）、左右并排（minipage/tabular）、复杂表格（booktabs/multirow/tabularx/longtable）、彩色框（tcolorbox/mdframed）、页面布局（geometry/fancyhdr/titlesec）、公式精细调整（amsmath/mathtools/间距/编号）、子图（subcaption）、算法伪代码（algorithm+algpseudocode）、代码高亮（listings/minted）、字体、颜色、图形绘制（tikz/pgfplots）、其他实用包（hyperref/caption/enumitem/siunitx）、常见问题速查、国赛模板已加载的包。每个包给出用途、核心命令、最小示例和注意事项。

## Compilation Rules

- Use `latexmkrc`; it defaults to XeLaTeX.
- Compile according to contest/template:

```bash
# MCM/ICM, mcmthesis workflow
latexmk -pdf -shell-escape main.tex

# CUMCM Chinese workflow
latexmk -xelatex -shell-escape main.tex
# or, when this skill's latexmkrc is present in the project directory
latexmk -shell-escape main.tex
```

- Do not use `latexmk -pdf` for CUMCM Chinese templates; it forces pdfLaTeX in many latexmk versions and can fail on `ctexart`/XeLaTeX font handling.

- For MCM/ICM, run `scripts/check_latex_env.py --contest mcm-icm` first to verify `mcmthesis.cls`. If `mcmthesis.cls` is missing, stop MCM/ICM project generation or compilation and tell the user to install `mcmthesis` through TeX Live, MiKTeX, or their TeX package manager before retrying.
- For CUMCM, run `scripts/check_latex_env.py --contest cumcm` first. Prefer the local `templates/cumcm/cumcmthesis.cls` compatibility class when copied with the project. If no local or TeX-tree `cumcmthesis.cls` is available, default to `templates/cumcm/main-ctexart-fallback.tex`; this is a warning, not a failure, as long as the `ctexart` fallback is available.
- Only when the user explicitly requires a third-party/full `cumcmthesis` class or strict official-class compatibility beyond the local compatibility class, ask the user to provide that class and verify its license/font requirements/current-year compliance.
- If `use_ref_bib = true`, add `--use-ref-bib` to the same contest-specific environment check, for example `scripts/check_latex_env.py --contest mcm-icm --use-ref-bib`.
- Do not make successful compilation depend on network access. Network downloads are not a valid build step.
- Before the contest, freeze the final compilable template and dependencies together, including allowed class files. Do not bundle font files unless their license clearly permits redistribution and the user intentionally provides them.

## Prohibited Behavior

- Do not add third-party `.cls` files with unclear redistribution rights. The bundled `templates/cumcm/cumcmthesis.cls` is a lightweight compatibility class; keep third-party class files separate unless the user intentionally provides them and their license permits redistribution.
- Do not invent official year-specific page limits, size limits, AI disclosure rules, or submission rules. Use the current official contest documents when supplied.
- Do not insert real schools, names, student IDs, adviser names, regions, emails, phone numbers, or acknowledgements.
- Do not switch Chinese templates to pdfLaTeX.
- Do not enable `ref.bib` without also keeping the `ref.bib` file in the copied project directory.
- Do not depend on online images, online bibliographies, or online package installation during final compilation.
- Do not include a table of contents in the CUMCM fallback electronic template unless the user explicitly requests it.

## Checklists

Before writing a project:

- Identify the contest as MCM/ICM or CUMCM.
- Decide whether `use_ref_bib` is true or false.
- Choose the matching template directory.
- Run `scripts/check_latex_env.py --contest mcm-icm` or `scripts/check_latex_env.py --contest cumcm`, adding `--use-ref-bib` when BibTeX is needed.
- Decide whether class dependencies are installed locally or whether a fallback is needed.

Before final submission:

- Compile from a clean directory with the contest-appropriate command: `latexmk -pdf -shell-escape main.tex` for MCM/ICM, and `latexmk -xelatex -shell-escape main.tex` or `latexmk -shell-escape main.tex` with this skill's `latexmkrc` for CUMCM.
- Run the structural and text-layer checks for the PDF. Do not perform visual inspection by default; perform visual inspection only when the user requests it. Confirm that the AI-use section and appendix file list are present in the extracted text.
- If official page and file-size limits are known, run `scripts/check_pdf.py <paper.pdf> --max-pages <official-page-limit> --max-size-mb <official-size-limit-mb>`.
- If official limits are not provided, run `scripts/check_pdf.py <paper.pdf>` without page or size flags, then note that the official current-year limits still need manual confirmation.
- Treat default identity keyword matches from `check_pdf.py` as warnings that need human review. For the final gate, run `scripts/check_pdf.py <paper.pdf> --identity-mode strict`, using repeated `--ignore-keyword <word>` only for reviewed false positives such as institution names in references or data sources.
- Confirm manually that the PDF does not contain real personal, school, adviser, team, email, phone, or regional identity information.
- Confirm all generated figures, tables, code listings, references, and supporting-material filenames match the final paper.

## 模板复制与编译要点

When copying a bundled template into a new paper project, copy the template-local `latexmkrc` as well. The CUMCM template-local `latexmkrc` enforces XeLaTeX and provides a BibTeX fallback; the MCM/ICM template-local `latexmkrc` only provides the BibTeX fallback so `latexmk -pdf -shell-escape main.tex` remains the expected workflow.


## CUMCM 图表标题与附录格式

- For CUMCM Chinese templates, table and figure captions must omit the colon: use `表 1 主要符号说明` / `图 1 模型流程图`, not `表 1: 主要符号说明`.
- Appendix section headings must render as `附录A ...`, `附录B ...`, `附录C ...`. After `\appendix`, set `\thesection` to `附录\mbox{\Alph{section}}` and reset the CTeX section style to use `number = \thesection` so xeCJK does not insert a visual space between `附录` and `A`.
- Do not simulate appendix or captions manually in text; use LaTeX `\section`, `\caption`, `\label`, and `\ref`.
