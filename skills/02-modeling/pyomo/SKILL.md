---
name: pyomo
description: Python Optimization Modeling Objects. A high-level framework for formulating, solving, and analyzing optimization models. Supports Linear Programming (LP), Mixed-Integer Linear Programming (MILP), and Non-Linear Programming (NLP). Part of the COIN-OR project. Use for mathematical optimization, linear programming, mixed-integer programming, non-linear programming, strategic planning, process engineering, energy systems, supply chain optimization, stochastic programming, and solver integration with IPOPT, SCIP, Gurobi, CPLEX, or GLPK. 触发：优化/线性规划/整数规划/混合整数/建模求解/约束/目标函数。
metadata:
  version: 6.10.0
license: BSD-3-Clause
---

# Pyomo - Mathematical Optimization Modeling

Pyomo allows you to define optimization problems using a natural mathematical syntax (Sets, Parameters, Variables, Constraints). It decouples the model from the solver, allowing the same model to be solved by different engines without code changes.

## Contest-Orchestrator Adapter

在 `contest-orchestrator` 中，本技能只实现已批准的精确优化模型。调用前必须读取任务卡、`model_contract.yaml`、`symbol_table.md`、数据来源和 solver 预算；不得自行改目标、约束、参数或切换到启发式。依赖安装只可在用户批准的项目环境中执行，不得静默改变全局环境。

- 模型代码、solver 配置、日志和结果只写项目工作区；结果必须登记 `run_manifest`、`result_registry` 和 `numeric_source_map`。
- 必须记录可行性、`termination_condition`、目标值、变量值、约束违约、单位/量纲、随机性（如有）和复算命令；非 optimal 结果不得标记为最优。
- 返回 `status`、`active_mode`、`task_card`、`artifacts`、`evidence`、`checks`、`blockers`、`next_node` 节点包。不可行、超时或 solver 缺失时回流事实，不自动改模型。
- 默认不做截图、渲染复核或 AI 视觉检查；结果图走 `modelviz` → `scipilot-figure-skill`，用户明确要求时才启用视觉检查。
- 节点包、论文成品和报告不得包含元话语、内部交流、调试、失败过程、旧版本或未确认方案等负回响。

## Sensitivity Analysis Tool（B 题优化加固协同变更）

`scripts/sensitivity_analysis.py` 为 LP/MILP/NLP 模型提供参数扰动灵敏度分析。

- **输入**：`sensitivity_plan.yaml`，包含 `model_contract_sha256`、`subproblem_id`、参数基准值、扰动点列表、求解器配置
- **输出**：`sensitivity_report.yaml`，`schema_version=1.0`，每个扰动点登记 `objective`、`feasible`、`decision_change`、`constraint_violation`、`termination_condition`
- **状态契约**：只有 `status: verified` 且所有扰动点有真实数值或明确 `not_applicable_reason` 时，才允许通过 contest-orchestrator 的 H6 验证；`completed`/`manual_required` 为空证据通路，会被主控检查器拒绝
- **求解器不可用时**：生成 `status: manual_required` 报告，明确标注需要人工完成灵敏度分析，禁止输出 `solver_executed` 或 `completed`
- **调用方式**：`python scripts/sensitivity_analysis.py <sensitivity_plan.yaml> --out <sensitivity_report.yaml>`
- **与 contest-orchestrator 的集成**：H5 节点优化子问题必须生成此报告；`check_model_evidence.py` 的 `_check_sensitivity_report()` 会自动校验报告的 `subproblem_id` 绑定、状态和数值完整性

## FIRST: Verify Prerequisites

```bash
python -c "import pyomo; print(pyomo.__version__)"
# If import fails: tell user pyomo and a solver are required (GLPK for LP/MILP, IPOPT for NLP),
# wait for confirmation, then install: pip install pyomo (and solver via conda/pip)
```

## When to Use

- **Strategic Planning**: Long-term resource allocation or investment planning.
- **Process Engineering**: Optimizing chemical plants or refinery operations (Non-linear).
- **Energy Systems**: Power grid dispatch and unit commitment problems.
- **Supply Chain Optimization**: Multi-period, multi-commodity flow problems.
- **Non-Linear Programming (NLP)**: When your constraints or objectives involve smooth curves (e.g., x², log(x)).
- **Stochastic Programming**: Modeling uncertainty in optimization.
- **Custom Solver Integration**: When you need to use specific solvers like IPOPT, SCIP, or Baron.


## B 题（优化决策类）方法选择指南

B 题优化方法选择优先级：先精确后启发，先简单后复杂，能解析不数值，能 LP 不 NLP。

- P0 首选：解析解、贪心算法、规则法、线性规划（LP）
- P1 次选：整数规划（MILP）、非线性规划（NLP）、动态规划
- P2 进阶：多目标规划（MOO）、混合整数非线性规划（MINLP）、随机规划
- P3 谨慎：遗传算法、模拟退火、粒子群、强化学习（必须有充分论证）

使用启发式算法的硬要求：先给数学规划模型、先建 baseline、先证明精确求解不可行、参数调优有依据、结果有稳定性分析、与 baseline 对比。

详细指南（含精确求解 vs 启发式选择标准、B 题常见炫技信号、baseline 推荐、求解器选择指南）：references/b_problem_method_guide.md

## Reference Documentation

**Official docs**: http://www.pyomo.org/  
**GitHub**: https://github.com/Pyomo/pyomo  
**Search patterns**: `pyo.ConcreteModel`, `pyo.Constraint`, `pyo.Objective`, `pyo.SolverFactory`

## Core Principles

### Concrete vs. Abstract Models

- **ConcreteModel**: Data is defined at the time the model is built (most common in Python/Data Science).
- **AbstractModel**: The structure is defined first, and data is loaded later (standard for large-scale industrial models).

### Components

- **Var**: Unknowns the solver needs to find.
- **Set/Param**: Data that defines the problem instance.
- **Objective**: The function to minimize or maximize.
- **Constraint**: Rules the variables must follow.

### Solvers

Pyomo does not have its own solver. It requires external solvers (like glpk for LP/MIP or ipopt for NLP) installed on the system.

## Quick Reference

### Installation

```bash
python -c "import pyomo; print(pyomo.__version__)"
# If import fails: tell user pyomo and a solver are required (GLPK for LP/MILP, IPOPT for NLP),
# wait for confirmation, then install: pip install pyomo (and solver via conda/pip)
```

### Standard Imports

```python
import pyomo.environ as pyo
from pyomo.opt import SolverFactory
```

### Basic Pattern - Simple Linear Model (Concrete)

```python
import pyomo.environ as pyo

# 1. Create Model
model = pyo.ConcreteModel()

# 2. Define Variables
model.x = pyo.Var(within=pyo.NonNegativeReals)
model.y = pyo.Var(within=pyo.NonNegativeReals)

# 3. Define Objective (Minimize x + 2*y)
model.obj = pyo.Objective(expr=model.x + 2*model.y, sense=pyo.minimize)

# 4. Define Constraints
model.con1 = pyo.Constraint(expr=3*model.x + 4*model.y >= 12)
model.con2 = pyo.Constraint(expr=2*model.x + 5*model.y >= 10)

# 5. Solve
solver = pyo.SolverFactory('glpk')
results = solver.solve(model)

# 6. Access Results
print(f"x = {pyo.value(model.x)}, y = {pyo.value(model.y)}")
```

## Critical Rules

### ✅ DO

- **Scale your problem** - Like all optimization, Pyomo works best if variables and constraints are within a similar order of magnitude (e.g., 0.1 to 100).
- **Use pyo.value()** - Always wrap variables in `pyo.value(model.x)` to get their numerical result after solving.
- **Check Solver Status** - Verify the solver reached an optimal solution using `results.solver.termination_condition`.
- **Use pyo.Set and pyo.Param** - For complex models, organize data using these components rather than raw Python lists/dicts.
- **Specify Solver Options** - Use `solver.options['tm_limit'] = 60` (or similar depending on the solver) to manage execution time.
- **Use model.dual** - Register the dual suffix first: `model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)`, then after solving read `pyo.value(model.dual[constraint])` for shadow prices (important for economic analysis).

### ❌ DON'T

- **Don't use Python math functions** - Use `pyo.log()`, `pyo.exp()`, `pyo.sqrt()` instead of `math.log()` or `np.log()` inside expressions.
- **Don't use if statements in constraints** - Constraints must be algebraic. Use "Big-M" notation or logical reformulations for conditional logic.
- **Avoid "Hard" non-linearities** - Functions like `abs(x)` or `max(x, y)` are non-smooth and can break many solvers. Use reformulations.
- **Don't forget the Intercept/Constant** - Constraints like `x + y = 10` are fine, but ensure your units are consistent.

## Anti-Patterns (NEVER)

```python
import pyomo.environ as pyo
import numpy as np

# ❌ BAD: Using NumPy/Math functions in constraints
# model.con = pyo.Constraint(expr=np.sin(model.x) <= 0.5)

# ✅ GOOD: Use Pyomo-compatible functions
model.con = pyo.Constraint(expr=pyo.sin(model.x) <= 0.5)

# ❌ BAD: Using Python IF for conditional constraints
# if model.x > 10:
#     model.con = pyo.Constraint(expr=model.y <= 5)

# ✅ GOOD: Using Big-M notation (for binary variable z)
# y <= 5 + M * (1 - z)
# x >= 10 - M * (1 - z)

# ❌ BAD: Printing a variable directly
# print(model.x) # Returns a reference object, not a number!

# ✅ GOOD: Use value()
print(pyo.value(model.x))
```

## Modeling with Sets and Indices

### Large-Scale Model Construction

```python
model = pyo.ConcreteModel()

# Data
products = ['A', 'B', 'C']
profit = {'A': 10, 'B': 20, 'C': 15}
limit = 100

# Components
model.P = pyo.Set(initialize=products)
model.x = pyo.Var(model.P, within=pyo.NonNegativeReals)

# Indexed Objective
def obj_rule(model):
    return sum(profit[p] * model.x[p] for p in model.P)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

# Indexed Constraint
def limit_rule(model):
    return sum(model.x[p] for p in model.P) <= limit
model.con = pyo.Constraint(rule=limit_rule)
```

## Non-Linear Programming (NLP)

### Using the IPOPT Solver

```python
# Solving: Minimize (x-2)^2 + (y-2)^2
model = pyo.ConcreteModel()
model.x = pyo.Var(initialize=0) # Initialization is CRUCIAL for NLP
model.y = pyo.Var(initialize=0)

model.obj = pyo.Objective(expr=(model.x - 2)**2 + (model.y - 2)**2)

# Constraint: x^2 + y <= 1
model.con = pyo.Constraint(expr=model.x**2 + model.y <= 1)

# Solve with IPOPT
solver = pyo.SolverFactory('ipopt')
solver.solve(model)
```

## Mixed-Integer Linear Programming (MILP)

### Discrete Decisions

```python
# Binary variable: 1 if we open a warehouse, 0 otherwise
model.use_warehouse = pyo.Var(within=pyo.Binary)

# Integer variable: Number of trucks to buy
model.num_trucks = pyo.Var(within=pyo.NonNegativeIntegers)

# Conditional logic: If warehouse is not used, trucks must be 0
# trucks <= Capacity * use_warehouse
model.cap_con = pyo.Constraint(expr=model.num_trucks <= 100 * model.use_warehouse)
```

## Practical Workflows

### 1. Diet Problem (Classic Linear Programming)

```python
def solve_diet(foods, nutrients, costs, requirements):
    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=foods)
    model.N = pyo.Set(initialize=nutrients)
    
    model.x = pyo.Var(model.F, within=pyo.NonNegativeReals)
    
    # Minimize cost
    model.obj = pyo.Objective(expr=sum(costs[f] * model.x[f] for f in model.F))
    
    # Meet nutrient requirements
    def nutrient_rule(model, n):
        return sum(nutrients[f][n] * model.x[f] for f in model.F) >= requirements[n]
    model.con = pyo.Constraint(model.N, rule=nutrient_rule)
    
    pyo.SolverFactory('glpk').solve(model)
    return {f: pyo.value(model.x[f]) for f in model.F}
```

### 2. Blending Problem (Chemical/Process Engineering)

```python
# Balancing component fractions in a mixture
# Note: Often becomes non-linear (NLP) if both flow and fraction are variables
def blend_optimization(inputs, target_purity):
    model = pyo.ConcreteModel()
    # ... model setup ...
    # con: sum(flow[i] * purity[i]) / sum(flow[i]) == target_purity
    # becomes: sum(flow[i] * purity[i]) == target_purity * sum(flow[i]) (Linearized)
```

## Performance Optimization

### Solver Choice

- **GLPK/CBC**: Good for free/open-source LP/MIP.
- **Gurobi/CPLEX**: Industrial standards (extremely fast for large MIP).
- **IPOPT**: Best for smooth Non-linear (NLP).

### Warm Starts

For iterative optimizations, use the previous solution as a starting point.

```python
# For NLP solvers like IPOPT
model.x.set_value(prev_x_value)
solver.solve(model)
```

## Common Pitfalls and Solutions

### Termination Condition

Always check why the solver stopped.

```python
from pyomo.opt import TerminationCondition

results = solver.solve(model)
if results.solver.termination_condition == TerminationCondition.optimal:
    print("Success")
elif results.solver.termination_condition == TerminationCondition.infeasible:
    print("Check your constraints!")
```

### Non-Convexity in NLP

If your NLP model has multiple local minima, IPOPT might get stuck.

```python
# ✅ Solution: 
# 1. Provide multiple different initial guesses (multistart).
# 2. Use a global solver like BARON or SCIP.
```

### Indexing with Variables

`model.x[model.y]` where `y` is a `Var` is illegal.

```python
# ✅ 正确做法：用 `model.add_component(name, obj)` 动态添加组件，或用二元变量重构为线性化约束。
#   注意：Pyomo 没有 `AddElement` API；动态添加用 `model.add_component("x", pyo.Var(...))`。
```

## Best Practices

1. Always scale your problem - variables and constraints should be within similar orders of magnitude
2. Use `pyo.value()` to extract numerical results from variables after solving
3. Check solver termination conditions to verify optimality or diagnose issues
4. Use `pyo.Set` and `pyo.Param` for organizing data in complex models
5. Initialize variables for NLP problems - good starting points are crucial
6. Use Pyomo-compatible functions (`pyo.log()`, `pyo.exp()`, etc.) instead of NumPy/math functions in expressions
7. Reformulate conditional logic using Big-M notation or binary variables
8. Avoid non-smooth functions like `abs()` or `max()` - use reformulations
9. Enable dual suffix for shadow prices when economic analysis is needed
10. Set solver time limits and options appropriately for your problem size

Pyomo is the ultimate tool for turning high-level mathematical abstractions into solved business and scientific problems. Its ability to bridge the gap between algebraic modeling and high-performance solvers makes it the foundation of modern prescriptive analytics.

## 代码注释规范（B 题优化加固协同变更）

使用 Pyomo 建立优化模型时，代码必须有必要的注释，像人写的而不是 AI 生成的。不用大量注释，但关键位置必须有。

**必须有注释的位置**：
- 文件头：1-3 行说明这个文件做什么
- 模型定义：说明模型的整体结构（决策变量、目标、约束）
- 决策变量：每个变量注释说明含义、量纲、取值范围
- 目标函数：注释说明优化目标和各项含义
- 约束条件：每个约束注释说明来源（题目要求/物理限制/工程规范）
- 求解器配置：注释说明选择原因和参数含义
- 结果解析：关键输出注释说明含义

**注释内容红线**：注释中禁止出现内部讨论话语（经讨论、agent建议）、AI 思考过程（首先、其次、让我）、元话语（本文将、以下代码）、负向回响（之前用、v2修正、尝试了）、AI 协作痕迹（agent、prompt、审查）。注释必须是纯粹的技术说明。

**详细规范和示例**：`references/code_comment_guide.md`

## 数值合理性检查规范（B 题优化加固协同变更）

使用 Pyomo 求解优化模型后，必须对结果进行数值合理性检查，禁止异常结果进入结果登记。

**必查项**：
- inf/nan 检测：求解结果中不得出现无穷大或非数
- 目标值量级异常：目标值 >1e15 或 <1e-15（非零）需要说明原因
- 约束违约：检查约束条件是否满足，违约量是否在可接受范围内
- 决策变量范围：决策变量是否在预设的取值范围内
- 结果文件完整性：JSON 可解析、CSV 列数一致、非空

**检查时机**：每次求解完成后立即检查，不通过的结果不得登记到 result_registry。

**异常处理**：发现异常必须排查原因（数值不稳定、约束违约、参数设置不当等），修复后重新求解，不得带着异常结果进入下一环节。

**详细规范和领域特定检查**：`references/numerical_sanity_guide.md`
