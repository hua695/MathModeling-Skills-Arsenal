# 交付验收门禁

正式交付由 `python scripts/delivery_all.py <项目根> --strict` 统一驱动。任一强制门禁 `FAIL` 或高风险 `WARN` 都阻断交付；单独脚本只用于定位问题。

## 验收顺序

0. `check_skill_consistency.py --strict`：版本、声明路径、活动脚本分类和运行时路径。
1. `check_core_execution.py <replay>`：题目解析、经验使用、baseline、结果、论文节点和回写产物。
2. 编译当前论文，检查 PDF 新鲜度、非图片文本层和文件大小。
3. `competition_gates.yaml`：profile 页数、结构、标题、匿名字段和竞赛格式。
4. `check_paper_hard_requirements.py`：profile 启用的摘要、关键词、图表、字体、附录和 AI 说明。
5. `check_literature_citation.py --strict`：引用键、正文作用、来源真实性和引用位置。
6. `check_modeling_contract.py`、`check_modeling_solution_contract.py --strict`：模型章节、子问题证据、原始关系、推导链、算法、参数和结果。
7. `check_model_evidence.py`、`check_derivation_chain.py`、`check_symbol_consistency.py`、`check_interface_contract.py`：模型、公式、符号、单位和跨问接口。
8. `check_tex_layout_patterns.py --strict`、`check_tex_references.py`、`latex_warning_check.py`：浮动体、分页、标签、引用和 overfull。
9. `check_latex_appendix_contract.py --strict`：附录输入、编号、正文引用、材料清单、核心代码和 minted 契约。
10. `check_anonymity.py`、`check_submission_meta_text.py`：正文、附录、源文件、PDF 元数据和交付目录。
11. `consistency_check.py`、`audit_numeric_sources.py --strict`、`figure_registry.py`：数字、结果、图表、来源和代码一致性。
12. `check_ai_compliance.py`（国赛 2026 profile）：参考文献前 AI 声明、支撑材料详情、真实披露和人工核验；不要求 AI 工具参考文献条目。
13. `check_formal_delivery_drift.py --strict`：正式交付 PDF、索引和当前源文件哈希一致。
14. 人工文本抽检：摘要、公式、符号、图表解读、引用作用、适用边界、附录覆盖和内部流程词。

## 硬性判定

- 模型、数据、代码、结果、图表、引用、公式、符号、单位和附录任一无法追溯，阻断。
- 标题、匿名、摘要、关键词、页边距、表格、附录或 AI 工具说明不符合启用的官方 profile，阻断。
- 正文或正式交付包含评审、用户、agent、提示词、交接、修改轮次、调试、失败尝试、旧版本、内部讨论或元话语，阻断。
- 正式交付与当前源文件、结果或索引漂移，阻断。
- 国赛 2026 论文为图片型 PDF、超过 20 MB、正文（正文主体、AI 声明和参考文献；摘要不计）超过 30 页，或支撑材料压缩包超过 20 MB，阻断。按湖南赛区当前确认口径，提交论文文件总页数超过 51 页也阻断；该总页数规则与全国正文页数规则分开计算。

## 视觉边界

文本层、结构、公式、数字、引用、来源和图表登记检查始终执行。图表按 `references/figure_policy.md` 默认执行渲染复核和视觉质检；论文、建模、求解、文献、评审及文档等非图表流程默认关闭视觉检查，用户明确要求或显式提供 `--visual-check` 时才启用。视觉检查不能替代其他门禁。
