---
name: thesis-init
version: 1.0.0
description: |
  初始化论文修改工作区。选择论文目录、配置编译命令、创建进度追踪文件夹。
  首次使用论文修改小组前必须运行。
  触发词："thesis-init"、"初始化论文"、"配置论文项目"。
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# /thesis-init — 论文项目初始化

## 设计哲学

> 论文修改小组是一套通用工具，适用于任何中文 LaTeX 学位论文。
> 初始化流程让每个用户配置自己的项目环境，所有 skill 从配置文件读取路径，不硬编码。

---

## Step 1：检测当前环境

首先检查当前工作目录是否已经初始化过：

```bash
if [ -f ".thesis/config.json" ]; then
  echo "ALREADY_INITIALIZED"
  cat .thesis/config.json
else
  echo "NOT_INITIALIZED"
  echo "CWD: $(pwd)"
fi
```

如果已初始化，展示当前配置并询问是否要重新配置。

---

## Step 2：选择论文工程目录

使用 AskUserQuestion：

> 请指定你的 LaTeX 论文工程目录（包含 main.tex 的目录）。

选项：
- A) 当前目录就是论文工程（检测到 main.tex）
- B) 当前目录的子目录（列出包含 .tex 文件的子目录供选择）
- C) 手动输入路径

验证：检查指定目录下是否存在 `main.tex`。如果不存在，提示用户确认。

---

## Step 3：检测论文结构

自动扫描论文工程目录，检测：

```bash
THESIS_DIR="<用户选择的目录>"

# 检测 main.tex
[ -f "$THESIS_DIR/main.tex" ] && echo "MAIN_TEX: found" || echo "MAIN_TEX: missing"

# 检测章节文件
echo "CHAPTERS:"
find "$THESIS_DIR" -name "c*.tex" -o -name "chapter*.tex" | sort

# 检测图片目录
for d in Figures figures images imgs fig; do
  [ -d "$THESIS_DIR/$d" ] && echo "FIGURES_DIR: $THESIS_DIR/$d"
done

# 检测参考文献
find "$THESIS_DIR" -name "*.bib" | head -5

# 检测编译系统
which latexmk >/dev/null 2>&1 && echo "LATEXMK: available" || echo "LATEXMK: not found"
which xelatex >/dev/null 2>&1 && echo "XELATEX: available" || echo "XELATEX: not found"
```

---

## Step 4：配置编译命令

使用 AskUserQuestion：

> 你的论文用什么方式编译？

选项：
- A) latexmk + xelatex（推荐，适用于大多数中文论文）
- B) latexmk + pdflatex
- C) 直接 xelatex（手动多次编译）
- D) 自定义编译命令

对于选项 A，生成命令：
```
PATH="/Library/TeX/texbin:$PATH" latexmk -xelatex -interaction=nonstopmode -f -g main.tex
```

如果是 Linux 系统（检测 `uname`），去掉 PATH 前缀。

---

## Step 5：创建工作区

在当前工作目录（论文项目的父目录或项目目录本身）创建 `.thesis/` 工作区：

```
.thesis/
├── config.json       # 核心配置文件
├── progress.md       # 进度追踪
├── issues.md         # 问题清单（首次审阅后填充）
└── reports/          # 各 skill 输出的报告存放处
```

---

## Step 6：生成 config.json

```json
{
  "version": "1.0.0",
  "initialized_at": "2026-03-22T22:30:00Z",
  "thesis_dir": "<论文工程绝对路径>",
  "workspace_dir": "<.thesis 目录绝对路径>",
  "main_tex": "main.tex",
  "chapters_dir": "<章节文件所在子目录，如 Main_Spine/>",
  "chapters": ["c1.tex", "c2.tex", "c3.tex", "c4.tex", "c5.tex"],
  "figures_dir": "<图片目录>",
  "bib_file": "<.bib 文件路径>",
  "build_command": "<编译命令>",
  "platform": "<darwin/linux>",
  "abstract_files": {
    "chinese": "<中文摘要文件路径，如 Main_Miscellaneous/abstract_chs.tex>",
    "english": "<英文摘要文件路径>"
  },
  "glossary_file": "<术语表文件路径，如 Main_Miscellaneous/glossary.tex>",
  "custom_terms": []
}
```

字段说明：
- `thesis_dir`：论文工程根目录（包含 main.tex）
- `workspace_dir`：.thesis 工作区目录
- `chapters_dir`：章节 tex 文件所在的相对子目录
- `chapters`：自动检测到的章节文件名列表
- `build_command`：编译命令（含 PATH 前缀）
- `custom_terms`：用户自定义术语表（`/terminology` 用，初始为空，后续通过 `/terminology` 填充）

---

## Step 7：生成 progress.md

```markdown
# 论文修改进度

> 初始化时间：<时间>
> 论文目录：<路径>
> 章节数：<N>

## 任务看板

（运行 `/review-chapter` 审阅后自动填充）

## 完成记录

（每个 skill 完成后自动追加）
```

---

## Step 8：生成 issues.md

```markdown
# 论文问题清单

> 本文件由各 skill 自动维护，也可手动编辑。
> 运行 `/review-chapter` 后自动填充问题。

## 待处理

（空）

## 已解决

（空）
```

---

## Step 9：验证配置

1. 尝试读取 `config.json` 中的 `thesis_dir`，确认目录存在
2. 尝试读取第一个章节文件，确认可访问
3. 尝试运行编译命令（dry-run 或实际编译），确认编译环境可用

---

## Step 10：输出初始化摘要

```
论文项目初始化完成
══════════════════════════════════════
论文目录：<路径>
章节文件：<N> 个（c1.tex ~ cN.tex）
编译命令：<命令>
工作区：.thesis/
──────────────────────────────────────
✅ config.json — 已生成
✅ progress.md — 已生成
✅ issues.md — 已生成
✅ reports/ — 已创建
──────────────────────────────────────
下一步建议：
  /review-chapter — 先审阅一个章节，生成问题清单
  /thesis — 查看全局状态
══════════════════════════════════════
```

---

## 其他 Skill 如何读取配置

所有 skill 的 Step 0 都应包含以下 preamble：

```bash
# 论文修改小组 — 配置加载
CONFIG=""
for candidate in ".thesis/config.json" "../.thesis/config.json" "../../.thesis/config.json"; do
  if [ -f "$candidate" ]; then
    CONFIG="$(cd "$(dirname "$candidate")" && pwd)/$(basename "$candidate")"
    break
  fi
done

if [ -z "$CONFIG" ]; then
  echo "ERROR: 未找到 .thesis/config.json"
  echo "请先运行 /thesis-init 初始化论文项目"
  exit 1
fi

echo "CONFIG: $CONFIG"
THESIS_DIR=$(python3 -c "import json; print(json.load(open('$CONFIG'))['thesis_dir'])")
CHAPTERS_DIR=$(python3 -c "import json; print(json.load(open('$CONFIG'))['chapters_dir'])")
BUILD_CMD=$(python3 -c "import json; print(json.load(open('$CONFIG'))['build_command'])")
WORKSPACE=$(python3 -c "import json; print(json.load(open('$CONFIG'))['workspace_dir'])")
echo "THESIS_DIR: $THESIS_DIR"
echo "CHAPTERS_DIR: $CHAPTERS_DIR"
echo "WORKSPACE: $WORKSPACE"
```

如果 preamble 输出 `ERROR: 未找到 .thesis/config.json`，该 skill 应立即停止并提示用户运行 `/thesis-init`。

---

## 收尾协议（完成后必须执行）

每次 skill 执行完毕后，无论结果如何，必须执行以下三步：

**1. 更新问题清单 `$WORKSPACE/issues.md`**
- 本次发现的新问题：追加到"待处理"区，格式为 `- [ ] **编号** 位置 — 问题描述 → 建议skill`
- 本次解决的问题：从"待处理"移到"已解决"，标注完成时间
- 未变化的问题：不动

**2. 更新进度文件 `$WORKSPACE/progress.md`**
- 在"完成记录"区追加一行：`- YYYY-MM-DD HH:MM /skill名 — 执行摘要（N项修改/N个问题）`
- 如果任务看板中有对应任务项，更新其状态（勾选 `[x]`）

**3. 保存报告（如有输出）**
- 报告保存到 `$WORKSPACE/reports/` 目录
- 文件名格式：`YYYYMMDD-skill名-目标.md`（如 `20260322-review-chapter-c4.md`）

---

## Completion Status

- **DONE** — 初始化完成，配置文件已生成，编译验证通过
- **DONE_WITH_CONCERNS** — 初始化完成但编译环境未验证（缺少 latexmk 等）
- **BLOCKED** — 找不到 main.tex 或论文目录不存在
- **NEEDS_CONTEXT** — 需要用户指定论文目录或编译方式
