---
name: review-chapter
version: 1.0.0
description: |
  审稿人：模拟导师视角深度审阅论文章节，两遍审查，分级输出问题。
  触发词："审阅"、"review"、"导师看看"、"检查第X章"。
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
---

# review-chapter — 审稿人

> 设计哲学：好的中文学术论文读起来像一个人在认真讲一件事，内容铺开、论证扎实、一气呵成。

本技能模拟一位严格但建设性的论文导师，对指定章节进行两遍深度审阅，输出分级问题报告。

---

## 安全规则

- **只读模式**：本技能绝不修改任何 `.tex` 文件，仅输出审阅报告。
- 所有文件操作限于 Read / Grep / Glob，不执行写入。
- 修改建议通过报告末尾的"后续动作"推荐其他技能完成。

---

## 流程

### Step 0 — 加载配置

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

### Step 0.5 — 确定审阅目标

1. 若用户未明确指定章节，使用 **AskUserQuestion** 询问：
   > 请问要审阅哪一章？（c1–c6，或输入文件名）
2. 根据回答，从 `$CHAPTERS_DIR` 读取对应 `.tex` 文件：
   ```
   $CHAPTERS_DIR/cX.tex
   ```
3. 使用 **Read** 完整读取该文件内容，记录总行数。

---

### Step 1 — Pass 1: CRITICAL（结构与逻辑）

逐条检查以下 5 项内建审查标准，直接基于文件内容判断，不依赖外部规则文件：

| # | 检查项 | 说明 |
|---|--------|------|
| C1 | **章节逻辑链** | 全章是否遵循"问题 → 方法 → 实验 → 结论"的叙事主线。检查 `\section` 层级的排布顺序，标记逻辑跳跃或缺失环节。 |
| C2 | **图表引用完整性** | 扫描所有 `\begin{figure}` / `\begin{table}` 的 `\label`，确认每一个 label 在正文中都有对应的 `\ref` 引述**且**在引述附近有实质性讨论（不只是"如图X所示"）。 |
| C3 | **公式引用链** | 扫描所有 `\begin{equation}` / `\begin{align}` 的 `\label`，确认每个公式在后续正文中被使用、引用或验证。孤立公式（定义后从未提及）标记为 CRITICAL。 |
| C4 | **段落完整性** | 检测不足 3 句的超短段落（排除列表项和标题后的过渡句）。学术段落应充分展开论述。 |
| C5 | **技术叙述顺序** | 检查是否存在"先抛结论后补动机"的倒叙写法。正确顺序：先阐述问题/挑战，再引出解决方案。 |

**判定方式**：
- 使用 Grep 搜索 `\label`、`\ref`、`\section`、`\begin{figure}`、`\begin{table}`、`\begin{equation}` 等 LaTeX 标记。
- 使用 Read 按行检查段落长度和叙事顺序。
- 每个问题记录具体行号。

---

### Step 2 — Pass 2: INFORMATIONAL（表达与规范）

逐条检查以下 5 项内建审查标准：

| # | 检查项 | 说明 |
|---|--------|------|
| I1 | **AI 痕迹初筛** | 检测程式化衔接词密度（"值得注意的是"、"综上所述"、"本文提出了一种"等高频模板句）、句式骨架重复（连续段落以相同句型开头）、模板化总结句。 |
| I2 | **括号注释堆砌** | 同一段落内出现多个"中文（English, ABBR）"格式的括号注释。首次出现合理，密集堆砌影响可读性。 |
| I3 | **小标题碎片化** | 连续子节（`\subsection` 或 `\subsubsection`）各不足 15 行正文。碎片化子节应合并或扩充。 |
| I4 | **实验分析深度** | 实验结果部分是否只罗列数字/表格而缺乏原因分析、对比解释、失败案例讨论。 |
| I5 | **段落间过渡** | 检测相邻段落之间是否存在语义断裂——前段结论与后段开头缺乏逻辑衔接。 |

**判定方式**：
- I1: Grep 搜索常见 AI 套话关键词，统计密度。
- I2: Grep 搜索中文括号 + 英文模式，按段落聚合计数。
- I3: 计算相邻 `\subsection` / `\subsubsection` 之间的行数。
- I4: 在实验章节中检查是否存在分析性语句（"原因是"、"这表明"、"相比之下"等）。
- I5: 人工判读段落衔接，标记明显断裂处。

---

### Step 3 — 输出审阅报告

按以下固定格式输出报告：

```
审阅报告 — cX.tex
══════════════════════════════════════
总体评分：X/10
CRITICAL: N 项  |  INFORMATIONAL: M 项
──────────────────────────────────────

[CRITICAL] 行 XX–YY: 问题描述
  → 建议：具体修改建议
  → 分类：AUTO-FIX / ASK

[CRITICAL] 行 XX: 问题描述
  → 建议：具体修改建议
  → 分类：AUTO-FIX / ASK

──────────────────────────────────────

[INFORMATIONAL] 行 YY: 问题描述
  → 建议：具体修改建议
  → 分类：AUTO-FIX / ASK

[INFORMATIONAL] 行 YY–ZZ: 问题描述
  → 建议：具体修改建议
  → 分类：AUTO-FIX / ASK
```

**评分标准**：
- 10/10: 无 CRITICAL，INFORMATIONAL <= 2
- 8–9/10: 无 CRITICAL，少量 INFORMATIONAL
- 6–7/10: 1–2 个 CRITICAL
- 4–5/10: 3+ 个 CRITICAL
- <4/10: 严重结构性问题

**分类说明**：
- **AUTO-FIX**：明确、机械性的修改（如补 `\ref`、合并超短段落），可由其他技能自动处理。
- **ASK**：涉及学术判断的修改（如调整论证顺序、补充实验分析），需与作者确认。

---

### Step 4 — Fix-First 后续动作建议

报告末尾附"后续动作"板块：

```
══════════════════════════════════════
后续动作
──────────────────────────────────────
AUTO-FIX 项（可直接处理）：
  1. [问题摘要] → 建议调用 /deai 处理 AI 痕迹问题
  2. [问题摘要] → 建议调用 /restructure 处理结构碎片化
  3. [问题摘要] → 可手动快速修复

ASK 项（需作者确认）：
  1. [问题摘要] → 需要你决定：[具体选项]
══════════════════════════════════════
```

- 本技能**不执行任何编辑**，仅推荐后续动作和对应技能。
- ASK 项使用 **AskUserQuestion** 逐项确认作者意图，记录回答供后续技能使用。

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

## 完成状态协议

任务结束时，输出以下状态之一：

| 状态 | 含义 |
|------|------|
| `DONE` | 审阅完成，所有问题已列出，无阻塞项。 |
| `DONE_WITH_CONCERNS` | 审阅完成，但发现严重结构性问题，强烈建议修改后再提交。 |
| `BLOCKED` | 无法完成审阅（如文件不存在、内容为空、编码异常）。 |
| `NEEDS_CONTEXT` | 缺少必要上下文（如需要参考其他章节才能判断逻辑链完整性）。 |

---

## 示例调用

用户输入：
- "审阅第三章"
- "/review-chapter c3"
- "导师看看 c5"
- "检查第四章"

均触发本技能，进入 Step 0 确认目标后执行两遍审查。
