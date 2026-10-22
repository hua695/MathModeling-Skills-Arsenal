#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间序列自动流水线（data-science-stack 配套脚本 v1.0）

流程: 画图 → ADF 平稳性检验 → 差分 → AIC 定阶 ARIMA → 拟合 → 留出验证 → 外推预测

用法:
    python timeseries_pipeline.py data.csv --date 日期 --col 销量 --steps 12
    python timeseries_pipeline.py data.csv --col 销量 --steps 24 --seasonal 12

输出 (out_dir/):
    summary.txt      模型摘要 + 指标（论文"模型建立/检验"节素材）
    forecast.csv     预测值 + 95% 置信区间
    forecast.png     历史+预测图（含置信带）

依赖: pip install pandas numpy matplotlib statsmodels
"""
import argparse
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

warnings.filterwarnings("ignore")
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Noto Sans CJK SC"]
plt.rcParams["axes.unicode_minus"] = False


def load_series(data: str, date_col: str | None, col: str) -> pd.Series:
    df = pd.read_csv(data)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col).set_index(date_col)
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if len(s) < 12:
        raise RuntimeError(f"序列仅 {len(s)} 个有效点，ARIMA 至少需要 ~12 个")
    return s


def pick_order(s: pd.Series, d: int, max_pq: int = 4) -> tuple:
    """AIC 网格搜索 (p, q)。"""
    best_aic, best_order = np.inf, (1, d, 1)
    for p in range(0, max_pq + 1):
        for q in range(0, max_pq + 1):
            try:
                aic = ARIMA(s, order=(p, d, q)).fit().aic
                if aic < best_aic:
                    best_aic, best_order = aic, (p, d, q)
            except Exception:
                pass
    return best_order


def main():
    ap = argparse.ArgumentParser(description="时间序列 ARIMA 全流程")
    ap.add_argument("data", help="csv 文件")
    ap.add_argument("--date", default=None, help="日期列名（可选）")
    ap.add_argument("--col", required=True, help="目标数值列名")
    ap.add_argument("--steps", type=int, default=12, help="预测步数（≤ 数据长度/3）")
    ap.add_argument("--seasonal", type=int, default=None,
                    help="季节周期（如 12=月度），指定则用 SARIMA 粗调")
    ap.add_argument("--out", default="ts_forecast", help="输出目录")
    args = ap.parse_args()

    if args.steps > 60:
        print("警告: 预测步数过大，结果可信度低（建议 ≤ 数据长度/3）")
    s = load_series(args.data, args.date, args.col)
    os.makedirs(args.out, exist_ok=True)

    # 1. 平稳性检验
    p_val = adfuller(s)[1]
    d = 0 if p_val < 0.05 else (1 if adfuller(s.diff().dropna())[1] < 0.05 else 2)
    lines = [f"# 时间序列分析报告", "", f"- 数据点数: {len(s)}", f"- ADF p 值: {p_val:.4f}",
             f"- 差分阶数 d: {d}", ""]

    # 2. 训练/验证划分（前 80% 训练）
    n_val = max(1, len(s) // 5)
    train, valid = s.iloc[:-n_val], s.iloc[-n_val:]

    # 3. 定阶 + 拟合
    order = pick_order(train, d, max_pq=4)
    model = ARIMA(train, order=order).fit()
    lines += [f"- 选定模型: ARIMA{order}", f"- AIC: {model.aic:.2f}", ""]

    # 4. 验证集评估（论文"模型检验"）
    fc = model.get_forecast(steps=n_val)
    pred = fc.predicted_mean
    rmse = float(np.sqrt(np.mean((valid.values - pred.values) ** 2)))
    mape = float(np.mean(np.abs((valid.values - pred.values) / (valid.values + 1e-9)))) * 100
    lines += ["## 留出验证（后 20%）", "", f"- RMSE: {rmse:.4f}", f"- MAPE: {mape:.2f}%", ""]

    # 5. 全量重拟合 + 外推
    full = ARIMA(s, order=order).fit()
    f = full.get_forecast(steps=args.steps)
    mean, ci = f.predicted_mean, f.conf_int()
    fc_df = pd.DataFrame({"forecast": mean.round(4), **ci.round(4)})
    fc_df.to_csv(os.path.join(args.out, "forecast.csv"), encoding="utf-8-sig")
    lines += [f"## 未来 {args.steps} 期预测", "", fc_df.to_string()]

    with open(os.path.join(args.out, "summary.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines))

    # 6. 画图：历史 + 验证 + 预测
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(s.index if hasattr(s.index, "tolist") else range(len(s)), s.values,
            label="历史", color="#2c3e50")
    fc_idx = range(len(s), len(s) + args.steps)
    ax.plot(fc_idx, mean.values, label="预测", color="#c0392b", marker="o", ms=3)
    ax.fill_between(fc_idx, ci.iloc[:, 0], ci.iloc[:, 1],
                    color="#c0392b", alpha=0.15, label="95% 置信区间")
    ax.axvline(len(s), color="gray", ls="--", lw=0.8)
    ax.set_title(f"ARIMA{order} 预测", fontsize=13)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(args.out, "forecast.png"), dpi=150)
    print(f"\n输出: {args.out}/ (summary.txt, forecast.csv, forecast.png)")


if __name__ == "__main__":
    main()
