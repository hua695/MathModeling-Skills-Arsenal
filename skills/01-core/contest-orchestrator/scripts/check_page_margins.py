#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check the minimum page margins required by the Guosai profile.

The check is deliberately source-based: a PDF content bounding box cannot
reliably distinguish a real page margin from a short paragraph or a floating
object.  TeX projects should declare the effective geometry explicitly.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


MIN_CM = 2.5
UNIT_TO_CM = {"cm": 1.0, "mm": 0.1, "in": 2.54, "pt": 2.54 / 72.27, "bp": 2.54 / 72.0}
SIDES = ("top", "bottom", "left", "right")


def parse_length(raw: str) -> float | None:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|in|pt|bp)\s*", raw, re.I)
    if not match:
        return None
    return float(match.group(1)) * UNIT_TO_CM[match.group(2).lower()]


def extract_geometry(text: str) -> tuple[dict[str, float], list[str]]:
    declarations: list[str] = []
    margins: dict[str, float] = {}
    patterns = [
        r"\\geometry\s*\{([^}]*)\}",
        r"\\usepackage\s*\[([^]]*)\]\s*\{geometry\}",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.I | re.S):
            raw = match.group(1)
            declarations.append(raw.strip())
            options = [item.strip() for item in raw.split(",") if item.strip()]
            for option in options:
                if "=" not in option:
                    continue
                key, value = (part.strip().lower() for part in option.split("=", 1))
                parsed = parse_length(value)
                if parsed is None:
                    continue
                if key == "margin":
                    for side in SIDES:
                        margins[side] = parsed
                elif key in SIDES:
                    margins[key] = parsed
                elif key in {"hmargin", "vmargin"}:
                    targets = ("left", "right") if key == "hmargin" else ("top", "bottom")
                    for side in targets:
                        margins[side] = parsed
    return margins, declarations


def check(paper_dir: Path, competition: str = "guosai", minimum_cm: float = MIN_CM) -> dict:
    report = {
        "schema_version": "1.0",
        "competition": competition,
        "minimum_cm": minimum_cm,
        "paper_dir": str(paper_dir.resolve()),
        "status": "BLOCK",
        "files": [],
        "margins_cm": {},
        "declarations": [],
        "issues": [],
    }
    if competition != "guosai":
        report["status"] = "INFO"
        report["issues"] = ["非国赛 profile 不继承国赛 2.5 cm 页边距门禁"]
        return report
    tex_files = sorted(paper_dir.rglob("*.tex")) if paper_dir.is_dir() else []
    report["files"] = [str(path.relative_to(paper_dir)) for path in tex_files]
    margins: dict[str, float] = {}
    for path in tex_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        found, declarations = extract_geometry(text)
        margins.update(found)  # later declarations are effective in TeX
        report["declarations"].extend({"file": str(path.relative_to(paper_dir)), "value": item}
                                      for item in declarations)
    report["margins_cm"] = {side: round(margins[side], 4) for side in SIDES if side in margins}
    missing = [side for side in SIDES if side not in margins]
    undersized = [side for side in SIDES if side in margins and margins[side] < minimum_cm - 1e-9]
    if not tex_files:
        report["issues"].append("论文目录中未找到 TeX 源文件，无法证明页边距")
    if missing:
        report["issues"].append("未明确声明页边距: " + ", ".join(missing))
    if undersized:
        report["issues"].append(
            "页边距小于 {:.2f} cm: {}".format(
                minimum_cm, ", ".join(f"{side}={margins[side]:.3f} cm" for side in undersized)
            )
        )
    if not report["issues"]:
        report["status"] = "PASS"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper_dir")
    parser.add_argument("--competition", default="guosai", choices=("guosai", "huashu", "mcm_icm"))
    parser.add_argument("--min-cm", type=float, default=MIN_CM)
    parser.add_argument("--out", default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = check(Path(args.paper_dir), args.competition, args.min_cm)
    if report["status"] == "BLOCK" and not args.strict:
        report["status"] = "WARN"
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"PASS", "INFO", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
