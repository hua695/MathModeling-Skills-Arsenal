#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞赛 EDA 一键报告生成器（data-science-stack 配套脚本 v1.0）

用法:
    python eda_report.py data.csv
    python eda_report.py data.xlsx --sheet Sheet1 --target 销量 --out report_dir

输出:
    report_dir/report.md   数据报告（论文"数据预处理/探索性分析"节素材）
    report_dir/figures/    分布直方图、相关热力图、分组箱线图

对接: 报告落盘后进入 orchestrator 的 result_registry；图表交给 scipilot 精修。
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 中文字体（国赛论文中文图表必需）
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Noto Sans CJK SC"]
plt.rcParams["axes.unicode_minus"] = False


def load_data(path: str, sheet: str | None) -> pd.DataFrame:
    """读取 csv/xlsx，自动处理 gbk 编码。"""
    if path.endswith((".xlsx", ".xls")):
        return pd.read_excel(path, sheet_name=sheet)
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"无法解码 {path}（utf-8/gbk 均失败）")


def iqr_outliers(s: pd.Series) -> int:
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    return int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())


def build_report(df: pd.DataFrame, target: str | None, out_dir: str) -> str:
    """逐列体检 → report.md。每行结论都是论文可引用的素材。"""
    lines = ["# 数据报告", "", f"- 数据形状: {df.shape[0]} 行 × {df.shape[1]} 列", f"- 重复行: {df.duplicated().sum()}"]
    lines += ["", "## 逐列体检", "", "| 列 | 类型 | 缺失率 | 唯一值/均值 | 异常数 | 处理建议 |", "|---|---|---|---|---|---|"]

    num_cols, cat_cols = [], []
    for col in df.columns:
        s = df[col]
        miss = s.isnull().mean()
        if pd.api.types.is_numeric_dtype(s):
            num_cols.append(col)
            if target and col == target:
                lines.append(f"| {col} | 数值(目标) | {miss:.1%} | 均值 {s.mean():.4g} | {iqr_outliers(s)} | 目标列 |")
            else:
                adv = "缩尾/保留" if iqr_outliers(s) / max(len(s), 1) > 0.05 else "一般处理"
                lines.append(f"| {col} | 数值 | {miss:.1%} | 均值 {s.mean():.4g} | {iqr_outliers(s)} | 缺失插值,异常{adv} |")
        else:
            cat_cols.append(col)
            lines.append(f"| {col} | 类别 | {miss:.1%} | {s.nunique()} 类 | - | 众数填充/OneHot |")

    # 相关性（数值列）
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        strong = [(corr.index[i], corr.columns[j], corr.iloc[i, j])
                  for i in range(len(corr)) for j in range(i + 1, len(corr))
                  if abs(corr.iloc[i, j]) > 0.8]
        lines += ["", "## 相关性", ""]
        if strong:
            lines += ["高相关对 (>0.8, 需去重/注意共线性):"]
            lines += [f"- {a} ~ {b}: {r:.3f}" for a, b, r in strong]
        else:
            lines.append("- 无明显高相关对 (|r|>0.8)")
        # 与目标列的相关性排序
        if target and target in corr.columns:
            ranks = corr[target].drop(target).abs().sort_values(ascending=False)
            lines += ["", "## 与目标列相关度排序", ""]
            lines += [f"- {k}: |r|={v:.3f}" for k, v in ranks.head(8).items()]

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path, num_cols, cat_cols


def plot_figures(df: pd.DataFrame, num_cols, cat_cols, target, out_dir):
    """三张基础图：分布直方图、相关热力图、目标分组箱线图。"""
    fig_dir = os.path.join(out_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    # 1. 数值列分布（最多 12 列，分两排）
    cols = [c for c in num_cols if c != target][:12]
    if cols:
        n = len(cols)
        fig, axes = plt.subplots(2, (n + 1) // 2, figsize=(14, 6))
        for ax, c in zip(np.array(axes).ravel(), cols):
            df[c].dropna().hist(bins=30, ax=ax, alpha=0.7, edgecolor="white")
            ax.set_title(c, fontsize=10)
        fig.suptitle("数值列分布", fontsize=13)
        fig.tight_layout()
        fig.savefig(os.path.join(fig_dir, "distributions.png"), dpi=150)
        plt.close(fig)

    # 2. 相关热力图
    if len(num_cols) >= 2:
        fig, ax = plt.subplots(figsize=(8, 7))
        im = ax.imshow(df[num_cols].corr(), cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(num_cols)), num_cols, rotation=45, ha="right", fontsize=9)
        ax.set_yticks(range(len(num_cols)), num_cols, fontsize=9)
        for i in range(len(num_cols)):
            for j in range(len(num_cols)):
                ax.text(j, i, f"{df[num_cols].corr().iloc[i, j]:.2f}",
                        ha="center", va="center", fontsize=7)
        fig.colorbar(im, shrink=0.8)
        fig.suptitle("相关热力图", fontsize=13)
        fig.tight_layout()
        fig.savefig(os.path.join(fig_dir, "correlation.png"), dpi=150)
        plt.close(fig)

    # 3. 目标列按类别分组箱线图
    if target and cat_cols:
        for c in cat_cols[:2]:
            fig, ax = plt.subplots(figsize=(10, 5))
            df.boxplot(column=target, by=c, ax=ax, rot=45, grid=False)
            ax.set_title(f"{target} 按 {c} 分组", fontsize=12)
            fig.suptitle("")
            fig.tight_layout()
            fig.savefig(os.path.join(fig_dir, f"group_{c}.png"), dpi=150)
            plt.close(fig)

    print(f"图表已输出: {fig_dir}")


def main():
    ap = argparse.ArgumentParser(description="竞赛 EDA 一键报告")
    ap.add_argument("data", help="数据文件 (csv/xlsx)")
    ap.add_argument("--sheet", default=None, help="xlsx 的 sheet 名")
    ap.add_argument("--target", default=None, help="目标列名（预测/回归目标）")
    ap.add_argument("--out", default="eda_report", help="输出目录")
    args = ap.parse_args()

    df = load_data(args.data, args.sheet)
    print(f"加载成功: {df.shape[0]} 行 × {df.shape[1]} 列")

    report_path, num_cols, cat_cols = build_report(df, args.target, args.out)
    plot_figures(df, num_cols, cat_cols, args.target, args.out)
    print(f"报告已生成: {report_path}")
    print(f"数值列: {len(num_cols)} 个 | 类别列: {len(cat_cols)} 个")


if __name__ == "__main__":
    main()
