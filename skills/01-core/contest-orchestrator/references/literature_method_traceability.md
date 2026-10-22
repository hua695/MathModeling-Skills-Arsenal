# 文献需求、摘要整合与方法迁移门禁

## 强制规则

1. 主 Agent 先生成 `literature_request.md`、`literature_request.yaml` 和 `literature_agent_prompt.md`，按每个小问列出检索方向、中文/英文数量、方法依据、应用/参数先例和可选对比边界。所有 Harness profile 合计硬范围为 6–11 篇，推荐 8–10 篇；中文文献按小问至少各覆盖 1 篇，英文文献不设硬性最低数量但建议覆盖全部小问。
2. 用户负责检索和下载全文；用户指定的文献 agent 负责阅读全文并回传 `title`、`authors`、`venue`、`year`、`doi_or_url`、`abstract`、`full_text_summary`、`method_summary`、`data_summary`、`limitations`、`evidence_locators` 和 `candidate_questions`。主 Agent 不联网检索、不下载、不读取或解析全文。
3. 用户将上述结果保存为 `literature_sources.yaml` 或等价 JSON。主 Agent 只读取摘要和结构化全文总结；缺少来源元数据、摘要、总结、方法、数据、局限或定位信息时返回 `PAUSE`，不得根据题名或搜索结果页补写结论。
4. 每条文献生成稳定的 `citation_key`，并同步写入 `references.yaml`、`citation_map.json` 和 `method_transfer_map.json`。建模与求解正文必须用该 key（或对应顺序编码 ref_ID）引用文献，不能只把文献堆在文末。
5. 每个子问题都必须对相关方法作出 `adopt`、`adapt` 或 `reject` 决定。`adopt` 要写明采用的方法和适用边界；`adapt` 还必须写 `innovation_delta`；`reject` 必须写出技术理由。
6. 文献解锁后、模型路线确定前，必须完成文献使用登记：每个子问题至少绑定一条 `adopt`/`adapt` 方法证据和一条实际数据、参数、测量先例或基准证据，分别写明 `citation_key`、证据定位、模型组件/数据字段和具体使用方式。只有文献综述或引用而未进入模型、代码、参数、数据或验证设计的条目，不算使用。

## 产物与门禁

- `literature_pause.json`：硬暂停状态、缺失原因和恢复文件。
- `literature_request.md`：用户和文献 agent 可直接执行的中英文检索提示词与提交格式。
- `literature_request.yaml`：按小问登记的数量、角色和关键词需求。
- `literature_agent_prompt.md`：交给全文文献分析 agent 的固定提示词。
- `method_transfer_map.json`：中文文献→子问题→模型决策的结构化登记。
- `literature_sources.yaml`：用户提交的元数据、摘要和结构化全文总结。
- 文献使用登记：文献方法、数据/参数证据→子问题→模型组件、数据字段或验证设计的落地映射。
- `model_contract.yaml`：每个 `Qn` 的 `literature_basis` 与 `innovation_delta` 正文证据卡。
- `check_model_traceability.py --strict`：核验中文数量、逐题决策、正文作用说明和引用；`delivery_all.py --strict` 自动启用此参数。

该门禁只校验可追溯证据，不替代人工判断文献是否真正适合本题。方法迁移记录必须和实际代码、结果及模型约束保持一致。
