# Data Acquisition Agent（第六角色：公开经验采集）

> 从公开数模论文/资料采集结构化经验，与真实比赛 replay 互补。
> 采集管线：搜索 → 原文来源 → LLM抽取 → 规则验证 → 人工审核 → memory

## 采集数据类型
| 类型 | 说明 | 进入 |
|---|---|---|
| 论文经验卡片 | 国赛/美赛/华数杯/电工杯/亚太杯优秀论文 → 结构化经验 | problem_graph / model_choice / decision_trace / failure / strategy |
| 模型选择经验 | 不同题型对应候选模型 + 决策规则 | planner |
| 失败案例 | 论文不足/误差/假设问题 → FD | failure_database |
| 方法适用条件 | 各方法适用场景与失败信号 | architecture selector |

## 质量门（防幻觉）
```
搜索 → 原文来源(URL/出处) → LLM抽取 → 规则验证(数值自洽) → 人工审核 → memory
```
- 必须标注来源与可信度
- 禁止编造实验结果
- 不复制论文全文，只抽结构化经验

## 采集入口

使用 `scripts/import_public_jsonl.py` 或 `scripts/import_public_experience.py` 将结构化内容写入 `memory/inbox/`，经来源、重复、数字和隐私检查后再合入正式库。

## 分工建议（多模型）
| 模型 | 任务 |
|---|---|
| Claude | 论文结构化抽取 |
| GPT | 经验卡片生成 |
| Gemini | 搜索与资料整理 |
| 本地模型 | 分类/去重/embedding |
