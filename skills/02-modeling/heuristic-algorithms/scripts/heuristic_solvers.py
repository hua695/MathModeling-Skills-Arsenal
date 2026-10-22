#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启发式求解器统一库（heuristic-algorithms 配套脚本 v1.0）

三个算法统一接口（默认最大化目标）:
    ga(fitness, n_var, bounds, ...)  遗传算法（实数编码）
    sa(fitness, x0, neighbor, ...)   模拟退火（自定义邻域）
    pso(fitness, n_var, bounds, ...) 粒子群

每个返回 (best_x, best_fit, history)，history 用于画收敛曲线。

自定义问题: 在 __main__ 中替换 fitness 函数（只依赖 numpy，无需改动算法主体）。

命令行演示（Ackley 函数三算法对比）:
    python heuristic_solvers.py demo --n-var 10

对接: 结果落盘 results/ 并配收敛曲线 → orchestrator result_registry；
      随机种子固定，保证可复现（论文附录写明 seed）。
"""
import argparse
import json
import os
import time

import numpy as np

SEED = 42


def _rng(seed):
    return np.random.default_rng(seed)


# ---------------------------------------------------------------- GA
def ga(fitness, n_var, bounds, n_pop=100, n_gen=200, pc=0.8, pm=0.1,
       seed=SEED, maximize=True):
    """实数编码遗传算法。fitness(x: np.ndarray) -> float"""
    rng = _rng(seed)
    lo, hi = np.array(bounds[0], float), np.array(bounds[1], float)
    pop = rng.uniform(lo, hi, (n_pop, n_var))
    sign = 1.0 if maximize else -1.0
    best_x, best_f, history = None, -np.inf, []

    for _ in range(n_gen):
        fits = sign * np.array([fitness(x) for x in pop])
        order = np.argsort(-fits)[: n_pop // 2]
        parents = pop[order]
        # 均匀交叉 + 高斯变异
        children = []
        while len(children) < n_pop - len(parents):
            a, b = parents[rng.integers(len(parents), size=2)]
            mask = rng.random(n_var) < pc
            child = np.where(mask, a, b)
            child = child + rng.normal(0, 0.1, n_var) * (hi - lo) * (rng.random() < pm)
            children.append(np.clip(child, lo, hi))
        pop = np.vstack([parents, np.array(children)[: n_pop - len(parents)]])
        if fits.max() > best_f:
            best_f, best_x = float(fits.max()), pop[np.argmax(fits)].copy()
        history.append(best_f)
    return best_x, best_f * sign, history


# ---------------------------------------------------------------- SA
def sa(fitness, x0, neighbor, t0=100.0, t_min=1e-3, alpha=0.95,
       seed=SEED, maximize=True):
    """模拟退火。neighbor(x)->x' 返回邻域点；fitness 默认最大化。"""
    rng = _rng(seed)
    sign = 1.0 if maximize else -1.0
    x, e = np.array(x0, float), sign * fitness(x0)
    best_x, best_e, history = x.copy(), e, [e]
    t = t0
    while t > t_min:
        xn = neighbor(x)
        en = sign * fitness(xn)
        if en < e or rng.random() < np.exp(-(en - e) / max(t, 1e-9)):
            x, e = xn, en
            if e < best_e:
                best_e, best_x = e, xn.copy()
        t *= alpha
        history.append(best_e)
    return best_x, best_e * sign, history


# ---------------------------------------------------------------- PSO
def pso(fitness, n_var, bounds, n_p=50, n_iter=200, w=0.7, c1=1.5, c2=1.5,
        seed=SEED, maximize=True):
    """粒子群优化。"""
    rng = _rng(seed)
    lo, hi = np.array(bounds[0], float), np.array(bounds[1], float)
    x = rng.uniform(lo, hi, (n_p, n_var))
    v = rng.uniform(-(hi - lo) * 0.1, (hi - lo) * 0.1, (n_p, n_var))
    sign = 1.0 if maximize else -1.0
    fits = sign * np.array([fitness(xi) for xi in x])
    pbest, pbest_f = x.copy(), fits.copy()
    gbest, gbest_f = pbest[np.argmax(pbest_f)].copy(), pbest_f.max()
    history = []
    for _ in range(n_iter):
        r1, r2 = rng.random((n_p, n_var)), rng.random((n_p, n_var))
        v = w * v + c1 * r1 * (pbest - x) + c2 * r2 * (gbest - x)
        x = np.clip(x + v, lo, hi)
        fits = sign * np.array([fitness(xi) for xi in x])
        better = fits > pbest_f
        pbest[better], pbest_f[better] = x[better], fits[better]
        if pbest_f.max() > gbest_f:
            gbest, gbest_f = pbest[np.argmax(pbest_f)].copy(), pbest_f.max()
        history.append(gbest_f)
    return gbest, gbest_f * sign, history


# ---------------------------------------------------------------- demo
def ackley(x):
    """多峰测试函数：全局最优 x=0, f=0（最小化演示用负号翻转）。"""
    d = len(x)
    a, b, c = 20, 0.2, 2 * np.pi
    s1 = -a * np.exp(-b * np.sqrt(np.mean(x**2)))
    s2 = -np.exp(np.mean(np.cos(c * x)))
    return -(s1 + s2 + a + np.e)  # 取负 → 最大化形式，最优=0


def demo(n_var):
    bounds = ([-5.0] * n_var, [5.0] * n_var)
    results = {}
    for name, runner in [
        ("GA", lambda: ga(ackley, n_var, bounds)),
        ("PSO", lambda: pso(ackley, n_var, bounds)),
        ("SA", lambda: sa(ackley, np.zeros(n_var),
                          lambda x: x + np.random.default_rng().normal(0, 0.3, n_var),
                          t0=50, alpha=0.97)),
    ]:
        t0 = time.time()
        best_x, best_f, hist = runner()
        results[name] = {"best_f": round(best_f, 6), "time_s": round(time.time() - t0, 2),
                         "n_iter": len(hist)}
        print(f"{name}: f*={best_f:.6f} 耗时 {results[name]['time_s']}s 迭代 {len(hist)}")
    # 收敛曲线数据落盘（论文图用）
    os.makedirs("results", exist_ok=True)
    with open("results/convergence_demo.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n对比结果: results/convergence_demo.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="启发式求解器库（GA/SA/PSO）")
    ap.add_argument("mode", choices=["demo"], help="当前仅 demo（自定义问题改 fitness）")
    ap.add_argument("--n-var", type=int, default=10)
    args = ap.parse_args()
    demo(args.n_var)
