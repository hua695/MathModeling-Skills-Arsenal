#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan paper sources and optional PDF text/metadata for identity leakage."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PATTERNS = {
    "identity_label": re.compile(r"(?:姓名|学号|指导教师|指导老师|手机号|联系电话|电子邮箱)\s*[:：]", re.I),
    "school_label": re.compile(r"(?:学校|学院|参赛队伍|队伍名称)\s*[:：]", re.I),
    "internal_delivery": re.compile(r"参考文献索引|交付索引|交付前核对清单|正文参考文献数据库", re.I),
    "forbidden_title": re.compile(r"数学建模竞赛论文|全国大学生数学建模竞赛组委会|全国大学生数学建模竞赛", re.I),
}


def files_to_scan(root: Path) -> list[Path]:
    suffixes = {".tex", ".bib", ".md", ".txt", ".py", ".yaml", ".yml", ".json"}
    return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in suffixes]


def check(root: Path, pdf: Path | None = None) -> dict:
    hits = []
    for path in files_to_scan(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for kind, pattern in PATTERNS.items():
            match = pattern.search(text)
            if match:
                hits.append({"kind": kind, "path": str(path), "line": text.count("\n", 0, match.start()) + 1,
                             "text": match.group(0)})
    if pdf and pdf.exists():
        try:
            import pypdf
            reader = pypdf.PdfReader(str(pdf))
            metadata = reader.metadata or {}
            for key, value in metadata.items():
                for kind, pattern in PATTERNS.items():
                    if pattern.search(str(value)):
                        hits.append({"kind": f"pdf_metadata:{kind}", "path": str(pdf), "field": str(key),
                                     "text": str(value)[:200]})
        except Exception:
            pass
    return {"schema_version": "1.0", "passed": not hits, "issues": hits,
            "scanned_files": len(files_to_scan(root))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", help="paper directory")
    parser.add_argument("--pdf", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.paper).resolve()
    try:
        report = check(root, Path(args.pdf).resolve() if args.pdf else None)
    except Exception as exc:
        report = {"schema_version": "1.0", "passed": False, "issues": [str(exc)]}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).resolve().write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
