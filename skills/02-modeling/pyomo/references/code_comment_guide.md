# Pyomo 代码注释规范

本规范适用于使用 Pyomo 建立精确优化模型（LP/MILP/NLP/MINLP）的代码。注释必须是纯粹的技术说明，禁止元话语、负向回响、内部讨论和 AI 协作痕迹。

## 一、必须有注释的位置

### 1. 文件头

每个 Python 文件开头必须有 1-3 行说明这个文件做什么。

```python
"""
多波束测线布设优化：LP模型 + 贪心baseline对比
输入：测区参数、波束宽度、重叠率要求
输出：最优测线位置、覆盖率、航行距离
"""
```

### 2. 模型定义

创建 ConcreteModel 时必须注释说明模型的整体结构。

```python
# 模型：测线布设优化，决策变量=每条测线的位置，目标=最小化航行距离
model = pyo.ConcreteModel()
```

### 3. 决策变量

每个决策变量必须注释说明含义、量纲、取值范围。

```python
# 决策变量：第i条测线的起始位置（米），范围[0, 测区宽度]
model.x = pyo.Var(model.lines, domain=pyo.NonNegativeReals, bounds=(0, area_width))

# 0-1变量：第i条测线是否启用（1=启用，0=不启用）
model.y = pyo.Var(model.lines, domain=pyo.Binary)
```

### 4. 目标函数

目标函数必须注释说明优化目标和各项含义。

```python
# 目标：最小化总航行距离 = 每条测线长度之和 + 测线间转移距离
model.total_distance = pyo.Objective(
    expr=sum(model.line_length[i] for i in model.lines) + sum(model.transfer_distance[i] for i in model.lines),
    sense=pyo.minimize
)
```

### 5. 约束条件

每个约束必须注释说明来源（题目要求/物理限制/工程规范）。

```python
# 约束1：相邻测线重叠率 >= 15%（题目要求，低于15%有盲区）
def overlap_constraint(model, i):
    return model.overlap[i] >= 0.15 * model.beam_width
model.overlap_con = pyo.Constraint(model.lines, rule=overlap_constraint)

# 约束2：测线不超出测区边界（物理限制）
def boundary_constraint(model, i):
    return model.x[i] + model.beam_width <= area_width
model.boundary_con = pyo.Constraint(model.lines, rule=boundary_constraint)
```

### 6. 求解器配置

求解器选择和参数配置必须注释说明原因。

```python
# 求解器：GLPK（MILP精确求解，规模<1000变量时足够）
solver = pyo.SolverFactory('glpk')

# 求解参数：时间限制60秒（竞赛时间约束），相对间隙0.01（1%精度足够）
results = solver.solve(model, tee=True, timelimit=60, options={'mipgap': 0.01})
```

### 7. 结果解析

关键结果输出必须注释说明含义。

```python
# 输出：最优总航行距离（米）
print(f"最优总航行距离: {pyo.value(model.total_distance):.2f} 米")

# 输出：每条测线的位置和是否启用
for i in model.lines:
    if pyo.value(model.y[i]) > 0.5:
        print(f"测线{i}: 位置={pyo.value(model.x[i]):.2f}m, 启用")
```

## 二、注释内容红线

注释中**禁止**出现以下内容：

| 类别 | 禁止内容 | 错误示例 | 正确做法 |
|------|---------|---------|---------|
| 内部讨论 | 经讨论、团队决定、agent建议 | `# 经讨论决定用GLPK` | `# 求解器：GLPK（MILP精确求解）` |
| AI思考 | 首先、其次、让我、经过分析 | `# 首先定义变量，然后加约束` | `# 决策变量：测线位置` |
| 元话语 | 本文将、以下代码、接下来 | `# 以下代码建立优化模型` | `# 模型：测线布设优化` |
| 负向回响 | 之前用、v2修正、尝试了、失败 | `# 之前用CPLEX太慢，改用GLPK` | `# 求解器：GLPK（小规模MILP足够）` |
| AI协作 | agent、prompt、审查、由H5生成 | `# 由H5 agent生成` | 直接删除 |

## 三、不需要注释的位置

- 显而易见的代码（`import numpy as np`、`for i in range(n):`）
- 简单的变量赋值（`n = 10`、`result = []`）
- 标准库函数调用（`print(...)`、`len(...)`）

## 四、注释密度参考

| 代码类型 | 注释密度 |
|---------|---------|
| 模型定义（变量/目标/约束） | 每个定义前1行注释 |
| 求解器配置 | 每个参数1行注释 |
| 结果解析 | 关键输出1行注释 |
| 数据预处理 | 关键步骤1行注释 |
| 工具函数 | docstring + 复杂逻辑行内注释 |

## 五、自检清单

写完代码后，逐项检查：

- [ ] 文件头有 1-3 行说明
- [ ] 每个决策变量有注释（含义+量纲+范围）
- [ ] 目标函数有注释（优化目标+各项含义）
- [ ] 每个约束有注释（来源：题目要求/物理限制/工程规范）
- 求解器配置有注释（选择原因+参数含义）
- 关键结果输出有注释（含义）
- 注释中没有元话语、负向回响、内部讨论、AI协作痕迹
- 没有过度注释（显而易见的代码不注释）
