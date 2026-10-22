#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize evidence state without pretending that warnings are verification."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def load(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--final", action="store_true", help="调用方已完成全部模型/论文/交付门禁")
    args = parser.parse_args()
    root = args.project_root.resolve()
    contest = root / ".contest"
    candidates = {
        "run_manifest": contest / "run_manifest_report.json",
        "stale_evidence": contest / "stale_evidence_report.json",
        "numeric_sources": contest / "numeric_source_report.json",
    }
    checks = []
    for name, path in candidates.items():
        report = load(path)
        if report is None:
            checks.append({"name": name, "status": "MISSING", "path": path.relative_to(root).as_posix()})
            continue
        checks.append({"name": name, "status": "PASS" if report.get("passed") else "FAIL",
                       "path": path.relative_to(root).as_posix()})
    statuses = {item["status"] for item in checks}
    if "FAIL" in statuses:
        status = "BLOCKED"
    elif statuses == {"PASS"}:
        status = "DELIVERY_READY" if args.final else "VERIFIED"
    elif "PASS" in statuses:
        status = "VALIDATED"
    else:
        status = "EXECUTED"
    payload = {"schema_version": "1.0", "checked_at": datetime.now(timezone.utc).isoformat(),
               "project_root": str(root), "status": status, "checks": checks,
               "passed": status in {"VERIFIED", "DELIVERY_READY"}}
    out = args.out.resolve() if args.out else contest / "readiness.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
