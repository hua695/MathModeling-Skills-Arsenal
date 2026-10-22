#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the compact reader-evidence fields used by the paper workflow.

The validator is intentionally small and structural.  It does not judge
mathematical truth or rewrite prose; it only prevents a declared reader-first
artifact from omitting the bridges that a paper author needs.
"""
from __future__ import annotations

from typing import Any


READER_EVIDENCE_VERSION = "1.0"
VALID_DATA_SCOPE_MODES = {"shared", "independent", "hybrid"}
VALID_REPRESENTATIONS = {"figure", "table", "text"}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _refs(value: Any) -> bool:
    return _string_list(value) and bool(value)


def _required_text(mapping: Any, fields: tuple[str, ...], label: str, errors: list[str]) -> None:
    if not isinstance(mapping, dict):
        errors.append(f"{label} 必须为对象")
        return
    for field in fields:
        if not _text(mapping.get(field)):
            errors.append(f"{label} 缺少 {field}")


def validate_model_card(card: dict[str, Any], label: str = "model_summary_cards.card") -> list[str]:
    """Validate the reader-facing bridge attached to one model summary card."""
    errors: list[str] = []
    evidence = card.get("reader_evidence") if isinstance(card, dict) else None
    if not isinstance(evidence, dict):
        return [f"{label}: 缺少 reader_evidence"]
    _required_text(evidence, ("problem_need", "model_choice_reason", "final_model_reading"), label, errors)

    scope = evidence.get("data_scope")
    if not isinstance(scope, dict):
        errors.append(f"{label}.data_scope 必须为对象")
    else:
        mode = _text(scope.get("mode")).lower()
        if mode not in VALID_DATA_SCOPE_MODES:
            errors.append(f"{label}.data_scope.mode 必须为 shared/independent/hybrid")
        for field in ("shared_inputs", "question_specific_inputs"):
            if not _string_list(scope.get(field)):
                errors.append(f"{label}.data_scope.{field} 必须为字符串列表")
        if mode == "shared" and not scope.get("shared_inputs"):
            errors.append(f"{label}.data_scope.shared_inputs 在 shared 模式下不得为空")
        if mode == "independent" and not scope.get("question_specific_inputs"):
            errors.append(f"{label}.data_scope.question_specific_inputs 在 independent 模式下不得为空")
        if mode == "hybrid" and (not scope.get("shared_inputs") or not scope.get("question_specific_inputs")):
            errors.append(f"{label}.data_scope.hybrid 必须同时登记 shared_inputs 和 question_specific_inputs")
        if not _text(scope.get("placement_rationale")):
            errors.append(f"{label}.data_scope 缺少 placement_rationale")

    assumptions = evidence.get("assumption_traceability")
    if not _nonempty_list(assumptions):
        errors.append(f"{label}.assumption_traceability 必须为非空列表")
    else:
        for index, item in enumerate(assumptions):
            item_label = f"{label}.assumption_traceability[{index}]"
            _required_text(
                item,
                ("assumption_id", "statement", "basis", "model_role", "impact_if_violated"),
                item_label,
                errors,
            )
            if isinstance(item, dict) and not _refs(item.get("validation_refs")):
                errors.append(f"{item_label}.validation_refs 必须为非空字符串列表")

    derivation = evidence.get("derivation_arc")
    if not _nonempty_list(derivation):
        errors.append(f"{label}.derivation_arc 必须为非空列表")
    else:
        for index, item in enumerate(derivation):
            item_label = f"{label}.derivation_arc[{index}]"
            _required_text(item, ("from", "to", "reason"), item_label, errors)

    evaluation = evidence.get("evaluation")
    if not isinstance(evaluation, dict):
        errors.append(f"{label}.evaluation 必须为对象")
    else:
        strengths = evaluation.get("strengths")
        limitations = evaluation.get("limitations")
        improvements = evaluation.get("improvements")
        for field in ("strengths", "limitations", "improvements"):
            if not _nonempty_list(evaluation.get(field)):
                errors.append(f"{label}.evaluation.{field} 必须为非空列表")
        if isinstance(strengths, list):
            for index, item in enumerate(strengths):
                item_label = f"{label}.evaluation.strengths[{index}]"
                _required_text(item, ("claim",), item_label, errors)
                if isinstance(item, dict) and not _refs(item.get("evidence_refs")):
                    errors.append(f"{item_label}.evidence_refs 必须为非空字符串列表")
        if isinstance(limitations, list):
            for index, item in enumerate(limitations):
                item_label = f"{label}.evaluation.limitations[{index}]"
                _required_text(item, ("source", "impact", "scope"), item_label, errors)
                if isinstance(item, dict) and not _refs(item.get("evidence_refs")):
                    errors.append(f"{item_label}.evidence_refs 必须为非空字符串列表")
        if isinstance(improvements, list):
            for index, item in enumerate(improvements):
                item_label = f"{label}.evaluation.improvements[{index}]"
                _required_text(item, ("addresses", "change", "expected_effect"), item_label, errors)
    return errors


def validate_result_card(card: dict[str, Any], label: str = "result_interpretation_cards.card") -> list[str]:
    """Require the observation-to-decision bridge used in result analysis."""
    errors: list[str] = []
    analysis = card.get("reader_analysis") if isinstance(card, dict) else None
    _required_text(
        analysis,
        ("observed_pattern", "comparison_basis", "decision_implication", "boundary_or_exception"),
        label + ".reader_analysis",
        errors,
    )
    return errors


def validate_author_chapter(chapter: dict[str, Any], label: str = "paper_author_brief.chapter") -> list[str]:
    """Require an authoring arc without forcing a fixed paragraph template."""
    errors: list[str] = []
    arc = chapter.get("authoring_arc") if isinstance(chapter, dict) else None
    if not isinstance(arc, dict):
        return [f"{label}: 缺少 authoring_arc"]
    _required_text(arc, ("opening_tension", "interpretive_move", "transition_question"), label + ".authoring_arc", errors)
    if not _nonempty_list(arc.get("evidence_sequence")) or not all(
        isinstance(item, str) and item.strip() for item in arc.get("evidence_sequence", [])
    ):
        errors.append(f"{label}.authoring_arc.evidence_sequence 必须为非空字符串列表")
    return errors


def validate_visual_representation(slot: dict[str, Any], label: str = "visual_slot") -> list[str]:
    """Ensure the visual plan records why a figure/table/text representation earns space."""
    errors: list[str] = []
    representation = slot.get("representation") if isinstance(slot, dict) else None
    if not isinstance(representation, dict):
        return [f"{label}: 缺少 representation"]
    mode = _text(representation.get("mode")).lower()
    if mode not in VALID_REPRESENTATIONS:
        errors.append(f"{label}.representation.mode 必须为 figure/table/text")
    disposition = _text(slot.get("disposition")).lower()
    expected = {
        "required": "figure",
        "recommended": "figure",
        "table_justified": "table",
        "text_sufficient": "text",
        "not_applicable": "text",
    }.get(disposition)
    if expected and mode != expected:
        errors.append(f"{label}.representation.mode={mode} 与 disposition={disposition} 不一致，应为 {expected}")
    if not _text(representation.get("reason")):
        errors.append(f"{label}.representation 缺少 reason")
    if mode in {"figure", "table"}:
        _required_text(
            representation,
            ("pre_text_role", "post_text_role"),
            label + ".representation",
            errors,
        )
    return errors


def validate_protocol_version(payload: dict[str, Any], label: str) -> list[str]:
    """Validate an optional protocol marker without forcing legacy artifacts to migrate."""
    if not isinstance(payload, dict) or "reader_evidence_version" not in payload:
        return []
    if payload.get("reader_evidence_version") != READER_EVIDENCE_VERSION:
        return [f"{label}.reader_evidence_version 必须为 {READER_EVIDENCE_VERSION}"]
    return []

