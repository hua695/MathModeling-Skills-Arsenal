# 论文模式

只处理论文结构、学术表达、公式符号、图表说明、排版或论文审阅。

- 先确认当前模型、数字、图表和引用已冻结；缺少上游证据时停止写作并报告缺口。
- H7 先由图表 agent 生成 `visual_argument_plan.yaml`，每个图槽位填写 `figure_intent`，提交 `.contest/reviews/H7_visual_plan_review_packet.yaml`，并以 `.contest/approval_log.yaml` 中 `H7_VISUAL_PLAN` 的当前哈希批准记录为准；完成该独立批准后才允许生成图表。数据结果图在计划批准后调用 `scipilot-figure-skill` 生成决策卡并执行数据图质检，流程图/技术路线图调用 `tech-route-maker`，机制/几何/公式示意图调用 `tikz-scientific-figures`。H8A 再由 `academic-writing` 生成 `paper_argument_blueprint.yaml`、经用户批准的 `paper_author_brief.yaml` 和 `abstract_argument_card.yaml`。H8B 论文 agent 每次只读取当前 `chapter_writing_card.yaml`、哈希绑定的 `paper_continuity_context.yaml`、经 H6 核验的 `model_summary_cards.yaml`、摘要论证卡、视觉论证计划和卡内冻结材料，且每张章节卡必须登记 `abstract_contribution`。遵循 [H8 写作者优先协议](../h8_writer_first_protocol.md)，不重新设计模型，也不把质量检查清单写成正文任务。H8C 先通读完整论文，依据摘要论证卡和章节摘要贡献最后写摘要，再由 `academic-writing` 独立编辑并运行严格摘要检查。按需材料见 [H8 章节执行协议](../h8_chapter_execution.md)。
- 论证中心编辑按需调用 `academic-writing/modules/claim-centered-editing/MODULE.md`：先登记主张、证据锚点、范围和作者确认项，再只修改普通正文；公式、数字、引用、表格、图表和模型逻辑保持冻结。
- 内容层按需参考，不改变固定链路与冻结要求：主张证据判定读 `references/paper_claim_review.md`；交付前自审、表达去痕、摘要写作由 `academic-writing` 承接（`paper_self_review.md`/`de-ai-writing.md`/`abstract-writing.md` 均已迁入其 references）；模型检验表述由 `data-science-stack` 承接（`validation_methods.md` 已迁入）。国赛摘要写作保留硬要求：禁止公式、每问方法名+创新点+量化结果。
- 固定论文链路为：`model/results/citations frozen → H5 结果解释卡 → H6 核验 → academic-writing 论证蓝图与作者简报 → 论文 agent 按章节卡写作 → academic-writing（含 claim-centered-editing 论证中心编辑）→ mathmodel_patch_guard → humanizer-zh → integrity/delivery gates`。
- 写作顺序固定为：先正文各章（按章节素材索引逐章取用）、再附录、最后写摘要。摘要论证卡在 H8A 先冻结结构，最终摘要必须在正文和附录定稿后依据该卡及各章 `abstract_contribution` 撰写；摘要写完后运行 `scripts/check_abstract_contract.py --strict` 并登记 `abstract_contract_report`，未通过不得完成 H8。
- 论证编辑输出完整修订正文，并仅允许保留 `【需要作者补充证据】`、`【需要作者重审主张】` 两类作者确认标记；不得把评审意见、内部交流或过程说明写入论文。
- 成品只保留最终定稿内容；不写入评审过程、交接信息、调试过程或内部讨论。
- 用户负责最终视觉确认；自动检查只覆盖文本层、结构、数字、引用和交付门禁。
