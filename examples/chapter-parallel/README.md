# 一个可复算的章节交接示例

本目录使用手工构造数据，展示交付物的内容与边界。正文和提示词是维护者编写的示例，不是一次真实比赛、自动生成质量评测或已发生的人工批准记录。

运行：

```bash
python examples/chapter-parallel/calculate.py
```

数据关系为 $y=2x+1$，前五个点用于拟合，最后一个点留作演示检查。脚本输出斜率 2、截距 1、留出点预测 13、误差 0。无噪声的构造数据不能用于证明真实泛化能力。

| 阶段 | 可直接查看的输出 | 使用者决定 |
| --- | --- | --- |
| 写作准备 | 全文计划中先写模型章，摘要排在最终目录前部但最后创作 | 批准论证路线 |
| 章节交付 | [模型建立与求解正文](chapter.md) | 审阅完整章节后决定是否继续 |
| 章节获批后 | [图表提示词示例](figure-prompt.md) | 将提示词转交图表角色 |
| 图件返修 | 生成 r2 提示词，保留 r1 的历史 | 选择图件；后续章节仍可继续 |
| 最终整合 | 对照最新请求、选定资产与章节正文接图 | 全文终审与交付批准 |

真实项目中的批准需要使用者实际作出，并绑定当前文件哈希。本目录不附伪造批准日志。实际字段分别见 [MathorCup 契约](../../skills/01-core/contest-orchestrator/references/mathorcup_chapter_parallel.md) 与 [Harness 契约](../../skills/01-core/contest-orchestrator/references/harness_chapter_parallel.md)。
