---
name: tidy
version: 1.0.0
description: |
  整理员：工作区文件归类整理。移动前分析依赖关系，确保不破坏引用路径。
  触发词："整理"、"tidy"、"收拾一下"、"文件太乱了"。
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
---

# 整理员（tidy）

工作区文件归类整理技能，遵循 gstack `/careful` 模式：先安全检查 + 依赖分析，再执行移动。

## 触发条件

用户提到以下任意关键词时激活本技能：
- "整理"、"tidy"、"收拾一下"、"文件太乱了"、"归类"、"清理工作区"

## 安全规则（铁律，不可违反）

1. **绝不移动**以下目录：`.claude/`、`.thesis/`、`$THESIS_DIR` 所在目录、`$WORKSPACE/reports/`
2. **绝不删除**任何文件——只做移动操作
3. **移动前必须确认**——通过 `AskUserQuestion` 获得用户批准
4. **每次移动后验证**——检查依赖是否完整

## 执行步骤

### Step 0：加载配置

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

如果 preamble 输出 ERROR，立即停止并提示用户运行 /thesis-init。

---

### 第一步：扫描工作区

列出 `$WORKSPACE` 根目录下所有文件，按类型分类：

| 分类 | 典型扩展名 | 示例 |
|------|-----------|------|
| Python 脚本 | `.py` | 数据处理、绘图脚本 |
| 图片文件 | `.png`, `.jpg`, `.svg`, `.pdf`（非论文主PDF） | 实验结果图、示意图 |
| PDF 文档 | `.pdf` | 参考文献、草稿快照 |
| 压缩包 | `.zip`, `.tar.gz`, `.rar` | 数据包、备份 |
| 数据文件 | `.csv`, `.xlsx`, `.json`, `.mat` | 实验数据 |
| 文档 | `.md`, `.txt`, `.docx` | 笔记、草稿 |
| 其他 | 无法归类的文件 | 逐个判断 |

使用 Glob 扫描根目录文件，使用 `ls -la` 获取详细信息。

### 第二步：依赖分析

这是整个流程最关键的步骤。在移动任何文件之前，必须建立完整的依赖关系图。

**扫描范围：**
- 所有 `.tex` 文件：搜索 `\includegraphics`、`\input`、`\include`、`\bibliography` 等引用命令
- 所有 `.py` 文件：搜索 `open()`、`pd.read_csv()`、`plt.savefig()`、路径字符串等
- 所有 `.bib` 文件：检查是否被 `.tex` 引用
- `Makefile` / `latexmkrc`：检查构建脚本中的路径引用

**输出依赖图格式：**

```
依赖关系图：
  data.csv
    ← 被引用于：process.py (第 12 行)
    ← 被引用于：analyze.py (第 45 行)
  figure1.png
    ← 被引用于：$CHAPTERS_DIR/ch3.tex (第 88 行)
  helper.py
    ← 无外部引用（安全移动）
```

### 第三步：制定整理方案

根据扫描和依赖分析结果，提出目标目录结构：

```
$WORKSPACE/
├── $THESIS_DIR 所在目录  （不动）
├── .thesis/              （不动）
├── .claude/              （不动）
├── scripts/              ← Python 脚本归入此处
├── figures/              ← 图片文件归入此处
├── snapshots/            ← PDF 快照、阶段性产出归入此处
├── archive/              ← 压缩包、旧版本归入此处
└── data/                 ← 数据文件归入此处（如有需要）
```

对每个待移动文件，标注：
- 原路径
- 目标路径
- 依赖状态（无引用 / 有引用需更新 / 有引用但路径不受影响）

### 第四步：用户确认

使用 `AskUserQuestion` 向用户展示完整的整理方案，等待确认。

展示内容包括：
- 待移动文件清单及目标位置
- 需要更新的引用路径列表
- 不会移动的文件及原因

用户可以：
- 批准全部
- 排除特定文件
- 修改目标目录

**未获得用户明确批准前，不执行任何移动操作。**

### 第五步：逐一执行移动

按以下顺序执行：

1. 先创建目标目录（如不存在）
2. 移动无依赖的文件（最安全）
3. 移动有依赖的文件，移动后立即更新引用

每次移动使用 `mv` 命令，并在移动后验证：
- 文件确实到达目标位置
- 原位置不再存在该文件

### 第六步：更新引用路径

如果被移动的文件在 `.py` 脚本中被引用，更新脚本中的路径。

更新策略：
- 找到引用该文件的所有位置
- 将旧路径替换为新的相对路径或绝对路径
- 保持路径风格与原脚本一致（相对路径用相对路径替换，绝对路径用绝对路径替换）

**注意：`.tex` 文件中的路径通常相对于 `$THESIS_DIR`，如果图片从根目录移到 `figures/`，需要确认 `.tex` 中的 `graphicspath` 设置是否覆盖新位置。**

### 第七步：验证完整性

执行两项验证：

1. **LaTeX 编译验证**：运行一次编译，确认没有引用断裂
   ```bash
   cd "$THESIS_DIR" && $BUILD_CMD
   ```
   检查日志中是否出现新的文件未找到错误。

2. **Python 脚本验证**：对更新了路径的 `.py` 脚本，运行语法检查
   ```bash
   python3 -c "import py_compile; py_compile.compile('<脚本路径>', doraise=True)"
   ```

### 第八步：输出整理报告

```
══════════════════════════════════════
  整理报告
══════════════════════════════════════
  移动文件数：XX 个
  更新引用数：XX 处
  新建目录数：XX 个
  编译验证：  通过 / 失败
══════════════════════════════════════

  移动明细：
    原位置                  →  新位置
    ./process.py            →  ./scripts/process.py
    ./figure1.png           →  ./figures/figure1.png
    ...

  引用更新明细：
    scripts/process.py 第 12 行：
      旧：open("data.csv")
      新：open("../data/data.csv")
══════════════════════════════════════
```

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

## 完成状态协议

任务完成时，输出以下结构化状态块：

```
[tidy] 完成
  结果：成功 / 部分完成 / 回滚
  移动：XX 个文件
  更新：XX 处引用
  验证：编译通过 / 编译失败（需人工检查）
  下一步建议：<基于当前状态的建议>
```

若编译验证失败，建议用户手动检查并考虑回滚（文件移回原位）。
若全部通过，建议运行一次完整编译确认论文输出正常。
若部分文件未移动（用户排除），列出剩余待整理文件供后续处理。
