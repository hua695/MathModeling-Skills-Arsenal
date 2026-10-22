# COLLAB 决策门

本策略只控制需要用户取舍的决策，不把每个写作小节变成等待点。项目初始化时从
`templates/collab_gate_policy.yaml` 复制策略到项目根或 `01_需求与规划/`；批准记录写入
`.contest/approval_log.yaml`，并绑定当时产物的 SHA-256。

## 项目侧接口路径

以下文件是项目运行实例，不应写回技能安装目录。脚本按下列优先级自动发现；命令行显式
参数优先于自动发现：

| 接口 | 稳定位置 | 说明 |
|---|---|---|
| `collab_gate_policy.yaml` | 项目根 / `01_需求与规划/` | 由模板复制后填写本题门禁策略 |
| `content_budget_plan.yaml` | 项目根 / `01_需求与规划/` / `paper/` | 仅在竞赛 profile 启用时生成 |
| `appendix_plan.yaml` | 项目根 / `01_需求与规划/` / `paper/` | 按实际能力覆盖附录，不固定套用 A/B/C/D |
| `.contest/approval_log.yaml` | 项目根下 `.contest/` | 仅保存批准记录；不得放入技能根目录 |

技能目录只保留 schema、模板、脚本和参考规则；项目实例、运行日志、图表、论文与交付包
必须写入稳定项目目录或外部审计目录。若路径存在多个候选，严格模式不得静默选择，应报告
候选并要求显式指定。

## 门的含义

| 门 | 必须确认 | 何时触发 |
|---|---|---|
| G0 | 条件账本、数据边界、假设 | A 阶段完成后 |
| G1 | 文献真实性与方法迁移 | 文献调研完成后 |
| G2 | 总体模型、baseline、内容与图表预算 | 正式复杂求解前 |
| G3 | 高风险、混合或 baseline 不稳的小问 | 仅条件式触发 |
| G4 | 真实结果、验证和图表证据 | 进入写作前 |
| G5 | 论文蓝图与附录覆盖 | 进入完整写作前 |
| G6 | 最终 PDF 和正式交付包 | 同步正式交付前 |

`AUTO` 不等待批准，但必须生成同一决策包；`COLLAB` 必须暂停并等待批准；`LOCK` 只接受
冻结前的批准记录，不允许借机更换架构或数字。普通章节写作、编译、格式修复和自动核对
不单独暂停。G3 由 Agent 在混合题、复杂非线性、低 baseline 或高风险探针时显式激活。

## 命令

```text
python scripts/collab_gate.py <项目根> --gate G2 --mode COLLAB
python scripts/collab_gate.py <项目根> --gate G2 --approve --note "确认模型架构"
python scripts/collab_gate.py <项目根> --gate G3 --mode COLLAB --activate
```

批准后若账本、模型契约、结果或图表计划发生变化，哈希不一致会重新 PAUSE；禁止用旧批准
覆盖新路线。策略缺失或必需产物缺失时，严格 COLLAB 不得进入下一阶段。
