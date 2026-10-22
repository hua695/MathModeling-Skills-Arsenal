# 题目条件账本（problem_condition_ledger）

这是 `problem-parser` 在题目标题定位后生成的结构化中间产物。它吸收题意逐句解释能力，但不替代 Problem Graph，也不要求生成最终论文图。

## 生成时机

1. 定位实际题目标题，排除标题前的竞赛名称、格式提醒和页眉水印。
2. 通读题目、问题编号、表头、图注、附件说明和题后限制。
3. 将会改变模型选择、变量定义、约束、数据处理、目标或验证方式的句子/独立分句登记为 `source_units`。
4. 为每个小问登记输入、任务、输出、依赖和必须出现的正文证据。
5. 再生成 Problem Graph 和 Problem Fingerprint；经验库不得反向修改原始条件账本。

## 条件分类

允许的 `roles`：`context`、`entity`、`definition`、`mechanism`、`given`、`constraint`、`task`、`objective`、`validation`、`deliverable`。

允许的 `link_type`：`defines`、`supplies`、`restricts`、`motivates`、`extends`、`reuses`、`compares`、`validates`、`overrides`。

`evidence_level` 必须区分：

- `confirmed`：题面直接给出，可直接进入模型接口；
- `inferred`：由题面语义推断，必须记录推断依据，不得直接当作硬约束；
- `pending`：存在歧义或材料缺失，进入 `unresolved_conditions`，等待人工确认或情景分析。

## 最小字段

```yaml
schema_version: "1.0"
source_file: problem.pdf
title_anchor: "实际题目标题"
source_units:
  - id: C-01
    source_location: "第1页第3句"
    source_text: "题目原文完整句子"
    roles: [constraint]
    normalized_meaning: "规范化建模含义"
    affected_questions: [Q1, Q2]
    downstream_evidence: [variables, constraints, validation]
    link_type: restricts
    evidence_level: confirmed
    status: mapped
questions:
  - id: Q1
    source_unit_ids: [C-01]
    inputs: [附件数据]
    task: "本小问任务"
    outputs: [模型参数]
    reused_by: [Q2]
unresolved_conditions: []
```

## 强制边界

- 原文条件必须保留来源位置和完整句子；不得用“题目要求建模”代替具体含义。
- “隐藏约束”只能作为 `inferred` 或 `pending`，除非正文有明确题面证据，否则不能直接写入硬约束。
- 题型可以混合，但每个条件必须绑定具体 `affected_questions`；不能用 Q1 的条件默认为 Q2 条件。
- Mermaid 不属于账本必需产物。账本只提供关系数据；问题分析流程图由 `tech-route-maker` 根据账本绘制并登记真实来源，原理/机制/几何示意图由 `tikz-scientific-figures` 根据模型契约绘制。
- `FULL_CONTEST --strict` 下，关键条件必须完成映射；未解决条件必须有人工决定、情景分析或明确的不适用说明。
