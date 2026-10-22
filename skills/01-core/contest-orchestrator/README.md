# contest-orchestrator

数学建模竞赛唯一主控 skill。完整执行规则见 [SKILL.md](SKILL.md)，机器可读路由见 [manifest.yaml](manifest.yaml)。当前稳定版本由 [VERSION](VERSION) 声明。

## 常用入口

```text
python scripts/scope_router.py --prompt "用户原话" --workspace <项目根>
python scripts/mode_router.py --mode <mode> [--variant <variant>]
python scripts/delivery_all.py <项目根> --strict
python scripts/skill_health_check.py . --strict --smoke
python scripts/check_skill_consistency.py . --strict
```

主会话管理范围、事实、权限、节点和交付；fork 分支执行授权的赛题、实验、图表和论文节点。论文写作链为 `academic-writing` 数模学术写作适配层 → 必要时 `humanizer-zh`。

## 目录

- `core/`：权限、状态、模型、论文、附录和交付契约。
- `planner/`：题目解析、题型 profile、选题、符号和文献。
- `executor/`：baseline、求解、结果登记和可复现输出。
- `critic/`：评审、证明链、一致性、摘要和合规检查。
- `memory/`：经验检索、蓝图、replay 和校准数据。
- `references/`：按需加载的执行规范、适配契约和模板。
- `scripts/`：登记的路由、门禁、回放和维护工具。

正式项目、数据、replay 和交付包必须写入项目工作区，不写入 skill 安装目录。
