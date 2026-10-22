# Math Blueprint Library · 数学推理脚手架

蓝图回答“现实问题如何变成数学对象”，提供对象、符号、目标、约束、推导、理论检查和可裁剪步骤；不替代题面分析，也不规定论文固定写法。

## 与其他五库的分工

| 库 | 回答的问题 | 粒度 | 触发方式 |
|---|---|---|---|
| FD | 这类题容易犯什么错误 | 条目 | 语义检索 |
| SD | 如何设计策略 | 条目 | 语义检索 |
| ST | 用什么技术路线 | 条目 | 语义检索 |
| DM | 如何决策（为什么这么选） | 条目 | 语义检索 |
| WR | 如何写得像竞赛论文 | 条目 | 语义检索 |
| **MB** | **这类题该怎么数学化（符号/目标/约束/推导/理论）** | **题型级骨架** | **强制检索（按 problem_type 匹配）** |

## 目录与命名

```
memory/math_blueprints/
├── COLLECT.md            # 本文件
├── MB-001_optimization.yaml    # 优化/规划 母蓝图
├── MB-002_mechanism.yaml       # 机理/物理 母蓝图
├── MB-003_prediction.yaml      # 预测/时序 母蓝图
└── (后续 family/case 按需：MB-001-1_scheduling.yaml 等)
```

## 蓝图 schema（每条 8 要素）

```yaml
blueprint_id: MB-0XX
problem_type: 题型标签（接入 retrieval fingerprint）
competition_variant: 国赛版 / 美赛版 / 通用版   # 首批国赛版
summary: 一句话：这类题的数学化核心矛盾
abstraction_map:               # ① 现实→数学映射（灵魂）
  objects: [现实对象 → 数学对象]
  relationships: [关系 → 数学结构]
  decision: [决策 → 变量类型]
symbols:                       # ② 符号体系表
  - {sym, meaning, unit}
steps:                         # ③ 建模步骤骨架（可裁剪）
  - {step, name, template, required: true/false, alternative: [..]}
selection_logic:               # ④ 为什么选这个模型
  - {if: 条件, choose: 模型, because: 理由}
propositions:                  # ⑤ 可复用命题/引理模板（定理式高级感来源）
  - {name, template, provenance?, see: [WR-xxx]}
theory_checks:                 # ⑥ 理论性质 checklist
  - {name, note, required: true/false}
antipattern:                   # ⑦ 反例 vs 修法（"调包侠"对照）
  bad: "..."
  good: "..."
failure_modes:                 # ⑧ 蓝图自己的失败模式（数学味不是越多越好）
  - {mode, symptom, guard}
readability_guard:             # ⑨ 可读性约束（数学化与可读性平衡）
  - 规则
```

## 采集规则

1. **来源**："专家分析 → 蓝图"，不是"论文 → 蓝图"。获奖论文片段只作 `provenance` 引用的 few-shot，
   必须标注来源（如 `2023B 国赛，式(1)`），仅作参考不照抄。
2. **2023B 补公式版（add_formulas.py 产物）只作 antipattern 素材**（before/after），不作 gold blueprint。
3. **数学感不是越多越好**：简单统计问题硬套复杂优化模型 = 反模式（unnecessary_theory / over_modeling）。
   采集时遇到"为了显得数学乱加数学"的案例，优先进 failure_modes 而非 propositions。
4. **一题型多骨架**：同 problem_type 下按 fingerprint 细节分 variants（调度/选址/排样…），禁止一题型一骨架。
5. **可裁剪**：step 必须标 required/alternative——注入时按 fingerprint 动态裁剪，模型可按需增删。
6. **粒度三层**：MB-core（范式）→ MB-family（问题族）→ MB-case（迁移案例）。不直接堆几百条；
   family/case 按实战 fingerprint 覆盖率逐步补。
7. **与 WR 双向引用**：MB 的 propositions/theory_checks 引用 `see WR-xxx`；WR 条目加 `related_blueprint: [MB-0XX]`。
   两库独立索引，不合并（合并会污染语义检索）。
8. **分层标注**：每条 blueprint 的 step 标 `level: L1（轻量，高能力默认）` 或
   `L2（完整，退化/低能力场景）`——L1 只含核心公式框架+关键符号，L2 含详细推导+标准验证步骤。
   采集时区分"保底必需项"（进 L1）与"增强验证项"（进 L2）。
9. **多蓝图竞争**：同一题型可存多条可行路线（物理机理/信号处理/优化反演等），注入时附"备选路线"
   提示，允许模型选择——不限制路径但满足数学契约。
10. **anti-anchor 素材**：采集"蓝图/模板导致过度依赖"的失败案例（如公式口径混用未被自检）进
    failure_modes 的 over-reliance 条目，供注入时的反锚检查引用。

## 维护

- 只吸收已验证、可复用且能绑定来源的数学化路径；先更新对应蓝图，再更新索引。
- `blueprint_retrieval.py` 输出 `match_confidence`；低于注入阈值时只提供参考。
- 每条蓝图保留 `failure_modes` 和 `readability_guard`，防止过度套用或为了形式增加无关公式。
