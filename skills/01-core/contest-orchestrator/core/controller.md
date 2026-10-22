# Controller：路由与止损

## 自动路由

```text
success        → continue
model_failure  → return Planner
experiment_failure → return Executor
paper_failure  → return Writer
data_anomaly   → DATA_RECHECK
architecture_limit → AUTO:切换互补路线 / COLLAB:提交证据等待确认
parameter_change → AUTO:修改并同步 registry / COLLAB:提交决策包
time_risk      → 收敛并进入论文模式
validation_pass → delivery gate
```

## Emergency Stop

满足任一条件即停止探索并进入收敛：剩余时间低于 15%，论文完成度超过 80%，或新路线的验证风险高于预期收益。收敛阶段优先保证摘要、主问、模型证据、关键结果和交付门禁。

## 架构止损

当多组 seed 和参数仍无法突破项目阈值时，记录证据并判定当前路线达到止损点。选择与当前路线机制互补的候选路线，先在小规模数据上验证，再决定是否扩展。`AUTO` 在授权范围内切换；`COLLAB` 必须提交决策包并等待确认。

## 决策留痕

当前决策文件只记录仍影响项目的决策，并为每条记录保留时间、角色、动作、依据、影响、证据路径和验证状态。已归档记录不参与当前路由。

```text
/log/decision_current.md
time | role | action | evidence | impact | status
```

## strategy-selector

输入题型、数据规模、剩余时间、资源限制和已验证经验，输出候选路线、选择依据、风险等级、验证动作和切换条件。数据少或时间紧时优先可验证 baseline；数据充足且时间允许时才增加创新路线。策略必须写入当前计划并与结果登记同步。
