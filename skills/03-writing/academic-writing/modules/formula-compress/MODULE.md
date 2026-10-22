---
name: formula-compress
version: 1.0.0
description: |
  公式编辑：公式密度控制与冗余压缩。每个公式必须在后文被引用或验证，否则改为文字。
  触发词："压缩公式"、"公式太多"、"formula"、"公式密度"。
allowed-tools:
  - Read
  - Edit
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
---

# 公式编辑：公式密度控制与冗余压缩

## 设计理念

每个公式必须赢得它的位置——如果后文没有引用它、没有在实验中验证它，它就不应该以独立公式的形式存在。

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

## 步骤一：读取目标章节，统计公式

1. 从 `$CHAPTERS_DIR` 读取用户指定的章节文件。
2. 统计所有公式环境：`\begin{equation}`、`\begin{align}`、`\begin{gather}`（含带星号变体）。
3. 计算公式密度：每个 `\subsection` 内的公式数量。
4. 标记密度 >3 个公式/小节的区域为"高密度区"。

输出格式示例：

```
章节公式统计：
  3.1 问题定义        — 2 个公式 ✓
  3.2 模型架构        — 6 个公式 ⚠ 高密度
  3.3 损失函数        — 4 个公式 ⚠ 高密度
  3.4 实验设置        — 1 个公式 ✓
总计：13 个公式
```

## 步骤二：逐公式分类

对每个公式标注以下三类之一：

### CORE（核心）
- 定义方法的关键思想
- 被 `\ref` 引用，或在实验部分讨论
- **绝不删除**

### SUPPORT（辅助推导）
- 中间推导步骤
- 如果逻辑链仍然清晰，可以转化为文字描述

### REDUNDANT（冗余）
- 重复已经说过的内容
- 定义读者已知的平凡操作（如 softmax、梯度公式）
- 可以安全移除

### 内置分类判据

| 判据 | 倾向分类 |
|------|----------|
| 有 `\label` 且在其他地方被 `\ref` 引用 | → CORE |
| 出现在 3 个以上连续公式中（中间无文字）→ 中间的公式 | → SUPPORT |
| 定义标准操作（softmax、cross-entropy、L2 norm 等）读者已知 | → REDUNDANT |
| 公式结果在后续公式中被直接使用 | → CORE 或 SUPPORT |
| 公式仅出现一次，后文从未提及 | → REDUNDANT |

## 步骤三：引用链检查

对每个公式逐一检查：

1. **文本引用**：是否在正文中被 `\ref{eq:xxx}` 引用？
2. **公式引用**：其结果是否被后续公式使用？
3. **实验关联**：是否在实验章节中被讨论或验证？

三项均不满足 → 标记为"**未被引用**"。

使用 Grep 工具搜索 `\ref{对应label}` 来自动化此检查。

## 步骤四：安全检查（每次编辑前必须执行）

> **⚠ Safety Check — 编辑前必查**

在对任何公式执行操作之前，必须确认以下三项：

- [ ] **证明逻辑**：移除此公式是否会破坏证明/推导的逻辑链？
- [ ] **悬空引用**：移除后是否会导致某处 `\ref{eq:xxx}` 指向不存在的标签？
- [ ] **特殊环境**：此公式是否在 `table`、`algorithm`、`figure` 等环境内部？（如是，需额外谨慎）

任一项为"是" → **停止操作，报告给用户**，不自行决定。

## 步骤五：生成压缩方案

生成压缩计划表格，展示给用户确认：

```
| 公式标签       | 分类       | 操作              | 理由                       |
|---------------|-----------|-------------------|---------------------------|
| eq:attention  | CORE      | 保留              | 核心方法定义，实验引用        |
| eq:softmax    | REDUNDANT | 删除              | 标准操作，读者已知           |
| eq:grad_step1 | SUPPORT   | 转为行内文字        | 中间推导，可用文字描述        |
| eq:grad_step2 | SUPPORT   | 转为行内文字        | 中间推导，合并到上下文        |
| eq:loss       | CORE      | 保留              | 损失函数定义，实验核心        |
```

**必须使用 AskUserQuestion 工具请求用户确认**，等待用户批准后才执行。

## 步骤六：执行压缩

### 执行规则

1. **REDUNDANT 公式**：删除 `equation` 环境，可选地添加一句文字说明。
2. **SUPPORT 公式**：删除 `equation` 环境，改写为行内公式 `$...$` 或自然语言描述。
3. **最低保留原则**：每个 `\subsection` 至少保留"1 个主公式 + 1 个关键变体"。
4. **单次编辑不超过 30 行**。
5. **每次编辑后**，立即用 Grep 检查是否产生悬空 `\ref`。

### 转化示例

**删除冗余公式（REDUNDANT）**：
```latex
% 删除前
对注意力分数应用 softmax 归一化：
\begin{equation}
  \alpha_i = \frac{\exp(e_i)}{\sum_j \exp(e_j)}
\end{equation}

% 删除后
对注意力分数应用 softmax 归一化。
```

**转化辅助推导为文字（SUPPORT）**：
```latex
% 转化前
将式~\ref{eq:main} 代入得：
\begin{equation}
  z = W_1 x + b_1
\end{equation}
再经过激活函数：
\begin{equation}
  h = \sigma(z)
\end{equation}

% 转化后
将式~\ref{eq:main} 代入，经过线性变换 $z = W_1 x + b_1$ 和激活函数 $h = \sigma(z)$，得到隐层表示。
```

## 步骤七：验证

1. **重新统计公式数量**，展示压缩前后对比：
   ```
   压缩结果：
     压缩前：13 个公式
     压缩后：8 个公式
     减少：5 个（38.5%）
   ```

2. **检查所有 `\ref` 是否仍能解析**：用 Grep 搜索所有 `\ref{eq:...}`，确认对应 `\label` 存在。

3. **检查结构重复模式**：如果 3 个以上连续小节都呈现"定义→公式→解释"的相同结构，标记为"结构重复"，建议用户调整行文节奏。

## 安全规则

1. **不破坏证明链**：如果一组公式构成完整推导，不得仅删除中间步骤而不补充文字衔接。
2. **不触碰 `\label` 内部命名**：不重命名任何 `\label{eq:xxx}`，只决定保留或删除整个公式环境。
3. **不修改 CORE 公式的数学内容**：CORE 公式只能保留原样，不改写其数学表达。
4. **算法环境内公式加倍谨慎**：`algorithm`、`algorithmic` 环境内的公式默认视为 CORE，除非用户明确要求。
5. **表格内公式不自动处理**：`table`、`tabular` 环境内的公式跳过，报告给用户手动处理。

## 收尾协议（完成后必须执行）

每次 skill 执行完毕后，无论结果如何，必须执行以下四步：

**0. 编译验证（修改 tex 文件后必须执行）**
- 进入论文工程目录：`cd "$THESIS_DIR"`
- 执行编译：`$BUILD_CMD`
- 检查编译结果：0 errors = 通过，有 error = 立即定位修复
- 记录编译状态到进度文件

**2. 更新问题清单 `$WORKSPACE/issues.md`**
- 本次发现的新问题：追加到"待处理"区，格式为 `- [ ] **编号** 位置 — 问题描述 → 建议skill`
- 本次解决的问题：从"待处理"移到"已解决"，标注完成时间
- 未变化的问题：不动

**3. 更新进度文件 `$WORKSPACE/progress.md`**
- 在"完成记录"区追加一行：`- YYYY-MM-DD HH:MM /skill名 — 执行摘要（N项修改/N个问题）`
- 如果任务看板中有对应任务项，更新其状态（勾选 `[x]`）

**4. 保存报告（如有输出）**
- 报告保存到 `$WORKSPACE/reports/` 目录
- 文件名格式：`YYYYMMDD-skill名-目标.md`（如 `20260322-review-chapter-c4.md`）

---

## 完成状态协议

任务完成时，输出以下摘要：

```
═══ 公式压缩完成 ═══
目标文件：[文件路径]
压缩前公式数：[N]
压缩后公式数：[M]
减少：[N-M] 个（[百分比]%）
悬空引用检查：通过 / 发现 [K] 处问题
结构重复检查：无重复 / 发现 [K] 处重复模式
════════════════════
```
