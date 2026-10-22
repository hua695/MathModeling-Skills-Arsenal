# 脚本目录

活动脚本的完整分类以 `scripts/script_registry.yaml` 为准。以下入口用于常规执行：

| 目的 | 脚本 |
|---|---|
| 范围与输入门 | `scripts/scope_router.py` |
| 完整交付 | `scripts/delivery_all.py` |
| 项目只读审计 | `scripts/audit_project.py` |
| 运行清单与证据 | `capture_run.py`、`check_run_manifest.py`、`check_h5_result_traceability.py`、`check_stale_evidence.py`、`build_evidence_index.py` |
| 数字与引用来源 | `audit_numeric_sources.py`、`verify_doi.py`、`consistency_check.py` |
| 模型与推导 | `check_modeling_solution_contract.py`、`check_derivation_chain.py`、`check_dimension_consistency.py` |
| 摘要与论文 | `check_abstract_contract.py`、`check_paper_integrity.py`、`check_latex_appendix_contract.py` |
| 图表与版面 | `figure_registry.py`、`latex_warning_check.py`、`check_page_margins.py`、`check_tex_references.py` |
| Skill 验收 | `skill_health_check.py`、`check_skill_consistency.py`、`smoke_test.py`、`replay_profiles.py` |

所有脚本从自身路径、显式参数或环境变量解析路径；正式项目路径必须由用户提供。默认不执行视觉渲染和截图，除非用户明确要求。
