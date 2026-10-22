#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check an existing formal-delivery folder against the current compiled PDF."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def check(root: Path, pdf: Path, formal_dir: Path | None = None, strict: bool = False) -> dict:
    formal = (formal_dir or (root / "05_输出与交付" / "正式交付")).resolve()
    if not formal.is_dir():
        return {"schema_version": "1.0", "applicable": False, "passed": True,
                "gate_status": "PASS", "issues": [], "warnings": [], "formal_dir": str(formal)}
    issues: list[str] = []
    warnings: list[str] = []
    if not pdf.is_file():
        issues.append(f"当前编译 PDF 不存在: {pdf}")
    else:
        current_hash = sha256(pdf)
        candidates = [path for path in formal.glob("*.pdf")
                      if any(token in path.stem.lower() for token in ("正式版", "final", "submission"))]
        for candidate in candidates:
            if sha256(candidate) != current_hash:
                issues.append(f"正式交付 PDF 与当前编译 PDF 不一致: {candidate.name}")
        index = formal / "FINAL_INDEX.md"
        if index.is_file() and current_hash not in index.read_text(encoding="utf-8", errors="replace").upper():
            issues.append("FINAL_INDEX.md 未登记当前编译 PDF 的 SHA-256")
    if issues and not strict:
        warnings.extend(issues)
        issues = []
    return {"schema_version": "1.0", "applicable": True, "passed": not issues,
            "gate_status": "BLOCK" if issues else ("WARN" if warnings else "PASS"),
            "issues": issues, "warnings": warnings, "formal_dir": str(formal)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--pdf", default=None)
    parser.add_argument("--formal-dir", default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    pdf = Path(args.pdf).resolve() if args.pdf else root / "03_文档" / "paper" / "paper.pdf"
    formal = Path(args.formal_dir).resolve() if args.formal_dir else None
    try:
        report = check(root, pdf, formal, args.strict)
    except Exception as exc:
        report = {"schema_version": "1.0", "applicable": True, "passed": False,
                  "gate_status": "BLOCK", "issues": [str(exc)], "warnings": []}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        output = Path(args.out).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
