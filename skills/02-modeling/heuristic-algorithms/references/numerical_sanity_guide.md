# 启发式算法数值合理性检查规范

本规范适用于遗传算法（GA）、模拟退火（SA）、粒子群（PSO）、蒙特卡洛、NSGA-II 等启发式算法。求解完成后必须执行数值合理性自检，确保"代码运行了但结果是错的"的情况被及时发现。

## 一、必须检查的项目

### 1. 收敛性检查

启发式算法必须检查是否收敛，不能假设迭代结束就一定找到了最优解。

```python
# 模拟退火收敛检查
def check_convergence_sa(history, threshold=1e-6, window=50):
    """检查模拟退火是否收敛：最近 window 次迭代最优解变化 < threshold。"""
    if len(history) < window:
        return False, f"迭代次数不足（{len(history)} < {window}），无法判断收敛"
    recent = history[-window:]
    change = abs(recent[-1] - recent[0])
    if change < threshold:
        return True, f"收敛：最近 {window} 次迭代最优解变化 {change:.2e} < {threshold}"
    else:
        return False, f"未收敛：最近 {window} 次迭代最优解变化 {change:.2e} >= {threshold}，建议增加迭代次数"

# 遗传算法收敛检查
def check_convergence_ga(fitness_history, threshold=1e-6, window=20):
    """检查遗传算法是否收敛：最近 window 代最优适应度变化 < threshold。"""
    if len(fitness_history) < window:
        return False, f"代数不足（{len(fitness_history)} < {window}），无法判断收敛"
    recent = fitness_history[-window:]
    change = abs(recent[-1] - recent[0])
    if change < threshold:
        return True, f"收敛：最近 {window} 代最优适应度变化 {change:.2e} < {threshold}"
    else:
        return False, f"未收敛：最近 {window} 代最优适应度变化 {change:.2e} >= {threshold}"
```

### 2. 解的可行性检查

启发式算法的解必须满足所有约束，不能只看目标函数值。

```python
def check_solution_feasibility(solution, constraints, tolerance=1e-6):
    """检查解是否满足所有约束。"""
    violations = []
    for i, constraint in enumerate(constraints):
        if not constraint(solution, tolerance):
            violations.append(f"约束 {i} 不满足")
    if violations:
        return False, f"解不可行：{len(violations)} 个约束不满足 - {', '.join(violations)}"
    return True, "解可行：所有约束满足"
```

### 3. 目标值合理性检查

```python
def check_objective_reasonable(obj_value, problem_type="minimize"):
    """检查目标值是否合理。"""
    import math
    if math.isinf(obj_value) or math.isnan(obj_value):
        return False, f"目标值为 inf/nan: {obj_value}"
    if abs(obj_value) > 1e15:
        return False, f"目标值量级过大: {obj_value} (>1e15)，可能是单位错误或计算溢出"
    if abs(obj_value) < 1e-15 and obj_value != 0:
        return False, f"目标值量级过小: {obj_value} (<1e-15)，可能是单位错误"
    return True, f"目标值合理: {obj_value}"
```

### 4. 参数敏感性检查（关键参数）

启发式算法的结果对关键参数敏感，必须检查参数设置是否合理。

```python
def check_parameter_sensitivity(algorithm, params, param_ranges, n_runs=5):
    """检查关键参数的敏感性：参数在合理范围内变化时，结果是否稳定。"""
    import numpy as np
    results = []
    for param_name, (min_val, max_val) in param_ranges.items():
        param_results = []
        for _ in range(n_runs):
            test_params = params.copy()
            test_params[param_name] = np.random.uniform(min_val, max_val)
            result = algorithm(test_params)
            param_results.append(result)
        cv = np.std(param_results) / (abs(np.mean(param_results)) + 1e-10)
        if cv > 0.5:
            return False, f"参数 {param_name} 敏感度过高（CV={cv:.2f} > 0.5），结果不稳定"
        results.append((param_name, cv))
    return True, f"参数敏感性正常: {', '.join(f'{name} CV={cv:.3f}' for name, cv in results)}"
```

### 5. 随机种子一致性检查

启发式算法有随机性，必须固定随机种子，确保结果可复现。

```python
def check_random_seed(seed=42):
    """检查随机种子是否固定，确保结果可复现。"""
    import numpy as np
    import random
    if seed is None:
        return False, "未设置随机种子，结果不可复现"
    np.random.seed(seed)
    random.seed(seed)
    return True, f"随机种子已固定: {seed}"
```

### 6. 多样性检查（GA/PSO）

遗传算法和粒子群必须检查种群多样性，避免早熟收敛。

```python
def check_population_diversity(population, threshold=1e-6):
    """检查种群多样性：个体之间的差异是否足够大。"""
    import numpy as np
    if len(population) < 2:
        return False, "种群数量不足，无法检查多样性"
    distances = []
    for i in range(len(population)):
        for j in range(i+1, len(population)):
            dist = np.linalg.norm(np.array(population[i]) - np.array(population[j]))
            distances.append(dist)
    avg_dist = np.mean(distances)
    if avg_dist < threshold:
        return False, f"种群多样性不足：平均距离 {avg_dist:.2e} < {threshold}，可能早熟收敛"
    return True, f"种群多样性正常：平均距离 {avg_dist:.2e}"
```

### 7. 蒙特卡洛收敛检查

蒙特卡洛模拟必须检查收敛性，增加样本量结果应该趋于稳定。

```python
def check_monte_carlo_convergence(results, threshold=0.01):
    """检查蒙特卡洛收敛：前半部分和后半部分的均值差异 < threshold。"""
    import numpy as np
    if len(results) < 100:
        return False, f"样本量不足（{len(results)} < 100），无法判断收敛"
    half = len(results) // 2
    mean1 = np.mean(results[:half])
    mean2 = np.mean(results[half:])
    relative_diff = abs(mean1 - mean2) / (abs(mean1) + 1e-10)
    if relative_diff > threshold:
        return False, f"未收敛：前半均值 {mean1:.4f}，后半均值 {mean2:.4f}，相对差异 {relative_diff:.2%} > {threshold:.0%}"
    return True, f"收敛：前半均值 {mean1:.4f}，后半均值 {mean2:.4f}，相对差异 {relative_diff:.2%}"
```

## 二、自检脚本模板

```python
def numerical_sanity_check_heuristic(result, algorithm_type="sa"):
    """启发式算法数值合理性自检。"""
    checks = []

    # 1. 目标值合理性
    ok, msg = check_objective_reasonable(result["best_fitness"])
    checks.append(("目标值合理性", ok, msg))

    # 2. 解的可行性
    if "constraints" in result:
        ok, msg = check_solution_feasibility(result["best_solution"], result["constraints"])
        checks.append(("解的可行性", ok, msg))

    # 3. 收敛性
    if algorithm_type == "sa" and "fitness_history" in result:
        ok, msg = check_convergence_sa(result["fitness_history"])
        checks.append(("收敛性", ok, msg))
    elif algorithm_type == "ga" and "fitness_history" in result:
        ok, msg = check_convergence_ga(result["fitness_history"])
        checks.append(("收敛性", ok, msg))
    elif algorithm_type == "monte_carlo" and "samples" in result:
        ok, msg = check_monte_carlo_convergence(result["samples"])
        checks.append(("收敛性", ok, msg))

    # 4. 随机种子
    if "seed" in result:
        ok, msg = check_random_seed(result["seed"])
        checks.append(("随机种子", ok, msg))

    # 汇总
    all_passed = all(ok for _, ok, _ in checks)
    return all_passed, checks
```

## 三、常见问题与处理

| 问题 | 可能原因 | 处理方法 |
|------|---------|---------|
| 未收敛 | 迭代次数不足、冷却率过快、学习率过大 | 增加迭代次数、调整冷却率/学习率、调整参数 |
| 解不可行 | 约束处理不当、惩罚系数过小 | 增加惩罚系数、用修复算子、用约束处理技术 |
| 早熟收敛 | 种群多样性不足、交叉/变异率过小 | 增加变异率、用多种群、用自适应参数 |
| 目标值 inf/nan | 适应度函数除零、对数取非正数 | 检查适应度函数、加保护措施 |
| 结果不稳定 | 未固定随机种子、参数敏感度过高 | 固定随机种子、增加运行次数取平均、调整参数 |
| 蒙特卡洛未收敛 | 样本量不足 | 增加样本量、用方差缩减技术 |

## 四、自检清单

求解完成后，逐项检查：

- [ ] 目标值无 inf/nan，量级合理
- [ ] 解满足所有约束（不可行解不能作为最终结果）
- [ ] 算法收敛（最近 N 次迭代最优解变化 < 阈值）
- [ ] 随机种子已固定，结果可复现
- [ ] 种群多样性正常（GA/PSO，无早熟收敛）
- [ ] 蒙特卡洛样本量足够，结果收敛
- [ ] 关键参数敏感性正常（参数变化时结果稳定）
- [ ] 与 baseline 对比有显著提升（防炫技）
- [ ] 自检结果写入 run_manifest
