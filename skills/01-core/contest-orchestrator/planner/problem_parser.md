# problem-parser（第一步：理解题）

## Problem Graph（含 Assumption Layer）
```
                 Objective(隐藏目标)
                     ↓
              Evaluation metric
                     ↓
      ┌──────────────┼──────────────┐
     变量          约束           数据
      │                              │
      └────────── Assumptions ───────┘   ← ⭐ 假设层
                     ↓
              Mathematical Model
                     ↓
                   Solver
                     ↓
                  Evidence
```
**假设层是数学建模扣分最多的地方**——每个假设都要有合理性说明，Proof Trace 才能接上（如"假设流量服从正态分布→评委问为什么→你给依据"）。

## 输出
```
{
  type, variables, constraints, hidden_goal, available_data, expected_method, assumptions[],
  complexity: { math: 0-10, data: 0-10, compute: 0-10 }   ← ⭐ 供 Controller 定 simple/medium/hard
}
```
输出喂给 topic-scorer；**complexity score 喂给 Controller**（hard→五角色全开，simple→只开 Planner+Executor）；并**查 memory/index.yaml** → 命中题型则读对应 FD(规避)/SD(复用)/ST(策略)。

## 条件账本与覆盖审计

在生成 Problem Graph 和 Fingerprint 之前，先读取 `planner/problem_condition_ledger.md`，生成项目根目录下的 `problem_condition_ledger.yaml`。
账本按实际题目标题定位，排除标题前的竞赛页眉和格式提醒；将会改变变量、约束、目标、数据口径、验证方法或最终交付的完整句子/独立分句登记为 source unit。

每条 source unit 必须保留来源位置、完整原文、规范化建模含义、影响小问、下游必须出现的证据和证据等级。证据等级分为 `confirmed`、`inferred`、`pending`：推断条件不得直接升级为硬约束，歧义和缺页材料必须进入 `unresolved_conditions`。

每个 Qn 还要登记输入、任务、输出、引用的 source unit，以及会被后问复用的结果。该账本是题目理解的中间接口，不是论文正文，不要求生成 Mermaid；问题分析流程图应根据账本调用 `tech-route-maker` 绘制，登记 `generator=tech-route-maker`、`diagram_role=problem_analysis_flowchart` 并保留 `tech-route.json` 源文件。

严格交付前运行：

```text
python scripts/check_problem_coverage.py <项目根> --strict --require-ledger
```

检查器负责 ID、来源、字段、角色、跨小问绑定、重复登记和 unresolved 状态；它不冒充数学语义证明。`FULL_CONTEST --strict` 缺少账本或存在未解决关键条件时，禁止进入正式模型交付；`PLAN_ONLY`/`SUBPROBLEM` 可先以 WARN 继续探索。

## Problem Fingerprint（v3.5，检索用指纹，非描述）
> 描述题"是什么"用 Problem Graph；指纹回答"**这题以前见没见过**"。检索按指纹匹配，不按关键词。
```yaml
problem_fingerprint:
  primary:     预测 / 优化决策 / 评价分类 / 物理建模 / 机理建模 / 图模型   # 主类（权重最大）
  subtype:     生产质检 / 选址 / 路径规划 / 资源配置 / 排程 / 定价 / 时序预测 ...  # ⭐ 结构身份（区分大类内问题）
  secondary:   时序 / 回归 / 分类 / 路径 / 布局 / 反演 / 排队 ...          # 副类
  keywords:    [结构性关键词，必须填]                                     # ⭐ 本题独特术语
  data_scale:  small(<100) / medium(100-1w) / large(>1w)                  # 数据规模
  constraints: [linear, nonlinear, integer, dynamic, spatial, temporal]    # 约束类型
  objective:   single / multi / fuzzy / robust                             # 目标特征
  time_budget: 剩余小时
```
**独立提取**：fingerprint 由 problem-parser 在**不看经验库**的情况下输出（避免检索结果反向污染指纹→confirmation bias），再进检索。

> ⚠️ **2024B 教训（v3.5.2）**：只填 `primary='优化决策'` 检索命中 0——库里 23 条大类候选（停车位/风光储/配送）全与本题不相关。**必须填 `subtype` + `keywords`（结构性关键词）**：如 2024B 填 `subtype: 生产质检` + `keywords: [抽样, 次品率, 拆解, 序贯, 验收]`，才能命中库里同题先例（DP031/DP056/CM2024B）。禁止只给大类。

## 经验检索（v3.5 Experience Retrieval → Strategy Prior）
```
Problem Fingerprint
   ↓
memory/retrieval.py（指纹匹配 → 多路召回 → ranking 精排 → 聚合决策先验）  ← 必须执行
   ↓
Strategy Prior（成功模式/失败警示/高风险动作，见 strategy_prior_template.md）
   ↓
注入 Planner
```
**必须执行，不可跳过**：
1. 出 Fingerprint 后**立即**跑 `python memory/retrieval.py`（或 import retrieval.retrieve）。
2. 把 `n_matched / strategy_prior / planner_responses / interventions` 记入 `competition_replay/<竞赛>_<年份>_<题号>/experience_usage.yaml`。
3. n_matched=0 也要如实记录（说明冷启动，为下场比赛建库）。
- 检索**不返回文档罗列**，返回**决策先验**：成功模式（含成功率）、失败警示（含 signal）、高风险动作（历史失败率高的动作）。
- 检索结果**含失败经验（FD 库）**——避坑比复用更值钱。
- 排序用 `memory/ranking.py`（v3.7.1 分档排序）：相似度定档（A≥1.5 / B 0.9~1.5 / C 0.5~0.9 / D<0.5）→ 档内有界 rank_score = sim × (0.5 + 0.5×min(quality×reuse×freshness×bonus, 2)) × 来源多样性；档内元数据不再作为无界乘子淹没相似度。
- 保留 index.yaml 快速索引作为兜底；命中题型也读对应 FD/SD/ST。

> 理解错题比模型差更致命——这一步出错，后面全白做。

## Problem-type Classifier（⭐ Physics Problem Gate，v0.2）
problem-parser 先判题型，再加载对应先验：

```
problem-parser
   ↓ problem-type classifier
   ├── 数据驱动（回归/分类/时序）→ 先验: ST-001(数据少保守) + FD-005(AIGC)
   ├── 物理机理（光学/热/力学/波动）→ 先验: ST-006(单位材料) + ST-008(避吸收带) + FD-006(单位) + FD-007(材料参数) + SD-004(多方法互证)
   └── 优化决策（运筹/布图/排程）→ 先验: FD-001(架构极限) + SD-001(确定性构造) + ST-002(换互补架构)
```
**关键**：若一开始判断"物理反演"，就自动加载 ST physics_prior + FD unit_check + FD material_parameter，**提前避免单位/折射率错误**——本案例就是没先判题型才踩了 FD-006/007 的坑。
