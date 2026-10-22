# 任务状态机

```
INIT→TOPIC_SELECTED→LITERATURE_READY→MODEL_READY→DATA_READY→SOLVED→VALIDATED→PAPER_READY→SUBMITTED

回退:
  MODEL_READY → MODEL_REVISE     (求解发现模型不可行)
  SOLVED      → MODEL_REVISE     (结果无法突破 → 换架构, AUTO直接/COLLAB拍板)
  VALIDATED   → DATA_RECHECK     (灵敏度不稳定/数据异常)
  PAPER_READY → TECHNICAL_REVIEW (数学漏洞/证明链跳步)
  DATA_READY  → DATA_RECHECK     (数据泄漏/异常)
```
每次回退后更新 risk-register，不带病前进。
