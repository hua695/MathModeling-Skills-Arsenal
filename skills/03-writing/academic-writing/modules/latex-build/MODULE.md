---
name: latex-build
version: 1.0.0
description: |
  排版员：LaTeX 编译、错误诊断、PDF 预览。编译失败则阻断后续操作。
  触发词："编译"、"build"、"预览"、"latex"。
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
---

# 排版员（latex-build）

LaTeX 编译流水线技能，遵循 gstack `/ship` 模式：构建流水线 + 门禁机制。

## 触发条件

用户提到以下任意关键词时激活本技能：
- "编译"、"build"、"预览"、"latex"、"排版"、"生成 PDF"

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

### 第一步：进入工作目录

切换到论文项目根目录：

```
cd "$THESIS_DIR"
```

### 第二步：执行编译

运行配置中指定的编译命令：

```bash
cd "$THESIS_DIR" && $BUILD_CMD
```

编译命令由 `config.json` 的 `build_command` 字段定义（默认为 `PATH="/Library/TeX/texbin:$PATH" latexmk -xelatex -interaction=nonstopmode -f -g main.tex`）。

### 第三步：解析日志

读取 `main.log` 文件，将所有消息分为三个级别：

| 级别 | 匹配模式 | 含义 |
|------|----------|------|
| **ERROR** | `! ` 开头的行、`Fatal error`、`Emergency stop` | 致命错误，编译失败 |
| **WARNING** | `LaTeX Warning`、`Package xxx Warning`、`Overfull`、`Underfull` | 警告，不影响产出但需关注 |
| **INFO** | `Output written`、`Transcript written`、页数信息 | 正常信息 |

### 第四步：常见错误诊断与修复建议

针对以下常见错误类型，给出具体修复建议：

1. **缺失宏包**（`! LaTeX Error: File 'xxx.sty' not found`）
   - 建议：运行 `tlmgr install <包名>` 或检查宏包名称拼写

2. **未定义引用**（`LaTeX Warning: Reference 'xxx' on page N undefined`）
   - 建议：检查 `\label{}` 是否存在，是否拼写一致，可能需要再编译一次

3. **编码问题**（`! Package inputenc Error`、乱码相关）
   - 建议：确认文件保存为 UTF-8 编码，XeLaTeX 下不要使用 `inputenc` 宏包

4. **字体缺失**（`! fontspec error: "font-not-found"`）
   - 建议：检查系统是否安装了指定字体，使用 `fc-list` 确认

5. **浮动体溢出**（`Too many unprocessed floats`）
   - 建议：在适当位置添加 `\clearpage`，或调整浮动体参数

6. **图表位置异常**（连续浮动体、图错位、`[H]` 被降级）
   - 日志 `LaTeX Warning: 'H' float specifier changed to '!ht'`：缺 `\usepackage{float}` 或 `[H]` 被编译器降级，图实际位置失控
   - 日志 `LaTeX Warning: Float too large for page by Npt`：图尺寸超过版心，需缩图或拆图
   - 源码扫描发现连续 `\begin{figure}`/`\begin{table}` 之间无正文：按 `references/figure-placement-rules.md` 补图前引出句和图后解释句，禁止把图堆在章节末尾
   - 建议：不自动把 `[htbp]` 改成 `[H]`；位置参数和补什么论证文字由作者或论文 agent 决定，本模块只报告问题和定位

### 第五步：门禁判定（Gate）

根据日志解析结果，做出三档判定：

```
┌─────────────────────────────────────────────┐
│  FAIL         存在 ERROR → 阻断后续操作      │
│  PASS(!)      仅 WARNING → 通过但附带关注项   │
│  PASS         无错误无警告 → 完全通过          │
└─────────────────────────────────────────────┘
```

- **FAIL**：立即停止，输出错误详情和修复建议，不执行后续任何操作
- **PASS WITH CONCERNS**：输出警告摘要，继续后续流程
- **PASS**：直接进入报告阶段

### 第六步：构建报告

编译成功后，收集并输出以下信息：

```
══════════════════════════════════════
  编译报告
══════════════════════════════════════
  状态：   PASS / PASS(!) / FAIL
  页数：   XX 页
  文件大小：X.XX MB
  警告数量：XX 条
  编译耗时：XX 秒
  输出文件：main.pdf
══════════════════════════════════════
```

页数通过解析日志中 `Output written on main.pdf (XX pages)` 获取，文件大小通过 `ls -lh main.pdf` 获取。

### 第七步：PDF 预览（可选）

使用 `AskUserQuestion` 询问用户是否打开 PDF 预览：

```bash
open main.pdf
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
[latex-build] 完成
  结果：PASS / PASS(!) / FAIL
  耗时：XX 秒
  产出：main.pdf (XX 页, X.XX MB)
  待处理警告：XX 条
  下一步建议：<基于当前状态的建议>
```

若为 FAIL，下一步建议应指向具体的错误修复操作。
若为 PASS(!)，列出最值得关注的前三条警告。
若为 PASS，建议进行下一阶段工作（如内容审校、提交等）。
