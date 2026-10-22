# Thesis Polish Agent（Codex academic-writing 集成版）

在本机 Codex 技能体系中，本目录以 `academic-writing` 作为主入口，安装位置为 `C:\Users\USER\.agents\skills\academic-writing`；下方 14 个目录作为内部角色资源使用。

为避免 Codex 多子技能自动加载不稳定，内部角色已放在 `modules/` 下并改名为 `MODULE.md`。README 中的 `/deai`、`/review-chapter` 等命令是角色名称，由主入口按需读取，不是独立顶层技能；数学建模论文的公式、引用、数字和三线表修改必须经过本地保护器。

**中文论文智能修改助手** — 一套工程化的 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) Skills，为中文 LaTeX 论文提供系统性的审阅、润色、结构优化和质量保障。

> 好的中文学术论文读起来像一个人在认真讲一件事，内容铺开、论证扎实、一气呵成。
> Thesis Polish Agent 的一切工作都服务于这个目标。

---

## 为什么需要这个工具

写中文论文时，你可能遇到过这些问题：

- AI 辅助写作后留下大量"首先/其次/最后"、"值得注意的是"等**机器痕迹**
- 章节结构碎片化，小标题太多，内容**不够厚实**
- 公式堆砌严重，读者看完公式不知道**它意味着什么**
- 实验分析只贴数字，缺乏**因果解释链**
- 术语写法不统一（同一个算法三种拼法）
- 导师批注一堆，改了这个忘了那个，**追踪困难**

Thesis Polish Agent 把这些问题拆分成 14 个专业角色，每个角色有独立的检测规则、修改策略和验收标准。你像"修改小组组长"一样分配任务，agent 并行执行。

---

## 特性

- **14 个专业 Skill**，覆盖论文修改全流程（审阅→润色→结构→扩写→质检→编译）
- **10 维 AI 痕迹检测**，内置完整的检测规则和替换词表
- **5 类薄弱点扫描**，自动发现段落过短、公式缺解释、实验分析浅等问题
- **配置化设计**，通过 `/thesis-init` 一键初始化，适配任何 LaTeX 论文项目
- **并行执行**，不同章节的修改可同时进行（利用 Claude Code 的 Agent 工具）
- **自动追踪**，每个 skill 执行后自动更新 `issues.md` 和 `progress.md`
- **编译验证**，修改 tex 文件的 skill 完成后自动编译确认无破坏
- **风格对标**，内置工科硕士论文结构规范，可与优秀范本对标

---

## 安装

### 前置要求

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI 已安装
- LaTeX 编译环境（推荐 TeX Live 2023+，需要 `latexmk` 和 `xelatex`）
- 你的论文是 LaTeX 格式（有 `main.tex`）

### 安装步骤

```bash
# 克隆到 Claude Code 的 skills 目录
git clone https://github.com/YOUR_USERNAME/thesis-polish-agent.git ~/.claude/skills/thesis

# 创建 symlinks 让每个 skill 可以被 / 命令调用
cd ~/.claude/skills
for d in thesis/*/; do
  name=$(basename "$d")
  [ -f "thesis/$name/SKILL.md" ] && ln -sf "thesis/$name" "$name"
done

# 重启 Claude Code 会话使 skills 生效
```

### 验证安装

重启 Claude Code 后，输入 `/thesis-init`，如果看到初始化流程启动，说明安装成功。

---

## 快速开始

### 1. 初始化项目

进入你的论文工作目录（包含 LaTeX 工程的上级目录），运行：

```
/thesis-init
```

按提示：
1. 选择论文工程目录（包含 `main.tex` 的目录）
2. 选择编译方式（默认 `latexmk + xelatex`）
3. 自动创建 `.thesis/` 工作区（config.json + progress.md + issues.md）

### 2. 审阅论文

```
/review-chapter c3
```

或全局审阅：

```
/review-chapter 全局
```

审稿人会进行两遍审查：
- **Pass 1 (CRITICAL)**：结构与逻辑（章节逻辑链、图表引用、公式引用链）
- **Pass 2 (INFORMATIONAL)**：表达与规范（AI痕迹、括号注释、碎片化、实验分析深度）

输出分级问题报告，每个问题标注 AUTO-FIX（可自动处理）或 ASK（需确认）。

### 3. 分派修改

根据审阅报告中的建议，调用对应的 skill：

```
/deai c4          # 润色第四章，去除 AI 痕迹
/restructure c4   # 重组第四章结构，合并碎片子节
/expand c2        # 扩写第二章，补充过渡和解释
```

**并行执行**：不同章节可以同时修改：

> "帮我同时润色 c1 和 c3"

Claude Code 会启动多个 agent 并行处理。

### 4. 质量检查

```
/consistency      # 8项终稿一致性全检
/style-check      # 与优秀论文结构对标
/latex-build      # 编译验证
```

### 5. 查看进度

```
/thesis           # 查看全局进度，推荐下一步
/thesis-status    # 详细的进度看板
```

---

## Skills 完整列表

### 流程管理

| 命令 | 角色 | 功能 |
|------|------|------|
| `/thesis-init` | 初始化 | 配置论文目录、编译命令，创建 `.thesis/` 工作区 |
| `/thesis` | 组长 | 展示全局进度，推荐下一步操作 |
| `/thesis-status` | 秘书 | 详细进度看板、任务管理 |

### 审阅与检查（只读，不修改文件）

| 命令 | 角色 | 功能 |
|------|------|------|
| `/review-chapter` | 审稿人 | 导师视角两遍审阅，分级输出问题报告 |
| `/consistency` | 质检员 | 8项终稿自动检查（引用完整性、编号连续性、数字一致性等） |
| `/style-check` | 风格对标 | 与工科硕士论文结构规范对标，输出差距报告 |

### 修改与润色（会修改 tex 文件）

| 命令 | 角色 | 功能 |
|------|------|------|
| `/deai` | 润色师 | **10维** AI 痕迹检测与自然化改写 |
| `/expand` | 扩写师 | **5类** 薄弱点检测与扩写（短段落/公式缺解释/分析浅/缺过渡/缺动机） |
| `/restructure` | 结构师 | 章节结构诊断与重组（合并碎片子节、调整层级） |
| `/formula-compress` | 公式编辑 | 公式分类（核心/辅助/冗余）、引用链检查、安全压缩 |
| `/terminology` | 术语官 | 全文术语一致性巡检与统一替换 |

### 工具

| 命令 | 角色 | 功能 |
|------|------|------|
| `/latex-build` | 排版员 | LaTeX 编译、日志解析、错误诊断 |
| `/thesis-research` | 调研员 | 文献搜索、结构化综述素材、BibTeX 生成 |
| `/tidy` | 整理员 | 工作区文件归类整理（依赖分析 + 安全移动） |

---

## `/deai` 的 10 维 AI 痕迹检测

润色师是最核心的 skill，内置 10 个检测维度：

| 维度 | 检测什么 | 示例 |
|------|---------|------|
| 1. 程式化衔接词 | 首先/其次/最后/综上所述 密度过高 | 同一小节 ≥3 个高频词 |
| 2. 句式骨架重复 | 连续段落用相同句型开头 | 连续3段"本文提出了…" |
| 3. 模板化总结句 | 空洞的万金油结尾 | "得到了充分的验证" |
| 4. 空洞修饰词 | 无数据支撑的强调 | "显著地提升了性能" |
| 5. 机械化段落开头 | 连续段落相同模式开头 | 连续用"具体而言，…" |
| 6. AI 套话收尾 | 万金油式章节结尾 | "存在深化空间" |
| 7. 括号注释堆砌 | 非核心术语的英文括注 | 同段 ≥2 个括号英文注释 |
| 8. 小标题碎片化 | 连续子节各 <15 行 | 列提纲代替铺开论述 |
| 9. 标题中英混杂 | 中文标题参数含英文 | `{方法名 (English)}` |
| 10. 正文伪标题 | `\textbf{xxx。}` 充当小标题 | 黑体标签代替正式标题 |

每个维度都有完整的检测规则、阈值、改写原则和替换词表，不依赖外部文件。

---

## `/expand` 的 5 类薄弱点检测

| 类型 | 检测什么 | 扩写策略 |
|------|---------|---------|
| A. 超短段落 | 正文段落 <3 句 | 补设计动机 / 替代方案对比 |
| B. 公式缺解释 | 公式后仅符号罗列 | 补形式层 + 直觉层 + 边界层 |
| C. 实验分析浅 | 只贴数字不解释 | 补"指标→原因→佐证→影响"四步链 |
| D. 章节间缺过渡 | 节首直接进技术描述 | 补"上节结论→本节问题"桥梁句 |
| E. 方法描述缺动机 | 先抛结论后补动机 | 补"为什么要做"的铺垫 |

扩写原则：**每句新增必须有信息增量**。没有数据支撑的不编造，标记 `NEEDS_DATA`。

---

## 工作区结构

`/thesis-init` 会在论文目录下创建：

```
你的论文目录/
├── main.tex              # 你的论文主文件
├── chapters/             # 你的章节文件
├── .thesis/              # ← thesis-polish-agent 工作区
│   ├── config.json       # 项目配置（路径、编译命令等）
│   ├── progress.md       # 修改进度追踪
│   ├── issues.md         # 问题清单（自动维护）
│   └── reports/          # 各 skill 输出的检查报告
```

所有 skill 通过 `config.json` 读取路径，**零硬编码**。

---

## 推荐工作流

```
                    /thesis-init
                         │
                    /review-chapter (全局审阅)
                         │
            ┌────────────┼────────────┐
            │            │            │
        /restructure  /deai       /expand
        (结构重组)    (AI降重)    (内容扩写)
            │            │            │
            └────────────┼────────────┘
                         │
                   /style-check (风格对标)
                         │
                   /consistency (一致性全检)
                         │
                   /latex-build (编译验证)
                         │
                      完成 ✅
```

**并行建议**：
- 不同章节的 `/deai` + `/expand` 可并行
- `/restructure` 和 `/deai` 对同一章节不能并行（会冲突）
- `/consistency` 和 `/terminology` 是只读扫描，可并行

---

## 收尾协议

每个 skill 执行完毕后自动执行：

1. **编译验证**（修改 tex 的 skill）— 确认无编译错误
2. **更新 issues.md** — 新问题追加，已解决问题标记
3. **更新 progress.md** — 追加完成记录
4. **保存报告** — 输出到 `.thesis/reports/`

---

## 安全红线

所有会修改文件的 skill 遵循以下规则：

- 不改 `\label{}`、`\ref{}`、`\cite{}`、`\caption{}` 内部标识符
- 不删实验数据（表格数值、图文件名）
- 不一次性替换超过 30 行 — 拆成多次 Edit
- 不编造实验数据 — 推测性分析标注"我们推测…"
- 改写后保持原段落的技术含义不变

---

## 自定义与扩展

### 添加新的检测维度

编辑 `deai/SKILL.md`，在"Step 2"中添加新的维度定义（检测规则 + 阈值 + 改写原则）。

### 添加新的 Skill

1. 创建目录：`mkdir thesis/your-skill`
2. 编写 `SKILL.md`（参考现有 skill 的 YAML frontmatter 格式）
3. 包含 Step 0 配置加载 preamble
4. 包含收尾协议
5. 创建 symlink：`ln -sf thesis/your-skill ~/.claude/skills/your-skill`

### 修改风格规范

编辑 `style-check/SKILL.md` 中的"内置规范"部分，调整为你的学校/学科的要求。

---

## 常见问题

**Q: 支持英文论文吗？**

当前的检测规则和润色策略都是针对中文论文设计的。英文论文需要调整 `/deai` 的检测词表和改写原则。

**Q: 支持 Word 格式吗？**

不支持。仅适用于 LaTeX 格式的论文。

**Q: 修改会不会破坏我的论文？**

每个修改 skill 都有安全红线（不改 label/ref/cite、不删数据、不超过 30 行批量替换）。修改后自动编译验证。建议在开始前用 git 做一个 commit 作为还原点。

**Q: 可以并行处理多个章节吗？**

可以。Claude Code 的 Agent 工具支持并行启动多个子任务。告诉 Claude "帮我同时润色 c1 和 c3"即可。

**Q: `/thesis-init` 需要重新运行吗？**

只需运行一次。配置保存在 `.thesis/config.json` 中，后续会话自动读取。

---

## 致谢

- 架构设计灵感来自 [gstack](https://github.com/garrytan/gstack) 的工程化 skill 系统
- 论文写作 prompt 参考了 [awesome-research-writing-skills](https://github.com/Leey21/awesome-ai-research-writing)（很牛的writing skills）
- AI 痕迹检测规则参考了 [chatgpt-prompts-for-academic-writing](https://github.com/ahmetbersoz/chatgpt-prompts-for-academic-writing) 等学术写作社区经验

## License

MIT
