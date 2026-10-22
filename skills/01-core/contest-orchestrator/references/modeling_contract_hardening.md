# 建模求解契约增强用法

本文件只描述可验证接口，不替代题型契约。它用于把“论文写了什么”连接到“代码实际运行了什么”。

## 1. schema 1.1 的推导链

将 `modeling_solution_contract.yaml` 升级到 `schema_version: '1.1'` 后，`formula_chain` 中除
`original` 外的每一步都应填写：

```yaml
- id: f1
  kind: rearranged
  derived_from: [f0]
  derivation_anchor: "将边界条件代入原始关系式并整理"
  source_anchor: "整理后的关系式"
  meaning_anchor: "该式表示中间状态"
```

`derived_from` 必须指向前序公式；`derivation_anchor` 必须在对应小问正文中出现。检查器只验证证据链和顺序，数学正确性仍由 Critic/人工复核负责。

## 2. 算法配置锁

只有需要锁定运行配置的项目才创建 `algorithm_manifest.yaml`。每个参数必须指向 JSON Pointer 或可静态解析的 Python 顶层变量；不得从任意打印文本猜测参数。清单一旦存在，严格模式下核对失败即阻断；未声明清单的旧项目保持兼容并报告未启用。

## 3. 派生结果反算

在 `result_code_map.json` 增加 `derived_checks`，用于检查结果文件内部的可复算关系：

```json
{
  "derived_checks": [
    {
      "result_file": "results/q1.json",
      "target_pointer": "/total",
      "input_pointers": ["/part_a", "/part_b"],
      "operation": "sum",
      "tolerance": 1e-9
    }
  ]
}
```

支持 `sum`、`product`、`mean`、`difference`、`ratio`。这不是完整模型证明，而是对“论文结果与中间量不一致”的低成本反向拦截。

## 4. 量纲声明

复杂公式不由脚本自动解析。题目需要量纲审计时，在 `model_contract.yaml` 声明 `dimensions`：符号使用固定维度向量，方程声明 `same/add/multiply/divide` 运算；未声明时检查器仅输出 INFO，不阻断旧项目。

## 5. 混合题作用域

正文出现 `\\label{subproblem:Q1}` 等显式标签后，缺少某个小问标签时不会再把全文当作该小问证据。混合题必须为每个小问提供独立标签和接口文件，防止 Q1 的公式、算法或结果串入 Q2。
