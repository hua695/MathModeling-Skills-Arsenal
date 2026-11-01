#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the project-side control record for full-contest-harness."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from validation_router import validate_control_validation  # noqa: E402
from figure_registry import layout_validation_errors  # noqa: E402
from check_visual_evidence import (  # noqa: E402
    validate_visual_argument_plan,
    validate_visual_evidence_packet,
)
from check_h5_result_traceability import (  # noqa: E402
    validate_h5_result_traceability,
)
from check_reader_evidence import (  # noqa: E402
    READER_EVIDENCE_VERSION,
    validate_author_chapter,
    validate_model_card,
    validate_protocol_version,
    validate_result_card,
)


class _UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently keeping the last value."""


def _construct_unique_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode,
                              deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"found duplicate key: {key!r}", key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def _reader_protocol_state(control: dict[str, Any] | None, payload: dict[str, Any],
                           label: str, failures: list[str]) -> bool:
    """Activate reader-evidence checks from the control file, not agent self-declaration."""
    control_enabled = isinstance(control, dict) and control.get("reader_evidence_protocol") == READER_EVIDENCE_VERSION
    failures.extend(validate_protocol_version(payload, label))
    marker = payload.get("reader_evidence_version")
    if control_enabled and marker != READER_EVIDENCE_VERSION:
        failures.append(f"{label}: 控制文件已启用 reader_evidence_protocol，必须登记 reader_evidence_version={READER_EVIDENCE_VERSION}")
    return control_enabled or marker == READER_EVIDENCE_VERSION


NODES = tuple(f"H{index}" for index in range(10))
REVIEW_NODES = tuple(f"H{index}" for index in range(2, 10))
ROLE_BY_NODE = {
    "H0": "主 agent", "H1": "题意理解 agent", "H2": "主 agent", "H3": "主 agent",
    "H4": "主 agent", "H5": "解题 agent", "H6": "验证 agent", "H7": "图表 agent",
    "H8": "论文 agent", "H9": "主 agent",
}
AGENT_NODES = {"H1", "H5", "H6", "H7", "H8"}
CONTROLLER_NODES = set(NODES) - AGENT_NODES
REQUIRED_INPUT_BY_NODE = {
    "H5": [
        "problem_statement.md", "literature_sources.yaml", "method_transfer_map.json",
        "model_blueprint.yaml", "model_contract.yaml",
    ],
    "H6": [
        "problem_statement.md", "validation_contract.yaml", "model_summary_cards.yaml",
        "h6_verification_scope.yaml", "result_interpretation_cards.yaml",
        "visual_evidence_packet.yaml",
    ],
    "H7": [
        "problem_statement.md", "chart_requirements.yaml", "model_summary_cards.yaml",
        "visual_evidence_packet.yaml",
    ],
    "H8": [
        "problem_statement.md", "paper_narrative.yaml", "result_interpretation_cards.yaml",
        "paper_argument_blueprint.yaml", "paper_material_readiness.yaml", "paper_claim_coverage.yaml",
        "chart_requirements.yaml", "visual_argument_plan.yaml", "abstract_argument_card.yaml",
    ],
}
AGENT_RUNTIME_BY_NODE = {
    "H1": {"model": "gpt-5.6-terra", "reasoning_effort": "medium"},
    "H5": {"model": "gpt-5.6-sol", "reasoning_effort": "high"},
    "H6": {"model": "gpt-5.6-sol", "reasoning_effort": "high"},
    "H7": {"model": "gpt-5.6-terra", "reasoning_effort": "medium"},
    "H8": {"model": "gpt-5.6-sol", "reasoning_effort": "high"},
}
STAGE_PREDECESSORS = {
    "H5": ("H3",),  # H4 已并入 H5，前驱只需 H3
    "H6": ("H5",),
    "H7": ("H6",),
    "H8": ("H7",),
    "H9": ("H8",),
}
TASK_CARD_FIELDS = (
    "task_id", "node_id", "owner_role", "objective", "inputs", "scope",
    "required_outputs", "verification", "prohibited_actions", "evidence_handoff", "model", "reasoning_effort",
)
REVIEW_FIELDS = (
    "node_id", "summary", "important_artifacts", "checks", "requested_decision", "proposed_next_node",
)
REQUIRED_ARTIFACT_COUNT = {"H6": 1, "H7": 1, "H9": 1}
NODE_STATUSES = {"not_started", "draft", "review_pending", "approved", "frozen", "evidence_gap", "stale"}

STATUS_TRANSITIONS: dict[str, set[str]] = {
    "not_started": {"draft"},
    "draft": {"review_pending"},
    "review_pending": {"approved", "evidence_gap"},
    "evidence_gap": {"draft"},
    "approved": {"frozen"},
    "frozen": {"stale"},
    "stale": {"review_pending"},
}


def validate_status_transition(from_status: str, to_status: str) -> tuple[bool, str]:
    """Validate a single node status transition against the fixed table.

    Returns (ok, message).  Any transition not listed in STATUS_TRANSITIONS
    is rejected.  PAUSE is a runtime result, not a node status.
    """
    if from_status not in STATUS_TRANSITIONS:
        return False, f"unknown source status: {from_status}"
    if to_status not in STATUS_TRANSITIONS[from_status]:
        return False, f"illegal status transition: {from_status} -> {to_status} (allowed: {sorted(STATUS_TRANSITIONS[from_status])})"
    return True, ""


def _validate_status_history(root: Path, control: dict[str, Any], through: str,
                              missing: list[str], failures: list[str]) -> set[str]:
    """P1-01: Validate status transition history for all nodes.

    Reads .contest/status_history.yaml, verifies each transition is legal,
    and returns the set of nodes that have reached 'approved' or 'frozen'
    status.  Nodes without history or with illegal transitions are reported.
    """
    history_path = root / ".contest" / "status_history.yaml"
    approved_nodes: set[str] = set()
    if not history_path.is_file():
        missing.append("缺少 .contest/status_history.yaml（状态转移历史，用于校验节点状态变更合法性）")
        return approved_nodes
    try:
        history = load_mapping(history_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures.append(f"status_history 不可读: {exc}")
        return approved_nodes
    records = history.get("transitions") or history.get("records")
    if not isinstance(records, list) or not records:
        failures.append("status_history 必须含非空 transitions 列表")
        return approved_nodes
    # 按时间排序
    def _sort_key(rec: dict) -> str:
        return str(rec.get("timestamp", ""))
    try:
        records_sorted = sorted(records, key=_sort_key)
    except Exception:
        records_sorted = records
    # 跟踪每个节点的当前状态
    node_current: dict[str, str] = {}
    for idx, rec in enumerate(records_sorted):
        if not isinstance(rec, dict):
            failures.append(f"status_history.transitions[{idx}] 必须为对象")
            continue
        node_id = rec.get("node_id")
        from_status = rec.get("from_status")
        to_status = rec.get("to_status")
        timestamp = rec.get("timestamp")
        if not isinstance(node_id, str) or not node_id.strip():
            failures.append(f"status_history.transitions[{idx}] 缺少 node_id")
            continue
        if not isinstance(from_status, str) or not from_status.strip():
            failures.append(f"status_history.transitions[{idx}] ({node_id}) 缺少 from_status")
            continue
        if not isinstance(to_status, str) or not to_status.strip():
            failures.append(f"status_history.transitions[{idx}] ({node_id}) 缺少 to_status")
            continue
        if not isinstance(timestamp, str) or not timestamp.strip():
            failures.append(f"status_history.transitions[{idx}] ({node_id}) 缺少 timestamp")
        else:
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                failures.append(f"status_history.transitions[{idx}] ({node_id}) timestamp 必须为 ISO 格式")
        # 校验状态转移合法性
        ok, msg = validate_status_transition(from_status, to_status)
        if not ok:
            failures.append(f"status_history: {node_id} 非法状态转移 {from_status} -> {to_status}: {msg}")
        # 校验 from_status 与当前状态一致
        if node_id in node_current and node_current[node_id] != from_status:
            failures.append(f"status_history: {node_id} 状态不连续（当前 {node_current[node_id]}，记录 from_status {from_status}）")
        node_current[node_id] = to_status
        if to_status in ("approved", "frozen"):
            approved_nodes.add(node_id)
    # 校验 --through 不超过已批准节点
    through_index = NODES.index(through) if through in NODES else len(NODES)
    for i, node_id in enumerate(NODES):
        if i > through_index:
            break
        if node_id in ("H0", "H4") or node_id not in node_current:  # H4已并入H5，跳过
            continue
        if node_current.get(node_id) not in ("approved", "frozen"):
            failures.append(f"status_history: 节点 {node_id} 当前状态为 {node_current.get(node_id)}，未达到 approved/frozen，不能通过 H{through_index}")
    return approved_nodes


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def validate_dispatch_order(root: Path, control: dict[str, Any], through: str,
                            missing: list[str], failures: list[str]) -> None:
    """Require every agent dispatch to follow its frozen upstream approvals."""
    if NODES.index(through) < NODES.index("H5"):
        return
    history_path = root / ".contest" / "status_history.yaml"
    if not history_path.is_file():
        return
    try:
        history = load_mapping(history_path)
    except (OSError, ValueError, yaml.YAMLError):
        return
    approved_at: dict[str, datetime] = {}
    for item in history.get("transitions", history.get("records", [])) or []:
        if not isinstance(item, dict) or item.get("to_status") not in {"approved", "frozen"}:
            continue
        timestamp = _parse_timestamp(item.get("timestamp"))
        node_id = item.get("node_id")
        if timestamp is not None and isinstance(node_id, str):
            approved_at[node_id] = max(timestamp, approved_at.get(node_id, timestamp))

    records = control.get("dispatch_records", [])
    if not isinstance(records, list):
        return
    through_index = NODES.index(through)
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        node_id = record.get("node_id")
        if (control.get("visual_workflow") in {"writer_first_draft", "chapter_parallel"} and node_id == "H8"
                and record.get("dispatch_kind") == "writer_preparation"):
            # This explicit H8-role preparation is independently gated by H6 and
            # H7_WRITING_PLAN; it does not advance the formal H8 node.
            continue
        if node_id not in STAGE_PREDECESSORS or node_id not in NODES[:through_index + 1]:
            continue
        dispatched_at = _parse_timestamp(record.get("dispatched_at"))
        if dispatched_at is None:
            continue
        for predecessor in STAGE_PREDECESSORS[node_id]:
            predecessor_time = approved_at.get(predecessor)
            if predecessor_time is None:
                missing.append(f"dispatch_records[{index}]: {node_id} 缺少前置节点 {predecessor} 的 approved/frozen 记录")
            elif dispatched_at < predecessor_time:
                failures.append(
                    f"dispatch_records[{index}]: {node_id} 在前置节点 {predecessor} 获批前派发，"
                    f"违反节点顺序（派发 {dispatched_at.isoformat()}，批准 {predecessor_time.isoformat()}）"
                )


def _require_node_file(root: Path, node: dict[str, Any], field: str,
                       label: str, missing: list[str]) -> None:
    raw_path = node.get(field) if isinstance(node, dict) else None
    if not isinstance(raw_path, str) or not raw_path.strip():
        missing.append(f"{label}: 缺少 {field} 文件登记")
        return
    path = resolve_project_path(root, raw_path)
    if path is None or not path.is_file():
        missing.append(f"{label}: {field} 文件不存在: {raw_path}")
    elif path.stat().st_size == 0:
        missing.append(f"{label}: {field} 文件为空: {raw_path}")


def validate_literature_gate(root: Path, nodes: dict[str, Any], through: str,
                             missing: list[str], failures: list[str]) -> None:
    """Enforce user-returned literature before H5 route selection and solving (H4已并入H5)."""
    if NODES.index(through) < NODES.index("H3"):
        return
    h3 = nodes.get("H3", {})
    _require_node_file(root, h3, "literature_request", "H3", missing)
    _require_node_file(root, h3, "literature_agent_prompt", "H3", missing)
    if NODES.index(through) >= NODES.index("H5"):
        _require_node_file(root, h3, "literature_sources", "H3", missing)
        h3_status = h3.get("status") if isinstance(h3, dict) else None
        if h3_status not in {"approved", "frozen"}:
            missing.append(f"H5: 文献输入门尚未获批，H3 status 必须为 approved/frozen（当前: {h3_status}）")
    if NODES.index(through) >= NODES.index("H5"):
        h5 = nodes.get("H5", {})
        for field in ("method_transfer_map", "model_blueprint", "chart_requirements"):
            _require_node_file(root, h5, field, "H5", missing)
REQUIRED_PRELOAD = {
    "H1": ["problem_statement.md"],
    "H5": ["problem_statement.md", "references/warmup/h5_solver_warmup.md"],
    "H6": ["problem_statement.md", "references/warmup/h6_verifier_warmup.md"],
    "H7": ["problem_statement.md", "references/warmup/h7_figure_warmup.md"],
    "H8": [
        "problem_statement.md",
        "references/warmup/h8_writer_warmup.md",
        "references/h8_writer_first_protocol.md",
        "references/model_summary_protocol.md",
    ],
}
READER_EVIDENCE_PRELOAD = "references/paper_author_evidence_protocol.md"
DISPATCH_FIELDS = (
    "task_id", "node_id", "owner_role", "agent_instance_id", "model", "reasoning_effort",
    "dispatched_at", "task_card_path", "task_card_sha256",
)
MATERIAL_FIELDS = (
    "problem_mapping", "assumptions", "symbols", "derivation", "algorithm_and_parameters",
    "quantified_results", "validation", "figures_or_tables", "literature_use", "conclusion_and_boundary",
)
MATERIAL_OWNER = {
    "problem_mapping": "H5", "assumptions": "H5", "symbols": "H5", "derivation": "H5",
    "algorithm_and_parameters": "H5", "quantified_results": "H5", "validation": "H6",
    "figures_or_tables": "H7", "literature_use": "H6", "conclusion_and_boundary": "H5",
}
EVIDENCE_MATRIX_FIELDS = (*MATERIAL_FIELDS, "sensitivity_or_robustness")
EVIDENCE_MATRIX_STATUSES = {"ready", "missing", "blocked", "not_applicable"}
INTERFACE_CHECKS = (
    "shared_symbols", "units", "data_versions", "upstream_downstream_fields", "time_scales",
    "parameters", "cross_question_constraints", "conclusions", "provenance",
)
CLAIM_EVIDENCE = {
    "conclusion": {"quantified_results", "validation"},
    "quantified_result": {"quantified_results"},
    "figure_claim": {"figures_or_tables", "quantified_results"},
    "citation_use": {"literature_use"},
}
QUESTION_NUMBERED_SECTIONS = ("模型建立", "模型求解与结果分析")
PAPER_SPINE_LIST_FIELDS = ("core_chapters", "support_chapters", "chapter_order")
CHAPTER_RELATION_FIELDS = ("chapter_role", "reads_from", "feeds_to", "new_claims_allowed", "handoff_question")

# 节点 → 绑定子 skill 契约（能力下沉后由子 skill 承接，节点必须登记调用）
SKILL_BINDING_BY_NODE = {
    "H5": {"must_call": ["math-model-selector"], "at_least_one": ["heuristic-algorithms", "data-science-stack", "pyomo"]},  # H4已并入H5，math-model-selector 为阶段一必调
    "H6": {"must_call": ["data-science-stack"]},
    "H7": {"at_least_one": ["scipilot-figure-skill", "tikz-scientific-figures"]},
    "H8": {"must_call": ["academic-writing", "mathmodel-latex-skill"]},
    "H9": {"must_call": ["bzd-review-paper", "mathmodel-latex-skill"]},
}
VALID_BINDING_SKILLS = {
    "math-model-selector", "heuristic-algorithms", "data-science-stack", "pyomo",
    "academic-writing", "humanizer-zh", "mathmodel-latex-skill", "latex-paper-en",
    "scipilot-figure-skill", "modelviz", "tikz-scientific-figures",
    "drawio-diagram", "bzd-review-paper", "web-access", "word-document", "math-modeling",
}

# 图表路由契约（figure_policy.md 硬约束）：kind → 允许的 generator
FIGURE_KIND_ROUTES = {
    "data": ("modelviz",),  # SciPilot→ModelViz→SciPilot 链，semantic_qa=scipilot-figure-skill
    "flowchart": ("tikz-scientific-figures",),
    "roadmap": ("tikz-scientific-figures",),
    "schematic": ("tikz-scientific-figures",),
    "drawio": ("drawio-diagram",),  # 仅显式请求，user_requested=true
}


def _string_list(value: Any) -> list[str]:
    """Return non-empty string entries while preserving declared order."""
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _spine_signature(spine: dict[str, Any]) -> dict[str, Any]:
    """Normalize a paper spine for exact cross-artifact comparison."""
    edges = []
    for edge in spine.get("chapter_edges", []):
        if isinstance(edge, dict):
            edges.append({
                "from": edge.get("from"),
                "to": edge.get("to"),
                "relation": edge.get("relation"),
                "handoff_question": edge.get("handoff_question"),
            })
    return {
        "core_chapters": _string_list(spine.get("core_chapters")),
        "support_chapters": _string_list(spine.get("support_chapters")),
        "chapter_order": _string_list(spine.get("chapter_order")),
        "chapter_edges": edges,
    }


def _validate_paper_spine(spine: Any, label: str, failures: list[str],
                          question_ids: set[str] | None = None) -> dict[str, Any] | None:
    """Validate the single source of truth for paper chapter order and handoffs."""
    if not isinstance(spine, dict):
        failures.append(f"{label}: 必须登记 paper_spine 对象")
        return None
    for field in PAPER_SPINE_LIST_FIELDS:
        if not isinstance(spine.get(field), list):
            failures.append(f"{label}: 缺少或无效 {field} 列表")
    if not isinstance(spine.get("chapter_edges"), list):
        failures.append(f"{label}: 缺少或无效 chapter_edges 列表")
    signature = _spine_signature(spine)
    for field in ("core_chapters", "chapter_order"):
        if not signature[field]:
            failures.append(f"{label}: {field} 必须为非空列表")
    for field in PAPER_SPINE_LIST_FIELDS:
        declared = _string_list(spine.get(field))
        if len(declared) != len(spine.get(field, [])):
            failures.append(f"{label}: {field} 只能包含非空字符串")
        if len(declared) != len(set(declared)):
            failures.append(f"{label}: {field} 不得重复")
    core = set(signature["core_chapters"])
    support = set(signature["support_chapters"])
    order = signature["chapter_order"]
    if core & support:
        failures.append(f"{label}: core_chapters 与 support_chapters 不得重叠")
    declared = core | support
    if declared != set(order):
        failures.append(f"{label}: core/support chapters 必须完整覆盖 chapter_order，不能有孤立章节")
    if question_ids is not None and question_ids != core:
        failures.append(f"{label}: core_chapters 必须逐一覆盖所有建模问题，不能遗漏或多出章节")

    edge_pairs: set[tuple[str, str]] = set()
    for index, edge in enumerate(spine.get("chapter_edges", [])):
        edge_label = f"{label}.chapter_edges[{index}]"
        if not isinstance(edge, dict):
            failures.append(f"{edge_label}: 必须为对象")
            continue
        for field in ("from", "to", "relation", "handoff_question"):
            if not isinstance(edge.get(field), str) or not edge[field].strip():
                failures.append(f"{edge_label}: 缺少 {field}")
        source = edge.get("from")
        target = edge.get("to")
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        pair = (source, target)
        if source == target:
            failures.append(f"{edge_label}: 不得建立自环")
        if source not in order or target not in order:
            failures.append(f"{edge_label}: from/to 必须位于 chapter_order")
        if pair in edge_pairs:
            failures.append(f"{edge_label}: chapter edge 重复")
        edge_pairs.add(pair)
    for previous, current in zip(order, order[1:]):
        if (previous, current) not in edge_pairs:
            failures.append(f"{label}: 缺少相邻章节 {previous} → {current} 的 chapter_edges 承接")
    return signature


def _validate_chapter_relation(label: str, chapter: dict[str, Any], spine: dict[str, Any],
                               failures: list[str], argument_ids: set[str] | None = None) -> None:
    """Validate one chapter's role, neighbors, and allowed claim boundary."""
    for field in CHAPTER_RELATION_FIELDS:
        if field in {"chapter_role", "handoff_question"}:
            if not isinstance(chapter.get(field), str) or not chapter[field].strip():
                failures.append(f"{label}: 缺少 {field}")
        elif not isinstance(chapter.get(field), list):
            failures.append(f"{label}: {field} 必须为列表")
    chapter_id = chapter.get("section_id") or chapter.get("chapter_id")
    if not isinstance(chapter_id, str) or not chapter_id.strip():
        return
    signature = _spine_signature(spine)
    order = signature["chapter_order"]
    if chapter_id not in order:
        failures.append(f"{label}: 章节 {chapter_id} 不在 paper_spine.chapter_order 中")
        return
    expected_role = "core" if chapter_id in set(signature["core_chapters"]) else "support"
    if chapter.get("chapter_role") != expected_role:
        failures.append(f"{label}: chapter_role 必须为 {expected_role}")
    index = order.index(chapter_id)
    reads_from = _string_list(chapter.get("reads_from"))
    feeds_to = _string_list(chapter.get("feeds_to"))
    if any(item not in order for item in reads_from + feeds_to):
        failures.append(f"{label}: reads_from/feeds_to 含不在 paper_spine 中的章节")
    if index == 0:
        if reads_from:
            failures.append(f"{label}: 首章 reads_from 必须为空")
    elif order[index - 1] not in reads_from:
        failures.append(f"{label}: reads_from 必须包含前一章 {order[index - 1]}")
    if index == len(order) - 1:
        if feeds_to:
            failures.append(f"{label}: 末章 feeds_to 必须为空")
    elif order[index + 1] not in feeds_to:
        failures.append(f"{label}: feeds_to 必须包含后一章 {order[index + 1]}")
    allowed_claims = _string_list(chapter.get("new_claims_allowed"))
    if chapter.get("chapter_role") == "support" and allowed_claims:
        failures.append(f"{label}: 支撑章节 new_claims_allowed 必须为空，只能组织已有主张")
    if argument_ids is not None and not set(allowed_claims).issubset(argument_ids):
        failures.append(f"{label}: new_claims_allowed 超出本章 argument_ids")
    if expected_role == "core" and argument_ids is not None and not argument_ids:
        failures.append(f"{label}: 核心章节必须绑定至少一个 argument_id")


def default_control() -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    for node_id in NODES:
        nodes[node_id] = {
            "owner_role": ROLE_BY_NODE[node_id],
            "agent_policy": "required" if node_id in AGENT_NODES else "controller_only",
            "support_agent_policy": "conditional",
            "status": "not_started",
        }
    nodes["H1"]["problem_statement"] = None
    nodes["H1"]["unified_problem_package"] = None
    nodes["H3"].update({
        "literature_request": None,
        "literature_agent_prompt": None,
        "literature_sources": None,
    })
    nodes["H5"].update({
        "method_transfer_map": None,
        "model_blueprint": None,
        "chart_requirements": None,
    })  # H4已并入H5，这些字段由H5阶段一产出
    nodes["H5"]["solver_instance_id"] = None
    nodes["H5"]["paper_narrative"] = None
    nodes["H5"]["validation_contract"] = None
    nodes["H5"]["model_summary_cards"] = None
    nodes["H5"]["result_interpretation_cards"] = None
    nodes["H5"]["run_manifest"] = None
    nodes["H5"]["sensitivity_report"] = None
    nodes["H5"]["visual_evidence_packet"] = None
    nodes["H6"]["global_interface_check"] = None
    nodes["H6"]["model_summary_cards"] = None
    nodes["H6"]["visual_evidence_packet"] = None
    nodes["H7"]["visual_argument_plan"] = None
    nodes["H7"]["visual_plan_review_packet"] = None
    nodes["H7"]["figure_registry"] = None
    nodes["H7"]["visual_evidence_packet"] = None
    nodes["H8"].update({
        "paper_material_readiness": None,
        "evidence_gap_matrix": None,
        "paper_claim_coverage": None,
        "abstract_argument_card": None,
        "abstract_contract_report": None,
        "abstract_written": False,
        "paper_continuity_context": None,
        "model_summary_cards": None,
        "writing_plan": None,
        "writing_plan_sha256": None,
        "plan_review_packet": None,
        "plan_approved": False,
        "writing_started": False,
    })
    for binding_node in SKILL_BINDING_BY_NODE:
        nodes[binding_node].setdefault("skill_invocations", [])
    return {
        "schema_version": "1.0",
        "active_mode": "full-contest-harness",
        "bootstrap": {
            "required_skill": "superpowers:using-superpowers",
            "invocations": [],
        },
        "roles": {
            "主 agent": {"kind": "controller"},
            "题意理解 agent": {"kind": "child"},
            "解题 agent": {"kind": "child"},
            "验证 agent": {"kind": "child"},
            "图表 agent": {"kind": "child"},
            "论文 agent": {"kind": "child"},
        },
        "agent_runtime_routes": AGENT_RUNTIME_BY_NODE,
        "problem_scope": {"subproblems": []},
        "solver_instance_id": None,
        "agent_instances": {},
        "dispatch_records": [],
        "validation": {
            "profile": "competition_fast",
            "change_impact_card": None,
            "full_delivery_gate": "H9",
        },
        "nodes": nodes,
    }


def load_mapping(path: Path) -> dict[str, Any]:
    value = yaml.load(
        path.read_text(encoding="utf-8", errors="replace"), Loader=_UniqueKeyLoader,
    ) or {}
    if not isinstance(value, dict):
        raise ValueError(f"配置必须为对象: {path}")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_abstract_argument_card(path: Path,
                                    expected_question_ids: list[str] | set[str] | None = None) -> dict[str, Any]:
    """Validate the H8A abstract argument card without reading paper prose.

    The card is the planning contract for the final abstract. It records the
    reader contract, the per-question method/result/meaning chain, validation,
    final synthesis, and keywords. Evidence freshness is checked by the
    project-level validator below because only that validator knows the project
    root and the current frozen files.
    """
    issues: list[str] = []
    try:
        card = load_mapping(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return {"passed": False, "issues": [f"摘要论证卡不可读: {exc}"]}
    if card.get("schema_version") != "1.0":
        issues.append("schema_version 必须为 1.0")
    if card.get("status") not in {"draft", "approved"}:
        issues.append("status 必须为 draft 或 approved")
    if card.get("prepared_by") != "academic-writing":
        issues.append("prepared_by 必须为 academic-writing")
    for field in ("reader_contract", "central_thesis", "modeling_line", "final_synthesis"):
        if not isinstance(card.get(field), str) or not card[field].strip():
            issues.append(f"缺少 {field}")
    questions = card.get("questions")
    if not isinstance(questions, list) or not questions:
        issues.append("questions 必须为非空列表")
        questions = []
    seen: set[str] = set()
    for index, question in enumerate(questions):
        label = f"questions[{index}]"
        if not isinstance(question, dict):
            issues.append(f"{label} 必须为对象")
            continue
        for field in ("id", "reader_question", "method", "result", "meaning"):
            if not isinstance(question.get(field), str) or not question[field].strip():
                issues.append(f"{label} 缺少 {field}")
        question_id = question.get("id")
        if isinstance(question_id, str) and question_id.strip():
            if question_id in seen:
                issues.append(f"{label} id 重复: {question_id}")
            seen.add(question_id)
        refs = question.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            issues.append(f"{label} evidence_refs 必须为非空列表")
    if expected_question_ids is not None:
        expected = {item.strip() for item in expected_question_ids if isinstance(item, str) and item.strip()}
        missing = sorted(expected - seen)
        extra = sorted(seen - expected)
        if missing:
            issues.append(f"questions 缺少小问: {','.join(missing)}")
        if extra:
            issues.append(f"questions 含未登记小问: {','.join(extra)}")
    validation = card.get("validation")
    if not isinstance(validation, dict):
        issues.append("validation 必须为对象")
    else:
        for field in ("method", "result"):
            if not isinstance(validation.get(field), str) or not validation[field].strip():
                issues.append(f"validation 缺少 {field}")
    keywords = card.get("keywords")
    if not isinstance(keywords, list) or not 4 <= len(keywords) <= 6 or any(
        not isinstance(item, str) or not item.strip() for item in keywords
    ):
        issues.append("keywords 必须为 4-6 个非空字符串")
    return {"passed": not issues, "issues": issues}


def same_digest(expected: Any, actual: Any) -> bool:
    """Compare SHA-256 values without making hexadecimal case significant."""
    return (
        isinstance(expected, str)
        and isinstance(actual, str)
        and expected.strip().lower() == actual.strip().lower()
    )


def as_relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def resolve_project_path(root: Path, raw: Any) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = (root / raw).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return None
    return path


def _approval_for(log: dict[str, Any], node_id: str) -> dict[str, Any] | None:
    approvals = log.get("approvals", [])
    if not isinstance(approvals, list):
        return None
    matches = [item for item in approvals if isinstance(item, dict) and item.get("gate") == node_id]
    return matches[-1] if matches else None


def _validate_task_card(root: Path, node_id: str, node: dict[str, Any], runtime: dict[str, Any], task_ids: set[str],
                        missing: list[str], failures: list[str]) -> None:
    card_path = resolve_project_path(root, node.get("task_card"))
    if card_path is None or not card_path.is_file():
        missing.append(f"{node_id}: 缺少任务卡")
        return
    try:
        card = load_mapping(card_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures.append(f"{node_id}: 任务卡不可读: {exc}")
        return
    absent = [field for field in TASK_CARD_FIELDS if field not in card]
    if absent:
        failures.append(f"{node_id}: 任务卡缺字段 {','.join(absent)}")
    if card.get("node_id") != node_id or card.get("owner_role") != ROLE_BY_NODE[node_id]:
        failures.append(f"{node_id}: 任务卡节点或角色不匹配")
    if card.get("model") != runtime.get("model") or card.get("reasoning_effort") != runtime.get("reasoning_effort"):
        failures.append(f"{node_id}: 任务卡模型路由不符合节点配置")
    task_id = card.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        failures.append(f"{node_id}: task_id 必须为非空字符串")
    elif task_id in task_ids:
        failures.append(f"{node_id}: task_id 必须在本次运行中唯一")
    else:
        task_ids.add(task_id)
    inputs = card.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        missing.append(f"{node_id}: 任务卡缺少带哈希的输入")
    else:
        for item in inputs:
            if not isinstance(item, dict):
                failures.append(f"{node_id}: 任务卡输入条目无效")
                continue
            input_path = resolve_project_path(root, item.get("path"))
            if input_path is None or not input_path.is_file():
                missing.append(f"{node_id}: 任务卡输入不存在")
                continue
            if not same_digest(item.get("sha256"), digest(input_path)):
                missing.append(f"{node_id}: 任务卡输入哈希已变化")
    if not isinstance(node.get("agent_instance_id"), str) or not node["agent_instance_id"].strip():
        missing.append(f"{node_id}: 缺少实际调度的 agent_instance_id")
    required_inputs = REQUIRED_INPUT_BY_NODE.get(node_id, [])
    if isinstance(required_inputs, str):
        required_inputs = [required_inputs]
    if required_inputs:
        input_paths = [str(item.get("path", "")) for item in (inputs or []) if isinstance(item, dict)]
        for required_input in required_inputs:
            if not any(p.endswith(required_input) for p in input_paths):
                missing.append(f"{node_id}: 任务卡 inputs 必须包含 {required_input}")
    if node_id == "H1":
        input_paths = [str(item.get("path", "")) for item in (inputs or []) if isinstance(item, dict)]
        if not input_paths:
            failures.append("H1: 任务卡 inputs 必须包含原始题面文件（题意理解源头不可追溯）")
        else:
            existing = [p for p in input_paths if resolve_project_path(root, p) and resolve_project_path(root, p).is_file()]
            if not existing:
                failures.append(f"H1: 任务卡 inputs 中无实际存在的原始题面文件: {input_paths}")
    if node_id == "H8":
        # 写哪章读哪章验证：H8 任务卡 inputs 不应直接包含大量原始数据文件
        # 应通过 paper_material_readiness.yaml 的章节素材索引逐章取用
        input_paths = [str(item.get("path", "")) for item in (inputs or []) if isinstance(item, dict)]
        raw_data_exts = (".csv", ".xlsx", ".xls", ".json", ".db", ".pkl", ".parquet", ".tsv")
        raw_data_files = [p for p in input_paths if p.lower().endswith(raw_data_exts)]
        if len(raw_data_files) > 3:
            failures.append(
                f"H8: 任务卡 inputs 直接包含 {len(raw_data_files)} 个原始数据文件（{', '.join(raw_data_files[:3])}...），"
                f"违反'写哪章读哪章'原则——应通过 paper_material_readiness.yaml 章节素材索引逐章取用，"
                f"不应一次性把所有原始数据读进上下文"
            )
        if node.get("writing_started") is True:
            protocol = card.get("authoring_protocol")
            if not isinstance(protocol, dict):
                missing.append("H8: 开始写作的任务卡必须包含 authoring_protocol")
            else:
                if protocol.get("stage") != "H8B":
                    failures.append("H8: 正文写作任务卡 authoring_protocol.stage 必须为 H8B")
                card_ref = protocol.get("chapter_writing_card")
                if not isinstance(card_ref, str) or not card_ref.strip():
                    missing.append("H8: 正文写作任务卡必须绑定 chapter_writing_card")
                elif node.get("active_chapter_card") and card_ref != node.get("active_chapter_card"):
                    failures.append("H8: 任务卡绑定的 chapter_writing_card 与 active_chapter_card 不一致")
                context_ref = protocol.get("paper_continuity_context")
                if not isinstance(context_ref, str) or not context_ref.strip():
                    missing.append("H8: 正文写作任务卡必须绑定 paper_continuity_context")
                elif node.get("paper_continuity_context") and context_ref != node.get("paper_continuity_context"):
                    failures.append("H8: 任务卡绑定的 paper_continuity_context 与节点登记不一致")
                protocol_ref = protocol.get("writer_first_protocol")
                if protocol_ref != "contest-orchestrator/references/h8_writer_first_protocol.md":
                    missing.append("H8: 正文写作任务卡必须绑定 writer-first 协议")
                model_summary_ref = protocol.get("model_summary_protocol")
                if model_summary_ref != "contest-orchestrator/references/model_summary_protocol.md":
                    missing.append("H8: 正文写作任务卡必须绑定 model-summary 协议")
                summary_cards_ref = protocol.get("model_summary_cards")
                if not isinstance(summary_cards_ref, str) or not summary_cards_ref.strip():
                    missing.append("H8: 正文写作任务卡必须绑定 model_summary_cards")
                elif node.get("model_summary_cards") and summary_cards_ref != node.get("model_summary_cards"):
                    failures.append("H8: 任务卡绑定的 model_summary_cards 与节点登记不一致")
                abstract_card_ref = protocol.get("abstract_argument_card")
                if not isinstance(abstract_card_ref, str) or not abstract_card_ref.strip():
                    missing.append("H8: 正文写作任务卡必须绑定 abstract_argument_card")
                elif node.get("abstract_argument_card") and abstract_card_ref != node.get("abstract_argument_card"):
                    failures.append("H8: 任务卡绑定的 abstract_argument_card 与节点登记不一致")
                input_paths = [str(item.get("path", "")) for item in (inputs or []) if isinstance(item, dict)]
                for required_input in (
                    "paper_author_brief.yaml",
                    "chapter_writing_card.yaml",
                    "paper_continuity_context.yaml",
                    "model_summary_cards.yaml",
                    "abstract_argument_card.yaml",
                ):
                    if not any(p.endswith(required_input) for p in input_paths):
                        missing.append(f"H8: 正文写作任务卡 inputs 必须包含 {required_input}")


def _validate_skill_invocations(root: Path, node_id: str, node: dict[str, Any],
                                missing: list[str], failures: list[str]) -> None:
    """节点-子 skill 绑定硬约束：能力下沉后，绑定子 skill 必须到点调用。"""
    if node.get("status") == "not_started":
        return
    binding = SKILL_BINDING_BY_NODE.get(node_id)
    if binding is None:
        return
    invocations = node.get("skill_invocations")
    if not isinstance(invocations, list):
        missing.append(f"{node_id}: 缺少 skill_invocations 登记（该节点绑定子 skill）")
        return
    if not invocations:
        missing.append(f"{node_id}: skill_invocations 为空，未登记任何子 skill 调用")
        return
    called: set[str] = set()
    at_least_one_na: set[str] = set()
    for index, item in enumerate(invocations):
        if not isinstance(item, dict):
            failures.append(f"{node_id}: skill_invocations[{index}] 条目必须为对象")
            continue
        skill = item.get("skill")
        if not isinstance(skill, str) or not skill.strip():
            failures.append(f"{node_id}: skill_invocations[{index}] 缺 skill 名")
            continue
        if skill not in VALID_BINDING_SKILLS:
            failures.append(f"{node_id}: skill_invocations 使用未登记 skill {skill}")
            continue
        if item.get("not_applicable") is True:
            if not str(item.get("reason", "")).strip():
                failures.append(f"{node_id}: skill_invocations[{index}] not_applicable 必须带 reason")
            at_least_one_na.add(skill)
            continue
        called.add(skill)
        evidence_ref = item.get("evidence_ref")
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            missing.append(f"{node_id}: skill_invocations[{index}] {skill} 缺少 evidence_ref（必须指向可追溯产物）")
        else:
            path = resolve_project_path(root, evidence_ref)
            if path is not None and not path.is_file():
                missing.append(f"{node_id}: skill_invocations evidence_ref 文件不存在: {evidence_ref}")
    for skill in binding.get("must_call", []):
        if skill not in called:
            missing.append(f"{node_id}: 必调子 skill {skill} 未调用")
    for skill in binding.get("at_least_one", []):
        if skill in called:
            break
    else:
        if binding.get("at_least_one") and not any(s in at_least_one_na for s in binding["at_least_one"]):
            missing.append(f"{node_id}: 至少调用一个绑定子 skill {','.join(binding['at_least_one'])}，或显式登记 not_applicable+reason")


def _validate_review(root: Path, node_id: str, node: dict[str, Any], log: dict[str, Any],
                     missing: list[str], failures: list[str], *,
                     packet_key: str = "review_packet", approval_gate: str | None = None,
                     packet_node_id: str | None = None, min_artifact_count: int | None = None,
                     label: str | None = None, required_artifact_paths: tuple[Path, ...] = ()) -> None:
    review_label = label or node_id
    gate_id = approval_gate or node_id
    expected_packet_node = packet_node_id or node_id
    packet_path = resolve_project_path(root, node.get(packet_key))
    if packet_path is None or not packet_path.is_file():
        missing.append(f"{review_label}: 缺少 {packet_key}")
        return
    try:
        packet = load_mapping(packet_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures.append(f"{review_label}: {packet_key} 不可读: {exc}")
        return
    absent = [field for field in REVIEW_FIELDS if field not in packet]
    if absent:
        failures.append(f"{review_label}: {packet_key} 缺字段 {','.join(absent)}")
    if packet.get("node_id") != expected_packet_node:
        failures.append(f"{review_label}: {packet_key} 节点不匹配")
    artifact_digests = {as_relative(root, packet_path): digest(packet_path)}
    artifacts = packet.get("important_artifacts", [])
    if not isinstance(artifacts, list):
        failures.append(f"{review_label}: important_artifacts 必须为列表")
    else:
        min_count = REQUIRED_ARTIFACT_COUNT.get(node_id, 0) if min_artifact_count is None else min_artifact_count
        if len(artifacts) < min_count:
            failures.append(f"{review_label}: {packet_key} important_artifacts 至少需要 {min_count} 个可定位产物（当前 {len(artifacts)} 个）")
    checks = packet.get("checks", [])
    if not isinstance(checks, list):
        failures.append(f"{review_label}: checks 必须为列表")
    elif not checks:
        failures.append(f"{review_label}: {packet_key} checks 不能为空（至少登记一项已执行检查）")
    else:
        for item in artifacts:
            if not isinstance(item, dict):
                failures.append(f"{review_label}: 重要产物条目无效")
                continue
            artifact_path = resolve_project_path(root, item.get("path"))
            if artifact_path is None or not artifact_path.is_file():
                missing.append(f"{review_label}: 审查包声明的产物不存在")
                continue
            expected = item.get("sha256")
            actual = digest(artifact_path)
            if not same_digest(expected, actual):
                missing.append(f"{review_label}: 审查包产物哈希已变化")
            artifact_digests[as_relative(root, artifact_path)] = actual
    expected_paths = set()
    for required_path in required_artifact_paths:
        try:
            expected_paths.add(as_relative(root, required_path))
        except ValueError:
            failures.append(f"{review_label}: required_artifact_paths 必须位于项目根目录")
    if expected_paths - set(artifact_digests):
        missing.append(
            f"{review_label}: {packet_key} 必须覆盖指定产物哈希: "
            f"{','.join(sorted(expected_paths - set(artifact_digests)))}"
        )
    approval = _approval_for(log, gate_id)
    if approval is None or approval.get("decision") != "approved":
        missing.append(f"{gate_id}: 等待 user_approval")
        return
    approval_digests = approval.get("artifact_digests")
    if not isinstance(approval_digests, dict) or set(approval_digests) != set(artifact_digests) or any(
        not same_digest(approval_digests.get(key), value) for key, value in artifact_digests.items()
    ):
        missing.append(f"{gate_id}: user_approval 未覆盖当前审查包与产物哈希")


def _validate_h7_figures(root: Path, node: dict[str, Any],
                         missing: list[str], failures: list[str]) -> None:
    registry_raw = node.get("figure_registry") or node.get("figure_decision_card")
    if not isinstance(registry_raw, str) or not registry_raw.strip():
        missing.append("H7: 缺少 figure_registry 或 figure_decision_card（图表决策与登记记录）")
        return
    path = resolve_project_path(root, registry_raw)
    if path is None or not path.is_file():
        missing.append(f"H7: 图表登记文件不存在: {registry_raw}")
        return
    try:
        registry = load_mapping(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures.append(f"H7: 图表登记文件不可读: {exc}")
        return
    if not isinstance(registry, dict):
        failures.append("H7: 图表登记必须为对象")
        return
    figures = registry.get("figures") or registry.get("items") or registry.get("charts")
    if not isinstance(figures, list) or not figures:
        failures.append("H7: 图表登记必须包含非空 figures 列表")
        return
    pipeline = registry.get("pipeline_audit")
    if not isinstance(pipeline, dict):
        failures.append("H7: 图表登记必须含 pipeline_audit（阶段顺序审计：scipilot_decision→modelviz_generation→scipilot_qa）")
    else:
        for stage in ("scipilot_decision", "modelviz_generation", "scipilot_qa"):
            stage_info = pipeline.get(stage)
            if not isinstance(stage_info, dict):
                failures.append(f"H7: pipeline_audit 缺少阶段 {stage}")
            elif stage_info.get("status") not in ("passed", "completed", "approved"):
                failures.append(f"H7: pipeline_audit 阶段 {stage} 状态必须为 passed/completed/approved（当前: {stage_info.get('status')}）")
    seen_ids: set[str] = set()
    for idx, fig in enumerate(figures):
        label = f"H7: figures[{idx}]"
        if not isinstance(fig, dict):
            failures.append(f"{label}: 必须为对象")
            continue
        fid = fig.get("figure_id") or fig.get("id")
        if not isinstance(fid, str) or not fid.strip():
            failures.append(f"{label}: 缺少 figure_id")
        elif fid in seen_ids:
            failures.append(f"{label}: duplicate figure_id（重复图表编号: {fid}）")
        else:
            seen_ids.add(fid)
        formats = fig.get("formats")
        if not isinstance(formats, list) or not formats:
            failures.append(f"{label}: 缺少 formats 列表")
        else:
            fmt_set = {str(f).lower() for f in formats}
            if fmt_set != {"svg", "png"}:
                failures.append(f"{label}: formats 必须精确等于 [svg, png]（当前: {formats}）")
        source_files = fig.get("source_files")
        if not isinstance(source_files, list) or not source_files:
            source_single = fig.get("source")
            if isinstance(source_single, str) and source_single.strip():
                source_files = [source_single]
        if not source_files:
            failures.append(f"{label}: 缺少 source_files 或 source（数据/模型来源定位）")
        else:
            for sf in source_files:
                if not isinstance(sf, str) or not sf.strip():
                    failures.append(f"{label}: source_files 含无效条目")
                    continue
                sf_path = resolve_project_path(root, sf)
                if sf_path is None or not sf_path.is_file():
                    failures.append(f"{label}: source 文件不存在: {sf}")
        script = fig.get("script")
        # P0-05: SVG/PNG 文件存在性强制检查，不依赖于 script 字段
        svg_path_raw = fig.get("svg")
        png_path_raw = fig.get("png")
        output_checked = False
        if isinstance(svg_path_raw, str) and svg_path_raw.strip() and isinstance(png_path_raw, str) and png_path_raw.strip():
            # 直接登记了 svg/png 路径
            for ext, raw_path in (("svg", svg_path_raw), ("png", png_path_raw)):
                out_path = resolve_project_path(root, raw_path)
                if out_path is None or not out_path.is_file():
                    failures.append(f"{label}: {ext} 输出文件不存在: {raw_path}")
            output_checked = True
        elif isinstance(script, str) and script.strip():
            # 通过 script 推导输出路径
            script_path = resolve_project_path(root, script)
            if script_path is None or not script_path.is_file():
                failures.append(f"{label}: script 源文件不存在: {script}")
            else:
                stem = script_path.with_suffix("")
                for ext in ("svg", "png"):
                    out_path = stem.with_suffix(f".{ext}")
                    if not out_path.is_file():
                        failures.append(f"{label}: 输出文件不存在: {out_path.relative_to(root) if out_path.is_relative_to(root) else out_path}")
                output_checked = True
        if not output_checked:
            failures.append(f"{label}: 必须登记 svg/png 输出文件路径，或登记 script 源文件用于推导输出；禁止只登记 formats 而不提供实际图像文件")
        qa = fig.get("qa_status") or fig.get("status")
        if qa not in ("passed", "reviewed", "approved"):
            failures.append(f"{label}: qa_status 必须为 passed/reviewed/approved（当前: {qa}）")
        kind = fig.get("kind")
        allowed_kinds = set(FIGURE_KIND_ROUTES)
        if not isinstance(kind, str) or kind not in allowed_kinds:
            failures.append(f"{label}: kind 必须为 {','.join(sorted(allowed_kinds))}（当前: {kind}）")
        else:
            allowed_generators = FIGURE_KIND_ROUTES[kind]
            gen = fig.get("generator")
            if gen not in allowed_generators:
                failures.append(f"{label}: kind={kind} 的 generator 必须为 {','.join(allowed_generators)}（当前: {gen}）")
            if kind == "data" and fig.get("semantic_qa") != "scipilot-figure-skill":
                failures.append(f"{label}: 数据图必须 semantic_qa=scipilot-figure-skill（SciPilot→ModelViz→SciPilot 链）")
            if kind == "drawio" and fig.get("user_requested") is not True:
                failures.append(f"{label}: drawio 图必须 user_requested=true（Draw.io 仅显式请求）")
        if fig.get("insertion_format") != "svg":
            failures.append(f"{label}: insertion_format 必须为 svg（当前: {fig.get('insertion_format')}）")
        failures.extend(layout_validation_errors(label, fig))
        if not isinstance(fig.get("caption_claim"), str) or not fig["caption_claim"].strip():
            failures.append(f"{label}: 缺少 caption_claim（图注主张，必须说明该图支持的核心结论）")
        if not isinstance(fig.get("paper_location"), str) or not fig["paper_location"].strip():
            failures.append(f"{label}: 缺少 paper_location（论文落位章节）")
        if kind == "data":
            if fig.get("decision_author") != "scipilot-figure-skill":
                failures.append(f"{label}: 数据图必须 decision_author=scipilot-figure-skill（当前: {fig.get('decision_author')}）")
            dc_raw = fig.get("decision_card")
            if not isinstance(dc_raw, str) or not dc_raw.strip():
                failures.append(f"{label}: 数据图必须登记 decision_card（SciPilot 决策卡路径）")
            else:
                dc_path = resolve_project_path(root, dc_raw)
                if dc_path is None or not dc_path.is_file():
                    failures.append(f"{label}: decision_card 文件不存在: {dc_raw}")
        if fig.get("visual_qa") not in ("passed", "reviewed"):
            failures.append(f"{label}: 图表视觉检查必须 passed/reviewed（当前: {fig.get('visual_qa')}）")
        # Hash verification: if a sha256 field is declared, it must match
        # the actual file content.  Missing hash fields are tolerated for
        # backward compatibility; declared-but-wrong hashes are failures.
        for hash_field, path_field in (
            ("decision_card_sha256", "decision_card"),
            ("svg_sha256", "svg"),
            ("png_sha256", "png"),
        ):
            expected = fig.get(hash_field)
            if not isinstance(expected, str) or not expected.strip():
                continue
            if not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
                failures.append(f"{label}: {hash_field} 必须为 64 位十六进制字符串（当前: {expected}）")
                continue
            raw_path = fig.get(path_field)
            if not isinstance(raw_path, str) or not raw_path.strip():
                failures.append(f"{label}: 声明了 {hash_field} 但缺少对应 {path_field} 路径")
                continue
            file_path = resolve_project_path(root, raw_path)
            if file_path is None or not file_path.is_file():
                failures.append(f"{label}: {hash_field} 对应文件不存在: {raw_path}")
                continue
            actual = digest(file_path)
            if actual.lower() != expected.lower():
                failures.append(f"{label}: {hash_field} 不匹配（声明: {expected[:16]}…, 实际: {actual[:16]}…）")


def _validate_h7_visual_plan_approval(root: Path, node: dict[str, Any], log: dict[str, Any],
                                      plan_path: Path, missing: list[str], failures: list[str]) -> None:
    """Require a separate user approval before H7 can generate or register figures."""
    try:
        plan = load_mapping(plan_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures.append(f"H7_VISUAL_PLAN: visual_argument_plan 不可读: {exc}")
        return
    if plan.get("status") not in {"approved", "complete"}:
        missing.append("H7_VISUAL_PLAN: visual_argument_plan 必须先标记为 approved/complete")
    _validate_review(
        root,
        "H7",
        node,
        log,
        missing,
        failures,
        packet_key="visual_plan_review_packet",
        approval_gate="H7_VISUAL_PLAN",
        packet_node_id="H7_VISUAL_PLAN",
        min_artifact_count=1,
        label="H7_VISUAL_PLAN",
        required_artifact_paths=(plan_path,),
    )
    packet_raw = node.get("visual_plan_review_packet")
    packet_path = resolve_project_path(root, packet_raw)
    if packet_path is None or not packet_path.is_file():
        return
    try:
        packet = load_mapping(packet_path)
    except (OSError, ValueError, yaml.YAMLError):
        return
    if packet.get("requested_decision") != "approve":
        failures.append("H7_VISUAL_PLAN: requested_decision 必须为 approve")
    if packet.get("proposed_next_node") != "H7_GENERATE":
        failures.append("H7_VISUAL_PLAN: proposed_next_node 必须为 H7_GENERATE")


def _validate_h7_generation_binding(root: Path, control: dict[str, Any], node: dict[str, Any],
                                    log: dict[str, Any], missing: list[str], failures: list[str]) -> None:
    """Bind every H7 generation dispatch to an approved plan version and time.

    A plan status is not an approval record.  The generation task card must
    carry the exact current plan digest, and its dispatch must happen after a
    matching user approval.  Plan-only H7 work has no generation binding to
    validate yet.
    """
    if control.get("visual_workflow") == "chapter_parallel":
        # Per-chapter prompt snapshots are validated by _validate_writer_preparation;
        # later prompt repairs must not invalidate earlier accepted chapter text.
        return
    raw_plan = node.get("visual_argument_plan") if isinstance(node, dict) else None
    plan_path = resolve_project_path(root, raw_plan)
    if plan_path is None or not plan_path.is_file():
        return

    records = control.get("dispatch_records") if isinstance(control, dict) else None
    if not isinstance(records, list):
        return
    generation_records: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict) or record.get("node_id") != "H7":
            continue
        card_path = resolve_project_path(root, record.get("task_card_path"))
        if card_path is None or not card_path.is_file():
            continue
        try:
            card = load_mapping(card_path)
        except (OSError, ValueError, yaml.YAMLError):
            continue
        scope = card.get("scope")
        phase = scope.get("phase") if isinstance(scope, dict) else None
        if phase in {"H7_generate", "H7_GENERATE", "generation"}:
            generation_records.append((index, record, card))
    if not generation_records:
        return

    plan_digest = digest(plan_path)
    matching_approvals: list[datetime] = []
    approvals = log.get("approvals", []) if isinstance(log, dict) else []
    if isinstance(approvals, list):
        for approval in approvals:
            if not isinstance(approval, dict) or approval.get("gate") != "H7_VISUAL_PLAN":
                continue
            if approval.get("decision") != "approved":
                continue
            artifact_digests = approval.get("artifact_digests")
            if not isinstance(artifact_digests, dict):
                continue
            plan_match = False
            for raw_path, expected_sha in artifact_digests.items():
                approved_path = resolve_project_path(root, raw_path)
                if approved_path is not None and approved_path == plan_path and same_digest(expected_sha, plan_digest):
                    plan_match = True
                    break
            if not plan_match:
                continue
            approved_at = _parse_timestamp(approval.get("timestamp"))
            if approved_at is None:
                missing.append("H7_VISUAL_PLAN: 匹配当前 visual_argument_plan 的批准记录缺少有效 timestamp")
            else:
                matching_approvals.append(approved_at)
    if not matching_approvals:
        missing.append("H7_GENERATE: 缺少覆盖当前 visual_argument_plan SHA-256 的 H7_VISUAL_PLAN 批准记录")
        return
    approved_at = max(matching_approvals)

    for index, record, card in generation_records:
        label = f"dispatch_records[{index}]"
        scope = card.get("scope") if isinstance(card.get("scope"), dict) else {}
        bound_hash = scope.get("approved_visual_plan_sha256")
        if not isinstance(bound_hash, str) or not bound_hash.strip():
            missing.append(f"{label}: H7 生成任务缺少 scope.approved_visual_plan_sha256")
        elif not re.fullmatch(r"[0-9a-fA-F]{64}", bound_hash):
            failures.append(f"{label}: scope.approved_visual_plan_sha256 必须为 64 位十六进制字符串")
        elif not same_digest(bound_hash, plan_digest):
            failures.append(f"{label}: H7 生成任务绑定的视觉计划哈希与当前计划不一致")
        dispatched_at = _parse_timestamp(record.get("dispatched_at"))
        if dispatched_at is not None and dispatched_at <= approved_at:
            failures.append(
                f"{label}: H7 生成任务必须在匹配的 H7_VISUAL_PLAN 批准后派发"
                f"（派发 {dispatched_at.isoformat()}，批准 {approved_at.isoformat()}）"
            )


def _validate_h7_visual_argument_plan(root: Path, node: dict[str, Any], control: dict[str, Any],
                                      log: dict[str, Any], missing: list[str], failures: list[str]) -> None:
    """Require H7's reader-first coverage plan before H7 can pass."""
    raw = node.get("visual_argument_plan")
    if not isinstance(raw, str) or not raw.strip():
        missing.append("H7: 缺少 visual_argument_plan（读者问题—视觉槽位—证据覆盖计划）")
        return
    plan_path = resolve_project_path(root, raw)
    if plan_path is None or not plan_path.is_file():
        missing.append(f"H7: visual_argument_plan 文件不存在: {raw}")
        return
    try:
        plan = load_mapping(plan_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures.append(f"H7: visual_argument_plan 不可读: {exc}")
        return

    registry_raw = node.get("figure_registry")
    requires_plan_approval = (
        node.get("status") in {"review_pending", "approved", "frozen"}
        or isinstance(registry_raw, str) and bool(registry_raw.strip())
        or plan.get("status") in {"approved", "complete"}
    )
    if requires_plan_approval and control.get("visual_workflow") != "chapter_parallel":
        _validate_h7_visual_plan_approval(root, node, log, plan_path, missing, failures)

    model_raw = node.get("model_summary_cards") or "model_summary_cards.yaml"
    model_path = resolve_project_path(root, model_raw)
    if model_path is None or not model_path.is_file():
        missing.append(f"H7: 缺少 model_summary_cards（视觉复杂度推断输入）: {model_raw}")
        model_cards = None
    else:
        try:
            model_cards = load_mapping(model_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            failures.append(f"H7: model_summary_cards 不可读: {exc}")
            model_cards = None

    packet = None
    packet_raw = node.get("visual_evidence_packet")
    packet_path = resolve_project_path(root, packet_raw) if isinstance(packet_raw, str) else None
    if packet_path is not None and packet_path.is_file():
        try:
            packet = load_mapping(packet_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            failures.append(f"H7: visual_evidence_packet 不可读: {exc}")

    registry = None
    if isinstance(registry_raw, str) and registry_raw.strip():
        registry_path = resolve_project_path(root, registry_raw)
        if registry_path is not None and registry_path.is_file():
            try:
                registry = load_mapping(registry_path)
            except (OSError, ValueError, yaml.YAMLError) as exc:
                failures.append(f"H7: figure_registry 不可读: {exc}")
        elif node.get("status") in {"approved", "frozen"}:
            missing.append(f"H7: figure_registry 文件不存在: {registry_raw}")
    stage = "final" if node.get("status") in {"approved", "frozen"} else "plan"
    scope = control.get("problem_scope") if isinstance(control.get("problem_scope"), dict) else {}
    expected = scope.get("subproblems") if isinstance(scope.get("subproblems"), list) else None
    report = validate_visual_argument_plan(
        plan,
        expected_subproblems=expected,
        model_cards=model_cards,
        evidence_packet=packet,
        registry=registry,
        stage=stage,
        reader_protocol_enabled=control.get("reader_evidence_protocol") == READER_EVIDENCE_VERSION,
        project_root=root,
    )
    failures.extend(f"H7 visual_argument_plan: {item}" for item in report.get("errors", []))


def _validate_h9_delivery(root: Path, node: dict[str, Any],
                          missing: list[str], failures: list[str]) -> None:
    report_raw = node.get("delivery_report")
    if not isinstance(report_raw, str) or not report_raw.strip():
        missing.append("H9: 缺少 delivery_report（必须登记 delivery_all.py --strict 的报告路径）")
        return
    report_path = resolve_project_path(root, report_raw)
    if report_path is None or not report_path.is_file():
        missing.append(f"H9: delivery_report 文件不存在: {report_raw}")
        return
    try:
        report = load_mapping(report_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures.append(f"H9: delivery_report 不可读: {exc}")
        return
    if report.get("status") != "PASS":
        failures.append(f"H9: delivery_all.py --strict 未通过（status={report.get('status')}）")
    command = report.get("command")
    if not isinstance(command, str) or "delivery_all.py" not in command or "--strict" not in command:
        failures.append("H9: delivery_report 必须登记 command 且包含 delivery_all.py --strict")
    elif not re.search(r"^\s*(?:[A-Za-z]:\\|/)?[\w./\\-]*python(?:\.exe)?\s+.*delivery_all\.py\s+.*--strict", command):
        failures.append(f"H9: command 必须为真实 python 执行（拒绝 echo/cat 等伪造）: {command}")
    project_root = report.get("project_root")
    if not isinstance(project_root, str) or not project_root.strip():
        failures.append("H9: delivery_report 必须登记 project_root")
    else:
        normalized_pr = Path(project_root).resolve()
        if normalized_pr != root.resolve():
            failures.append(f"H9: delivery_report project_root({project_root}) 与当前项目根({root}) 不一致")
    run_at = report.get("run_at")
    if not isinstance(run_at, str) or not run_at.strip():
        failures.append("H9: delivery_report 必须登记 run_at 时间戳")
    else:
        try:
            datetime.fromisoformat(run_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            failures.append(f"H9: run_at 必须为 ISO 时间戳格式（当前: {run_at}）")
    input_sha = report.get("input_sha256")
    if not isinstance(input_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", input_sha):
        failures.append("H9: input_sha256 必须为 64 位十六进制字符串")
    else:
        # P0-06: 实际重算输入清单哈希，拒绝自报
        input_manifest_raw = report.get("input_manifest")
        if not isinstance(input_manifest_raw, str) or not input_manifest_raw.strip():
            failures.append("H9: delivery_report 必须登记 input_manifest（输入清单路径），不得只自报 input_sha256")
        else:
            manifest_path = resolve_project_path(root, input_manifest_raw)
            if manifest_path is None or not manifest_path.is_file():
                failures.append(f"H9: input_manifest 文件不存在: {input_manifest_raw}")
            else:
                try:
                    manifest = load_mapping(manifest_path)
                    manifest_files = manifest.get("files")
                    if not isinstance(manifest_files, list) or not manifest_files:
                        failures.append("H9: input_manifest 必须含非空 files 列表")
                    else:
                        computed_hashes = []
                        manifest_errors = []
                        for idx, mf in enumerate(manifest_files):
                            if not isinstance(mf, dict):
                                manifest_errors.append(f"input_manifest.files[{idx}] 必须为对象")
                                continue
                            mf_path = mf.get("path")
                            mf_sha = mf.get("sha256")
                            if not isinstance(mf_path, str) or not mf_path.strip():
                                manifest_errors.append(f"input_manifest.files[{idx}] 缺少 path")
                                continue
                            resolved_mf = resolve_project_path(root, mf_path)
                            if resolved_mf is None or not resolved_mf.is_file():
                                manifest_errors.append(f"input_manifest.files[{idx}] 文件不存在: {mf_path}")
                                continue
                            actual_mf = digest(resolved_mf)
                            computed_hashes.append(f"{mf_path}:{actual_mf}")
                            if isinstance(mf_sha, str) and re.fullmatch(r"[0-9a-fA-F]{64}", mf_sha):
                                if actual_mf.lower() != mf_sha.lower():
                                    manifest_errors.append(f"input_manifest.files[{idx}] sha256 不匹配: {mf_path}")
                        if manifest_errors:
                            failures.extend(f"H9: {e}" for e in manifest_errors[:5])
                        # 重算清单总哈希：按路径排序的 path:sha256 列表的 SHA-256
                        if computed_hashes:
                            computed_hashes.sort()
                            manifest_content = "\n".join(computed_hashes)
                            import hashlib
                            manifest_total = hashlib.sha256(manifest_content.encode("utf-8")).hexdigest()
                            if manifest_total.lower() != input_sha.lower():
                                failures.append(f"H9: input_sha256 与实际重算的输入清单总哈希不匹配（声明: {input_sha[:16]}…, 实际: {manifest_total[:16]}…）")
                except (OSError, ValueError, yaml.YAMLError) as exc:
                    failures.append(f"H9: input_manifest 不可读: {exc}")
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        failures.append("H9: delivery_report 必须含非空 artifacts 列表")
    else:
        for idx, art in enumerate(artifacts):
            if not isinstance(art, dict):
                failures.append(f"H9: artifacts[{idx}] 必须为对象")
                continue
            apath = art.get("path")
            asha = art.get("sha256")
            if not isinstance(apath, str) or not apath.strip():
                failures.append(f"H9: artifacts[{idx}] 缺少 path")
                continue
            resolved = resolve_project_path(root, apath)
            if resolved is None or not resolved.is_file():
                failures.append(f"H9: artifacts[{idx}] 文件不存在: {apath}")
                continue
            if not isinstance(asha, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", asha):
                failures.append(f"H9: artifacts[{idx}] sha256 必须为 64 位十六进制字符串")
                continue
            actual = digest(resolved)
            if actual.lower() != asha.lower():
                failures.append(f"H9: artifacts[{idx}] sha256 不匹配（声明: {asha[:16]}…, 实际: {actual[:16]}…, 文件: {apath}）")


def _load_project_mapping(root: Path, raw_path: Any, label: str, missing: list[str],
                          failures: list[str]) -> tuple[Path | None, dict[str, Any] | None]:
    path = resolve_project_path(root, raw_path)
    if path is None or not path.is_file():
        missing.append(f"{label}: 文件不存在")
        return None, None
    try:
        return path, load_mapping(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures.append(f"{label}: 文件不可读: {exc}")
        return None, None


def _h6_targeted_scope(root: Path, nodes: dict[str, Any]) -> set[str] | None:
    """Return the subproblems explicitly rechecked by a targeted H6 run."""
    h6 = nodes.get("H6", {})
    raw_scope = h6.get("h6_verification_scope") if isinstance(h6, dict) else None
    path = resolve_project_path(root, raw_scope) if isinstance(raw_scope, str) else None
    if path is None or not path.is_file():
        return None
    try:
        scope = load_mapping(path)
    except (OSError, ValueError, yaml.YAMLError):
        return None
    mode = str(scope.get("mode", "")).strip().lower()
    if mode not in {"targeted", "targeted_review"}:
        return None
    values = scope.get("rechecked_subproblems")
    if not isinstance(values, list):
        return None
    result = {str(item).strip() for item in values if str(item).strip()}
    return result or None


def _reference_is_fresh(root: Path, reference: Any) -> tuple[bool, tuple[str, str] | None]:
    if not isinstance(reference, dict):
        return False, None
    path = resolve_project_path(root, reference.get("path"))
    expected = reference.get("sha256")
    if path is None or not path.is_file() or not isinstance(expected, str):
        return False, None
    actual = digest(path)
    return same_digest(expected, actual), (as_relative(root, path), actual)


def _validate_abstract_argument_card(root: Path, node: dict[str, Any],
                                     problem_scope: dict[str, Any],
                                     missing: list[str], failures: list[str]) -> None:
    """Require the H8A abstract plan and bind its evidence to frozen files."""
    card_path, card = _load_project_mapping(
        root, node.get("abstract_argument_card"),
        "H8: abstract_argument_card", missing, failures,
    )
    if card_path is None or card is None:
        return
    expected_ids: list[str] = []
    raw_scope = problem_scope.get("subproblems", []) if isinstance(problem_scope, dict) else []
    if isinstance(raw_scope, list):
        for item in raw_scope:
            value = item.get("id") if isinstance(item, dict) else item
            if isinstance(value, str) and value.strip():
                expected_ids.append(value.strip())
    report = validate_abstract_argument_card(card_path, expected_ids or None)
    for issue in report.get("issues", []):
        failures.append(f"H8: abstract_argument_card: {issue}")
    if node.get("writing_started") is True and card.get("status") != "approved":
        failures.append("H8: 开始正文写作前 abstract_argument_card 必须经批准（status=approved）")
    blueprint_path = resolve_project_path(root, node.get("paper_argument_blueprint"))
    if blueprint_path is not None and blueprint_path.is_file():
        blueprint_hash = card.get("paper_argument_blueprint_sha256")
        if not isinstance(blueprint_hash, str) or not same_digest(blueprint_hash, digest(blueprint_path)):
            failures.append("H8: abstract_argument_card 必须绑定当前 paper_argument_blueprint")
    for index, question in enumerate(card.get("questions", [])):
        if not isinstance(question, dict):
            continue
        refs = question.get("evidence_refs", [])
        for ref_index, reference in enumerate(refs if isinstance(refs, list) else []):
            if isinstance(reference, dict):
                fresh, _ = _reference_is_fresh(root, reference)
            elif isinstance(reference, str) and reference.strip():
                fresh = resolve_project_path(root, reference).is_file() if resolve_project_path(root, reference) else False
            else:
                fresh = False
            if not fresh:
                failures.append(
                    f"H8: abstract_argument_card.questions[{index}].evidence_refs[{ref_index}] "
                    "必须指向存在且未过期的证据"
                )
    if node.get("abstract_written") is True:
        report_path, abstract_report = _load_project_mapping(
            root, node.get("abstract_contract_report"),
            "H8: abstract_contract_report", missing, failures,
        )
        if report_path is None or abstract_report is None:
            return
        if abstract_report.get("passed") is not True:
            failures.append("H8: abstract_contract_report.passed 必须为 true")
        card_hash = abstract_report.get("abstract_argument_card_sha256")
        if not isinstance(card_hash, str) or not card_hash.strip():
            failures.append("H8: abstract_contract_report 必须登记 abstract_argument_card_sha256")
        elif not same_digest(card_hash, digest(card_path)):
            failures.append("H8: abstract_contract_report 未绑定当前 abstract_argument_card")
    elif node.get("status") in {"approved", "frozen"} and node.get("paper_source"):
        missing.append("H8: 完成 H8C 前必须登记 abstract_written=true 并提交摘要专项检查报告")


def _validate_spawn_invocations(control: dict[str, Any], through: str,
                                missing: list[str], failures: list[str]) -> dict[str, str]:
    """H1 后必须存在 superpowers spawn_roles 调用记录且覆盖 H5-H8。

    返回 role -> agent_instance_id 溯源映射；只写技能名、缺 task_id 或非 completed 不算调用。
    """
    agent_ids_by_role: dict[str, str] = {}
    if NODES.index(through) < NODES.index("H2"):
        return agent_ids_by_role  # H1 未完成，尚不要求批量创建
    bootstrap = control.get("bootstrap", {})
    invocations = bootstrap.get("invocations", []) if isinstance(bootstrap, dict) else []
    if not isinstance(invocations, list):
        failures.append("bootstrap.invocations 必须为列表")
        return agent_ids_by_role
    spawn_created_lists: list[list[Any]] = []
    for index, item in enumerate(invocations):
        label = f"bootstrap.invocations[{index}]"
        if not isinstance(item, dict):
            failures.append(f"{label}: 条目必须为对象")
            continue
        if not str(item.get("task_id", "")).strip():
            failures.append(f"{label}: 缺少 task_id（只写技能名不构成调用记录）")
        if item.get("status") != "completed":
            continue
        agent_ids = item.get("agent_ids")
        if isinstance(agent_ids, dict):
            for role, instance_id in agent_ids.items():
                if role == "H1" and isinstance(instance_id, str) and instance_id.strip():
                    agent_ids_by_role[role] = instance_id
        if item.get("purpose") == "spawn_roles":
            if item.get("skill") != "superpowers:using-superpowers":
                failures.append(f"{label}: spawn_roles 必须登记 skill=superpowers:using-superpowers")
            if item.get("completed") is not True:
                failures.append(f"{label}: spawn_roles 必须 completed=true")
            if item.get("after_node") != "H1":
                failures.append(f"{label}: spawn_roles 必须登记 after_node=H1（H1 产出题面后一次性创建全角色）")
            created = item.get("created")
            if isinstance(created, list):
                spawn_created_lists.append(created)
                if len(created) != len(set(str(r) for r in created if isinstance(r, str))):
                    failures.append(f"{label}: spawn_roles created 不得重复（当前: {created}）")
                created_set = {r for r in created if isinstance(r, str)}
                if created_set != {"H5", "H6", "H7", "H8"}:
                    failures.append(f"{label}: spawn_roles created 必须恰好为 H5,H6,H7,H8（当前: {','.join(sorted(created_set))}）")
                agent_ids = item.get("agent_ids")
                if isinstance(agent_ids, dict):
                    for role, instance_id in agent_ids.items():
                        if isinstance(role, str) and isinstance(instance_id, str) and instance_id.strip():
                            agent_ids_by_role[role] = instance_id
                    spawn_agent_roles = set(k for k in agent_ids.keys() if isinstance(k, str))
                    missing_agent = created_set - spawn_agent_roles
                    if missing_agent:
                        failures.append(f"{label}: spawn_roles agent_ids 缺少角色 {','.join(sorted(missing_agent))}")
    if len(spawn_created_lists) > 1:
        failures.append(f"H1: spawn_roles 必须唯一（当前 {len(spawn_created_lists)} 条）")
    covered: set[str] = set()
    for created in spawn_created_lists:
        covered.update(role for role in created if isinstance(role, str))
    missing_roles = {"H5", "H6", "H7", "H8"} - covered
    if missing_roles:
        missing.append(f"H1: 缺少 superpowers spawn_roles 调用覆盖角色 {','.join(sorted(missing_roles))}")
    return agent_ids_by_role


def _validate_agent_instances(root: Path, control: dict[str, Any], through: str, agent_ids_by_role: dict[str, str],
                              missing: list[str], failures: list[str]) -> None:
    """实例注册表校验：H1 后必须全角色注册、preloaded 含题面、实例 ID 可溯源、H6≠H5。"""
    if NODES.index(through) < NODES.index("H2"):
        return
    instances = control.get("agent_instances")
    if not isinstance(instances, dict):
        failures.append("agent_instances 必须为对象（H1 后一次性创建全部固定角色）")
        return
    for role in ("H1", "H5", "H6", "H7", "H8"):
        entry = instances.get(role)
        if not isinstance(entry, dict):
            missing.append(f"agent_instances: 缺少 {role} 实例")
            continue
        instance_id = entry.get("agent_instance_id")
        if not isinstance(instance_id, str) or not instance_id.strip():
            failures.append(f"agent_instances.{role}: 缺少 agent_instance_id")
            continue
        preloaded = entry.get("preloaded")
        required = list(REQUIRED_PRELOAD.get(role, ["problem_statement.md"]))
        if control.get("reader_evidence_protocol") == "1.0" and role == "H8":
            required.append(READER_EVIDENCE_PRELOAD)
        if not isinstance(preloaded, list):
            failures.append(f"agent_instances.{role}: preloaded 必须为列表")
        else:
            missing_preload = [f for f in required if f not in preloaded]
            if missing_preload:
                failures.append(f"agent_instances.{role}: preloaded 缺少 {','.join(missing_preload)}")
            for preload_path in preloaded:
                if not isinstance(preload_path, str) or not preload_path.strip():
                    failures.append(f"agent_instances.{role}: preloaded 含无效条目")
                    continue
                if preload_path == "problem_statement.md":
                    ps_path = root / "problem_statement.md"
                    if not ps_path.is_file():
                        missing.append(f"agent_instances.{role}: 预载声明的 problem_statement.md 不存在于项目工作区")
                elif preload_path.startswith("references/"):
                    skill_root = Path(__file__).resolve().parent.parent
                    skill_file = skill_root / preload_path
                    if not skill_file.is_file():
                        failures.append(f"agent_instances.{role}: 预载声明的 skill 文件不存在: {preload_path}")
        if agent_ids_by_role.get(role) != instance_id:
            failures.append(f"agent_instances.{role}: 实例 {instance_id} 无法溯源到 superpowers 调用返回")
    h5_entry = instances.get("H5")
    h6_entry = instances.get("H6")
    h5_id = h5_entry.get("agent_instance_id") if isinstance(h5_entry, dict) else None
    h6_id = h6_entry.get("agent_instance_id") if isinstance(h6_entry, dict) else None
    if h5_id and h6_id and h5_id == h6_id:
        failures.append("agent_instances: H6 必须使用与 H5 不同的 agent_instance_id")


def _validate_narrative(root: Path, nodes: dict[str, Any], through: str,
                        missing: list[str], failures: list[str]) -> None:
    """叙事蓝图校验：H5阶段一产出 method/innovation/problem_solved，H5阶段二-四回填 key_result，H6 核验。（H4已并入H5）"""
    if NODES.index(through) < NODES.index("H5"):
        return
    h5 = nodes.get("H5", {})
    path, narrative = _load_project_mapping(root, h5.get("paper_narrative"), "H5: paper_narrative", missing, failures)
    if path is None or narrative is None:
        return
    status = narrative.get("status")
    if status not in {"draft", "results_filled", "verified"}:
        failures.append("paper_narrative: status 必须为 draft/results_filled/verified")
    narrative_map = narrative.get("narrative")
    if not isinstance(narrative_map, dict) or not narrative_map:
        failures.append("paper_narrative: narrative 必须为非空对象")
        return
    question_ids = {key for key in narrative_map if key != "global"}
    global_entry = narrative_map.get("global")
    if not isinstance(global_entry, dict):
        failures.append("paper_narrative: global 必须为对象")
    else:
        for field in ("storyline", "validation_story"):
            if not str(global_entry.get(field, "")).strip():
                failures.append(f"paper_narrative: global 缺少 {field}")
        _validate_paper_spine(
            global_entry.get("paper_spine"), "paper_narrative.global.paper_spine", failures, question_ids,
        )
    at_h6_or_later = NODES.index(through) >= NODES.index("H6")
    if at_h6_or_later and status == "draft":
        failures.append("paper_narrative: H6 前必须由 H5 回填 key_result（status 至少为 results_filled）")
    for qid, entry in narrative_map.items():
        if not isinstance(entry, dict):
            failures.append(f"paper_narrative: {qid} 条目必须为对象")
            continue
        if qid == "global":
            continue
        for field in ("method", "innovation", "problem_solved"):
            if not str(entry.get(field, "")).strip():
                failures.append(f"paper_narrative: {qid} 缺少 {field}")
        if at_h6_or_later and not str(entry.get("key_result", "")).strip():
            failures.append(f"paper_narrative: {qid} 缺少 key_result（H5 未回填）")


def _validate_result_interpretation_cards(root: Path, nodes: dict[str, Any], through: str,
                                          missing: list[str], failures: list[str],
                                          control: dict[str, Any] | None = None) -> None:
    """Require H5 results to carry verified meaning and scope before H8."""
    if NODES.index(through) < NODES.index("H6"):
        return
    h5 = nodes.get("H5", {})
    path, cards_doc = _load_project_mapping(
        root, h5.get("result_interpretation_cards"), "H5: result_interpretation_cards", missing, failures
    )
    if path is None or cards_doc is None:
        return
    reader_protocol_enabled = _reader_protocol_state(
        control, cards_doc, "result_interpretation_cards", failures,
    )
    if cards_doc.get("status") != "verified":
        failures.append("result_interpretation_cards: H6 完成后 status 必须为 verified")
    if cards_doc.get("created_by") != "H5":
        failures.append("result_interpretation_cards: created_by 必须为 H5")
    if cards_doc.get("verified_by") != "H6":
        failures.append("result_interpretation_cards: verified_by 必须为 H6")
    if cards_doc.get("verification_agent_instance_id") != nodes.get("H6", {}).get("agent_instance_id"):
        failures.append("result_interpretation_cards: 必须由当前 H6 实例核验")
    cards = cards_doc.get("cards")
    if not isinstance(cards, list) or not cards:
        failures.append("result_interpretation_cards: cards 必须为非空列表")
        return
    seen_ids: set[str] = set()
    targeted_subproblems = _h6_targeted_scope(root, nodes)
    required_fields = ("card_id", "subproblem_id", "result_statement", "meaning", "reasoning_basis", "supported_scope")
    for index, card in enumerate(cards):
        label = f"result_interpretation_cards.cards[{index}]"
        if not isinstance(card, dict):
            failures.append(f"{label}: 必须为对象")
            continue
        if targeted_subproblems is not None and card.get("subproblem_id") not in targeted_subproblems:
            continue
        for field in required_fields:
            if not isinstance(card.get(field), str) or not card[field].strip():
                failures.append(f"{label}: 缺少 {field}")
        card_id = card.get("card_id")
        if isinstance(card_id, str) and card_id.strip():
            if card_id in seen_ids:
                failures.append(f"{label}: card_id 重复: {card_id}")
            seen_ids.add(card_id)
        refs = card.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            failures.append(f"{label}: evidence_refs 必须为非空列表")
            continue
        for reference in refs:
            fresh, _ = _reference_is_fresh(root, reference)
            if not fresh:
                failures.append(f"{label}: evidence_refs 含不存在、过期或哈希不匹配的证据")
        if reader_protocol_enabled:
            failures.extend(validate_result_card(card, label))


def _validate_visual_evidence_packet(root: Path, nodes: dict[str, Any], problem_scope: dict[str, Any],
                                     through: str, missing: list[str], failures: list[str]) -> None:
    """Bind the compact H5 visual evidence packet to H6 verification and H7 input."""
    if NODES.index(through) < NODES.index("H5"):
        return
    if NODES.index(through) == NODES.index("H5"):
        required_nodes = ("H5",)
        stage = "h5"
    elif NODES.index(through) == NODES.index("H6"):
        required_nodes = ("H5", "H6")
        stage = "h6"
    else:
        required_nodes = ("H5", "H6", "H7")
        stage = "h7"

    refs: dict[str, str] = {}
    for node_id in required_nodes:
        node = nodes.get(node_id, {})
        raw = node.get("visual_evidence_packet") if isinstance(node, dict) else None
        if not isinstance(raw, str) or not raw.strip():
            missing.append(f"{node_id}: 当前阶段必须登记 visual_evidence_packet")
            continue
        refs[node_id] = raw
    canonical_ref = refs.get("H5") or next(iter(refs.values()), None)
    if canonical_ref is None:
        return
    for node_id, raw in refs.items():
        if raw != canonical_ref:
            failures.append(f"{node_id}: visual_evidence_packet 必须与 H5 权威登记路径一致")
    packet_path, packet = _load_project_mapping(
        root, canonical_ref, "visual_evidence_packet", missing, failures,
    )
    if packet_path is None or packet is None:
        return
    expected_ids: list[str] = []
    raw_scope = problem_scope.get("subproblems", []) if isinstance(problem_scope, dict) else []
    if isinstance(raw_scope, list):
        for item in raw_scope:
            value = item.get("id") if isinstance(item, dict) else item
            if isinstance(value, str) and value.strip():
                expected_ids.append(value.strip())
    targeted_subproblems = _h6_targeted_scope(root, nodes)
    if targeted_subproblems is not None:
        expected_ids = [item for item in expected_ids if item in targeted_subproblems]
    h5 = nodes.get("H5", {})
    contract_raw = h5.get("model_contract") if isinstance(h5, dict) else None
    contract_path = resolve_project_path(root, contract_raw) if isinstance(contract_raw, str) else None
    if stage in {"h6", "h7"} and (contract_path is None or not contract_path.is_file()):
        missing.append("visual_evidence_packet: H6/H7 阶段必须登记可核验的 model_contract")
    h6_instance = nodes.get("H6", {}).get("agent_instance_id") if isinstance(nodes.get("H6"), dict) else None
    report = validate_visual_evidence_packet(
        packet,
        root=root,
        expected_subproblems=None if targeted_subproblems is not None else (expected_ids or None),
        stage=stage,
        expected_h6_instance=h6_instance if stage in {"h6", "h7"} else None,
        model_contract_path=contract_path,
    )
    failures.extend(f"visual_evidence_packet: {item}" for item in report.get("errors", []))
    if packet.get("status") == "evidence_gap":
        missing.append("visual_evidence_packet: status=evidence_gap，必须回流 H5 补充证据")


def _validate_argument_blueprint(root: Path, nodes: dict[str, Any],
                                 missing: list[str], failures: list[str]) -> None:
    """Bind H8 writing to an approved reader-question to evidence blueprint."""
    h5 = nodes.get("H5", {})
    h8 = nodes.get("H8", {})
    narrative_path = resolve_project_path(root, h5.get("paper_narrative"))
    cards_path = resolve_project_path(root, h5.get("result_interpretation_cards"))
    blueprint_path, blueprint = _load_project_mapping(
        root, h8.get("paper_argument_blueprint"), "H8: paper_argument_blueprint", missing, failures
    )
    if blueprint_path is None or blueprint is None:
        return
    if blueprint.get("status") not in {"draft", "approved"}:
        failures.append("paper_argument_blueprint: status 必须为 draft 或 approved")
    if h8.get("writing_started") is True and blueprint.get("status") != "approved":
        failures.append("H8: 开始写作前 paper_argument_blueprint 必须经批准（status=approved）")
    if blueprint.get("prepared_by") != "academic-writing":
        failures.append("paper_argument_blueprint: prepared_by 必须为 academic-writing")
    if narrative_path is None or not narrative_path.is_file():
        failures.append("paper_argument_blueprint: 无法核验 paper_narrative.yaml")
    elif not same_digest(blueprint.get("narrative_sha256"), digest(narrative_path)):
        failures.append("paper_argument_blueprint: narrative_sha256 与 paper_narrative.yaml 不匹配")
    narrative_spine = None
    if narrative_path is not None and narrative_path.is_file():
        try:
            narrative_doc = load_mapping(narrative_path)
            narrative_global = (narrative_doc.get("narrative") or {}).get("global", {})
            if isinstance(narrative_global, dict):
                narrative_spine = _spine_signature(narrative_global.get("paper_spine", {}))
        except (OSError, ValueError, yaml.YAMLError):
            narrative_spine = None
    if cards_path is None or not cards_path.is_file():
        failures.append("paper_argument_blueprint: 无法核验 result_interpretation_cards.yaml")
        card_ids: set[str] = set()
    else:
        if not same_digest(blueprint.get("interpretation_cards_sha256"), digest(cards_path)):
            failures.append("paper_argument_blueprint: interpretation_cards_sha256 与结果解释卡不匹配")
        try:
            cards_doc = load_mapping(cards_path)
        except (OSError, ValueError, yaml.YAMLError):
            cards_doc = {}
        card_ids = {
            item.get("card_id") for item in cards_doc.get("cards", [])
            if isinstance(item, dict) and isinstance(item.get("card_id"), str) and item["card_id"].strip()
        }
    global_map = blueprint.get("global")
    if not isinstance(global_map, dict):
        failures.append("paper_argument_blueprint: global 必须为对象")
        blueprint_spine = None
    else:
        for field in ("central_thesis", "reader_journey"):
            if not isinstance(global_map.get(field), str) or not global_map[field].strip():
                failures.append(f"paper_argument_blueprint: global 缺少 {field}")
        blueprint_spine = _validate_paper_spine(
            global_map.get("paper_spine"), "paper_argument_blueprint.global.paper_spine", failures,
        )
        if narrative_spine is not None and blueprint_spine is not None and narrative_spine != blueprint_spine:
            failures.append("paper_argument_blueprint.global.paper_spine 必须与 paper_narrative.global.paper_spine 一致")
    chapters = blueprint.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        failures.append("paper_argument_blueprint: chapters 必须为非空列表")
    else:
        for index, chapter in enumerate(chapters):
            label = f"paper_argument_blueprint.chapters[{index}]"
            if not isinstance(chapter, dict):
                failures.append(f"{label}: 必须为对象")
                continue
            for field in ("section_id", "reader_question", "chapter_answer"):
                if not isinstance(chapter.get(field), str) or not chapter[field].strip():
                    failures.append(f"{label}: 缺少 {field}")
            for field in ("argument_ids", "evidence_refs", "figure_roles", "excluded_material"):
                if not isinstance(chapter.get(field), list):
                    failures.append(f"{label}: {field} 必须为列表")
            if blueprint_spine is not None:
                chapter_arguments = {
                    item for item in (chapter.get("argument_ids") if isinstance(chapter.get("argument_ids"), list) else [])
                    if isinstance(item, str)
                }
                _validate_chapter_relation(label, chapter, blueprint_spine, failures, chapter_arguments)
            for reference in chapter.get("evidence_refs", []):
                fresh, _ = _reference_is_fresh(root, reference)
                if not fresh:
                    failures.append(f"{label}: evidence_refs 含不存在、过期或哈希不匹配的证据")
        if blueprint_spine is not None:
            chapter_ids = {
                chapter.get("section_id") for chapter in chapters
                if isinstance(chapter, dict) and isinstance(chapter.get("section_id"), str)
            }
            if chapter_ids != set(blueprint_spine["chapter_order"]):
                failures.append("paper_argument_blueprint: chapters 必须完整覆盖 paper_spine.chapter_order")
    arguments = blueprint.get("arguments")
    if not isinstance(arguments, list) or not arguments:
        failures.append("paper_argument_blueprint: arguments 必须为非空列表")
        return
    seen_arguments: set[str] = set()
    for index, argument in enumerate(arguments):
        label = f"paper_argument_blueprint.arguments[{index}]"
        if not isinstance(argument, dict):
            failures.append(f"{label}: 必须为对象")
            continue
        for field in ("argument_id", "subproblem_id", "claim", "result_card_id", "why_it_matters", "supported_scope"):
            if not isinstance(argument.get(field), str) or not argument[field].strip():
                failures.append(f"{label}: 缺少 {field}")
        argument_id = argument.get("argument_id")
        if isinstance(argument_id, str) and argument_id.strip():
            if argument_id in seen_arguments:
                failures.append(f"{label}: argument_id 重复: {argument_id}")
            seen_arguments.add(argument_id)
        if argument.get("result_card_id") not in card_ids:
            failures.append(f"{label}: result_card_id 未绑定已核验结果解释卡")
        refs = argument.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            failures.append(f"{label}: evidence_refs 必须为非空列表")
        else:
            for reference in refs:
                fresh, _ = _reference_is_fresh(root, reference)
                if not fresh:
                    failures.append(f"{label}: evidence_refs 含不存在、过期或哈希不匹配的证据")


def _validate_paper_author_brief(root: Path, node: dict[str, Any],
                                 missing: list[str], failures: list[str],
                                 control: dict[str, Any] | None = None) -> None:
    """Require a compact author-facing brief before H8 starts drafting."""
    if node.get("writing_started") is not True:
        return
    blueprint_path = resolve_project_path(root, node.get("paper_argument_blueprint"))
    brief_path, brief = _load_project_mapping(
        root, node.get("paper_author_brief"), "H8: paper_author_brief", missing, failures
    )
    if brief_path is None or brief is None:
        return
    reader_protocol_enabled = _reader_protocol_state(
        control, brief, "paper_author_brief", failures,
    )
    if brief.get("status") != "approved":
        failures.append("paper_author_brief: 开始写作前 status 必须为 approved")
    if brief.get("prepared_by") != "academic-writing":
        failures.append("paper_author_brief: prepared_by 必须为 academic-writing")
    if blueprint_path is None or not blueprint_path.is_file():
        failures.append("paper_author_brief: 无法核验 paper_argument_blueprint.yaml")
    elif not same_digest(brief.get("argument_blueprint_sha256"), digest(blueprint_path)):
        failures.append("paper_author_brief: argument_blueprint_sha256 与论证蓝图不匹配")
    blueprint_spine = None
    if blueprint_path is not None and blueprint_path.is_file():
        try:
            blueprint_doc = load_mapping(blueprint_path)
            blueprint_global = blueprint_doc.get("global", {})
            if isinstance(blueprint_global, dict):
                blueprint_spine = _spine_signature(blueprint_global.get("paper_spine", {}))
        except (OSError, ValueError, yaml.YAMLError):
            blueprint_spine = None
    brief_spine = _validate_paper_spine(
        brief.get("paper_spine"), "paper_author_brief.paper_spine", failures,
    )
    if blueprint_spine is not None and brief_spine is not None and blueprint_spine != brief_spine:
        failures.append("paper_author_brief.paper_spine 必须与论证蓝图保持一致")
    if not isinstance(brief.get("central_thesis"), str) or not brief["central_thesis"].strip():
        failures.append("paper_author_brief: 缺少 central_thesis")
    chapters = brief.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        failures.append("paper_author_brief: chapters 必须为非空列表")
        return
    required = ("section_id", "reader_question", "chapter_purpose", "chapter_answer", "reader_takeaway")
    list_fields = ("argument_ids", "evidence_refs", "figure_roles", "excluded_material")
    for index, chapter in enumerate(chapters):
        label = f"paper_author_brief.chapters[{index}]"
        if not isinstance(chapter, dict):
            failures.append(f"{label}: 必须为对象")
            continue
        for field in required:
            if not isinstance(chapter.get(field), str) or not chapter[field].strip():
                failures.append(f"{label}: 缺少 {field}")
        for field in list_fields:
            if not isinstance(chapter.get(field), list):
                failures.append(f"{label}: {field} 必须为列表")
        if brief_spine is not None:
            chapter_arguments = {
                item for item in (chapter.get("argument_ids") if isinstance(chapter.get("argument_ids"), list) else [])
                if isinstance(item, str)
            }
            _validate_chapter_relation(label, chapter, brief_spine, failures, chapter_arguments)
        chapter_id = chapter.get("section_id")
        chapter_kind = chapter.get("chapter_kind")
        is_modeling_question = (
            chapter_kind in {"modeling", "modeling_question"}
            or (isinstance(chapter_id, str) and chapter_id.upper().startswith("Q"))
        )
        if is_modeling_question:
            _validate_question_structure(label, chapter, failures)
        if reader_protocol_enabled:
            failures.extend(validate_author_chapter(chapter, label))
    if brief_spine is not None:
        chapter_ids = {
            chapter.get("section_id") for chapter in chapters
            if isinstance(chapter, dict) and isinstance(chapter.get("section_id"), str)
        }
        if chapter_ids != set(brief_spine["chapter_order"]):
            failures.append("paper_author_brief: chapters 必须完整覆盖 paper_spine.chapter_order")


def _validate_question_structure(label: str, chapter: dict[str, Any], failures: list[str]) -> None:
    """Keep each modeling question readable without turning the manuscript into a checklist."""
    if not isinstance(chapter.get("opening_bridge"), str) or not chapter["opening_bridge"].strip():
        failures.append(f"{label}: 缺少 opening_bridge（问题引入与建模思路段）")
    structure = chapter.get("section_structure")
    if not isinstance(structure, dict):
        failures.append(f"{label}: 缺少 section_structure（模型建立/模型求解与结果分析）")
        return
    numbered = structure.get("numbered_sections")
    if numbered != list(QUESTION_NUMBERED_SECTIONS):
        failures.append(
            f"{label}: numbered_sections 必须按顺序为「{' / '.join(QUESTION_NUMBERED_SECTIONS)}」"
        )
    if structure.get("summary_location") != "模型建立小节末尾":
        failures.append(f"{label}: summary_location 必须为 模型建立小节末尾")
    if not isinstance(structure.get("optional_sections", []), list):
        failures.append(f"{label}: optional_sections 必须为列表")


def _validate_model_summary_cards(root: Path, nodes: dict[str, Any], problem_scope: dict[str, Any],
                                  missing: list[str], failures: list[str], through: str | None = None,
                                  control: dict[str, Any] | None = None) -> None:
    """Bind H6/H8 to one verified, solvable model summary per subproblem."""
    h8 = nodes.get("H8", {})
    h8_writing = isinstance(h8, dict) and h8.get("writing_started") is True
    h6 = nodes.get("H6", {})
    h6_active = (
        (through in NODES and NODES.index(through) >= NODES.index("H6"))
        or (isinstance(h6, dict) and (
            h6.get("status") != "not_started" or
            isinstance(h6.get("model_summary_cards"), str)
        ))
    )
    if not h8_writing and not h6_active:
        return

    refs: dict[str, str] = {}
    required_nodes = ("H5", "H6", "H8") if h8_writing else ("H5", "H6")
    for node_id in required_nodes:
        node = nodes.get(node_id, {})
        raw_path = node.get("model_summary_cards") if isinstance(node, dict) else None
        if not isinstance(raw_path, str) or not raw_path.strip():
            missing.append(f"{node_id}: 当前阶段必须登记 model_summary_cards")
            continue
        refs[node_id] = raw_path
    canonical_ref = refs.get("H8") or refs.get("H6") or refs.get("H5")
    if canonical_ref is None:
        return
    for node_id, raw_path in refs.items():
        if raw_path != canonical_ref:
            failures.append(f"{node_id}: model_summary_cards 必须与当前阶段的权威登记路径一致")
    summary_path, summary = _load_project_mapping(
        root, canonical_ref, "model_summary_cards", missing, failures,
    )
    if summary_path is None or summary is None:
        return
    reader_protocol_enabled = _reader_protocol_state(
        control, summary, "model_summary_cards", failures,
    )
    if summary.get("status") != "verified":
        failures.append("model_summary_cards: H8 前 status 必须为 verified")
    if summary.get("created_by") != "H5":
        failures.append("model_summary_cards: created_by 必须为 H5")
    if summary.get("verified_by") != "H6":
        failures.append("model_summary_cards: verified_by 必须为 H6")
    h6_instance = nodes.get("H6", {}).get("agent_instance_id") if isinstance(nodes.get("H6"), dict) else None
    if isinstance(h6_instance, str) and h6_instance.strip():
        if summary.get("verification_agent_instance_id") != h6_instance:
            failures.append("model_summary_cards: 必须由当前 H6 实例核验")

    h5 = nodes.get("H5", {})
    contract_path = resolve_project_path(root, h5.get("model_contract")) if isinstance(h5, dict) else None
    if contract_path is not None and contract_path.is_file():
        if not same_digest(summary.get("model_contract_sha256"), digest(contract_path)):
            failures.append("model_summary_cards: model_contract_sha256 与 model_contract.yaml 不匹配")

    cards = summary.get("cards")
    if not isinstance(cards, list) or not cards:
        failures.append("model_summary_cards: cards 必须为非空列表")
        return
    expected_ids: set[str] = set()
    scope_items = problem_scope.get("subproblems", []) if isinstance(problem_scope, dict) else []
    if isinstance(scope_items, list):
        for item in scope_items:
            value = item.get("id") if isinstance(item, dict) else item
            if isinstance(value, str) and value.strip():
                expected_ids.add(value.strip())
    seen_ids: set[str] = set()
    targeted_subproblems = _h6_targeted_scope(root, nodes)
    for index, card in enumerate(cards):
        label = f"model_summary_cards.cards[{index}]"
        if not isinstance(card, dict):
            failures.append(f"{label}: 必须为对象")
            continue
        if targeted_subproblems is not None and card.get("subproblem_id") not in targeted_subproblems:
            continue
        for field in ("card_id", "subproblem_id", "purpose", "model_family"):
            if not isinstance(card.get(field), str) or not card[field].strip():
                failures.append(f"{label}: 缺少 {field}")
        card_id = card.get("card_id")
        if isinstance(card_id, str) and card_id.strip():
            if card_id in seen_ids:
                failures.append(f"{label}: card_id 重复: {card_id}")
            seen_ids.add(card_id)
        subproblem_id = card.get("subproblem_id")
        if isinstance(subproblem_id, str) and subproblem_id.strip() and expected_ids and subproblem_id not in expected_ids:
            failures.append(f"{label}: subproblem_id 不在 problem_scope 中: {subproblem_id}")
        variables = card.get("decision_variables")
        if not isinstance(variables, list) or not variables:
            failures.append(f"{label}: decision_variables 必须为非空列表")
        else:
            for var_index, variable in enumerate(variables):
                var_label = f"{label}.decision_variables[{var_index}]"
                if not isinstance(variable, dict):
                    failures.append(f"{var_label}: 必须为对象")
                    continue
                for field in ("symbol", "meaning", "unit", "domain"):
                    if not isinstance(variable.get(field), str) or not variable[field].strip():
                        failures.append(f"{var_label}: 缺少 {field}")
        if not isinstance(card.get("parameters"), list):
            failures.append(f"{label}: parameters 必须为列表")
        formulation = card.get("final_formulation")
        if not isinstance(formulation, dict):
            failures.append(f"{label}: 缺少 final_formulation")
        else:
            for field in ("kind", "expression"):
                if not isinstance(formulation.get(field), str) or not formulation[field].strip():
                    failures.append(f"{label}: final_formulation 缺少 {field}")
        solver = card.get("solver_interface")
        if not isinstance(solver, dict):
            failures.append(f"{label}: 缺少 solver_interface")
        else:
            if not isinstance(solver.get("method"), str) or not solver["method"].strip():
                failures.append(f"{label}: solver_interface 缺少 method")
            for field in ("inputs", "outputs"):
                if not isinstance(solver.get(field), list) or not solver[field]:
                    failures.append(f"{label}: solver_interface.{field} 必须为非空列表")
        refs_for_card = card.get("source_equation_refs")
        if not isinstance(refs_for_card, list) or not refs_for_card:
            failures.append(f"{label}: source_equation_refs 必须为非空列表")
        structure = card.get("paper_structure")
        if not isinstance(structure, dict):
            failures.append(f"{label}: 缺少 paper_structure")
        else:
            if not isinstance(structure.get("opening_bridge"), str) or not structure["opening_bridge"].strip():
                failures.append(f"{label}: paper_structure 缺少 opening_bridge")
            if structure.get("numbered_sections") != list(QUESTION_NUMBERED_SECTIONS):
                failures.append(f"{label}: paper_structure.numbered_sections 结构不符合双小节规范")
            if structure.get("summary_location") != "模型建立小节末尾":
                failures.append(f"{label}: paper_structure.summary_location 必须为 模型建立小节末尾")
            if not isinstance(structure.get("optional_sections", []), list):
                failures.append(f"{label}: paper_structure.optional_sections 必须为列表")
        if reader_protocol_enabled:
            failures.extend(validate_model_card(card, label))
    if expected_ids:
        card_subproblem_ids = {
            item.get("subproblem_id") for item in cards
            if isinstance(item, dict) and isinstance(item.get("subproblem_id"), str)
        }
        if card_subproblem_ids != expected_ids:
            failures.append("model_summary_cards: cards 必须逐一覆盖且只能覆盖 problem_scope.subproblems")


def _validate_paper_continuity_context(root: Path, node: dict[str, Any],
                                       missing: list[str], failures: list[str]) -> None:
    """Require a compact reader-path context for each H8B chapter draft."""
    if node.get("writing_started") is not True:
        return
    brief_path, brief = _load_project_mapping(
        root, node.get("paper_author_brief"), "H8: paper_author_brief", missing, failures
    )
    context_path, context = _load_project_mapping(
        root, node.get("paper_continuity_context"),
        "H8: paper_continuity_context", missing, failures,
    )
    if brief_path is None or brief is None or context_path is None or context is None:
        return
    if context.get("status") not in {"ready", "current", "approved"}:
        failures.append("paper_continuity_context: status 必须为 ready/current/approved")
    if not same_digest(context.get("paper_author_brief_sha256"), digest(brief_path)):
        failures.append("paper_continuity_context: paper_author_brief_sha256 与作者简报不匹配")
    brief_spine = _validate_paper_spine(
        brief.get("paper_spine"), "paper_author_brief.paper_spine", failures,
    )
    context_spine = _validate_paper_spine(
        context.get("paper_spine"), "paper_continuity_context.paper_spine", failures,
    )
    if brief_spine is not None and context_spine is not None and brief_spine != context_spine:
        failures.append("paper_continuity_context.paper_spine 必须与作者简报保持一致")
    for field in (
        "central_thesis", "reader_journey", "current_chapter_id",
        "previous_section_takeaway", "next_section_question", "voice",
    ):
        if not isinstance(context.get(field), str) or not context[field].strip():
            failures.append(f"paper_continuity_context: 缺少 {field}")
    for field in ("central_thesis", "reader_journey"):
        brief_value = brief.get(field)
        context_value = context.get(field)
        if isinstance(brief_value, str) and brief_value.strip() and context_value != brief_value:
            failures.append(f"paper_continuity_context: {field} 与作者简报不一致")
    for field in ("completed_chapters", "terminology_lock"):
        if not isinstance(context.get(field), list):
            failures.append(f"paper_continuity_context: {field} 必须为列表")

    active_card_path, active_card = _load_project_mapping(
        root, node.get("active_chapter_card"),
        "H8: active_chapter_card", missing, failures,
    )
    if active_card_path is None or active_card is None:
        return
    if not same_digest(context.get("chapter_writing_card_sha256"), digest(active_card_path)):
        failures.append("paper_continuity_context: chapter_writing_card_sha256 与当前章节卡不匹配")
    if context.get("current_chapter_id") != active_card.get("chapter_id"):
        failures.append("paper_continuity_context: current_chapter_id 与 active_chapter_card 不匹配")
    if context_spine is not None and context.get("current_chapter_id") not in context_spine["chapter_order"]:
        failures.append("paper_continuity_context: current_chapter_id 不在 paper_spine.chapter_order 中")
    completed = context.get("completed_chapters")
    if isinstance(completed, list):
        completed_ids: list[str] = []
        for index, item in enumerate(completed):
            if not isinstance(item, dict):
                failures.append(f"paper_continuity_context.completed_chapters[{index}] 必须为对象")
                continue
            for field in ("section_id", "takeaway"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    failures.append(f"paper_continuity_context.completed_chapters[{index}]: 缺少 {field}")
            if isinstance(item.get("section_id"), str) and item["section_id"].strip():
                completed_ids.append(item["section_id"].strip())
        if context_spine is not None:
            current_index = context_spine["chapter_order"].index(context.get("current_chapter_id")) \
                if context.get("current_chapter_id") in context_spine["chapter_order"] else None
            for completed_id in completed_ids:
                if completed_id not in context_spine["chapter_order"]:
                    failures.append(f"paper_continuity_context: completed chapter {completed_id} 不在 paper_spine 中")
                elif current_index is not None and context_spine["chapter_order"].index(completed_id) >= current_index:
                    failures.append(f"paper_continuity_context: completed chapter {completed_id} 必须位于当前章节之前")


def _validate_chapter_writing_cards(root: Path, node: dict[str, Any],
                                    missing: list[str], failures: list[str],
                                    control: dict[str, Any] | None = None) -> None:
    """Require each active H8 draft to be scoped by an author-brief-derived card."""
    if node.get("writing_started") is not True:
        return
    brief_path, brief = _load_project_mapping(
        root, node.get("paper_author_brief"), "H8: paper_author_brief", missing, failures
    )
    if brief_path is None or brief is None:
        return
    reader_protocol_enabled = _reader_protocol_state(
        control, brief, "paper_author_brief", failures,
    )
    chapter_map = {
        item.get("section_id"): item
        for item in brief.get("chapters", [])
        if isinstance(item, dict) and isinstance(item.get("section_id"), str)
    }
    brief_spine = _validate_paper_spine(
        brief.get("paper_spine"), "paper_author_brief.paper_spine", failures,
    )
    cards = node.get("chapter_writing_cards")
    if not isinstance(cards, list) or not cards:
        missing.append("H8: writing_started=true 时必须登记 chapter_writing_cards（至少一个 chapter_writing_card）")
        return
    active_card = node.get("active_chapter_card")
    if not isinstance(active_card, str) or not active_card.strip():
        missing.append("H8: writing_started=true 时必须登记 active_chapter_card")
    elif active_card not in cards:
        failures.append("H8: active_chapter_card 必须出现在 chapter_writing_cards 中")
    seen_chapters: set[str] = set()
    for index, raw_path in enumerate(cards):
        label = f"H8: chapter_writing_cards[{index}]"
        path, card = _load_project_mapping(root, raw_path, label, missing, failures)
        if path is None or card is None:
            continue
        if card.get("status") not in {"ready", "drafted", "reviewed"}:
            failures.append(f"{label}: status 必须为 ready/drafted/reviewed")
        if not same_digest(card.get("prepared_from_author_brief_sha256"), digest(brief_path)):
            failures.append(f"{label}: prepared_from_author_brief_sha256 与作者简报不匹配")
        chapter_id = card.get("chapter_id")
        if not isinstance(chapter_id, str) or not chapter_id.strip():
            failures.append(f"{label}: 缺少 chapter_id")
            continue
        if chapter_id in seen_chapters:
            failures.append(f"{label}: chapter_id 重复: {chapter_id}")
        seen_chapters.add(chapter_id)
        brief_chapter = chapter_map.get(chapter_id)
        if brief_chapter is None:
            failures.append(f"{label}: chapter_id 不在 paper_author_brief 中: {chapter_id}")
            continue
        for field in CHAPTER_RELATION_FIELDS:
            if card.get(field) != brief_chapter.get(field):
                failures.append(f"{label}: {field} 必须与作者简报中的当前章节一致")
        for field in ("reader_question", "chapter_purpose", "chapter_answer", "reader_takeaway", "writer_instruction"):
            if not isinstance(card.get(field), str) or not card[field].strip():
                failures.append(f"{label}: 缺少 {field}")
        for field in ("argument_ids", "evidence_refs", "figure_roles", "excluded_material"):
            if not isinstance(card.get(field), list):
                failures.append(f"{label}: {field} 必须为列表")
        contribution = card.get("abstract_contribution")
        if not isinstance(contribution, dict):
            failures.append(f"{label}: 缺少 abstract_contribution（H8B 必须向 H8C 提供摘要证据）")
        else:
            for field in ("method", "result", "meaning"):
                if not isinstance(contribution.get(field), str) or not contribution[field].strip():
                    failures.append(f"{label}: abstract_contribution 缺少 {field}")
            contribution_refs = contribution.get("evidence_refs")
            if not isinstance(contribution_refs, list) or not contribution_refs:
                failures.append(f"{label}: abstract_contribution.evidence_refs 必须为非空列表")
        if reader_protocol_enabled:
            _reader_protocol_state(control, card, label, failures)
            failures.extend(validate_author_chapter(card, label))
        card_arguments = {
            item for item in (card.get("argument_ids") if isinstance(card.get("argument_ids"), list) else [])
            if isinstance(item, str)
        }
        if brief_spine is not None:
            _validate_chapter_relation(label, card, brief_spine, failures, card_arguments)
        is_modeling_question = (
            brief_chapter.get("chapter_kind") in {"modeling", "modeling_question"}
            or chapter_id.upper().startswith("Q")
        )
        if is_modeling_question:
            _validate_question_structure(label, card, failures)
            summary_ref = card.get("model_summary_card")
            if not isinstance(summary_ref, str) or not summary_ref.strip():
                failures.append(f"{label}: 缺少 model_summary_card")
            elif node.get("model_summary_cards") and summary_ref != node.get("model_summary_cards"):
                failures.append(f"{label}: model_summary_card 与节点登记的 model_summary_cards 不一致")
        brief_argument_values = brief_chapter.get("argument_ids")
        card_argument_values = card.get("argument_ids")
        brief_arguments = {
            item for item in (brief_argument_values if isinstance(brief_argument_values, list) else [])
            if isinstance(item, str)
        }
        card_arguments = {
            item for item in (card_argument_values if isinstance(card_argument_values, list) else [])
            if isinstance(item, str)
        }
        if not card_arguments.issubset(brief_arguments):
            failures.append(f"{label}: argument_ids 超出作者简报的当前章节范围")
        brief_figure_values = brief_chapter.get("figure_roles")
        card_figure_values = card.get("figure_roles")
        brief_figures = {
            item for item in (brief_figure_values if isinstance(brief_figure_values, list) else [])
            if isinstance(item, str)
        }
        card_figures = {
            item for item in (card_figure_values if isinstance(card_figure_values, list) else [])
            if isinstance(item, str)
        }
        if not card_figures.issubset(brief_figures):
            failures.append(f"{label}: figure_roles 超出作者简报的当前章节范围")
        brief_refs = {
            (item.get("path"), item.get("sha256"))
            for item in (brief_chapter.get("evidence_refs") if isinstance(brief_chapter.get("evidence_refs"), list) else [])
            if isinstance(item, dict)
            and isinstance(item.get("path"), str)
            and isinstance(item.get("sha256"), str)
        }
        for reference in card.get("evidence_refs", []):
            if not isinstance(reference, dict):
                failures.append(f"{label}: evidence_refs 含无效条目")
                continue
            if (reference.get("path"), reference.get("sha256")) not in brief_refs:
                failures.append(f"{label}: evidence_refs 超出作者简报的当前章节范围")


def _validate_validation_contract(root: Path, nodes: dict[str, Any], through: str,
                                  missing: list[str], failures: list[str]) -> None:
    """验证契约校验：H5 产出关键结论/接口值/符号/自验声明，H6 依据契约核对。"""
    if NODES.index(through) < NODES.index("H6"):
        return
    h5 = nodes.get("H5", {})
    path, contract = _load_project_mapping(root, h5.get("validation_contract"),
                                           "H5: validation_contract", missing, failures)
    if path is None or contract is None:
        return
    status = contract.get("status")
    if status not in {"draft", "verified", "rejected"}:
        failures.append("validation_contract: status 必须为 draft/verified/rejected")
    elif status != "verified":
        failures.append(f"validation_contract: H6 完成后必须为 verified（当前: {status}）")
    if not isinstance(contract.get("key_conclusions"), list) or not contract["key_conclusions"]:
        failures.append("validation_contract: key_conclusions 必须为非空列表")
    if not isinstance(contract.get("interface_values"), dict) or not contract["interface_values"]:
        failures.append("validation_contract: interface_values 必须为非空对象")
    if not isinstance(contract.get("symbol_definitions"), list) or not contract["symbol_definitions"]:
        failures.append("validation_contract: symbol_definitions 必须为非空列表")
    if not isinstance(contract.get("self_verified"), list) or not contract["self_verified"]:
        failures.append("validation_contract: self_verified 必须为非空列表")


def _validate_dispatch_records(root: Path, control: dict[str, Any], nodes: dict[str, Any],
                               runtime_routes: dict[str, Any], through: str, missing: list[str],
                               failures: list[str]) -> None:
    records = control.get("dispatch_records")
    if not isinstance(records, list):
        failures.append("dispatch_records 必须为列表")
        return
    records_by_task: dict[str, dict[str, Any]] = {}
    cards_by_task: dict[str, dict[str, Any]] = {}
    through_nodes = set(NODES[:NODES.index(through) + 1])
    for index, record in enumerate(records):
        label = f"dispatch_records[{index}]"
        if not isinstance(record, dict):
            failures.append(f"{label}: 条目必须为对象")
            continue
        absent = [field for field in DISPATCH_FIELDS if not str(record.get(field, "")).strip()]
        if absent:
            failures.append(f"{label}: 缺字段 {','.join(absent)}")
            continue
        task_id = record["task_id"]
        if task_id in records_by_task:
            failures.append(f"{label}: task_id 必须唯一")
            continue
        node_id = record["node_id"]
        if node_id not in AGENT_NODES:
            failures.append(f"{label}: 只允许登记实际子 agent 节点")
            continue
        card_path, card = _load_project_mapping(root, record["task_card_path"], label, missing, failures)
        if card_path is None or card is None:
            continue
        if not same_digest(record["task_card_sha256"], digest(card_path)):
            failures.append(f"{label}: 任务卡 SHA-256 不匹配")
        for field in ("task_id", "node_id", "owner_role", "model", "reasoning_effort"):
            if record.get(field) != card.get(field):
                failures.append(f"{label}: {field} 与任务卡不一致")
        # P1-03: dispatched_at 必须为 ISO 时间戳
        dispatched_at = record.get("dispatched_at")
        if isinstance(dispatched_at, str) and dispatched_at.strip():
            try:
                datetime.fromisoformat(dispatched_at.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                failures.append(f"{label}: dispatched_at 必须为 ISO 时间戳格式（当前: {dispatched_at}）")
        # P1-03: harness_run_id 校验（把实例、任务卡和 dispatch 记录绑定到同一运行）
        harness_run_id = control.get("harness_run_id")
        record_run_id = record.get("harness_run_id")
        if isinstance(harness_run_id, str) and harness_run_id.strip():
            if not isinstance(record_run_id, str) or not record_run_id.strip():
                failures.append(f"{label}: 缺少 harness_run_id（必须与主控运行 ID 绑定）")
            elif record_run_id != harness_run_id:
                failures.append(f"{label}: harness_run_id({record_run_id}) 与主控运行 ID({harness_run_id}) 不一致")
        # P1-03: spawn_receipt 校验（原生 spawn_agent 包装层生成的不可歧义收据）
        receipt = record.get("spawn_receipt")
        if not isinstance(receipt, dict):
            missing.append(f"{label}: 缺少 spawn_receipt（原生 spawn 收据，用于证明 agent 实际被调用）")
        else:
            receipt_task_id = receipt.get("task_id")
            receipt_agent_id = receipt.get("agent_instance_id")
            receipt_card_sha = receipt.get("task_card_sha256")
            receipt_model = receipt.get("model")
            receipt_effort = receipt.get("reasoning_effort")
            if receipt_task_id != task_id:
                failures.append(f"{label}: spawn_receipt.task_id({receipt_task_id}) 与 dispatch task_id({task_id}) 不一致")
            if isinstance(receipt_agent_id, str) and receipt_agent_id.strip() and receipt_agent_id != record.get("agent_instance_id"):
                failures.append(f"{label}: spawn_receipt.agent_instance_id({receipt_agent_id}) 与 dispatch agent_instance_id 不一致")
            if isinstance(receipt_card_sha, str) and receipt_card_sha.strip() and not same_digest(receipt_card_sha, record.get("task_card_sha256")):
                failures.append(f"{label}: spawn_receipt.task_card_sha256 与 dispatch task_card_sha256 不一致")
            if isinstance(receipt_model, str) and receipt_model.strip() and receipt_model != record.get("model"):
                failures.append(f"{label}: spawn_receipt.model 与 dispatch model 不一致")
            if isinstance(receipt_effort, str) and receipt_effort.strip() and receipt_effort != record.get("reasoning_effort"):
                failures.append(f"{label}: spawn_receipt.reasoning_effort 与 dispatch reasoning_effort 不一致")
        records_by_task[task_id] = record
        cards_by_task[task_id] = card

    registered_instance_ids: set[str] = set()
    instances_raw = control.get("agent_instances")
    if isinstance(instances_raw, dict):
        for entry in instances_raw.values():
            if isinstance(entry, dict):
                iid = entry.get("agent_instance_id")
                if isinstance(iid, str) and iid.strip():
                    registered_instance_ids.add(iid)
    for record in records_by_task.values():
        rid = record.get("agent_instance_id")
        if registered_instance_ids and isinstance(rid, str) and rid not in registered_instance_ids:
            failures.append(f"dispatch_records: agent_instance_id {rid} 未在 agent_instances 注册")

    for node_id in AGENT_NODES:
        if node_id not in through_nodes:
            continue
        node = nodes.get(node_id, {})
        card_path, card = _load_project_mapping(root, node.get("task_card"), f"{node_id}: 主任务卡", missing, failures)
        if card_path is None or card is None:
            continue
        record = records_by_task.get(card.get("task_id"))
        if record is None:
            missing.append(f"{node_id}: 缺少主任务卡对应的 dispatch_record")
            continue
        if record.get("agent_instance_id") != node.get("agent_instance_id"):
            failures.append(f"{node_id}: dispatch_record 与节点 agent_instance_id 不一致")
        expected_runtime = runtime_routes.get(node_id, {})
        if record.get("model") != expected_runtime.get("model") or record.get("reasoning_effort") != expected_runtime.get("reasoning_effort"):
            failures.append(f"{node_id}: dispatch_record 不符合节点模型路由")

    if "H5" not in through_nodes:
        return
    solver_instance_id = control.get("solver_instance_id")
    if not isinstance(solver_instance_id, str) or not solver_instance_id.strip():
        failures.append("H5: 缺少唯一 solver_instance_id")
        return
    for record in records_by_task.values():
        recorded_solver_id = record.get("solver_instance_id")
        if recorded_solver_id not in (None, "") and recorded_solver_id != solver_instance_id:
            failures.append(f"{record.get('node_id')}: dispatch_record 引入了非本次运行的 solver_instance_id")
    h5_records = [(record, cards_by_task.get(task_id, {})) for task_id, record in records_by_task.items()
                  if record.get("node_id") == "H5"]
    primary = [(record, card) for record, card in h5_records if card.get("dispatch_kind") == "primary_solver"]
    if not primary:
        failures.append("H5: 必须至少有一个 primary_solver 调度")
    else:
        primary_solver_ids = {record.get("solver_instance_id") for record, _ in primary if isinstance(record.get("solver_instance_id"), str)}
        if len(primary_solver_ids) > 1:
            failures.append(f"H5: 存在多个不同 solver_instance_id 的主解题实例: {primary_solver_ids}")
        if len(primary) > 1:
            first_task_id = primary[0][0].get("task_id")
            for record, _ in primary[1:]:
                if not isinstance(record.get("rework_of"), str) or not record["rework_of"].strip():
                    failures.append(f"H5: 第2条及以后的 primary_solver 必须有 rework_of 指向原始 task_id（{record.get('task_id')} 缺失）")
                elif record["rework_of"] != first_task_id:
                    failures.append(f"H5: rework_of 必须指向首次 primary_solver task_id={first_task_id}（当前: {record['rework_of']}）")
    problem_scope = control.get("problem_scope")
    declared_subproblems: set[str] = set()
    if not isinstance(problem_scope, dict):
        failures.append("H5: problem_scope 必须为对象")
    else:
        raw_subproblems = problem_scope.get("subproblems")
        if not isinstance(raw_subproblems, list) or not raw_subproblems:
            failures.append("H5: problem_scope.subproblems 必须为非空列表")
        else:
            normalized = []
            valid = True
            for item in raw_subproblems:
                if isinstance(item, str) and item.strip():
                    normalized.append(item.strip())
                elif isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip():
                    normalized.append(item["id"].strip())
                else:
                    valid = False
                    break
            if not valid:
                failures.append("H5: problem_scope.subproblems 含无效小问标识（必须为字符串或含 id 的对象）")
            elif len(set(normalized)) != len(normalized):
                failures.append("H5: problem_scope.subproblems 不得重复")
            else:
                declared_subproblems = set(normalized)
    if len(primary) >= 1 and declared_subproblems:
        _, primary_card = primary[0]
        covered_subproblems = primary_card.get("covered_subproblems")
        if not isinstance(covered_subproblems, list):
            failures.append("H5: 主解题实例 covered_subproblems 必须为列表")
        elif any(not isinstance(item, str) for item in covered_subproblems):
            failures.append("H5: 主解题实例 covered_subproblems 含非字符串元素")
        elif set(covered_subproblems) != declared_subproblems or len(covered_subproblems) != len(declared_subproblems):
            failures.append("H5: 主解题实例必须恰好覆盖 problem_scope 的全部小问")
        if primary_card.get("cross_question_interface") is not True:
            failures.append("H5: 主解题实例必须承担跨问接口责任")
    for record, card in h5_records:
        dispatch_kind = card.get("dispatch_kind")
        authority = card.get("authority")
        if not isinstance(authority, dict):
            failures.append(f"H5: {record.get('task_id')} 缺少 authority")
            continue
        if dispatch_kind == "primary_solver":
            if card.get("owner_role") != "解题 agent" or record.get("solver_instance_id") != solver_instance_id:
                failures.append(f"H5: {record.get('task_id')} 主解题实例不一致")
            if card.get("solver_instance_id") != solver_instance_id:
                failures.append(f"H5: {record.get('task_id')} 任务卡 solver_instance_id 不一致")
        elif dispatch_kind == "conditional_support":
            if card.get("owner_role") != "辅助 agent" or record.get("solver_instance_id") not in (None, ""):
                failures.append(f"H5: {record.get('task_id')} 辅助 agent 身份不合法")
            if card.get("parent_solver_instance_id") != solver_instance_id:
                failures.append(f"H5: {record.get('task_id')} 未绑定唯一主解题实例")
            if any(authority.get(key) is not False for key in (
                "may_change_model_route", "may_write_final_results", "may_aggregate_conclusions",
            )):
                failures.append(f"H5: {record.get('task_id')} 辅助 agent 越权")
            allowed = card.get("allowed_output_kinds", [])
            if not isinstance(allowed, list) or not allowed or any(kind not in {
                "local_computation_evidence", "data_processing_evidence", "code_experiment_evidence",
            } for kind in allowed):
                failures.append(f"H5: {record.get('task_id')} 辅助输出类型不合法")
        else:
            failures.append(f"H5: {record.get('task_id')} dispatch_kind 不合法")
    h5_node = nodes.get("H5", {})
    if h5_node.get("solver_instance_id") != solver_instance_id:
        failures.append("H5: 节点 solver_instance_id 不一致")
    if "H6" in through_nodes and nodes.get("H6", {}).get("agent_instance_id") == h5_node.get("agent_instance_id"):
        failures.append("H6: 必须使用与 H5 不同的 agent_instance_id")


def _validate_h1_problem_statement(root: Path, node: dict[str, Any],
                                    missing: list[str], failures: list[str]) -> None:
    if node.get("status") == "not_started":
        return
    raw = node.get("problem_statement")
    if not raw:
        missing.append("H1: 缺少 problem_statement 产物路径")
    else:
        path = resolve_project_path(root, raw)
        if path is None or not path.is_file():
            missing.append("H1: problem_statement 文件不存在")
        elif path.stat().st_size == 0:
            failures.append("H1: problem_statement.md 为空")
    # unified_problem_package.yaml：机器可读事实权威，H1 必须产出
    raw_up = node.get("unified_problem_package")
    if not raw_up:
        missing.append("H1: 缺少 unified_problem_package 产物路径")
        return
    up_path = resolve_project_path(root, raw_up)
    if up_path is None or not up_path.is_file():
        missing.append("H1: unified_problem_package 文件不存在")
        return
    if up_path.stat().st_size == 0:
        failures.append("H1: unified_problem_package.yaml 为空")
    # 原始题面文件：H1 必须登记原始题面路径和 SHA-256，检查器重新计算核对
    raw_original = node.get("original_problem_file")
    if not isinstance(raw_original, str) or not raw_original.strip():
        missing.append("H1: 缺少 original_problem_file（原始题面文件路径）")
    else:
        original_path = resolve_project_path(root, raw_original)
        if original_path is None or not original_path.is_file():
            failures.append(f"H1: original_problem_file 文件不存在: {raw_original}")
        elif original_path.stat().st_size == 0:
            failures.append("H1: original_problem_file 为空")
        else:
            original_sha = node.get("original_problem_sha256")
            if not isinstance(original_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", original_sha):
                failures.append("H1: original_problem_sha256 必须为 64 位十六进制字符串")
            elif not same_digest(original_sha, digest(original_path)):
                failures.append(f"H1: original_problem_sha256 与原始题面文件不匹配（声明: {original_sha[:16]}…, 实际: {digest(original_path)[:16]}…）")


def _validate_h6_interface(root: Path, nodes: dict[str, Any], problem_scope: dict[str, Any],
                            missing: list[str], failures: list[str]) -> None:
    path, report = _load_project_mapping(root, nodes.get("H6", {}).get("global_interface_check"),
                                         "H6: global_interface_check", missing, failures)
    if path is None or report is None:
        return
    status = report.get("status")
    if status not in {"PASS", "PAUSE"}:
        failures.append("H6: global_interface_check status 必须为 PASS 或 PAUSE")
        return
    checks = report.get("checks")
    if not isinstance(checks, dict):
        failures.append("H6: global_interface_check checks 必须为对象")
        return
    failed_checks = [name for name in INTERFACE_CHECKS if checks.get(name) is not True]
    if status == "PAUSE" or failed_checks:
        missing.append(f"H6: 跨问接口待修复 {','.join(failed_checks) or 'reported_issue'}")
    if not isinstance(report.get("issues"), list):
        failures.append("H6: global_interface_check issues 必须为列表")
    elif status == "PASS" and report.get("issues"):
        failures.append("H6: global_interface_check status=PASS 时 issues 必须为空")
    verified_by = report.get("verified_by")
    if verified_by != "H6":
        failures.append(f"H6: global_interface_check verified_by 必须为 H6（当前: {verified_by}）")
    h6_instance = report.get("verification_agent_instance_id")
    h6_node_instance = nodes.get("H6", {}).get("agent_instance_id")
    if not isinstance(h6_instance, str) or not h6_instance.strip():
        failures.append("H6: global_interface_check 缺少 verification_agent_instance_id")
    elif isinstance(h6_node_instance, str) and h6_node_instance.strip() and h6_instance != h6_node_instance:
        failures.append(f"H6: verification_agent_instance_id({h6_instance}) 与当前 H6 节点实例({h6_node_instance}) 不一致")
    else:
        h5 = nodes.get("H5", {})
        h5_instance = h5.get("agent_instance_id") or h5.get("solver_instance_id")
        if isinstance(h5_instance, str) and h5_instance.strip() and h6_instance == h5_instance:
            failures.append("H6: 验证实例与 H5 解题实例相同，违反独立验证要求")
    task_card_path = report.get("task_card_path")
    if not isinstance(task_card_path, str) or not task_card_path.strip():
        failures.append("H6: global_interface_check 必须登记 task_card_path")
    else:
        h6_card_raw = nodes.get("H6", {}).get("task_card")
        if isinstance(h6_card_raw, str) and h6_card_raw.strip() and task_card_path != h6_card_raw:
            failures.append(f"H6: interface task_card_path({task_card_path}) 与 H6 任务卡({h6_card_raw}) 不一致")
        tc_path = resolve_project_path(root, task_card_path)
        if tc_path is None or not tc_path.is_file():
            failures.append(f"H6: interface task_card_path 文件不存在: {task_card_path}")
        else:
            tc_sha = report.get("task_card_sha256")
            if not isinstance(tc_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", tc_sha):
                failures.append("H6: task_card_sha256 必须为 64 位十六进制字符串")
            elif not same_digest(tc_sha, digest(tc_path)):
                failures.append("H6: task_card_sha256 与 H6 任务卡不匹配")
    per_sub = report.get("per_subproblem")
    if not isinstance(per_sub, list) or not per_sub:
        failures.append("H6: global_interface_check 必须含非空 per_subproblem 列表（逐问接口明细）")
    else:
        scope_subs = problem_scope.get("subproblems") if isinstance(problem_scope, dict) else None
        expected_subs: set[str] = set()
        if isinstance(scope_subs, list):
            for item in scope_subs:
                if isinstance(item, str) and item.strip():
                    expected_subs.add(item.strip())
                elif isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip():
                    expected_subs.add(item["id"].strip())
        targeted_subproblems = _h6_targeted_scope(root, nodes)
        if targeted_subproblems is not None:
            expected_subs = expected_subs.intersection(targeted_subproblems)
        actual_subs: set[str] = set()
        for idx, sub in enumerate(per_sub):
            if not isinstance(sub, dict):
                failures.append(f"H6: per_subproblem[{idx}] 必须为对象")
                continue
            sid = sub.get("subproblem_id") or sub.get("id")
            if not isinstance(sid, str) or not sid.strip():
                failures.append(f"H6: per_subproblem[{idx}] 缺少 subproblem_id")
                continue
            actual_subs.add(sid.strip())
            ifields = sub.get("interface_fields")
            if not isinstance(ifields, list) or not ifields:
                failures.append(f"H6: per_subproblem[{sid}] 缺少 interface_fields（逐问接口字段明细）")
            else:
                # P1-02: 校验 interface_fields 内容，拒绝占位字段
                has_structured = any(isinstance(f, dict) for f in ifields)
                has_string = any(isinstance(f, str) for f in ifields)
                if has_string and not has_structured:
                    # 旧格式：字符串列表，产生 WARN 建议升级
                    failures.append(f"H6: per_subproblem[{sid}] interface_fields 为旧格式字符串列表，建议升级为结构化对象（含 field/unit/source_path/comparison_status）")
                elif has_structured:
                    # 新格式：结构化对象，校验必填字段
                    for fidx, ifield in enumerate(ifields):
                        if not isinstance(ifield, dict):
                            failures.append(f"H6: per_subproblem[{sid}] interface_fields[{fidx}] 必须为对象或字符串")
                            continue
                        field_name = ifield.get("field")
                        if not isinstance(field_name, str) or not field_name.strip():
                            failures.append(f"H6: per_subproblem[{sid}] interface_fields[{fidx}] 缺少 field 字段名")
                        elif field_name.strip().lower() in {"placeholder", "test", "todo", "xxx", "none"}:
                            failures.append(f"H6: per_subproblem[{sid}] interface_fields[{fidx}] field 为占位值（{field_name}），必须登记真实接口字段")
                        comp_status = ifield.get("comparison_status")
                        if not isinstance(comp_status, str) or not comp_status.strip():
                            missing.append(f"H6: per_subproblem[{sid}] interface_fields[{fidx}] 缺少 comparison_status")
                        elif comp_status.strip().lower() not in {"pass", "passed", "consistent", "match", "verified"}:
                            failures.append(f"H6: per_subproblem[{sid}] interface_fields[{fidx}] comparison_status 无效（{comp_status}），必须为 pass/passed/consistent/match/verified")
                        # C-03: every structured field must carry a real source and
                        # its current digest.  Absence pauses the gate; malformed
                        # or stale provenance is a hard integrity failure.
                        source_path = ifield.get("source_path")
                        if not isinstance(source_path, str) or not source_path.strip():
                            missing.append(f"H6: per_subproblem[{sid}] interface_fields[{fidx}] 缺少 source_path")
                            source_sha = ifield.get("source_sha256")
                            if not isinstance(source_sha, str) or not source_sha.strip():
                                missing.append(f"H6: per_subproblem[{sid}] interface_fields[{fidx}] 缺少 source_sha256")
                            continue
                        sp = resolve_project_path(root, source_path)
                        if sp is None or not sp.is_file():
                            failures.append(f"H6: per_subproblem[{sid}] interface_fields[{fidx}] source_path 文件不存在: {source_path}")
                            continue
                        source_sha = ifield.get("source_sha256")
                        if not isinstance(source_sha, str) or not source_sha.strip():
                            missing.append(f"H6: per_subproblem[{sid}] interface_fields[{fidx}] 缺少 source_sha256")
                        elif not re.fullmatch(r"[0-9a-fA-F]{64}", source_sha):
                            failures.append(f"H6: per_subproblem[{sid}] interface_fields[{fidx}] source_sha256 必须为 64 位十六进制字符串")
                        elif digest(sp).lower() != source_sha.lower():
                            failures.append(f"H6: per_subproblem[{sid}] interface_fields[{fidx}] source_sha256 不匹配: {source_path}")
        if expected_subs:
            missing_subs = expected_subs - actual_subs
            if missing_subs:
                failures.append(f"H6: per_subproblem 未覆盖全部小问，缺少 {','.join(sorted(missing_subs))}")


def _validate_h5_result_traceability_registration(root: Path, node: dict[str, Any],
                                                   missing: list[str], failures: list[str]) -> None:
    """Run the H5 evidence-package gate when H5 has reached a reviewable state."""
    if not isinstance(node, dict) or node.get("status") not in {
        "review_pending", "approved", "frozen", "evidence_gap", "stale",
    }:
        return
    run_manifest = node.get("run_manifest")
    if not isinstance(run_manifest, str) or not run_manifest.strip():
        missing.append("H5: 缺少 run_manifest（H5 结果追溯包登记）")
        return
    report = validate_h5_result_traceability(
        root,
        run_manifest=run_manifest,
        sensitivity_report=node.get("sensitivity_report") if isinstance(node.get("sensitivity_report"), str) else None,
    )
    missing.extend(f"{item}" for item in report.get("missing", []))
    failures.extend(f"{item}" for item in report.get("failures", []))


def _collect_material_gaps(root: Path, readiness: dict[str, Any], failures: list[str]) -> tuple[list[dict[str, str]], dict[tuple[str, str], tuple[str, str]]]:
    gaps: list[dict[str, str]] = []
    material_refs: dict[tuple[str, str], tuple[str, str]] = {}
    subproblems = readiness.get("subproblems")
    if not isinstance(subproblems, list) or not subproblems:
        failures.append("paper_material_readiness: subproblems 必须为非空列表")
        return gaps, material_refs
    for item in subproblems:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
            failures.append("paper_material_readiness: 子问题 id 无效")
            continue
        qid = item["id"]
        materials = item.get("materials")
        if not isinstance(materials, dict):
            failures.append(f"paper_material_readiness: {qid} materials 必须为对象")
            continue
        for field in MATERIAL_FIELDS:
            fresh, ref = _reference_is_fresh(root, materials.get(field))
            if not fresh or ref is None:
                gaps.append({"subproblem_id": qid, "requirement": field, "responsible_node": MATERIAL_OWNER[field]})
            else:
                material_refs[(qid, field)] = ref
        # P0-03: 灵敏度/稳健性证据硬门
        sens = materials.get("sensitivity_or_robustness")
        if not isinstance(sens, dict):
            gaps.append({"subproblem_id": qid, "requirement": "sensitivity_or_robustness", "responsible_node": "H6"})
        else:
            if sens.get("not_applicable") is True:
                reason = sens.get("not_applicable_reason")
                if not isinstance(reason, str) or not reason.strip():
                    failures.append(f"paper_material_readiness: {qid} sensitivity_or_robustness.not_applicable=true 但未提供 not_applicable_reason")
            else:
                fresh, ref = _reference_is_fresh(root, {"path": sens.get("path"), "sha256": sens.get("sha256")})
                if not fresh or ref is None:
                    gaps.append({"subproblem_id": qid, "requirement": "sensitivity_or_robustness", "responsible_node": "H6"})
                else:
                    material_refs[(qid, "sensitivity_or_robustness")] = ref
    target_length = readiness.get("target_length", {})
    sections = target_length.get("sections") if isinstance(target_length, dict) else None
    if not isinstance(sections, list) or not sections:
        gaps.append({"subproblem_id": "GLOBAL", "requirement": "target_length", "responsible_node": "H5"})
    else:
        body_page_total = 0.0
        for section in sections:
            if not isinstance(section, dict):
                gaps.append({"subproblem_id": "GLOBAL", "requirement": "target_length", "responsible_node": "H5"})
                break
            page_count = section.get("page_count")
            if page_count is not None:
                if not isinstance(page_count, (int, float)) or isinstance(page_count, bool) or page_count <= 0:
                    failures.append(f"paper_material_readiness: 章节 page_count 无效（必须为正数）: {page_count}")
                elif section.get("chapter_type") not in ("appendix",):
                    body_page_total += page_count
            chapter_type = section.get("chapter_type", "evidence")
            if chapter_type == "narrative_only":
                # 叙事型章节（摘要/问题分析/结论）只读叙事蓝图，不强制素材文件
                if section.get("capacity_status") != "adequate":
                    gaps.append({"subproblem_id": "GLOBAL", "requirement": "target_length", "responsible_node": "H5"})
                    break
                continue
            refs = section.get("material_refs")
            section_ok = section.get("capacity_status") == "adequate" and isinstance(refs, list) and bool(refs)
            if section_ok:
                section_ok = all(_reference_is_fresh(root, ref)[0] for ref in refs)
            if not section_ok:
                gaps.append({"subproblem_id": "GLOBAL", "requirement": "target_length", "responsible_node": "H5"})
                break
        if body_page_total > 30:
            failures.append(f"paper_material_readiness: 正文规划页数 {body_page_total} 超过硬上限 30 页")
    return gaps, material_refs


def _validate_evidence_matrix(readiness: dict[str, Any], gaps: list[dict[str, str]], failures: list[str]) -> None:
    """Validate the compact H8 readiness matrix when schema_version=2.0.

    The matrix is a human-readable summary of the existing material references;
    it does not replace their SHA-256 checks.  A ready cell is legal only when
    the corresponding material reference is fresh, so the summary cannot hide
    an evidence gap from the existing admission gate.
    """
    if str(readiness.get("schema_version", "1.0")) != "2.0":
        return
    matrix = readiness.get("evidence_matrix")
    if not isinstance(matrix, dict):
        failures.append("paper_material_readiness: schema_version=2.0 时必须提供 evidence_matrix")
        return
    expected_subproblems = {
        item.get("id") for item in readiness.get("subproblems", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item.get("id").strip()
    }
    actual_subproblems = {key for key in matrix if key != "global"}
    missing_subproblems = expected_subproblems - actual_subproblems
    unknown_subproblems = actual_subproblems - expected_subproblems
    if missing_subproblems:
        failures.append(f"paper_material_readiness.evidence_matrix 缺少小问 {','.join(sorted(missing_subproblems))}")
    if unknown_subproblems:
        failures.append(f"paper_material_readiness.evidence_matrix 存在未声明小问 {','.join(sorted(unknown_subproblems))}")

    gap_pairs = {
        (str(item.get("subproblem_id")), str(item.get("requirement")))
        for item in gaps
        if isinstance(item, dict)
    }
    for subproblem_id in sorted(expected_subproblems):
        checks = matrix.get(subproblem_id)
        if not isinstance(checks, dict):
            failures.append(f"paper_material_readiness.evidence_matrix.{subproblem_id} 必须为对象")
            continue
        absent = [field for field in EVIDENCE_MATRIX_FIELDS if field not in checks]
        if absent:
            failures.append(f"paper_material_readiness.evidence_matrix.{subproblem_id} 缺字段 {','.join(absent)}")
        for field in EVIDENCE_MATRIX_FIELDS:
            status = checks.get(field)
            if status not in EVIDENCE_MATRIX_STATUSES:
                failures.append(
                    f"paper_material_readiness.evidence_matrix.{subproblem_id}.{field} "
                    f"状态必须为 ready/missing/blocked/not_applicable（当前: {status}）"
                )
                continue
            pair = (subproblem_id, field)
            if field == "sensitivity_or_robustness":
                material = next(
                    (
                        item.get("materials", {}).get(field)
                        for item in readiness.get("subproblems", [])
                        if isinstance(item, dict) and item.get("id") == subproblem_id
                        and isinstance(item.get("materials"), dict)
                    ),
                    None,
                )
                expected_status = "not_applicable" if isinstance(material, dict) and material.get("not_applicable") is True else (
                    "missing" if pair in gap_pairs else "ready"
                )
            else:
                expected_status = "missing" if pair in gap_pairs else "ready"
            if expected_status == "ready" and status != "ready":
                failures.append(f"paper_material_readiness.evidence_matrix.{subproblem_id}.{field} 必须为 ready")
            elif expected_status == "not_applicable" and status != "not_applicable":
                failures.append(f"paper_material_readiness.evidence_matrix.{subproblem_id}.{field} 必须为 not_applicable")
            elif expected_status == "missing" and status not in {"missing", "blocked"}:
                failures.append(f"paper_material_readiness.evidence_matrix.{subproblem_id}.{field} 必须标记为 missing 或 blocked")

    global_checks = matrix.get("global")
    if not isinstance(global_checks, dict):
        failures.append("paper_material_readiness.evidence_matrix.global 必须为对象")
    else:
        target_status = global_checks.get("target_length")
        if target_status not in EVIDENCE_MATRIX_STATUSES:
            failures.append("paper_material_readiness.evidence_matrix.global.target_length 状态无效")
        target_gap = ("GLOBAL", "target_length") in gap_pairs
        expected_status = "missing" if target_gap else "ready"
        if expected_status == "ready" and target_status != "ready":
            failures.append("paper_material_readiness.evidence_matrix.global.target_length 必须为 ready")
        elif expected_status == "missing" and target_status not in {"missing", "blocked"}:
            failures.append("paper_material_readiness.evidence_matrix.global.target_length 必须标记为 missing 或 blocked")

    if readiness.get("status") == "PASS":
        for subproblem_id in sorted(expected_subproblems):
            checks = matrix.get(subproblem_id, {})
            if isinstance(checks, dict) and any(
                checks.get(field) not in {"ready", "not_applicable"} for field in EVIDENCE_MATRIX_FIELDS
            ):
                failures.append(f"paper_material_readiness: status=PASS 时 {subproblem_id} 仍存在未就绪证据单元")
        if isinstance(global_checks, dict) and global_checks.get("target_length") != "ready":
            failures.append("paper_material_readiness: status=PASS 时 global.target_length 必须为 ready")


def _validate_gap_matrix(root: Path, node: dict[str, Any], readiness_path: Path, gaps: list[dict[str, str]],
                         missing: list[str], failures: list[str]) -> None:
    path_value = node.get("evidence_gap_matrix")
    path, matrix = _load_project_mapping(root, path_value, "H8: evidence_gap_matrix", missing, failures)
    if path is None or matrix is None:
        return
    if not same_digest(matrix.get("readiness_sha256"), digest(readiness_path)):
        failures.append("H8: evidence_gap_matrix 未绑定当前 readiness 哈希")
    matrix_gaps = matrix.get("gaps")
    if not isinstance(matrix_gaps, list):
        failures.append("H8: evidence_gap_matrix gaps 必须为列表")
        return
    expected = {(gap["subproblem_id"], gap["requirement"], gap["responsible_node"]) for gap in gaps}
    actual: set[tuple[str, str, str]] = set()
    seen_gap_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    valid_responsible = {"H5", "H6", "H7"}
    for item in matrix_gaps:
        if not isinstance(item, dict):
            failures.append("H8: evidence_gap_matrix 条目无效")
            continue
        gap_id = item.get("gap_id")
        if not isinstance(gap_id, str) or not gap_id.strip():
            failures.append("H8: evidence_gap_matrix 条目缺少 gap_id")
        elif gap_id in seen_gap_ids:
            failures.append(f"H8: evidence_gap_matrix gap_id 重复: {gap_id}")
        else:
            seen_gap_ids.add(gap_id)
        absent = [field for field in ("subproblem_id", "requirement", "responsible_node", "required_artifact", "acceptance_criteria", "return_to", "priority")
                  if not str(item.get(field, "")).strip()]
        if absent:
            failures.append(f"H8: evidence_gap_matrix 缺字段 {','.join(absent)}")
            continue
        if item["responsible_node"] not in valid_responsible:
            failures.append(f"H8: evidence_gap_matrix responsible_node 必须为 H5/H6/H7（当前: {item['responsible_node']}）")
        pair = (item["subproblem_id"], item["requirement"])
        if pair in seen_pairs:
            failures.append(f"H8: evidence_gap_matrix 重复缺口: {pair[0]}/{pair[1]}")
        else:
            seen_pairs.add(pair)
        entry = (item["subproblem_id"], item["requirement"], item["responsible_node"])
        if item["return_to"] != item["responsible_node"]:
            failures.append("H8: evidence_gap_matrix return_to 必须与责任节点一致")
        actual.add(entry)
    if actual != expected:
        failures.append("H8: evidence_gap_matrix 未覆盖全部已检测缺口")


def _validate_h8_writing_plan(root: Path, node: dict[str, Any],
                               missing: list[str], failures: list[str]) -> None:
    """Validate H8 writing plan structure and approval status.

    Called only when writing_started=true.  Checks the plan file exists,
    has status=approved, contains non-empty sections, and the declared
    sha256 matches the actual file.
    """
    plan_raw = node.get("writing_plan")
    if not isinstance(plan_raw, str) or not plan_raw.strip():
        failures.append("H8: 开始写作前必须登记 writing_plan（写作计划文件路径）")
        return
    plan_path = resolve_project_path(root, plan_raw)
    if plan_path is None or not plan_path.is_file():
        failures.append(f"H8: writing_plan 文件不存在: {plan_raw}")
        return
    if plan_path.stat().st_size == 0:
        failures.append("H8: writing_plan 为空")
        return
    plan_sha = node.get("writing_plan_sha256")
    if not isinstance(plan_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", plan_sha):
        failures.append("H8: writing_plan_sha256 必须为 64 位十六进制字符串")
    elif not same_digest(plan_sha, digest(plan_path)):
        failures.append("H8: writing_plan_sha256 与计划文件不匹配")
    try:
        plan = load_mapping(plan_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures.append(f"H8: writing_plan 不可读: {exc}")
        return
    if not isinstance(plan, dict):
        failures.append("H8: writing_plan 必须为对象")
        return
    if plan.get("status") != "approved":
        failures.append(f"H8: writing_plan.status 必须为 approved（当前: {plan.get('status')}）")
    sections = plan.get("sections")
    if not isinstance(sections, list) or not sections:
        failures.append("H8: writing_plan 必须包含非空 sections 列表")
    else:
        body_page_total = 0.0
        for idx, sec in enumerate(sections):
            if not isinstance(sec, dict):
                failures.append(f"H8: writing_plan.sections[{idx}] 必须为对象")
                continue
            sid = sec.get("section_id") or f"section_{idx}"
            if not sec.get("section_id"):
                failures.append(f"H8: writing_plan.sections[{idx}] 缺少 section_id")
            if not sec.get("subproblem_id"):
                failures.append(f"H8: writing_plan.sections[{idx}] 缺少 subproblem_id")
            # P1-04: 每章强制登记 page_count、material_refs、figure_locations、claim_ids
            page_count = sec.get("page_count")
            if page_count is None:
                failures.append(f"H8: writing_plan.sections[{sid}] 缺少 page_count（必须登记规划页数）")
            elif not isinstance(page_count, (int, float)) or isinstance(page_count, bool) or page_count <= 0:
                failures.append(f"H8: writing_plan.sections[{sid}] page_count 无效（必须为正数）: {page_count}")
            else:
                chapter_type = sec.get("chapter_type", "body")
                if chapter_type not in ("appendix", "references", "cover"):
                    body_page_total += page_count
            if not sec.get("material_refs"):
                failures.append(f"H8: writing_plan.sections[{sid}] 缺少 material_refs（必须登记该章使用的素材引用）")
            if not sec.get("figure_locations"):
                failures.append(f"H8: writing_plan.sections[{sid}] 缺少 figure_locations（必须登记该章图表落位）")
            if not sec.get("claim_ids"):
                failures.append(f"H8: writing_plan.sections[{sid}] 缺少 claim_ids（必须登记该章支持的论文主张）")
            if not isinstance(sec.get("argument_ids"), list) or not sec["argument_ids"]:
                failures.append(f"H8: writing_plan.sections[{sid}] 缺少 argument_ids（必须绑定论证蓝图）")
            if not isinstance(sec.get("reader_question"), str) or not sec["reader_question"].strip():
                failures.append(f"H8: writing_plan.sections[{sid}] 缺少 reader_question（本章要回答的读者问题）")
            if not isinstance(sec.get("chapter_answer"), str) or not sec["chapter_answer"].strip():
                failures.append(f"H8: writing_plan.sections[{sid}] 缺少 chapter_answer（本章给出的回答）")
        # P1-04: 正文页数容量审查（国赛 profile 硬上限 30 页）
        if body_page_total > 30:
            failures.append(f"H8: writing_plan 正文规划页数 {body_page_total} 超过硬上限 30 页")
        elif body_page_total < 20:
            failures.append(f"H8: writing_plan 正文规划页数 {body_page_total} 低于推荐下限 20 页（国赛正文目标 [25,30]）")
    abstract_plan = plan.get("abstract_plan")
    if abstract_plan is not None:
        if not isinstance(abstract_plan, dict):
            failures.append("H8: writing_plan.abstract_plan 必须为对象")
        elif not abstract_plan.get("claim_ids"):
            failures.append("H8: writing_plan.abstract_plan 必须包含 claim_ids")


def _validate_paper_materials(root: Path, nodes: dict[str, Any], problem_scope: dict[str, Any],
                              missing: list[str], failures: list[str]) -> tuple[bool, Path | None, dict[tuple[str, str], tuple[str, str]], dict[str, Any] | None]:
    h8 = nodes.get("H8", {})
    readiness_path, readiness = _load_project_mapping(root, h8.get("paper_material_readiness"),
                                                       "H8: paper_material_readiness", missing, failures)
    if readiness_path is None or readiness is None:
        return False, None, {}, None
    required = ("status", "prepared_by", "verified_by", "verification_agent_instance_id", "target_length", "subproblems", "claim_requirements")
    absent = [field for field in required if field not in readiness]
    if absent:
        failures.append(f"paper_material_readiness 缺字段 {','.join(absent)}")
        return False, readiness_path, {}, readiness
    if readiness.get("status") not in {"PASS", "PAUSE"}:
        failures.append("paper_material_readiness status 必须为 PASS 或 PAUSE")
        return False, readiness_path, {}, readiness
    if readiness.get("verified_by") != "H6" or readiness.get("verification_agent_instance_id") != nodes.get("H6", {}).get("agent_instance_id"):
        failures.append("paper_material_readiness 必须由当前 H6 实例核验")
    target_length = readiness.get("target_length")
    wpr = None
    if isinstance(target_length, dict):
        wpr = target_length.get("whole_pdf_recommended_range")
    if wpr is None:
        wpr = readiness.get("whole_pdf_recommended_range")
    if wpr is not None:
        if not isinstance(wpr, list) or len(wpr) != 2 or not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in wpr):
            failures.append("paper_material_readiness: whole_pdf_recommended_range 必须为 [min, max] 数值列表")
        elif wpr[0] != 35 or wpr[1] != 51:
            failures.append(f"paper_material_readiness: whole_pdf_recommended_range 必须为 [35, 51]（当前: {wpr}）")
    expected_ids = set()
    scope_subs = problem_scope.get("subproblems") if isinstance(problem_scope, dict) else None
    if isinstance(scope_subs, list):
        for item in scope_subs:
            if isinstance(item, str) and item.strip():
                expected_ids.add(item.strip())
            elif isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip():
                expected_ids.add(item["id"].strip())
    actual_ids = []
    for item in readiness.get("subproblems", []) or []:
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip():
            actual_ids.append(item["id"].strip())
    actual_set = set(actual_ids)
    if len(actual_ids) != len(actual_set):
        failures.append("paper_material_readiness: subproblems 存在重复 id")
    if expected_ids:
        missing_ids = expected_ids - actual_set
        unknown_ids = actual_set - expected_ids
        if missing_ids:
            failures.append(f"paper_material_readiness: 缺少题目范围声明的小问 {','.join(sorted(missing_ids))}")
        if unknown_ids:
            failures.append(f"paper_material_readiness: 存在题目范围未声明的小问 {','.join(sorted(unknown_ids))}")
    gaps, material_refs = _collect_material_gaps(root, readiness, failures)
    _validate_evidence_matrix(readiness, gaps, failures)
    admitted = readiness.get("status") == "PASS" and not gaps
    if not admitted:
        missing.append("H8: paper_material_readiness=PAUSE")
        _validate_gap_matrix(root, h8, readiness_path, gaps, missing, failures)
    if h8.get("writing_started") is True and not admitted:
        failures.append("H8: 素材未通过准入即开始写论文")
    if h8.get("writing_started") is True and admitted:
        plan_raw = h8.get("writing_plan")
        if not isinstance(plan_raw, str) or not plan_raw.strip():
            failures.append("H8: 开始写作前必须登记 writing_plan（写作计划文件路径）")
        else:
            plan_path = resolve_project_path(root, plan_raw)
            if plan_path is None or not plan_path.is_file():
                failures.append(f"H8: writing_plan 文件不存在: {plan_raw}")
            elif plan_path.stat().st_size == 0:
                failures.append("H8: writing_plan 为空")
            else:
                plan_sha = h8.get("writing_plan_sha256")
                if not isinstance(plan_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", plan_sha):
                    failures.append("H8: writing_plan_sha256 必须为 64 位十六进制字符串")
                elif not same_digest(plan_sha, digest(plan_path)):
                    failures.append("H8: writing_plan_sha256 与计划文件不匹配")
        plan_packet = h8.get("plan_review_packet")
        if not isinstance(plan_packet, str) or not plan_packet.strip():
            failures.append("H8: 开始写作前必须登记 plan_review_packet（计划审查包路径）")
        else:
            packet_path = resolve_project_path(root, plan_packet)
            if packet_path is None or not packet_path.is_file():
                failures.append(f"H8: plan_review_packet 文件不存在: {plan_packet}")
        if h8.get("plan_approved") is not True:
            failures.append("H8: 开始写作前写作计划必须经用户批准（plan_approved=true）")
    return admitted, readiness_path, material_refs, readiness


def _validate_claim_coverage(root: Path, node: dict[str, Any], readiness_path: Path,
                             material_refs: dict[tuple[str, str], tuple[str, str]], readiness: dict[str, Any],
                             missing: list[str], failures: list[str]) -> None:
    coverage_path, coverage = _load_project_mapping(root, node.get("paper_claim_coverage"),
                                                     "H8: paper_claim_coverage", missing, failures)
    if coverage_path is None or coverage is None:
        return
    if coverage.get("status") != "PASS":
        missing.append("H8: paper_claim_coverage 未通过")
        return
    if not same_digest(coverage.get("readiness_sha256"), digest(readiness_path)):
        missing.append("H8: paper_claim_coverage 对应的素材包已失效")
        return
    # P1-05: 论文源文件路径及 SHA-256 登记
    paper_source_raw = node.get("paper_source") or coverage.get("paper_source")
    paper_source_path = None
    paper_text = None
    if isinstance(paper_source_raw, str) and paper_source_raw.strip():
        paper_source_path = resolve_project_path(root, paper_source_raw)
        if paper_source_path is None or not paper_source_path.is_file():
            failures.append(f"H8: paper_source 文件不存在: {paper_source_raw}")
        else:
            paper_source_sha = node.get("paper_source_sha256") or coverage.get("paper_source_sha256")
            if isinstance(paper_source_sha, str) and paper_source_sha.strip():
                if not re.fullmatch(r"[0-9a-fA-F]{64}", paper_source_sha):
                    failures.append("H8: paper_source_sha256 必须为 64 位十六进制字符串")
                elif digest(paper_source_path).lower() != paper_source_sha.lower():
                    failures.append(f"H8: paper_source_sha256 与论文源文件不匹配")
            try:
                paper_text = paper_source_path.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                failures.append(f"H8: paper_source 不可读: {exc}")
    else:
        failures.append("H8: 必须登记 paper_source（论文源文件路径），用于核对 paper_anchor 实际存在性")
    requirements = readiness.get("claim_requirements")
    claims = coverage.get("claims")
    if not isinstance(requirements, list) or not isinstance(claims, list):
        failures.append("H8: claim_requirements 与 claims 必须为列表")
        return
    expected = {item.get("id"): item.get("type") for item in requirements if isinstance(item, dict)}
    seen_claim_ids: set[str] = set()
    duplicate_claim_ids: set[str] = set()
    for item in claims:
        if isinstance(item, dict):
            cid = item.get("id")
            if isinstance(cid, str) and cid.strip():
                if cid in seen_claim_ids:
                    duplicate_claim_ids.add(cid)
                else:
                    seen_claim_ids.add(cid)
    if duplicate_claim_ids:
        failures.append(f"H8: 论文主张覆盖表存在重复 claim_id: {','.join(sorted(duplicate_claim_ids))}")
        return
    actual = {item.get("id"): item for item in claims if isinstance(item, dict)}
    if not expected or set(actual) != set(expected):
        failures.append("H8: 论文主张覆盖表必须覆盖且只能覆盖准入主张")
        return
    fields_by_reference: dict[tuple[str, str], set[str]] = {}
    for (_, field), reference in material_refs.items():
        fields_by_reference.setdefault(reference, set()).add(field)
    for claim_id, expected_type in expected.items():
        claim = actual[claim_id]
        if claim.get("type") != expected_type or not isinstance(claim.get("paper_anchor"), str) or not claim["paper_anchor"].strip():
            failures.append(f"H8: 主张 {claim_id} 类型或正文锚点无效")
            continue
        # P1-05: 确认 paper_anchor 在论文源文件中实际存在
        if paper_text is not None:
            anchor = claim["paper_anchor"].strip()
            if anchor not in paper_text:
                failures.append(f"H8: 主张 {claim_id} 的 paper_anchor（{anchor}）未在论文源文件中出现")
        evidence_refs = claim.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            failures.append(f"H8: 主张 {claim_id} 缺少证据映射")
            continue
        fields: set[str] = set()
        for reference in evidence_refs:
            fresh, ref = _reference_is_fresh(root, reference)
            if not fresh or ref not in fields_by_reference:
                failures.append(f"H8: 主张 {claim_id} 使用未冻结或过期证据")
                continue
            fields.update(fields_by_reference[ref])
        if expected_type not in CLAIM_EVIDENCE:
            failures.append(f"H8: 主张 {claim_id} 使用未知主张类型 {expected_type}，允许类型: {', '.join(sorted(CLAIM_EVIDENCE.keys()))}")
        elif not CLAIM_EVIDENCE[expected_type].issubset(fields):
            failures.append(f"H8: 主张 {claim_id} 的证据类型不完整")


def _validate_writer_preparation(root: Path, control: dict[str, Any], log: dict[str, Any],
                                  missing: list[str], failures: list[str], admission_only: bool = False) -> None:
    if control.get("visual_workflow") == "chapter_parallel":
        from harness_chapter_workflow import validate
        validate(root, control, log, missing, failures, admission_only=admission_only)
        return
    h7 = control.get("nodes", {}).get("H7", {})
    prep = h7.get("writer_preparation")
    if not isinstance(prep, dict):
        missing.append("H7: writer_preparation required before formal figures")
        return

    def reference(value: Any, label: str) -> Path | None:
        path = resolve_project_path(root, value.get("path")) if isinstance(value, dict) else None
        if path is None or not path.is_file():
            missing.append(f"{label}: missing project artifact")
            return None
        if not same_digest(value.get("sha256"), digest(path)):
            failures.append(f"{label}: stale artifact hash")
        return path

    h6_approval = _approval_for(log, "H6") or {}
    h6_time = _parse_timestamp(h6_approval.get("timestamp"))
    if h6_approval.get("decision") != "approved" or h6_time is None:
        missing.append("writer preparation requires actual H6 user approval")
    plan = reference(prep.get("writing_plan"), "writer_preparation.writing_plan")
    if plan:
        _validate_review(root, "H7", prep, log, missing, failures,
                         packet_key="plan_review_packet", approval_gate="H7_WRITING_PLAN",
                         packet_node_id="H7_WRITING_PLAN", min_artifact_count=1,
                         required_artifact_paths=(plan,))
    writing_approval = _approval_for(log, "H7_WRITING_PLAN") or {}
    writing_time = _parse_timestamp(writing_approval.get("timestamp"))
    records = control.get("dispatch_records", [])
    preparation_records = [r for r in records if isinstance(r, dict) and r.get("dispatch_kind") == "writer_preparation"]
    if admission_only and not preparation_records and prep.get("draft") is None:
        return
    matching = [r for r in preparation_records if r.get("task_id") == prep.get("task_id")]
    if len(preparation_records) != 1 or len(matching) != 1:
        failures.append("H7: one explicit accepted writer-preparation dispatch required")
        return
    record = matching[0]
    h8 = control.get("nodes", {}).get("H8", {})
    if h8.get("task_card") == record.get("task_card_path"):
        failures.append("H8: formal integration requires a separate task card/dispatch; preparation cannot complete H8")
    writer_id = control.get("agent_instances", {}).get("H8", {}).get("agent_instance_id")
    route = control.get("agent_runtime_routes", {}).get("H8", {})
    if (not writer_id or record.get("node_id") != "H8" or record.get("owner_role") != "论文 agent"
            or record.get("agent_instance_id") != writer_id
            or any(record.get(key) != route.get(key) for key in ("model", "reasoning_effort"))):
        failures.append("H7: preparation must use the registered H8 writer and actual H8 runtime route")
    card_path = reference({"path": record.get("task_card_path"), "sha256": record.get("task_card_sha256")},
                          "writer_preparation.task_card")
    if card_path:
        card = load_mapping(card_path)
        if card.get("scope", {}).get("phase") != "H8_draft_preparation":
            failures.append("H7: preparation task must declare H8_draft_preparation")
        if any(card.get(key) != record.get(key) for key in ("task_id", "node_id", "owner_role", "model", "reasoning_effort")):
            failures.append("H7: preparation card identity/runtime mismatch")
        inputs = card.get("inputs")
        if not isinstance(inputs, list) or len(inputs) < 2:
            failures.append("H7: preparation needs the approved writing plan and frozen scientific inputs")
        else:
            for item in inputs:
                reference(item, "writer_preparation.input")
            if prep.get("writing_plan") not in inputs:
                failures.append("H7: preparation input must bind the approved writing plan")
    receipt = record.get("spawn_receipt")
    if not isinstance(receipt, dict) or any(receipt.get(key) != record.get(key) for key in
                                           ("task_id", "agent_instance_id", "task_card_sha256")):
        failures.append("H7: actual writer preparation receipt required")
    called = _parse_timestamp(record.get("dispatched_at"))
    completed = _parse_timestamp(prep.get("draft_completed_at"))
    if called is None or h6_time is None or writing_time is None or called <= max(h6_time, writing_time):
        failures.append("H7: writer draft dispatched before H6/writing-plan approval")
    if completed is None or called is None or completed <= called:
        failures.append("H7: draft completion must follow actual writer dispatch")
    draft = reference(prep.get("draft"), "writer_preparation.draft")
    visual_path = resolve_project_path(root, h7.get("visual_argument_plan"))
    if visual_path is None or not visual_path.is_file():
        missing.append("H7: writer-derived visual_argument_plan required")
    else:
        visual = load_mapping(visual_path)
        prepared = _parse_timestamp(visual.get("prepared_at"))
        if (visual.get("prepared_by_role") != "论文 agent" or visual.get("draft") != prep.get("draft")
                or prepared is None or completed is None or prepared < completed):
            failures.append("H7: visual requirements must be authored by writer after and bound to the draft")
        if draft:
            approved = _approval_for(log, "H7_VISUAL_PLAN") or {}
            if not same_digest(approved.get("artifact_digests", {}).get(as_relative(root, draft)), digest(draft)):
                missing.append("H7_VISUAL_PLAN: human approval must bind the writer draft as well as visual plan")
            approved_at = _parse_timestamp(approved.get("timestamp"))
            if approved_at is None:
                missing.append("H7_VISUAL_PLAN: actual human approval timestamp required")
            elif prepared is not None and approved_at < prepared:
                failures.append("H7_VISUAL_PLAN: approval cannot predate writer visual requirements")
    for r in records:
        if isinstance(r, dict) and r.get("node_id") == "H7":
            at = _parse_timestamp(r.get("dispatched_at"))
            if completed is not None and (at is None or at <= completed):
                failures.append("H7: figure work cannot precede completed writer draft")
    registry_path = resolve_project_path(root, h7.get("figure_registry"))
    if not admission_only and registry_path is not None and registry_path.is_file():
        registry = load_mapping(registry_path)
        selected_paths = [registry_path]
        figures = registry.get("figures", registry.get("items", []))
        if not isinstance(figures, list):
            failures.append("H7: selected figure registry must contain a list")
            figures = []
        for figure in figures:
            if not isinstance(figure, dict):
                continue
            for extension in ("svg", "png"):
                raw = figure.get(extension)
                if raw is None and isinstance(figure.get("outputs"), dict):
                    raw = figure["outputs"].get(extension)
                path = resolve_project_path(root, raw.get("path") if isinstance(raw, dict) else raw)
                if path is None or not path.is_file():
                    missing.append(f"H7: selected {extension} asset missing")
                else:
                    selected_paths.append(path)
        _validate_review(root, "H7", h7, log, missing, failures,
                         packet_key="figure_selection_review_packet", approval_gate="H7_FIGURE_SELECTION",
                         packet_node_id="H7_FIGURE_SELECTION", min_artifact_count=1,
                         required_artifact_paths=tuple(selected_paths))
        selection = _approval_for(log, "H7_FIGURE_SELECTION") or {}
        selected_at = _parse_timestamp(selection.get("timestamp"))
        generation_times = [_parse_timestamp(r.get("dispatched_at")) for r in records
                            if isinstance(r, dict) and r.get("node_id") == "H7"]
        if selected_at is None or not generation_times or any(at is None or at >= selected_at for at in generation_times):
            failures.append("H7: human figure selection must follow figure generation")
        node_approval = _approval_for(log, "H7") or {}
        node_at = _parse_timestamp(node_approval.get("timestamp"))
        if h7.get("status") in {"approved", "frozen"} and (node_at is None or selected_at is None or node_at < selected_at):
            failures.append("H7: final node approval cannot precede selected figure versions")


def check_harness_control(root: Path, through: str = "H9", preflight_draft: bool = False) -> dict[str, Any]:
    if preflight_draft:
        report = check_harness_control(root, through="H6")
        control = load_mapping(root / ".contest/harness_control.yaml")
        log = load_mapping(root / ".contest/approval_log.yaml")
        if control.get("visual_workflow") not in {"writer_first_draft", "chapter_parallel"}:
            report["failures"].append("draft admission requires an explicit writer-led workflow")
        else:
            _validate_writer_preparation(root.resolve(), control, log, report["missing"], report["failures"], admission_only=True)
        report["status"] = "BLOCK" if report["failures"] else "PAUSE" if report["missing"] or report["evidence_gaps"] else "PASS"
        report["through"] = "H7-draft"
        return report
    root = root.resolve()
    failures: list[str] = []
    missing: list[str] = []
    evidence_gaps: list[str] = []
    return_nodes: list[str] = []
    if through not in NODES:
        return {"status": "BLOCK", "failures": [f"未知节点: {through}"], "missing": [], "evidence_gaps": [], "return_nodes": []}
    control_path = root / ".contest" / "harness_control.yaml"
    if not control_path.is_file():
        return {"status": "BLOCK", "failures": ["缺少 .contest/harness_control.yaml"], "missing": [], "evidence_gaps": [], "return_nodes": []}
    try:
        control = load_mapping(control_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return {"status": "BLOCK", "failures": [str(exc)], "missing": [], "evidence_gaps": [], "return_nodes": []}
    validation_plan = None
    validation_errors, validation_plan = validate_control_validation(root, control)
    failures.extend(validation_errors)
    if control.get("active_mode") != "full-contest-harness":
        failures.append("active_mode 必须为 full-contest-harness")
    if control.get("visual_workflow") not in (None, "writer_first_draft", "chapter_parallel"):
        failures.append("visual_workflow must select a supported writer-led workflow or be omitted for legacy runs")
    if "reader_evidence_protocol" in control and control.get("reader_evidence_protocol") != READER_EVIDENCE_VERSION:
        failures.append(f"reader_evidence_protocol 必须为 {READER_EVIDENCE_VERSION}")
    roles = control.get("roles", {})
    if not isinstance(roles, dict):
        failures.append("roles 必须为对象")
        roles = {}
    for role in set(ROLE_BY_NODE.values()):
        if role not in roles:
            failures.append(f"缺少固定角色: {role}")
    runtime_routes = control.get("agent_runtime_routes", {})
    if not isinstance(runtime_routes, dict):
        failures.append("agent_runtime_routes 必须为对象")
        runtime_routes = {}
    for node_id, expected_runtime in AGENT_RUNTIME_BY_NODE.items():
        if runtime_routes.get(node_id) != expected_runtime:
            failures.append(f"{node_id}: agent_runtime_routes 不符合节点配置")
    bootstrap = control.get("bootstrap", {})
    invocations = bootstrap.get("invocations", []) if isinstance(bootstrap, dict) else []
    invoked = isinstance(invocations, list) and any(
        isinstance(item, dict) and item.get("skill") == "superpowers:using-superpowers"
        and item.get("completed") is True and item.get("status") == "completed"
        and str(item.get("task_id", "")).strip()
        for item in invocations
    )
    if bootstrap.get("required_skill") != "superpowers:using-superpowers" or not invoked:
        missing.append("H0: 缺少 superpowers:using-superpowers 实际调用记录")
    agent_ids_by_role = _validate_spawn_invocations(control, through, missing, failures)
    nodes = control.get("nodes", {})
    if not isinstance(nodes, dict):
        failures.append("nodes 必须为对象")
        nodes = {}
    log_path = root / ".contest" / "approval_log.yaml"
    try:
        log = load_mapping(log_path) if log_path.is_file() else {"approvals": []}
    except (OSError, ValueError, yaml.YAMLError) as exc:
        failures.append(f"approval_log 不可读: {exc}")
        log = {"approvals": []}
    task_ids: set[str] = set()
    checked_nodes = NODES[:NODES.index(through) + 1]
    if control.get("visual_workflow") in {"writer_first_draft", "chapter_parallel"} and "H7" in checked_nodes:
        _validate_writer_preparation(root, control, log, missing, failures)
    for node_id in checked_nodes:
        node = nodes.get(node_id)
        if not isinstance(node, dict):
            failures.append(f"{node_id}: 节点记录缺失")
            continue
        # H4 节点已取消（v4.19 起并入 H5 阶段一），跳过其独立检查
        if node_id == "H4":
            continue
        node_status = node.get("status")
        if node_status not in NODE_STATUSES:
            failures.append(f"{node_id}: status 必须为 {','.join(sorted(NODE_STATUSES))}，当前: {node_status}")
        elif node_id != through and node_id in AGENT_NODES and node_status == "not_started":
            failures.append(f"{node_id}: --through={through} 时前置 agent 节点不能为 not_started（必须至少已启动为 draft）")
        if node.get("owner_role") != ROLE_BY_NODE[node_id]:
            failures.append(f"{node_id}: owner_role 不符合固定职责")
        expected_policy = "required" if node_id in AGENT_NODES else "controller_only"
        if node.get("agent_policy") != expected_policy:
            failures.append(f"{node_id}: agent_policy 必须为 {expected_policy}")
        if node.get("support_agent_policy") not in ("none", "conditional"):
            failures.append(f"{node_id}: support_agent_policy 只能为 none 或 conditional")
        if node_id in AGENT_NODES:
            _validate_task_card(root, node_id, node, runtime_routes.get(node_id, {}), task_ids, missing, failures)
        if node_id in SKILL_BINDING_BY_NODE:
            _validate_skill_invocations(root, node_id, node, missing, failures)
        if node_id == "H1":
            _validate_h1_problem_statement(root, node, missing, failures)
        if node_id in REVIEW_NODES:
            # H7 has two user-controlled phases.  During the plan-only draft
            # phase, H7_VISUAL_PLAN is the approval gate; the ordinary H7
            # review packet belongs to the generated-figure final review.
            h7_plan_only = (
                node_id == "H7"
                and node_status == "draft"
                and not str(node.get("figure_registry") or "").strip()
            )
            if not h7_plan_only:
                _validate_review(root, node_id, node, log, missing, failures)
        if node_id == "H7":
            _validate_h7_visual_argument_plan(root, node, control, log, missing, failures)
            h7_plan_only = (
                node_status == "draft"
                and not str(node.get("figure_registry") or "").strip()
            )
            if not h7_plan_only:
                _validate_h7_figures(root, node, missing, failures)
        if node_id == "H9":
            _validate_h9_delivery(root, node, missing, failures)
        if node_id == "H8" and node.get("outcome") == "evidence_gap":
            evidence_gaps.append("H8")
            destination = node.get("return_to")
            if destination not in {"H5", "H6", "H7"}:
                failures.append("H8: evidence_gap 必须回到 H5/H6/H7")
            else:
                return_nodes.append(destination)
    _validate_status_history(root, control, through, missing, failures)
    validate_dispatch_order(root, control, through, missing, failures)
    validate_literature_gate(root, nodes, through, missing, failures)
    _validate_dispatch_records(root, control, nodes, runtime_routes, through, missing, failures)
    if "H5" in checked_nodes:
        _validate_h5_result_traceability_registration(root, nodes.get("H5", {}), missing, failures)
    if "H7" in checked_nodes:
        _validate_h7_generation_binding(root, control, nodes.get("H7", {}), log, missing, failures)
    _validate_agent_instances(root, control, through, agent_ids_by_role, missing, failures)
    _validate_narrative(root, nodes, through, missing, failures)
    _validate_validation_contract(root, nodes, through, missing, failures)
    _validate_result_interpretation_cards(root, nodes, through, missing, failures, control=control)
    paper_material_status = None
    if "H6" in checked_nodes:
        _validate_h6_interface(root, nodes, control.get("problem_scope", {}), missing, failures)
        _validate_model_summary_cards(
            root, nodes, control.get("problem_scope", {}), missing, failures,
            through=through, control=control,
        )
    if NODES.index(through) >= NODES.index("H5"):
        _validate_visual_evidence_packet(
            root, nodes, control.get("problem_scope", {}), through, missing, failures,
        )
    if "H8" in checked_nodes:
        admitted, readiness_path, material_refs, readiness = _validate_paper_materials(root, nodes, control.get("problem_scope", {}), missing, failures)
        paper_material_status = "PASS" if admitted else "PAUSE"
        if admitted and readiness_path is not None and readiness is not None:
            _validate_claim_coverage(root, nodes["H8"], readiness_path, material_refs, readiness, missing, failures)
        h8_node = nodes.get("H8", {})
        if isinstance(h8_node, dict):
            _validate_abstract_argument_card(
                root, h8_node, control.get("problem_scope", {}), missing, failures,
            )
            _validate_argument_blueprint(root, nodes, missing, failures)
        if isinstance(h8_node, dict) and h8_node.get("writing_started") is True:
            _validate_paper_author_brief(root, h8_node, missing, failures, control=control)
            _validate_chapter_writing_cards(root, h8_node, missing, failures, control=control)
            _validate_paper_continuity_context(root, h8_node, missing, failures)
            _validate_h8_writing_plan(root, h8_node, missing, failures)
    status = "BLOCK" if failures else "PAUSE" if missing or evidence_gaps else "PASS"
    return {
        "schema_version": "1.0", "status": status, "through": through,
        "failures": failures, "missing": missing,
        "evidence_gaps": evidence_gaps, "return_nodes": return_nodes,
        "paper_material_status": paper_material_status,
        "validation_plan": validation_plan,
        "control_path": str(control_path), "approval_log": str(log_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--through", choices=NODES, default="H9")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--preflight-draft", action="store_true", help="Check H6 and writer-plan admission without finished figures")
    args = parser.parse_args()
    try:
        report = check_harness_control(args.project_root, through=args.through, preflight_draft=args.preflight_draft)
    except Exception as exc:
        report = {
            "schema_version": "1.0", "status": "BLOCK", "through": args.through,
            "failures": [f"检查器内部异常（非法结构）: {type(exc).__name__}: {exc}"],
            "missing": [], "evidence_gaps": [], "return_nodes": [],
            "paper_material_status": None, "control_path": str(args.project_root / ".contest" / "harness_control.yaml"),
            "approval_log": str(args.project_root / ".contest" / "approval_log.yaml"),
        }
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.out.resolve().write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "PASS" else 2 if report["status"] == "PAUSE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
