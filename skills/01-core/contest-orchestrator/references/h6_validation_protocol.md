# H6 验证协议

H6 在范围卡通过后读取本协议。验证只覆盖任务卡登记的范围，不重读 H5 全部推导和代码；L3 全局回流或用户明确要求时例外。

## 必查项

1. 按 `validation_contract.yaml` 核对关键结论与深度抽查锚点。
2. 核对跨问共享变量、单位、数据版本、字段、时间尺度、参数、约束、结论和来源。`global_interface_check.yaml` 的每个结构化 `interface_fields` 条目必须同时登记 `comparison_status`、项目相对 `source_path` 和与当前文件一致的 `source_sha256`；缺字段保持 `PAUSE`，来源不存在或哈希不一致为 `BLOCK`。
3. 核对 `paper_narrative.yaml` 的 `key_result` 与冻结结果一致。
4. 核对 `model_summary_cards.yaml`：每个小问均有唯一最终求解模型、决策变量及单位、参数/输入、边界或约束、求解接口和来源公式；逐项与推导、代码、结果和适用范围对齐。通过后写入 `status: verified`、`verified_by: H6` 和当前实例 ID。
5. 核对 `result_interpretation_cards.yaml`：事实、意义、解释依据和适用范围均有冻结证据；通过后写入 `status: verified`、`verified_by: H6` 和当前实例 ID。
6. 运行任务卡指定的专项检查：方法选择证据、代码注释质量和数值合理性。不得以 H5 自检替代。
7. 核验 `paper_material_readiness.yaml`，确认其证据引用、容量和 H6 签名一致。

## 输出与回流

- 通过：输出独立验证报告、`global_interface_check.yaml`、已签名的 `model_summary_cards.yaml` 与结果解释卡、冻结清单。
- 不通过：逐项记录小问、字段、期望与实际证据、影响范围和建议回流节点；不修改上游材料。
- `targeted_recheck`：只报告变更材料及其受影响的下游证据；未受影响的冻结产物保持有效。

## 禁止事项

不得补写推导、重算模型、调整结果、代写论文或把验证过程写入论文和交付材料。
