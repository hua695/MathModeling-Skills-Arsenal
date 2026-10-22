# 上下文加载策略

按任务范围和阶段最小加载。`SKILL.md` 负责路由，`manifest.yaml` 负责机器可读文件分类；未列入当前阶段的材料不自动读取。

## 固定加载

- `SKILL.md`
- `VERSION`
- `core/permission.md`
- `scripts/scope_router.py`

## 阶段加载

| 阶段 | 读取内容 |
|---|---|
| 理解与规划 | `planner/`、`core/risk_probe.md`、`planner/symbol_table.md`、命中的 `memory/index.yaml` 条目 |
| 求解与图表 | `executor/`、题型对应的 `planner/modeling_profiles.yaml`、`references/figure_policy.md` |
| 论文与打磨 | `core/paper_hard_requirements.md`、`core/output_contract.md`、`core/presentation_polish.md`、`core/paper_postfix_checklist.md`、`references/paper_review_and_absorption_lessons.md`、`references/excellent_paper_patterns.md` |
| 评审 | `critic/`、`core/universal_modeling_contract.md`、`core/modeling_chapter_contract.md`、`references/evidence_integrity.md` |
| 交付 | `scripts/delivery_all.py` 及其登记的门禁；`core/appendix_contract.md`、`references/delivery_contract.md`、`references/appendix_coverage_policy.md` |
| 协作 | `team/interface.md`、`references/collab_gate_policy.md`、`references/mode_state_machine.md` |

## 经验检索

1. 先读 `memory/index.yaml`。
2. 只读取命中的 `failure_database.md`、`success_database.md`、`strategy_memory.md`、`memory/decision_memory.md` 和相关 replay 条目。
3. 数学蓝图按题型命中读取；论文写法按章节、题型和竞赛 profile 命中读取。
4. 命中经验必须绑定当前题目证据；经验只能提供候选约束，不能替代题面、数据或代码验证。

## 不自动加载

- `references/` 中未命中当前任务的材料
- `memory/inbox/`
- `scripts/archive/`
- 项目运行产物、实验数据、正式交付文件和外部归档

## 复杂度裁剪

| 复杂度 | 最小链路 |
|---|---|
| `simple` | 题目解析 → baseline → 求解 → 论文 |
| `medium` | 标准全流程 |
| `hard` | 全流程 + 多候选架构 + 稳健性/灵敏度核验 |

复杂度由题目小问数、数据规模、约束复杂度和计算成本共同判定；不得仅按页数或单一阈值裁剪。

## 视觉策略

绘图任务的渲染、截图和自动视觉质检默认开启，以保证图片美观、整洁和可读；论文、建模、求解、文献、评审和文档任务默认关闭视觉入口。非绘图任务仅在用户明确要求或显式提供 `--visual-check` 时启用；所有任务的文本层、结构、公式、数字、引用、来源、图表登记和交付完整性检查照常执行。
