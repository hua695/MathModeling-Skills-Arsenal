#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check appendix scope, order, code mapping and no-code declaration."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def locate_tex(path: Path) -> Path:
    if path.is_file():
        return path
    candidates = sorted(path.glob("paper*.tex")) or sorted(path.glob("*.tex"))
    if not candidates:
        raise FileNotFoundError(f"未找到 TeX 文件: {path}")
    return candidates[0]


def check(text: str, paper_dir: Path | None = None) -> dict:
    appendix = re.search(r"\\appendix", text, re.I)
    if not appendix:
        has_code = bool(re.search(r"lst(input)?listing|minted|\\begin\{verbatim\}", text, re.I))
        issues = ["存在代码内容但未找到 \\appendix"] if has_code else []
        return {"schema_version": "1.0", "passed": not issues, "issues": issues,
                "warnings": ["未发现附录；如论文无程序，正式附录规则由竞赛 profile 决定"]}
    tail = text[appendix.end():]
    issues: list[str] = []
    warnings: list[str] = []
    has_code = bool(re.search(r"lst(input)?listing|minted|\\begin\{verbatim\}", tail, re.I))
    no_code = bool(re.search(r"本论文没有用到程序|未使用程序|未进行程序求解", tail))
    if not has_code and not no_code:
        issues.append("附录无代码时缺少明确无代码声明")
    forbidden = re.findall(r"核心结论|主要结论|模型建立与求解|结论与建议", tail)
    if forbidden:
        warnings.append("附录标题或正文疑似包含正文核心内容: " + "、".join(sorted(set(forbidden))))
    order_terms = ["材料", "推导", "代码", "源代码", "数据表", "原始数据"]
    positions = {term: (tail.find(term) if tail.find(term) >= 0 else None) for term in order_terms}
    ordered = [p for p in positions.values() if p is not None]
    if ordered and ordered != sorted(ordered):
        warnings.append("附录材料/推导/代码/原始数据顺序可能不符合默认顺序")
    listings = re.findall(r"\\lstinputlisting(?:\[[^]]*\])?\{([^}]+)\}", tail)
    missing_sources = []
    if paper_dir:
        for rel in listings:
            candidate = (paper_dir / rel).resolve()
            if not candidate.exists():
                missing_sources.append(rel)
    if missing_sources:
        issues.append("附录引用的源代码文件不存在: " + ", ".join(missing_sources))
    return {"schema_version": "1.0", "passed": not issues, "issues": issues,
            "warnings": warnings, "has_appendix": True, "has_code": has_code,
            "no_code_statement": no_code, "source_listings": listings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", help="paper directory or TeX file")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    path = Path(args.paper).resolve()
    try:
        tex = locate_tex(path)
        report = check(tex.read_text(encoding="utf-8", errors="replace"), tex.parent)
        report["tex"] = str(tex)
    except Exception as exc:
        report = {"schema_version": "1.0", "passed": False, "issues": [str(exc)], "warnings": []}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).resolve().write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
