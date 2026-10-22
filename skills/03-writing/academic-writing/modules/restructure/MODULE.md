---
name: restructure
version: 1.0.0
description: |
  结构师：章节结构诊断与重组。先诊断后动手，Scope Lock 防止误碰其他章。
  触发词："重组"、"restructure"、"调整结构"、"合并小节"。
allowed-tools:
  - Read
  - Edit
  - Write
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
---

# 结构师（restructure）

> 好的中文学术论文读起来像一个人在认真讲一件事，内容铺开、论证扎实、一气呵成。

本技能用于诊断和重组论文章节结构。严格遵循"先诊断后动手"的铁律，通过 Scope Lock 确保只修改目标章节文件。

---

## 安全规则

1. **铁律（Iron Law）**：必须完成诊断阶段并获得用户确认后，才能进行任何编辑操作。绝不跳过诊断直接动手。
2. **Scope Lock**：只编辑用户指定的目标章节 `.tex` 文件。不修改其他章节、主文件、宏包文件或参考文献文件。
3. **单次编辑 ≤30 行**：每次 Edit 操作不超过 30 行，便于用户审查和回退。
4. **标签安全**：移动内容块时，同步迁移所有 `\label` 和 `\ref`，不得产生悬空引用。
5. **备份意识**：实施前提醒用户确认 git 状态或手动备份。
6. **不删内容**：重组只调整位置和层级，不删除用户撰写的正文内容。合并小节时保留所有段落。

---

## Step 0 — 加载配置

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

## Phase 1 — 诊断（Investigate）

### 步骤

1. 用 `Read` 读取 `$CHAPTERS_DIR` 下目标章节 `.tex` 文件全文。
2. 用 `Grep` 提取结构命令，构建结构树：
   - 提取所有 `\chapter`、`\section`、`\subsection` 及其行号。
   - 计算每个结构单元的行数（从当前标题到下一个同级或更高级标题之间的行数）。
3. 输出结构树，格式如下：

```
结构树：chapters/chap03.tex
────────────────────────────────
L12   \chapter{系统设计}
L15   ├── \section{总体架构}                    [45 行]
L18   │   ├── \subsection{设计目标}             [12 行] ⚠ 碎片化
L30   │   ├── \subsection{技术选型}             [10 行] ⚠ 碎片化
L40   │   └── \subsection{架构概览}             [23 行]
L63   ├── \section{模块设计}                    [120 行]
L65   │   ├── \subsection{数据采集模块}         [85 行]
L150  │   └── \subsection{处理模块}             [35 行] ⚠ 节间失衡
L185  └── \section{小结}                        [5 行]
```

4. 逐项检查以下问题：

| 问题类型     | 检测规则                                               | 标记   |
|-------------|-------------------------------------------------------|--------|
| 碎片化       | 连续子节各 <15 行                                      | ⚠ 碎片化 |
| 层级过深     | `\subsection` 内部出现手工编号 `\textbf{(N)}` 作为段落标题 | ⚠ 层级过深 |
| 逻辑断裂     | 前一节末尾结论与后一节开头语义不连贯                       | ⚠ 逻辑断裂 |
| 节间失衡     | 同层级小节行数差异 >3 倍                                 | ⚠ 节间失衡 |

5. 输出诊断报告，列出所有发现的问题及其位置。

---

## Phase 2 — 分析（Analyze）

### 良好结构的内建标准

- 每个 `\section` 下包含 **2–4 个** `\subsection`。
- 每个 `\subsection` 至少 **20–30 行**（约一页正文）。
- 层级不超过三层：`\chapter` → `\section` → `\subsection`。
- 手工编号 `\textbf{(1)}` 等只用于**短列表**（如 3–5 个要点），不用于段落标题。

### 对每个问题的分析说明

针对 Phase 1 发现的每个问题，向用户解释：

- **碎片化**：连续出现多个不足 15 行的小节，读起来像幻灯片提纲而非论文。读者刚进入一个话题就被切断，无法形成连贯理解。应合并为一个完整小节，内容自然展开。
- **层级过深**：`\subsection` 下再用 `\textbf{(N)}` 造出第四层结构，说明该 subsection 承载了过多内容，应拆分为多个 subsection，或将手工编号改为段内列表。
- **逻辑断裂**：前一节结尾与后一节开头之间缺乏衔接，读者需要自行脑补过渡。应补写过渡段落，说明"上一节做了什么，本节要解决什么"。
- **节间失衡**：同层级小节中某节 85 行、另一节 10 行，说明内容划分不合理。短节可能需要并入相邻节，或者长节需要进一步拆分。

---

## Phase 3 — 方案（Hypothesize）

### 步骤

1. 基于 Phase 2 的分析，生成重组方案。
2. 以"旧结构树 → 新结构树"的对比形式展示：

```
【旧结构】                              【新结构】
├── \section{总体架构}                  ├── \section{总体架构}
│   ├── \subsection{设计目标}  [12行]   │   ├── \subsection{设计目标与技术选型} [合并]
│   ├── \subsection{技术选型}  [10行]   │   └── \subsection{架构概览}
│   └── \subsection{架构概览}  [23行]   │
├── \section{模块设计}                  ├── \section{模块设计}
│   ├── \subsection{数据采集}  [85行]   │   ├── \subsection{数据采集模块}
│   └── \subsection{处理模块}  [35行]   │   ├── \subsection{数据预处理}  [从采集中拆出]
│                                       │   └── \subsection{核心处理模块}
└── \section{小结}             [5行]    └── \section{本章小结}          [扩充]
```

3. 对每项变更说明理由：
   - 哪些节被合并，为什么。
   - 哪些节被拆分，为什么。
   - 哪些过渡段落需要重写。

4. **必须用 `AskUserQuestion` 请求用户确认方案**，等待用户同意后才进入 Phase 4。

---

## Phase 4 — 实施（Implement）

### 约束

- **Scope Lock**：只编辑目标章节文件，不碰任何其他文件。
- **每次 Edit ≤30 行**：小步操作，便于追踪。
- **保留全部正文**：重组是调整结构，不是删减内容。

### 步骤

1. **移动内容块**：按照 Phase 3 确认的方案，使用 `Edit` 工具调整 `\section` 和 `\subsection` 的顺序和从属关系。
2. **更新标题**：修改合并后或拆分后的 `\section`/`\subsection` 标题，使其准确反映新内容范围。
3. **更新标签**：同步修改所有受影响的 `\label{...}`，确保命名与新结构一致。
4. **重写过渡段落**：对合并或移动后语义不连贯的衔接处，重写过渡段落。遵循以下原则：
   - 用地道的中文学术语言，不翻译腔。
   - 过渡段说明"上文做了什么 → 本节要做什么"，自然衔接。
   - 保持全文语气一致，像一个人在连贯地讲一件事。
5. **处理手工编号**：将不当使用的 `\textbf{(N)}` 段落标题改为正式的 `\subsection` 或 `\begin{enumerate}` 列表。

---

## Phase 5 — 验证（Verify）

### 步骤

1. **标签完整性检查**：
   - 用 `Grep` 提取目标文件中所有 `\label{...}`。
   - 用 `Grep` 在整个项目中搜索对应的 `\ref{...}` 和 `\autoref{...}`，确认无悬空引用。
   - 检查是否存在孤立的 `\label`（定义了但全项目无引用——仅作提示，不要求删除）。

2. **结构树验证**：
   - 重新提取修改后的结构树。
   - 与 Phase 3 确认的方案逐项比对，确保一致。

3. **编译检查**：
   - 用 `Bash` 执行 `$BUILD_CMD` 编译。
   - 检查编译日志中是否有 `undefined reference`、`multiply defined label` 等警告。
   - 若有错误，修复后重新编译，直到通过。

4. **输出验证报告**：

```
验证报告
────────
✅ 结构树与方案一致
✅ 所有 \ref 有对应 \label
✅ 无重复 \label
✅ 编译通过，无引用警告
```

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

任务完成后，输出以下摘要：

```
══════════════════════════════════
结构重组完成
──────────────────────────────────
目标文件：{文件路径}
发现问题：{N} 个
  - {问题1简述}
  - {问题2简述}
  ...
执行变更：{M} 项
  - {变更1简述}
  - {变更2简述}
  ...
验证状态：{通过/未通过}
══════════════════════════════════
```

---

## 使用示例

用户输入：
> 重组第三章

助手行为：
1. 确认目标文件（如 `chapters/chap03.tex`）。
2. 执行 Phase 1–5，每个阶段输出清晰的中间结果。
3. Phase 3 结束后必须等待用户确认，不可自行跳到 Phase 4。
