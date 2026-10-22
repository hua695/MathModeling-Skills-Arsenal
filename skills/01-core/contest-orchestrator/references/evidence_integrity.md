# 证据完整性规范

本规范把“运行过、结果可追溯、结果仍然新鲜、论文数字有来源”分成四个状态，不把文件存在误认为计算已完成。

## 项目侧车文件

严格全流程在项目根目录使用以下结构；这些文件不属于论文正文，也不写入技能安装目录：

```text
.contest/
  runs/<run_id>/run_manifest.json
  run_manifest_report.json
  stale_evidence_report.json
  numeric_source_report.json
  readiness.json
numeric_source_map.json
```

`run_manifest.json` 由 `scripts/capture_run.py` 从已经执行的命令记录生成，不会替用户执行命令。清单中的输入、代码、配置和输出必须使用项目相对路径、SHA-256 和稳定 `ev:` ID；结果应通过 `source_ids` 指向输入/代码/配置证据。随机算法必须登记 seed；失败运行不能标记为 completed。

`numeric_source_map.json` 只登记论文中需要交付的量化结论。每项 claim 指向结果 JSON 文件和 JSON Pointer，并可给出正文锚点。审计器只核验声明值与来源值的一致性，不会替模型猜测、补造或改写数字。

## 门禁状态

- `EXECUTED`：有运行记录，但尚未完成证据校验；
- `VALIDATED`：运行清单、哈希和数字来源校验通过；
- `VERIFIED`：运行清单、哈希、数字来源三项证据校验通过；
- `DELIVERY_READY`：调用方已额外确认模型、论文、图表和引用等全部强制门禁通过；
- `BLOCKED`：任一来源缺失、哈希变化、数字漂移或失败运行未处理。

严格模式下，缺少运行清单、数字来源表或存在过期证据会阻断正式交付；普通回放保留可见 WARN，便于旧项目逐步迁移。该机制不规定全局图数、扰动比例、页数或文献数量，也不替代不同竞赛 profile 的规则。

需要将研究过程、模型限制和复现入口连成统一证据链时，按 `references/research_evidence_contract.md` 扩展现有运行清单、数字来源表和模型契约；不另建结果数据库。
