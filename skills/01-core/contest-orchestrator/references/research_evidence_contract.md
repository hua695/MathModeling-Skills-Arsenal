# 研究证据链契约

本契约将文献、模型、计算结果和论文表述连接为可核验链路。它复用项目已有的 `references.yaml`、`citation_map.json`、`model_contract.yaml` 与 `.contest/runs/*/run_manifest.json`，不新增平行数据库。

## 启用方式

需要完整研究审计的项目显式运行：

```text
python scripts/check_research_evidence.py <项目根> --strict
```

完整交付流程使用：

```text
python scripts/delivery_all.py <项目根> --strict --research-evidence-strict
```

该门禁属于 v4.18 的完整审计增强；未显式启用时，基础流程保持兼容。

## 来源记录

`references.yaml` 的每条正式来源记录使用以下规范字段：

```yaml
citation_key: "稳定引用键"
title: "完整题名"
authors: "作者"
venue: "期刊、会议、标准组织或平台"
year: 2024
status: peer_reviewed # peer_reviewed|preprint|standard|dataset|software|web
doi: ""
url: "官方或可核验链接"
relevance: "与当前问题和小问的关系"
key_points: "实际支撑的关键方法、数据或结论"
limitations: "来源自身的局限或适用边界"
used_in: [section_Q1_modeling]
verified_at: "核验时间；未完成核验时保留为空"
```

`doi` 与 `url` 至少提供一项。`status` 是来源分类，不等同于仅凭检索元数据证明同行评审；来源的 `verification_status` 仍需保留。文献用于正文前，必须完成题目相关性、关键点、局限和实际使用位置登记。

## 主张—证据—位置—用途

在现有 `citation_map.json` 中登记 `claim_evidence`：

```json
{
  "claim_id": "claim:score",
  "claim": "论文中的可核验主张",
  "claim_type": "direct",
  "evidence": [{
    "source_id": "ev:result.score",
    "locator": "results/result.json#/score",
    "use": "支持主结果"
  }],
  "location": {"file": "paper.tex", "anchor": "claim:score"},
  "use": "Q1 主结果",
  "recomputable_from": []
}
```

每条主张必须说明证据 ID、证据定位、论文位置和证据用途。差值、比值、排名、区间和比较结论将 `claim_type` 设为 `derived`、`comparison` 或 `ranking`，并在 `recomputable_from` 中写明输入证据和计算关系，禁止只登记最终数字。

## 限制性分析

启用研究证据链时，`model_contract.yaml` 顶层登记 `research_evidence_version: "1.0"`；每个 `subproblems` 项登记：

```yaml
limitations:
  assumptions: "模型依赖的假设"
  applicable_conditions: "假设成立和模型有效的条件"
  failure_conditions: "可能失效的情形"
  impact_direction: "失效对结果方向或不确定性的影响"
  mitigation: "检验、敏感性分析或替代处理"
```

五个字段均应针对当前小问，不能用通用套话替代。模型章节应把限制性分析与假设、参数、检验和结论范围相互引用。

## 复现性证据

每个用于论文结果的运行清单，在已有输入、代码、配置、输出和 `evidence` 之外，登记：

```json
"reproducibility": {
  "entrypoint": "solve.py",
  "inputs": ["inputs/raw.csv"],
  "parameters": [],
  "seed": 7,
  "command": ["python", "solve.py"],
  "outputs": ["results/result.json"],
  "figure_scripts": ["figures/plot.py"],
  "result_paper_map": [{
    "claim_id": "claim:score",
    "output_evidence_id": "ev:result.score",
    "paper_location": "paper.tex#claim:score"
  }]
}
```

`entrypoint`、输入、输出和绘图脚本使用项目相对路径；随机过程显式登记 `seed`，确定性过程也保留该字段并填 `null`。`result_paper_map` 将结果证据绑定到论文主张，保证代码、结果、图表和正文数字可以沿同一链路回查。

## H5 结果追溯包

Harness 的 H5 节点必须登记 `run_manifest`，并运行 `scripts/check_h5_result_traceability.py <项目根> --strict`。运行清单至少包含：`status: verified`、`node_id: H5`、显式 `seed`、可执行 `command`、带 `path` 与 `sha256` 的主结果、`formal_tests.record_fields`、正式记录的结果文件哈希和 `formal_interpretation_boundary`。结果包还必须通过 `model_contract_sha256` 将模型契约与结果绑定，并登记已核验的 `sensitivity_report.yaml` 或 `robustness_report.yaml`，包含 `canonical_report` 的路径与 SHA-256、方法、模型契约哈希和非空扰动结果。

该检查器只读取项目文件并返回 `PASS`、`PAUSE` 或 `BLOCK`：缺少证据保持 `PAUSE`，路径越界、文件不存在、格式错误或 SHA-256 不一致为 `BLOCK`。H6 仍需在独立实例中核验这些记录；H5 结果追溯通过不替代 H6、H8 或 H9 门禁。

## 检查边界

该契约只检查字段完整性、路径安全、证据 ID、位置和关系是否可追溯，不替代数学正确性、来源真实性、论文表达审阅或图表视觉检查。它本身不触发视觉检查；图表视觉检查按 `references/figure_policy.md` 执行，其他流程只有用户明确要求或显式传入 `--visual-check` 时启用。
