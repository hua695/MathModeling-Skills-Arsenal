#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_heading_levels.py — 标题层级规范检查（2026-08，防"老问题复发"）

国赛标题层级规范（用户明确，多次论文踩坑）:
  一级: 一、二、三…（中文数字+顿号，四号黑体）    二级: 1.1 1.2…（小四黑体）
  三级: 1.1.1…（小四黑体）                         四级: 尽量不开
规则: 优先三级够用 / 不跳级 / 同一级至少 2 个 / 标题后不加句号

检查（对 paper.tex）:
  1. 一级中文编号: ctexset 是否配置 \\chinese{section} + name 含顿号（无 → FAIL）
  2. 无跳级: section 后直接 subsubsection（跳过 subsection）→ FAIL
  3. 同级≥2: 有子级的 section 下 subsection 数 < 2 → WARN
  4. 无四级: 使用 \\subparagraph/\\paragraph 作标题 → FAIL
  5. 标题无句号: 标题文本以 。/. 结尾 → WARN
  6. 附录编号: \\appendix 后恢复 \\Alph（"附录A"）→ 未恢复 WARN

用法: python scripts/check_heading_levels.py <paper.tex 或 论文目录>
"""
from __future__ import annotations

import os
import re
import sys

HEADINGS = re.compile(r"\\(subsubsection|subsection|section)\{([^}]+)\}")


def parse_headings(tex: str) -> list[tuple[int, str, str]]:
    """返回 [(层级, 标题文本, 行号)]。层级: section=1, subsection=2, subsubsection=3。"""
    out = []
    for i, line in enumerate(tex.split("\n"), 1):
        m = HEADINGS.search(line)
        if m:
            lv = {"section": 1, "subsection": 2, "subsubsection": 3}[m.group(1)]
            out.append((lv, m.group(2), i))
    return out


def check(tex: str) -> dict[str, str]:
    r = {}
    headings = parse_headings(tex)
    body = tex.split("\\appendix", 1)[0]

    # 1. 一级中文编号配置
    has_chinese = "\\chinese{section}" in tex
    has_dun = re.search(r"name\s*=\s*\{[^}]*、", tex) is not None
    r["1 一级中文编号(一、)"] = ("PASS(ctexset: \\chinese{section}+顿号)" if (has_chinese and has_dun)
                              else "FAIL(未配置一级中文编号——需 ctexset section={name={,、}, number=\\chinese{section}}，当前显示阿拉伯 1/2/3)")

    # 2. 无跳级: 检查 body 中 section 的直接子级序列
    jumps = []
    prev_lv = 0
    for lv, title, ln in headings:
        if lv > prev_lv + 1:
            jumps.append((ln, title, lv, prev_lv))
        prev_lv = lv
    r["2 不跳级"] = "PASS" if not jumps else f"FAIL(跳级: {[f'L{ln} {t}(层级{lv}, 前一层{pl})' for ln, t, lv, pl in jumps][:3]})"

    # 3. 同级≥2: 每个有直接子级的 section，其 subsection 数
    singles = []
    i = 0
    while i < len(headings):
        lv, title, ln = headings[i]
        if lv == 1:
            j = i + 1
            n_sub = 0
            while j < len(headings) and headings[j][0] > 1:
                if headings[j][0] == 2:
                    n_sub += 1
                j += 1
            if j > i + 1 and n_sub < 2:   # 有子级但 subsection < 2
                singles.append((ln, title, n_sub))
            i = j
        else:
            i += 1
    r["3 同级≥2"] = "PASS" if not singles else f"WARN(单子级: {[f'L{ln} {t} 仅 {n} 个二级' for ln, t, n in singles][:3]}——同一级至少 2 个)"

    # 4. 无四级
    has_l4 = bool(re.search(r"\\(subparagraph|paragraph)\{", tex))
    r["4 无四级标题"] = "PASS" if not has_l4 else "FAIL(使用四级标题 \\paragraph/\\subparagraph——四级层级繁杂, 评委观感差)"

    # 5. 标题无句号
    dots = [f"L{ln} {t}" for lv, t, ln in headings if t.rstrip().endswith(("。", "."))]
    r["5 标题不加句号"] = "PASS" if not dots else f"WARN(标题以句号结尾: {dots[:3]})"

    # 6. 附录编号恢复
    if "\\appendix" in tex:
        after_app = tex.split("\\appendix", 1)[1][:200]
        has_alph = "\\Alph{section}" in after_app
        r["6 附录编号(附录A)"] = "PASS" if has_alph else "WARN(\\appendix 后未恢复 \\Alph{section}——附录可能显示为数字/中文续编, 应显示\"附录A\")"
    else:
        r["6 附录编号(附录A)"] = "PASS(无附录)"

    # 7. 一级标题固定八章（2026-08 用户硬性: 一~八 章节固定; 各问不得占一级标题）
    ALLOWED_TOP = ["问题重述", "问题分析", "模型假设", "符号说明", "数据预处理", "特征工程", "模型建立与求解",
                   "模型建立", "模型求解", "模型检验", "灵敏度", "模型评价", "结论"]
    app_pos = tex.find("\\appendix")
    app_line = tex[:app_pos].count("\n") + 1 if app_pos >= 0 else 10 ** 9   # 附录起始行号
    bad_top = []
    for lv, title, ln in headings:
        if lv == 1 and ln < app_line:
            ok = any(k in title for k in ALLOWED_TOP)
            is_problem = bool(re.match(r"^(问题[一二三四五六七八九十]|问题\d)", title))
            if not ok or is_problem:
                bad_top.append((ln, title))
    if bad_top:
        r["7 一级标题八章"] = (f"FAIL(正文一级标题不在八章集合或为'问题X': "
                            f"{[f'L{ln} {t}' for ln, t in bad_top][:4]}——"
                            f"一级只能是 问题重述/问题分析/模型假设/符号说明/模型建立与求解/"
                            f"模型检验/模型评价/结论; 各问并入第五章作二级标题)")
    else:
        r["7 一级标题八章"] = "PASS(正文一级标题均为八章规范章节)"

    # 8. 图解读（2026-08 用户硬性: 每图配"由图可知+数值+解释"; 连续图无解读 = 注水）
    figs = list(re.finditer(r"\\begin\{figure\}.*?\\end\{figure\}", tex, re.S))
    no_interp = []
    for i, m in enumerate(figs):
        cap = re.search(r"\\caption\{([^}]+)\}", m.group(0))
        cap_t = cap.group(1)[:22] if cap else "?"
        after = tex[m.end():m.end() + 300]
        if i < len(figs) - 1:
            gap = tex[m.end():figs[i + 1].start()]
        else:
            gap = tex[m.end():m.end() + 300]
        has_zh = bool(re.search(r"[\u4e00-\u9fff]", gap))
        if not has_zh:
            no_interp.append(cap_t)
    if no_interp:
        r["8 图配解读"] = (f"FAIL({len(no_interp)} 张图后无中文解读(连续图): {no_interp[:4]}——"
                        f"用户硬性'有图必有文字': 每图须配'由图可知+数值+解释'(C5), 禁止连续图片无文字描述)")
    else:
        r["8 图配解读"] = "PASS(每张图后均有中文解读)"

    # 9. 关键词存在。文献与附录是否另起页由 PDF 视觉门禁判断，避免强制分页制造留白。
    # cumcmthesis 的 \keywords{...} 宏负责模板样式；不应把关键词词条或摘要术语
    # 强制加粗。加粗会破坏模板一致性，也不能作为论文质量信号。
    issues9 = []
    # 9a. 识别手写关键词行或 cumcmthesis 的 \keywords 宏。
    kw_line = None
    # Build the label from code points rather than embedding Chinese literals.
    # This keeps the check stable when Windows launches the script under a
    # legacy code page while the TeX file itself is UTF-8.
    keyword_label = "".join(chr(c) for c in (0x5173, 0x952e, 0x8bcd))
    keyword_colon = chr(0xFF1A)
    keyword_pattern = (r"\\textbf\{" + re.escape(keyword_label) + r"\}"
                       + re.escape(keyword_colon) + r"([^\n]+)")
    m = re.search(keyword_pattern, tex)
    if m:
        kw_line = m.group(1)
    else:
        macro_match = re.search(r"\\keywords\{([^\n]+)\}", tex)
        if macro_match:
            kw_line = macro_match.group(1)
    if kw_line:
        raw_terms = [t.strip() for t in re.split(r"[、；;]|\\quad", kw_line) if t.strip()]
        if not raw_terms:
            issues9.append("关键词为空")
    else:
        issues9.append("未找到 \\textbf{关键词} 行或 \\keywords{...} 宏")
    # 文献和附录均可自然接续，避免孤立的末页。实际版面由 PDF 空白页/留白门禁审计。
    r["9 关键词/分页"] = "PASS" if not issues9 else "FAIL(" + "; ".join(issues9[:3]) + ")"

    return r


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else "paper.tex"
    path = arg if os.path.isfile(arg) else os.path.join(arg, "paper.tex")
    if not os.path.exists(path):
        print(f"[FATAL] 未找到 {path}")
        return 1
    tex = open(path, encoding="utf-8").read()
    results = check(tex)
    all_ok = True
    has_warn = False
    print(f"=== 标题层级检查: {path} ===")
    for k, v in results.items():
        ok = v.startswith("PASS")
        warn = v.startswith("WARN")
        if not ok and not warn:
            all_ok = False
        has_warn = has_warn or warn
        print(f"  [{'PASS' if ok else ('WARN' if warn else 'FAIL')}] {k}: {v}")
    if not all_ok:
        print("===== 标题层级: FAIL(需修正) =====")
    elif has_warn:
        print("===== 标题层级: PASS(含 WARN, 人工确认) =====")
    else:
        print("===== 标题层级: PASS =====")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
