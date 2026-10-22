# 图表位置纪律（防浮动/防连图/防错位）

本文件是学术写作时的图表位置硬纪律，用于在写作阶段和编译后阶段主动预防"图片连在一起中间无文字""图表出现在不该出现的位置""图片浮动到下一页"三类问题。它不是排版美化建议，是可被扫描器检出的结构约束。

## 1. 每条图/表必须满足的结构

| 检查项 | 要求 | 违反后果 |
|---|---|---|
| 图前引出句 | 每个 `\begin{figure}` 之前的最近正文段落必须包含对该图的引出（如"如图 X 所示""结果见图 X"或 `\ref{fig:xxx}`） | 图无来源，读者不知道为什么出现 |
| 图后解释句 | 每个 `\end{figure}` 之后的最近正文段落必须对图中关键结论做至少一句解释，不能立刻接下一个图或下一节 | 图成了纯装饰，论证断裂 |
| 禁止连续浮动体 | 同一节内两个 `\begin{figure}`（或 figure 与 table 混合）之间必须有正文段落；连续 ≥2 个浮动体无正文即违规 | 图片堆在一起，中间无文字 |
| 引用先于图 | 图的首次正文引用必须出现在图环境之前或同段，禁止图先于引用出现 | 读者先看到图再看到说明，逻辑倒置 |
| 浮动参数合法 | 默认 `[htbp]`；用 `[H]` 强制当前位置时必须已 `\usepackage{float}`；禁止裸 `[H]` 无 float 包 | 编译警告 "H float specifier changed"，图实际位置失控 |

## 2. 自动检查器（check_tex_layout_patterns.py）

以下5项已接入 `contest-orchestrator/scripts/check_tex_layout_patterns.py`，在 `delivery_all.py` 的 F2.6 步骤自动运行（--strict模式，BLOCK级别）：

| 检查项 | kind字段 | 级别 | 说明 |
|--------|----------|------|------|
| 连续浮动体检测 | `consecutive_floats` | BLOCK | 两个figure/table之间无正文段落 |
| 图前无引出检测 | `figure_no_intro` | BLOCK | figure之前的最近正文行不含\ref/\cref/如图/见图/所示等引出信号（附录除外） |
| 图后无解释检测 | `figure_no_explanation` | BLOCK | figure之后到下一个\section之间无正文（附录除外，连续浮动体已被上一项检测则跳过） |
| [H]强制位置检测 | `hard_float` | BLOCK | 正文图表使用[H]，可能把后续内容推到下一页 |
| 连续强制分页检测 | `consecutive_page_break` | BLOCK | 连续\clearpage/\newpage制造空白页 |
| 大手工留白检测 | `large_manual_space` | WARN | \vspace超过24pt，可能用于凑页数 |

运行命令：
```bash
python scripts/check_tex_layout_patterns.py <paper.tex或目录> --strict
```

## 3. 写作阶段扫描规则（补充检查，非自动）

以下2项目前靠agent手动扫描，未接入自动检查器：

1. **`[H]` 无 float 包检测**：源码出现 `\begin{figure}[H]` 但导言区无 `\usepackage{float}`，标记"[H] 需 float 宏包"。（注：check_tex_layout_patterns.py 已检测[H]使用，但不检查float包是否加载）
2. **图过大检测**：编译日志出现 `Float too large for page`，标记"图尺寸超过版心，需缩图或拆图"。（靠编译日志，不自动扫描源码）

## 4. 与 H8 写作计划的对齐

H8 阶段一的写作计划必须包含"图片位置规划"：每张图放在哪一章哪一小节、图前引出句属于哪个论证点、图后解释句承接哪个结论。写作时按该规划落位，不允许把所有图堆在章节末尾。若实际写作中某图无法按规划落位（如内容不足），回流 H7 调整图数或 H5 补结果，不得用空白或重复文字硬凑位置。

## 5. 附录图的例外

附录中的图（`\appendix` 之后）不受"图前引出/图后解释"强制约束，但仍受"禁止连续浮动体"和"浮动参数合法"约束。附录图不占用正文论证容量，正文 30 页硬上限不计附录。

## 6. 不做的事

- 不自动改 `[htbp]` 为 `[H]`（位置参数选择由作者判断，强制 [H] 可能导致版面空洞）。
- 不自动在图前后插入文字（插入什么论证内容是作者/论文 agent 的职责，扫描器只标记缺口）。
- 不修改图本身的尺寸、路径或编号（那是 H7 图表 agent 和 mathmodel-latex-skill 的职责）。
