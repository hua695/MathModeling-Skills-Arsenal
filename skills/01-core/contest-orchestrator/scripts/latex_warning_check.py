#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classify LaTeX overfull boxes by body/appendix severity."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

OVERFULL = re.compile(
    r"Overfull \\hbox \((?P<width>[-0-9.]+)pt too wide\)[^\n]*"
    r"(?:lines? (?P<start>\d+)(?:--(?P<end>\d+))?|detected at line (?P<detected>\d+))",
    re.MULTILINE,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--body-threshold", type=float, default=2.0)
    parser.add_argument("--appendix-threshold", type=float, default=10.0)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    tex = workspace / "paper.tex"
    log = workspace / "paper.log"
    report = {"workspace": str(workspace), "passed": False, "body": [], "appendix": [], "warnings": []}
    if not tex.exists() or not log.exists():
        report["warnings"].append("缺少 paper.tex 或 paper.log")
    else:
        lines = tex.read_text(encoding="utf-8", errors="replace").splitlines()
        appendix_line = next((i + 1 for i, line in enumerate(lines)
                              if "\\appendix" in line or "附录" in line or "支撑材料文件列表" in line), len(lines) + 1)
        for match in OVERFULL.finditer(log.read_text(encoding="utf-8", errors="replace")):
            width = abs(float(match.group("width")))
            start = int(match.group("start") or match.group("detected"))
            end = match.group("end") or str(start)
            item = {"width_pt": width, "lines": f"{start}-{end}",
                    "threshold_pt": args.appendix_threshold if start >= appendix_line else args.body_threshold}
            target = report["appendix"] if start >= appendix_line else report["body"]
            if width > item["threshold_pt"]:
                target.append(item)
        report["passed"] = not report["body"]
    out = args.json_out.resolve() if args.json_out else workspace / "latex_warning_report.json"
    if workspace.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
