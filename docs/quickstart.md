# 按任务启动

先安装所需技能及其引用的依赖技能，打开新会话。宿主必须实际具备读取文件、运行脚本、编译或调用角色的工具；缺少能力时先补环境，不让 agent 伪填调用记录。

## MathorCup 全流程

```text
使用 contest-orchestrator，模式 full-contest-mathorcup。
题目在 ./inputs/problem.pdf，附件在 ./inputs/data/，
本届官方规则在 ./inputs/rules.pdf，正式工作目录为 ./contest/。
先完成 M1 题意、数据边界与规则确认，再按 M1–M5 推进。
论文使用 chapter_parallel：先建模求解，每章完整交给我批准；
批准后生成本章图表提示词，我亲自转交图表 agent。
下一章继续写，图件返修不暂停写作；摘要最后写。
```

期望先收到：题意划分、数据边界、缺失输入与待裁决事项。尚未有真实实验时，不应收到声称实验通过的最终论文。

## 单问模型选择

```text
使用 math-model-selector。目标是根据给定需求选择模型。
请先判断优化/预测/评价/分类任务，结合数据规模和约束，
输出“子问题、模型、选择理由、Python 库、备选方案”。
缺少数据时列出需要确认的字段，不编造模型精度。
```

## 科研数据图

```text
使用 scipilot-figure-skill 与 modelviz。
数据在 ./results/metrics.csv，包含 model、fold、rmse 三列。
读者需要比较相同验证折上的误差与波动。
先剖析数据并提出图表决策卡，再按模板生成 SVG/PNG 和复现脚本。
不要把折间波动自动称作置信区间，也不要把不同数据切分当公平比较。
```

## 正文局部审阅

```text
使用 academic-writing 审阅 ./paper/question1.tex。
冻结证据在 ./evidence/。只改普通正文，保护公式、数字、引用、图表与模型逻辑。
先指出主张、证据、解释和符号首用问题，再给局部修改。
材料缺失时报告缺口，不以修辞替代缺失推导。
```

## 选哪一种流程

| 场景 | 入口 |
| --- | --- |
| MathorCup 完整参赛 | `full-contest-mathorcup`，M1–M5 |
| 需要受控角色、回执与节点批准 | `full-contest-harness`，按实际环境满足能力要求 |
| 使用原协作节点 | `full-contest-4-18`，G0–G6，保留原流程 |
| 只求解、绘图、写作或审计 | 对应单项技能或 `subproblem` / `figures` / `paper` / `delivery-audit` |

主控中的固定模型配置、用户可直接进入的长期角色会话、宿主内部临时代理是不同能力。不要把内部 task ID 当作用户可访问的聊天链接，也不要把预载当成节点批准。
