#!/usr/bin/env python3
"""Check MathorCup node approvals, role dispatch, and frozen evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


NODES = ("M1", "M2", "M3", "M4", "M5")
ROUTES = {
    "data": ("gpt-6-luna", "max"),
    "solver": ("gpt-6.1-sol", "max"),
    "verifier": ("gpt-6.1-sol", "max"),
    "figure": ("gpt-6-luna", "max"),
    "writer": ("gpt-6.1-sol", "max"),
}
NODE_ROLES = {
    "M1": {"data"}, "M2": {"data", "verifier", "figure"},
    "M3": {"solver", "verifier", "figure", "support"},
    "M4": {"figure", "writer", "verifier"}, "M5": set(),
}
REQUIRED_ROLES = {
    "M1": {"data"}, "M2": {"data", "verifier"},
    "M3": {"solver", "verifier"},
    "M4": {"figure", "writer", "verifier"}, "M5": set(),
}
REQUIRED_SKILLS = {
    "M1": {"math-model-selector"},
    "M2": {"data-science-stack"},
    "M3": {"math-model-selector", "data-science-stack"},
    "M4": {"academic-writing", "mathmodel-latex-skill"},
    "M5": {"mathmodel-latex-skill"},
}
NODE_ARTIFACTS = {
    "M1": ("problem_statement", "data_overview", "task_kpi", "literature_request"),
    "M2": ("eda_report", "features", "leakage_audit", "literature_sources"),
    "M3": ("run_manifest", "model_summary_cards", "result_interpretation_cards", "independent_validation"),
    "M4": ("visual_argument_plan", "figure_registry", "paper_argument_blueprint", "paper_material_readiness", "paper_claim_coverage", "paper_pdf"),
    "M5": ("reproducibility_report", "delivery_report", "paper_pdf", "submission_package"),
}
MATERIAL_FIELDS = (
    "problem_mapping", "assumptions", "symbols", "data_processing", "model_choice",
    "method_and_parameters", "quantitative_results", "validation", "figures_or_tables",
    "literature_use", "conclusion_and_boundary",
)
DELIVERY_CHECKS = (
    "official_rules", "paper_format", "code_reproduction", "numeric_sources",
    "figures_and_citations", "anonymity", "ai_disclosure", "final_text",
)
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
SUPPORT_OUTPUTS = {"local_computation_evidence", "data_processing_evidence", "code_experiment_evidence"}
LEAKAGE_CHECKS = {"split_integrity", "train_only_preprocessing", "target_leakage"}
MODEL_CHECKS = {"cross_question_interface", "data_version", "units", "split_integrity", "numeric_provenance", "generalization"}


def _read(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"missing file: {path}")
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        value = yaml.safe_load(text) if yaml is not None else json.loads(text)
    except (OSError, ValueError, yaml.YAMLError if yaml is not None else ValueError) as exc:
        errors.append(f"invalid YAML/JSON: {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"mapping required: {path}")
        return {}
    return value


def _digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _artifact(root: Path, ref: Any, label: str, errors: list[str]) -> tuple[str, Path] | None:
    if not isinstance(ref, dict) or not isinstance(ref.get("path"), str):
        errors.append(f"{label}: path/sha256 reference required")
        return None
    relative = ref["path"]
    if not relative or Path(relative).is_absolute() or "\\" in relative:
        errors.append(f"{label}: project-relative POSIX path required")
        return None
    try:
        path = (root / relative).resolve()
        path.relative_to(root)
    except (OSError, ValueError):
        errors.append(f"{label}: path outside project: {relative}")
        return None
    if not path.is_file():
        errors.append(f"{label}: file missing: {relative}")
        return None
    if not isinstance(ref.get("sha256"), str) or not HEX64.fullmatch(ref["sha256"]):
        errors.append(f"{label}: sha256 required: {relative}")
        return None
    actual = _digest(path)
    if actual != ref["sha256"].lower():
        errors.append(f"{label}: hash mismatch: {relative}")
        return None
    return relative, path


def _time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def _named_pass_checks(root: Path, value: Any, required: set[str], label: str,
                       errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{label}: checks must be a nonempty list")
        return
    names: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or item.get("status") != "PASS":
            errors.append(f"{label}.checks[{index}]: named PASS check required")
            continue
        names.add(item["name"])
        _artifact(root, {"path": item.get("evidence_ref"),
                         "sha256": item.get("evidence_sha256")},
                  f"{label}.checks[{index}].evidence", errors)
    for name in sorted(required - names):
        errors.append(f"{label}: missing PASS check {name}")


def _approval(log: dict[str, Any], gate: str, refs: list[tuple[str, Path]],
              errors: list[str], pauses: list[str]) -> datetime | None:
    approvals = log.get("approvals")
    if not isinstance(approvals, list):
        errors.append("approval_log.approvals must be a list")
        return None
    matching = [entry for entry in approvals if isinstance(entry, dict) and entry.get("gate") == gate
                and entry.get("decision") == "approve" and entry.get("approved_by") == "user"]
    if not matching:
        pauses.append(f"{gate}: current user approval missing")
        return None
    entry = matching[-1]
    approved_at = _time(entry.get("approved_at"))
    if approved_at is None:
        errors.append(f"{gate}: approved_at must be timezone-aware ISO-8601")
    digests = entry.get("artifact_digests")
    if not isinstance(digests, dict):
        errors.append(f"{gate}: artifact_digests required")
        return approved_at
    for relative, path in refs:
        if digests.get(relative) != _digest(path):
            errors.append(f"{gate}: approval hash missing or stale: {relative}")
    return approved_at


def _check_instances(root: Path, control: dict[str, Any], errors: list[str]) -> dict[str, str]:
    routes = control.get("agent_runtime_routes")
    instances = control.get("agent_instances")
    if not isinstance(routes, dict) or not isinstance(instances, dict):
        errors.append("agent_runtime_routes and agent_instances must be mappings")
        return {}
    ids: dict[str, str] = {}
    for role, (model, effort) in ROUTES.items():
        if routes.get(role) != {"model": model, "reasoning_effort": effort}:
            errors.append(f"{role}: route must be {model}/{effort}")
        record = instances.get(role)
        if not isinstance(record, dict) or not isinstance(record.get("agent_instance_id"), str) or not record["agent_instance_id"]:
            errors.append(f"{role}: agent_instance_id required")
            continue
        if (record.get("model"), record.get("reasoning_effort")) != (model, effort):
            errors.append(f"{role}: instance route mismatch")
        ids[role] = record["agent_instance_id"]
        preloaded = record.get("preloaded")
        if not isinstance(preloaded, list) or not preloaded:
            errors.append(f"{role}: preloaded input list required")
            continue
        paths = []
        for index, item in enumerate(preloaded):
            found = _artifact(root, item, f"{role}.preloaded[{index}]", errors)
            if found:
                paths.append(found[0])
        if role != "data" and "problem_statement.md" not in paths:
            errors.append(f"{role}: problem_statement.md must be preloaded")
    if len(set(ids.values())) != len(ids):
        errors.append("fixed roles require distinct agent_instance_id values")
    if control.get("solver_instance_id") != ids.get("solver"):
        errors.append("solver_instance_id must equal the sole solver instance")
    if ids.get("verifier") == ids.get("solver") and ids.get("solver"):
        errors.append("verifier must use an independent instance")
    return ids


def _check_dispatch(root: Path, control: dict[str, Any], ids: dict[str, str],
                    log: dict[str, Any], approval_times: dict[str, datetime],
                    through_index: int, errors: list[str]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    records = control.get("dispatch_records")
    if not isinstance(records, list):
        errors.append("dispatch_records must be a list")
        return {}, {}
    dispatched: dict[str, set[str]] = {node: set() for node in NODES}
    m4_phases: dict[str, set[str]] = {"figure": set(), "writer": set()}
    task_ids: set[str] = set()
    for index, record in enumerate(records):
        label = f"dispatch_records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label}: mapping required")
            continue
        node, role, task_id = record.get("node_id"), record.get("owner_role"), record.get("task_id")
        if node in NODES and NODES.index(node) > through_index:
            continue
        if not isinstance(node, str) or node not in NODE_ROLES or not isinstance(role, str) or role not in NODE_ROLES[node]:
            errors.append(f"{label}: node/role not permitted")
            continue
        if not isinstance(task_id, str) or not task_id or task_id in task_ids:
            errors.append(f"{label}: unique task_id required")
        else:
            task_ids.add(task_id)
        dispatched[node].add(role)
        if role == "support":
            model, effort = "gpt-6-luna", "max"
            support_id = record.get("agent_instance_id")
            if not isinstance(support_id, str) or not support_id or support_id in ids.values():
                errors.append(f"{label}: support requires a distinct agent_instance_id")
            if record.get("dispatch_kind") != "conditional_support" or record.get("parent_solver_instance_id") != ids.get("solver"):
                errors.append(f"{label}: conditional support must bind the sole solver")
        else:
            model, effort = ROUTES[role]
            if record.get("agent_instance_id") != ids.get(role):
                errors.append(f"{label}: agent_instance_id mismatch")
        if (record.get("model"), record.get("reasoning_effort")) != (model, effort):
            errors.append(f"{label}: model/reasoning_effort mismatch")
        called_at = _time(record.get("called_at"))
        if called_at is None:
            errors.append(f"{label}: called_at must be timezone-aware ISO-8601")
        predecessor = NODES[NODES.index(node) - 1] if node != "M1" else None
        if predecessor and called_at is not None:
            approved_at = approval_times.get(predecessor)
            if approved_at is None or called_at < approved_at:
                errors.append(f"{label}: dispatch before {predecessor} approval")
        ref = {"path": record.get("task_card"), "sha256": record.get("task_card_sha256")}
        found = _artifact(root, ref, f"{label}.task_card", errors)
        if not found:
            continue
        card = _read(found[1], errors)
        for key, expected in (
            ("node_id", node), ("owner_role", role), ("task_id", task_id),
            ("agent_instance_id", record.get("agent_instance_id") if role == "support" else ids.get(role)),
            ("model", model), ("reasoning_effort", effort),
        ):
            if card.get(key) != expected:
                errors.append(f"{label}: task card {key} mismatch")
        if node == "M3" and role == "solver":
            scope = card.get("scope")
            questions = control.get("problem_scope", {}).get("subproblems", [])
            selected = scope.get("subproblems") if isinstance(scope, dict) else None
            if not isinstance(selected, list) or not all(isinstance(item, str) for item in selected) or set(selected) != set(questions) or scope.get("cross_question_interface") is not True:
                errors.append(f"{label}: sole solver task must cover all subproblems and cross-question interface")
        if role == "support":
            if card.get("dispatch_kind") != "conditional_support" or card.get("parent_solver_instance_id") != ids.get("solver"):
                errors.append(f"{label}: support task card must bind the sole solver")
            outputs = card.get("allowed_output_kinds")
            if not isinstance(outputs, list) or not outputs or not all(isinstance(item, str) for item in outputs) or not set(outputs).issubset(SUPPORT_OUTPUTS):
                errors.append(f"{label}: support output kinds must be local evidence only")
            authority = card.get("authority")
            if not isinstance(authority, dict) or any(authority.get(key) is not False for key in (
                "may_change_model_route", "may_write_final_results", "may_aggregate_conclusions"
            )):
                errors.append(f"{label}: support authority must forbid route/results/conclusions")
        if not isinstance(card.get("objective"), str) or not card["objective"].strip():
            errors.append(f"{label}: task card objective required")
        if not isinstance(card.get("prohibited_actions"), list) or not card["prohibited_actions"]:
            errors.append(f"{label}: task card prohibited_actions required")
        inputs = card.get("inputs")
        if not isinstance(inputs, list) or not inputs:
            errors.append(f"{label}: task card inputs required")
        else:
            for input_index, item in enumerate(inputs):
                _artifact(root, item, f"{label}.inputs[{input_index}]", errors)
        if node == "M4" and role in m4_phases:
            scope = card.get("scope")
            phase = scope.get("phase") if isinstance(scope, dict) else None
            allowed = {"plan", "generate"} if role == "figure" else {"plan", "write"}
            if phase not in allowed:
                errors.append(f"{label}: M4 {role} scope.phase must be one of {sorted(allowed)}")
                continue
            m4_phases[role].add(phase)
            if role == "writer" and phase == "write":
                if not isinstance(scope.get("chapter_id"), str) or not scope["chapter_id"]:
                    errors.append(f"{label}: writer write task requires chapter_id")
            gate = None
            required_inputs: list[str] = []
            m4 = control.get("nodes", {}).get("M4", {})
            def path_of(field: str) -> str | None:
                value = m4.get(field) if isinstance(m4, dict) else None
                return value.get("path") if isinstance(value, dict) else None
            if phase == "generate":
                gate = "M4_VISUAL_PLAN"
                required_inputs = [path_of("visual_argument_plan")]
            elif phase == "write":
                gate = "M4_WRITING_PLAN"
                required_inputs = [path_of(field) for field in (
                    "paper_argument_blueprint", "paper_material_readiness", "paper_claim_coverage")]
            if gate:
                approvals = log.get("approvals", [])
                matching = [entry for entry in approvals if isinstance(entry, dict) and
                            entry.get("gate") == gate and entry.get("decision") == "approve" and
                            entry.get("approved_by") == "user"] if isinstance(approvals, list) else []
                gate_time = _time(matching[-1].get("approved_at")) if matching else None
                if called_at is None or gate_time is None or called_at <= gate_time:
                    errors.append(f"{label}: {phase} dispatched before {gate} approval")
                input_paths = {item.get("path") for item in inputs if isinstance(item, dict)} if isinstance(inputs, list) else set()
                if not all(path is not None and path in input_paths for path in required_inputs):
                    errors.append(f"{label}: {phase} task card omits current approved inputs")
    return dispatched, m4_phases


def _check_chapter_sequence(root: Path, control: dict[str, Any], log: dict[str, Any],
                            errors: list[str]) -> None:
    m4 = control.get("nodes", {}).get("M4", {})
    if not isinstance(m4, dict) or not m4.get("writing_started"):
        return
    chapters = m4.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        return
    records = control.get("dispatch_records", [])
    approvals = log.get("approvals", [])
    if not isinstance(records, list) or not isinstance(approvals, list):
        return
    writes: dict[str, list[datetime]] = {}
    for record in records:
        if not isinstance(record, dict) or record.get("node_id") != "M4" or record.get("owner_role") != "writer":
            continue
        card_ref = record.get("task_card")
        if not isinstance(card_ref, str):
            continue
        card_path = (root / card_ref).resolve()
        if not card_path.is_relative_to(root) or not card_path.is_file():
            continue
        card = _read(card_path, errors)
        scope = card.get("scope")
        if not isinstance(scope, dict) or scope.get("phase") != "write":
            continue
        chapter_id = scope.get("chapter_id")
        called_at = _time(record.get("called_at"))
        if isinstance(chapter_id, str) and called_at is not None:
            writes.setdefault(chapter_id, []).append(called_at)
    previous_id: str | None = None
    for chapter in chapters:
        if not isinstance(chapter, dict) or not isinstance(chapter.get("chapter_id"), str):
            continue
        chapter_id = chapter["chapter_id"]
        times = writes.get(chapter_id, [])
        if len(times) != 1:
            errors.append(f"M4.{chapter_id}: exactly one writer dispatch required")
            previous_id = chapter_id
            continue
        if previous_id:
            gate = f"M4_CHAPTER:{previous_id}"
            previous = [entry for entry in approvals if isinstance(entry, dict) and
                        entry.get("gate") == gate and entry.get("decision") == "approve" and
                        entry.get("approved_by") == "user"]
            previous_time = _time(previous[-1].get("approved_at")) if previous else None
            if previous_time is None or times[0] <= previous_time:
                errors.append(f"M4.{chapter_id}: writer dispatched before {gate} approval")
        gate = f"M4_CHAPTER:{chapter_id}"
        own = [entry for entry in approvals if isinstance(entry, dict) and
               entry.get("gate") == gate and entry.get("decision") == "approve" and
               entry.get("approved_by") == "user"]
        own_time = _time(own[-1].get("approved_at")) if own else None
        if own_time is not None and own_time <= times[0]:
            errors.append(f"M4.{chapter_id}: chapter approval precedes writer dispatch")
        previous_id = chapter_id
    extra = set(writes) - {item.get("chapter_id") for item in chapters if isinstance(item, dict) and isinstance(item.get("chapter_id"), str)}
    if extra:
        errors.append(f"M4: writer dispatched for unplanned chapters: {sorted(extra)}")


def _check_skill_calls(root: Path, node_id: str, node: dict[str, Any],
                       figure_dispatched: bool, errors: list[str]) -> None:
    calls = node.get("skill_invocations")
    if not isinstance(calls, list):
        errors.append(f"{node_id}: skill_invocations must be a list")
        return
    completed: set[str] = set()
    for index, call in enumerate(calls):
        if not isinstance(call, dict) or not isinstance(call.get("skill"), str):
            errors.append(f"{node_id}.skill_invocations[{index}]: skill required")
            continue
        if call.get("status") != "completed":
            errors.append(f"{node_id}: skill {call['skill']} not completed")
        ref = {"path": call.get("evidence_ref"), "sha256": call.get("evidence_sha256")}
        _artifact(root, ref, f"{node_id}.{call['skill']}.evidence", errors)
        completed.add(call["skill"])
    required = set(REQUIRED_SKILLS[node_id])
    if figure_dispatched and node_id in {"M2", "M3"}:
        required.update(("scipilot-figure-skill", "modelviz"))
    if figure_dispatched and node_id == "M4":
        registry_ref = node.get("figure_registry")
        found = _artifact(root, registry_ref, "M4.figure_registry", errors)
        if found:
            registry = _read(found[1], errors)
            figures = registry.get("figures", [])
            routes = {item.get("generator") for item in figures if isinstance(item, dict) and isinstance(item.get("generator"), str)} if isinstance(figures, list) else set()
            if "modelviz" in routes:
                required.update(("scipilot-figure-skill", "modelviz"))
            if "tech-route-maker" in routes:
                required.add("tech-route-maker")
            if "tikz-scientific-figures" in routes:
                required.add("tikz-scientific-figures")
    for skill in sorted(required - completed):
        errors.append(f"{node_id}: required skill invocation missing: {skill}")


def _node_refs(root: Path, node_id: str, node: dict[str, Any],
               errors: list[str]) -> dict[str, tuple[str, Path]]:
    refs: dict[str, tuple[str, Path]] = {}
    for field in NODE_ARTIFACTS[node_id]:
        found = _artifact(root, node.get(field), f"{node_id}.{field}", errors)
        if found:
            refs[field] = found
    return refs


def _review(root: Path, log: dict[str, Any], gate: str, packet_ref: Any,
            extra_refs: list[tuple[str, Path]], errors: list[str], pauses: list[str]) -> datetime | None:
    found = _artifact(root, packet_ref, f"{gate}.review_packet", errors)
    if not found:
        return None
    packet = _read(found[1], errors)
    if packet.get("node_id") != gate.split(":", 1)[0].split("_", 1)[0]:
        errors.append(f"{gate}: review packet node_id mismatch")
    artifacts = packet.get("important_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append(f"{gate}: important_artifacts required")
        artifacts = []
    checked = [found]
    for index, item in enumerate(artifacts):
        ref = _artifact(root, item, f"{gate}.important_artifacts[{index}]", errors)
        if ref:
            checked.append(ref)
    if extra_refs and not set(path for path, _ in extra_refs).issubset({path for path, _ in checked}):
        errors.append(f"{gate}: review packet omits required artifacts")
    checks = packet.get("checks")
    if not isinstance(checks, list) or not checks or any(
        not isinstance(check, dict) or check.get("status") != "PASS" for check in checks
    ):
        errors.append(f"{gate}: checks must be nonempty and PASS")
    elif isinstance(checks, list):
        for index, check in enumerate(checks):
            _artifact(root, {"path": check.get("evidence_ref"),
                             "sha256": check.get("evidence_sha256")},
                      f"{gate}.checks[{index}]", errors)
    return _approval(log, gate, checked, errors, pauses)


def _validate_node_evidence(root: Path, node_id: str, refs: dict[str, tuple[str, Path]],
                            ids: dict[str, str], subproblems: list[str], errors: list[str]) -> None:
    if node_id == "M2":
        if "leakage_audit" in refs:
            audit = _read(refs["leakage_audit"][1], errors)
            if audit.get("status") != "PASS" or audit.get("verification_agent_instance_id") != ids.get("verifier"):
                errors.append("M2: leakage audit requires independent verifier PASS")
            if not all(isinstance(audit.get(key), str) and HEX64.fullmatch(audit[key])
                       for key in ("dataset_sha256", "feature_pipeline_sha256")):
                errors.append("M2: leakage audit requires dataset and feature pipeline hashes")
            if not audit.get("split_policy"):
                errors.append("M2: leakage audit requires split_policy")
            _named_pass_checks(root, audit.get("checks"), LEAKAGE_CHECKS, "M2.leakage_audit", errors)
        if "literature_sources" in refs:
            sources = _read(refs["literature_sources"][1], errors)
            entries = sources.get("sources")
            if sources.get("status") != "PASS" or not isinstance(entries, list) or not entries:
                errors.append("M2: user literature sources must be verified and nonempty")
            else:
                covered: set[str] = set()
                seen: set[str] = set()
                for index, item in enumerate(entries):
                    label = f"M2.literature_sources[{index}]"
                    if not isinstance(item, dict):
                        errors.append(f"{label}: source mapping required")
                        continue
                    key = item.get("citation_key")
                    questions = item.get("subproblems")
                    if not isinstance(key, str) or not key or key in seen:
                        errors.append(f"{label}: unique citation_key required")
                    else:
                        seen.add(key)
                    if not isinstance(questions, list) or not questions or not all(isinstance(q, str) for q in questions):
                        errors.append(f"{label}: subproblems required")
                    else:
                        if not set(questions).issubset(subproblems):
                            errors.append(f"{label}: unknown subproblem")
                        covered.update(questions)
                    if item.get("user_supplied") is not True or not all(item.get(field) for field in ("locator", "use")):
                        errors.append(f"{label}: user source locator and actual use required")
                    _artifact(root, item.get("summary_ref"), f"{label}.summary_ref", errors)
                if covered != set(subproblems):
                    errors.append("M2: literature use must cover every subproblem")
    elif node_id == "M3":
        if "run_manifest" in refs:
            manifest = _read(refs["run_manifest"][1], errors)
            if manifest.get("solver_instance_id") != ids.get("solver") or not isinstance(manifest.get("seed"), int):
                errors.append("M3: run_manifest solver_instance_id/seed invalid")
            if not isinstance(manifest.get("command"), list) or not manifest["command"]:
                errors.append("M3: run_manifest command required")
            results = manifest.get("results")
            if not isinstance(results, list) or not all(isinstance(r, dict) and isinstance(r.get("subproblem_id"), str) for r in results) or {r["subproblem_id"] for r in results} != set(subproblems):
                errors.append("M3: run_manifest must cover every subproblem")
            else:
                for index, item in enumerate(results):
                    _artifact(root, item, f"M3.run_manifest.results[{index}]", errors)
        if "independent_validation" in refs:
            audit = _read(refs["independent_validation"][1], errors)
            if audit.get("status") != "PASS" or audit.get("verification_agent_instance_id") != ids.get("verifier"):
                errors.append("M3: independent validation requires verifier PASS")
            checked = audit.get("checked_subproblems")
            if not isinstance(checked, list) or not all(isinstance(item, str) for item in checked) or set(checked) != set(subproblems):
                errors.append("M3: independent validation must cover every subproblem")
            _named_pass_checks(root, audit.get("checks"), MODEL_CHECKS, "M3.independent_validation", errors)
    elif node_id == "M5":
        if "reproducibility_report" in refs:
            report = _read(refs["reproducibility_report"][1], errors)
            if report.get("status") != "PASS" or report.get("exit_code") != 0:
                errors.append("M5: isolated reproduction must PASS with exit_code=0")
            if not isinstance(report.get("command"), list) or not report["command"]:
                errors.append("M5: reproduction command required")
            results = report.get("result_refs")
            if not isinstance(results, list) or not results:
                errors.append("M5: reproduced result_refs required")
            else:
                for index, item in enumerate(results):
                    _artifact(root, item, f"M5.result_refs[{index}]", errors)
        if "delivery_report" in refs:
            report = _read(refs["delivery_report"][1], errors)
            checks = report.get("checks")
            if report.get("status") != "PASS" or not isinstance(checks, dict):
                errors.append("M5: delivery_report status/checks invalid")
            else:
                for name in DELIVERY_CHECKS:
                    item = checks.get(name)
                    if not isinstance(item, dict) or item.get("status") != "PASS":
                        errors.append(f"M5: delivery check {name} must PASS")
                    else:
                        _artifact(root, {"path": item.get("evidence_ref"),
                                         "sha256": item.get("evidence_sha256")},
                                  f"M5.checks.{name}", errors)


def _validate_figures(root: Path, plan_path: Path, registry_path: Path,
                      errors: list[str]) -> int:
    plan = _read(plan_path, errors)
    registry = _read(registry_path, errors)
    catalog = _read(Path(__file__).resolve().parents[1] / "references" / "figure_template_catalog.yaml", errors)
    catalog_routes = {
        item["template_id"]: item
        for item in catalog.get("templates", [])
        if isinstance(item, dict) and isinstance(item.get("template_id"), str)
    }
    slots = plan.get("slots")
    figures = registry.get("figures")
    if not isinstance(slots, list) or not isinstance(figures, list):
        errors.append("M4: visual plan slots and figure_registry.figures must be lists")
        return 0
    planned: dict[str, tuple[str, str | None]] = {}
    for index, slot in enumerate(slots):
        if not isinstance(slot, dict) or not isinstance(slot.get("slot_id"), str) or not slot["slot_id"]:
            errors.append(f"M4.visual.slots[{index}]: slot_id required")
            continue
        if slot["slot_id"] in planned:
            errors.append(f"M4: duplicate visual slot {slot['slot_id']}")
        representation = slot.get("representation")
        if representation not in {"figure", "table", "text"}:
            errors.append(f"M4.visual.slots[{index}]: representation invalid")
        if representation == "figure":
            route = slot.get("generation_route")
            if route not in {"modelviz", "tech-route-maker", "tikz-scientific-figures"}:
                errors.append(f"M4.visual.slots[{index}]: generation_route invalid")
            else:
                template_id = slot.get("template_id")
                if route in {"tech-route-maker", "tikz-scientific-figures"}:
                    entry = catalog_routes.get(template_id)
                    if not entry or entry.get("generation_route") != route:
                        errors.append(f"M4.visual.slots[{index}]: template_id/route mismatch")
                planned[slot["slot_id"]] = (route, template_id)
            evidence = slot.get("evidence_refs")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"M4.visual.slots[{index}]: evidence_refs required")
            else:
                for ref_index, ref in enumerate(evidence):
                    _artifact(root, ref, f"M4.visual.slots[{index}].evidence[{ref_index}]", errors)
    actual: set[str] = set()
    for index, figure in enumerate(figures):
        if not isinstance(figure, dict):
            errors.append(f"M4.figure_registry.figures[{index}]: mapping required")
            continue
        slot_ids = figure.get("visual_slot_ids")
        if not isinstance(slot_ids, list) or len(slot_ids) != 1 or not isinstance(slot_ids[0], str) or slot_ids[0] not in planned:
            errors.append(f"M4.figure_registry.figures[{index}]: one approved visual_slot_id required")
            continue
        slot_id = slot_ids[0]
        if slot_id in actual:
            errors.append(f"M4: visual slot realized twice: {slot_id}")
        actual.add(slot_id)
        route, template_id = planned[slot_id]
        if figure.get("generator") != route or figure.get("generation_route") != route:
            errors.append(f"M4: generator mismatch for {slot_id}")
        if route in {"tech-route-maker", "tikz-scientific-figures"}:
            entry = catalog_routes.get(template_id)
            if figure.get("template_id") != template_id or not entry or figure.get("template_sha256") != entry.get("template_sha256"):
                errors.append(f"M4: template provenance mismatch for {slot_id}")
            expected_kind = "flowchart" if route == "tech-route-maker" else "schematic"
            if figure.get("kind") != expected_kind:
                errors.append(f"M4: kind/route mismatch for {slot_id}")
        formats = figure.get("formats")
        if not isinstance(formats, list) or not all(isinstance(item, str) for item in formats) or set(formats) != {"svg", "png"} or figure.get("insertion_format") != "svg":
            errors.append(f"M4: SVG+PNG outputs and SVG insertion required for {slot_id}")
        if figure.get("visual_qa") != "passed" or figure.get("qa_status") != "reviewed":
            errors.append(f"M4: visual QA required for {slot_id}")
        if not figure.get("caption") or not figure.get("source_files"):
            errors.append(f"M4: caption/source_files required for {slot_id}")
        for extension in ("svg", "png"):
            _artifact(root, {"path": figure.get(extension),
                             "sha256": figure.get(f"{extension}_sha256")},
                      f"M4.figures[{index}].{extension}", errors)
        if route == "modelviz":
            if figure.get("decision_author") != "scipilot-figure-skill" or figure.get("semantic_qa") != "scipilot-figure-skill":
                errors.append(f"M4: SciPilot decision and QA required for {slot_id}")
            _artifact(root, {"path": figure.get("decision_card"),
                             "sha256": figure.get("decision_card_sha256")},
                      f"M4.figures[{index}].decision_card", errors)
        elif route in {"tech-route-maker", "tikz-scientific-figures"}:
            starter = _artifact(root, {"path": figure.get("starter_source"),
                                       "sha256": figure.get("starter_sha256")},
                                f"M4.figures[{index}].starter_source", errors)
            if starter and starter[0].split(".")[-1] != ("json" if route == "tech-route-maker" else "tex"):
                errors.append(f"M4: starter source type mismatch for {slot_id}")
            if starter and entry and starter[1] and figure.get("starter_sha256") != entry.get("template_sha256"):
                errors.append(f"M4: starter/catalog hash mismatch for {slot_id}")
            script = _artifact(root, {"path": figure.get("script"),
                                      "sha256": figure.get("script_sha256")},
                               f"M4.figures[{index}].script", errors)
            if script and script[0].split(".")[-1] != ("json" if route == "tech-route-maker" else "tex"):
                errors.append(f"M4: script source type mismatch for {slot_id}")
    if set(planned) != actual:
        errors.append(f"M4: visual slots not closed: {sorted(set(planned) - actual)}")
    return len(planned)


def _writing_preflight(root: Path, control: dict[str, Any], log: dict[str, Any],
                       ids: dict[str, str], subproblems: list[str],
                       errors: list[str], pauses: list[str]) -> int:
    m4 = control.get("nodes", {}).get("M4", {})
    if not isinstance(m4, dict):
        errors.append("M4 node mapping required")
        return 0
    def required(field: str) -> tuple[str, Path] | None:
        value = m4.get(field)
        if value is None:
            pauses.append(f"M4: {field} not ready")
            return None
        return _artifact(root, value, f"M4.{field}", errors)

    figure_count = 0
    for field, gate, packet_field in (
        ("visual_argument_plan", "M4_VISUAL_PLAN", "visual_plan_review_packet"),
        ("paper_argument_blueprint", "M4_WRITING_PLAN", "writing_plan_review_packet"),
    ):
        found = required(field)
        if found:
            if m4.get(packet_field) is None:
                pauses.append(f"{gate}: review packet not ready")
            else:
                _review(root, log, gate, m4.get(packet_field), [found], errors, pauses)
    plan_ref = m4.get("visual_argument_plan")
    registry_ref = required("figure_registry")
    if isinstance(plan_ref, dict) and registry_ref:
        plan_file = _artifact(root, plan_ref, "M4.visual_argument_plan", errors)
        if plan_file:
            figure_count = _validate_figures(root, plan_file[1], registry_ref[1], errors)
    readiness_ref = required("paper_material_readiness")
    if readiness_ref:
        readiness = _read(readiness_ref[1], errors)
        if readiness.get("status") != "PASS" or readiness.get("verification_agent_instance_id") != ids.get("verifier"):
            pauses.append("M4: paper_material_readiness requires verifier PASS")
        matrix = readiness.get("evidence_matrix")
        if not isinstance(matrix, dict) or set(matrix) != set(subproblems):
            errors.append("M4: evidence_matrix must cover exactly the declared subproblems")
        else:
            for question in subproblems:
                cells = matrix[question]
                if not isinstance(cells, dict):
                    errors.append(f"M4: {question} evidence matrix must be a mapping")
                    continue
                for field in MATERIAL_FIELDS:
                    cell = cells.get(field)
                    if not isinstance(cell, dict) or cell.get("status") != "ready":
                        pauses.append(f"M4: {question}.{field} material not ready")
                    else:
                        _artifact(root, cell, f"M4.{question}.{field}", errors)
        chapters = readiness.get("chapters")
        if not isinstance(chapters, list) or not chapters or any(
            not isinstance(item, dict) or not item.get("chapter_id") or
            not item.get("capacity") or not item.get("material_refs") for item in chapters
        ):
            errors.append("M4: chapter capacity and material coverage required")
        else:
            for chapter_index, chapter in enumerate(chapters):
                for ref_index, item in enumerate(chapter["material_refs"]):
                    _artifact(root, item, f"M4.chapters[{chapter_index}].material_refs[{ref_index}]", errors)
    claims_ref = required("paper_claim_coverage")
    if claims_ref:
        claims = _read(claims_ref[1], errors)
        if claims.get("status") != "PASS" or not readiness_ref or claims.get("readiness_sha256") != _digest(readiness_ref[1]):
            pauses.append("M4: paper_claim_coverage is not bound to ready materials")
        entries = claims.get("claims")
        if not isinstance(entries, list) or not entries:
            errors.append("M4: claims list required")
        else:
            seen: set[str] = set()
            for index, claim in enumerate(entries):
                if not isinstance(claim, dict) or not isinstance(claim.get("id"), str) or not claim["id"] or claim["id"] in seen or not claim.get("paper_anchor"):
                    errors.append(f"M4.claims[{index}]: unique id and paper_anchor required")
                    continue
                seen.add(claim["id"])
                refs = claim.get("evidence_refs")
                if not isinstance(refs, list) or not refs:
                    errors.append(f"M4.claims[{index}]: evidence_refs required")
                else:
                    for ref_index, item in enumerate(refs):
                        _artifact(root, item, f"M4.claims[{index}].evidence_refs[{ref_index}]", errors)
    return figure_count


def check(root: Path, through: str = "M1", preflight_writing: bool = False) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    pauses: list[str] = []
    control = _read(root / ".contest" / "mathorcup_control.yaml", errors)
    log = _read(root / ".contest" / "approval_log.yaml", errors)
    if control.get("active_mode") != "full-contest-mathorcup":
        errors.append("active_mode must be full-contest-mathorcup")
    if control.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    profile_ref = _artifact(root, control.get("competition_profile"), "competition_profile", errors)
    if profile_ref:
        profile = _read(profile_ref[1], errors)
        _artifact(root, profile.get("official_rules_source"), "official_rules_source", errors)
    scope = control.get("problem_scope")
    subproblems = scope.get("subproblems") if isinstance(scope, dict) else None
    if not isinstance(subproblems, list) or not subproblems or any(
        not isinstance(item, str) or not item for item in subproblems
    ) or len(set(subproblems)) != len(subproblems):
        errors.append("problem_scope.subproblems must be a nonempty unique list")
        subproblems = []
    ids = _check_instances(root, control, errors)
    nodes = control.get("nodes")
    if not isinstance(nodes, dict):
        errors.append("nodes must be a mapping")
        nodes = {}
    approval_times: dict[str, datetime] = {}
    figure_count = 0
    through_index = NODES.index("M3") if preflight_writing else NODES.index(through)
    for node_id in NODES[:through_index + 1]:
        node = nodes.get(node_id)
        if not isinstance(node, dict):
            errors.append(f"{node_id}: node mapping required")
            continue
        if node.get("status") not in {"approved", "frozen"}:
            pauses.append(f"{node_id}: node not approved")
            continue
        refs = _node_refs(root, node_id, node, errors)
        _validate_node_evidence(root, node_id, refs, ids, subproblems, errors)
        if node_id == "M4":
            figure_count = _writing_preflight(root, control, log, ids, subproblems, errors, pauses)
            chapters = node.get("chapters")
            if not isinstance(chapters, list) or not chapters:
                errors.append("M4: chapters and chapter review packets required")
            else:
                seen: set[str] = set()
                for chapter in chapters:
                    if not isinstance(chapter, dict) or not isinstance(chapter.get("chapter_id"), str) or not chapter["chapter_id"] or chapter["chapter_id"] in seen:
                        errors.append("M4: unique chapter_id required")
                        continue
                    chapter_id = chapter["chapter_id"]
                    seen.add(chapter_id)
                    manuscript = _artifact(root, chapter.get("manuscript"), f"M4.{chapter_id}.manuscript", errors)
                    if manuscript:
                        _review(root, log, f"M4_CHAPTER:{chapter_id}", chapter.get("review_packet"),
                                [manuscript], errors, pauses)
            if node.get("writing_started") is not True:
                errors.append("M4: writing_started must be true for completed node")
        found_packet = _artifact(root, node.get("review_packet"), f"{node_id}.review_packet", errors)
        if found_packet:
            approval_times[node_id] = _review(root, log, node_id, node.get("review_packet"),
                                              list(refs.values()), errors, pauses) or None
    dispatch_index = NODES.index("M4") if preflight_writing else through_index
    dispatched, m4_phases = _check_dispatch(root, control, ids, log, approval_times, dispatch_index, errors)
    if preflight_writing or through_index >= NODES.index("M4"):
        _check_chapter_sequence(root, control, log, errors)
    for node_id in NODES[:through_index + 1]:
        node = nodes.get(node_id)
        if not isinstance(node, dict) or node.get("status") not in {"approved", "frozen"}:
            continue
        for role in REQUIRED_ROLES[node_id] - dispatched.get(node_id, set()):
            errors.append(f"{node_id}: required role not dispatched: {role}")
        _check_skill_calls(root, node_id, node, "figure" in dispatched.get(node_id, set()), errors)
    if preflight_writing:
        for role in REQUIRED_ROLES["M4"] - dispatched.get("M4", set()):
            errors.append(f"M4: required role not dispatched: {role}")
        figure_count = _writing_preflight(root, control, log, ids, subproblems, errors, pauses)
        m4 = nodes.get("M4", {})
        if isinstance(m4, dict) and m4.get("writing_started") and (errors or pauses):
            errors.append("M4: writing started before preflight PASS")
    if preflight_writing or through_index >= NODES.index("M4"):
        if figure_count and "generate" not in m4_phases["figure"]:
            errors.append("M4: approved figure plan requires post-approval generate dispatch")
        m4 = nodes.get("M4", {})
        if isinstance(m4, dict) and m4.get("writing_started") and "write" not in m4_phases["writer"]:
            errors.append("M4: writing_started requires post-approval writer dispatch")
    status = "BLOCK" if errors else "PAUSE" if pauses else "PASS"
    return {"status": status, "active_mode": control.get("active_mode"),
            "through": "M4-writing" if preflight_writing else through,
            "failures": errors, "pending": pauses}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--through", choices=NODES, default="M1")
    group.add_argument("--preflight-writing", action="store_true")
    args = parser.parse_args()
    report = check(args.project_root, through=args.through, preflight_writing=args.preflight_writing)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return {"PASS": 0, "PAUSE": 2, "BLOCK": 1}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
