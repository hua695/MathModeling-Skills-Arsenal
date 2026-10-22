# 数字冻结机制

数字冻结机制保证论文关键数字有唯一来源，并阻止源数据、代码或参数变化后论文继续使用过期结果。

## 核心规则

1. 论文关键数字必须登记在 `frozen_numbers.json`，并追溯到结果文件。
2. 冻结后不得直接改动结果口径；源文件、代码或参数变化时，先在 `frozen_changelog.jsonl` 登记原因，再重新生成冻结表。
3. 写作阶段只从冻结表或其权威结果源取数，不手工凭记忆填写。
4. 交付前运行数字来源检查；未匹配数字只能进入人工复核，不能自动视为一致。

## 文件约定

| 文件 | 位置 | 说明 |
|---|---|---|
| `frozen_numbers.json` | `<项目根>/competition_replay/<竞赛>_<年份>_<题号>/` | 冻结数字表 |
| `frozen_changelog.jsonl` | 同上 | 每次重新冻结的原因 |
| 结果源文件 | `results/` 或求解落盘目录 | 数字来源及文件哈希 |

## 数据结构

```json
{
  "competition": "cumcm",
  "frozen_at": "2026-09-12T10:00:00",
  "source_files": {"results/q1.json": "<sha256>"},
  "numbers": [
    {"key": "q1_metric", "value": 0.9342, "unit": "", "source": "results/q1.json"}
  ],
  "policy": "变更先登记原因，再重新冻结"
}
```

## 使用流程

```text
python scripts/freeze_numbers.py freeze <结果目录> --out <冻结表路径>
python scripts/freeze_numbers.py check <论文目录> --frozen <冻结表路径>
python scripts/freeze_numbers.py changelog <冻结表路径> --reason "说明变更原因"
```

重新冻结前必须完成变更登记。冻结表与 `delivery_gate.py`、结果代码一致性检查、数字来源审计和 replay 配合使用；冻结表是代码结果进入论文的唯一数字通道。
