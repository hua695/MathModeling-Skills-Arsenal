# Result Registry（结果注册表）

> 原则：**结果只从代码生成**。
> 所有数值/图/表的唯一可信来源是 registry；Writer 写论文时**只能读 registry**，不能引用临时输出或代码 stdout。

## 目录
```
executor/result_registry.md                       # 本文档（schema + 登记规则）
<项目根>/competition_replay/<竞赛>_<年份>_<题号>/results/  # 实际实验产物落盘处（qN_results.json + 求解脚本 + figures/）
```
每条实验按下方 schema 登记（随比赛目录存为 `results/EXP-<竞赛>-Q<n>-<seq>.yaml`）。

## schema
```yaml
experiment_id: EXP-2026hsb-B-Q2-03
status: [已验证] / [仅数值] / [存疑]        # 与 confidence-tag 一致
generated_by: scripts/q2_solve.py
code_hash:   sha256-<代码哈希>              # 生成脚本的哈希
input_hash:  sha256-<输入数据哈希>
result_hash: sha256-<结果JSON哈希>
figure_hash: sha256-<图哈希>                # 每张图一个，图↔结果绑定
seed: 1003                                 # 多 seed 择优后的最优 seed（当场记）
params:
  key1: value1                             # 关键参数快照（如权重0.95/0.05）
results:
  key: value                               # 论文要用到的每个数字都在这
verified: true / false                     # 是否通过 critic 一致性验证
```

## 规则（强制）
1. **写**：只有生成结果的脚本能登记（脚本内调用 registry.write()）。
2. **读**：Writer 生成论文数字/表格/图时，只从 registry 读；找不到→问 Executor，不自己编。
3. **一致性**：critic 的 consistency-check 拿 registry 的 result_hash 与论文表逐一对照。
4. **哈希**：code/result/figure 三者哈希互相绑定，改代码→结果失效→重新登记。
5. **可复现**：seed + code_hash + input_hash 齐全 = 评委可复现。

## 与 confidence-tag 的关系
registry 的 `status` 复用 Executor 的 `[已验证]/[仅数值]/[存疑]`：
- `[已验证]` → 论文可写死
- `[仅数值]` → 论文写但标注"计算值"
- `[存疑]` → 不写，回 Executor 重查
