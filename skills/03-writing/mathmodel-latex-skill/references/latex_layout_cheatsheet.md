# 数学建模论文 LaTeX 精细排版速查表

本文件是数学建模论文常用LaTeX排版包的速查表，覆盖图文混排、复杂表格、彩色框、页面布局、公式调整、子图、算法伪代码等场景。每个包给出用途、核心命令、最小示例和注意事项。

---

## 一、图文混排

### 1. wrapfig — 文字环绕图片

**用途**：图片在左/右侧，文字自动环绕。

**核心命令**：
```latex
\usepackage{wrapfig}
\begin{wrapfigure}{l}{0.4\textwidth}  % l=左, r=右, i=内侧, o=外侧
  \centering
  \includegraphics[width=\linewidth]{fig.png}
  \caption{图题}
  \label{fig:1}
\end{wrapfigure}
这里是环绕的文字...
```

**注意事项**：
- 只适合短段落环绕，长段落可能出现排版异常
- 列表环境内不支持
- 图片宽度建议设为 `0.3-0.5\textwidth`
- 数学建模论文中慎用，标准排版是图片单独占一行

### 2. floatrow — 浮动体高级控制

**用途**：多图并排、图题位置控制、浮动体对齐。

**核心命令**：
```latex
\usepackage{floatrow}
\begin{figure}[htbp]
  \begin{floatrow}
    \ffigbox[\FBwidth]{\caption{图1}}{\includegraphics[width=0.45\textwidth]{fig1.png}}
    \ffigbox[\FBwidth]{\caption{图2}}{\includegraphics[width=0.45\textwidth]{fig2.png}}
  \end{floatrow}
\end{figure}
```

---

## 二、左右并排（minipage / tabular）

### 1. minipage — 左右分栏（最常用）

**用途**：左图右文、左文右图、左右两图、左右两表。

**核心命令**：
```latex
\begin{figure}[htbp]
  \begin{minipage}{0.58\textwidth}
    \centering
    \includegraphics[width=\textwidth]{fig.png}
  \end{minipage}
  \hfill  % 或 \hspace{0.02\textwidth}
  \begin{minipage}{0.38\textwidth}
    分析文字...
  \end{minipage}
  \caption{图题}
  \label{fig:1}
\end{figure}
```

**注意事项**：
- 两个minipage宽度之和不超过 `\textwidth`（留一点间距）
- 垂直对齐用 `[t]`（顶部）、`[c]`（居中，默认）、`[b]`（底部）
- 左图右文时，文字框宽度建议 `0.35-0.4\textwidth`，每行15-20字

### 2. tabular — 表格方式并排

```latex
\begin{figure}[htbp]
  \centering
  \begin{tabular}{cc}
    \includegraphics[width=0.45\textwidth]{fig1.png} &
    \includegraphics[width=0.45\textwidth]{fig2.png} \\
    (a) 子图1 & (b) 子图2
  \end{tabular}
  \caption{图题}
\end{figure}
```

---

## 三、复杂表格

### 1. booktabs — 三线表（国赛标准）

**用途**：专业三线表，国赛论文标配。

**核心命令**：
```latex
\usepackage{booktabs}
\begin{table}[htbp]
  \centering
  \caption{表题}
  \label{tab:1}
  \begin{tabular}{ccc}
    \topline  % 或 \toprule
    列1 & 列2 & 列3 \\
    \midline  % 或 \midrule
    数据1 & 数据2 & 数据3 \\
    数据4 & 数据5 & 数据6 \\
    \bottomline  % 或 \bottomrule
  \end{tabular}
\end{table}
```

**注意事项**：
- cumcm-extras.sty 已提供 `\topline`/`\midline`/`\bottomline` 快捷命令
- 禁止用竖线（`|`），三线表不用竖线
- 表头加粗用 `\textbf{}`

### 2. multirow + multicol — 合并单元格

**用途**：跨行、跨列的复杂表头。

```latex
\usepackage{multirow}
\begin{tabular}{|c|c|c|}
  \hline
  \multirow{2}{*}{跨行} & \multicolumn{2}{c|}{跨列} \\
  \cline{2-3}
  & 列1 & 列2 \\
  \hline
\end{tabular}
```

### 3. tabularx — 自动列宽

**用途**：某列自动填充剩余宽度。

```latex
\usepackage{tabularx}
\begin{tabularx}{\textwidth}{c X c}  % X列自动填充
  序号 & 内容（自动换行） & 备注 \\
\end{tabularx}
```

### 4. longtable — 跨页长表

**用途**：表格超过一页时自动分页。

```latex
\usepackage{longtable}
\begin{longtable}{ccc}
  \caption{跨页长表}\\
  \topline
  列1 & 列2 & 列3 \\
  \midline
  \endfirsthead  % 第一页表头
  \topline
  列1 & 列2 & 列3 \\
  \midline
  \endhead  % 后续页表头
  \bottomline
  \endfoot  % 每页底部线
  数据... \\
\end{longtable}
```

**注意事项**：longtable 不能放在 table 环境内，直接用。

---

## 四、彩色框 / 提示框

### 1. tcolorbox — 高级彩色框（推荐）

**用途**：虚线框、彩色框、提示框、定理框。

```latex
\usepackage{tcolorbox}
\tcbuselibrary{skins, breakable}

% 虚线框
\begin{tcolorbox}[colback=white, colframe=black, boxrule=0.5pt,
                   dash pattern=on 3pt off 2pt, breakable]
  框内文字...
\end{tcolorbox}

% 彩色提示框
\begin{tcolorbox}[colback=blue!5, colframe=blue!50!black,
                   title=提示, breakable]
  提示内容...
\end{tcolorbox}
```

**注意事项**：
- `breakable` 允许跨页
- 数学建模论文中慎用彩色框，正式论文用虚线框或无框
- 你上一张图问的虚线框就是用 tcolorbox 或 mdframed 做的

### 2. mdframed — 简单框架

```latex
\usepackage{mdframed}
\begin{mdframed}[linestyle=dashed, linewidth=1pt, roundcorner=5pt]
  框内文字...
\end{mdframed}
```

### 3. \fbox — 最简单的框

```latex
\fbox{\parbox{0.8\textwidth}{框内文字，支持多行}}
```

---

## 五、页面布局

### 1. geometry — 页边距控制

```latex
\usepackage{geometry}
\geometry{a4paper, left=2.5cm, right=2.5cm, top=2.5cm, bottom=2.5cm}
```

### 2. fancyhdr — 页眉页脚

```latex
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}  % 清空默认
\fancyhead[L]{左侧页眉}
\fancyhead[C]{中间页眉}
\fancyhead[R]{右侧页眉}
\fancyfoot[C]{\thepage}  % 页脚居中页码
\renewcommand{\headrulewidth}{0.4pt}  % 页眉横线
```

### 3. titlesec — 章节标题样式

```latex
\usepackage{titlesec}
\titleformat{\section}{\bfseries\Large}{\thesection}{1em}{}
\titleformat{\subsection}{\bfseries\large}{\thesubsection}{1em}{}
\titlespacing{\section}{0pt}{12pt}{6pt}  % 左间距、上间距、下间距
```

---

## 六、公式精细调整

### 1. amsmath — 公式基础（必加载）

```latex
\usepackage{amsmath}
% 对齐公式
\begin{align}
  f(x) &= ax^2 + bx + c \label{eq:1} \\
  g(x) &= \int_0^x f(t) dt \label{eq:2}
\end{align}
%  cases 环境
\[
f(x) = \begin{cases}
  x, & x \geq 0 \\
  -x, & x < 0
\end{cases}
\]
```

### 2. mathtools — amsmath增强

```latex
\usepackage{mathtools}  % 自动加载amsmath
% 大括号
\DeclarePairedDelimiter{\abs}{\lvert}{\rvert}
\abs{x}  % 普通
\abs*{x}  % 自动调整大小
```

### 3. 公式间距调整

```latex
% 行内公式与文字间距
\thinmuskip=3mu  % 细间距
\medmuskip=4mu   % 中间距
\thickmuskip=5mu % 粗间距

% 公式前后垂直间距
\abovedisplayskip=12pt
\belowdisplayskip=12pt
\abovedisplayshortskip=6pt
\belowdisplayshortskip=6pt
```

### 4. 公式编号控制

```latex
% 单个公式不编号
\[
  f(x) = x^2
\]
% 或
\begin{equation*}
  f(x) = x^2
\end{equation*}

% align中某行不编号
\begin{align}
  f(x) &= x^2 \nonumber \\
  g(x) &= x^3 \label{eq:2}
\end{align}
```

---

## 七、子图 / 多图

### 1. subcaption — 子图（推荐）

```latex
\usepackage{subcaption}
\begin{figure}[htbp]
  \centering
  \begin{subfigure}{0.45\textwidth}
    \centering
    \includegraphics[width=\linewidth]{fig1.png}
    \caption{子图1}
    \label{subfig:1}
  \end{subfigure}
  \hfill
  \begin{subfigure}{0.45\textwidth}
    \centering
    \includegraphics[width=\linewidth]{fig2.png}
    \caption{子图2}
    \label{subfig:2}
  \end{subfigure}
  \caption{总图题}
  \label{fig:1}
\end{figure}
% 引用：\ref{fig:1} 引用总图，\ref{subfig:1} 引用子图
```

---

## 八、算法伪代码

### 1. algorithm + algpseudocode（国赛常用）

```latex
\usepackage{algorithm}
\usepackage{algpseudocode}
\begin{algorithm}[htbp]
  \caption{算法名称}
  \label{alg:1}
  \begin{algorithmic}[1]  % [1]表示行号
    \Require 输入参数
    \Ensure 输出结果
    \State 初始化
    \For{$i = 1$ \textbf{to} $n$}
      \State 执行操作
      \If{条件}
        \State 分支1
      \Else
        \State 分支2
      \EndIf
    \EndFor
    \State \Return 结果
  \end{algorithmic}
\end{algorithm}
```

**注意事项**：
- cumcm-extras.sty 已提供 algorithm 环境和中文关键字汉化
- 正文是否放算法伪代码：自定义核心算法可放正文，标准算法放附录

---

## 九、代码高亮

### 1. listings — 代码块（附录用）

```latex
\usepackage{listings}
\usepackage{xcolor}
\lstset{
  language=Python,
  basicstyle=\ttfamily\small,
  keywordstyle=\color{blue},
  commentstyle=\color{green!50!black},
  stringstyle=\color{red},
  numbers=left,
  numberstyle=\tiny,
  frame=single,
  breaklines=true,
  showstringspaces=false
}
\begin{lstlisting}[caption=Python代码, label=code:1]
def hello():
    print("Hello World")
\end{lstlisting}
```

### 2. minted — 更美观的代码高亮（需要Pygments）

```latex
\usepackage{minted}
\begin{minted}[linenos, frame=single]{python}
def hello():
    print("Hello World")
\end{minted}
```

**注意事项**：minted 需要 `--shell-escape` 编译参数，且需安装 Pygments。数学建模论文附录代码用 listings 足够。

---

## 十、字体

### 1. fontspec — 字体设置（XeLaTeX/LuaLaTeX）

```latex
\usepackage{fontspec}
\setmainfont{Times New Roman}  % 西文字体
\setsansfont{Arial}
\setmonofont{Courier New}
```

### 2. xeCJK — 中文字体（XeLaTeX）

```latex
\usepackage{xeCJK}
\setCJKmainfont{SimSun}  % 宋体
\setCJKsansfont{SimHei}  % 黑体
\setCJKmonofont{FangSong}  % 仿宋
```

**注意事项**：国赛模板已配置好中文字体，一般不需要手动设置。

---

## 十一、颜色

### 1. xcolor — 颜色基础

```latex
\usepackage{xcolor}
% 预定义颜色
\textcolor{red}{红色文字}
\colorbox{yellow}{黄色背景}
% 自定义颜色
\definecolor{myblue}{RGB}{0, 102, 204}
\definecolor{mygray}{gray}{0.8}
% 颜色混合
blue!20  % 20%蓝色+80%白色
red!50!blue  % 50%红+50%蓝
```

---

## 十二、图形绘制

### 1. tikz — 矢量图绘制（机理/几何/流程图）

```latex
\usepackage{tikz}
\usetikzlibrary{arrows, positioning, shapes.geometric}
\begin{tikzpicture}[node distance=2cm]
  \node (start) [draw, rectangle] {开始};
  \node (process) [draw, rectangle, right=of start] {处理};
  \node (end) [draw, ellipse, right=of process] {结束};
  \draw[->] (start) -- (process);
  \draw[->] (process) -- (end);
\end{tikzpicture}
```

### 2. pgfplots — 数据图绘制

```latex
\usepackage{pgfplots}
\begin{tikzpicture}
  \begin{axis}[
    xlabel={$x$},
    ylabel={$f(x)$},
    legend pos=north west,
    grid=major
  ]
  \addplot[blue, mark=o] coordinates {
    (0, 0) (1, 1) (2, 4) (3, 9)
  };
  \addlegendentry{$f(x)=x^2$}
  \end{axis}
\end{tikzpicture}
```

**注意事项**：
- 数据图建议用 Python (matplotlib) 生成 SVG，再用 `\includesvg` 插入
- 机理/几何/流程图用 tikz 或 tikz-scientific-figures skill
- 问题分析/技术路线图用 tech-route-maker skill

---

## 十三、其他实用包

### 1. hyperref — 超链接（最后加载）

```latex
\usepackage{hyperref}
\hypersetup{
  colorlinks=true,
  linkcolor=black,    % 内部链接
  citecolor=black,    % 引用链接
  urlcolor=blue,      % URL链接
  bookmarksnumbered=true
}
```

**注意事项**：hyperref 必须在大多数包之后加载。国赛模板已配置。

### 2. caption — 图表标题样式

```latex
\usepackage{caption}
\captionsetup{
  font=small,
  labelfont=bf,
  labelsep=quad,
  justification=centering
}
```

### 3. enumitem — 列表样式

```latex
\usepackage{enumitem}
\begin{itemize}[itemsep=2pt, topsep=4pt]
  \item 项目1
  \item 项目2
\end{itemize}
```

### 4. siunitx — 单位排版

```latex
\usepackage{siunitx}
\SI{1.23}{\meter}  % 1.23 m
\SI{10}{\percent}   % 10 %
\SIrange{0}{10}{\m}  % 0–10 m
```

---

## 十四、常见问题速查

| 问题 | 解决方案 |
|------|---------|
| 图片浮动到下一页 | 用 `[htbp]` 代替 `[H]`；缩小图片；调整图片位置；加文字填充 |
| 两张图连在一起 | 在两图之间加过渡文字；用 `\clearpage` 强制分页（慎用） |
| 表格太宽超出页面 | 用 `tabularx` 的 X 列；缩小字号 `\small`；旋转表格 `sidewaystable` |
| 公式编号断裂 | 检查 `\label` 是否在 `\caption` 之后；检查是否用了 `\nonumber` |
| 参考文献不显示 | 运行 BibTeX；检查 `\cite` 键是否正确；检查 `ref.bib` 编码 |
| 中文乱码 | 用 XeLaTeX 编译；检查 `ctex` 包；检查文件编码为 UTF-8 |
| 图片不显示 | 检查路径；用 `\graphicspath` 设置图片目录；SVG 用 `--shell-escape` |
| 页面空白太多 | 检查是否有 `\clearpage`；检查浮动体参数；用 `\vspace{-10pt}` 微调（慎用） |

---

## 十五、国赛模板已加载的包

cumcm-extras.sty 已默认加载以下包，无需重复加载：
- amsmath, amssymb, mathtools
- graphicx, svg
- booktabs
- algorithm, algpseudocode（中文关键字汉化）
- hyperref
- xcolor
- geometry
- caption, subcaption
- enumitem

**使用时优先用模板已提供的快捷命令**：
- `\mat`（矩阵）、`\vb`（向量）、`\argmin`/`\argmax`
- `\topline`/`\midline`/`\bottomline`（三线表）
- `\figplot{题注}{label}{文件}{说明}`（插图）
- `\cref{fig:1}`（智能引用，输出"图1"）
