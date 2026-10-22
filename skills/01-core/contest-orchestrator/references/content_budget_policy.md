# 内容预算与正文篇幅策略

本策略适用于需要正文目标区间的竞赛 profile，默认使用国赛个人 profile。它解决的是“先写出短稿、最后再补页”的流程缺陷，不是用页数替代内容质量。

篇幅目标按竞赛 profile 隔离：25--30 页只在国赛个人 profile（或显式传入
`--content-budget-plan`）启用，美赛、华数杯等其他 profile 不会因未提供计划而继承该目标。国赛正文定义按湖南赛区口径：摘要不计入，正文从正文主体起计，包含正文主体、参考文献前的 AI 工具使用声明和参考文献，最多 30 页；提交论文文件总页数最多 51 页。

## 核心原则

1. 在题目解析完成后生成项目侧 `content_budget_plan.yaml`，先规划论证容量，再开始模型求解和论文写作。
2. 预算按共享章节、小问和全局验证任务分配；页数只是容量预测，真正的准入依据是每个小问的证据单元是否完成。
3. 页数不足必须回溯到建模、求解、验证或结果解释阶段，禁止在 Writer 阶段通过重复、空白、无效图表、调字号或调行距补页。
4. `body_target_range` 是个人 profile 的质量目标；`body_hard_max_pages` 才是格式硬上限。不得把目标下限解释为自动生成废话的许可。

## 证据优先扩展（schema 1.1）

为避免“先写短稿、最后补页”，新计划可以声明
`planning_contract: evidence_first`。此时 `evidence_policy` 只登记证据来源
和反凑页信号，不复制结果数据；执行器由现有契约和运行清单派生
`.contest/evidence_index.json`。该索引是只读视图，不能手工改状态来制造
通过。每个小问可指定 `capability_profile`、`validation_scope` 和按论证目的
登记的 `visual_evidence`，但不规定全局图数。

内容预算中的 `visual_decision` 只记录 H5 阶段一的主张级初步需求（原H4职责），不能决定数据图图型、视觉编码或页面布局，也不能替代 H7 的视觉论证计划。H5 的 `required`、`table_justified` 或
`not_applicable` 及其 `visual_evidence` 用于标记正文主张、证据来源和容量关系；进入 H7 后，`visual_argument_plan.yaml` 才按读者问题、模型事实和六类视觉义务决定具体视觉槽位。最终图表注册表必须闭合到 H7 已批准槽位并通过 QA。`check_visual_evidence.py` 仍可把“表多图少”作为回溯审查信号，但不以固定图数强行制造图。

题型组合按小问分别路由：同一计划可以让 Q1 使用
`mechanistic_optimization`、Q2 使用 `data_prediction`，混合题再由
`model_blueprint` 和接口契约检查跨问连接。局部验证写在对应 6.x，小问间
共享的扰动或整体稳健性写入全局验证章节；页数预算只分配容量，不改变这一
职责边界。

## 三个检查点

- `blueprint`：建模蓝图完成后，检查预算是否能支撑目标正文，缺口要在求解前暴露。
- `solution`：真实求解和验证完成后，检查每个小问证据状态与预计正文容量；缺项回退到上游。
- `pdf`：最终 PDF 渲染后检查实际正文页数。低于目标进入短论文复核，超过硬上限失败。

## 国赛个人 profile 默认语义

```yaml
body_planning_target: [25, 30]
preferred_body_pages: 27
body_delivery_target: [25, 30]
body_hard_min_pages: null
body_hard_max_pages: 30
short_paper_review_threshold: 25
whole_paper_recommended_range: [35, 51]  # 总 PDF 推荐区间，不作为交付失败门禁
```

正文低于 25 页时，只有在所有小问证据、推导、真实结果和验证均完成，且不存在版面操纵时，才可以由人工确认短论文例外；执行器不得自动把它标成正式 PASS。

总 PDF 的 35–51 页是篇幅规划与人工复核的推荐区间。它应由摘要、正文、真实附录和 AI 工具说明共同形成；不能为达到推荐下限添加重复、无效或与正文无关的内容。51 页仍是提交文件总页数硬上限。

## 证据单元

每个小问至少登记：问题目标、建模思路、候选模型比较、假设映射、变量与单位、原始关系、推导链、最终模型、参数确定、算法与终止条件、真实结果来源、验证、结果解释和结论映射。题型 profile 可以增加要求，但不能删除与该题型无关的证据。

## 使用方式

```text
python scripts/check_content_budget.py <project_root> --stage blueprint --strict
python scripts/check_content_budget.py <project_root> --stage solution --strict
python scripts/check_content_budget.py <project_root> --stage pdf --pdf paper/paper.pdf --strict
python scripts/build_evidence_index.py <project_root> --stage solution --strict
python scripts/check_visual_evidence.py <project_root> --stage blueprint
python scripts/check_visual_evidence.py <project_root> --stage paper --tex paper/paper.tex
```

该检查器只读取项目侧计划和产物，不写入技能安装目录。计划缺失、预测不足或证据状态不完整时返回结构化失败原因。
