#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Block internal delivery/index text from entering a contest paper."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DEFAULT_BANNED = ("数学建模竞赛论文", "参考文献索引", "交付索引", "references.yaml",
                  "paper/ref.bib", "交付报告", "delivery_all_report")


def scan(root: Path, extra: list[str] | None = None) -> dict:
    files = [root] if root.is_file() else sorted(root.rglob("*.tex"))
    banned = tuple(dict.fromkeys(DEFAULT_BANNED + tuple(extra or [])))
    hits = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for phrase in banned:
            if phrase in text:
                hits.append({"file": str(path), "phrase": phrase})
    return {"schema_version": "1.0", "passed": not hits,
            "gate_status": "BLOCK" if hits else "PASS", "banned": list(banned), "hits": hits,
            "scanned_files": [str(path) for path in files]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper")
    parser.add_argument("--pdf", default=None, help="保留接口；PDF 文本扫描由 pdf 版面门禁负责")
    parser.add_argument("--banned", action="append", default=[])
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    try:
        report = scan(Path(args.paper).resolve(), args.banned)
    except Exception as exc:
        report = {"schema_version": "1.0", "passed": False, "gate_status": "BLOCK", "hits": [{"error": str(exc)}]}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out = Path(args.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
