# Citation and DOI policy

Count unique citation keys that occur in the paper and resolve to entries in the BibTeX database. Repeated `\\cite` commands never increase the count. Every cited key must have a bibliography entry, and every formal bibliography entry should be cited unless explicitly marked as an appendix-only source.

Offline checks validate DOI syntax, duplicates, and required metadata fields. `--doi-online` additionally resolves DOI URLs. Network failures are `WARN/UNVERIFIED`; HTTP not-found, malformed DOI, fabricated records, and severe metadata mismatch are failures.

参考文献数量只统计正文引用命令实际调用的唯一 BibTeX 键；`.bib` 中未被正文调用的条目不能满足数量下限。正文引用键不存在于 `.bib` 时直接 FAIL，报告同时给出 `unique_cited_keys`、`unused_bib_keys` 和 `unknown_citation_keys`。

## 文献作用与语言门禁

每个被引用的键都必须在 `citation_map.json` 中登记 `role`，并在正文对应句子中明确它的作用，例如 `method_basis`（理论或模型依据）、`parameter_source`（材料参数来源）、`measurement_precedent`（测量先例）、`selection_criterion`（模型选择准则）、`solver`（算法实现依据）或 `comparison_boundary`（适用边界）。只在段末放置 `[n]` 而没有说明“该文献支持了什么、本文采用了什么、哪些内容没有照搬”，不能通过引用审计。

竞赛题面、附件说明、竞赛通知和“某年度某题题名”不是学术参考文献，不得写入正式 `.bib`，也不得用来填充文献数量。题面条件在正文中属于输入资料，不用学术引用伪装；如需追溯题面，应在项目证据目录登记原始文件，而不是把它列入参考文献表。这条规则优先于外部文档中“必须把赛题原始文档列为参考文献”的建议，因为用户已明确禁止这类题面条目进入论文。

## 正文引用落地规则

1. **引用对象**：外部理论、已有模型、算法、行业结论、公开材料参数、公共数据集或测量先例必须引用；完全由本文推导的公式和自研流程不强行添加引用。
2. **引用位置**：引用紧跟其支持的事实或判断，并置于句末标点之前，例如“该色散式作为参数来源\cite{key}。”；不能把多个无关编号集中堆到段末。
3. **作用说明**：引用所在句或紧邻句必须说明文献承担的作用：`method_basis`、`parameter_source`、`measurement_precedent`、`selection_criterion`、`solver` 或 `comparison_boundary`。只有编号而没有作用说明，按“挂名引用”处理。
4. **一一对应**：正文实际调用的唯一键与文末条目必须一一对应；正式交付的 `.bib` 条目都必须在正文被调用。仅供内部附录使用的资料不得混入正式参考文献表。
5. **编号与格式**：具体使用上角标、方括号或顺序编码，服从竞赛模板和 `gbt7714` 样式；无论视觉样式如何变化，引用位置、唯一编号和正文—文末对应关系不得变化。

## 国赛 2026 AI 说明边界

国赛 2026 的 AI 工具使用声明不要求把 AI 工具作为参考文献条目列入 `.bib` 或参考文献表。AI 工具的合规信息通过正文中参考文献前的“AI工具使用声明”和支撑材料中的 `AI工具使用详情.pdf` 提供；只有当 AI 工具本身是独立的软件、数据或研究来源且正文确实引用其技术内容时，才按普通来源规则处理。

声明和详情应覆盖实际使用过的工具及用途范围，关键交互以摘要形式记录，并说明采纳、人工修改和核验情况。可以强调参赛队主导核心建模、分析和结论，但不得把已发生的 AI 使用写成未使用或故意省略必要字段。

## 用户负责检索，系统只做摘要级整合

主 Agent 先生成 `literature_request.md` 与 `literature_request.yaml`，明确中文/英文数量、每个小问的覆盖角色、检索关键词和可直接交给文献 agent 的提示词。用户负责检索和下载全文；文献 agent 负责阅读全文并回传摘要、方法、数据、适用边界和定位信息。主 Agent 只接收 `literature_sources.yaml` 中的题名、作者、来源、年份、DOI/官方链接、摘要及结构化全文总结，不主动联网检索、不替用户下载、不读取或解析全文。

所有 Harness profile 的文献总数硬范围为 **6–11 篇**，其中 **8–10 篇为推荐范围**；中文文献必须覆盖每个小问，每个小问至少 1 篇；英文文献不设硬性最低数量，但建议覆盖全部小问。推荐数量和英文全小问覆盖仅产生建议状态，不阻断节点。任何计入总数的文献必须同时具备稳定 `citation_key`、原文定位、`use_in_paper` 和 H5 的实际落位记录（原H4职责已并入H5阶段一）。硬条件不满足时保持 `PAUSE`，不得用题面、竞赛通知、博客、搜索结果页或占位条目替代。

摘要和外部 agent 的全文总结只能支持已回传内容；涉及未回传的定理条件、实验细节、参数来源或结论，不得写成已核验事实，必须登记为待补充或不采用。

解锁后必须生成 `method_transfer_map.json`。每个子问题对相关中文方法填写 `adopt`、`adapt` 或 `reject`；`adapt` 要有 `innovation_delta`，`reject` 要有技术理由。严格交付会检查该表、模型契约中的 `literature_basis`/`innovation_delta`，以及模型建立与求解正文的引用和作用说明。

每条文献还必须有稳定的 `citation_key`，并在 `references.yaml`、`citation_map.json`、`method_transfer_map.json` 和 `.bib` 之间保持一致。采用或改造的方法必须在对应模型小节出现 `\cite{citation_key}` 或等价的顺序编码引用；仅在文献综述中引用、不在模型正文中落地，不算方法使用。

需要完整研究证据链时，来源记录补充 `title`、`authors`、`venue`、`year`、`status`、`doi`、`url`、`relevance`、`key_points`、`limitations`、`used_in` 和 `verified_at`，并在现有 `citation_map.json` 中登记主张—证据—位置—用途映射。字段和严格检查规则见 `references/research_evidence_contract.md`。
