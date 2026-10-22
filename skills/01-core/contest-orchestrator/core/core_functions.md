# 核心功能强制执行清单(Core Functions)
> **定位**: 本技能的核心功能(非可选)。每个功能 = 触发时机 + 必读文件 + 强制输出 + 验证脚本 + 门禁拦截。
> 判定: 任一核心功能未执行或验证 FAIL → 交付不合格(REJECTED)。
> CF = Core Function。每项核心功能都必须有触发条件、项目产物、验证脚本和阻断条件。

## 执行自检
交付前必须运行 `python scripts/check_core_execution.py <项目根>/competition_replay/<竞赛>_<年份>_<题号>/` 检查下列全部产物, 缺一 FAIL。

| # | 核心功能 | 触发时机 | 必读文件 | 强制输出(验证项) | 验证脚本 |
|---|---|---|---|---|---|
| CF1 | problem-parser | 开工第一步 | planner/problem_parser.md | problem_graph.md(含假设层) | check_core_execution |
| CF2 | 经验检索 | Fingerprint 出后立即 | memory/retrieval.py | experience_usage.yaml(n_matched/strategy_prior) | check_core_execution |
| CF3 | baseline-gate | 建模前 | executor/execution.md | baseline 结果落盘(先基线后复杂) | check_core_execution |
| CF4 | 求解落盘 | 每问求解 | executor/execution.md | results/q*_results.json + 求解脚本 | check_core_execution |
| CF5 | 数字一致性审计 | 写作后 | critic/criticism.md | 审计脚本全 PASS(数字=JSON) | scripts/consistency_check.py |
| CF6 | 硬性要求核对 | 写作后 | core/paper_hard_requirements.md | 9 项全 PASS | check_paper_hard_requirements.py |
| CF7 | 视觉契约核对(docx 管线) | 用户明确要求视觉检查时 | core/presentation_polish.md | 显式 `--visual-check` 后检查版面与代码块；未请求时记录跳过，文本层和结构检查仍执行 | docx_pipeline.py + check_visual_contract.py |
| CF8 | **academic-writing 表达校正** | 写作后、审计前 | academic-writing skill | ①论文不含 AI 套路词(脚本扫描) ②改后数字审计仍 PASS | check_core_execution(AI 词扫描) + scripts/consistency_check.py |
| CF9 | 记忆回写 | 比赛结束 | memory/memory.md | decision_log.md + snapshot.md + experience_usage.yaml | check_core_execution |
| CF10 | 交付门禁 | 交付前 | core/delivery_gate.md | 七步验收全过（delivery_gate.md 0-6） | delivery_gate 流程 |

## 防漏执行三层机制
1. **主流程编号**: SKILL.md 启动流程显式编号每一步(检索/写作/academic-writing/三核对/门禁), 跳过=违规。
2. **脚本验证**: 每个功能有可执行验证项(产物存在性 / 文本扫描 / 审计结果), 不是"自觉"。
3. **门禁拦截**: delivery_gate 七步验收, 任一 FAIL 打回, 不交付。

## 内容层自审参考（非门禁）
下列文件只在对应写作或审查环节按需读取，用于提升内容质量，不新增 CF 编号、不改变任何脚本判定：
- 论证主张是否有证据支撑：`references/paper_claim_review.md`
- 交付前四轮自审顺序：由 `academic-writing` 承接（`paper_self_review.md` 已迁入其 references）
- 表达去 AI 味：由 `academic-writing` 承接（`de-ai-writing.md`/`modules/humanizer` 已迁入），CF8 自动扫描仍只以 `core/aigc_risk_checklist.json` 的三个扫描字段为准
- 模型检验具体做法：由 `data-science-stack` 承接（`validation_methods.md` 已迁入其 references）
