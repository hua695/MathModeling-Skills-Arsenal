# 附录覆盖规划

附录不是固定的 A/B/C/D 容器。先完成小问求解、确认真实源码和推导材料，再填写
`appendix_plan.yaml`。当 `planning_contract: coverage_first` 时，`coverage_matrix` 必须覆盖每个
子问题，并将其正文主章节映射到实际存在的附录模块：

- `core_code_module`：实际运行过并在论文附录展示的核心函数或算法片段；完整源码由
  `source_inputs.full_source_files` 和 `support_source_files` 登记到支撑材料包；
- `long_derivation_module`：正文无法容纳但支撑结论的推导；
- `verification_module`：扰动、对照、误差或交叉验证材料。

若 `source_inputs.program_used=true`，每个小问必须登记真实代码模块，或明确填写
`code_not_applicable_reason`。没有程序、长推导或验证材料时应如实留空并说明，不得为凑附录
编造代码、数据或计算表。模块仍以 `used_by` 和 `paper_anchor` 和正文交叉核验。

程序题同时填写 `appendix_code_mode`、`core_source_files`、`full_source_files` 和
`support_source_files`。默认 `core_only`：论文附录只展示核心代码，支撑材料提供完整源码；
`full_source` 仅在项目明确需要将完整源码嵌入论文时使用。

```text
python scripts/appendix_planner.py <项目根> --out <报告路径>
```

该规划只验证覆盖关系和来源，不强制某一题型拥有固定数量或固定名称的附录。
