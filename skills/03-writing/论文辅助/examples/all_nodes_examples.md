# G0–G6 节点审查典型示例（精简版）

> 每个节点展示 1–2 个典型发现，完整审查流程见 `g4_review_example.md`。
> 所有发现均为示例数据，用于展示各节点的检查重点差异。

---

## G0 题目理解与条件账本

**审查范围**：`problem_condition_ledger.yaml`、`model_assumptions.md`

**发现 G0-001**：
```yaml
status: TRUE_CURRENT
severity: HIGH
source_path: "problem_condition_ledger.yaml"
line_range: "12-15"
observed_text: "样本量上限：未登记"
evidence: "题面明确给出'每批样本量不超过500件'，但条件账本的输入约束栏未登记该参数"
recommended_action: "在条件账本中补登样本量上限约束，并标注来源为题设给定"
risk_if_ignored: "后续建模可能超出题设约束，导致方案不可行"
```

**发现 G0-002**：
```yaml
status: TRUE_CURRENT
severity: MEDIUM
source_path: "model_assumptions.md"
line_range: "8-9"
observed_text: "假设次品率服从正态分布"
evidence: "题设已明确次品率为固定参数p，将其写为建模假设属于把题设规则误写为新增假设"
recommended_action: "移至条件账本的题设给定栏，不放在假设小节"
risk_if_ignored: "评委可能认为建模者未准确区分题设条件与自主假设"
```

**审查结论**：有条件通过（需补登 1 项约束、修正 1 处假设分类）

---

## G1 文献调研与方法迁移

**审查范围**：`references.yaml`、文献综述章节

**发现 G1-001**：
```yaml
status: TRUE_CURRENT
severity: BLOCKER
source_path: "references.yaml"
line_range: "5-6"
observed_text: "- title: '抽样检验方法综述' url: 'https://blog.csdn.net/xxx'"
evidence: "该文献只有博客链接，无DOI、无期刊来源，不符合正式文献要求；且当前可核验中文学术文献仅1篇，不足2篇硬门禁"
recommended_action: "替换为有DOI的中文学术期刊文献，或补充至少1篇可核验中文文献"
risk_if_ignored: "国赛文献门禁不通过，且引用不可追溯"
```

**发现 G1-002**：
```yaml
status: TRUE_CURRENT
severity: HIGH
source_path: "sections/02_literature.tex"
line_range: "30-32"
observed_text: "本文采用文献[3]的序贯检验方法"
evidence: "仅声明采用，未说明对原方法做了哪些改造（adopt/adapt/reject决策缺失），正文引用位置与文献作用不对应"
recommended_action: "补充方法迁移说明：原方法假设XX，本题改造为XX，改造理由XX"
risk_if_ignored: "方法迁移边界不清，评委无法判断模型创新性与合理性"
```

**审查结论**：不通过（存在 BLOCKER 级文献来源问题）

---

## G2 总体架构与内容预算

**审查范围**：`content_budget_plan.yaml`、`model_blueprint.yaml`

**发现 G2-001**：
```yaml
status: TRUE_CURRENT
severity: HIGH
source_path: "content_budget_plan.yaml"
line_range: "20-22"
observed_text: "问题三：模型建立与求解（待定）"
evidence: "问题三的内容预算只有标题，无推导链计划、无结果文件、无图表计划，属于空架构"
recommended_action: "补全问题三的关键结论、推导链、代码结果、图表计划"
risk_if_ignored: "进入求解后无路线图，可能导致该问内容缺失或仓促补写"
```

**发现 G2-002**：
```yaml
status: TRUE_CURRENT
severity: MEDIUM
source_path: "content_budget_plan.yaml"
line_range: "45-46"
observed_text: "图表计划：图1、图2、图3"
evidence: "图表计划只有数量编号，无论证价值说明（每张图支撑什么主张），且问题二为优化题却无趋势图计划"
recommended_action: "每张图绑定明确主张；优化题补充参数敏感性趋势图"
risk_if_ignored: "图表可能沦为装饰，缺乏证据价值"
```

**审查结论**：有条件通过（需补全问题三内容预算）

---

## G3 条件式小问建模（高风险题触发）

**审查范围**：`sections/06_model_solution.tex` 高风险小问

**发现 G3-001**：
```yaml
status: TRUE_CURRENT
severity: HIGH
source_path: "sections/06_model_solution.tex"
line_range: "88-90"
observed_text: "取阈值δ=0.05"
evidence: "参数δ直接设定为0.05，无来源说明、无推导、无敏感性分析，属于凭空设定"
recommended_action: "补充δ的来源（题设/文献/推导），或增加敏感性分析说明δ取值对结果的影响"
risk_if_ignored: "参数无依据，模型可信度受损"
```

**发现 G3-002**：
```yaml
status: TRUE_CURRENT
severity: HIGH
source_path: "sections/06_model_solution.tex"
line_range: "102-110"
observed_text: "由式(5)可得最优策略为..."
evidence: "式(5)到最优策略之间缺少关键推导步骤（状态转移方程未展开、边界条件未说明），推导跳步"
recommended_action: "补全中间推导：状态转移方程→贝尔曼方程→边界条件→最优策略"
risk_if_ignored: "推导链不闭合，评委无法复现模型"
```

**审查结论**：不通过（2 项 HIGH，推导链与参数来源均有问题）

---

## G5 论文与附录蓝图

**审查范围**：`appendix_plan.yaml`、附录章节、论文大纲

**发现 G5-001**：
```yaml
status: TRUE_CURRENT
severity: HIGH
source_path: "sections/appendix.tex"
line_range: "45-52"
observed_text: "\\begin{minted}{python}\ndef solve():\n    return result\n\\end{minted}"
evidence: "附录代码片段只有函数体，无输入输出说明、无参数含义、无依赖说明，无法独立理解"
recommended_action: "代码片段前补充输入参数、输出格式、依赖库说明；或选取更完整的核心代码段"
risk_if_ignored: "附录代码断裂，不符合可复现要求"
```

**发现 G5-002**：
```yaml
status: TRUE_CURRENT
severity: MEDIUM
source_path: "appendix_plan.yaml"
line_range: "10-12"
observed_text: "附录B：补充表格（仅1个表）"
evidence: "附录B只有单个表格独占一节，内容过薄，不符合'禁止少量文字或单表独占一节附录'的要求"
recommended_action: "将该表并入相关附录节，或补充更多补充结果/验证材料"
risk_if_ignored: "附录结构松散，影响专业性"
```

**审查结论**：有条件通过（需修复附录代码说明、合并薄附录节）

---

## G6 最终交付

**审查范围**：编译 PDF、支撑材料包、交付清单

**发现 G6-001**：
```yaml
status: TRUE_CURRENT
severity: BLOCKER
source_path: "build/main.pdf"
line_range: "p.12, p.15"
observed_text: "见图??（第12页）；如表??（第15页）"
evidence: "PDF 文本层中存在2处未解析引用（显示??），编译日志确认 Reference undefined"
recommended_action: "检查对应\\label是否存在、拼写是否正确，重新完整编译（xelatex→bibtex→xelatex→xelatex）"
risk_if_ignored: "正式交付 PDF 有引用断裂，严重影响专业性"
```

**发现 G6-002**：
```yaml
status: TRUE_CURRENT
severity: HIGH
source_path: "delivery/support_materials.zip"
line_range: "清单第3项"
observed_text: "清单列出 q3_sensitivity.py，但压缩包中实际文件为 q3_sens.py"
evidence: "支撑材料清单与实际压缩包内容不一致，文件名不匹配"
recommended_action: "统一文件名，或更新清单为实际文件名；重新生成压缩包并核对哈希"
risk_if_ignored: "交付包与清单不符，评委无法定位支撑材料"
```

**发现 G6-003**：
```yaml
status: TRUE_CURRENT
severity: MEDIUM
source_path: "build/main.pdf"
line_range: "全文"
observed_text: "正文共22页（不含附录、参考文献）"
evidence: "国赛正文要求25-30页，当前22页不达标"
recommended_action: "补充推导细节、敏感性分析、模型评价与推广内容，或检查是否有内容被错误压缩"
risk_if_ignored: "页数不满足竞赛硬性要求"
```

**审查结论**：不通过（1 项 BLOCKER + 1 项 HIGH + 1 项 MEDIUM，需全部修复后方可交付）
