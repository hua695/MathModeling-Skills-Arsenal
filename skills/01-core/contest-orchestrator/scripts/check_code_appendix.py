#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check source-code appendix formatting and reproducibility markers."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEBUG_RE = re.compile(r"\b(?:pdb\.set_trace|breakpoint\s*\(|DEBUG_ONLY|TODO\s*:\s*remove)\b", re.I)


def locate_tex(path: Path) -> Path:
    if path.is_file():
        return path
    candidates = sorted(path.glob("paper*.tex")) or sorted(path.glob("*.tex"))
    if not candidates:
        raise FileNotFoundError(f"未找到 TeX 文件: {path}")
    return candidates[0]


def check(tex: str, paper_dir: Path) -> dict:
    code = bool(re.search(r"lst(input)?listing|minted|\\begin\{verbatim\}", tex, re.I))
    if not code:
        return {"schema_version": "1.0", "passed": True, "issues": [],
                "warnings": ["未发现代码块，按无代码附录规则检查声明"], "code_blocks": 0}
    issues: list[str] = []
    warnings: list[str] = []
    if not re.search(r"backgroundcolor|fill=gray|bgcolor|\bgray!", tex, re.I):
        issues.append("代码块未发现浅灰背景配置")
    if not re.search(r"frame\s*=\s*(single|lines)|tcolorbox|border", tex, re.I):
        issues.append("代码块未发现边框配置")
    if not re.search(r"numbers\s*=\s*left|linenos|line_numbers", tex, re.I):
        warnings.append("代码块未发现左侧行号配置")
    if not re.search(r"footnotesize|scriptsize", tex, re.I):
        warnings.append("代码块未发现 footnotesize/scriptsize")
    listings = re.findall(r"\\lstinputlisting(?:\[[^]]*\])?\{([^}]+)\}", tex)
    source_reports = []
    for rel in listings:
        source = (paper_dir / rel).resolve()
        item = {"source": rel, "exists": source.exists()}
        if not source.exists():
            issues.append(f"源代码不存在: {rel}")
        else:
            content = source.read_text(encoding="utf-8", errors="replace")
            head = "\n".join(content.splitlines()[:35])
            item["header_comment"] = bool(re.search(r"功能|输入|输出|对应正文|对应模型|purpose|input|output", head, re.I))
            item["debug_markers"] = DEBUG_RE.findall(content)
            item["tabs"] = "\t" in content
            if not item["header_comment"]:
                issues.append(f"源代码缺少功能/输入/输出/正文映射注释: {rel}")
            if item["debug_markers"]:
                issues.append(f"源代码包含调试标记: {rel}")
            if item["tabs"]:
                warnings.append(f"源代码包含 Tab 缩进，建议统一为 4 空格: {rel}")
        source_reports.append(item)
    return {"schema_version": "1.0", "passed": not issues, "issues": issues,
            "warnings": warnings, "code_blocks": len(listings) or 1,
            "source_reports": source_reports}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", help="paper directory or TeX file")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    path = Path(args.paper).resolve()
    try:
        tex_path = locate_tex(path)
        report = check(tex_path.read_text(encoding="utf-8", errors="replace"), tex_path.parent)
        report["tex"] = str(tex_path)
    except Exception as exc:
        report = {"schema_version": "1.0", "passed": False, "issues": [str(exc)], "warnings": []}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).resolve().write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
