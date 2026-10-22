# 竞赛 replay 记录模板

每次 replay 只记录可验证事实、证据路径、决策依据和可复用规则。项目运行日志、临时输出和内部沟通不写入此模板。

## 1. 题目与输入

```yaml
competition:
year:
problem:
problem_type:
objective:
variables: []
constraints: []
data_sources: []
assumptions: []
complexity:
  math:
  data:
  compute:
```

## 2. 规划与证据

```yaml
selected_route:
selection_basis: []
baseline_result:
baseline_evidence: []
model_contract:
result_sources: []
figure_registry:
```

## 3. 节点记录

| 阶段 | 完成事实 | 证据路径 | 验证命令 | 状态 |
|---|---|---|---|---|
| A 题目理解 |  |  |  |  |
| B 规划与 baseline |  |  |  |  |
| C 求解与图表 |  |  |  |  |
| D 论文写作 |  |  |  |  |
| E 评审 |  |  |  |  |
| F 交付 |  |  |  |  |
| G replay |  |  |  |  |

## 4. 结果与可靠性

| 指标 | 数值 | 单位 | 来源文件 | 代码哈希 | 状态 |
|---|---:|---|---|---|---|
|  |  |  |  |  |  |

记录 seed、参数、环境、敏感性、消融、误差或适用边界。结果必须能从代码、推导或登记数据源重建。

## 5. 复用规则

只登记已经验证并适用于明确条件的规则：

```yaml
rule:
applicable_conditions: []
evidence: []
verification_command:
scope:
```
