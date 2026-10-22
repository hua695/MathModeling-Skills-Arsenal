---
name: terminology
version: 1.0.0
description: |
  术语官：全文术语一致性巡检与统一。扫描所有章节，建立术语表，检测冲突，一次性统一。
  触发词："术语"、"terminology"、"命名统一"、"术语检查"。
allowed-tools:
  - Read
  - Edit
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
---

# 术语官（Terminology Guardian）

全文术语一致性巡检与统一工具。遵循 guard 模式：全局守护 + 钩子式校验。

---

## 安全规则

1. **绝不触碰引用内部**：`\label{}`、`\ref{}`、`\cite{}` 内部内容严禁修改
2. **逐条替换**：每次替换后立即验证，确保不破坏 LaTeX 编译
3. **存疑必问**：遇到无法自动判断的冲突，必须通过 AskUserQuestion 询问作者
4. **备份优先**：替换前记录所有变更，便于回滚
5. **不擅自造词**：所有标准术语以作者确认为准，不自行发明新译名
6. **不改语义**：仅统一术语拼写和格式，不改变原文语义

---

## 术语表来源

术语表从 `config.json` 的 `custom_terms` 字段读取。如果 `custom_terms` 为空或不存在，则在首次运行时通过交互式问答（AskUserQuestion）与作者建立术语表。

建立后的术语表会保存回 `config.json`，供后续运行复用。

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

## 执行步骤

### 第一步：扫描全部章节

扫描 `$CHAPTERS_DIR` 下所有 `.tex` 文件，以及 `$THESIS_DIR` 下的摘要和术语表文件，提取全文术语信息。

**操作方式：**

1. 使用 Glob 定位 `$CHAPTERS_DIR/*.tex` 和 `$THESIS_DIR` 下的摘要文件
2. 使用 Read 逐一读取每个文件
3. 使用 Grep 搜索所有内置术语表中的术语及其可能的变体拼写
4. 同时搜索常见的术语引入模式：`（`...`）`括注、`\textbf{}`、`\emph{}`、首字母大写缩写词

### 第二步：建立术语表

对每一个检测到的术语，记录以下字段：

| 字段 | 说明 |
|------|------|
| 标准名称 | 确定的规范写法 |
| 中文全称 | 中文正式名称 |
| 英文全称 | 英文正式名称 |
| 缩写 | 标准缩写形式 |
| 首次出现位置 | `文件名:行号` |
| 全文出现次数 | 在所有文件中的总出现次数 |
| 变体列表 | 检测到的所有不同拼写形式 |

**输出格式**：以 Markdown 表格形式展示完整术语表。

### 第三步：冲突检测

检测以下三类冲突：

#### 3.1 同一概念、不同拼写

同一术语在不同位置出现了不同的拼写方式。例如：
- `Multi-Head Attention` vs `multi-head attention` vs `Multi-head Attention`
- `OpenAI Gym` vs `OpenAi Gym` vs `openai gym`
- `DeepMind Lab` vs `Deepmind Lab` vs `DeepMind-Lab`

#### 3.2 同一缩写、不同含义

同一个符号或缩写在不同章节中代表不同含义。例如：
- `α`：在第二章（c2.tex）中表示某个超参数，在第四章（c4.tex）中表示另一个系数
- 检查所有希腊字母和单字母变量的语义一致性

#### 3.3 重复括注定义

术语缩写在某一章（如 c1.tex）已经首次定义，但在后续章节（如 c3.tex）中又重新给出了完整英文括注。规则：
- 全文首次出现时必须给出完整定义（中文名称（English Full Name, ABBR））
- 后续出现直接使用缩写即可，无需重复括注
- 但每章首次出现时可以简短提示（如直接用缩写），不需要再写全称

**输出格式**：将所有冲突分类列出，标明文件名、行号和具体内容。

### 第四步：询问作者确认

对于检测到的冲突，通过 AskUserQuestion 询问作者：

1. 将所有冲突分组展示
2. 对每组冲突提供推荐的标准形式
3. 让作者逐一确认或修改
4. 记录作者的最终决定

**询问格式示例：**

```
检测到以下术语冲突，请确认标准形式：

冲突 1：Multi-Head Attention 的拼写
  - c2.tex:42  → "multi-head attention"
  - c3.tex:18  → "Multi-Head Attention"
  - c4.tex:95  → "Multi-head Attention"
  推荐标准形式：Multi-Head Attention（连字符连接，首字母大写）
  请确认 [Y/修改为其他形式]：
```

### 第五步：全局替换

根据作者确认的标准形式，执行全局替换：

**替换规则：**

1. 使用 Grep 定位所有需要替换的位置
2. 使用 Edit 逐一替换（不使用正则批量替换，避免误伤）
3. **严格排除**：`\label{}`、`\ref{}`、`\cite{}` 内部内容不做任何修改
4. 替换完成后，使用 Grep 验证：
   - 所有变体已消除（搜索结果为零）
   - 标准形式正确存在于预期位置

**排除模式**（正则）：

```
\\label\{[^}]*\}
\\ref\{[^}]*\}
\\cite\{[^}]*\}
\\cref\{[^}]*\}
\\eqref\{[^}]*\}
```

### 第六步：生成术语报告

替换完成后，输出最终术语报告：

```
═══════════════════════════════════════════
        术语一致性巡检报告
═══════════════════════════════════════════

扫描文件数：X
检测术语数：X
发现冲突数：X
已修复冲突：X
作者确认项：X

───────────────────────────────────────────
术语表（最终版）
───────────────────────────────────────────

| 标准名称 | 中文全称 | 英文全称 | 缩写 | 首次出现 | 出现次数 |
|----------|----------|----------|------|----------|----------|
| ...      | ...      | ...      | ...  | ...      | ...      |

───────────────────────────────────────────
修复记录
───────────────────────────────────────────

1. [文件:行号] "旧写法" → "新写法"
2. ...

═══════════════════════════════════════════
```

### 第七步：验证

1. **编译验证**：使用 Bash 运行 `$BUILD_CMD` 编译论文，确保无编译错误
2. **二次扫描**：重新执行第一步至第三步，确认零冲突
3. **报告最终状态**

---

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

任务完成时，输出以下状态摘要：

```
✅ 术语巡检完成
   - 扫描文件：X 个
   - 检测术语：X 个
   - 修复冲突：X 处
   - 编译状态：通过 / 失败
   - 剩余冲突：0
```

如果存在未解决的问题：

```
⚠️ 术语巡检完成（有遗留项）
   - 扫描文件：X 个
   - 检测术语：X 个
   - 修复冲突：X 处
   - 未解决项：X 处（需作者后续确认）
   - 编译状态：通过 / 失败
```

---

## 注意事项

- 本技能为**只读优先**模式：先完成全部扫描和分析，经作者确认后才执行修改
- 所有修改均通过 Edit 工具逐条执行，便于追踪和回滚
- 若论文中新增了章节文件，需手动将文件名加入第一步的扫描列表
- 术语表可作为后续写作的参考标准，建议保存到 `glossary.tex` 中
