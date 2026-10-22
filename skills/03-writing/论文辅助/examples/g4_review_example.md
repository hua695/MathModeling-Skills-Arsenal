# G4 结果与图表节点审查示例

本示例展示 paper-assistant skill 的一次完整审查过程。

---

## 1. 审查请求

**用户输入**：
```
审查 G4 结果与图表节点，检查结果是否真实、图表是否正确。
```

---

## 2. 审查范围

| 项目 | 内容 |
|---|---|
| 审查节点 | G4 结果与图表 |
| 审查文件 | `sections/06_model_solution.tex`, `sections/07_validation.tex` |
| 结果文件 | `results/baseline_result.json`, `results/g4_result_register.json` |

---

## 3. 四项检查发现（示例）

### A. 符号完整性

| 符号 | 首次出现 | 符号表 | 状态 |
|---|---|---|---|
| $T_k(x;p)$ | 6.1.2 | ✗ 未在表3 | HIGH |
| $V(\sigma)$ | 6.2.2 | ✓ 表3 | OK |

**发现 A-001**：
```yaml
status: TRUE_CURRENT
severity: HIGH
source_path: "sections/06_model_solution.tex"
line_range: "120-125"
observed_text: "令T_k(x;p)表示真实次品率为p时，以累计次品数x到达第k个报告阶段的概率"
evidence: "符号表（04_symbols.tex）中未定义T_k(x;p)"
recommended_action: "在符号表中添加T_k(x;p)的定义"
risk_if_ignored: "评委无法快速定位符号定义，影响论文规范性"
```

### B. 元话语检查

**发现 B-001**：
```yaml
status: TRUE_CURRENT
severity: HIGH
source_path: "sections/07_validation.tex"
line_range: "45-46"
observed_text: "该表只反映首阶段样本量，不能据此把某一分配称为全局最优"
evidence: "属于边界提醒类元话语，'不能据此'是对读者的提醒"
recommended_action: "改为客观陈述：'表中数据对应首阶段样本量'"
risk_if_ignored: "元话语影响论文客观性"
```

### C. 负向回声检查

**发现 C-001**：
```yaml
status: TRUE_CURRENT
severity: HIGH
source_path: "sections/06_model_solution.tex"
line_range: "89-90"
observed_text: "本文将前四个观察时点作为报告窗口，但这里不把未报告阶段外推为全程ASN"
evidence: "包含被否决的方案描述，属于中间修改过程残留"
recommended_action: "删除整句，直接陈述前四个观察时点的计算结果"
risk_if_ignored: "暴露内部讨论痕迹，产生负向回声"
```

### D. 模型证据检查

| 论文数字 | 位置 | 结果文件 | 可复现 | 状态 |
|---|---|---|---|---|
| 60.222元/件 | 6.3.3 | q3_optimal.json | ✓ | OK |
| 27648个策略 | 6.3.2 | 代码枚举 | ✓ | OK |
| 173.683件 | 6.1.3 | q1_oc_curve.json | ✗ | UNVERIFIED |

---

## 4. STALE_REPORT 标记（示例）

> 以下问题来自历史子Agent报告，但与当前源文件冲突，已排除。

**S-001**：
- 原报告声称："第113行ranked[0]未修复"
- 当前源文件状态：第113行已正确写为ranked[0]
- 处理：排除，不进入修改清单

---

## 5. 审查结论

| 严重程度 | 数量 |
|---|---|
| BLOCKER | 0 |
| HIGH | 4 |
| MEDIUM | 3 |
| LOW | 0 |
| STALE_REPORT | 1 |
| UNVERIFIED | 1 |

**审查结论**：有条件通过

**修改清单（共7项）**：
1. H-001：符号表添加$T_k(x;p)$定义
2. H-002：删除"该表只反映...不能据此"元话语
3. H-003：删除"本文将前四个观察时点...但这里不把"负向回声
4. H-004：图4中'Q2'改为'问题二'
5. M-001：符号表添加$\alpha_{A,k}$定义
6. M-002："本节表格和图形只报告"改为客观陈述
7. M-003：人工核实173.683件的计算来源

---

## 6. 使用说明

本示例展示了skill的标准工作流程：
1. 接收审查请求，自动加载对应节点的检查重点
2. 读取当前源文件，计算哈希，确保基于最新版本
3. 执行四项检查（A符号、B元话语、C负向回声、D模型证据）
4. 标记STALE_REPORT（基于旧版本的问题）
5. 只有TRUE_CURRENT且有明确证据的问题进入修改清单
6. 输出JSON+MD双格式报告

用户（或主agent）根据修改清单执行修改后，可再次调用skill进行回验。
