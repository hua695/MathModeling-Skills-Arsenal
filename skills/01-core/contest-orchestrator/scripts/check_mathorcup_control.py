#!/usr/bin/env python3
"""Check MathorCup node approvals, role dispatch, and frozen evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import uuid
from datetime import date, datetime
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
M4_SOLVER_TASK_PHASES = {
    "MC25A-M4-H5-MATERIAL-AUDIT-001": "post_h6_paper_material_audit",
    "MC25A-M4-H5-SUMMARY-CARDS-001": "evidence_reconciliation",
}
M4_VISUAL_PLAN_CHECKS = {
    "subproblem_coverage", "q1_claim_boundary", "q2_selection_evidence",
    "model_fact_scope", "q2_threshold_sweep_boundary", "q3_interpretation_boundary",
    "cross_question_interface", "source_coverage", "representation_minimum",
    "body_page_role", "protected_scope", "template_execution_readiness",
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
    "M4": {"academic-writing", "mathmodel-latex-skill", "论文辅助"},
    "M5": {"mathmodel-latex-skill"},
}
NODE_ARTIFACTS = {
    "M1": ("problem_statement", "data_overview", "task_kpi", "literature_request"),
    "M2": ("eda_report", "features", "leakage_audit", "literature_sources"),
    "M3": ("run_manifest", "model_summary_cards", "result_interpretation_cards", "independent_validation"),
    "M4": ("visual_argument_plan", "figure_registry", "paper_argument_blueprint", "paper_language_profile", "paper_material_readiness", "paper_claim_coverage", "abstract_framework", "paper_pdf"),
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
PREAUTH_POLICY = "user_preauthorized_autoadvance_for_this_replay_only"
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


def _has_task_card_prohibitions(card: dict[str, Any]) -> bool:
    actions = card.get("prohibited_actions")
    if isinstance(actions, list) and any(isinstance(item, str) and item.strip() for item in actions):
        return True
    verification = card.get("verification")
    return isinstance(verification, list) and any(
        isinstance(item, str) and re.match(r"^\s*(?:do not|must not|never)\b", item, re.IGNORECASE)
        for item in verification
    )


def _artifact(root: Path, ref: Any, label: str, errors: list[str],
              reviewed: dict[str, str] | None = None) -> tuple[str, Path] | None:
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
    if actual != ref["sha256"].lower() and (reviewed or {}).get(relative) != actual:
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


def _unique_strings(value: Any, label: str, errors: list[str], allow_empty: bool = False) -> set[str]:
    if (not isinstance(value, list) or (not value and not allow_empty)
            or any(not isinstance(item, str) or not item.strip() for item in value)):
        errors.append(f"{label}: explicit string list required")
        return set()
    if len(set(value)) != len(value):
        errors.append(f"{label}: duplicate entries")
    return set(value)


def _check_requirement_coverage(root: Path, kpi: dict[str, Any], coverage: Any,
                                subproblems: list[str], errors: list[str]) -> None:
    """Compare actual result keys with the frozen problem requirements, not model size."""
    requirements = kpi.get("subproblems")
    if not isinstance(requirements, dict) or set(requirements) != set(subproblems):
        errors.append("task_kpi.subproblems: exact problem coverage required")
        return
    if not isinstance(coverage, dict) or set(coverage) != set(subproblems):
        errors.append("model_summary_cards.requirement_coverage: exact problem coverage required")
        return
    for question in subproblems:
        label = f"requirements.{question}"
        required, actual = requirements[question], coverage[question]
        if not isinstance(required, dict) or not isinstance(actual, dict):
            errors.append(f"{label}: requirement and coverage mappings required")
            continue
        _artifact(root, required.get("source"), f"{label}.source", errors)
        if not all(required.get(key) for key in ("locator", "requirement_text", "final_carrier")):
            errors.append(f"{label}: source locator, original requirement text and final carrier required")
        targets = _unique_strings(required.get("targets"), f"{label}.targets", errors)
        count = required.get("outputs_per_target")
        if type(count) is not int or count < 1:
            errors.append(f"{label}: positive outputs_per_target required")
            continue
        found = _artifact(root, actual.get("output_artifact"), f"{label}.output_artifact", errors)
        rows = []
        if found:
            if found[1].suffix.lower() == ".csv":
                try:
                    with found[1].open(encoding="utf-8-sig", newline="") as stream:
                        rows = list(csv.DictReader(stream))
                except (OSError, UnicodeError, csv.Error) as exc:
                    errors.append(f"{label}: unreadable output CSV: {exc}")
            else:
                rows = _read(found[1], errors).get("outputs")
        if not isinstance(rows, list):
            errors.append(f"{label}: output records required")
            rows = []
        groups: dict[str, set[str]] = {}
        target_field = actual.get("target_field", "target_id")
        output_field = actual.get("output_field", "output_id")
        for row in rows:
            if (not isinstance(row, dict) or not isinstance(target_field, str)
                    or not isinstance(output_field, str)
                    or not isinstance(row.get(target_field), str)
                    or not isinstance(row.get(output_field), str) or not row[output_field].strip()):
                errors.append(f"{label}: target/output key missing")
                continue
            target, output = row[target_field], row[output_field]
            outputs = groups.setdefault(target, set())
            if output in outputs:
                errors.append(f"{label}: duplicate output for {target}: {output}")
            outputs.add(output)
        if set(groups) != targets or any(len(group) != count for group in groups.values()):
            errors.append(f"{label}: incomplete target/output coverage; missing={sorted(targets - set(groups))}")
        constraints = required.get("constraints", [])
        checks = actual.get("constraints", [])
        if (not isinstance(constraints, list) or not isinstance(checks, list)
                or any(not isinstance(item, dict) for item in constraints + checks)):
            errors.append(f"{label}: constraint lists required")
            continue
        expected = _unique_strings([c.get("constraint_id") for c in constraints],
                                   f"{label}.constraints", errors, allow_empty=True)
        observed = _unique_strings([c.get("constraint_id") for c in checks],
                                   f"{label}.constraint_checks", errors, allow_empty=True)
        if expected != observed:
            errors.append(f"{label}: original constraints must each have a check")
        by_id = {item.get("constraint_id"): item for item in checks if isinstance(item.get("constraint_id"), str)}
        for constraint in constraints:
            constraint_id = constraint.get("constraint_id")
            check = by_id.get(constraint_id, {}) if isinstance(constraint_id, str) else {}
            if (check.get("status") != "PASS" or check.get("evaluation_kind") != "original"
                    or not constraint.get("object") or not constraint.get("unit")
                    or any(check.get(key) != constraint.get(key) for key in ("object", "unit"))):
                errors.append(f"{label}.{constraint.get('constraint_id')}: original constraint remains uncertified; proxy/UNKNOWN is not PASS")
            _artifact(root, check.get("evidence"), f"{label}.constraint_evidence", errors)


def _check_reproduction(root: Path, manifest: dict[str, Any], report: dict[str, Any] | None,
                        errors: list[str]) -> None:
    entry = manifest.get("training_entrypoint")
    if not isinstance(entry, dict):
        errors.append("run_manifest.training_entrypoint: raw-data training entry required")
        return
    _artifact(root, entry.get("script"), "training_entrypoint.script", errors)
    command = entry.get("command")
    if not isinstance(command, list) or not command or any(not isinstance(x, str) or not x for x in command):
        errors.append("training_entrypoint.command: argv required")
    inputs = entry.get("raw_inputs")
    configs = entry.get("config_refs", [])
    if not isinstance(inputs, list) or not inputs or not isinstance(configs, list):
        errors.append("training_entrypoint: raw inputs and configuration references required")
    else:
        for ref in inputs + configs:
            found = _artifact(root, ref, "training_entrypoint.input", errors)
            if found and ".contest" in found[1].relative_to(root).parts:
                errors.append("training_entrypoint: numerical configuration must not depend on approval files")
    if report is None:
        return
    levels = {"saved_results": 0, "inference": 1, "refit": 2, "full_retrain": 3}
    level = report.get("level")
    if not isinstance(level, str) or level not in levels or report.get("claim") not in ("partial", "full"):
        errors.append("reproduction: explicit level and partial/full claim required")
        return
    if report.get("clean_directory") is not True:
        errors.append("reproduction: isolated clean directory required")
    required = _unique_strings(report.get("required_units"), "reproduction.required_units", errors)
    plan = manifest.get("reproduction_plan")
    if not isinstance(plan, dict):
        errors.append("run_manifest.reproduction_plan: frozen reproduction scope required")
    else:
        planned = _unique_strings(plan.get("required_units"), "reproduction_plan.required_units", errors)
        minimum_level = plan.get("minimum_level")
        if required != planned or not isinstance(minimum_level, str) or minimum_level not in levels:
            errors.append("reproduction: required units/level must match the frozen plan")
        elif levels[level] < levels[minimum_level]:
            errors.append("reproduction: result checks cannot replace the planned training verification")
    completed = _unique_strings(report.get("completed_units"), "reproduction.completed_units", errors)
    runs = report.get("runs")
    if not isinstance(runs, list) or not runs or any(not isinstance(run, dict) for run in runs):
        errors.append("reproduction: executed runs required")
        return
    executed = _unique_strings([run.get("unit_id") for run in runs], "reproduction.runs", errors)
    if not completed.issubset(required) or executed != completed:
        errors.append("reproduction: completed units must match executed units within required scope")
    if (report.get("claim") == "full" or level == "full_retrain") and completed != required:
        errors.append("reproduction: full claim requires every planned unit")
    for run in runs:
        run_level = run.get("level")
        if run.get("exit_code") != 0 or not isinstance(run_level, str) or levels.get(run_level, -1) < levels[level]:
            errors.append("reproduction: failed or lower-level run cannot certify claimed level")
        if not isinstance(run.get("command"), list) or not run["command"]:
            errors.append("reproduction: execution argv required")
        refs = run.get("result_refs")
        if not isinstance(refs, list) or not refs:
            errors.append("reproduction: per-run result references required")
        else:
            for ref in refs:
                _artifact(root, ref, "reproduction.run.result", errors)


def _named_pass_checks(root: Path, value: Any, required: set[str], label: str,
                       errors: list[str], reviewed: dict[str, str] | None = None) -> None:
    if isinstance(value, dict) and value:
        entries = list(value.items())
    elif isinstance(value, list) and value:
        entries = [(item.get("name") if isinstance(item, dict) else None, item)
                   for item in value]
    else:
        errors.append(f"{label}: checks must be a nonempty list or mapping")
        return
    names: set[str] = set()
    for index, (name, item) in enumerate(entries):
        if not isinstance(name, str) or not name or not isinstance(item, dict) or item.get("status") != "PASS":
            errors.append(f"{label}.checks[{index}]: named PASS check required")
            continue
        names.add(name)
        _artifact(root, {"path": item.get("evidence_ref"),
                         "sha256": item.get("evidence_sha256")},
                  f"{label}.checks[{index}].evidence", errors, reviewed)
    for name in sorted(required - names):
        errors.append(f"{label}: missing PASS check {name}")


def _preauthorized_date(root: Path, control: dict[str, Any], log: dict[str, Any],
                        gate: str, errors: list[str]) -> date | None:
    if control.get("approval_policy") != PREAUTH_POLICY:
        return None
    scope_gate = gate.split(":", 1)[0]
    if gate in NODES:
        node_id = gate
    elif gate.startswith("M4_"):
        node_id = "M4"
    else:
        return None
    nodes = control.get("nodes")
    node = nodes.get(node_id) if isinstance(nodes, dict) else None
    pointer = node.get("advancement_authorization") if isinstance(node, dict) else None
    authorizations = log.get("authorizations")
    if not isinstance(authorizations, list):
        errors.append("approval_log.authorizations must be a list for preauthorized advancement")
        return None
    applicable = [item for item in authorizations if isinstance(item, dict)
                  and isinstance(item.get("applies_to"), list)
                  and scope_gate in item["applies_to"]]
    if not applicable:
        return None
    if len(applicable) != 1:
        errors.append(f"{gate}: exactly one applicable preauthorization required")
        return None
    authorization = applicable[0]
    auth_id = authorization.get("id")
    if not isinstance(auth_id, str) or not auth_id:
        errors.append(f"{gate}: preauthorization id required")
        return None
    if authorization.get("type") != "preauthorized_autoadvance" or authorization.get("authorized_by") != "user":
        errors.append(f"{gate}: preauthorization must be explicitly user-authorized")
    scope = authorization.get("scope")
    if not isinstance(scope, str) or "replay only" not in scope.lower():
        errors.append(f"{gate}: preauthorization scope must be limited to this replay")
    conditions = authorization.get("conditions")
    if not isinstance(conditions, list) or not conditions or not all(
        isinstance(item, str) and item.strip() for item in conditions
    ):
        errors.append(f"{gate}: preauthorization conditions must be recorded")
    applies_to = authorization.get("applies_to")
    if not isinstance(applies_to, list) or not all(isinstance(item, str) for item in applies_to):
        errors.append(f"{gate}: preauthorization applies_to must be a list of gates")
    authorized_on = authorization.get("authorized_on")
    try:
        authorized_date = date.fromisoformat(authorized_on) if isinstance(authorized_on, str) else None
    except ValueError:
        authorized_date = None
    if authorized_date is None:
        errors.append(f"{gate}: preauthorization authorized_on must be an ISO date")

    source_path = ".contest/approval_log.yaml"
    try:
        source_file = (root / source_path).resolve()
        source_file.relative_to(root)
    except (OSError, ValueError):
        source_file = None
    actual_source_digest = (
        _digest(source_file) if source_file is not None and source_file.is_file() else None
    )
    if (not isinstance(pointer, dict) or pointer.get("id") != auth_id
            or pointer.get("source") != source_path
            or pointer.get("source_sha256") != actual_source_digest
            or not isinstance(actual_source_digest, str)):
        errors.append(f"{gate}: node advancement_authorization must bind the current approval log")
    if authorized_date is None:
        return None
    return authorized_date


def _approval(root: Path, control: dict[str, Any], log: dict[str, Any], gate: str,
              refs: list[tuple[str, Path]], errors: list[str],
              pauses: list[str]) -> datetime | date | None:
    approvals = log.get("approvals")
    if not isinstance(approvals, list):
        errors.append("approval_log.approvals must be a list")
        return None
    matching = [entry for entry in approvals if isinstance(entry, dict) and entry.get("gate") == gate
                and entry.get("decision") == "approve" and entry.get("approved_by") == "user"]
    if not matching:
        authorized_date = _preauthorized_date(root, control, log, gate, errors)
        if authorized_date is not None:
            return authorized_date
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


def _check_instances(root: Path, control: dict[str, Any], errors: list[str],
                     required_roles: set[str] | None = None) -> dict[str, str]:
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
        if required_roles is not None and role not in required_roles and record is None:
            continue
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
    if "solver" in ids and control.get("solver_instance_id") != ids.get("solver"):
        errors.append("solver_instance_id must equal the sole solver instance")
    if ids.get("verifier") == ids.get("solver") and ids.get("solver"):
        errors.append("verifier must use an independent instance")
    return ids


def _node_instances(root: Path, control: dict[str, Any], log: dict[str, Any],
                    base: dict[str, str], through_index: int,
                    errors: list[str]) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, datetime]]]:
    """Resolve boundary recoveries without relabeling any historical dispatch."""
    resolved = {node: dict(base) for node in NODES}
    activation: dict[str, dict[str, datetime]] = {node: {} for node in NODES}
    events = log.get("instance_recoveries", [])
    if not isinstance(events, list):
        errors.append("approval_log.instance_recoveries must be a list")
        return resolved, activation
    seen_events: set[str] = set()
    last_boundary: dict[str, int] = {}
    seen_ids = set(base.values())
    for index, event in enumerate(events):
        label = f"instance_recoveries[{index}]"
        if not isinstance(event, dict) or event.get("effective_from_node") not in NODES[1:]:
            errors.append(f"{label}: recovery must start at a boundary after M1")
            continue
        start = NODES.index(event["effective_from_node"])
        if start > through_index:
            continue
        before = len(errors)
        event_id = event.get("id")
        if not isinstance(event_id, str) or not event_id or event_id in seen_events:
            errors.append(f"{label}: unique recovery id required")
        else:
            seen_events.add(event_id)
        approved_at = _time(event.get("approved_at"))
        if (event.get("decision") != "approve" or event.get("approved_by") != "user"
                or not isinstance(approved_at, datetime)):
            errors.append(f"{label}: explicit user approval and timezone-aware time required")
        for key in ("source_ref", "context_ref", "recovery_record_ref"):
            _artifact(root, event.get(key), f"{label}.{key}", errors)
        configured_nodes = control.get("nodes", {})
        predecessor = configured_nodes.get(NODES[start - 1], {}) if isinstance(configured_nodes, dict) else {}
        if not isinstance(predecessor, dict) or event.get("context_ref") != predecessor.get("review_packet"):
            errors.append(f"{label}: context must bind the preceding node review packet")
        record_ref = event.get("recovery_record_ref")
        recovery = (_read(root / record_ref["path"], errors)
                    if isinstance(record_ref, dict) and isinstance(record_ref.get("path"), str)
                    and len(errors) == before else {})
        replacements = event.get("replacements")
        if not isinstance(replacements, list) or not replacements:
            errors.append(f"{label}: replacements required")
            continue
        changes: dict[str, str] = {}
        for change in replacements:
            if (not isinstance(change, dict) or not isinstance(change.get("role"), str)
                    or change["role"] not in ROUTES):
                errors.append(f"{label}: valid replacement role required")
                continue
            role = change["role"]
            new_id = change.get("new_agent_instance_id")
            if (role in changes or start <= last_boundary.get(role, -1)
                    or change.get("previous_agent_instance_id") != resolved[NODES[start]].get(role)):
                errors.append(f"{label}: invalid {role} identity chain or boundary")
            if not isinstance(new_id, str) or not new_id or new_id in seen_ids or new_id in changes.values():
                errors.append(f"{label}: replacement must use a distinct new instance")
            if (change.get("model"), change.get("reasoning_effort")) != ROUTES[role]:
                errors.append(f"{label}: {role} recovery route mismatch")
            runtime = control.get("runtime_instances_by_node", {})
            boundary_roles = runtime.get(NODES[start], {}) if isinstance(runtime, dict) else {}
            if not isinstance(boundary_roles, dict) or role not in boundary_roles:
                errors.append(f"{label}: recovered {role} runtime/preload record required")
            registered = recovery.get("replacements", [])
            if not isinstance(registered, list):
                registered = []
            matches = [item for item in registered
                       if isinstance(item, dict) and item.get("role") == role
                       and item.get("new_agent_instance_id") == new_id
                       and isinstance(item.get("previous_instance"), dict)
                       and item["previous_instance"].get("agent_instance_id") == change.get("previous_agent_instance_id")]
            if recovery.get("authorized_by") != "user" or len(matches) != 1:
                errors.append(f"{label}: {role} does not match the bound recovery record")
            changes[role] = new_id
        if len(errors) != before:
            continue
        for role, new_id in changes.items():
            seen_ids.add(new_id)
            last_boundary[role] = start
            for node in NODES[start:]:
                resolved[node][role] = new_id
                activation[node][role] = approved_at
    overrides = control.get("runtime_instances_by_node", {})
    if not isinstance(overrides, dict):
        errors.append("runtime_instances_by_node must be a mapping")
        return resolved, activation
    for node, records in overrides.items():
        if node not in NODES or not isinstance(records, dict):
            errors.append("runtime_instances_by_node requires valid nodes and role mappings")
            continue
        if NODES.index(node) > through_index:
            continue
        for role, record in records.items():
            label = f"runtime_instances_by_node.{node}.{role}"
            if (role not in ROUTES or not isinstance(record, dict)
                    or record.get("agent_instance_id") != resolved[node].get(role)):
                errors.append(f"{label}: instance is not authorized for this node")
                continue
            if (record.get("model"), record.get("reasoning_effort")) != ROUTES[role]:
                errors.append(f"{label}: model/reasoning_effort mismatch")
            preloaded = record.get("preloaded")
            if not isinstance(preloaded, list) or not preloaded:
                errors.append(f"{label}: preloaded inputs required")
                continue
            for item in preloaded:
                _artifact(root, item, f"{label}.preloaded", errors)
            if role != "data" and not any(isinstance(item, dict) and item.get("path") == "problem_statement.md"
                                          for item in preloaded):
                errors.append(f"{label}: problem_statement.md must be preloaded")
    return resolved, activation


def _task_input(root: Path, ref: Any, label: str, reviewed: dict[str, str],
                errors: list[str]) -> None:
    if not isinstance(ref, dict) or not isinstance(ref.get("path"), str):
        errors.append(f"{label}: path/sha256 reference required")
        return
    relative = ref["path"]
    if not relative or Path(relative).is_absolute() or "\\" in relative:
        errors.append(f"{label}: project-relative POSIX path required")
        return
    try:
        path = (root / relative).resolve()
        path.relative_to(root)
    except (OSError, ValueError):
        errors.append(f"{label}: path outside project: {relative}")
        return
    if not path.is_file():
        errors.append(f"{label}: file missing: {relative}")
        return
    declared = ref.get("sha256")
    if not isinstance(declared, str) or not HEX64.fullmatch(declared):
        errors.append(f"{label}: sha256 required: {relative}")
        return
    actual = _digest(path)
    if actual == declared.lower():
        return
    if reviewed.get(relative) == actual:
        return
    errors.append(f"{label}: stale input hash is not rebound by the current node review: {relative}")


def _check_dispatch(root: Path, control: dict[str, Any], ids: dict[str, str],
                    approval_times: dict[str, datetime | date],
                    reviewed_inputs: dict[str, dict[str, str]],
                    phase_approval_times: dict[str, datetime | date],
                    through_index: int, errors: list[str],
                    node_instances: dict[str, dict[str, str]] | None = None,
                    recovery_times: dict[str, dict[str, datetime]] | None = None) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    records = control.get("dispatch_records")
    if not isinstance(records, list):
        errors.append("dispatch_records must be a list")
        return {}, {}
    dispatched: dict[str, set[str]] = {node: set() for node in NODES}
    m4_phases: dict[str, set[str]] = {"figure": set(), "writer": set()}
    task_records: dict[str, list[dict[str, Any]]] = {}
    for index, record in enumerate(records):
        label = f"dispatch_records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label}: mapping required")
            continue
        node, role, task_id = record.get("node_id"), record.get("owner_role"), record.get("task_id")
        if node in NODES and NODES.index(node) > through_index:
            continue
        m4_solver_phase = (
            M4_SOLVER_TASK_PHASES.get(task_id)
            if node == "M4" and role == "solver" else None
        )
        m4_solver_task = m4_solver_phase is not None
        if (not isinstance(node, str) or node not in NODE_ROLES
                or not isinstance(role, str)
                or (role not in NODE_ROLES[node] and not m4_solver_task)):
            errors.append(f"{label}: node/role not permitted")
            continue
        effective_ids = (node_instances or {}).get(node, ids)
        authorized_at = (recovery_times or {}).get(node, {}).get(role)
        dispatch_time = _time(record.get("called_at"))
        if authorized_at is not None and (not isinstance(dispatch_time, datetime) or dispatch_time < authorized_at):
            errors.append(f"{label}: dispatch before instance recovery approval")
        if role != "support" and record.get("agent_instance_id") != effective_ids.get(role):
            errors.append(f"{label}: agent_instance_id mismatch")
        superseded_by = record.get("superseded_by")
        if superseded_by is not None:
            if (not isinstance(task_id, str) or not task_id
                    or not isinstance(superseded_by, str) or not superseded_by
                    or superseded_by == task_id
                    or not isinstance(record.get("superseded_reason"), str)
                    or not record["superseded_reason"].strip()
                    or not isinstance(record.get("task_card"), str)
                    or not isinstance(record.get("task_card_sha256"), str)
                    or not HEX64.fullmatch(record["task_card_sha256"])):
                errors.append(f"{label}: superseded dispatch requires its task identity, card digest, successor, and reason")
                continue
            successors = [item for item in records if isinstance(item, dict)
                          and item.get("task_id") == superseded_by]
            if len(successors) != 1:
                errors.append(f"{label}: superseded dispatch requires exactly one successor record")
                continue
            successor = successors[0]
            prior_time = _time(record.get("called_at"))
            successor_time = _time(successor.get("called_at"))
            if (successor.get("node_id") != node
                    or successor.get("owner_role") != role
                    or successor.get("agent_instance_id") != record.get("agent_instance_id")
                    or prior_time is None or successor_time is None
                    or successor_time <= prior_time):
                errors.append(f"{label}: superseding dispatch must be a later retry by the same node, role, and agent")
            old_card = _artifact(root, {"path": record["task_card"], "sha256": record["task_card_sha256"]},
                                 f"{label}.superseded_task_card", errors)
            if old_card:
                card = _read(old_card[1], errors)
                # Retain a documented incorrect historical route; its successor
                # must still pass the normal accepted-dispatch route checks.
                if any(card.get(key) != record.get(key) for key in
                               ("task_id", "node_id", "owner_role", "agent_instance_id", "model", "reasoning_effort")):
                    errors.append(f"{label}: superseded task identity/model mismatch")
            continue
        if not isinstance(task_id, str) or not task_id:
            errors.append(f"{label}: task_id required")
        else:
            previous = task_records.setdefault(task_id, [])
            if previous:
                group = [*previous, record]

                def signature(item: dict[str, Any]) -> tuple[Any, ...]:
                    return tuple(item.get(key) for key in (
                        "node_id", "owner_role", "agent_instance_id", "model",
                        "reasoning_effort", "task_card", "task_card_sha256",
                        "dispatch_kind", "parent_solver_instance_id",
                    ))

                submissions = [item.get("submission_id") for item in group]
                if (any(signature(item) != signature(group[0]) for item in group)
                        or any(not isinstance(value, str) or not value for value in submissions)
                        or len(set(submissions)) != len(submissions)):
                    errors.append(f"{label}: repeated task_id requires an identical task card and unique submission_id values")
            previous.append(record)
        dispatched[node].add(role)
        if role == "support":
            model, effort = "gpt-6-luna", "max"
            support_id = record.get("agent_instance_id")
            if not isinstance(support_id, str) or not support_id or support_id in effective_ids.values():
                errors.append(f"{label}: support requires a distinct agent_instance_id")
            if record.get("dispatch_kind") != "conditional_support" or record.get("parent_solver_instance_id") != effective_ids.get("solver"):
                errors.append(f"{label}: conditional support must bind the sole solver")
        else:
            model, effort = ROUTES[role]
        if (record.get("model"), record.get("reasoning_effort")) != (model, effort):
            errors.append(f"{label}: model/reasoning_effort mismatch")
        called_at = _time(record.get("called_at"))
        if called_at is None:
            errors.append(f"{label}: called_at must be timezone-aware ISO-8601")
        predecessor = NODES[NODES.index(node) - 1] if node != "M1" else None
        if predecessor and called_at is not None:
            approved_at = approval_times.get(predecessor)
            before_approval = (
                approved_at is None
                or (called_at < approved_at if isinstance(approved_at, datetime)
                    else called_at.date() < approved_at)
            )
            if before_approval:
                errors.append(f"{label}: dispatch before {predecessor} approval")
        ref = {"path": record.get("task_card"), "sha256": record.get("task_card_sha256")}
        found = _artifact(root, ref, f"{label}.task_card", errors)
        if not found:
            continue
        card = _read(found[1], errors)
        for key, expected in (
            ("node_id", node), ("owner_role", role), ("task_id", task_id),
            ("agent_instance_id", record.get("agent_instance_id") if role == "support" else effective_ids.get(role)),
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
        if m4_solver_task:
            scope = card.get("scope")
            if not isinstance(scope, dict) or scope.get("phase") != m4_solver_phase:
                errors.append(f"{label}: M4 solver dispatch phase must be {m4_solver_phase}")
        if role == "support":
            if card.get("dispatch_kind") != "conditional_support" or card.get("parent_solver_instance_id") != effective_ids.get("solver"):
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
        if not _has_task_card_prohibitions(card):
            errors.append(f"{label}: task card prohibited_actions required")
        inputs = card.get("inputs")
        if not isinstance(inputs, list) or not inputs:
            errors.append(f"{label}: task card inputs required")
        else:
            reviewed: dict[str, str] = {}
            for reviewed_node in NODES[:NODES.index(node) + 1]:
                reviewed.update(reviewed_inputs.get(reviewed_node, {}))
            if node == "M3":
                reviewed.update(reviewed_inputs.get("M4", {}))
            for input_index, item in enumerate(inputs):
                _task_input(root, item, f"{label}.inputs[{input_index}]",
                            reviewed, errors)
        if node == "M4" and role in m4_phases:
            scope = card.get("scope")
            phase = scope.get("phase") if isinstance(scope, dict) else None
            if control.get("nodes", {}).get("M4", {}).get("visual_workflow") == "chapter_parallel":
                allowed = {"plan", "generate"} if role == "figure" else {"plan", "draft", "figure_prompt", "abstract_framework", "write"}
                if phase not in allowed:
                    errors.append(f"{label}: M4 {role} scope.phase must be one of {sorted(allowed)}")
                else:
                    m4_phases[role].add(phase)
                # The chapter branch checks scoped inputs, approvals and actual
                # retry history after native identity and artifact validation.
                continue
            if (role == "figure" and task_id == "MC25A-M4-H7-FIGURES-001"
                    and phase == "h7_visual_argument_and_data_figures"):
                phase = "plan"
            allowed = {"plan", "generate"} if role == "figure" else {"plan", "write", "abstract_framework"}
            writer_first = control.get("nodes", {}).get("M4", {}).get("visual_workflow") == "writer_first_batches"
            if writer_first and role == "writer":
                allowed.add("draft")
            if phase not in allowed:
                errors.append(f"{label}: M4 {role} scope.phase must be one of {sorted(allowed)}")
                continue
            m4_phases[role].add(phase)
            if role == "writer" and phase in {"write", "draft"}:
                batch_id = scope.get("batch_id")
                batch = next((item for item in control.get("nodes", {}).get("M4", {}).get("writing_batches", [])
                              if isinstance(item, dict) and item.get("batch_id") == batch_id), None)
                chapter_ids = scope.get("chapter_ids")
                if (not isinstance(batch_id, str) or not isinstance(batch, dict)
                        or not isinstance(chapter_ids, list)
                        or chapter_ids != batch.get("chapter_ids")):
                    errors.append(f"{label}: writer write task must match one approved writing batch")
            gate = None
            required_inputs: list[str] = []
            m4 = control.get("nodes", {}).get("M4", {})
            def path_of(field: str) -> str | None:
                value = m4.get(field) if isinstance(m4, dict) else None
                return value.get("path") if isinstance(value, dict) else None
            if phase == "generate":
                gate = "M4_VISUAL_PLAN"
                required_inputs = [path_of("visual_argument_plan")]
                if writer_first:
                    batch_id = scope.get("batch_id")
                    batch = next((b for b in m4.get("writing_batches", [])
                                  if isinstance(b, dict) and b.get("batch_id") == batch_id), {})
                    gate = f"M4_VISUAL_PLAN:{batch_id}"
                    required_inputs = [batch.get(key, {}).get("path") for key in ("draft", "visual_argument_plan")
                                       if isinstance(batch.get(key), dict)]
                    if len(required_inputs) != 2:
                        errors.append(f"{label}: generation must bind the writer draft and batch visual plan")
            elif phase in {"write", "draft"}:
                batch_id = scope.get("batch_id")
                gate = "M4_ABSTRACT_FRAMEWORK" if batch_id == "B4" else "M4_WRITING_PLAN"
                required_inputs = [path_of(field) for field in (
                    "paper_argument_blueprint", "paper_language_profile",
                    "paper_material_readiness", "paper_claim_coverage")]
                batches = m4.get("writing_batches", []) if isinstance(m4, dict) else []
                current_index = next((index for index, item in enumerate(batches)
                                      if isinstance(item, dict) and item.get("batch_id") == batch_id), None) \
                    if isinstance(batches, list) else None
                if current_index is not None:
                    for item in batches[:current_index]:
                        manuscript = item.get("manuscript") if isinstance(item, dict) else None
                        if isinstance(manuscript, dict):
                            required_inputs.append(manuscript.get("path"))
                if batch_id == "B4":
                    required_inputs.append(path_of("abstract_framework"))
                if writer_first and phase == "write":
                    batch = next((b for b in batches if isinstance(b, dict) and b.get("batch_id") == batch_id), {})
                    required_inputs.extend(batch.get(key, {}).get("path") for key in ("draft", "visual_argument_plan")
                                           if isinstance(batch.get(key), dict))
                    selection = batch.get("figure_selection")
                    if isinstance(selection, dict):
                        gate = f"M4_FIGURE_SELECTION:{batch_id}"
                        required_inputs.append(selection.get("path"))
            elif phase == "abstract_framework":
                gate = "M4_WRITING_BATCH:B3"
                required_inputs = [path_of("paper_argument_blueprint"), path_of("paper_language_profile")]
                batches = m4.get("writing_batches", []) if isinstance(m4, dict) else []
                for item in batches[:3] if isinstance(batches, list) else []:
                    manuscript = item.get("manuscript") if isinstance(item, dict) else None
                    if isinstance(manuscript, dict):
                        required_inputs.append(manuscript.get("path"))
            if gate:
                gate_time = phase_approval_times.get(gate)
                before_gate = (
                    called_at is None or gate_time is None
                    or (called_at <= gate_time if isinstance(gate_time, datetime)
                        else called_at.date() < gate_time)
                )
                if before_gate:
                    errors.append(f"{label}: {phase} dispatched before {gate} approval")
                input_paths = {item.get("path") for item in inputs if isinstance(item, dict)} if isinstance(inputs, list) else set()
                if not all(path is not None and path in input_paths for path in required_inputs):
                    errors.append(f"{label}: {phase} task card omits current approved inputs")
    return dispatched, m4_phases


def _gate_was_satisfied_before(called_at: datetime, gate_time: datetime | date | None,
                               strict: bool = True) -> bool:
    if gate_time is None:
        return False
    if isinstance(gate_time, datetime):
        return called_at > gate_time if strict else called_at >= gate_time
    return called_at.date() >= gate_time


def _check_writing_batch_sequence(root: Path, control: dict[str, Any], log: dict[str, Any],
                                  phase_approval_times: dict[str, datetime | date],
                                  errors: list[str], pauses: list[str]) -> None:
    m4 = control.get("nodes", {}).get("M4", {})
    if not isinstance(m4, dict) or not m4.get("writing_started"):
        return
    batches = m4.get("writing_batches")
    if not isinstance(batches, list) or len(batches) != 4:
        errors.append("M4: exactly four writing batches are required")
        batches = batches if isinstance(batches, list) else []
    blueprint_ref = _artifact(root, m4.get("paper_argument_blueprint"),
                              "M4.paper_argument_blueprint", errors)
    blueprint_batches = []
    if blueprint_ref:
        blueprint = _read(blueprint_ref[1], errors)
        blueprint_batches = blueprint.get("writing_batches", [])
        if not isinstance(blueprint_batches, list) or len(blueprint_batches) != 4:
            errors.append("M4: paper_argument_blueprint must define exactly four writing batches")
            blueprint_batches = blueprint_batches if isinstance(blueprint_batches, list) else []
    expected_batch_ids = [f"B{index}" for index in range(1, 5)]
    if [item.get("batch_id") for item in blueprint_batches if isinstance(item, dict)] != expected_batch_ids:
        errors.append("M4: blueprint writing_batches must be ordered B1 through B4")
    if [item.get("batch_id") for item in batches if isinstance(item, dict)] != expected_batch_ids:
        errors.append("M4: control writing_batches must be ordered B1 through B4")

    readiness_found = _artifact(root, m4.get("paper_material_readiness"),
                                 "M4.paper_material_readiness", errors)
    readiness = _read(readiness_found[1], errors) if readiness_found else {}
    readiness_chapters = readiness.get("chapters", [])
    declared_chapters = {
        item.get("chapter_id") for item in readiness_chapters
        if isinstance(item, dict) and isinstance(item.get("chapter_id"), str)
    } if isinstance(readiness_chapters, list) else set()
    assigned_chapters: list[str] = []
    for index, batch in enumerate(batches):
        if not isinstance(batch, dict):
            errors.append(f"M4.writing_batches[{index}]: mapping required")
            continue
        batch_id = batch.get("batch_id")
        if index >= len(expected_batch_ids) or batch_id != expected_batch_ids[index]:
            errors.append(f"M4.writing_batches[{index}]: batch_id must follow B1 through B4")
        chapters = batch.get("chapter_ids")
        if not isinstance(chapters, list) or not chapters or any(not isinstance(item, str) for item in chapters):
            errors.append(f"M4.{batch_id}: nonempty chapter_ids required")
            chapters = []
        assigned_chapters.extend(chapters)
        if index < len(blueprint_batches):
            blueprint_batch = blueprint_batches[index]
            if not isinstance(blueprint_batch, dict) or blueprint_batch.get("chapter_ids") != chapters:
                errors.append(f"M4.{batch_id}: control chapter_ids must match the approved blueprint")
        manuscript = _artifact(root, batch.get("manuscript"), f"M4.{batch_id}.manuscript", errors)
        if manuscript:
            gate = f"M4_WRITING_BATCH:{batch_id}"
            approved_at, _ = _review(root, control, log, gate, batch.get("review_packet"),
                                     [manuscript], errors, pauses)
            if approved_at is not None:
                phase_approval_times[gate] = approved_at
        packet_ref = batch.get("review_packet")
        packet_file = _artifact(root, packet_ref, f"M4.{batch_id}.review_packet", errors)
        if packet_file:
            packet = _read(packet_file[1], errors)
            if packet.get("review_type") != "paper_batch_review" or packet.get("reviewer_skill") != "论文辅助":
                errors.append(f"M4.{batch_id}: review packet must record the read-only 论文辅助 batch review")
            checks = packet.get("checks")
            statuses = {
                item.get("id", item.get("name")): item.get("status")
                for item in checks if isinstance(item, dict)
            } if isinstance(checks, list) else {}
            required_checks = {
                "language_profile_terms", "first_use_symbol_definitions",
                "claim_evidence_coverage", "metadiscourse", "negative_echo",
            }
            if batch_id == "B4":
                required_checks.update({"abstract_contract", "whole_paper_final"})
            missing = sorted(name for name in required_checks if statuses.get(name) != "PASS")
            if missing:
                errors.append(f"M4.{batch_id}: 论文辅助 batch review missing PASS checks: {missing}")
    if len(assigned_chapters) != len(set(assigned_chapters)):
        errors.append("M4: a chapter may belong to only one writing batch")
    if declared_chapters and set(assigned_chapters) != declared_chapters:
        errors.append("M4: writing batches must cover every paper-material chapter exactly once")

    abstract_ref = _artifact(root, m4.get("abstract_framework"), "M4.abstract_framework", errors)
    if abstract_ref:
        abstract_packet_ref = m4.get("abstract_framework_review_packet")
        abstract_packet = _artifact(root, abstract_packet_ref,
                                    "M4.abstract_framework_review_packet", errors)
        if abstract_packet:
            packet = _read(abstract_packet[1], errors)
            if packet.get("review_type") != "abstract_framework_review":
                errors.append("M4: abstract framework must have a separate abstract_framework_review packet")
        abstract_time, _ = _review(
            root, control, log, "M4_ABSTRACT_FRAMEWORK",
            abstract_packet_ref, [abstract_ref], errors, pauses,
        )
        if abstract_time is not None:
            phase_approval_times["M4_ABSTRACT_FRAMEWORK"] = abstract_time

    records = control.get("dispatch_records", [])
    if not isinstance(records, list):
        return
    writes: dict[str, list[datetime]] = {}
    abstract_dispatches: list[datetime] = []
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
        if not isinstance(scope, dict):
            continue
        called_at = _time(record.get("called_at"))
        if called_at is None:
            continue
        if scope.get("phase") == "abstract_framework":
            abstract_dispatches.append(called_at)
        elif scope.get("phase") == "write" and isinstance(scope.get("batch_id"), str):
            writes.setdefault(scope["batch_id"], []).append(called_at)
    if set(writes) != set(expected_batch_ids):
        errors.append("M4: writer dispatches must cover exactly B1, B2, B3 and B4")
    if any(len(writes.get(batch_id, [])) != 1 for batch_id in expected_batch_ids):
        errors.append("M4: exactly one writer dispatch is required per batch")
    if len(abstract_dispatches) != 1:
        errors.append("M4: exactly one separate abstract-framework dispatch is required after B3")

    previous_gate: datetime | date | None = phase_approval_times.get("M4_WRITING_PLAN")
    for index, batch_id in enumerate(expected_batch_ids):
        times = writes.get(batch_id, [])
        if len(times) != 1:
            continue
        if index == 3:
            previous_gate = phase_approval_times.get("M4_ABSTRACT_FRAMEWORK")
        elif index > 0:
            previous_gate = phase_approval_times.get(f"M4_WRITING_BATCH:B{index}")
        if not _gate_was_satisfied_before(times[0], previous_gate):
            gate_name = "M4_ABSTRACT_FRAMEWORK" if index == 3 else (
                f"M4_WRITING_BATCH:B{index}" if index > 0 else "M4_WRITING_PLAN")
            errors.append(f"M4.{batch_id}: writer dispatched before {gate_name} approval")
        own_approval = phase_approval_times.get(f"M4_WRITING_BATCH:{batch_id}")
        if isinstance(own_approval, datetime) and own_approval <= times[0]:
            errors.append(f"M4.{batch_id}: batch approval must follow its writer dispatch")
    batch3_approval = phase_approval_times.get("M4_WRITING_BATCH:B3")
    if len(abstract_dispatches) == 1 and not _gate_was_satisfied_before(abstract_dispatches[0], batch3_approval):
        errors.append("M4: abstract framework dispatched before B3 approval")
    abstract_approval = phase_approval_times.get("M4_ABSTRACT_FRAMEWORK")
    if (len(abstract_dispatches) == 1 and isinstance(abstract_approval, datetime)
            and abstract_approval <= abstract_dispatches[0]):
        errors.append("M4: abstract framework approval must follow its separate author discussion")
    if any(isinstance(item, dict) and str(item.get("gate", "")).startswith("M4_CHAPTER:")
           for item in log.get("approvals", [])):
        errors.append("M4: chapter-level approval is not permitted; use four writing-batch approvals")


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
    if node_id == "M4" and node.get("visual_workflow") != "chapter_parallel":
        paper_reviews = sum(
            isinstance(call, dict) and call.get("skill") == "论文辅助"
            for call in calls
        )
        if paper_reviews != 4:
            errors.append("M4: 论文辅助 must complete one read-only review for each of the four writing batches")
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


def _review(root: Path, control: dict[str, Any], log: dict[str, Any], gate: str,
            packet_ref: Any, extra_refs: list[tuple[str, Path]],
            errors: list[str], pauses: list[str],
            rebindings: dict[str, str] | None = None) -> tuple[datetime | date | None, dict[str, str]]:
    found = _artifact(root, packet_ref, f"{gate}.review_packet", errors)
    if not found:
        return None, {}
    packet = _read(found[1], errors)
    if packet.get("node_id") != gate.split(":", 1)[0].split("_", 1)[0]:
        errors.append(f"{gate}: review packet node_id mismatch")
    native_visual_review = (
        gate == "M4_VISUAL_PLAN"
        and packet.get("review_type") == "plan_scope_and_evidence_preflight"
    )
    if native_visual_review:
        m4 = control.get("nodes", {}).get("M4", {})
        plan_ref = m4.get("visual_argument_plan") if isinstance(m4, dict) else None
        plan = _artifact(root, plan_ref, f"{gate}.visual_argument_plan", errors, rebindings)
        plan_digest = packet.get("plan_digest")
        input_gate = packet.get("input_hash_gate")
        if (packet.get("status") != "PASS" or not plan
                or packet.get("plan_path") != (plan_ref.get("path") if isinstance(plan_ref, dict) else None)
                or not isinstance(plan_digest, dict)
                or plan_digest.get("sha256") != (_digest(plan[1]) if plan else None)
                or not isinstance(input_gate, dict)
                or input_gate.get("status") != "PASS"
                or input_gate.get("mismatches") != 0
                or input_gate.get("matched_inputs") != input_gate.get("declared_inputs")):
            errors.append(f"{gate}: native visual review must PASS with current plan and input hashes")
        checks = packet.get("checks")
        statuses: dict[str, str] = {}
        if not isinstance(checks, list):
            errors.append(f"{gate}: native visual review checks must be a list")
            checks = []
        for item in checks:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                if item["id"] in statuses:
                    errors.append(f"{gate}: duplicate native review check {item['id']}")
                statuses[item["id"]] = item.get("status")
        valid_statuses = {
            name: {"PASS", "PASS_WITH_SCOPE_BOUNDARY"} if name == "model_fact_scope" else {"PASS"}
            for name in M4_VISUAL_PLAN_CHECKS
        }
        if (set(statuses) != M4_VISUAL_PLAN_CHECKS
                or any(status not in valid_statuses.get(name, set())
                       for name, status in statuses.items())):
            errors.append(f"{gate}: all required native visual-plan checks must PASS")
        artifacts = [plan_ref] if isinstance(plan_ref, dict) else []
    else:
        artifacts = packet.get("important_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append(f"{gate}: important_artifacts required")
        artifacts = []
    checked = [found]
    for index, item in enumerate(artifacts):
        item_label = "visual_argument_plan" if native_visual_review else f"important_artifacts[{index}]"
        ref = _artifact(root, item, f"{gate}.{item_label}", errors, rebindings)
        if ref:
            checked.append(ref)
    if extra_refs and not set(path for path, _ in extra_refs).issubset({path for path, _ in checked}):
        errors.append(f"{gate}: review packet omits required artifacts")
    if not native_visual_review:
        _named_pass_checks(root, packet.get("checks"), set(), gate, errors, rebindings)
    reviewed = {relative: _digest(path) for relative, path in checked}
    return _approval(root, control, log, gate, checked, errors, pauses), reviewed


def _h6_material_rebindings(root: Path, control: dict[str, Any], ids: dict[str, str],
                            errors: list[str], pauses: list[str]) -> dict[str, str]:
    nodes = control.get("nodes")
    m4 = nodes.get("M4") if isinstance(nodes, dict) else None
    review_ref = m4.get("material_readiness_review_packet") if isinstance(m4, dict) else None
    if review_ref is None:
        pauses.append("M4: independent H6 material-readiness review not ready")
        return {}
    local_errors: list[str] = []
    report_file = _artifact(root, review_ref, "M4.material_readiness_review_packet", local_errors)
    if not report_file:
        errors.extend(local_errors)
        return {}
    report = _read(report_file[1], local_errors)
    if (report.get("status") != "PASS"
            or report.get("material_readiness") != "PASS"
            or report.get("node_id") != "M4"
            or report.get("verification_agent_instance_id") != ids.get("verifier")):
        pauses.append("M4: independent H6 material-readiness review requires verifier PASS")
        return {}
    card_ref = m4.get("task_card")
    declared_card = report.get("task_card")
    if (not isinstance(card_ref, dict) or not isinstance(declared_card, dict)
            or declared_card.get("path") != card_ref.get("path")
            or declared_card.get("sha256") != card_ref.get("sha256")):
        local_errors.append("M4.material_readiness_review_packet: task-card binding mismatch")
    card_file = _artifact(root, card_ref, "M4.material_readiness_task_card", local_errors)
    if card_file:
        card = _read(card_file[1], local_errors)
        if (card.get("task_id") != report.get("task_id")
                or card.get("agent_instance_id") != ids.get("verifier")):
            local_errors.append("M4.material_readiness_review_packet: task identity mismatch")
        inputs = card.get("inputs")
        if not isinstance(inputs, list) or not inputs:
            local_errors.append("M4.material_readiness_task_card: inputs required")
        else:
            for index, item in enumerate(inputs):
                _artifact(root, item, f"M4.material_readiness_task_card.inputs[{index}]", local_errors)
    input_gate = report.get("input_hash_gate")
    if (not isinstance(input_gate, dict) or input_gate.get("status") != "PASS"
            or input_gate.get("mismatches") != 0
            or input_gate.get("matched_inputs") != input_gate.get("declared_inputs")
            or not card_file
            or input_gate.get("declared_inputs") != len(card.get("inputs", []))):
        local_errors.append("M4.material_readiness_review_packet: complete input hash gate required")
    artifacts = report.get("important_artifacts")
    required_paths = {
        "paper_material_readiness.yaml", "paper_claim_coverage.yaml",
        "paper_argument_blueprint.yaml", "evidence_gap_matrix.yaml",
    }
    if not isinstance(artifacts, list) or not artifacts:
        local_errors.append("M4.material_readiness_review_packet: important_artifacts required")
        artifacts = []
    rebound: dict[str, str] = {report_file[0]: _digest(report_file[1])}
    seen: set[str] = set()
    for index, item in enumerate(artifacts):
        ref = _artifact(root, item, f"M4.material_readiness_review_packet.important_artifacts[{index}]", local_errors)
        if ref:
            seen.add(ref[0])
            rebound[ref[0]] = _digest(ref[1])
    if not required_paths.issubset(seen):
        local_errors.append("M4.material_readiness_review_packet: readiness, claims, blueprint and gap hashes required")
    _named_pass_checks(root, report.get("checks"), set(),
                       "M4.material_readiness_review_packet", local_errors)
    if local_errors:
        errors.extend(local_errors)
        return {}
    return rebound


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
                errors.append("M2: literature sources must be verified and nonempty")
            else:
                authorization_date = sources.get("user_authorization_date")
                try:
                    date.fromisoformat(authorization_date)
                    assistant_search_authorized = (
                        sources.get("search_owner") == "assistant"
                        and sources.get("acquisition_mode") == "assistant_search_user_authorized"
                    )
                except (TypeError, ValueError):
                    assistant_search_authorized = False
                covered: set[str] = set()
                seen: set[str] = set()
                for index, item in enumerate(entries):
                    label = f"M2.literature_sources[{index}]"
                    if not isinstance(item, dict):
                        errors.append(f"{label}: source mapping required")
                        continue
                    key = item.get("citation_key")
                    questions = item.get("subproblems", item.get("covered_subproblems"))
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
                    authorized_origin = (
                        assistant_search_authorized
                        and item.get("user_supplied") is False
                        and item.get("source_origin") == "assistant_search_under_explicit_user_authorization"
                    )
                    if (item.get("user_supplied") is not True and not authorized_origin) or not all(
                        item.get(field) for field in ("locator", "use")
                    ):
                        errors.append(f"{label}: authorized source origin, locator and actual use required")
                    _artifact(root, item.get("summary_ref"), f"{label}.summary_ref", errors)
                if covered != set(subproblems):
                    errors.append("M2: literature use must cover every subproblem")
    elif node_id == "M3":
        if "run_manifest" in refs:
            manifest = _read(refs["run_manifest"][1], errors)
            if manifest.get("solver_instance_id") != ids.get("solver") or not isinstance(manifest.get("seed"), int):
                errors.append("M3: run_manifest solver_instance_id/seed invalid")
            command = manifest.get("command")
            valid_command = (
                isinstance(command, str) and bool(command.strip())
            ) or (
                isinstance(command, list) and bool(command)
                and all(isinstance(item, str) and item.strip() for item in command)
            )
            if not valid_command:
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


def _visual_ref(item: Any) -> dict[str, str] | None:
    if isinstance(item, dict):
        return item
    if not isinstance(item, str):
        return None
    match = re.fullmatch(r"(.+?)#sha256=([0-9a-fA-F]{64})(?:#.*)?", item)
    return {"path": match.group(1), "sha256": match.group(2)} if match else None


def _modern_visual_slots(plan: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    legacy_slots = plan.get("slots")
    if isinstance(legacy_slots, list):
        return legacy_slots, False
    slots: list[dict[str, Any]] = []
    global_slots = plan.get("global_visual_slots")
    subproblems = plan.get("subproblems")
    if not isinstance(global_slots, list) or not isinstance(subproblems, list):
        return slots, True
    for slot in global_slots:
        if not isinstance(slot, dict):
            continue
        representation = slot.get("representation")
        mode = representation.get("mode") if isinstance(representation, dict) else None
        if mode in {"figure", "table"}:
            slots.append({**slot, "representation": mode})
    for subproblem in subproblems:
        audits = subproblem.get("visual_audit") if isinstance(subproblem, dict) else None
        if not isinstance(audits, list):
            continue
        for slot in audits:
            if not isinstance(slot, dict):
                continue
            representation = slot.get("representation")
            mode = representation.get("mode") if isinstance(representation, dict) else None
            if mode not in {"figure", "table"}:
                continue
            intent = slot.get("figure_intent")
            intent = intent if isinstance(intent, dict) else {}
            slots.append({
                **slot,
                "representation": mode,
                "generation_route": intent.get("generation_route"),
                "template_id": intent.get("template_id"),
            })
    return slots, True


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
    slots, modern_plan = _modern_visual_slots(plan)
    figures = registry.get("figures")
    if not isinstance(slots, list) or not isinstance(figures, list):
        errors.append("M4: visual plan slots and figure_registry.figures must be lists")
        return 0
    planned: dict[str, tuple[str, str | None]] = {}
    planned_tables: set[str] = set()
    for index, slot in enumerate(slots):
        if not isinstance(slot, dict) or not isinstance(slot.get("slot_id"), str) or not slot["slot_id"]:
            errors.append(f"M4.visual.slots[{index}]: slot_id required")
            continue
        slot_id = slot["slot_id"]
        representation = slot.get("representation")
        if representation not in {"figure", "table", "text"}:
            errors.append(f"M4.visual.slots[{index}]: representation invalid")
        if slot_id in planned or slot_id in planned_tables:
            errors.append(f"M4: duplicate visual slot {slot_id}")
        if representation == "figure":
            route = slot.get("generation_route")
            if route not in {"modelviz", "tikz-scientific-figures"}:
                errors.append(f"M4.visual.slots[{index}]: generation_route invalid")
            else:
                template_id = slot.get("template_id")
                if route == "tikz-scientific-figures":
                    entry = catalog_routes.get(template_id)
                    if not entry or entry.get("generation_route") != route:
                        errors.append(f"M4.visual.slots[{index}]: template_id/route mismatch")
                planned[slot_id] = (route, template_id)
        elif representation == "table":
            planned_tables.add(slot_id)
        evidence = slot.get("evidence_refs")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"M4.visual.slots[{index}]: evidence_refs required")
        else:
            for ref_index, item in enumerate(evidence):
                ref = _visual_ref(item)
                if ref is None:
                    errors.append(f"M4.visual.slots[{index}].evidence[{ref_index}]: path and SHA-256 required")
                else:
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
        if figure.get("generator") != route or figure.get("generation_route", figure.get("generator")) != route:
            errors.append(f"M4: generator mismatch for {slot_id}")
        if figure.get("template_id") != template_id:
            errors.append(f"M4: template mismatch for {slot_id}")
        if route == "tikz-scientific-figures":
            entry = catalog_routes.get(template_id)
            if not entry or figure.get("template_sha256") != entry.get("template_sha256"):
                errors.append(f"M4: template provenance mismatch for {slot_id}")
            if figure.get("kind") not in {"flowchart", "schematic"}:
                errors.append(f"M4: TikZ kind must be flowchart or schematic for {slot_id}")
        formats = figure.get("formats")
        insertion_format = figure.get("insertion_format", registry.get("insertion_format"))
        if not isinstance(formats, list) or not all(isinstance(item, str) for item in formats) or set(formats) != {"svg", "png"} or insertion_format != "svg":
            errors.append(f"M4: SVG+PNG outputs and SVG insertion required for {slot_id}")
        qa = figure.get("visual_qa")
        qa_report = None
        if isinstance(qa, dict):
            if qa.get("status") != "passed":
                errors.append(f"M4: visual QA required for {slot_id}")
            qa_report = qa.get("report")
        elif qa != "passed" or figure.get("qa_status") != "reviewed":
            errors.append(f"M4: visual QA required for {slot_id}")
        if not figure.get("caption"):
            errors.append(f"M4: caption required for {slot_id}")
        source_files = figure.get("source_files")
        if not source_files and modern_plan:
            source_files = [figure.get("editable_source"), figure.get("data_source")]
        if not isinstance(source_files, list) or not source_files:
            errors.append(f"M4: source_files required for {slot_id}")
        else:
            for source_index, source in enumerate(source_files):
                if isinstance(source, dict):
                    _artifact(root, source, f"M4.figures[{index}].source_files[{source_index}]", errors)
                elif isinstance(source, str):
                    if not (root / source).is_file():
                        errors.append(f"M4: figure source missing for {slot_id}: {source}")
                else:
                    errors.append(f"M4: figure source reference invalid for {slot_id}")
        if qa_report is not None:
            report_path = root / qa_report if isinstance(qa_report, str) else None
            if report_path is None or not report_path.is_file():
                errors.append(f"M4: visual QA report missing for {slot_id}")
            elif _read(report_path, errors).get("status") != "PASS":
                errors.append(f"M4: visual QA report must PASS for {slot_id}")
        for extension in ("svg", "png"):
            outputs = figure.get("outputs")
            output = outputs.get(extension) if isinstance(outputs, dict) else None
            ref = output if isinstance(output, dict) else {
                "path": figure.get(extension), "sha256": figure.get(f"{extension}_sha256")}
            _artifact(root, ref, f"M4.figures[{index}].{extension}", errors)
        if route == "modelviz" and not modern_plan:
            if figure.get("decision_author") != "scipilot-figure-skill" or figure.get("semantic_qa") != "scipilot-figure-skill":
                errors.append(f"M4: SciPilot decision and QA required for {slot_id}")
            _artifact(root, {"path": figure.get("decision_card"),
                             "sha256": figure.get("decision_card_sha256")},
                      f"M4.figures[{index}].decision_card", errors)
        elif route == "tikz-scientific-figures":
            starter = _artifact(root, {"path": figure.get("starter_source"),
                                       "sha256": figure.get("starter_sha256")},
                                f"M4.figures[{index}].starter_source", errors)
            if starter and starter[0].split(".")[-1] != "tex":
                errors.append(f"M4: starter source type mismatch for {slot_id}")
            if starter and entry and starter[1] and figure.get("starter_sha256") != entry.get("template_sha256"):
                errors.append(f"M4: starter/catalog hash mismatch for {slot_id}")
            script = _artifact(root, {"path": figure.get("script"),
                                      "sha256": figure.get("script_sha256")},
                               f"M4.figures[{index}].script", errors)
            if script and script[0].split(".")[-1] != "tex":
                errors.append(f"M4: script source type mismatch for {slot_id}")
        if modern_plan:
            sources = figure.get("evidence_sources")
            if not isinstance(sources, list) or not sources:
                errors.append(f"M4: evidence_sources required for {slot_id}")
            else:
                for source_index, source in enumerate(sources):
                    _artifact(root, source, f"M4.figures[{index}].evidence_sources[{source_index}]", errors)
    if set(planned) != actual:
        errors.append(f"M4: visual slots not closed: {sorted(set(planned) - actual)}")
    tables = registry.get("tables", [])
    if not isinstance(tables, list):
        errors.append("M4: figure_registry.tables must be a list")
        tables = []
    actual_tables: set[str] = set()
    for index, table in enumerate(tables):
        if not isinstance(table, dict):
            errors.append(f"M4.figure_registry.tables[{index}]: mapping required")
            continue
        slot_ids = table.get("visual_slot_ids")
        if not isinstance(slot_ids, list) or len(slot_ids) != 1 or slot_ids[0] not in planned_tables:
            if modern_plan and planned_tables:
                errors.append(f"M4.figure_registry.tables[{index}]: one approved table slot required")
            continue
        if slot_ids[0] in actual_tables:
            errors.append(f"M4: visual table slot realized twice: {slot_ids[0]}")
        actual_tables.add(slot_ids[0])
        _artifact(root, {"path": table.get("path"), "sha256": table.get("sha256")},
                  f"M4.tables[{index}]", errors)
        qa = table.get("qa")
        if modern_plan:
            if not isinstance(qa, dict) or qa.get("status") != "PASS":
                errors.append(f"M4: table QA required for {slot_ids[0]}")
            elif isinstance(qa.get("report"), str) and not (root / qa["report"]).is_file():
                errors.append(f"M4: table QA report missing for {slot_ids[0]}")
    if modern_plan and planned_tables != actual_tables:
        errors.append(f"M4: visual table slots not closed: {sorted(planned_tables - actual_tables)}")
    return len(planned)


def _writing_preflight(root: Path, control: dict[str, Any], log: dict[str, Any],
                       ids: dict[str, str], subproblems: list[str],
                       errors: list[str], pauses: list[str],
                       phase_approval_times: dict[str, datetime | date],
                       reviewed_inputs: dict[str, dict[str, str]], draft_only: bool = False) -> int:
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
    writer_first = m4.get("visual_workflow") in {"writer_first_batches", "chapter_parallel"}
    for field, gate, packet_field in (() if writer_first else (
        ("visual_argument_plan", "M4_VISUAL_PLAN", "visual_plan_review_packet"),
    )):
        found = required(field)
        if found:
            if m4.get(packet_field) is None:
                pauses.append(f"{gate}: review packet not ready")
            else:
                gate_time, reviewed = _review(root, control, log, gate, m4.get(packet_field),
                                              [found], errors, pauses)
                reviewed_inputs.setdefault("M4", {}).update(reviewed)
                if gate_time is not None:
                    phase_approval_times[gate] = gate_time
    blueprint_ref = required("paper_argument_blueprint")
    language_profile_ref = required("paper_language_profile")
    if blueprint_ref and language_profile_ref:
        packet_ref = m4.get("writing_plan_review_packet")
        if packet_ref is None:
            pauses.append("M4_WRITING_PLAN: review packet not ready")
        else:
            gate_time, reviewed = _review(
                root, control, log, "M4_WRITING_PLAN", packet_ref,
                [blueprint_ref, language_profile_ref], errors, pauses,
            )
            reviewed_inputs.setdefault("M4", {}).update(reviewed)
            if gate_time is not None:
                phase_approval_times["M4_WRITING_PLAN"] = gate_time
    plan_ref = m4.get("visual_argument_plan")
    registry_ref = None if draft_only else required("figure_registry")
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
        blueprint_ref = _artifact(root, m4.get("paper_argument_blueprint"),
                                  "M4.paper_argument_blueprint", errors)
        blueprint = _read(blueprint_ref[1], errors) if blueprint_ref else {}
        language_profile_ref = _artifact(root, m4.get("paper_language_profile"),
                                         "M4.paper_language_profile", errors)
        if language_profile_ref:
            language_profile = _read(language_profile_ref[1], errors)
            if language_profile.get("scope") != "ordinary_prose_only" or not isinstance(language_profile.get("term_rules"), list):
                errors.append("M4: paper_language_profile must define ordinary_prose_only scope and a term_rules list")
            if (language_profile.get("status") != "approved"
                    or language_profile.get("approval_gate") != "M4_WRITING_PLAN"):
                pauses.append("M4: paper_language_profile requires user approval with M4_WRITING_PLAN")
            targets = language_profile.get("review_targets")
            if not isinstance(targets, list) or not {"题目", "题干"}.issubset(set(targets)):
                errors.append("M4: paper_language_profile must review the project use of 题目 and 题干")
            if language_profile.get("change_policy") != "context_review_no_global_replace":
                errors.append("M4: paper_language_profile must use context review and prohibit global replacement")
            protected = language_profile.get("protected_scopes")
            required_protected = {
                "formulas", "symbols", "values", "citations", "figure_and_table_content",
                "headings", "direct_quotes", "model_logic",
            }
            if not isinstance(protected, list) or not required_protected.issubset(set(protected)):
                errors.append("M4: paper_language_profile must protect formulas, symbols, values, citations, figures/tables, headings, direct quotes and model logic")
            application = language_profile.get("batch_application")
            if (not isinstance(application, dict)
                    or application.get("apply_only_to_ordinary_prose") is not True
                    or application.get("approved_at") != "writing_plan_gate"):
                errors.append("M4: paper_language_profile batch application must be prose-only and approved at the writing-plan gate")
            profile_sources = language_profile.get("source_refs")
            profile_competition = profile_sources.get("competition_profile") if isinstance(profile_sources, dict) else None
            control_competition = control.get("competition_profile")
            if (not isinstance(profile_competition, dict)
                    or not isinstance(control_competition, dict)
                    or profile_competition.get("path") != control_competition.get("path")
                    or profile_competition.get("sha256") != control_competition.get("sha256")):
                errors.append("M4: paper_language_profile must bind the current competition_profile")
            for index, rule in enumerate(language_profile.get("term_rules", []) if isinstance(language_profile.get("term_rules"), list) else []):
                if (not isinstance(rule, dict) or not isinstance(rule.get("observed_form"), str)
                        or not rule["observed_form"].strip()
                        or not isinstance(rule.get("preferred_form"), str)
                        or not rule["preferred_form"].strip()
                        or not isinstance(rule.get("contexts"), list) or not rule["contexts"]):
                    errors.append(f"M4.paper_language_profile.term_rules[{index}]: observed_form, preferred_form and contexts required")
        writing_batches = blueprint.get("writing_batches")
        if m4.get("visual_workflow") == "chapter_parallel":
            blueprint_chapters = blueprint.get("chapters")
            declared = {c.get("chapter_id") for c in chapters if isinstance(c, dict)} if isinstance(chapters, list) else set()
            if (not isinstance(blueprint_chapters, list) or not blueprint_chapters
                    or len(blueprint_chapters) != len(declared)
                    or {c.get("chapter_id") for c in blueprint_chapters if isinstance(c, dict)} != declared):
                errors.append("M4: blueprint chapters must map one-to-one to paper-material chapters")
            for chapter in blueprint_chapters if isinstance(blueprint_chapters, list) else []:
                if (not isinstance(chapter, dict) or not chapter.get("role") or not chapter.get("page_capacity")
                        or any(not isinstance(chapter.get(key), list) for key in ("figure_ids", "table_ids", "claim_ids", "evidence_refs"))):
                    errors.append("M4: chapter role, capacity and evidence mappings required")
            global_plan = blueprint.get("global", {})
            length = global_plan.get("target_length") if isinstance(global_plan, dict) else None
            if not isinstance(length, dict) or not length.get("page_range") or not length.get("basis"):
                errors.append("M4: official-rule-based total page capacity required")
        elif not isinstance(writing_batches, list) or len(writing_batches) != 4:
            errors.append("M4: paper_argument_blueprint must define exactly four writing batches")
        else:
            batch_ids = [item.get("batch_id") for item in writing_batches if isinstance(item, dict)]
            if batch_ids != ["B1", "B2", "B3", "B4"]:
                errors.append("M4: writing batches must be ordered B1 through B4")
            assigned = [
                chapter_id
                for item in writing_batches if isinstance(item, dict)
                for chapter_id in item.get("chapter_ids", []) if isinstance(chapter_id, str)
            ]
            chapter_ids = {
                item.get("chapter_id") for item in chapters
                if isinstance(item, dict) and isinstance(item.get("chapter_id"), str)
            } if isinstance(chapters, list) else set()
            if len(assigned) != len(set(assigned)) or set(assigned) != chapter_ids:
                errors.append("M4: four writing batches must cover each blueprint/readiness chapter exactly once")
            blueprint_chapters = blueprint.get("chapters")
            if not isinstance(blueprint_chapters, list) or not blueprint_chapters:
                errors.append("M4: paper_argument_blueprint chapters are required")
            else:
                blueprint_chapter_ids = []
                for index, chapter in enumerate(blueprint_chapters):
                    if not isinstance(chapter, dict):
                        errors.append(f"M4.paper_argument_blueprint.chapters[{index}]: mapping required")
                        continue
                    chapter_id = chapter.get("chapter_id")
                    blueprint_chapter_ids.append(chapter_id)
                    if (not isinstance(chapter_id, str) or not chapter_id
                            or not chapter.get("role") or not chapter.get("page_capacity")
                            or not isinstance(chapter.get("figure_ids"), list)
                            or not isinstance(chapter.get("table_ids"), list)
                            or not isinstance(chapter.get("claim_ids"), list)
                            or not isinstance(chapter.get("evidence_refs"), list)):
                        errors.append(f"M4.paper_argument_blueprint.chapters[{index}]: role, page_capacity, figure_ids, table_ids, claim_ids and evidence_refs required")
                if len(blueprint_chapter_ids) != len(set(blueprint_chapter_ids)) or set(blueprint_chapter_ids) != chapter_ids:
                    errors.append("M4: blueprint chapters must map one-to-one to paper_material_readiness chapters")
            global_plan = blueprint.get("global")
            target_length = global_plan.get("target_length") if isinstance(global_plan, dict) else None
            if (not isinstance(target_length, dict) or not target_length.get("page_range")
                    or not target_length.get("basis")
                    or not isinstance(global_plan.get("chapter_order"), list)):
                errors.append("M4: blueprint must define official-rule-based total page range and chapter order")
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


def check(root: Path, through: str = "M1", preflight_writing: bool = False,
          preflight_node: str | None = None, preflight_draft: bool = False) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    pauses: list[str] = []
    control = _read(root / ".contest" / "mathorcup_control.yaml", errors)
    preflight_writing = preflight_writing or preflight_draft
    workflow = control.get("nodes", {}).get("M4", {}).get("visual_workflow")
    chapter_parallel = workflow == "chapter_parallel"
    writer_first = workflow in {"writer_first_batches", "chapter_parallel"}
    if workflow not in (None, "writer_first_batches", "chapter_parallel"):
        errors.append("M4: unsupported visual_workflow")
    if preflight_draft and not writer_first:
        errors.append("--preflight-draft requires writer_first_batches or chapter_parallel")
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
    protocol = control.get("execution_protocol")
    if protocol not in (None, "2.0"):
        errors.append("execution_protocol: unsupported version")
    target_node = preflight_node or ("M4" if preflight_writing else through)
    required_roles = None
    if protocol == "2.0":
        required_roles = set().union(*(REQUIRED_ROLES[n] for n in NODES[:NODES.index(target_node) + 1]))
        if preflight_draft or writer_first:
            required_roles.discard("figure")
    ids = _check_instances(root, control, errors, required_roles)
    nodes = control.get("nodes")
    if not isinstance(nodes, dict):
        errors.append("nodes must be a mapping")
        nodes = {}
    approval_times: dict[str, datetime | date] = {}
    reviewed_inputs: dict[str, dict[str, str]] = {}
    phase_approval_times: dict[str, datetime | date] = {}
    figure_count = 0
    if preflight_node is not None:
        through = preflight_node
    through_index = NODES.index("M3") if preflight_writing else NODES.index(through)
    node_ids, recovery_times = _node_instances(
        root, control, log, ids, NODES.index("M4") if preflight_writing else through_index, errors)
    if preflight_writing:
        reviewed_inputs["M4"] = _h6_material_rebindings(
            root, control, node_ids["M4"], errors, pauses)
    for node_id in NODES[:through_index + 1]:
        node = nodes.get(node_id)
        if not isinstance(node, dict):
            errors.append(f"{node_id}: node mapping required")
            continue
        if node.get("status") not in {"approved", "frozen"}:
            pauses.append(f"{node_id}: node not approved")
            if node_id != preflight_node:
                continue
        refs = _node_refs(root, node_id, node, errors)
        _validate_node_evidence(root, node_id, refs, node_ids[node_id], subproblems, errors)
        if node_id == "M4":
            figure_count = _writing_preflight(root, control, log, node_ids["M4"], subproblems,
                                              errors, pauses, phase_approval_times,
                                              reviewed_inputs)
            if node.get("writing_started") is not True:
                errors.append("M4: writing_started must be true for completed node")
        found_packet = _artifact(root, node.get("review_packet"), f"{node_id}.review_packet", errors)
        if found_packet:
            approval_time, reviewed = _review(root, control, log, node_id,
                                              node.get("review_packet"), list(refs.values()),
                                              errors, pauses,
                                              reviewed_inputs.get("M4") if preflight_writing and node_id == "M3" else None)
            if approval_time is not None:
                approval_times[node_id] = approval_time
            reviewed_inputs[node_id] = reviewed
    dispatch_index = NODES.index("M4") if preflight_writing else through_index
    if preflight_writing:
        figure_count = _writing_preflight(root, control, log, node_ids["M4"], subproblems,
                                          errors, pauses, phase_approval_times,
                                          reviewed_inputs, draft_only=preflight_draft)
    if (through_index >= NODES.index("M4") or preflight_writing) and not preflight_draft and not chapter_parallel:
        _check_writing_batch_sequence(root, control, log, phase_approval_times, errors, pauses)
    if workflow == "writer_first_batches" and (through_index >= NODES.index("M4") or preflight_writing):
        _check_batch_visual_workflow(root, control, log, phase_approval_times, errors, pauses,
                                     final=not preflight_draft)
    if chapter_parallel and (through_index >= NODES.index("M4") or preflight_writing):
        from mathorcup_chapter_workflow import validate
        validate(root, control, log, node_ids["M4"], phase_approval_times,
                 reviewed_inputs, errors, pauses, sys.modules[__name__], final=not preflight_draft)
    if through_index >= NODES.index("M4"):
        final_batch_approval = phase_approval_times.get("M4_FINAL_PAPER" if chapter_parallel else "M4_WRITING_BATCH:B4")
        final_node_approval = approval_times.get("M4")
        if (isinstance(final_batch_approval, datetime) and isinstance(final_node_approval, datetime)
                and final_node_approval <= final_batch_approval):
            errors.append("M4: final node approval must follow the whole-paper review")
    dispatched, m4_phases = _check_dispatch(
        root, control, ids, approval_times, reviewed_inputs,
        phase_approval_times, dispatch_index, errors, node_ids, recovery_times,
    )
    for node_id in NODES[:through_index + 1]:
        node = nodes.get(node_id)
        if (not isinstance(node, dict)
                or (node.get("status") not in {"approved", "frozen"} and node_id != preflight_node)):
            continue
        needed = REQUIRED_ROLES[node_id] - ({"figure"} if writer_first and node_id == "M4" and not figure_count else set())
        for role in needed - dispatched.get(node_id, set()):
            errors.append(f"{node_id}: required role not dispatched: {role}")
        _check_skill_calls(root, node_id, node, "figure" in dispatched.get(node_id, set()), errors)
    if preflight_writing:
        needed = REQUIRED_ROLES["M4"] - ({"figure"} if preflight_draft or (writer_first and not figure_count) else set())
        for role in needed - dispatched.get("M4", set()):
            errors.append(f"M4: required role not dispatched: {role}")
        m4 = nodes.get("M4", {})
        if isinstance(m4, dict) and m4.get("writing_started") and (errors or pauses):
            errors.append("M4: writing started before preflight PASS")
    if preflight_writing or through_index >= NODES.index("M4"):
        if figure_count and "generate" not in m4_phases["figure"]:
            errors.append("M4: approved figure plan requires post-approval generate dispatch")
        m4 = nodes.get("M4", {})
        if isinstance(m4, dict) and m4.get("writing_started") and not preflight_draft and "write" not in m4_phases["writer"]:
            errors.append("M4: writing_started requires post-approval writer dispatch")
    if protocol == "2.0":
        _check_execution_evidence(root, control, target_node, subproblems, errors, draft_only=preflight_draft)
    status = "BLOCK" if errors else "PAUSE" if pauses else "PASS"
    return {"status": status, "active_mode": control.get("active_mode"),
            "through": "M4-draft" if preflight_draft else "M4-writing" if preflight_writing else through,
            **({"preflight_node": preflight_node, "evidence_status": "BLOCK" if errors else "PASS"}
               if preflight_node is not None else {}),
            "failures": errors, "pending": pauses}


def _check_batch_visual_workflow(root: Path, control: dict[str, Any], log: dict[str, Any],
                                  phase_times: dict[str, datetime | date], errors: list[str],
                                  pauses: list[str], final: bool = False) -> None:
    """Bind writer-selected visuals to the draft and human-selected asset version."""
    m4 = control.get("nodes", {}).get("M4", {})
    batches = m4.get("writing_batches", [])
    if not isinstance(batches, list):
        errors.append("M4: writing_batches must be a list")
        return
    calls: dict[tuple[str, str, str], list[datetime]] = {}
    for record in control.get("dispatch_records", []):
        if not isinstance(record, dict) or record.get("node_id") != "M4" or record.get("superseded_by"):
            continue
        found = _artifact(root, {"path": record.get("task_card"), "sha256": record.get("task_card_sha256")},
                          "M4.batch_dispatch", errors)
        if not found:
            continue
        card = _read(found[1], errors)
        scope = card.get("scope", {})
        if not isinstance(scope, dict):
            continue
        batch_id, phase = scope.get("batch_id"), scope.get("phase")
        if phase not in {"draft", "write", "generate"}:
            continue
        called = _time(record.get("called_at"))
        if batch_id not in {"B1", "B2", "B3", "B4"} or called is None:
            errors.append("M4: draft/generate/write dispatch requires batch_id and timestamp")
            continue
        calls.setdefault((batch_id, record.get("owner_role"), phase), []).append(called)
    aggregate_slots = []
    selected_assets = {}
    for index, batch in enumerate(batches):
        if not isinstance(batch, dict):
            errors.append("M4: batch mapping required")
            continue
        batch_id = batch.get("batch_id")
        if batch_id not in ("B1", "B2", "B3", "B4"):
            errors.append("M4: valid writing batch ID required")
            continue
        label = f"M4.{batch_id}"
        # An unstarted batch is a blueprint slot, not a missing result.
        if batch.get("draft") is None:
            if final or calls.get((batch_id, "figure", "generate")) or calls.get((batch_id, "writer", "write")):
                errors.append(f"{label}: immutable writer draft required before visuals/integration")
            continue
        draft = _artifact(root, batch.get("draft"), f"{label}.draft", errors)
        completed_at = _time(batch.get("draft_completed_at"))
        draft_calls = calls.get((batch_id, "writer", "draft"), [])
        if len(draft_calls) != 1 or completed_at is None or draft_calls[0] >= completed_at:
            errors.append(f"{label}: draft completion must follow its single accepted writer draft dispatch")
        previous_gate = "M4_ABSTRACT_FRAMEWORK" if batch_id == "B4" else (
            f"M4_WRITING_BATCH:B{index}" if index else "M4_WRITING_PLAN")
        prior_time = phase_times.get(previous_gate)
        if previous_gate == "M4_ABSTRACT_FRAMEWORK" and prior_time is None:
            framework = _artifact(root, m4.get("abstract_framework"), "M4.abstract_framework", errors)
            if framework:
                prior_time, _ = _review(root, control, log, previous_gate,
                                        m4.get("abstract_framework_review_packet"), [framework], errors, pauses)
                if prior_time is not None:
                    phase_times[previous_gate] = prior_time
        if prior_time is not None and any(not _gate_was_satisfied_before(at, prior_time) for at in draft_calls):
            errors.append(f"{label}: draft before previous batch/writing-plan approval")
        if prior_time is None:
            errors.append(f"{label}: missing {previous_gate} before draft")
        plan_ref = _artifact(root, batch.get("visual_argument_plan"), f"{label}.visual_argument_plan", errors)
        if not plan_ref:
            continue
        plan = _read(plan_ref[1], errors)
        batch_review_refs = [ref for ref in (draft, plan_ref) if ref]
        prepared_at = _time(plan.get("prepared_at"))
        if (plan.get("owner_role") != "writer" or plan.get("batch_id") != batch_id
                or plan.get("draft") != batch.get("draft") or prepared_at is None or completed_at is None
                or prepared_at < completed_at):
            errors.append(f"{label}: writer visual requirements must bind the completed draft")
        slots = plan.get("slots")
        if not isinstance(slots, list) or any(not isinstance(slot, dict) for slot in slots):
            errors.append(f"{label}: explicit visual slots list required (empty means no visuals)")
            continue
        figure_slots: set[str] = set()
        for slot in slots:
            slot_id = slot.get("slot_id")
            if (not isinstance(slot_id, str) or not slot_id or slot.get("representation") not in {"figure", "table", "text"}
                    or not all(slot.get(key) for key in ("reader_question", "body_anchor", "claim", "evidence_refs"))):
                errors.append(f"{label}: visual intent, anchor and evidence required")
            if slot.get("representation") == "figure" and isinstance(slot_id, str):
                if slot.get("generation_route") not in {"modelviz", "tikz-scientific-figures"}:
                    errors.append(f"{label}: approved figure generation route required")
                figure_slots.add(slot_id)
            for evidence in slot.get("evidence_refs", []) if isinstance(slot.get("evidence_refs"), list) else []:
                _artifact(root, evidence, f"{label}.visual_evidence", errors)
        aggregate_slots.extend(slots)
        gate = f"M4_VISUAL_PLAN:{batch_id}"
        approval_time, _ = _review(root, control, log, gate, batch.get("visual_plan_review_packet"),
                                    [ref for ref in (draft, plan_ref) if ref], errors, pauses)
        if approval_time is not None:
            phase_times[gate] = approval_time
            if prepared_at is not None and isinstance(approval_time, datetime) and approval_time < prepared_at:
                errors.append(f"{label}: visual approval predates requirements")
        generation = calls.get((batch_id, "figure", "generate"), [])
        writes = calls.get((batch_id, "writer", "write"), [])
        if figure_slots and (final or writes) and not generation:
            errors.append(f"{label}: requested figures have no generation dispatch")
        if not figure_slots and generation:
            errors.append(f"{label}: generation outside approved figure demand")
        if any(not _gate_was_satisfied_before(at, approval_time) for at in generation):
            errors.append(f"{label}: generation before human requirement approval")
        selection_time = approval_time
        if figure_slots and (final or batch.get("figure_selection") is not None or writes):
            selection_ref = _artifact(root, batch.get("figure_selection"), f"{label}.figure_selection", errors)
            selection = _read(selection_ref[1], errors) if selection_ref else {}
            assets = selection.get("assets")
            if not isinstance(assets, list) or any(not isinstance(asset, dict) for asset in assets):
                errors.append(f"{label}: selected assets list required")
                assets = []
            selected_ids = [asset.get("slot_id") for asset in assets]
            if (selection.get("batch_id") != batch_id or len(selected_ids) != len(figure_slots)
                    or any(not isinstance(value, str) for value in selected_ids) or set(selected_ids) != figure_slots):
                errors.append(f"{label}: selected assets must cover exactly the requested figure slots")
            refs = [_artifact(root, asset, f"{label}.selected_asset", errors) for asset in assets]
            batch_review_refs.extend(ref for ref in (selection_ref, *refs) if ref)
            for asset in assets:
                if isinstance(asset.get("slot_id"), str):
                    selected_assets[asset["slot_id"]] = asset
            gate = f"M4_FIGURE_SELECTION:{batch_id}"
            selection_time, _ = _review(root, control, log, gate, batch.get("figure_selection_review_packet"),
                                         [ref for ref in (selection_ref, *refs) if ref], errors, pauses)
            if selection_time is not None:
                phase_times[gate] = selection_time
                if isinstance(selection_time, datetime) and any(selection_time <= at for at in generation):
                    errors.append(f"{label}: human asset selection must follow generation")
        if any(not _gate_was_satisfied_before(at, selection_time) for at in writes):
            errors.append(f"{label}: writer integration before human asset selection/requirements")
        manuscript = batch.get("manuscript")
        if isinstance(manuscript, dict):
            found = _artifact(root, manuscript, f"{label}.manuscript", errors)
            if found:
                at, _ = _review(root, control, log, f"M4_WRITING_BATCH:{batch_id}", batch.get("review_packet"),
                                 [found, *batch_review_refs], errors, pauses)
                if at is not None:
                    phase_times[f"M4_WRITING_BATCH:{batch_id}"] = at
    if final:
        aggregate = _artifact(root, m4.get("visual_argument_plan"), "M4.visual_argument_plan", errors)
        if aggregate and _read(aggregate[1], errors).get("slots") != aggregate_slots:
            errors.append("M4: aggregate visual plan must equal the approved batch slots")
        registry = _artifact(root, m4.get("figure_registry"), "M4.figure_registry", errors)
        if registry:
            figures = _read(registry[1], errors).get("figures", [])
            for figure in figures if isinstance(figures, list) else []:
                if not isinstance(figure, dict):
                    continue
                slots = figure.get("visual_slot_ids", [])
                expected = selected_assets.get(slots[0]) if isinstance(slots, list) and len(slots) == 1 else None
                selected = figure.get("selected_asset")
                if (not expected or not isinstance(selected, dict)
                        or any(selected.get(key) != expected.get(key) for key in ("path", "sha256"))):
                    errors.append(f"M4.{figure.get('figure_id')}: registry differs from human-selected asset")


def _check_human_authorization(root: Path, card: dict[str, Any], called_at: Any,
                                errors: list[str]) -> None:
    authorization = card.get("authorization")
    if not isinstance(authorization, dict):
        errors.append(f"{card.get('task_id')}: human authorization source required")
        return
    found = _artifact(root, authorization.get("source"), "authorization.source", errors)
    if not found:
        return
    message = _read(found[1], errors)
    approved_at, dispatched_at = _time(message.get("created_at")), _time(called_at)
    if (message.get("role") != "user" or not message.get("content")
            or not message.get("message_id") or message.get("message_id") != authorization.get("message_id")
            or not isinstance(message.get("task_ids"), list) or card.get("task_id") not in message["task_ids"]
            or not isinstance(message.get("roles"), list) or card.get("owner_role") not in message["roles"]
            or approved_at is None or dispatched_at is None or approved_at > dispatched_at):
        errors.append(f"{card.get('task_id')}: scoped original human authorization required before dispatch")


def _check_role_registry(root: Path, control: dict[str, Any], through: str, errors: list[str]) -> None:
    registry = _read(root / ".contest" / "agent_registry.yaml", errors)
    entries = registry.get("instances")
    if not isinstance(entries, list) or not entries:
        errors.append("agent_registry.instances: register every created chat before dispatch")
        return
    records: dict[str, dict[str, Any]] = {}
    threads: dict[str, tuple[str, str]] = {}
    for item in entries:
        if not isinstance(item, dict):
            errors.append("agent_registry: instance mapping required")
            continue
        if item.get("status") == "pending":
            if not item.get("client_thread_id") and not item.get("operation_id"):
                errors.append("agent_registry: pending creation requires the returned client/operation ID")
            continue
        instance, thread = item.get("agent_instance_id"), item.get("thread_id")
        if not isinstance(instance, str) or not instance or instance in records:
            errors.append("agent_registry: unique execution instance ID required")
            continue
        records[instance] = item
        try:
            uuid.UUID(thread)
            valid_thread = True
        except (ValueError, TypeError, AttributeError):
            valid_thread = False
        previous = threads.get(thread) if isinstance(thread, str) else None
        resumed_chat = previous == (item.get("role"), item.get("replaces"))
        if not valid_thread or (previous is not None and not resumed_chat) or item.get("user_accessible") is not True:
            errors.append(f"agent_registry.{instance}: distinct user-accessible thread UUID required")
        if isinstance(thread, str):
            threads[thread] = (item.get("role"), instance)
        created_at, registered_at = _time(item.get("created_at")), _time(item.get("registered_at"))
        if created_at is None or registered_at is None or registered_at < created_at:
            errors.append(f"agent_registry.{instance}: valid creation/registration times required")
        if (item.get("role") not in {*ROUTES, "support"} or item.get("effective_from") not in NODES
                or not all(item.get(key) for key in ("created_by", "model", "reasoning_effort", "status"))):
            errors.append(f"agent_registry.{instance}: role, creator, runtime route, status and effective node required")
    instances = control.get("agent_instances")
    if not isinstance(instances, dict):
        errors.append("agent_registry: control instance bindings must be a mapping")
        instances = {}
    for role, item in instances.items():
        if isinstance(item, dict):
            instance = item.get("agent_instance_id")
            registered = records.get(instance, {}) if isinstance(instance, str) else {}
            if registered.get("role") != role:
                errors.append(f"agent_registry: created {role} instance missing or mismatched")
    dispatches = control.get("dispatch_records")
    if not isinstance(dispatches, list):
        errors.append("agent_registry: dispatch records must be a list")
        dispatches = []
    for dispatch in dispatches:
        if not isinstance(dispatch, dict) or dispatch.get("node_id") not in NODES:
            continue
        if NODES.index(dispatch["node_id"]) > NODES.index(through):
            continue
        instance = dispatch.get("agent_instance_id")
        registered = records.get(instance, {}) if isinstance(instance, str) else {}
        registered_at, called_at = _time(registered.get("registered_at")), _time(dispatch.get("called_at"))
        successors = [item for item in records.values() if item.get("replaces") == instance]
        retired_at = [_time(item.get("created_at")) for item in successors]
        historical_dispatch = (registered.get("status") == "superseded" and bool(retired_at)
                               and called_at is not None and all(at is not None and called_at < at for at in retired_at))
        if (registered.get("role") != dispatch.get("owner_role")
                or (registered.get("status") not in ("active", "ready", "idle", "running") and not historical_dispatch)
                or registered_at is None
                or called_at is None or registered_at > called_at
                or registered.get("effective_from") not in NODES
                or NODES.index(registered["effective_from"]) > NODES.index(dispatch["node_id"])):
            errors.append(f"agent_registry.{instance}: matching registration required before dispatch")
        if registered and any(registered.get(key) != dispatch.get(key) for key in ("model", "reasoning_effort")):
            errors.append(f"agent_registry.{instance}: registered and actual runtime route differ")
        found = _artifact(root, {"path": dispatch.get("task_card"), "sha256": dispatch.get("task_card_sha256")},
                          f"agent_registry.{instance}.task", errors)
        if found:
            card = _read(found[1], errors)
            _check_human_authorization(root, card, dispatch.get("called_at"), errors)


def _check_figure_integration(root: Path, registry: dict[str, Any], errors: list[str]) -> None:
    entries = registry.get("figures")
    if not isinstance(entries, list):
        errors.append("figure_registry.figures: list required")
        return
    seen_ids, seen_labels, seen_numbers = set(), set(), set()
    for figure in entries:
        if not isinstance(figure, dict):
            errors.append("figure_registry: figure mapping required")
            continue
        asset_id, label, number = figure.get("figure_id"), figure.get("paper_label"), figure.get("paper_number")
        prefix = f"figure_registry.{asset_id}"
        if (not isinstance(asset_id, str) or not asset_id or asset_id in seen_ids
                or not isinstance(label, str) or not label or label in seen_labels
                or type(number) is not int or number < 1 or number in seen_numbers):
            errors.append(f"{prefix}: unique asset ID, paper label and positive paper number required")
            continue
        seen_ids.add(asset_id)
        seen_labels.add(label)
        seen_numbers.add(number)
        if not figure.get("selected_version") or figure.get("integration_status") != "integrated":
            errors.append(f"{prefix}: selected version must be integrated before paper completion")
        for key in ("canvas", "insertion"):
            size = figure.get(key)
            dimensions = ("width", "height") if key == "canvas" else ("width",)
            if (not isinstance(size, dict) or not size.get("unit")
                    or any(type(size.get(d)) not in (float, int) or size[d] <= 0 for d in dimensions)):
                errors.append(f"{prefix}: {key} size with units required")
        selected = _artifact(root, figure.get("selected_asset"), f"{prefix}.selected_asset", errors)
        copy_ref = _artifact(root, figure.get("paper_copy"), f"{prefix}.paper_copy", errors)
        source = _artifact(root, figure.get("paper_source"), f"{prefix}.paper_source", errors)
        if selected and copy_ref and _digest(selected[1]) != _digest(copy_ref[1]):
            errors.append(f"{prefix}: paper copy differs from selected asset")
        if source and copy_ref:
            text = source[1].read_text(encoding="utf-8")
            text = re.sub(r"(?<!\\)%[^\n]*", "", text)
            includes = re.findall(r"\\includesvg\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}", text)
            candidates = [(source[1].parent / name).with_suffix(".svg").resolve() for name in includes]
            if copy_ref[1] not in candidates or not re.search(r"\\label\s*\{" + re.escape(label) + r"\}", text):
                errors.append(f"{prefix}: selected paper copy/label is not used in declared TeX source")


def _check_execution_evidence(root: Path, control: dict[str, Any], through: str,
                              subproblems: list[str], errors: list[str], draft_only: bool = False) -> None:
    """Additional semantics for new runs; historical controls remain readable."""
    nodes = control.get("nodes")
    if not isinstance(nodes, dict):
        nodes = {}
    _check_role_registry(root, control, through, errors)

    def load(node: str, key: str) -> dict[str, Any]:
        record = nodes.get(node, {})
        found = _artifact(root, record.get(key), f"{node}.{key}", errors)
        return _read(found[1], errors) if found else {}

    kpi = load("M1", "task_kpi")
    requirements = kpi.get("subproblems")
    if not isinstance(requirements, dict) or set(requirements) != set(subproblems):
        errors.append("task_kpi.subproblems: original requirements for every question required")
    elif through in {"M1", "M2"}:
        for question, item in requirements.items():
            if not isinstance(item, dict):
                errors.append(f"task_kpi.{question}: requirement mapping required")
                continue
            _artifact(root, item.get("source"), f"task_kpi.{question}.source", errors)
            _unique_strings(item.get("targets"), f"task_kpi.{question}.targets", errors)
            if (not all(item.get(key) for key in ("locator", "requirement_text", "final_carrier"))
                    or type(item.get("outputs_per_target")) is not int or item["outputs_per_target"] < 1):
                errors.append(f"task_kpi.{question}: original text, locator and output cardinality required")
    if NODES.index(through) >= NODES.index("M3"):
        cards = load("M3", "model_summary_cards")
        _check_requirement_coverage(root, kpi, cards.get("requirement_coverage"), subproblems, errors)
        manifest = load("M3", "run_manifest")
        report = load("M5", "reproducibility_report") if through == "M5" else None
        _check_reproduction(root, manifest, report, errors)
    if NODES.index(through) >= NODES.index("M4") and not draft_only:
        _check_figure_integration(root, load("M4", "figure_registry"), errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--through", choices=NODES, default="M1")
    group.add_argument("--preflight-writing", action="store_true")
    group.add_argument("--preflight-draft", action="store_true", help="Admit writer-first drafts without finished figures")
    group.add_argument("--preflight-node", choices=NODES,
                       help="Read-only evidence check without granting node approval")
    args = parser.parse_args()
    report = check(args.project_root, through=args.through, preflight_writing=args.preflight_writing,
                   preflight_node=args.preflight_node, preflight_draft=args.preflight_draft)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return {"PASS": 0, "PAUSE": 2, "BLOCK": 1}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
