---
name: heuristic-algorithms
description: 数学建模竞赛启发式与数值算法库（A/B 类复杂优化题、机理建模题专用）：遗传算法、模拟退火、粒子群、蒙特卡洛模拟、爬山/禁忌搜索、贪心、常微分方程数值求解。触发词：NP难、大规模优化、排产、路径、调度、选址、随机模拟、蒙特卡洛、排队、微分方程、机理模型、GA、SA、PSO、遗传算法、模拟退火。与 pyomo（精确求解）互补：精确求解超时或不可行时切换启发式。
metadata:
  version: "1.0"
---

# 数学建模竞赛 · 启发式与数值算法库

> 定位：解决"优化问题解不动/模型是微分方程"的问题。配套 `pyomo`（精确求解）和 `data-science-stack`（数据侧），三者构成求解三角。

## Contest-Orchestrator Adapter

本技能只在 `contest-orchestrator` 已批准启发式/数值求解路线后执行，不负责选题或擅自替换模型。输入必须包含任务卡、`model_contract.yaml`、baseline、约束、数据源和求解预算；输出代码与结果只写项目工作区并登记到 `run_manifest`、`result_registry` 和 `numeric_source_map`。

- 每个随机过程固定并记录 `seed`；重复运行、可行性、收敛、约束违约、敏感性和与 baseline 的比较必须有可定位证据。
- 启发式不能掩盖精确模型的不可行或超时原因；切换依据、参数范围、停止条件和适用边界必须回流主会话。
- 返回 `status`、`active_mode`、`task_card`、`artifacts`、`evidence`、`checks`、`blockers`、`next_node`。任何失败只作为当前节点事实，不写入论文成品或长期规则。
- 默认不生成截图或自动视觉检查；图表另走 `modelviz` → `scipilot-figure-skill`，用户明确要求时才开启视觉检查。
- 节点包和论文可见内容不得出现元话语、内部交流、调试、失败过程、旧版本或未确认方案等负回响。

## Robustness Check Tool（B 题优化加固协同变更）

`scripts/robustness_check.py` 为 GA/SA/PSO 等启发式算法提供随机种子敏感性和参数鲁棒性检查。

- **输入**：`robustness_plan.yaml`，包含 `model_contract_sha256`、`subproblem_id`、算法类型、随机种子列表、参数扫描范围、目标方向（min/max）
- **输出**：`robustness_report.yaml`，`schema_version=1.0`，每个种子/参数组合登记 `best_fitness`、`feasible`、`constraint_violation`、`iterations_to_converge`、`decision_change`
- **状态契约**：只有 `status: verified` 且所有运行有真实数值或明确 `not_applicable_reason` 时，才允许通过 contest-orchestrator 的 H6 验证；`completed`/`manual_required` 为空证据通路，会被主控检查器拒绝
- **CV 统计量限制**：变异系数（CV）只能作为统计量，不能单独产生"可用于论文"的结论；必须配合可行性、约束违约、收敛曲线和决策变化证据
- **调用方式**：`python scripts/robustness_check.py <robustness_plan.yaml> --out <robustness_report.yaml>`
- **与 contest-orchestrator 的集成**：H5 节点启发式优化子问题必须生成此报告；`check_model_evidence.py` 的 `_check_sensitivity_report()` 会自动校验报告的 `subproblem_id` 绑定、状态和数值完整性

## 0. 何时触发

- 优化问题规模大（决策变量 >10³ 或组合爆炸），`pyomo`/`scipy.optimize` 精确求解超时或不可行（典型：路径规划、排产调度、选址分配、装箱）
- 目标函数非凸/不可导/黑盒（无法用梯度方法）
- 题目要求随机模拟（排队、库存、可靠性、风险）
- 题目机理是微分方程（传染病、热传导、种群、电路、物理过程）

## 1. 算法选择决策树（先想清楚再用）

```
优化问题
├─ 规模小、线性/凸 → pyomo 精确求解（LP/MILP/QP），别用启发式
├─ 规模大、组合优化 → 遗传算法（离散编码）或模拟退火（邻域搜索）
├─ 连续变量、非凸 → 粒子群 或 遗传算法（实数编码）
├─ 有明确贪心结构 → 贪心/局部搜索 + 扰动重试（先做，往往够用）
├─ 需要评估不确定性 → 蒙特卡洛模拟
└─ 动态/多阶段决策 → 动态规划 或 遗传算法（决策序列编码）

微分方程问题 → scipy.integrate.solve_ivp（第 7 节）
```

**纪律**：先用贪心/局部搜索跑通拿到结果（baseline），再用 GA/SA 提升并报告对比——论文叙事"贪心 baseline → 启发式提升 X%"是评委喜欢的结构。绝不直接上启发式而没有任何对比。

## 1.5 详细算法手册（按需加载）

- 优化类算法完整手册（GA/PSO/SA/LP/IP/DP 系统展开）：`references/cookbook-optimization.md`
- 启发式算法使用条件与防炫技指南（前置条件、各算法适用场景、硬要求、炫技检测清单、vs 精确求解决策流程、论文写作建议）：`references/heuristic_usage_guide.md`
- 统计与不确定类手册（假设检验/ANOVA/实验设计/蒙特卡洛/贝叶斯/成分数据/时间序列/灰色关联）：`references/cookbook-statistical.md`
- 需要系统方法论时加载对应手册；本文档的决策树与代码模板是首选入口，手册提供更细的问题适配框架。

## 2. 遗传算法（GA）——组合优化主武器

适用：TSP/路径、排产、选址、调度、背包类。要点：**编码决定一切**（排列编码/二进制/实数），适应度=目标函数，选择=锦标赛，交叉/变异按问题定制。

```python
import numpy as np

def ga_solve(fitness, n_var, bounds=None, n_pop=100, n_gen=200,
             pc=0.8, pm=0.1, seed=42, maximize=True):
    """通用实数编码 GA。fitness(x)->float 为目标函数。"""
    rng = np.random.default_rng(seed)
    lo, hi = (np.zeros(n_var), np.ones(n_var)) if bounds is None else bounds
    pop = rng.uniform(lo, hi, (n_pop, n_var))
    best_fit, best_x, history = -np.inf, None, []
    for g in range(n_gen):
        fits = np.array([fitness(x) for x in pop])
        if not maximize: fits = -fits
        # 锦标赛选择（取每组随机两个中适应度更优者）
        order = np.argsort(-fits)[:n_pop // 2]
        parents = pop[order]
        # 均匀交叉 + 高斯变异
        children = []
        while len(children) < n_pop - len(parents):
            a, b = parents[rng.integers(len(parents), size=2)]
            mask = rng.random(n_var) < pc
            child = np.where(mask, a, b)
            child = child + rng.normal(0, 0.1, n_var) * (hi - lo) * (rng.random() < pm)
            children.append(np.clip(child, lo, hi))
        pop = np.vstack([parents, np.array(children)[:n_pop - len(parents)]])
        if fits.max() > best_fit:
            best_fit, best_x = fits.max(), pop[np.argmax(fits)].copy()
        history.append(best_fit)
    return best_x, best_fit, history  # history 用于画收敛曲线
```

**论文呈现**：
- 收敛曲线图（x=代数，y=最优适应度）——证明算法收敛、代数设置合理
- 参数敏感性表：种群/交叉率/变异率扰动 ±50% 后结果波动 <5% 即可宣称鲁棒
- 与贪心/精确小规模解对比表

**GA 雷区**：❌ 变异率过大（退化成随机搜索）｜ ❌ 无收敛曲线 ｜ ❌ 不设随机种子（不可复现）｜ ❌ 编码不解释（评委看不懂就不信）。

## 3. 模拟退火（SA）——连续/离散邻域搜索

适用：目标函数崎岖、邻域定义自然的问题。核心是**温度调度**：高温大探索、低温小扰动。

```python
import numpy as np

def sa_solve(neighbor, energy, x0, t0=100, t_min=1e-3, alpha=0.95, seed=42):
    """neighbor(x)->x' 邻域函数；energy(x)->float 能量（越小越好）"""
    rng = np.random.default_rng(seed)
    x, e = x0, energy(x0)
    best_x, best_e = x, e
    t = t0; history = []
    while t > t_min:
        xn = neighbor(x); en = energy(xn)   # 只调一次邻域（随机邻域重复调用会得到不同邻居）
        if en < e or rng.random() < np.exp(-(en - e) / max(t, 1e-9)):
            x, e = xn, en
            if e < best_e: best_e, best_x = e, xn
        t *= alpha
        history.append(best_e)
    return best_x, best_e, history
```

**雷区**：❌ 邻域函数每步算两次 energy（浪费 2 倍时间）——先 `xn = neighbor(x)` 再 `en = energy(xn)`｜ ❌ 退火太快（alpha<0.9）探索不足｜ ❌ 初始温度过高导致前期纯随机（看收敛曲线判断）。

## 4. 粒子群（PSO）——连续优化快速收敛

```python
import numpy as np

def pso_solve(fitness, n_var, bounds, n_p=50, n_iter=200, w=0.7, c1=1.5, c2=1.5, seed=42):
    rng = np.random.default_rng(seed)
    lo, hi = bounds
    x = rng.uniform(lo, hi, (n_p, n_var))
    v = rng.uniform(-(hi-lo)*0.1, (hi-lo)*0.1, (n_p, n_var))
    pbest, pbest_f = x.copy(), np.array([fitness(xi) for xi in x])
    gbest, gbest_f = pbest[np.argmax(pbest_f)].copy(), pbest_f.max()
    history = []
    for _ in range(n_iter):
        r1, r2 = rng.random((n_p, n_var)), rng.random((n_p, n_var))
        v = w*v + c1*r1*(pbest - x) + c2*r2*(gbest - x)
        x = np.clip(x + v, lo, hi)
        f = np.array([fitness(xi) for xi in x])
        better = f > pbest_f
        pbest[better], pbest_f[better] = x[better], f[better]
        if pbest_f.max() > gbest_f:
            gbest, gbest_f = pbest[np.argmax(pbest_f)].copy(), pbest_f.max()
        history.append(gbest_f)
    return gbest, gbest_f, history
```

**何时选 PSO 而非 GA**：连续变量、目标函数光滑但有多个局部最优（如参数辨识、曲线拟合）。离散问题优先 GA。

## 5. 蒙特卡洛模拟（MC）——不确定性/随机过程

适用：排队系统、库存策略、设备可靠性、风险评价、随机性强的预测。**核心纪律：随机种子固定 + 大样本 + 报告置信区间**。

```python
import numpy as np

def monte_carlo_sim(run_once, n=10000, seed=42):
    """run_once()->单个场景结果；返回均值/分位数/95%区间"""
    rng = np.random.default_rng(seed)
    results = np.array([run_once(rng) for _ in range(n)])
    return {'mean': results.mean(), 'std': results.std(),
            'p5': np.percentile(results, 5), 'p95': np.percentile(results, 95),
            'hist': results}  # hist 画直方图/分布曲线

# 示例：M/M/1 排队模拟（验证理论值 λ/μ 利用率）
def mm1_once(rng, lam=8.0, mu=10.0, T=1000):
    t, n, busy = 0.0, 0, 0.0
    next_arr, next_dep = rng.exponential(1/lam), np.inf
    while t < T:
        if next_arr < next_dep:
            t, n, next_arr = next_arr, n+1, next_arr + rng.exponential(1/lam)
        else:
            t, n, next_dep = next_dep, n-1, next_dep + rng.exponential(1/mu)
            if n == 0: next_dep = np.inf
        if n > 0: busy += min(next_arr, next_dep) - t
    return busy / T  # 服务台利用率 ≈ ρ = λ/μ
```

**论文呈现**：直方图/累计分布 + 与理论值/解析解对比表（MC 对解析解的验证是评委最爱看的"模型检验"）。

## 6. 快速手段：贪心 / 局部搜索 / 禁忌

- **贪心**：按某个启发规则逐步决策（例：最短路 Dijkstra、排产按最短加工时间）。5 分钟跑通，作为 baseline。
- **局部搜索**：贪心解 + 邻域交换，迭代到局部最优（2-opt 解 TSP 效果极好）。
- **禁忌搜索**：局部搜索 + 禁忌表防循环，比 SA 快但实现稍复杂。
- **决策建议**：**先贪心拿结果 → 2-opt/局部搜索提升 → 时间富余再 GA/SA**。多数题目到第二步已够省奖。

## 7. 常微分方程数值求解（机理建模）

适用：题目机理可写为 ODE（传染病 SIR、热传导、冷却、种群、电路、药物浓度）。**先写微分方程再数值求解，图+结果一起出**。

```python
import numpy as np
from scipy.integrate import solve_ivp

def ode_model(t, y, params):
    S, I, R = y
    beta, gamma = params
    dS = -beta * S * I
    dI = beta * S * I - gamma * I
    dR = gamma * I
    return [dS, dI, dR]

# SIR：S(0)=0.99, I(0)=0.01
sol = solve_ivp(ode_model, [0, 60], [0.99, 0.01, 0.0],
                args=([0.3, 0.1],), method='RK45', dense_output=True)
t = np.linspace(0, 60, 300)
S, I, R = sol.sol(t)
# 关键量：感染峰值时间与峰值（论文必写）
peak_t = t[np.argmax(I)]; peak_I = I.max()
print(f'感染峰值 {peak_I:.3f} 出现在 t={peak_t:.1f}')
```

**参数辨识**（有真实数据时）：用 `scipy.optimize.curve_fit` 或 PSO 拟合参数 → 论文"模型参数估计"节。
**雷区**：❌ 不检查 `sol.success`（数值发散要换 method='LSODA' 或减小步长）｜ ❌ 参数无物理意义乱给｜ ❌ 不报告初始条件假设。

## 8. 结果呈现规范（论文直接可用）

| 元素 | 要求 |
|---|---|
| 收敛曲线 | 每次启发式求解必配（x=迭代次数，y=目标值） |
| 对比表 | 贪心/局部搜索/GA/SA（或精确小规模解）四列：目标值+耗时 |
| 参数敏感性 | 关键参数 ±20% 扰动，结果变化 <5% 声明鲁棒 |
| 解的展示 | 路径图/甘特图/布局图（drawio 或 scipilot 出图），光给数字评委没感觉 |
| 可复现 | 所有随机算法固定 seed 并在附录写明；结果落盘 `results/` |

## 9. 雷区总清单（红线）

- ❌ 不设 seed、不报参数 → 不可复现，评审核对失败
- ❌ 无收敛曲线就声称"算法收敛"
- ❌ 没有 baseline 对比就宣称"算法最优"
- ❌ 大规模问题硬上精确求解器（超时后两手空空）——赛前 1h 先判断规模
- ❌ 启发式结果与论文数字不一致
- ❌ 把启发式包装成"创新算法"（就叫 GA/SA，实事求是；创新在问题建模和约束处理上）

## 10. 与现有体系对接

- `contest-orchestrator`：本技能在 **executor 阶段**调用；求解结果进 result_registry，失败记录进失败库（如 GA 不收敛，记录参数与现象，供 Replay 复用）
- 精确求解优先尝试 `pyomo`（LP/MILP）；超时/不可行再切本技能——决策记录写进 decision_trace
- 数据驱动部分先走 `data-science-stack`；参数辨识（第 7 节）用拟合结果喂给 ODE
- 数据结果图交给 `modelviz` → `scipilot-figure-skill`；模型流程/技术路线图交给 `tech-route-maker`；原理、受力和几何示意图交给 `tikz-scientific-figures`；Draw.io 仅用户明确要求时使用

## 代码注释规范（B 题优化加固协同变更）

使用启发式算法（GA/SA/PSO/蒙特卡洛/NSGA-II）时，代码必须有必要的注释，像人写的而不是 AI 生成的。不用大量注释，但关键位置必须有。

**必须有注释的位置**：
- 文件头：1-3 行说明这个文件做什么
- 算法参数：每个参数注释说明含义、取值依据、对结果的影响（初始温度、冷却率、迭代次数、交叉率、变异率等）
- 适应度函数：docstring 说明目标含义、各项权重、约束处理方式
- 核心算法步骤：每个步骤注释说明做什么、为什么这么做
- 选择/交叉/变异：每个函数 docstring + 关键参数注释
- 收敛判断：注释说明判断标准
- 结果输出：关键输出注释说明含义

**注释内容红线**：注释中禁止出现内部讨论话语（经讨论、agent建议）、AI 思考过程（首先、其次、让我）、元话语（本文将、以下代码）、负向回响（之前用、v2修正、尝试了）、AI 协作痕迹（agent、prompt、审查）。注释必须是纯粹的技术说明。

**详细规范和示例**：`references/code_comment_guide.md`

## 数值合理性检查规范（B 题优化加固协同变更）

使用启发式算法（GA/SA/PSO/蒙特卡洛等）求解后，必须对结果进行数值合理性检查，禁止异常结果进入结果登记。

**必查项**：
- inf/nan 检测：求解结果中不得出现无穷大或非数
- 目标值量级异常：目标值 >1e15 或 <1e-15（非零）需要说明原因
- 收敛性检查：算法是否收敛，收敛曲线是否合理，是否存在早熟收敛
- 约束违约：检查约束条件是否满足，违约量是否在可接受范围内
- 随机种子一致性：相同种子下结果是否可复现
- 结果文件完整性：JSON 可解析、CSV 列数一致、非空

**检查时机**：每次求解完成后立即检查，不通过的结果不得登记到 result_registry。

**异常处理**：发现异常必须排查原因（数值不稳定、参数设置不当、收敛不充分等），修复后重新求解，不得带着异常结果进入下一环节。

**详细规范和领域特定检查**：`references/numerical_sanity_guide.md`
