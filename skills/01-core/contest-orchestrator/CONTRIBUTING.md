# 经验与框架贡献规范

贡献内容必须是可核验、可复用、去身份化的规则或经验卡片。论文、运行目录、原始数据、评审对话、提示词和内部交接不直接进入 skill。

## 经验卡片

```yaml
method: 使用的方法
failure: 可观察的失败现象
cause: 已核验的原因
signal: 事前可识别信号
lesson: 可迁移规则
avoid: 下一次的具体动作
source: 来源、竞赛、年份或项目证据
verified: true|false
```

成功经验使用 `outcome`、`why_it_worked` 和 `reproduce`；策略经验使用 `when_to_use`、`how_to_apply`、`risk` 和 `evidence`。未经核验的内容只能进入 `memory/inbox/`，不能直接进入正式库。

## Replay

真人 replay 只保留匿名的阶段、决策、证据、结果、风险和可迁移结论。原始聊天、身份信息、未确认方案和调试记录不得入库；失败实验必须先蒸馏为失败模式和防护规则。

项目侧 replay 至少包含题目条件、关键决策、结果来源、验证状态和最终复盘。正式经验写入项目工作区或经审核后进入 `memory/`，不写入技能安装目录的运行产物区。

## 导入与审核

公开经验：

```text
import_public_jsonl.py → memory/inbox/ → merge_inbox_to_memory.py → 人工审核 → 正式库
```

个人经验包使用 `scripts/import_experience.py`，必须提供来源和结构化字段。入库前检查来源、重复、占位内容、数字真实性和隐私；导入脚本不得把历史变更日志写回 skill。

## 框架修改

新增或修改入口、契约、门禁、schema、模板或测试时：

1. 更新对应权威文件；
2. 更新 `manifest.yaml` 或 `scripts/script_registry.yaml`；
3. 增加静态检查、负例或 replay 证据；
4. 运行 skill 健康检查和一致性检查。

只保留已验证规则。版本升级必须遵守 `SKILL.md` 的发布验收流程；稳定版本当前为 `4.18`。
