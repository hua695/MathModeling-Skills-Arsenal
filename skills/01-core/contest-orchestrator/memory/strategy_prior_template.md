# Strategy Prior 模板（注入 Planner 的决策先验）

> 由 `memory/retrieval.py` 按 Problem Fingerprint 生成，注入 Planner 的第一轮决策。
> 返回的是**统计先验**，不是文档罗列；Planner 必须显式回应。

```markdown
# 历史决策先验（基于 {n_matched} 条相关经验）

## 相似问题模式
{primary}/{secondary} · 数据{data_scale} · 约束{constraints} · 目标{objective}

## 已被验证的成功模式（成功经验数 {n_success}）
- {pattern}：出现 {count} 次，占比 {rate}
...

## 已知失败警示（含触发信号）
- 方法 {method}
  失败原因：{lesson}
  信号：{signal}
...

## 高风险动作（历史失败率显著，避免或触发 Critic 加强审查）
- {action_1}
- {action_2}

## 可复用策略
- 场景 {scenario} → {strategy}
...

## Planner 必须回答（否则先验无效）
1. 基于成功模式，我计划采用哪个策略？**为什么**
2. 我是否规避了全部高风险动作？**逐一说明**
3. 是否尝试历史没有的新方法？**如果"是"，说明理由与风险兜底**
```

## 使用规则
1. **先验是约束不是圣旨**：Planner 可以偏离，但必须给出理由（新题/数据不同）。
2. **失败经验必须呈现**：retrieval 强制召回 FD 库，别只给成功经验。
3. **动态权重**：某类问题失败经验多 → 失败警示权重自动上调（坑多的地方保守）。
4. **注入位置**：problem-parser 之后、Planner 建模方案之前。
