#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detect changed inputs/code or broken source links in run evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_one(root: Path, path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    stale: list[str] = []
    known: set[str] = set()
    all_artifacts = []
    for group in ("inputs", "code", "configs", "outputs"):
        for item in payload.get(group, []):
            all_artifacts.append(item)
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str):
                known.add(item["evidence_id"])
            if not isinstance(item, dict):
                stale.append(f"{group}: 非对象记录")
                continue
            try:
                target = (root / Path(str(item.get("path", "")))).resolve()
                target.relative_to(root)
            except (ValueError, OSError):
                stale.append(f"{group}:{item.get('path')} 位于项目根目录外")
                continue
            if not target.is_file():
                stale.append(f"{group}:{item.get('path')} 不存在")
            elif item.get("sha256") != sha256(target):
                stale.append(f"{group}:{item.get('path')} 哈希变化")
    for item in payload.get("evidence", []):
        if not isinstance(item, dict):
            stale.append("evidence 非对象记录")
            continue
        missing = [value for value in item.get("source_ids", []) if value not in known]
        if missing:
            stale.append(f"{item.get('evidence_id')} 来源不存在: {missing}")
    if payload.get("status") != "completed" or payload.get("exit_code") != 0:
        stale.append(f"run 未成功完成: status={payload.get('status')} exit_code={payload.get('exit_code')}")
    return {"run_id": payload.get("run_id"), "manifest": path.relative_to(root).as_posix(),
            "status": "STALE" if stale else "FRESH", "reasons": stale,
            "output_count": len(payload.get("outputs", []))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve()
    manifests = sorted((root / ".contest" / "runs").glob("*/run_manifest.json"))
    reports: list[dict] = []
    errors: list[str] = []
    warnings: list[str] = []
    if not manifests:
        (errors if args.strict else warnings).append("未发现运行清单，无法进行过期传播检查")
    for path in manifests:
        try:
            report = check_one(root, path)
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            report = {"manifest": path.relative_to(root).as_posix(), "status": "FAIL", "reasons": [str(exc)]}
        reports.append(report)
        if report.get("status") in {"STALE", "FAIL"}:
            errors.extend(f"{report['manifest']}: {reason}" for reason in report.get("reasons", []))
    payload = {"schema_version": "1.0", "checked_at": datetime.now(timezone.utc).isoformat(),
               "project_root": str(root), "reports": reports, "issues": errors,
               "warnings": warnings, "passed": not errors}
    out = args.out.resolve() if args.out else root / ".contest" / "stale_evidence_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
