#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Route post-freeze project changes to the smallest safe validation scope."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml


NODES = tuple(f"H{index}" for index in range(10))
PROFILE_NAMES = {"competition_fast", "standard"}
IMPACT_LEVELS = {"L0", "L1", "L2", "L3"}
HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
REQUIRED_CARD_FIELDS = (
    "schema_version",
    "change_id",
    "profile",
    "impact_level",
    "reason",
    "changed_artifacts",
    "affected_subproblems",
    "earliest_invalid_node",
    "protected_fields",
)

ROUTE_BY_LEVEL: dict[str, dict[str, Any]] = {
    "L0": {
        "recheck_nodes": ["H8"],
        "checks": ["paper_narrative", "paper_claim_coverage", "process_term_scan"],
        "visual_check": False,
    },
    "L1": {
        "recheck_nodes": ["H7"],
        "checks": ["figure_registry", "figure_format", "visual_evidence_binding", "scipilot_visual_qa"],
        "visual_check": True,
    },
    "L2": {
        "recheck_nodes": ["H5", "H6", "H7", "H8"],
        "checks": ["targeted_H5", "targeted_H6", "refresh_visual_evidence_packet", "affected_H7", "affected_H8"],
        "visual_check": False,
    },
}

ALLOWED_ARTIFACT_KINDS = {
    "paper_prose",
    "paper_layout",
    "paper_metadata",
    "figure",
    "question_model",
    "question_result",
    "question_code",
    "question_data",
    "global_interface",
    "global_assumption",
    "citation",
}
L0_KINDS = {"paper_prose", "paper_layout", "paper_metadata", "citation"}
L1_KINDS = {"figure"}
L2_KINDS = {"question_model", "question_result", "question_code", "question_data"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_relative_path(root: Path, raw: Any) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts or "\x00" in raw:
        return None
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return resolved


def validate_change_impact(root: Path, card: dict[str, Any]) -> list[str]:
    """Validate a change card without mutating the project."""
    root = root.resolve()
    errors: list[str] = []
    if not isinstance(card, dict):
        return ["change_impact_card 必须为对象"]
    missing = [field for field in REQUIRED_CARD_FIELDS if field not in card]
    if missing:
        errors.append(f"change_impact_card 缺少字段: {','.join(missing)}")
    if card.get("schema_version") != "1.0":
        errors.append("change_impact_card.schema_version 必须为 1.0")
    profile = card.get("profile")
    if profile not in PROFILE_NAMES:
        errors.append(f"change_impact_card.profile 无效: {profile}")
    level = card.get("impact_level")
    if level not in IMPACT_LEVELS:
        errors.append(f"change_impact_card.impact_level 必须为 L0/L1/L2/L3（当前: {level}）")
    if not isinstance(card.get("change_id"), str) or not re.fullmatch(r"chg-[A-Za-z0-9][A-Za-z0-9_.-]{2,63}", card.get("change_id", "")):
        errors.append("change_impact_card.change_id 必须匹配 chg-<unique-id>")
    if not isinstance(card.get("reason"), str) or not card.get("reason", "").strip():
        errors.append("change_impact_card.reason 不得为空")

    artifacts = card.get("changed_artifacts")
    artifact_kinds: set[str] = set()
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("change_impact_card.changed_artifacts 必须为非空列表")
        artifacts = []
    for index, artifact in enumerate(artifacts):
        label = f"changed_artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{label} 必须为对象")
            continue
        path = _safe_relative_path(root, artifact.get("path"))
        if path is None:
            errors.append(f"{label}.path 必须为项目内相对路径")
        elif not path.is_file():
            errors.append(f"{label}.path 文件不存在: {artifact.get('path')}")
        after = artifact.get("after_sha256")
        if not isinstance(after, str) or not HASH_RE.fullmatch(after):
            errors.append(f"{label}.after_sha256 必须为 64 位十六进制字符串")
        elif path is not None and path.is_file() and _sha256(path).lower() != after.lower():
            errors.append(f"{label}.after_sha256 与当前文件不匹配: {artifact.get('path')}")
        before = artifact.get("before_sha256")
        if before is not None:
            if not isinstance(before, str) or not HASH_RE.fullmatch(before):
                errors.append(f"{label}.before_sha256 必须为 null 或 64 位十六进制字符串")
            elif isinstance(after, str) and before.lower() == after.lower():
                errors.append(f"{label}.before_sha256 与 after_sha256 不能相同")
        kind = artifact.get("artifact_kind")
        if kind not in ALLOWED_ARTIFACT_KINDS:
            errors.append(f"{label}.artifact_kind 无效: {kind}")
        elif isinstance(kind, str):
            artifact_kinds.add(kind)

    affected = card.get("affected_subproblems")
    if not isinstance(affected, list) or any(not isinstance(item, str) or not item.strip() for item in affected):
        errors.append("change_impact_card.affected_subproblems 必须为字符串列表")
        affected = []
    elif len(set(affected)) != len(affected):
        errors.append("change_impact_card.affected_subproblems 不得重复")

    earliest = card.get("earliest_invalid_node")
    if earliest not in NODES[1:9]:
        errors.append("change_impact_card.earliest_invalid_node 必须为 H1–H8")
    protected = card.get("protected_fields")
    if not isinstance(protected, list) or not protected or any(not isinstance(item, str) or not item.strip() for item in protected):
        errors.append("change_impact_card.protected_fields 必须为非空字符串列表")
    elif len(set(protected)) != len(protected):
        errors.append("change_impact_card.protected_fields 不得重复")

    if level == "L0":
        if not artifact_kinds.issubset(L0_KINDS):
            errors.append("L0 只能登记正文、排版、论文元数据或引用文件")
        if earliest != "H8":
            errors.append("L0 的 earliest_invalid_node 必须为 H8")
    elif level == "L1":
        if artifact_kinds != L1_KINDS:
            errors.append("L1 只能登记 figure 文件")
        if earliest != "H7":
            errors.append("L1 的 earliest_invalid_node 必须为 H7")
    elif level == "L2":
        if len(affected) != 1:
            errors.append("L2 只允许覆盖一个小问")
        if not artifact_kinds.issubset(L2_KINDS):
            errors.append("L2 只能登记单小问模型、结果、代码或数据文件")
        if earliest != "H5":
            errors.append("L2 的 earliest_invalid_node 必须为 H5")
    elif level == "L3":
        if earliest == "H9":
            errors.append("L3 的 earliest_invalid_node 必须早于 H9")
        if affected and len(affected) == 1 and not any(kind.startswith("global_") for kind in artifact_kinds):
            errors.append("L3 的单小问变更必须降级为 L2，或登记全局影响")

    if not isinstance(card.get("skill_code_changed", False), bool):
        errors.append("change_impact_card.skill_code_changed 必须为布尔值")
    return errors


def build_validation_plan(card: dict[str, Any]) -> dict[str, Any]:
    """Build the deterministic validation plan declared by a valid card."""
    level = card.get("impact_level")
    if level == "L3":
        earliest = card.get("earliest_invalid_node")
        start = NODES.index(earliest) if earliest in NODES else NODES.index("H1")
        recheck_nodes = list(NODES[start:NODES.index("H9")])
        checks = [
            "recompute_from_earliest_invalid_node",
            "global_interface_check",
            "refresh_visual_evidence_packet",
            "full_cross_question_check",
        ]
        visual_check = True if "figure" in {item.get("artifact_kind") for item in card.get("changed_artifacts", []) if isinstance(item, dict)} else False
    else:
        route = ROUTE_BY_LEVEL.get(level, {"recheck_nodes": [], "checks": [], "visual_check": False})
        recheck_nodes = list(route["recheck_nodes"])
        checks = list(route["checks"])
        visual_check = bool(route["visual_check"])
    skill_code_changed = card.get("skill_code_changed", False) is True
    return {
        "schema_version": "1.0",
        "profile": card.get("profile"),
        "change_id": card.get("change_id"),
        "impact_level": level,
        "affected_subproblems": list(card.get("affected_subproblems", [])),
        "recheck_nodes": recheck_nodes,
        "checks": checks,
        "visual_check": visual_check,
        "run_skill_suite": skill_code_changed,
        "h9_full_delivery_required": True,
        "full_delivery_gate": "H9",
        "operator_rule": "H9 前不得以局部检查替代完整交付门禁",
    }


def validate_control_validation(root: Path, control: dict[str, Any]) -> tuple[list[str], dict[str, Any] | None]:
    """Validate the optional control-level profile and any active change card."""
    root = root.resolve()
    errors: list[str] = []
    validation = control.get("validation", {})
    if validation is None:
        validation = {}
    if not isinstance(validation, dict):
        return ["validation 必须为对象"], None
    profile = validation.get("profile", "standard")
    if profile not in PROFILE_NAMES:
        errors.append(f"validation.profile 无效: {profile}")
    card_raw = validation.get("change_impact_card")
    stale_nodes = [
        node_id for node_id, node in (control.get("nodes", {}) or {}).items()
        if isinstance(node, dict) and node.get("status") == "stale"
    ]
    if stale_nodes and profile == "competition_fast" and not isinstance(card_raw, str):
        errors.append("competition_fast 下存在 stale 节点时必须登记 change_impact_card")
        return errors, None
    if card_raw is None:
        return errors, None
    card_path = _safe_relative_path(root, card_raw)
    if card_path is None or not card_path.is_file():
        errors.append(f"change_impact_card 文件不存在或路径不安全: {card_raw}")
        return errors, None
    try:
        card = yaml.safe_load(card_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"change_impact_card 不可读: {exc}")
        return errors, None
    errors.extend(validate_change_impact(root, card))
    if card.get("profile") != profile:
        errors.append("change_impact_card.profile 必须与 validation.profile 一致")
    return errors, build_validation_plan(card) if not errors else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--card", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    root = args.project_root.resolve()
    card_path = (args.card or (root / ".contest" / "change_impact_card.yaml")).resolve()
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "BLOCK",
        "card": str(card_path),
        "errors": [],
        "plan": None,
    }
    if not card_path.is_file():
        report["errors"] = [f"change_impact_card 文件不存在: {card_path}"]
    else:
        try:
            card = yaml.safe_load(card_path.read_text(encoding="utf-8")) or {}
            errors = validate_change_impact(root, card)
            report["errors"] = errors
            if not errors:
                report["status"] = "PASS"
                report["plan"] = build_validation_plan(card)
        except (OSError, yaml.YAMLError) as exc:
            report["errors"] = [f"change_impact_card 不可读: {exc}"]
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.out.resolve().write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
