# Pyomo 优化模型数值合理性检查规范

本规范适用于 Pyomo 建立的 LP/MILP/NLP 优化模型。求解完成后必须执行数值合理性自检，确保"代码运行了但结果是错的"的情况被及时发现。

## 一、必须检查的项目

### 1. 求解器状态检查

求解完成后，必须检查求解器终止条件，不能假设求解一定成功。

```python
from pyomo.opt import TerminationCondition

results = solver.solve(model)
status = results.solver.termination_condition

# 必须检查的状态
if status == TerminationCondition.optimal:
    pass  # 正常，继续后续检查
elif status == TerminationCondition.infeasible:
    raise ValueError("模型不可行：约束之间存在矛盾，请检查约束条件")
elif status == TerminationCondition.unbounded:
    raise ValueError("模型无界：目标函数可以无限优化，请检查是否缺少约束")
elif status == TerminationCondition.maxIterations:
    raise ValueError("达到最大迭代次数：可能未收敛到最优解，请增加迭代次数或调整参数")
elif status == TerminationCondition.timeLimit:
    raise ValueError("达到时间限制：可能未收敛到最优解，请增加时间限制")
else:
    raise ValueError(f"求解器异常终止: {status}")
```

### 2. 决策变量范围检查

求解完成后，必须检查所有决策变量的值是否在物理合理范围内。

```python
# 遍历所有变量，检查范围
for var in model.component_objects(pyo.Var, active=True):
    for index in var:
        value = pyo.value(var[index])
        # 检查 inf/nan
        if math.isinf(value) or math.isnan(value):
            raise ValueError(f"变量 {var.name}[{index}] 值为 inf/nan")
        # 检查变量上下界（如果定义了）
        if var[index].lb is not None and value < var[index].lb - 1e-6:
            raise ValueError(f"变量 {var.name}[{index}] = {value} 低于下界 {var[index].lb}")
        if var[index].ub is not None and value > var[index].ub + 1e-6:
            raise ValueError(f"变量 {var.name}[{index}] = {value} 超过上界 {var[index].ub}")
```

### 3. 约束满足检查

求解完成后，必须检查所有约束是否满足（允许微小的数值误差）。

```python
tolerance = 1e-6  # 数值误差容限

for con in model.component_objects(pyo.Constraint, active=True):
    for index in con:
        # 获取约束的左值、右值和关系
        c = con[index]
        lhs = pyo.value(c.body)
        if c.equality:
            # 等式约束：lhs == rhs
            rhs = pyo.value(c.upper)
            if abs(lhs - rhs) > tolerance:
                raise ValueError(f"约束 {con.name}[{index}] 不满足: {lhs} != {rhs}, 差值 {abs(lhs-rhs)}")
        else:
            # 不等式约束：lb <= lhs <= ub
            if c.lower is not None:
                lb = pyo.value(c.lower)
                if lhs < lb - tolerance:
                    raise ValueError(f"约束 {con.name}[{index}] 不满足: {lhs} < {lb}")
            if c.upper is not None:
                ub = pyo.value(c.upper)
                if lhs > ub + tolerance:
                    raise ValueError(f"约束 {con.name}[{index}] 不满足: {lhs} > {ub}")
```

### 4. 目标值量级检查

求解完成后，必须检查目标值的量级是否合理。

```python
obj_value = pyo.value(model.obj)

# 检查 inf/nan
if math.isinf(obj_value) or math.isnan(obj_value):
    raise ValueError(f"目标值为 inf/nan: {obj_value}")

# 检查量级（根据问题实际情况调整阈值）
abs_obj = abs(obj_value)
if abs_obj > 1e15:
    raise ValueError(f"目标值量级过大: {obj_value} (>1e15)，可能是单位错误或计算溢出")
if abs_obj < 1e-15 and obj_value != 0:
    raise ValueError(f"目标值量级过小: {obj_value} (<1e-15)，可能是单位错误或数值不稳定")

# 检查目标值符号（根据问题是最大化还是最小化）
# 如果是最大化问题，目标值不应该是负数（除非问题允许）
# 如果是最小化问题，目标值不应该是负数（除非问题允许）
```

### 5. 对偶变量合理性检查（LP/MILP 可选）

如果需要做灵敏度分析，必须检查对偶变量（影子价格）的合理性。

```python
# 启用对偶后缀
model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

# 求解后检查对偶变量
for con in model.component_objects(pyo.Constraint, active=True):
    for index in con:
        dual_value = model.dual[con[index]]
        if math.isinf(dual_value) or math.isnan(dual_value):
            raise ValueError(f"约束 {con.name}[{index}] 对偶变量为 inf/nan")
        # 对偶变量的符号应该与约束类型一致
        # <= 约束的对偶变量应该 <= 0（最小化问题）
        # >= 约束的对偶变量应该 >= 0（最小化问题）
```

### 6. 整数变量完整性检查（MILP）

如果是整数规划，必须检查整数变量的值是否真的是整数。

```python
for var in model.component_objects(pyo.Var, active=True):
    if var.domain in (pyo.Integer, pyo.Binary, pyo.NonNegativeIntegers):
        for index in var:
            value = pyo.value(var[index])
            if abs(value - round(value)) > 1e-6:
                raise ValueError(f"整数变量 {var.name}[{index}] = {value} 不是整数（误差 >1e-6）")
```

## 二、自检脚本模板

求解完成后，必须运行以下自检脚本，所有检查通过才能将结果写入 result_registry。

```python
def numerical_sanity_check(model, tolerance=1e-6):
    """优化模型数值合理性自检，所有检查通过返回 True，否则抛出异常。"""
    import math
    import pyomo.environ as pyo
    from pyomo.opt import TerminationCondition

    # 1. 求解器状态检查（需要传入 results）
    # if results.solver.termination_condition != TerminationCondition.optimal:
    #     raise ValueError(...)

    # 2. 决策变量范围检查
    for var in model.component_objects(pyo.Var, active=True):
        for index in var:
            value = pyo.value(var[index])
            if math.isinf(value) or math.isnan(value):
                raise ValueError(f"变量 {var.name}[{index}] = {value} (inf/nan)")

    # 3. 约束满足检查
    for con in model.component_objects(pyo.Constraint, active=True):
        for index in con:
            c = con[index]
            lhs = pyo.value(c.body)
            if c.equality:
                rhs = pyo.value(c.upper)
                if abs(lhs - rhs) > tolerance:
                    raise ValueError(f"约束 {con.name}[{index}] 不满足: |{lhs}-{rhs}|={abs(lhs-rhs)} > {tolerance}")
            else:
                if c.lower is not None and lhs < pyo.value(c.lower) - tolerance:
                    raise ValueError(f"约束 {con.name}[{index}] 不满足: {lhs} < {pyo.value(c.lower)}")
                if c.upper is not None and lhs > pyo.value(c.upper) + tolerance:
                    raise ValueError(f"约束 {con.name}[{index}] 不满足: {lhs} > {pyo.value(c.upper)}")

    # 4. 目标值量级检查
    obj_value = pyo.value(model.obj)
    if math.isinf(obj_value) or math.isnan(obj_value):
        raise ValueError(f"目标值为 inf/nan: {obj_value}")
    if abs(obj_value) > 1e15:
        raise ValueError(f"目标值量级过大: {obj_value}")

    return True
```

## 三、常见问题与处理

| 问题 | 可能原因 | 处理方法 |
|------|---------|---------|
| 模型不可行 | 约束之间矛盾、变量范围设置错误 | 放松约束、检查变量范围、用 IIS 找出矛盾约束 |
| 模型无界 | 缺少约束、目标函数方向错误 | 增加约束、检查目标函数方向 |
| 目标值 inf/nan | 除零、对数取非正数、变量未初始化 | 检查分母、检查对数输入、给变量初始值 |
| 约束不满足 | 求解器精度不足、容限设置过小 | 增加求解器迭代次数、调整容限、检查约束定义 |
| 整数变量不是整数 | 求解器精度不足、MIP gap 过大 | 减小 MIP gap、增加求解器迭代次数 |
| 目标值量级过大 | 单位错误、变量缩放不当 | 统一单位、对变量进行缩放 |

## 四、自检清单

求解完成后，逐项检查：

- [ ] 求解器状态为 optimal（不是 infeasible/unbounded/maxIterations）
- [ ] 所有决策变量值无 inf/nan
- [ ] 所有决策变量值在定义的上下界范围内
- [ ] 所有约束满足（误差 < 1e-6）
- [ ] 目标值无 inf/nan
- [ ] 目标值量级合理（< 1e15）
- [ ] 整数变量值为整数（MILP）
- [ ] 对偶变量无 inf/nan（如需要灵敏度分析）
- [ ] 自检结果写入 run_manifest
