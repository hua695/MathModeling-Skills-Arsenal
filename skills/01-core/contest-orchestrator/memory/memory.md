# Memory architecture

## Storage layout

```text
memory/
├── index.yaml                 # 题型到条目的索引
├── hot/                       # 当前比赛快照、决策和风险
├── cold/                      # 已完成比赛的归档材料
├── retrieval.py               # 问题指纹检索与决策先验
├── semantic.py                # 字符 n-gram TF-IDF 与可选 embedding
├── ranking.py                 # 相似度分档和经验排序
├── topic_intelligence.py      # 选题经验覆盖分析
├── blueprint_retrieval.py     # 数学蓝图检索
├── paper_retrieval.py         # 论文呈现经验检索
├── decision_trace/            # 经过整理的决策链
├── replay/                    # 复盘输入与回放记录
├── calibration_db/            # 评审校准条目
├── math_blueprints/           # 数学模型蓝图
├── inbox/                     # 待审核的外部经验
├── writing_database.md        # 论文写作与呈现经验
└── decision_memory.md         # 决策经验
```

经验库正文位于 skill 根目录的 `failure_database.md`、`success_database.md`、`strategy_memory.md`，以及 `memory/decision_memory.md`、`memory/writing_database.md`。这些路径由检索脚本统一读取。

## Loading policy

1. `problem_parser` 生成 Problem Fingerprint。
2. 先读取 `memory/index.yaml`，再读取命中的条目。
3. 命中结果经过相似度、质量、复用、新鲜度和来源多样性排序。
4. 向 Planner 注入决策先验，而不是直接复制经验库正文。
5. 覆盖不足时明确标记 `weak` 或 `cold_start`，仅提供通用方法论和风险提示，不生成强结论。

经验价值优先级为 `strategy_memory`、`decision_memory`、`failure_database`、`success_database`。失败条目用于风险拦截，成功条目用于方法候选；二者都必须与当前题目证据绑定。

## Retrieval contract

问题检索使用三层召回：

- tier0：字符指纹匹配，识别主类、子类型和结构关键词；
- tier1：字符 n-gram TF-IDF，补充同义改写和词序变化；
- tier2：可选 embedding，仅在检测到本地模型或 API 时启用。

混合相似度经 A/B/C/D 分档后，档内使用有界 `rank_score` 和来源多样性系数排序。相似度是绝对门槛，质量、复用、新鲜度和探索奖励不能跨档改变语义相关性。

覆盖状态按强字符命中和强语义命中统计：

- `rich`：经验覆盖充足，可将成功模式作为强先验并规避失败警示；
- `normal`：经验可作候选，保留架构探索空间；
- `weak`：仅提供避坑信息，建模以题面和第一性原理为主；
- `cold_start`：禁止生成“历史表明”类强结论，采用通用方法论并先做文献核验。

数学蓝图只提供可裁剪的模型骨架，不替代题面分析和模型契约。低置信度命中只能作为参考。

## Paper presentation retrieval

`paper_retrieval.py` 根据章节、题型和场景检索 `writing_database.md`，向 Writer 和 Paper-Critic 提供呈现先验。论文成品不得复制经验库、评审记录、协作信息、提示词或未确认内容。

## Decision and replay

影响结果的选择登记为结构化决策，至少包含问题背景、候选方法、风险、最终选择、理由、证据和置信度。比赛期间的短记录写入 `decision.log`；赛后整理为 `decision_memory`；需要保留完整决策链时写入 `decision_trace`。同一事实只保留一个原始记录，其他载体保存引用关系。

回放通过 `scripts/replay_profiles.py` 或项目 replay 目录执行。只有经过验证、可复用且不依赖特定对话的结论，才可回写经验库或更新排序参数。临时文件、原始日志、身份信息和未经核验的材料不得进入长期经验。

## Snapshots and handoff

每个阶段保存完成状态、当前状态、风险、下一步、证据索引和运行清单。主会话维护范围、权限、冻结状态和节点确认；fork 只处理已授权任务卡，并在回流时提交证据、变更范围和验证结果。

## Artifact boundary

经验库和审计报告是内部工程材料；论文、报告、导出文件和第三方交付物只允许包含最终定稿、已核验事实、推导、来源、结果和必要附件。交付前必须执行负向回声扫描。
