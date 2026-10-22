# 独立审查报告：<节点> 节点

**审查建议**：RECOMMEND_HOLD | RECOMMEND_FIX | NO_CRITICAL_ISSUE_FOUND | INSUFFICIENT_EVIDENCE
**审查深度**：QUICK | DEEP
**输入完整性**：COMPLETE | PARTIAL | INSUFFICIENT
**审查置信度**：HIGH | MEDIUM | LOW
**材料快照**：manifest_sha256: <整体哈希>
**审查时间**：YYYY-MM-DD HH:MM
**active_mode**：<模式>

---

## 优先处理（顶部 3-5 项）

> 只列最需要你关注的问题，按严重度和影响排序。QUICK 模式只显示 BLOCKER + HIGH。

| ID | 级别 | 问题 | 影响 | 建议动作 | 验收标准 |
|---|---|---|---|---|---|
| REV-G4-001 | BLOCKER | 一句话描述 | 对什么的影响 | 怎么做 | 修好后怎么验证 |
| REV-G4-002 | HIGH | 一句话描述 | 对什么的影响 | 怎么做 | 修好后怎么验证 |
| ... | ... | ... | ... | ... | ... |

---

## 审查摘要

| 严重程度 | 新增 | 上次未关闭 | 已关闭 | 已接受风险 |
|---|---|---|---|---|
| BLOCKER | X | X | X | X |
| HIGH | X | X | X | X |
| MEDIUM | X | X | X | X |
| LOW | X | X | X | X |

**验证状态**：VERIFIED X 项 / PARTIALLY_VERIFIED X 项 / UNVERIFIED X 项
**新鲜度**：CURRENT X 项 / STALE X 项 / UNKNOWN X 项

---

## 新增问题详情

### BLOCKER

#### REV-G4-001: 问题标题

- **finding_state**: OPEN
- **verification_state**: VERIFIED
- **freshness_state**: CURRENT
- **confidence**: HIGH
- **位置**: `path/to/file.tex` (行 45-52)
- **文件哈希**: `abc123...`
- **原文**: "观察到的原文片段"
- **证据**: 引用当前源文件的具体内容（跨文件可列多项）
- **影响**: 对模型正确性/结果可信度/论文质量/节点放行的影响
- **建议动作**: 优化建议（只提意见，不修改文件）
- **验收标准**: 修复后怎么验证

### HIGH

#### REV-G4-002: 问题标题

（同上结构）

### MEDIUM

（同上结构，QUICK 模式可折叠）

---

## 上次未关闭问题（跨节点追踪）

> 来自 issues_tracker.yaml，检查是否仍然存在。

| ID | 首次节点 | 问题 | 当前状态 | 本次核实结果 |
|---|---|---|---|---|
| REV-G3-001 | G3 | 符号 $x_3$ 定义矛盾 | OPEN | 仍然存在（STALE→CURRENT） |
| REV-G2-003 | G2 | 结果表数字与代码不一致 | OPEN | 已修复（标记 RESOLVED） |
| ... | ... | ... | ... | ... |

---

## 已关闭 / 已接受风险

| ID | 问题 | 关闭方式 | 关闭时间 |
|---|---|---|---|
| REV-G3-002 | 元话语"显然" | RESOLVED（已修改） | YYYY-MM-DD |
| REV-G1-001 | 排版细节 | ACCEPTED_RISK（用户确认） | YYYY-MM-DD |

---

## 未验证范围

> 明确声明哪些没有检查，不把"未检查"说成"通过"。

- 未提供材料：<列出缺失的文件>
- 未执行检查：<列出因材料不足或时间限制未做的检查>
- 无法验证：<列出无法确认的项及原因>

---

## 质量对比（可选，仅当提供主 agent 自评时）

> 基础发现已在第 5 步冻结，本对比不修改冻结结果。不计算未经裁定的漏检率/误判率。

| 类别 | 数量 | 说明 |
|---|---|---|
| matched_findings | X | 双方均发现 |
| reviewer_only_findings | X | 仅独立审查发现（主 agent 未提及） |
| main_only_claims | X | 仅主 agent 声明（独立审查未发现对应问题） |
| conflicting_findings | X | 双方判断冲突 |
| not_comparable | X | 无法建立对应关系 |

**冲突详情**：

| 独立审查 ID | 独立结论 | 主 agent 声称 | 差异说明 |
|---|---|---|---|
| REV-G4-001 | 符号未定义（HIGH） | 已检查符号完整性，无问题 | 主 agent 漏检 |

---

## LOW 级别附录

> QUICK 模式默认隐藏，DEEP 模式显示。

| ID | 问题 | 位置 | 建议 |
|---|---|---|---|
| REV-G4-010 | 用词不精确 | 7.1 | 建议改为... |

---

## 审查说明

- 本报告基于主 agent 交付的当前源文件（manifest_sha256: xxx）
- 所有 HIGH/BLOCKER 均有明确证据、影响、修复动作和验收标准
- 审查过程性内容仅出现在本报告中，未写入论文正文
- 本报告为独立外部审查结果，只提意见和优化建议，不修改任何文件
- 主 agent 不知道本审查的存在，报告仅交付给用户
- 用户自行决定是否将问题反馈给主 agent、是否自己修改、是否忽略
- NO_CRITICAL_ISSUE_FOUND 不等于绝对通过，仅表示在已声明审查范围内未发现严重问题
