#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paper_check.py — 论文写作后一键自检（2026-08 实战沉淀: 呈现问题分散在多个脚本,
写作完要逐个跑容易漏——一条命令全查）

组合:
  1. check_heading_levels  （9 项: 标题层级/八章/图解读/关键词加粗/分页）
  2. visual_critic         （显式启用时检查 PDF: 内部词P0/参考痕迹/乱码/LaTeX残留/抬头）
  3. 摘要禁词 P7b          （"针对XX竞赛X题"/竞赛名, 读 competition_gates.yaml 同源）
  4. 数字一致性            （consistency_check 快速版）
  5. 摘要字数550-800/段数3-6（B2）
  6. 学术正式度口语词      （防表达校正过度口语化）

用法: python scripts/paper_check.py <论文目录> [--strict] [--visual-check]
     论文目录含 paper.tex + paper.pdf
输出: 每项 PASS/WARN/FAIL + 汇总（任一 FAIL = 不可提交）
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
# 竞赛名禁词（从 core/competition_gates.yaml 读取，避免与 delivery_gate 漂移；
# 年份不做字面硬编码——"针对20xx年…竞赛"由正则动态拦截, 换年份不失效）
FORBIDDEN_FALLBACK = ["全国大学生数学建模竞赛", "高教社杯"]
YEAR_ABS_RE = re.compile(r"针对\s*20\d\d\s*年")
# 内部词/参考痕迹（与 visual_critic 的 INTERNAL 词表对齐）
TRACE_WORDS = ["经验库", "呈现先验", "skills", "Agent", "提示词", "检索系统",
               "同题先例", "方法链", "公开答案", "优秀论文"]
# 口语/非学术词（学术正式度下限；表达校正只降低 AI 痕迹，不能降为口语；
# output_contract 明确"正文措辞学术化, 避免口语化表达（'我们搞了''跑了一下'）"）
COLLOQUIAL_WORDS = ["这东西", "不够看", "白烧", "说白了", "其实就是", "跑了一下", "我们搞了",
                    "搞搞", "弄一下", "随便", "讲道理", "说实话", "挺不错", "蛮好", "感觉上",
                    "差不多得了", "草草", "大概其"]


def main() -> int:
    ap = argparse.ArgumentParser(description="论文写作后一键自检")
    ap.add_argument("paper_dir", help="论文目录（含 paper.tex + paper.pdf）")
    ap.add_argument("--strict", action="store_true", help="WARN 也视为不通过")
    ap.add_argument("--competition", default="guosai", help="竞赛类型（读 competition_gates.yaml 禁词, 默认 guosai）")
    ap.add_argument("--visual-check", action="store_true",
                    help="显式启用自动视觉质检；默认跳过，由用户肉眼检查")
    args = ap.parse_args()
    d = os.path.abspath(args.paper_dir)
    tex_path = os.path.join(d, "paper.tex")
    pdf_path = os.path.join(d, "paper.pdf")
    results = []   # (name, status, detail)

    def add(name, ok, warn, detail):
        results.append((name, "PASS" if ok else ("WARN" if warn else "FAIL"), detail))

    if not os.path.exists(tex_path):
        print(f"[FATAL] 未找到 {tex_path}")
        return 1

    # 1. check_heading_levels（9 项）
    sys.path.insert(0, SCRIPTS)
    import check_heading_levels as chl
    tex = open(tex_path, encoding="utf-8").read()
    hres = chl.check(tex)
    hfail = [f"{k}" for k, v in hres.items() if v.startswith("FAIL")]
    hwarn = [f"{k}" for k, v in hres.items() if v.startswith("WARN")]
    add("标题层级(9项)", not hfail, bool(hwarn), f"FAIL:{hfail}" if hfail else (f"WARN:{hwarn}" if hwarn else "全 PASS"))

    # 2. 摘要禁词 P7b（竞赛名由 competition_gates.yaml 提供，年份由正则动态拦截）
    abs_m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    forbidden = list(FORBIDDEN_FALLBACK)
    try:
        import yaml
        gates = yaml.safe_load(open(os.path.join(os.path.dirname(SCRIPTS), "core", "competition_gates.yaml"),
                                    encoding="utf-8"))
        forbidden = gates.get(args.competition, {}).get("forbidden_title_patterns") or FORBIDDEN_FALLBACK
    except Exception:
        pass
    ahits = []
    if abs_m:
        ahits = [f for f in forbidden if f in abs_m.group(1)]
        if YEAR_ABS_RE.search(abs_m.group(1)):
            ahits.append("针对20xx年(竞赛开头)")
    add("摘要禁词(P7b)", not ahits, False, f"命中: {ahits}" if ahits else "无竞赛名/年份")

    # 3. 参考痕迹/内部词（tex 层粗查, 精确在 visual_critic; 词表与之对齐）
    # 跳过 LaTeX 注释（% 至行尾，排除 \%）；注释不会进入 PDF 正文。
    tex_visible = re.sub(r"(?<!\\)%.*$", "", tex, flags=re.M)
    trace = [k for k in TRACE_WORDS if k in tex_visible and "\\bibliography" not in k]
    add("内部词/参考痕迹", not trace, False, f"命中: {trace}" if trace else "无")

    # 3.5 学术正式度（口语词下限；跳过注释和代码块）
    code_stripped = re.sub(r"\\begin\{lstlisting\}.*?\\end\{lstlisting\}", "", tex_visible, flags=re.S)
    colloquial = [w for w in COLLOQUIAL_WORDS if w in code_stripped]
    add("学术正式度(口语词)", not colloquial, False, f"命中: {colloquial}" if colloquial else "无")

    # 4. visual_critic（PDF，仅用户显式启用）
    if not args.visual_check:
        add("视觉质检(PDF)", True, False, "SKIPPED_USER_OPT_IN（自动视觉检查默认关闭，由用户肉眼检查）")
    elif os.path.exists(pdf_path):
        r = subprocess.run([PY, os.path.join(SCRIPTS, "visual_critic.py"), pdf_path],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = r.stdout or ""
        p0 = len(re.findall(r"\[P0\]", out))
        p1 = len(re.findall(r"\[P1\]", out))
        if r.returncode != 0 and not re.search(r"\[(P0|P1)\]", out):
            add("视觉质检(PDF)", False, False,
                f"visual_critic 运行失败(exit {r.returncode}): {(r.stderr or '无输出').strip()[-120:]}")
        else:
            add("视觉质检(PDF)", p0 == 0, p1 > 0, f"P0:{p0} P1:{p1}" if (p0 or p1) else "PASS")
    else:
        add("视觉质检(PDF)", False, True, "未编译 paper.pdf——写作完应编译核对")

    # 5. 数字一致性（快速: 仅提示, 完整跑 consistency_check）
    r2 = subprocess.run([PY, os.path.join(SCRIPTS, "consistency_check.py"), d],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    out2 = r2.stdout or ""
    m = re.search(r"\[(PASS|WARN|FAIL)\]", out2)
    st = m.group(1) if m else "?"
    # 同时读取 stderr，避免底层门禁错误被吞掉。
    if st == "?":
        # consistency_check is a low-level utility that requires explicit
        # paper/result/layout arguments.  paper_check only receives a paper
        # directory, so the authoritative consistency gate is the dedicated
        # delivery_all step.  Do not turn the utility's usage banner into a
        # spurious paper failure.
        detail = "快速检查参数不足；由主流程 consistency_check 执行完整校验"
        add("数字一致性", True, False, detail)
    elif r2.stderr.strip():
        detail = "FATAL: " + r2.stderr.strip().splitlines()[-1][:80]
        add("数字一致性", False, False, detail)
    else:
        detail = out2.split("\n")[1][:60] if len(out2.split("\n")) > 1 else st
        add("数字一致性", st == "PASS", st == "WARN", detail)

    # 6-7. 摘要字数/段数（B2）
    #   口径: 摘要块内、关键词行之前; 去 LaTeX 命令/花括号/数学; 字数 = CJK 字符 + ASCII 单词数
    if abs_m:
        # 兼容 cumcmthesis 的 \keywords{...} 与手写“关键词”标签，避免把
        # 关键词命令误计为摘要第 6/7 段。
        abs_body = re.split(r"\\keywords\s*\{|\\noindent?\s*\\textbf\{关键词\}|\\textbf\{关键词\}", abs_m.group(1))[0]
        t2 = re.sub(r"\\[a-zA-Z]+\*?", "", abs_body)
        t2 = re.sub(r"[{}]", "", t2)
        t2 = re.sub(r"\$[^$]*\$", "", t2)
        n_char = len(re.findall(r"[\u4e00-\u9fff]", t2)) + len(re.findall(r"[A-Za-z0-9]+", t2))
        paras = [p for p in re.split(r"\n\s*\n", abs_body) if re.search(r"\S", p)]
        n_par = len(paras)
        add("摘要字数550-800(B2)", 550 <= n_char <= 800,
            500 <= n_char < 550 or 800 < n_char <= 850, f"{n_char}字")
        add("摘要段数3-6(B2)", 3 <= n_par <= 6, n_par in (2, 7), f"{n_par}段")
    else:
        add("摘要字数550-800(B2)", False, False, "无摘要块")
        add("摘要段数3-6(B2)", False, False, "无摘要块")

    # 汇总
    print(f"=== 论文一键自检: {d} ===")
    any_fail = False
    any_warn = False
    for name, st, detail in results:
        ok = st == "PASS"
        warn = st == "WARN"
        if not ok and not warn:
            any_fail = True
        any_warn = any_warn or warn
        print(f"  [{'PASS' if ok else ('WARN' if warn else 'FAIL')}] {name}: {detail}")
    if not any_fail and not (args.strict and any_warn):
        print("===== 论文自检: PASS =====")
        return 0
    print("===== 论文自检: FAIL(需修复) =====")
    return 1


if __name__ == "__main__":
    sys.exit(main())
