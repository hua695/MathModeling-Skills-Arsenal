# heuristic-algorithms · 模板脚本

赛时直接调用。与 `pyomo`（精确求解）互补：精确求解超时/不可行时切换启发式。

## 脚本列表

| 脚本 | 功能 | 用法 |
|---|---|---|
| `heuristic_solvers.py` | GA / SA / PSO 统一接口库（返回 best_x, best_fit, history 收敛曲线） | `python heuristic_solvers.py demo --n-var 5`（自定义问题改 fitness） |
| `ode_solver.py` | ODE 数值求解 + 观测数据参数辨识（curve_fit）+ 解曲线图 | `python ode_solver.py demo` / `python ode_solver.py fit --data obs.csv` |

## 快速开始

```bash
# 1) 三算法对比演示（验证环境 + 看收敛）
python scripts/heuristic_solvers.py demo --n-var 5

# 2) 自定义优化问题：复制 heuristic_solvers.py，
#    把 __main__ 里的 ackley 换成你的目标函数，调用 ga/pso/sa
from heuristic_solvers import ga, pso, sa
best_x, best_f, history = ga(my_fitness, n_var, bounds, n_pop=100, n_gen=200)

# 3) ODE 求解：改 ode_system() 为你的微分方程组
python scripts/ode_solver.py demo

# 4) 参数辨识（有观测数据时）：csv 两列 t,I
python scripts/ode_solver.py fit --data observations.csv
```

## 依赖

```bash
pip install numpy scipy matplotlib
```

## 输出对接（论文规范）

| 输出 | 论文用途 | 要求 |
|---|---|---|
| `history` 收敛序列 | 收敛曲线图（每次启发式求解必配） | x=迭代次数, y=目标值 |
| 多算法对比（GA/PSO/SA） | "模型求解"对比表 | 目标值 + 耗时 + 迭代数 |
| `results/convergence_demo.json` | demo 对比数据 | 直接转表格 |
| `solution.png` + `report.txt` | ODE 解曲线 + 参数/峰值 | 峰值点必须在图上标注 |
| `params.json` | 参数辨识结果（含误差±） | 论文"参数估计"节 |

## 纪律（雷区）

1. **必须固定 seed**（脚本默认 seed=42），论文附录写明，否则结果不可复现
2. **必须有 baseline 对比**：贪心/局部搜索 → 启发式提升 X% 的叙事结构
3. **求解前先估规模**：小问题用 pyomo 精确求解，不要用启发式
4. 论文数字必须与脚本输出一致，禁止手改
