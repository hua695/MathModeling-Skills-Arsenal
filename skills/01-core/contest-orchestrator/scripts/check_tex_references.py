#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check LaTeX label/reference integrity before relying on compiler output."""
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


def expand_inputs(text: str, base: Path, seen: set[Path] | None = None) -> str:
    seen = set() if seen is None else seen
    pattern = re.compile(r"\\(?:input|include)\{([^{}]+)\}")

    def replace(match: re.Match[str]) -> str:
        candidate = base / match.group(1).strip()
        if not candidate.suffix:
            candidate = candidate.with_suffix(".tex")
        candidate = candidate.resolve()
        if candidate in seen or not candidate.is_file():
            return match.group(0)
        seen.add(candidate)
        return expand_inputs(candidate.read_text(encoding="utf-8", errors="replace"), candidate.parent, seen)

    return pattern.sub(replace, text)


def check(text: str) -> dict:
    source = re.sub(r"(?m)^\s*%.*$", "", text)
    labels: dict[str, int] = {}
    duplicates: list[str] = []
    for match in re.finditer(r"\\label\{([^{}]+)\}", source):
        key = match.group(1).strip()
        line = source.count("\n", 0, match.start()) + 1
        if key in labels:
            duplicates.append(key)
        labels.setdefault(key, line)

    referenced: set[str] = set()
    for match in re.finditer(r"\\(?:ref|eqref|pageref|autoref|cref|Cref)\{([^{}]+)\}", source):
        referenced.update(item.strip() for item in match.group(1).split(",") if item.strip())
    missing = sorted(item for item in referenced if item not in labels)
    issues = []
    if duplicates:
        issues.append({"kind": "duplicate_label", "labels": sorted(set(duplicates)),
                       "message": "同一标签被定义多次，交叉引用可能漂移。"})
    if missing:
        issues.append({"kind": "missing_label", "labels": missing,
                       "message": "正文引用了未定义的 label；必须修复源文件后再交付。"})
    return {"schema_version": "1.0", "passed": not issues,
            "gate_status": "BLOCK" if issues else "PASS", "issues": issues,
            "defined_labels": len(labels), "referenced_labels": len(referenced),
            "unused_labels": sorted(set(labels) - referenced)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    try:
        tex = locate_tex(Path(args.paper).resolve())
        report = check(expand_inputs(tex.read_text(encoding="utf-8", errors="replace"), tex.parent))
        report["tex"] = str(tex)
    except Exception as exc:
        report = {"schema_version": "1.0", "passed": False, "gate_status": "BLOCK",
                  "issues": [{"kind": "runtime", "message": str(exc)}]}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        output = Path(args.out).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
