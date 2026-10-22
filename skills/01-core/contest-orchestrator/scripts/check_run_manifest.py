#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate project-relative run manifests and their evidence relationships."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

EVIDENCE_ID = re.compile(r"^ev:[A-Za-z0-9_.-]+$")
REQUIRED = ("schema_version", "run_id", "status", "command", "inputs", "outputs", "exit_code", "evidence")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_rel(root: Path, raw: object) -> Path:
    value = Path(str(raw))
    if value.is_absolute():
        raise ValueError(f"出现绝对路径: {raw}")
    resolved = (root / value).resolve()
    resolved.relative_to(root)
    return resolved


def artifact_issues(root: Path, item: object, ids: set[str], label: str) -> list[str]:
    issues: list[str] = []
    if not isinstance(item, dict):
        return [f"{label} 必须是对象"]
    path = item.get("path")
    evidence_id = item.get("evidence_id")
    if not isinstance(path, str):
        issues.append(f"{label}.path 缺失")
        return issues
    try:
        target = safe_rel(root, path)
    except (ValueError, OSError) as exc:
        issues.append(f"{label}: {exc}")
        return issues
    if not target.is_file():
        issues.append(f"{label} 文件不存在: {path}")
    elif item.get("sha256") != sha256(target):
        issues.append(f"{label} 哈希已变化: {path}")
    if not isinstance(evidence_id, str) or not EVIDENCE_ID.fullmatch(evidence_id):
        issues.append(f"{label} evidence_id 无效: {evidence_id}")
    elif evidence_id in ids:
        issues.append(f"evidence_id 重复: {evidence_id}")
    else:
        ids.add(evidence_id)
    source_ids = item.get("source_ids", [])
    if not isinstance(source_ids, list) or not all(isinstance(value, str) for value in source_ids):
        issues.append(f"{label}.source_ids 必须是字符串数组")
    return issues


def validate_manifest(root: Path, path: Path) -> dict:
    issues: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"path": path.relative_to(root).as_posix(), "status": "FAIL", "issues": [str(exc)]}
    if not isinstance(payload, dict):
        return {"path": path.relative_to(root).as_posix(), "status": "FAIL", "issues": ["根节点必须是对象"]}
    missing = [key for key in REQUIRED if key not in payload]
    issues.extend(f"缺少字段: {key}" for key in missing)
    if payload.get("schema_version") != "1.0":
        issues.append("schema_version 必须为 1.0")
    if payload.get("status") == "completed" and payload.get("exit_code") != 0:
        issues.append("completed run 的 exit_code 必须为 0")
    if payload.get("status") != "completed" and payload.get("exit_code") == 0:
        issues.append("failed/cancelled run 不能使用 exit_code=0")
    command = payload.get("command")
    if not isinstance(command, dict) or not isinstance(command.get("argv"), list) or not command.get("argv"):
        issues.append("command.argv 必须是非空数组")
    elif any(not isinstance(value, str) for value in command["argv"]):
        issues.append("command.argv 只能包含字符串")
    if isinstance(command, dict):
        try:
            safe_rel(root, command.get("cwd", "."))
        except (ValueError, OSError) as exc:
            issues.append(f"command.cwd: {exc}")
    ids: set[str] = set()
    artifact_ids: set[str] = set()
    for group in ("inputs", "code", "configs", "outputs"):
        values = payload.get(group, [])
        if not isinstance(values, list):
            issues.append(f"{group} 必须是数组")
            continue
        for index, item in enumerate(values):
            before = set(ids)
            issues.extend(artifact_issues(root, item, ids, f"{group}[{index}]"))
            artifact_ids.update(ids - before)
    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list):
        issues.append("evidence 必须是数组")
        evidence = []
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            issues.append(f"evidence[{index}] 必须是对象")
            continue
        evidence_id = item.get("evidence_id")
        if not isinstance(evidence_id, str) or not EVIDENCE_ID.fullmatch(evidence_id):
            issues.append(f"evidence[{index}] evidence_id 无效")
        elif evidence_id in ids:
            issues.append(f"evidence_id 重复: {evidence_id}")
        else:
            ids.add(evidence_id)
        source_ids = item.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            issues.append(f"evidence[{index}] 必须绑定 source_ids")
        else:
            unknown = [value for value in source_ids if value not in ids and value not in artifact_ids]
            if unknown:
                issues.append(f"evidence[{index}] 存在未知 source_ids: {unknown}")
    output_ids = {item.get("evidence_id") for item in payload.get("outputs", []) if isinstance(item, dict)}
    for index, item in enumerate(payload.get("outputs", []) if isinstance(payload.get("outputs"), list) else []):
        sources = item.get("source_ids", []) if isinstance(item, dict) else []
        if not sources:
            issues.append(f"outputs[{index}] 缺少 source_ids，无法证明结果来源")
        elif any(value not in ids and value not in artifact_ids for value in sources):
            issues.append(f"outputs[{index}] source_ids 未解析: {sources}")
    return {"path": path.relative_to(root).as_posix(), "run_id": payload.get("run_id"),
            "status": "PASS" if not issues else "FAIL", "issues": issues,
            "output_ids": sorted(value for value in output_ids if isinstance(value, str))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--strict", action="store_true", help="缺少运行清单也失败")
    args = parser.parse_args()
    root = args.project_root.resolve()
    run_root = root / ".contest" / "runs"
    manifests = sorted(run_root.glob("*/run_manifest.json")) if run_root.is_dir() else []
    issues: list[str] = []
    warnings: list[str] = []
    if not manifests:
        message = "未发现 .contest/runs/*/run_manifest.json"
        (issues if args.strict else warnings).append(message)
    reports = [validate_manifest(root, path) for path in manifests]
    issues.extend(f"{item['path']}: {issue}" for item in reports for issue in item["issues"])
    payload = {"schema_version": "1.0", "checked_at": datetime.now(timezone.utc).isoformat(),
               "project_root": str(root), "manifest_count": len(manifests),
               "reports": reports, "issues": issues, "warnings": warnings,
               "passed": not issues}
    out = args.out.resolve() if args.out else root / ".contest" / "run_manifest_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
