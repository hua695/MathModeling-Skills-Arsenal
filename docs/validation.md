# 验证结果与适用边界

## 检查的含义

本仓库的测试检查流程契约和工具行为，例如未批准就派发下一章、遗漏冻结输入、修改已批准正文、使用旧图件版本时应被拒绝。这些检查不能证明模型精度、获奖概率、长篇论文质量或某一宿主的真实多角色调用已发生。

`examples/chapter-parallel` 使用可复算的合成线性数据，其误差为零源于数据构造方式。示例中的正文、交接提示词不构成真实比赛记录或自动生成质量评测。

## 本轮记录

同步前的维护环境为 Windows、Python 3.13：MathorCup 140 项、Harness 106 项相关测试通过；严格 smoke 和机理、优化、预测三类 replay 通过。完整检查点运行 617 项，其中 616 项通过，一项原有一致性检查失败；其后新增两项返修链测试由最终 MathorCup 套件覆盖。

这些是维护检查，不是本届比赛的重训、正式论文编译或提交验证。公开副本的复查结果记录在同目录 [public-validation.json](public-validation.json)。CI 从公开副本重新运行相关套件，不依赖维护者的本地路径。

## 已知发布阻碍

- 主控 `VERSION` 与 manifest 登记 4.18，SKILL 元数据为 4.19，发布登记尚未统一。本次更新不提升稳定版版本号。
- 15 个历史维护脚本尚未在技能内部 registry 分类。严格 health 共报告 17 个条目，包含重复的版本一致性发现。
- 因此，针对相关流程的 CI 通过不等于完整发布检查通过。全量失败项为 `test_current_skill_passes_strict_consistency_audit`。
- 临时工程代理与用户可直接进入的长期角色会话不是同一能力。MathorCup 本次独立工程审查代理因工作区额度限制未完成最终审查；本地测试不冒充独立签署。

## 本地复现

```bash
python -m pip install pyyaml
python scripts/check_repository.py
python examples/chapter-parallel/calculate.py
cd skills/01-core/contest-orchestrator
python -m unittest discover -s tests -p 'test_mathorcup*.py'
python -m unittest discover -s tests -p 'test_harness*.py'

# 完整检查：目前预期会报告上面的既有一致性阻碍。
python -m unittest discover -s tests -p 'test_*.py'
python scripts/skill_health_check.py . --strict --smoke
python scripts/replay_profiles.py --strict
```

科研绘图需要真实数据、语义与视觉 QA；LaTeX 交付还需要真实编译、字体、SVG 转换和引用检查。仅源码检查或测试夹具中的 PDF 不能被称作可提交论文。
