#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check claim-driven visual evidence in a project content budget plan."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

try:  # Support both package imports in tests and direct CLI execution.
    from .check_reader_evidence import READER_EVIDENCE_VERSION, validate_protocol_version, validate_visual_representation
except ImportError:  # pragma: no cover
    from check_reader_evidence import READER_EVIDENCE_VERSION, validate_protocol_version, validate_visual_representation


VISUAL_AUDIT_CATEGORIES = (
    "orientation",
    "mechanism",
    "model_structure",
    "algorithm_process",
    "result_evidence",
    "validation_robustness",
)
VISUAL_DISPOSITIONS = {
    "required", "recommended", "table_justified", "text_sufficient", "not_applicable",
}
COMPLEX_MODEL_FAMILIES = {"optimization", "prediction", "ode", "simulation", "statistical"}
ALGORITHM_MARKERS = (
    "iteration", "iterative", "heuristic", "genetic", "particle", "pso", "simulated annealing",
    "monte carlo", "模拟退火", "遗传", "粒子群", "迭代", "启发", "蒙特卡洛",
)
MECHANISM_MARKERS = (
    "mechanism", "geometry", "force", "spatial", "coverage", "path", "trajectory", "dynamics",
    "几何", "机理", "受力", "空间", "覆盖", "路径", "轨迹", "动力", "海域", "角度", "深度",
)
PLACEHOLDER_VALUES = {"todo", "tbd", "fixture", "待填", "待补", "未定"}
PACKET_STATUSES = {"draft", "verified", "stale", "evidence_gap"}
PACKET_UNIT_TYPES = {
    "model", "result", "validation", "mechanism", "algorithm", "comparison",
    "cross_question", "parameter",
}
PACKET_FORBIDDEN_FIELDS = {
    "raw_data", "full_code", "full_literature", "full_text", "chat_history",
    "debug_log", "prompts", "conversation", "internal_notes",
}
FIGURE_INTENT_ROUTES = {
    "modelviz",
    "tikz-scientific-figures",
    "drawio-diagram",
}
FIGURE_TEMPLATE_STATUSES = {"native", "external_adapted", "custom_required"}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
TEMPLATE_ROUTES_REQUIRING_STARTER = {"tikz-scientific-figures"}
CANVAS_ORIENTATIONS = {"horizontal", "vertical", "square"}
CANVAS_LAYOUTS = {"single", "side_by_side", "wrap_short", "tall_constrained"}
TEMPLATE_FIXTURE_STATUSES = {"passed"}
TEMPLATE_CATALOG_PATH = Path(__file__).resolve().parents[1] / "references" / "figure_template_catalog.yaml"


def load(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    value = json.loads(raw) if path.suffix.lower() == ".json" else (yaml.safe_load(raw) if yaml else None)
    if not isinstance(value, dict):
        raise ValueError("内容预算计划必须是对象")
    return value


def find(root: Path, names: tuple[str, ...]) -> Path | None:
    for base in (root, root / "01_需求与规划", root / "05_输出与交付", root / "paper"):
        for name in names:
            path = base / name
            if path.is_file():
                return path
    return None


def registry_entries(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    value = load(path)
    entries = value.get("figures", value) if isinstance(value, dict) else {}
    if isinstance(entries, list):
        entries = {str(item.get("id", index)): item for index, item in enumerate(entries) if isinstance(item, dict)}
    return entries if isinstance(entries, dict) else {}


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _valid_text(value: Any) -> bool:
    text = _text(value)
    return bool(text) and text.lower() not in PLACEHOLDER_VALUES and not text.startswith("<")


def _template_catalog() -> dict[str, dict[str, Any]]:
    """Load the contest route starter catalog keyed by its stable template ID."""
    if yaml is None or not TEMPLATE_CATALOG_PATH.is_file():
        return {}
    try:
        payload = yaml.safe_load(TEMPLATE_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    entries = payload.get("templates") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return {}
    return {
        str(item.get("template_id")): item
        for item in entries
        if isinstance(item, dict) and _valid_text(item.get("template_id"))
    }


def _safe_project_path(root: Path, raw: Any) -> Path | None:
    """Resolve a project-relative path without allowing traversal."""
    if root is None or not isinstance(raw, str) or not raw.strip():
        return None
    candidate_raw = Path(raw)
    if candidate_raw.is_absolute() or ".." in candidate_raw.parts:
        return None
    candidate = (root / candidate_raw).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _element_map_signature(value: Any) -> list[tuple[str, str, tuple[str, ...]]]:
    if not isinstance(value, list):
        return []
    signature: list[tuple[str, str, tuple[str, ...]]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        signature.append((
            _text(item.get("element")),
            _text(item.get("role")).lower(),
            tuple(_strings(item.get("evidence_refs"))),
        ))
    return signature


def _validate_visible_element_map(
    value: Any,
    label: str,
    must_show: list[str] | None = None,
) -> list[str]:
    """Validate the evidence map that binds visible elements to source locators."""
    errors: list[str] = []
    if not isinstance(value, list) or not value:
        return [f"{label} visible_element_map 必须为非空列表"]
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(value):
        item_label = f"{label} visible_element_map[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_label} 必须为对象")
            continue
        element = _text(item.get("element"))
        role = _text(item.get("role")).lower()
        evidence_refs = _strings(item.get("evidence_refs"))
        if not _valid_text(element):
            errors.append(f"{item_label}.element 不得为空或占位")
        if not _valid_text(role):
            errors.append(f"{item_label}.role 不得为空或占位")
        if not evidence_refs:
            errors.append(f"{item_label}.evidence_refs 必须为非空列表")
        elif any(not _valid_text(ref) for ref in evidence_refs):
            errors.append(f"{item_label}.evidence_refs 不得包含占位值")
        key = (element.casefold(), role)
        if key in seen:
            errors.append(f"{label} visible_element_map 不得重复 element/role")
        seen.add(key)
    minimum = max(1, len(must_show or []))
    if len(value) < minimum:
        errors.append(f"{label} visible_element_map 至少需要 {minimum} 个可视元素")
    return errors


def _validate_canvas_profile(value: Any, label: str) -> list[str]:
    """Validate the deterministic canvas contract used by generation and LaTeX layout."""
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{label} canvas_profile 必须为对象"]
    orientation = _text(value.get("orientation")).lower()
    if orientation not in CANVAS_ORIENTATIONS:
        errors.append(f"{label} canvas_profile.orientation 必须为 horizontal/vertical/square")
    target_layout = _text(value.get("target_layout")).lower()
    if target_layout not in CANVAS_LAYOUTS:
        errors.append(f"{label} canvas_profile.target_layout 必须为 single/side_by_side/wrap_short/tall_constrained")
    node_limit = value.get("top_level_node_limit")
    if not isinstance(node_limit, int) or not 2 <= node_limit <= 12:
        errors.append(f"{label} canvas_profile.top_level_node_limit 必须为 2-12 的整数")
    for field in ("width_ratio", "height_ratio"):
        if field not in value:
            continue
        ratio = value.get(field)
        if not isinstance(ratio, (int, float)) or not 0 < ratio <= 1:
            errors.append(f"{label} canvas_profile.{field} 必须为 (0,1] 数值")
    return errors


def _packet_unit_index(packet: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Return information units keyed by their globally unique unit id."""
    if not isinstance(packet, dict):
        return {}
    index: dict[str, dict[str, Any]] = {}
    for item in packet.get("subproblems", []) or []:
        if not isinstance(item, dict):
            continue
        for unit in item.get("information_units", []) or []:
            if isinstance(unit, dict) and _valid_text(unit.get("unit_id")):
                index[str(unit["unit_id"])] = unit
    return index


def _packet_statement_key(value: Any) -> str:
    """Normalize a statement for exact duplicate detection within a packet."""
    return re.sub(r"\s+", " ", _text(value)).strip().casefold()


def _validate_packet_evidence_ref(
    reference: Any,
    root: Path | None,
    label: str,
    errors: list[str],
) -> None:
    """Validate one hash-bound evidence pointer without reading its full payload."""
    if not isinstance(reference, dict):
        errors.append(f"{label} 必须为含 path/sha256/locator 的对象")
        return
    path_raw = reference.get("path")
    expected = reference.get("sha256")
    locator = reference.get("locator")
    if not isinstance(path_raw, str) or not path_raw.strip():
        errors.append(f"{label}.path 不得为空")
    elif Path(path_raw).is_absolute() or ".." in Path(path_raw).parts:
        errors.append(f"{label}.path 必须为项目内相对路径")
    if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
        errors.append(f"{label}.sha256 必须为 64 位十六进制字符串")
    if not _valid_text(locator):
        errors.append(f"{label}.locator 不得为空或占位")
    if root is None or not isinstance(path_raw, str) or not path_raw.strip():
        return
    path = (root / path_raw).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label}.path 超出项目根目录")
        return
    if not path.is_file():
        errors.append(f"{label}.path 文件不存在: {path_raw}")
        return
    if isinstance(expected, str) and SHA256_RE.fullmatch(expected):
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual.lower() != expected.lower():
            errors.append(f"{label} 证据哈希不匹配: {path_raw}")


def validate_visual_evidence_packet(
    packet: dict[str, Any],
    *,
    root: Path | None = None,
    expected_subproblems: list[str] | None = None,
    stage: str = "h5",
    expected_h6_instance: str | None = None,
    model_contract_path: Path | None = None,
) -> dict[str, Any]:
    """Validate the compact H5-to-H7 visual evidence handoff."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(packet, dict):
        return {"status": "BLOCK", "errors": ["visual_evidence_packet 必须为对象"], "warnings": [], "metrics": {}}
    if packet.get("schema_version") != "1.0":
        errors.append("visual_evidence_packet.schema_version 必须为 1.0")
    status = _text(packet.get("status")).lower()
    if status not in PACKET_STATUSES:
        errors.append("visual_evidence_packet.status 必须为 draft/verified/stale/evidence_gap")
    if stage not in {"h5", "h6", "h7"}:
        errors.append("visual_evidence_packet.stage 必须为 h5/h6/h7")
    elif stage == "h5" and status not in {"draft", "evidence_gap"}:
        errors.append("H5 阶段 visual_evidence_packet.status 必须为 draft 或 evidence_gap")
    elif stage in {"h6", "h7"} and status != "verified":
        errors.append(f"{stage.upper()} 阶段 visual_evidence_packet.status 必须为 verified")
    if packet.get("package_mode") != "indexed_minimal":
        errors.append("visual_evidence_packet.package_mode 必须为 indexed_minimal")
    if packet.get("source_node") != "H5":
        errors.append("visual_evidence_packet.source_node 必须为 H5")
    if packet.get("created_by") != "H5":
        errors.append("visual_evidence_packet.created_by 必须为 H5")
    if stage in {"h6", "h7"}:
        if packet.get("verified_by") != "H6":
            errors.append(f"{stage.upper()} 阶段 visual_evidence_packet.verified_by 必须为 H6")
        instance = packet.get("verification_agent_instance_id")
        if not isinstance(instance, str) or not instance.strip():
            errors.append("visual_evidence_packet 缺少 verification_agent_instance_id")
        elif expected_h6_instance and instance != expected_h6_instance:
            errors.append("visual_evidence_packet 必须由当前 H6 实例核验")
    contract_sha = packet.get("model_contract_sha256")
    if not isinstance(contract_sha, str) or not SHA256_RE.fullmatch(contract_sha):
        errors.append("visual_evidence_packet.model_contract_sha256 必须为 64 位十六进制字符串")
    elif model_contract_path is not None:
        if not model_contract_path.is_file():
            errors.append("visual_evidence_packet 绑定的 model_contract.yaml 不存在")
        else:
            actual = hashlib.sha256(model_contract_path.read_bytes()).hexdigest()
            if actual.lower() != contract_sha.lower():
                errors.append("visual_evidence_packet.model_contract_sha256 与 model_contract.yaml 不匹配")
    forbidden = sorted(PACKET_FORBIDDEN_FIELDS.intersection(packet.keys()))
    if forbidden:
        errors.append(f"visual_evidence_packet 不得嵌入完整或过程材料: {','.join(forbidden)}")

    raw_subproblems = packet.get("subproblems")
    if not isinstance(raw_subproblems, list) or not raw_subproblems:
        errors.append("visual_evidence_packet.subproblems 必须为非空列表")
        raw_subproblems = []
    expected = [item.strip() for item in (expected_subproblems or []) if isinstance(item, str) and item.strip()]
    seen_subproblems: set[str] = set()
    unit_index: dict[str, dict[str, Any]] = {}
    unit_statement_keys: set[str] = set()
    for index, item in enumerate(raw_subproblems):
        label = f"subproblems[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} 必须为对象")
            continue
        qid = _text(item.get("subproblem_id"))
        if not _valid_text(qid):
            errors.append(f"{label} 缺少有效 subproblem_id")
        elif qid in seen_subproblems:
            errors.append(f"{label} subproblem_id 重复: {qid}")
        else:
            seen_subproblems.add(qid)
        for field in ("task_goal", "model_role"):
            if not _valid_text(item.get(field)):
                errors.append(f"{label} 缺少 {field}")
        units = item.get("information_units")
        if not isinstance(units, list) or not units:
            errors.append(f"{label}.information_units 必须为非空列表")
            continue
        if len(units) < 2:
            errors.append(f"{label}.information_units 至少需要 2 个独立信息单元")
        local_ids: set[str] = set()
        for unit_index_value, unit in enumerate(units):
            unit_label = f"{label}.information_units[{unit_index_value}]"
            if not isinstance(unit, dict):
                errors.append(f"{unit_label} 必须为对象")
                continue
            for field in ("unit_id", "unit_type", "statement", "meaning", "scope", "unit"):
                if not _valid_text(unit.get(field)):
                    errors.append(f"{unit_label} 缺少 {field}")
            unit_id = _text(unit.get("unit_id"))
            if unit_id:
                if unit_id in local_ids or unit_id in unit_index:
                    errors.append(f"{unit_label} unit_id 重复: {unit_id}")
                else:
                    local_ids.add(unit_id)
                    unit_index[unit_id] = unit
            unit_type = _text(unit.get("unit_type")).lower()
            if unit_type and unit_type not in PACKET_UNIT_TYPES:
                errors.append(f"{unit_label}.unit_type 无效: {unit_type}")
            statement_key = _packet_statement_key(unit.get("statement"))
            if statement_key:
                if statement_key in unit_statement_keys:
                    errors.append(f"{unit_label}.statement 与其他信息单元重复")
                unit_statement_keys.add(statement_key)
            refs = unit.get("evidence_refs")
            if not isinstance(refs, list) or not refs:
                errors.append(f"{unit_label}.evidence_refs 必须为非空列表")
            else:
                for ref_index, reference in enumerate(refs):
                    _validate_packet_evidence_ref(reference, root, f"{unit_label}.evidence_refs[{ref_index}]", errors)
    if expected and seen_subproblems != set(expected):
        missing = sorted(set(expected) - seen_subproblems)
        extra = sorted(seen_subproblems - set(expected))
        if missing:
            errors.append(f"visual_evidence_packet 缺少小问: {','.join(missing)}")
        if extra:
            errors.append(f"visual_evidence_packet 含未登记小问: {','.join(extra)}")
    if status == "evidence_gap":
        warnings.append("visual_evidence_packet 标记为 evidence_gap，必须回流 H5 补充证据")
    return {
        "status": "BLOCK" if errors else ("WARN" if warnings else "PASS"),
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "subproblem_count": len(seen_subproblems),
            "information_unit_count": len(unit_index),
            "information_unit_ids": sorted(unit_index),
        },
    }


def _model_card_index(model_cards: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(model_cards, dict):
        return {}
    cards = model_cards.get("cards", model_cards)
    if isinstance(cards, dict):
        cards = list(cards.values())
    if not isinstance(cards, list):
        return {}
    return {
        str(card.get("subproblem_id")): card
        for card in cards
        if isinstance(card, dict) and _text(card.get("subproblem_id"))
    }


def _infer_visual_profile(card: dict[str, Any] | None, plan_item: dict[str, Any]) -> dict[str, Any]:
    """Infer hard visual obligations from upstream model facts, not figure count."""
    card = card or {}
    final_formulation = card.get("final_formulation")
    formulation_mapping = final_formulation if isinstance(final_formulation, dict) else {}
    family = _text(card.get("model_family") or formulation_mapping.get("kind")).lower()
    purpose = _text(card.get("purpose"))
    solver = _text((card.get("solver_interface") or {}).get("method"))
    formulation = _text(
        formulation_mapping.get("expression")
        if isinstance(final_formulation, dict)
        else final_formulation
    )
    searchable = " ".join((family, purpose, solver, formulation)).lower()
    variables = card.get("decision_variables")
    variable_count = len(variables) if isinstance(variables, list) else 0
    hard = {"result_evidence"}
    signals: list[str] = []
    if family in COMPLEX_MODEL_FAMILIES or variable_count >= 2:
        hard.update({"model_structure", "validation_robustness"})
        signals.append("structured_model")
    if any(marker in searchable for marker in ALGORITHM_MARKERS):
        hard.add("algorithm_process")
        signals.append("iterative_or_heuristic_solver")
    if family in {"ode", "simulation"} or any(marker in searchable for marker in MECHANISM_MARKERS):
        hard.add("mechanism")
        signals.append("mechanism_or_spatial_relation")
    declared = _text(plan_item.get("complexity") or plan_item.get("complexity_tier")).lower()
    if declared not in {"simple", "standard", "complex"}:
        declared = ""
    inferred = "complex" if len(hard) >= 3 else "standard"
    return {
        "model_family": family or "unknown",
        "variable_count": variable_count,
        "complexity": inferred,
        "declared_complexity": declared,
        "hard_categories": sorted(hard),
        "signals": signals,
    }


def _registry_list(registry: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(registry, dict):
        return []
    figures = registry.get("figures") or registry.get("items") or registry.get("charts")
    if isinstance(figures, dict):
        figures = list(figures.values())
    return [item for item in figures if isinstance(item, dict)] if isinstance(figures, list) else []


def _validate_figure_intent(
    slot: dict[str, Any],
    label: str,
    figure_ids: list[str],
) -> tuple[list[str], dict[str, Any]]:
    """Validate the reader-first contract for every planned figure slot."""
    errors: list[str] = []
    representation = slot.get("representation")
    is_figure = bool(figure_ids) or (
        isinstance(representation, dict)
        and _text(representation.get("mode")).lower() == "figure"
    )
    intent = slot.get("figure_intent")
    if not is_figure:
        if intent is not None:
            errors.append(f"{label} 无 planned figure 时不得登记 figure_intent")
        return errors, {}
    if not isinstance(intent, dict):
        return errors + [f"{label} 规划图表时必须提供 figure_intent"], {}

    for field in (
        "reader_question",
        "explanatory_relation",
        "body_anchor",
        "pre_text_function",
        "post_text_function",
    ):
        if not _valid_text(intent.get(field)):
            errors.append(f"{label} figure_intent.{field} 不得为空或占位")

    for field, minimum in (("must_show", 1), ("must_not_show", 0)):
        values = intent.get(field)
        if not isinstance(values, list):
            errors.append(f"{label} figure_intent.{field} 必须为列表")
            continue
        if len(values) < minimum:
            errors.append(f"{label} figure_intent.{field} 至少需要 {minimum} 项")
        elif any(not _valid_text(value) for value in values):
            errors.append(f"{label} figure_intent.{field} 不得包含空值或占位")

    route = _text(intent.get("generation_route")).lower()
    if route not in FIGURE_INTENT_ROUTES:
        errors.append(
            f"{label} figure_intent.generation_route 必须为 {','.join(sorted(FIGURE_INTENT_ROUTES))}"
        )
    template_status = _text(intent.get("template_status")).lower()
    if template_status not in FIGURE_TEMPLATE_STATUSES:
        errors.append(
            f"{label} figure_intent.template_status 必须为 {','.join(sorted(FIGURE_TEMPLATE_STATUSES))}"
        )
    template_id = _text(intent.get("template_id"))
    if not _valid_text(template_id):
        errors.append(f"{label} figure_intent.template_id 不得为空或占位")
    elif route in TEMPLATE_ROUTES_REQUIRING_STARTER:
        catalog_entry = _template_catalog().get(template_id)
        if catalog_entry is None:
            errors.append(f"{label} figure_intent.template_id 未在 contest starter 目录中登记: {template_id}")
        elif _text(catalog_entry.get("generation_route")).lower() != route:
            errors.append(
                f"{label} figure_intent.template_id 与 generation_route 不匹配（"
                f"模板 {template_id}，路由 {route}）"
            )
    must_show = intent.get("must_show") if isinstance(intent.get("must_show"), list) else []
    errors.extend(_validate_visible_element_map(intent.get("visible_element_map"), label, must_show))
    errors.extend(_validate_canvas_profile(intent.get("canvas_profile"), label))
    return errors, {
        "generation_route": route,
        "template_status": template_status,
        "template_id": template_id,
        "visible_element_map": intent.get("visible_element_map"),
        "visible_element_count": (
            len(intent.get("visible_element_map"))
            if isinstance(intent.get("visible_element_map"), list)
            else 0
        ),
        "canvas_profile": intent.get("canvas_profile"),
    }


def _validate_slot(slot: Any, label: str, category: str | None = None) -> tuple[list[str], list[str], dict[str, Any] | None]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(slot, dict):
        return [f"{label} 必须为对象"], warnings, None
    slot_id = _text(slot.get("slot_id"))
    if not _valid_text(slot_id):
        errors.append(f"{label} 缺少有效 slot_id")
    actual_category = _text(slot.get("category"))
    if category is not None and actual_category != category:
        errors.append(f"{label} category 必须为 {category}")
    elif not _valid_text(actual_category):
        errors.append(f"{label} 缺少 category")
    disposition = _text(slot.get("disposition")).lower()
    if disposition not in VISUAL_DISPOSITIONS:
        errors.append(f"{label} disposition 必须为 {','.join(sorted(VISUAL_DISPOSITIONS))}")
    if not _valid_text(slot.get("reader_question")):
        errors.append(f"{label} 缺少 reader_question")
    if not _valid_text(slot.get("reader_gain")):
        errors.append(f"{label} 缺少 reader_gain")
    evidence_refs = _strings(slot.get("evidence_refs"))
    if not evidence_refs:
        errors.append(f"{label} 缺少 evidence_refs")
    elif any(not _valid_text(ref) for ref in evidence_refs):
        errors.append(f"{label} evidence_refs 不得包含占位值")
    figure_ids = _strings(slot.get("planned_figure_ids"))
    table_refs = _strings(slot.get("table_refs"))
    if any(not _valid_text(value) for value in figure_ids):
        errors.append(f"{label} planned_figure_ids 不得包含占位值")
    if any(not _valid_text(value) for value in table_refs):
        errors.append(f"{label} table_refs 不得包含占位值")
    intent_errors, intent = _validate_figure_intent(slot, label, figure_ids)
    errors.extend(intent_errors)
    if disposition == "required" and not figure_ids:
        errors.append(f"{label} 为 required 时必须登记 planned_figure_ids")
    elif disposition == "recommended" and not figure_ids and not _valid_text(slot.get("deferred_reason")):
        errors.append(f"{label} 为 recommended 时必须给出 planned_figure_ids 或 deferred_reason")
    elif disposition in {"text_sufficient", "not_applicable"}:
        if not _valid_text(slot.get("rationale")):
            errors.append(f"{label} 为 {disposition} 时必须给出 rationale")
        if figure_ids:
            errors.append(f"{label} 为 {disposition} 时不得登记 planned_figure_ids")
    elif disposition == "table_justified":
        if actual_category != "result_evidence":
            errors.append(f"{label} 只有 result_evidence 可以使用 table_justified")
        if not table_refs:
            errors.append(f"{label} 为 table_justified 时必须登记 table_refs")
        justification = slot.get("table_justification")
        if not isinstance(justification, dict):
            errors.append(f"{label} 缺少 table_justification")
        else:
            shape = _text(justification.get("result_shape")).lower()
            rows = justification.get("row_count")
            continuous = justification.get("continuous_dimension_count")
            if shape not in {"discrete", "categorical", "few_scenarios"}:
                errors.append(f"{label} table_justification.result_shape 必须为 discrete/categorical/few_scenarios")
            if not isinstance(rows, int) or not 1 <= rows <= 12:
                errors.append(f"{label} table_justification.row_count 必须为 1-12 的整数")
            if not isinstance(continuous, int) or continuous != 0:
                errors.append(f"{label} table_justification.continuous_dimension_count 必须为 0")
            if justification.get("reader_can_compare_directly") is not True:
                errors.append(f"{label} table_justification.reader_can_compare_directly 必须为 true")
            if not _valid_text(justification.get("reason")):
                errors.append(f"{label} table_justification.reason 不得为空或占位")
        if figure_ids:
            errors.append(f"{label} 为 table_justified 时不得登记 planned_figure_ids")
    return errors, warnings, {
        "slot_id": slot_id,
        "category": actual_category,
        "disposition": disposition,
        "figure_ids": figure_ids,
        "table_refs": table_refs,
        "evidence_refs": evidence_refs,
        "information_unit_ids": _strings(slot.get("information_unit_ids")),
        "density_profile": _text(slot.get("density_profile")).lower(),
        "generation_route": intent.get("generation_route"),
        "template_status": intent.get("template_status"),
        "template_id": intent.get("template_id"),
        "visible_element_map": intent.get("visible_element_map"),
        "visible_element_count": intent.get("visible_element_count", 0),
        "canvas_profile": intent.get("canvas_profile"),
    }


def _validate_slot_information_units(
    slot: dict[str, Any],
    normalized: dict[str, Any],
    packet_units: dict[str, dict[str, Any]],
    label: str,
    errors: list[str],
) -> None:
    """Require a planned visual slot to name distinct evidence units."""
    disposition = normalized["disposition"]
    figure_ids = normalized["figure_ids"]
    if disposition in {"text_sufficient", "not_applicable"} and not figure_ids:
        return
    unit_ids = normalized["information_unit_ids"]
    if not unit_ids:
        errors.append(f"{label} 缺少 information_unit_ids（图表必须绑定证据信息单元）")
        return
    if len(set(unit_ids)) != len(unit_ids):
        errors.append(f"{label} information_unit_ids 不得重复")
    unknown = sorted(set(unit_ids) - set(packet_units))
    if unknown:
        errors.append(f"{label} 引用了不存在的信息单元: {','.join(unknown)}")
    density = normalized["density_profile"]
    if density not in {"standard", "compact"}:
        errors.append(f"{label} density_profile 必须为 standard 或 compact")
    elif density == "standard" and len(set(unit_ids)) < 2:
        errors.append(f"{label} standard 图至少需要 2 个独立信息单元")
    if density == "standard" and normalized.get("visible_element_count", 0) < 2:
        errors.append(f"{label} standard 图至少需要 2 个可视元素证据映射")
    elif density == "compact":
        if len(set(unit_ids)) != 1:
            errors.append(f"{label} compact 图只能绑定 1 个信息单元")
        if not _valid_text(slot.get("compact_figure_reason")):
            errors.append(f"{label} compact 图必须给出 compact_figure_reason")


def _validate_registry_information_units(
    entry: dict[str, Any],
    expected_unit_ids: list[str],
    expected_density: str | None,
    packet_units: dict[str, dict[str, Any]],
    label: str,
    errors: list[str],
) -> None:
    """Ensure a generated figure realizes exactly the evidence planned for it."""
    information_unit_ids = _strings(entry.get("information_unit_ids"))
    realized_unit_ids = _strings(entry.get("realized_information_unit_ids"))
    if not information_unit_ids:
        errors.append(f"{label} 缺少 information_unit_ids")
    if len(set(information_unit_ids)) != len(information_unit_ids):
        errors.append(f"{label} information_unit_ids 不得重复")
    if len(set(realized_unit_ids)) != len(realized_unit_ids):
        errors.append(f"{label} realized_information_unit_ids 不得重复")
    unknown = sorted((set(information_unit_ids) | set(realized_unit_ids)) - set(packet_units))
    if unknown:
        errors.append(f"{label} 引用了不存在的信息单元: {','.join(unknown)}")
    if set(information_unit_ids) != set(expected_unit_ids):
        errors.append(f"{label} information_unit_ids 与视觉槽位计划不一致")
    if set(realized_unit_ids) != set(information_unit_ids):
        errors.append(f"{label} realized_information_unit_ids 必须与 information_unit_ids 完全一致")
    density = _text(entry.get("density_profile")).lower()
    if density not in {"standard", "compact"}:
        errors.append(f"{label} density_profile 必须为 standard 或 compact")
    elif density == "standard" and len(set(realized_unit_ids)) < 2:
        errors.append(f"{label} standard 图至少需要 2 个独立信息单元")
    elif density == "compact":
        if len(set(realized_unit_ids)) != 1:
            errors.append(f"{label} compact 图只能绑定 1 个信息单元")
        if not _valid_text(entry.get("compact_figure_reason")):
            errors.append(f"{label} compact 图必须给出 compact_figure_reason")
    if expected_density and density != expected_density:
        errors.append(f"{label} density_profile 必须与视觉槽位计划一致")


def _validate_template_fixture_report(
    fixture: dict[str, Any],
    *,
    template_id: str,
    template_sha256: str,
    label: str,
    project_root: Path | None,
    errors: list[str],
) -> None:
    """Require a machine-readable fixture report for the selected starter."""
    fixture_id = _text(fixture.get("fixture_id"))
    if not _valid_text(fixture_id):
        errors.append(f"{label} template_fixture.fixture_id 不得为空或占位")
    status = _text(fixture.get("status")).lower()
    if status not in TEMPLATE_FIXTURE_STATUSES:
        errors.append(f"{label} template_fixture.status 必须为 passed")
    report_raw = fixture.get("report")
    if not _valid_text(report_raw):
        errors.append(f"{label} template_fixture.report 不得为空或占位")
        return
    if project_root is None:
        return
    report_path = _safe_project_path(project_root, report_raw)
    if report_path is None or not report_path.is_file():
        errors.append(f"{label} template_fixture.report 文件不存在: {report_raw}")
        return
    try:
        report = load(report_path)
    except (OSError, ValueError, yaml.YAMLError if yaml else ValueError) as exc:
        errors.append(f"{label} template_fixture.report 不可读: {exc}")
        return
    if _text(report.get("status")).lower() != "passed":
        errors.append(f"{label} template_fixture.report.status 必须为 passed")
    if _text(report.get("template_id")) != template_id:
        errors.append(f"{label} template_fixture.report.template_id 必须与 template_id 一致")
    if _text(report.get("template_sha256")).lower() != template_sha256.lower():
        errors.append(f"{label} template_fixture.report.template_sha256 必须与登记哈希一致")
    if _text(report.get("visual_qa")).lower() not in {"passed", "reviewed"}:
        errors.append(f"{label} template_fixture.report.visual_qa 必须为 passed/reviewed")


def _validate_template_source_provenance(
    entry: dict[str, Any],
    *,
    route: str,
    template_id: str,
    starter_source: str,
    template_sha256: str,
    label: str,
    project_root: Path | None,
    errors: list[str],
) -> None:
    """Check that the editable route source carries the selected starter provenance."""
    if project_root is None:
        return
    script_path = _safe_project_path(project_root, entry.get("script"))
    if script_path is None or not script_path.is_file():
        return
    try:
        source = script_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        errors.append(f"{label} script 无法读取模板来源标记: {exc}")
        return
    if route == "tikz-scientific-figures":
        markers = {
            "template_id": f"contest-template-id: {template_id}",
            "starter_source": f"contest-template-source: {starter_source}",
            "template_sha256": f"contest-template-sha256: {template_sha256}",
        }
        for field, marker in markers.items():
            if marker not in source:
                errors.append(f"{label} TikZ 源文件缺少或不匹配 {field} 来源标记")


def _validate_registry_template_execution(
    entry: dict[str, Any],
    expected_slots: list[dict[str, Any]],
    *,
    label: str,
    project_root: Path | None,
    errors: list[str],
) -> None:
    """Enforce template selection, starter provenance, canvas and QA closure."""
    template_id = _text(entry.get("template_id"))
    if not _valid_text(template_id):
        errors.append(f"{label} 缺少 template_id（必须登记实际模板 ID）")
    expected_template_ids = {
        _text(slot.get("template_id")) for slot in expected_slots if _valid_text(slot.get("template_id"))
    }
    if len(expected_template_ids) == 1 and template_id != next(iter(expected_template_ids)):
        errors.append(f"{label} 的 template_id 必须与视觉计划一致")

    expected_maps = [_element_map_signature(slot.get("visible_element_map")) for slot in expected_slots]
    errors.extend(_validate_visible_element_map(entry.get("visible_element_map"), label))
    if expected_maps and expected_maps[0] and _element_map_signature(entry.get("visible_element_map")) != expected_maps[0]:
        errors.append(f"{label} visible_element_map 必须与视觉计划的可视元素证据映射一致")

    errors.extend(_validate_canvas_profile(entry.get("canvas_profile"), label))
    expected_canvas = expected_slots[0].get("canvas_profile") if expected_slots else None
    actual_canvas = entry.get("canvas_profile")
    if isinstance(expected_canvas, dict) and isinstance(actual_canvas, dict):
        for field in ("orientation", "target_layout", "top_level_node_limit"):
            if actual_canvas.get(field) != expected_canvas.get(field):
                errors.append(f"{label} canvas_profile.{field} 必须与视觉计划一致")
    target_layout = _text((entry.get("canvas_profile") or {}).get("target_layout")).lower()
    layout_mode = _text(entry.get("layout_mode")).lower()
    if target_layout and layout_mode and target_layout != layout_mode:
        errors.append(f"{label} layout_mode 必须与 canvas_profile.target_layout 一致")
    if not layout_mode:
        errors.append(f"{label} 缺少 layout_mode")

    visual_qa = _text(entry.get("visual_qa")).lower()
    if visual_qa not in {"passed", "reviewed"}:
        errors.append(f"{label} visual_qa 必须为 passed/reviewed")

    template_sha256 = _text(entry.get("template_sha256"))
    if not SHA256_RE.fullmatch(template_sha256):
        errors.append(f"{label} template_sha256 必须为 64 位十六进制字符串")
    fixture = entry.get("template_fixture")
    if not isinstance(fixture, dict):
        errors.append(f"{label} 缺少 template_fixture（对应模板 fixture 与视觉检查报告）")
    else:
        _validate_template_fixture_report(
            fixture,
            template_id=template_id,
            template_sha256=template_sha256,
            label=label,
            project_root=project_root,
            errors=errors,
        )

    route = _text(entry.get("generator") or entry.get("generation_route")).lower()
    if route in TEMPLATE_ROUTES_REQUIRING_STARTER:
        catalog_entry = _template_catalog().get(template_id)
        starter_source = _text(entry.get("starter_source"))
        if not _valid_text(starter_source):
            errors.append(f"{label} 缺少 starter_source（必须从已登记 starter 生成）")
        if catalog_entry is None:
            errors.append(f"{label} template_id 未在 contest starter 目录中登记: {template_id}")
        else:
            expected_source = _text(catalog_entry.get("starter_source"))
            expected_hash = _text(catalog_entry.get("template_sha256"))
            if starter_source != expected_source:
                errors.append(f"{label} starter_source 必须与模板目录一致")
            if template_sha256.lower() != expected_hash.lower():
                errors.append(f"{label} template_sha256 必须与 starter 实际哈希一致")
            fixture_id = _text((entry.get("template_fixture") or {}).get("fixture_id"))
            if fixture_id and fixture_id != _text(catalog_entry.get("fixture_id")):
                errors.append(f"{label} template_fixture.fixture_id 必须与模板目录一致")
        _validate_template_source_provenance(
            entry,
            route=route,
            template_id=template_id,
            starter_source=starter_source,
            template_sha256=template_sha256,
            label=label,
            project_root=project_root,
            errors=errors,
        )
    else:
        if route == "modelviz" and not _valid_text(entry.get("template_source")):
            errors.append(f"{label} modelviz 图必须登记 template_source")
        fixture_id = _text((entry.get("template_fixture") or {}).get("fixture_id"))
        if route == "modelviz" and fixture_id and fixture_id != f"modelviz/{template_id}":
            errors.append(f"{label} template_fixture.fixture_id 必须绑定实际 ModelViz template_id")


def validate_visual_argument_plan(
    plan: dict[str, Any],
    *,
    expected_subproblems: list[str] | None = None,
    model_cards: dict[str, Any] | None = None,
    evidence_packet: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
    stage: str = "plan",
    reader_protocol_enabled: bool | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Validate reader-first visual coverage and, when final, registry closure."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan, dict):
        return {"status": "BLOCK", "errors": ["visual_argument_plan 必须为对象"], "warnings": [], "metrics": {}}
    errors.extend(validate_protocol_version(plan, "visual_argument_plan"))
    if reader_protocol_enabled is None:
        reader_protocol_enabled = plan.get("reader_evidence_version") == READER_EVIDENCE_VERSION
    elif reader_protocol_enabled and plan.get("reader_evidence_version") != READER_EVIDENCE_VERSION:
        errors.append(
            "visual_argument_plan: 控制文件已启用 reader_evidence_protocol，必须登记 "
            f"reader_evidence_version={READER_EVIDENCE_VERSION}"
        )
    if plan.get("schema_version") != "1.0":
        errors.append("visual_argument_plan.schema_version 必须为 1.0")
    if plan.get("status") not in {"draft", "approved", "complete"}:
        errors.append("visual_argument_plan.status 必须为 draft/approved/complete")
    if plan.get("source_node") != "H7":
        errors.append("visual_argument_plan.source_node 必须为 H7")
    if plan.get("prepared_by") != "h7-figure-agent":
        errors.append("visual_argument_plan.prepared_by 必须为 h7-figure-agent")
    if stage != "plan" and plan.get("status") not in {"approved", "complete"}:
        errors.append("图表生成或交付阶段的 visual_argument_plan.status 必须为 approved/complete")
    packet_units = _packet_unit_index(evidence_packet)
    if evidence_packet is not None:
        if not packet_units:
            errors.append("visual_evidence_packet 必须提供至少一个 information_unit")
        if evidence_packet.get("source_node") != "H5":
            errors.append("visual_evidence_packet.source_node 必须为 H5")
        if stage != "plan" and evidence_packet.get("status") != "verified":
            errors.append("图表生成或交付阶段的 visual_evidence_packet.status 必须为 verified")

    scope = plan.get("scope")
    if not isinstance(scope, dict):
        errors.append("visual_argument_plan.scope 必须为对象")
        scope = {}
    if not isinstance(scope.get("cross_question_dependencies"), bool):
        errors.append("visual_argument_plan.scope.cross_question_dependencies 必须为布尔值")
    scope_ids = _strings(scope.get("subproblems"))
    expected_ids = [item for item in (expected_subproblems or scope_ids) if isinstance(item, str) and item.strip()]
    if not expected_ids:
        errors.append("visual_argument_plan 必须登记非空 scope.subproblems")
    if len(set(scope_ids)) != len(scope_ids):
        errors.append("visual_argument_plan.scope.subproblems 不得重复")
    if expected_subproblems is not None and scope_ids != expected_ids:
        errors.append(f"visual_argument_plan.scope.subproblems 必须与 Harness 小问完全一致（当前: {scope_ids}）")

    cards = _model_card_index(model_cards)
    if expected_subproblems is not None:
        if not cards:
            errors.append("visual_argument_plan 必须提供非空 model_summary_cards 以推断视觉硬性义务")
        else:
            missing_cards = sorted(set(expected_ids) - set(cards))
            if missing_cards:
                errors.append(f"model_summary_cards 缺少小问，无法完成视觉义务推断: {','.join(missing_cards)}")
    subproblem_items = plan.get("subproblems")
    if not isinstance(subproblem_items, list):
        errors.append("visual_argument_plan.subproblems 必须为列表")
        subproblem_items = []
    by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(subproblem_items):
        label = f"subproblems[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} 必须为对象")
            continue
        qid = _text(item.get("subproblem_id"))
        if not qid:
            errors.append(f"{label} 缺少 subproblem_id")
            continue
        complexity = _text(item.get("complexity")).lower()
        if complexity not in {"simple", "standard", "complex"}:
            errors.append(f"{label}.complexity 必须为 simple/standard/complex")
        if qid in by_id:
            errors.append(f"subproblems 重复 subproblem_id: {qid}")
        by_id[qid] = item
    if set(by_id) != set(expected_ids):
        missing_ids = sorted(set(expected_ids) - set(by_id))
        extra_ids = sorted(set(by_id) - set(expected_ids))
        if missing_ids:
            errors.append(f"visual_argument_plan 缺少小问: {','.join(missing_ids)}")
        if extra_ids:
            errors.append(f"visual_argument_plan 含未登记小问: {','.join(extra_ids)}")

    all_slots: dict[str, dict[str, Any]] = {}
    slot_to_figures: dict[str, list[str]] = {}
    hard_slot_ids: set[str] = set()
    required_figure_slot_ids: set[str] = set()
    table_slot_ids: set[str] = set()
    recommended_unfilled: list[str] = []
    profile_report: dict[str, Any] = {}
    for qid in expected_ids:
        item = by_id.get(qid, {})
        if not _valid_text(item.get("reader_question")):
            errors.append(f"{qid} 缺少 reader_question")
        if not isinstance(item.get("visual_audit"), list):
            errors.append(f"{qid} 缺少 visual_audit 列表")
            audit = []
        else:
            audit = item["visual_audit"]
        category_items: dict[str, dict[str, Any]] = {}
        for index, slot in enumerate(audit):
            label = f"{qid}.visual_audit[{index}]"
            slot_errors, slot_warnings, normalized = _validate_slot(slot, label)
            errors.extend(slot_errors)
            warnings.extend(slot_warnings)
            if reader_protocol_enabled:
                errors.extend(validate_visual_representation(slot, label))
            if normalized is None:
                continue
            if evidence_packet is not None:
                _validate_slot_information_units(slot, normalized, packet_units, label, errors)
            category = normalized["category"]
            if category not in VISUAL_AUDIT_CATEGORIES:
                errors.append(f"{label} category 不在固定视觉审计类别中")
            elif category in category_items:
                errors.append(f"{qid} category 重复: {category}")
            else:
                category_items[category] = normalized
            slot_id = normalized["slot_id"]
            if slot_id in all_slots:
                errors.append(f"slot_id 重复: {slot_id}")
            else:
                all_slots[slot_id] = normalized
                slot_to_figures[slot_id] = normalized["figure_ids"]
        missing_categories = sorted(set(VISUAL_AUDIT_CATEGORIES) - set(category_items))
        if missing_categories:
            errors.append(f"{qid} visual_audit 缺少类别: {','.join(missing_categories)}")
        profile = _infer_visual_profile(cards.get(qid), item)
        profile_report[qid] = profile
        if profile["declared_complexity"] and profile["declared_complexity"] == "simple" and profile["complexity"] == "complex":
            errors.append(f"{qid} 声明为 simple，但上游模型事实推断为 complex")
        for category in VISUAL_AUDIT_CATEGORIES:
            slot = category_items.get(category)
            if slot is None:
                continue
            disposition = slot["disposition"]
            if category in profile["hard_categories"]:
                hard_slot_ids.add(slot["slot_id"])
                if category == "result_evidence" and disposition == "table_justified":
                    table_slot_ids.add(slot["slot_id"])
                elif disposition != "required":
                    errors.append(f"{qid}.{category} 是硬性视觉义务，disposition 必须为 required")
                else:
                    required_figure_slot_ids.add(slot["slot_id"])
            if disposition == "recommended" and not slot["figure_ids"]:
                recommended_unfilled.append(slot["slot_id"])

    global_slots = plan.get("global_visual_slots")
    needs_global = len(expected_ids) > 1 or scope.get("cross_question_dependencies") is True
    if needs_global and not isinstance(global_slots, list):
        errors.append("多小问或存在跨问接口时必须提供 global_visual_slots")
        global_slots = []
    if not isinstance(global_slots, list):
        global_slots = []
    global_story_found = False
    for index, slot in enumerate(global_slots):
        label = f"global_visual_slots[{index}]"
        slot_errors, slot_warnings, normalized = _validate_slot(slot, label)
        errors.extend(slot_errors)
        warnings.extend(slot_warnings)
        if reader_protocol_enabled:
            errors.extend(validate_visual_representation(slot, label))
        if normalized is None:
            continue
        if evidence_packet is not None:
            _validate_slot_information_units(slot, normalized, packet_units, label, errors)
        slot_id = normalized["slot_id"]
        if slot_id in all_slots:
            errors.append(f"slot_id 重复: {slot_id}")
        else:
            all_slots[slot_id] = normalized
            slot_to_figures[slot_id] = normalized["figure_ids"]
        if normalized["category"] == "global_story":
            global_story_found = True
            if needs_global and normalized["disposition"] != "required":
                errors.append("多小问或跨问接口的 global_story 必须为 required")
            if needs_global:
                hard_slot_ids.add(slot_id)
                required_figure_slot_ids.add(slot_id)
    if needs_global and not global_story_found:
        errors.append("多小问或跨问接口必须有一个 category=global_story 的全局视觉槽位")

    figure_to_slots: dict[str, list[str]] = {}
    all_planned_figures: set[str] = set()
    for slot_id, figure_ids in slot_to_figures.items():
        for figure_id in figure_ids:
            all_planned_figures.add(figure_id)
            figure_to_slots.setdefault(figure_id, []).append(slot_id)
    for figure_id, slot_ids in figure_to_slots.items():
        if len(slot_ids) > 1:
            errors.append(f"图表 {figure_id} 被重复复用于多个视觉槽位: {','.join(slot_ids)}")

    metrics = {
        "required_visual_slots": len(hard_slot_ids),
        "required_figure_slots": len(required_figure_slot_ids),
        "planned_figure_count": len(all_planned_figures),
        "table_justified_slots": len(table_slot_ids),
        "recommended_unfilled": len(recommended_unfilled),
        "inferred_profiles": profile_report,
    }
    summary = plan.get("coverage_summary")
    if not isinstance(summary, dict):
        errors.append("visual_argument_plan 缺少 coverage_summary")
    else:
        for key in ("required_visual_slots", "required_figure_slots", "planned_figure_count"):
            if key not in summary:
                errors.append(f"coverage_summary 缺少 {key}")
            elif summary.get(key) != metrics[key]:
                errors.append(f"coverage_summary.{key} 与实际槽位统计不一致（声明 {summary.get(key)}，实际 {metrics[key]}）")
    if recommended_unfilled:
        warnings.append("存在未落实的 recommended 视觉槽位: " + ",".join(recommended_unfilled))
    if metrics["required_figure_slots"] == 0 and needs_global:
        errors.append("多小问视觉计划不得没有 required figure slot")

    if stage != "plan":
        entries = _registry_list(registry)
        if not entries:
            errors.append("生成或交付阶段必须提供非空 figure registry")
        registry_by_id: dict[str, dict[str, Any]] = {}
        for index, entry in enumerate(entries):
            figure_id = _text(entry.get("figure_id") or entry.get("id"))
            if not figure_id:
                errors.append(f"figure_registry[{index}] 缺少 figure_id")
                continue
            if figure_id in registry_by_id:
                errors.append(f"figure_registry 重复 figure_id: {figure_id}")
            registry_by_id[figure_id] = entry
            if figure_id not in figure_to_slots:
                errors.append(f"figure_registry 图表 {figure_id} 未绑定已批准的视觉槽位")
            slot_ids = _strings(entry.get("visual_slot_ids"))
            expected_slot_ids = figure_to_slots.get(figure_id, [])
            if not slot_ids:
                errors.append(f"figure_registry 图表 {figure_id} 缺少 visual_slot_ids")
            elif set(slot_ids) != set(expected_slot_ids):
                errors.append(f"figure_registry 图表 {figure_id} 的 visual_slot_ids 与视觉计划不一致")
            if not _valid_text(entry.get("claim")):
                errors.append(f"figure_registry 图表 {figure_id} 缺少 claim")
            if not _valid_text(entry.get("reader_takeaway")):
                errors.append(f"figure_registry 图表 {figure_id} 缺少 reader_takeaway")
            expected_routes = {
                all_slots[slot_id].get("generation_route")
                for slot_id in expected_slot_ids
                if slot_id in all_slots and all_slots[slot_id].get("generation_route")
            }
            expected_template_statuses = {
                all_slots[slot_id].get("template_status")
                for slot_id in expected_slot_ids
                if slot_id in all_slots and all_slots[slot_id].get("template_status")
            }
            if len(expected_routes) == 1:
                registry_route = _text(entry.get("generator") or entry.get("generated_by")).lower()
                expected_route = next(iter(expected_routes))
                if registry_route != expected_route:
                    errors.append(
                        f"figure_registry 图表 {figure_id} 的 generator 必须与视觉计划路由一致（"
                        f"计划 {expected_route}，登记 {registry_route or '缺失'}）"
                    )
                declared_route = _text(entry.get("generation_route")).lower()
                if declared_route and declared_route != registry_route:
                    errors.append(
                        f"figure_registry 图表 {figure_id} 的 generation_route 必须与 generator 一致"
                    )
            if len(expected_template_statuses) == 1:
                registry_template_status = _text(entry.get("template_status")).lower()
                expected_template_status = next(iter(expected_template_statuses))
                if registry_template_status != expected_template_status:
                    errors.append(
                        f"figure_registry 图表 {figure_id} 的 template_status 必须与视觉计划一致（"
                        f"计划 {expected_template_status}，登记 {registry_template_status or '缺失'}）"
                    )
            expected_slots = [
                all_slots[visual_slot_id]
                for visual_slot_id in expected_slot_ids
                if visual_slot_id in all_slots
            ]
            _validate_registry_template_execution(
                entry,
                expected_slots,
                label=f"figure_registry 图表 {figure_id}",
                project_root=project_root,
                errors=errors,
            )
            if evidence_packet is not None:
                expected_unit_ids = sorted({
                    unit_id
                    for visual_slot_id in expected_slot_ids
                    for unit_id in all_slots.get(visual_slot_id, {}).get("information_unit_ids", [])
                })
                expected_densities = {
                    all_slots[visual_slot_id].get("density_profile")
                    for visual_slot_id in expected_slot_ids
                    if visual_slot_id in all_slots and all_slots[visual_slot_id].get("density_profile")
                }
                expected_density = next(iter(expected_densities)) if len(expected_densities) == 1 else None
                _validate_registry_information_units(
                    entry,
                    expected_unit_ids,
                    expected_density,
                    packet_units,
                    f"figure_registry 图表 {figure_id}",
                    errors,
                )
        for figure_id in all_planned_figures:
            if figure_id not in registry_by_id:
                errors.append(f"视觉计划图表 {figure_id} 未在 figure_registry 中登记")
        for slot_id in required_figure_slot_ids:
            for figure_id in slot_to_figures.get(slot_id, []):
                if figure_id not in registry_by_id:
                    errors.append(f"required 视觉槽位 {slot_id} 缺少已登记图表 {figure_id}")

    return {
        "status": "BLOCK" if errors else ("WARN" if warnings else "PASS"),
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
    }


def check(plan: dict[str, Any], root: Path, stage: str, tex: Path | None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    subproblems = (plan.get("content_budget") or {}).get("subproblems") or []
    registry_path = find(root, ("figure_registry.json", "figure_registry.yaml"))
    entries = registry_entries(registry_path) if stage != "blueprint" else {}
    required_count = 0
    for item in subproblems:
        if not isinstance(item, dict):
            errors.append("content_budget.subproblems 存在非对象条目")
            continue
        qid = str(item.get("id", "未知小问"))
        decision = item.get("visual_decision")
        if not isinstance(decision, dict):
            errors.append(f"{qid} 缺少 visual_decision")
            continue
        status = str(decision.get("status", "")).lower()
        rationale = str(decision.get("rationale", "")).strip()
        visuals = item.get("visual_evidence") or []
        if status not in {"required", "table_justified", "not_applicable"}:
            errors.append(f"{qid}.visual_decision.status 必须为 required/table_justified/not_applicable")
            continue
        if status != "required" and not rationale:
            errors.append(f"{qid} 不出主图必须给出可核验 rationale")
        if status == "required":
            required_count += 1
            primary = [value for value in visuals if isinstance(value, dict) and value.get("role") == "primary"]
            if not primary:
                errors.append(f"{qid} 声明需要主视觉证据但没有 role=primary 图")
        for index, visual in enumerate(visuals):
            if not isinstance(visual, dict):
                errors.append(f"{qid}.visual_evidence[{index}] 必须是对象")
                continue
            missing = [key for key in ("id", "claim", "role", "source", "target_section")
                       if not str(visual.get(key, "")).strip()]
            if missing:
                errors.append(f"{qid}.visual_evidence[{index}] 缺少 {','.join(missing)}")
            if stage != "blueprint" and status == "required":
                figure_id = str(visual.get("figure_id", "")).strip()
                if not figure_id or figure_id not in entries:
                    errors.append(f"{qid} 图表登记缺少 {figure_id or visual.get('id')}")
                elif str(entries[figure_id].get("qa_status", "")).lower() not in {"pass", "reviewed"}:
                    errors.append(f"{qid} 图表 {figure_id} 未完成 QA")
                else:
                    source = str(visual.get("source", "")).strip()
                    registered_sources = entries[figure_id].get("source_files", [])
                    if isinstance(registered_sources, str):
                        registered_sources = [registered_sources]
                    if source and source not in {str(item) for item in registered_sources or []}:
                        errors.append(f"{qid} 图表 {figure_id} 的登记数据源与 visual_evidence.source 不一致")
    visual_plan_path = find(root, ("visual_argument_plan.yaml",))
    visual_packet_path = find(root, ("visual_evidence_packet.yaml",))
    visual_plan_report: dict[str, Any] | None = None
    visual_packet: dict[str, Any] | None = None
    visual_policy = plan.get("visual_policy") or {}
    if visual_plan_path is None:
        if visual_policy.get("mode") == "reader_first_coverage":
            errors.append("visual_policy.mode=reader_first_coverage 时必须提供 visual_argument_plan.yaml")
    else:
        try:
            visual_plan = load(visual_plan_path)
            model_card_path = find(root, ("model_summary_cards.yaml",))
            model_cards = load(model_card_path) if model_card_path else None
            registry_payload = load(registry_path) if registry_path and stage != "blueprint" else None
            if visual_packet_path is not None:
                visual_packet = load(visual_packet_path)
            expected_ids = [str(item.get("id")) for item in subproblems if isinstance(item, dict) and str(item.get("id", "")).strip()]
            visual_plan_report = validate_visual_argument_plan(
                visual_plan,
                expected_subproblems=expected_ids or None,
                model_cards=model_cards,
                evidence_packet=visual_packet,
                registry=registry_payload,
                stage="plan" if stage == "blueprint" else "final",
                project_root=root,
            )
            errors.extend(f"视觉论证计划: {item}" for item in visual_plan_report["errors"])
            warnings.extend(f"视觉论证计划: {item}" for item in visual_plan_report["warnings"])
        except (OSError, ValueError, yaml.YAMLError if yaml else ValueError) as exc:
            errors.append(f"visual_argument_plan 不可读: {exc}")
    if stage == "paper" and tex and tex.is_file():
        text = tex.read_text(encoding="utf-8", errors="replace")
        figures = len(re.findall(r"\\begin\s*\{figure\}", text))
        tables = len(re.findall(r"\\begin\s*\{table\}", text))
        ratio = float(((plan.get("visual_policy") or {}).get("table_to_figure_review_ratio", 1.5)))
        if required_count >= 2 and (figures == 0 or tables > figures * ratio):
            warnings.append(f"VISUAL_BALANCE_REVIEW: 主图需求={required_count}，正文图/表={figures}/{tables}")
    return {"schema_version": "1.0", "status": "BLOCK" if errors else ("WARN" if warnings else "PASS"),
            "errors": errors, "warnings": warnings, "registry": str(registry_path) if registry_path else None,
            "required_visual_subproblems": required_count,
            "visual_argument_plan": visual_plan_report}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--stage", choices=("blueprint", "solution", "paper"), default="blueprint")
    parser.add_argument("--plan", default=None)
    parser.add_argument("--tex", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    plan_path = Path(args.plan).resolve() if args.plan else find(root, ("content_budget_plan.yaml", "content_budget_plan.json"))
    try:
        if plan_path is None:
            raise ValueError("缺少 content_budget_plan.yaml/json")
        tex = Path(args.tex).resolve() if args.tex else None
        report = check(load(plan_path), root, args.stage, tex)
        report["plan_path"] = str(plan_path)
        code = 1 if report["status"] == "BLOCK" else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report, code = {"schema_version": "1.0", "status": "BLOCK", "errors": [str(exc)], "warnings": []}, 1
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        output = Path(args.out).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
