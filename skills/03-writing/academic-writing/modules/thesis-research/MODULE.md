---
name: thesis-research
version: 1.0.0
description: |
  调研员：文献调研与素材收集。可并行多个搜索任务，输出结构化综述素材和 BibTeX。
  触发词："调研"、"research"、"找文献"、"文献综述"。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Agent
  - WebSearch
  - WebFetch
  - AskUserQuestion
---

# /thesis-research -- 调研员

## 设计哲学

> 文献调研不是堆砌引用，而是理解领域脉络。
> 每篇文献都要回答三个问题：他们做了什么？和我们的区别是什么？我们可以引用什么？

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

## Step 0.5：澄清调研目标

使用 AskUserQuestion 确认：
1. 调研主题（如"你的研究领域中的某个方向"、"某类方法的最新进展"）
2. 调研范围（年份、会议/期刊、语言偏好）
3. 预期产出（补充参考文献？写综述段落？找对比基线？）
4. 数量要求（补几篇？找多少相关工作？）

---

## Step 1：规划子任务

根据目标拆分搜索维度：
- 按方法类别（如某类技术方向的不同实现路线）
- 按发表渠道（如 NeurIPS, ICML, ICLR, 自动化学报, 计算机学报）
- 按时间（如 2022-2026 近年工作）

子任务 ≥3 个时，使用 Agent 工具并行搜索。

---

## Step 2：执行搜索

对每个子任务：
1. 使用 WebSearch 搜索关键词组合
2. 对有价值的结果使用 WebFetch 获取摘要和关键信息
3. 记录：论文标题、作者、年份、发表渠道、核心方法、与本文的关系

---

## Step 3：筛选与整理

对搜索结果进行筛选：
- **高度相关**：直接解决相同或相似问题，必须引用
- **中度相关**：方法有借鉴意义，建议引用
- **低相关**：仅作背景参考，可选引用

对高度相关的文献，生成结构化卡片：

```
## [论文标题]
- 作者：XXX
- 发表：会议/期刊, 年份
- 核心方法：一句话描述
- 与本文关系：和本文方法的区别或联系
- 可引用点：本文可以在哪里引用它、引用什么内容
- BibTeX key 建议：author2024keyword
```

---

## Step 4：生成 BibTeX

为每篇推荐文献生成 BibTeX 条目，格式符合论文已有的引用风格。

---

## Step 5：输出调研报告

保存到 `$WORKSPACE/reports/` 目录，文件名含日期和主题。

```
文献调研报告 — [主题]
══════════════════════════════════════
调研时间：YYYY-MM-DD
搜索维度：N 个
找到文献：M 篇（高相关 X / 中相关 Y / 低相关 Z）
──────────────────────────────────────
[逐篇文献卡片]
──────────────────────────────────────
BibTeX 条目（可直接复制到 .bib 文件）
══════════════════════════════════════
```

---

## 注意事项

- 优先搜索已确认可靠的来源（Google Scholar、DBLP、知网）
- 中文论文搜索时注意作者姓名完整性（答辩前需去知网核实）
- 不编造不存在的论文——如果搜索结果不确定，标注"待核实"
- BibTeX 中 author 字段必须完整（不用 et al.）

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

- **DONE** -- 调研完成，报告已保存，BibTeX 已生成
- **DONE_WITH_CONCERNS** -- 部分文献信息不完整，需人工核实
- **BLOCKED** -- 搜索服务不可用
- **NEEDS_CONTEXT** -- 调研方向不明确，需作者进一步说明
