# Skill 资源目录

`SKILL.md` 是执行路由；`manifest.yaml` 是机器可读文件清单；`VERSION` 是唯一版本来源；`scripts/script_registry.yaml` 是活动脚本分类登记表。

## 入口

| 目标 | 入口 |
|---|---|
| 范围判定 | `scripts/scope_router.py` |
| 完整交付 | `scripts/delivery_all.py` |
| Skill 健康检查 | `scripts/skill_health_check.py` |
| Skill 一致性检查 | `scripts/check_skill_consistency.py` |
| 隔离项目审计 | `scripts/audit_project.py` |

## 目录

| 目录 | 职责 |
|---|---|
| `core/` | 全局权限、状态、模型、论文、附录和交付契约 |
| `planner/` | 题目解析、选题、文献、符号和题型 profile |
| `executor/` | 求解、结果注册和可复现输出 |
| `critic/` | 证明链、一致性、摘要、合规和交付反馈 |
| `memory/` | 经验检索、replay、蓝图和校准数据 |
| `references/` | 参考材料、论文经验和竞赛 profile |
| `knowledge/` | 领域知识资产（节点按需加载） |
| `schemas/`、`templates/` | 结构约束和项目模板 |
| `scripts/` | 活动工具、门禁、回放和维护脚本 |

## knowledge/ 加载规则（节点强制契约）

领域知识资产不进入主流程上下文，由节点按需加载，并在 `harness_control.yaml` 节点登记 `knowledge_loaded`（检查器校验）：

| 目录 | 内容 | 加载节点 | 加载依据 |
|---|---|---|---|
| `knowledge/playbooks/` | 国赛 9 题型完整例题 | H5 解题参考 | 题面题型匹配对应 playbook |
| `knowledge/cookbooks/` | 机理/网络/聚类/博弈/评价 5 本算法手册 | H5 解题参考 | 题面本质匹配对应 cookbook |
| `knowledge/code-templates/` | evaluation + mechanistic 代码模板 | H5 代码生成 | 对应题型直接套用 |
| 子 skill 的 `references/cookbook-*` | optimization/statistical → heuristic；ml → data-science | H5 求解执行 | 按适配契约调子 skill |

项目运行产物、数据、论文和正式交付包必须位于项目工作区。技能目录只保存可复用规则、脚本、契约、模板、测试和已验证经验。
