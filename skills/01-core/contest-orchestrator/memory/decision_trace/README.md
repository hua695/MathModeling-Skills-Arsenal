# Decision Trace（决策轨迹）

> 不只是记录"做了什么"，而是记录"**为什么这么做**"。
> 目标是未来可以作为 **Planner 的蒸馏数据**（从真实决策轨迹学习选模型/定参数）。

## 与 decision_memory 的区别
| | decision_memory | decision_trace |
|---|---|---|
| 粒度 | 单条决策 | 一整场比赛/项目的完整决策链 |
| 关注 | 结果 | 候选方法的 **pros / cons / risk** 权衡过程 |
| 用途 | 复盘提取"对/错" | Planner 蒸馏 + 检索复用 |

## 目录
```
memory/decision_trace/
├── README.md              # 本文档
├── <competition>_<year>/  # 每场比赛一个目录
│   └── decision_trace.yaml
```

## schema
```yaml
decision_id: DT-<competition>-<year>-<n>
problem_context:             # 当时的完整背景
  problem_type: 组合优化 / 预测 / ...
  data_scale: 小样本 / 中等 / 大规模
  time_left: 40h
  existing_failures: [FD-xxx, ...]   # 已触发的失败预警
  existing_strategies: [ST-xxx, ...] # 已命中的策略

candidate_methods:
  method_A:
    pros: [优点1, 优点2]
    cons: [缺点1]
    risk: 高风险 / 中风险 / 低风险
  method_B:
    pros: [...]
    cons: [...]
    risk: 中风险

final_choice: method_A
reason: 为什么选它（对比说明，越具体越好）
evidence: 关联的结果文件/实验ID（结果只从代码生成）
confidence: 高 / 中 / 低

quality_score:               # 与 memory-schema 一致
  source_quality: 高 / 中 / 低
  confidence: 高 / 中 / 低
  verified: true / false
  reuse_count: 0
  success_rate: null
```

## 记录时机
- 每次 Controller/Executor 做出**影响结果的决策**时记一条：换架构 / 改参数 / 加约束 / 定初值 / 选模型。
- 赛后复盘时把零散 DM 合并成完整 decision_trace，作为未来蒸馏素材。

## 职责界定（避免与 decision_memory / decision.log 三重写入）
| 载体 | 时机 | 粒度 | 用途 |
|---|---|---|---|
| `core/controller.md` 的 decision.log | **比赛中实时**（每步留痕） | 短条目 | 回溯/晨报 |
| `decision_memory`（DM 库） | **赛后复盘**（逐条评审对错） | 单条 | 检索复用 |
| `decision_trace/` | **赛后蒸馏**（合并成一整场权衡链） | 完整链 | **Planner 蒸馏** |

**单一权威**：比赛中 → decision.log；复盘入库 → decision_memory；喂给未来 Planner → decision_trace。
三者不重复写同一份数据：trace 是 log/DM 的**加工产物**，不是第三处原始记录。
