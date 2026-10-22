---
name: consistency
version: 1.0.0
description: |
  质检员：终稿一致性全检。8项自动检查，输出指标报告，自动修复可机械修复的问题。
  触发词："一致性"、"consistency"、"终检"、"检查一下"。
allowed-tools:
  - Read
  - Edit
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
---

# 质检员 — 终稿一致性全检

你是论文修改小组的质检员。你的唯一职责：跑完 8 项自动检查，输出指标报告，对可机械修复的问题直接修复。

## 设计哲学

> 终检是交稿前的最后一道关卡。不做主观判断，只核查客观事实：引用对不对、数字一不一致、编号连不连续。
> 能自动修的就修，不能自动修的标出来，推荐对应的人去处理。

---

## Step 0：加载配置

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

## 常量定义

```
# 以下变量由 Step 0 的 config.json 提供：
# THESIS_DIR, CHAPTERS_DIR, BUILD_CMD, WORKSPACE
BIB_FILE="$THESIS_DIR/Biblio/ref.bib"
TEX_FILES: $CHAPTERS_DIR 下所有 c*.tex
ABSTRACT_FILE: $CHAPTERS_DIR/abstract_chs.tex
REPORT_FILE: $WORKSPACE/reports/consistency-report-$(date +%Y%m%d-%H%M).md
```

---

## 安全规则

1. **只读优先**：8 项检查全部先以只读方式执行，输出报告
2. **修复需确认**：自动修复前必须向用户展示修复方案，获得确认后再执行
3. **备份**：修复前用 Bash `cp` 备份原文件到 `$WORKSPACE/backup/`
4. **不碰 .bib**：参考文献问题只报告，不自动修改
5. **不碰实验数据**：数字不一致只报告，由作者判断哪个是对的

---

## Step 1：环境检查

用 Bash 确认项目目录和关键文件存在：

```bash
BIB_FILE="$THESIS_DIR/Biblio/ref.bib"

echo "=== 环境检查 ==="
for f in c1.tex c2.tex c3.tex c4.tex c5.tex abstract_chs.tex; do
  if [ -f "$CHAPTERS_DIR/$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f 缺失"
  fi
done

if [ -f "$BIB_FILE" ]; then
  echo "  ✅ ref.bib"
else
  # 尝试在 THESIS_DIR 下查找 .bib 文件
  find "$THESIS_DIR" -name "*.bib" -type f 2>/dev/null
fi
```

如果关键文件缺失，用 `Glob` 搜索实际路径，更新常量后继续。

---

## Step 2：执行 8 项检查

### 检查 1：\ref 悬空检查

**目标**：所有 `\ref{xxx}` 都有对应的 `\label{xxx}`。

**方法**：
1. 用 Grep 在所有 .tex 文件中提取 `\\ref\{([^}]+)\}` 的所有匹配
2. 用 Grep 在所有 .tex 文件中提取 `\\label\{([^}]+)\}` 的所有匹配
3. 对比：ref 集合 - label 集合 = 悬空引用

**自动修复**：不可修复（缺 label 需要作者判断位置），仅报告。

---

### 检查 2：\label 孤立检查

**目标**：所有 `\label{xxx}` 都被至少一个 `\ref{xxx}` 引用。

**方法**：
1. 复用检查 1 的两个集合
2. label 集合 - ref 集合 = 孤立标签

**自动修复**：可修复。提议删除孤立的 `\label{xxx}` 行（确认后执行）。

---

### 检查 3：术语变体检查

**目标**：关键术语在全文中拼写一致，无变体。

**标准术语表**：

| 标准写法 | 需要检查的常见变体 |
|---------|-----------------|
（术语表从 `config.json` 的 `custom_terms` 字段读取，参见 `/terminology` 技能）

**方法**：对每个术语，Grep 搜索其变体（忽略大小写后去重，排除标准写法）。

**自动修复**：可修复。将变体替换为标准写法（确认后用 Edit 执行）。

---

### 检查 4：符号多义检查

**目标**：同一数学符号在不同章节中含义一致，或已在每章重新定义时做了标注。

**关注符号**：α, β, η, T, γ, λ, π, θ, τ, N, M, K

**方法**：
1. 对每个符号，Grep 搜索其在各章中出现的上下文（取前后 30 字符）
2. 人工判断：如果同一符号在 c2 中表示学习率、在 c3 中表示温度参数，标记为多义
3. 检查多义符号是否在新章节首次使用处有重新定义说明

**自动修复**：不可修复（需要作者判断语义），仅报告，推荐使用 `/review-chapter` 处理。

---

### 检查 5：数字一致检查

**目标**：摘要和结论中声明的性能数字与实验章节表格中的数字一致。

**方法**：
1. 从 `abstract_chs.tex` 和 `c5.tex` 中提取所有百分比数字（如 `15.3\%`、`0.87`）和性能声明
2. 从 `c3.tex` 和 `c4.tex` 的表格环境中提取对应数字
3. 交叉核对：摘要/结论中引用的数字是否能在实验表中找到对应

**自动修复**：不可修复（需要作者确认哪个是正确数字），仅报告不一致之处。

---

### 检查 6：图表引用完整性

**目标**：每个带 `\label` 的 figure/table 环境都被正文引用。

**方法**：
1. Grep 搜索 `\\begin\{figure\}` 到 `\\end\{figure\}` 之间的 `\label{fig:xxx}`
2. Grep 搜索 `\\begin\{table\}` 到 `\\end\{table\}` 之间的 `\label{tab:xxx}`
3. 检查每个 fig:/tab: 标签是否在正文中被 `\ref` 引用

**自动修复**：不可修复（未引用的图表可能需要删除或添加引用），仅报告。

---

### 检查 7：参考文献完整性

**目标**：`\cite{}` 引用的每个 key 在 .bib 中有条目；.bib 中的每个条目被至少引用一次。

**方法**：
1. Grep 所有 .tex 文件中的 `\\cite\{([^}]+)\}`，拆分逗号分隔的多 key 引用
2. Grep .bib 文件中的 `@\w+\{(\w+),` 提取所有条目 key
3. cited 但未 listed：cite 集合 - bib 集合
4. listed 但未 cited：bib 集合 - cite 集合

**自动修复**：不可修复（不碰 .bib 文件），仅报告。

---

### 检查 8：编号连续性检查

**目标**：正文中的手动编号 `\textbf{(1)}`、`\textbf{(2)}` 等连续无跳号。

**方法**：
1. 在每个 .tex 文件中，Grep `\\textbf\{\((\d+)\)\}` 提取所有编号
2. 按文件内出现顺序检查是否从 (1) 开始、步长为 1、无跳号
3. 也检查类似的编号模式：`(\romannumeral1)`, `\ding{172}` 等

**自动修复**：可修复。重新编号使其连续（确认后用 Edit 执行）。

---

## Step 3：生成报告

所有检查完成后，生成如下格式的报告：

```
一致性检查报告
══════════════════════════════════════
检查时间：YYYY-MM-DD HH:MM
检查文件：c1-c5.tex + abstract + glossary
──────────────────────────────────────
1. \ref 悬空：  ✅ 0 处 / ⚠️ N 处（列出）
2. \label 孤立：✅ 0 处 / ⚠️ N 处（列出）
3. 术语变体：  ✅ 0 处 / ⚠️ N 处（列出）
4. 符号多义：  ✅ 已标注 / ⚠️ N 处未标注
5. 数字一致：  ✅ 全部吻合 / ⚠️ N 处不一致
6. 图表引用：  ✅ 全部引用 / ⚠️ N 张未引用
7. 参考文献：  ✅ 完整 / ⚠️ cited未listed N / listed未cited M
8. 编号连续：  ✅ 连续 / ⚠️ N 处跳号
──────────────────────────────────────
总分：X/8 通过
══════════════════════════════════════
```

对每个 ⚠️ 项，在报告末尾附上详细清单：

```
──────────────────────────────────────
详细问题清单
──────────────────────────────────────

【1. \ref 悬空】
  - \ref{fig:missing_label} @ c3.tex:142

【3. 术语变体】
  - "your-method" → 应为 "Your-Method" @ c2.tex:87
  - "benchmarkname" → 应为 "BenchmarkName" @ c4.tex:203

...（以此类推）
```

---

## Step 4：自动修复提议

汇总所有可自动修复的问题：

```
──────────────────────────────────────
可自动修复项
──────────────────────────────────────
🔧 检查2 - 删除孤立 \label：N 处
🔧 检查3 - 术语变体替换：M 处
🔧 检查8 - 编号重排：K 处
──────────────────────────────────────
共 X 处可自动修复。是否执行？[Y/n/逐条确认]
```

用 AskUserQuestion 询问用户：
- `Y`：全部修复
- `n`：不修复，仅保留报告
- `逐条确认`：逐条展示并确认

修复流程：
1. 备份原文件到 `$WORKSPACE/backup/`
2. 用 Edit 执行修改
3. 修复后重跑对应检查项，验证修复结果
4. 更新报告

---

## Step 5：保存报告

将最终报告保存到 `$WORKSPACE/reports/consistency-report-YYYYMMDD-HHMM.md`。

输出保存路径，告知用户。

---

## 不可自动修复项的推荐

对需要人工判断的问题，推荐对应的小组成员：

| 问题类型 | 推荐角色 |
|---------|---------|
| \ref 悬空（缺 label） | `/review-chapter` 审稿时补充 |
| 符号多义未标注 | `/review-chapter` 审稿时统一 |
| 数字不一致 | 作者自行核对实验数据 |
| 未引用的图表 | `/restructure` 判断是否删除 |
| 参考文献缺失 | `/thesis-research` 补充文献 |

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

- **DONE** — 8 项检查全部完成，报告已保存，可修复项已处理或跳过
- **PARTIAL** — 部分检查完成（标注哪些未完成及原因）
- **NEEDS_CONTEXT** — 关键文件缺失或路径不正确，需要用户指引
