#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evidence-backed approval gates for COLLAB contest workflows.

The script never makes a modeling decision.  In ``COLLAB`` it emits a
decision packet and pauses until an approval record covers the current hashes
of the declared project artifacts.  ``AUTO`` remains backward-compatible;
``LOCK`` accepts only approvals made before the freeze.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - JSON remains available
    yaml = None


def load_mapping(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    value = json.loads(raw) if path.suffix.lower() == ".json" else (yaml.safe_load(raw) if yaml else None)
    if not isinstance(value, dict):
        raise ValueError(f"配置必须是对象: {path}")
    return value


def write_mapping(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json" or yaml is None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_policy(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        raw = Path(explicit)
        return raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    candidates = (
        root / "collab_gate_policy.yaml", root / "collab_gate_policy.json",
        root / "01_需求与规划" / "collab_gate_policy.yaml",
    )
    return next((item for item in candidates if item.is_file()), None)


def find_log(root: Path, explicit: str | None) -> Path:
    if explicit:
        raw = Path(explicit)
        return raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    return root / ".contest" / "approval_log.yaml"


def resolve_groups(root: Path, gate: dict[str, Any]) -> tuple[dict[str, Path], list[str]]:
    resolved: dict[str, Path] = {}
    missing: list[str] = []
    for item in gate.get("artifact_groups", []) or []:
        if not isinstance(item, dict):
            missing.append("非法 artifact_groups 条目")
            continue
        name = str(item.get("name", "")).strip()
        choices = item.get("any_of", [])
        if not name or not isinstance(choices, list) or not choices:
            missing.append(f"artifact_groups 配置不完整: {item}")
            continue
        match = next((root / str(choice) for choice in choices if (root / str(choice)).is_file()), None)
        if match is None:
            missing.append(f"{name}: " + " 或 ".join(map(str, choices)))
        else:
            resolved[name] = match.resolve()
    return resolved, missing


def approval_for(log: dict[str, Any], gate_id: str) -> dict[str, Any] | None:
    approvals = log.get("approvals", [])
    if not isinstance(approvals, list):
        return None
    candidates = [item for item in approvals if isinstance(item, dict) and item.get("gate") == gate_id]
    return candidates[-1] if candidates else None


def digest_map(root: Path, paths: dict[str, Path]) -> dict[str, str]:
    return {str(path.relative_to(root)).replace("\\", "/"): sha256(path) for path in paths.values()}


def report_for(root: Path, gate: dict[str, Any], mode: str, log: dict[str, Any],
               activate: bool, freeze_at: str | None = None) -> tuple[dict[str, Any], int]:
    gate_id = str(gate.get("id", "")).strip()
    conditional = bool(gate.get("conditional", False))
    resolved, missing = resolve_groups(root, gate)
    report: dict[str, Any] = {
        "schema_version": "1.0", "gate": gate_id, "mode": mode,
        "conditional": conditional, "review_packet": gate.get("review_packet", []),
        "artifacts": [str(path.relative_to(root)).replace("\\", "/") for path in resolved.values()],
        "missing_artifacts": missing,
    }
    if conditional and not activate:
        report.update({"status": "NOT_APPLICABLE", "reason": "条件式小问门未被本次路线激活"})
        return report, 0
    if missing:
        report.update({"status": "BLOCK", "reason": "决策包缺少必需产物"})
        return report, 1
    if mode == "AUTO":
        report.update({"status": "PASS", "reason": "AUTO 模式记录决策包但不等待人工批准"})
        return report, 0
    approval = approval_for(log, gate_id)
    if approval is None or approval.get("decision") != "approved":
        report.update({"status": "PAUSE", "reason": "等待用户确认该决策包", "approval_command": f"python scripts/collab_gate.py {root} --gate {gate_id} --approve --note <用户确认摘要>"})
        return report, 2
    if mode == "LOCK":
        if not freeze_at:
            report.update({"status": "PAUSE", "reason": "LOCK 模式缺少 policy.freeze_at，不能判断批准是否早于冻结点"})
            return report, 2
        if str(approval.get("approved_at", "")) > str(freeze_at):
            report.update({"status": "PAUSE", "reason": "批准记录晚于冻结点，LOCK 不接受新批准", "freeze_at": freeze_at})
            return report, 2
    expected = approval.get("artifact_digests", {})
    current = digest_map(root, resolved)
    if not isinstance(expected, dict) or expected != current:
        report.update({"status": "PAUSE", "reason": "已批准产物发生变化，需重新确认", "approved_at": approval.get("approved_at")})
        return report, 2
    report.update({"status": "PASS", "reason": "批准记录与当前产物哈希一致", "approved_at": approval.get("approved_at")})
    return report, 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--gate", required=True)
    parser.add_argument("--mode", choices=("AUTO", "COLLAB", "LOCK"), default="COLLAB")
    parser.add_argument("--policy", default=None)
    parser.add_argument("--approval-log", default=None)
    parser.add_argument("--activate", action="store_true", help="激活条件式 G3 小问门")
    parser.add_argument("--approve", action="store_true", help="在用户明确确认后写入当前产物哈希")
    parser.add_argument("--note", default="")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    policy_path = find_policy(root, args.policy)
    if policy_path is None or not policy_path.is_file():
        report, code = {"schema_version": "1.0", "status": "BLOCK", "gate": args.gate,
                        "reason": "缺少 collab_gate_policy.yaml"}, 1
    else:
        try:
            policy = load_mapping(policy_path)
            gate = next((item for item in policy.get("gates", []) if isinstance(item, dict) and item.get("id") == args.gate), None)
            if gate is None:
                raise ValueError(f"策略中不存在 gate={args.gate}")
            log_path = find_log(root, args.approval_log)
            log = load_mapping(log_path) if log_path.is_file() else {"schema_version": "1.0", "approvals": []}
            if args.approve:
                if args.mode == "LOCK":
                    raise ValueError("LOCK 模式禁止写入新批准记录")
                resolved, missing = resolve_groups(root, gate)
                if missing:
                    raise ValueError("不能批准，缺少产物: " + "; ".join(missing))
                approvals = log.setdefault("approvals", [])
                if not isinstance(approvals, list):
                    raise ValueError("approval_log.approvals 必须是数组")
                approvals.append({"gate": args.gate, "decision": "approved", "note": args.note,
                                  "approved_at": datetime.now(timezone.utc).isoformat(),
                                  "artifact_digests": digest_map(root, resolved)})
                write_mapping(log_path, log)
            report, code = report_for(root, gate, args.mode, log, args.activate,
                                      str(policy.get("freeze_at", "")).strip() or None)
            report["policy_path"] = str(policy_path)
            report["approval_log"] = str(log_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            report, code = {"schema_version": "1.0", "status": "BLOCK", "gate": args.gate, "reason": str(exc)}, 1
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        output = Path(args.out).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
