#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计推断急救包（stat_kit.py）——data-science-stack 配套脚本 v1.1

Kimi 评审 P0 建议：概率统计未系统学 → 预置 8 个"即用即走"检验，
每个检验输出：统计量 + p 值 + 结论 + 【论文话术】（可直接抄进论文的句子）。

用法:
    python stat_kit.py ttest    data.csv --value 值列 --group 组列        # 两组独立 t 检验
    python stat_kit.py mw       data.csv --value 值列 --group 组列        # Mann-Whitney U（非正态）
    python stat_kit.py chi2     data.csv --col1 类别A --col2 类别B        # 卡方独立性
    python stat_kit.py anova    data.csv --value 值列 --group 组列        # 单因素方差分析
    python stat_kit.py shapiro  data.csv --value 值列                     # 正态性 Shapiro-Wilk
    python stat_kit.py ks       data.csv --value 值列                     # 正态性 K-S
    python stat_kit.py regress  data.csv --y 目标列 --x x1,x2             # 线性回归（含 DW 残差自相关）
    python stat_kit.py vif      data.csv --cols x1,x2,x3                  # 多重共线性 VIF

依赖: pip install numpy pandas scipy statsmodels
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd
from scipy import stats


def load(path: str) -> pd.DataFrame:
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"无法解码 {path}")


def talk(stat_name: str, stat: float, p: float, alpha: float = 0.05) -> str:
    sig = "显著" if p < alpha else "不显著"
    return (f"【论文话术】{stat_name}检验统计量为 {stat:.4f}，p 值 = {p:.4f}"
            f"（{'<0.05' if p < alpha else '>0.05'}），差异{sig}。"
            f"（p<0.05 时：表明……存在统计学差异；否则：不能拒绝原假设，差异无统计学意义。）")


def need(series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").dropna()


def cmd_ttest(a, v, g):
    df = a[[v, g]].dropna()
    groups = [need(df.loc[df[g] == k, v]) for k in df[g].unique()[:2]]
    if len(groups) < 2 or min(len(x) for x in groups) < 2:
        sys.exit("[FATAL] ttest 需要两组且每组 ≥2 个样本")
    t, p = stats.ttest_ind(*groups, equal_var=False)
    print(f"t = {t:.4f}  p = {p:.4f}  自由度 ≈ {min(len(x)-1 for x in groups)}（Welch 近似）")
    print(talk("t", t, p))


def cmd_mw(a, v, g):
    df = a[[v, g]].dropna()
    groups = [need(df.loc[df[g] == k, v]) for k in df[g].unique()[:2]]
    u, p = stats.mannwhitneyu(*groups, alternative="two-sided")
    print(f"U = {u:.4f}  p = {p:.4f}")
    print(talk("Mann-Whitney U", u, p))


def cmd_chi2(a, c1, c2):
    ct = pd.crosstab(a[c1], a[c2])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    print(f"chi2 = {chi2:.4f}  p = {p:.4f}  自由度 = {dof}")
    print(f"交叉表:\n{ct.to_string()}")
    print(talk("卡方", chi2, p))


def cmd_anova(a, v, g):
    df = a[[v, g]].dropna()
    groups = [need(df.loc[df[g] == k, v]) for k in df[g].unique()]
    if len(groups) < 2:
        sys.exit("[FATAL] ANOVA 需要 ≥2 组")
    f, p = stats.f_oneway(*groups)
    print(f"F = {f:.4f}  p = {p:.4f}")
    print(talk("单因素方差分析", f, p))
    if p < 0.05:
        print("提示: 组间差异显著，可用 Tukey HSD 找出具体差异组 "
              "(statsmodels.stats.multicomp.pairwise_tukeyhsd)")


def cmd_shapiro(a, v):
    s = need(a[v])
    if len(s) > 5000:
        print("[WARN] n>5000，Shapiro 过于敏感，建议结合偏度/峰度判断")
    w, p = stats.shapiro(s.sample(min(len(s), 5000), random_state=42))
    print(f"W = {w:.4f}  p = {p:.4f}")
    print(talk("Shapiro-Wilk 正态性", w, p))
    print("（p>0.05：不拒绝正态假设，可用参数检验；否则用非参数检验）")


def cmd_ks(a, v):
    s = need(a[v])
    mu, sd = s.mean(), s.std()
    # 用自定义 CDF 绕开 scipy 新版 kstest 的 args 传参差异
    d, p = stats.kstest(s, lambda x: stats.norm.cdf(x, mu, sd))
    print(f"D = {d:.4f}  p = {p:.4f}")
    print(talk("K-S 正态性", d, p))


def cmd_regress(a, y, xs):
    import statsmodels.api as sm
    X = a[xs.split(",")].apply(pd.to_numeric, errors="coerce")
    Y = pd.to_numeric(a[y], errors="coerce")
    mask = X.notna().all(axis=1) & Y.notna()
    Xc, Yc = sm.add_constant(X[mask]), Y[mask]
    model = sm.OLS(Yc, Xc).fit()
    print(model.summary2().tables[1].to_string())
    print(f"R^2 = {model.rsquared:.4f}  调整R^2 = {model.rsquared_adj:.4f}")
    # Durbin-Watson 残差自相关
    from statsmodels.stats.stattools import durbin_watson
    dw = durbin_watson(model.resid)
    print(f"Durbin-Watson = {dw:.4f}（≈2 无自相关；<1.5 或 >2.5 需警惕）")
    print("【论文话术】回归模型 R^2 = {:.4f}，DW = {:.4f}，各系数显著性见上表。".format(model.rsquared, dw))


def cmd_vif(a, cols):
    import statsmodels.api as sm
    X = a[cols.split(",")].apply(pd.to_numeric, errors="coerce").dropna()
    Xc = sm.add_constant(X)
    out = {}
    for c in X.columns:
        vif = 1 / (1 - sm.OLS(X[c], Xc.drop(columns=c)).fit().rsquared)
        out[c] = round(float(vif), 2)
    print("VIF（>10 严重共线性，>5 需关注）:")
    for k, v in out.items():
        flag = "  [WARN] VIF>10" if v > 10 else ("  [~] VIF>5" if v > 5 else "")
        print(f"  {k}: {v}{flag}")


COMMANDS = {"ttest": cmd_ttest, "mw": cmd_mw, "chi2": cmd_chi2, "anova": cmd_anova,
            "shapiro": cmd_shapiro, "ks": cmd_ks, "regress": cmd_regress, "vif": cmd_vif}
CMD_ARGS = {"ttest": {"value": "v", "group": "g"}, "mw": {"value": "v", "group": "g"},
            "chi2": {"col1": "c1", "col2": "c2"}, "anova": {"value": "v", "group": "g"},
            "shapiro": {"value": "v"}, "ks": {"value": "v"},
            "regress": {"y": "y", "x": "xs"}, "vif": {"cols": "cols"}}


def main():
    ap = argparse.ArgumentParser(description="统计推断急救包（8 检验）")
    ap.add_argument("cmd", choices=list(COMMANDS), help="检验名")
    ap.add_argument("data", help="数据 csv")
    ap.add_argument("--value", default=None, help="数值列")
    ap.add_argument("--group", default=None, help="分组列")
    ap.add_argument("--col1", default=None)
    ap.add_argument("--col2", default=None)
    ap.add_argument("--y", default=None, help="回归目标列")
    ap.add_argument("--x", default=None, help="回归特征列（逗号分隔）")
    ap.add_argument("--cols", default=None, help="VIF 特征列（逗号分隔）")
    args = ap.parse_args()

    df = load(args.data)
    kwargs = {CMD_ARGS[args.cmd][k]: v for k, v in {"value": args.value, "group": args.group,
                                                    "col1": args.col1, "col2": args.col2,
                                                    "y": args.y, "x": args.x,
                                                    "cols": args.cols}.items()
              if k in CMD_ARGS[args.cmd]}
    COMMANDS[args.cmd](df, **kwargs)


if __name__ == "__main__":
    main()
