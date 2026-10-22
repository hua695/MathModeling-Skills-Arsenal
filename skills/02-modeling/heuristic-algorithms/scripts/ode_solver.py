#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ODE 数值求解 + 参数辨识（heuristic-algorithms 配套脚本 v1.0）

功能:
    1. solve_ivp 数值求解自定义 ODE 系统 → 解曲线图
    2. 有观测数据时用 curve_fit 拟合模型参数（论文"参数估计"节）

用法（演示 SIR 传染病模型）:
    python ode_solver.py demo
    python ode_solver.py fit --data sir_cases.csv --tmax 60

自定义问题: 修改 ode_system(t, y, params) 与 __main__ 中的初值/参数。

输出 (out_dir/):
    solution.png   解曲线（含关键量标注，如峰值）
    params.json    拟合参数 + 协方差
    report.txt     论文素材（初始条件、参数、峰值时间）

依赖: pip install numpy scipy matplotlib
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Noto Sans CJK SC"]
plt.rcParams["axes.unicode_minus"] = False


def ode_system(t, y, beta, gamma):
    """SIR 模型：y = [S, I, R]；beta 感染率, gamma 康复率。自定义时替换本函数。"""
    S, I, R = y
    dS = -beta * S * I
    dI = beta * S * I - gamma * I
    dR = gamma * I
    return [dS, dI, dR]


def solve_ode(y0, params, t_span=(0, 60), n_points=300, method="RK45"):
    """求解并返回 (t, sol, ok)。sol 形状 (len(y0), n_points)。"""
    res = solve_ivp(ode_system, t_span, y0, args=params,
                    method=method, dense_output=True, rtol=1e-6)
    if not res.success:
        raise RuntimeError(f"求解失败: {res.message}（换 method='LSODA' 或检查参数）")
    t = np.linspace(*t_span, n_points)
    return t, res.sol(t), res.success


def fit_params(t_obs, y_obs, p0=(0.5, 0.2), bounds=([0, 0], [5, 5])):
    """用观测数据拟合 [beta, gamma]。y_obs 为感染人数 I(t)。"""
    def model(t, beta, gamma):
        t2, sol, _ = solve_ode((1 - 1e-3, 1e-3, 0.0), (beta, gamma), t_span=(0, max(t)), n_points=len(t))
        return sol[1]  # I 曲线

    popt, pcov = curve_fit(model, t_obs, y_obs, p0=p0, bounds=bounds, maxfev=5000)
    perr = np.sqrt(np.diag(pcov))
    return popt, perr


def main():
    ap = argparse.ArgumentParser(description="ODE 求解 + 参数辨识")
    ap.add_argument("mode", choices=["demo", "fit"], help="demo=演示; fit=参数拟合")
    ap.add_argument("--data", default=None, help="观测数据 csv（两列: t, I）")
    ap.add_argument("--tmax", type=float, default=60.0)
    ap.add_argument("--out", default="ode_results", help="输出目录")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    report = ["# ODE 模型报告", ""]
    y0 = (1 - 1e-3, 1e-3, 0.0)

    if args.mode == "demo":
        params = (0.3, 0.1)
        t, sol, _ = solve_ode(y0, params, t_span=(0, args.tmax))
        S, I, R = sol
        peak_t, peak_I = t[np.argmax(I)], I.max()
        report += [f"- 模型: SIR（β={params[0]}, γ={params[1]}）", f"- 初始条件: S0={y0[0]:.4f}, I0={y0[1]:.4f}, R0={y0[2]:.4f}",
                   f"- 感染峰值: {peak_I:.4f} @ t={peak_t:.1f}",
                   f"- 终态: S∞={S[-1]:.4f}, 累计感染≈{1 - S[-1]:.4f}", ""]
    else:  # fit
        if not args.data:
            raise SystemExit("fit 模式需要 --data csv（两列: t, I）")
        raw = np.loadtxt(args.data, delimiter=",", skiprows=1)
        t_obs, y_obs = raw[:, 0], raw[:, 1]
        (beta, gamma), (eb, eg) = fit_params(t_obs, y_obs)
        params = (float(beta), float(gamma))
        t, sol, _ = solve_ode(y0, params, t_span=(0, args.tmax))
        S, I, R = sol
        report += [f"- 拟合参数: β={beta:.4f}±{eb:.4f}, γ={gamma:.4f}±{eg:.4f}",
                   f"- 决定系数 vs 观测: R²=...（用拟合曲线重算）", ""]
        # 与观测对比
        y_fit = np.interp(t_obs, t, I)
        ss_res = np.sum((y_obs - y_fit) ** 2)
        ss_tot = np.sum((y_obs - y_obs.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot
        report[-2] = f"- 决定系数 vs 观测: R²={r2:.4f}"
        json.dump({"beta": beta, "gamma": gamma, "beta_err": eb, "gamma_err": eg, "R2": r2},
                  open(os.path.join(args.out, "params.json"), "w"), indent=2)

    with open(os.path.join(args.out, "report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print("\n".join(report))

    # 画图：三仓室曲线 + 峰值标注
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(t, S, label="S 易感", color="#2c3e50", lw=1.8)
    ax.plot(t, I, label="I 感染", color="#c0392b", lw=1.8)
    ax.plot(t, R, label="R 康复", color="#27ae60", lw=1.8)
    peak_idx = int(np.argmax(I))
    ax.scatter([t[peak_idx]], [I[peak_idx]], color="#c0392b", zorder=5)
    ax.annotate(f"峰值 {I[peak_idx]:.3f}\nt={t[peak_idx]:.1f}",
                (t[peak_idx], I[peak_idx]), textcoords="offset points",
                xytext=(10, -14), fontsize=9)
    ax.set_xlabel("时间 t"); ax.set_ylabel("比例")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, "solution.png"), dpi=150)
    print(f"\n输出: {args.out}/ (solution.png, report.txt)")


if __name__ == "__main__":
    main()
