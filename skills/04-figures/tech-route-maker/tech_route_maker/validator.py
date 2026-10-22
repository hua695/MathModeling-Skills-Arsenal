import json
from pathlib import Path

from .quality import (
    _assumption_node_ids,
    build_quality_report,
    declared_source_ids,
    iter_nodes,
    valid_evidence_item,
)
from .registry import SUPPORTED_LAYOUTS, SUPPORTED_STYLES, canonical_style_name
from .schema import (
    ROUTE_VERSION,
    SUPPORTED_FORMATS,
    VALID_CONFIDENCE,
    VALID_PRESETS,
    domain_context_missing_fields,
    domain_context_status,
    selected_output_formats,
)
from .sources import verify_sources


def load_route(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _evidence_status(node, source_ids, resolved_sources):
    valid = False
    errors = []
    issues = []
    evidence = node.get("evidence")
    if not isinstance(evidence, list):
        return False, ["evidence must be a list"], issues

    for index, item in enumerate(evidence, start=1):
        if not valid_evidence_item(item, source_ids):
            errors.append(f"evidence item {index} is incomplete or references an undeclared source")
            continue
        source_id = str(item.get("source_id"))
        source = resolved_sources.get(source_id)
        if not source or source.get("status") != "verified":
            issues.append(f"Evidence source is not hash-verified for node {node.get('id')}: {source_id}")
            continue
        evidence_path = str(item.get("path") or "")
        declared_path = str(source.get("raw_path") or "")
        if evidence_path and evidence_path != declared_path:
            issues.append(
                f"Evidence path differs from the declared source for node {node.get('id')}: {evidence_path}"
            )
            continue
        locator = str(item.get("locator") or "").strip()
        source_text = source.get("text")
        if source_text is not None and locator.casefold() not in source_text.casefold():
            issues.append(f"Evidence locator was not found in source text for node {node.get('id')}: {locator}")
            continue
        valid = True
    return valid, errors, issues


def validate(route, route_path=None):
    errors = []
    warnings = []

    if not route.get("title"):
        errors.append("Missing route title.")
    if not route.get("stages"):
        errors.append("Missing stages.")

    route_version = route.get("route_version")
    if not route_version:
        errors.append("Missing route_version.")
    elif route_version != ROUTE_VERSION:
        warnings.append(f"Route version is {route_version}; current schema version is {ROUTE_VERSION}.")

    selected_preset = route.get("selected_preset")
    if not selected_preset:
        errors.append("Missing selected_preset.")
    elif selected_preset not in VALID_PRESETS:
        errors.append(f"Invalid selected_preset: {selected_preset}")

    layout = str(route.get("layout") or "")
    if layout not in SUPPORTED_LAYOUTS:
        errors.append(f"Unsupported layout: {layout or '(missing)'}")
    style = str(route.get("style") or "")
    if canonical_style_name(style) not in SUPPORTED_STYLES:
        errors.append(f"Unsupported style: {style or '(missing)'}")

    domain_status = domain_context_status(route)
    missing_domain = domain_context_missing_fields(route)
    if domain_status == "missing":
        warnings.append("Missing domain_context; final diagrams require a stated discipline and field-specific context.")
    elif missing_domain:
        warnings.append(f"Incomplete domain_context; missing: {', '.join(missing_domain)}")

    stages = route.get("stages") or []
    if len(stages) < 4:
        warnings.append("Route has fewer than 4 stages; consider adding validation or output stages.")
    if len(stages) > 7:
        warnings.append("Route has more than 7 stages; consider grouping stages.")

    metadata = route.get("metadata") or {}
    source_files = metadata.get("source_files", [])
    source_hashes = metadata.get("source_hashes", [])
    if not isinstance(source_files, list):
        errors.append("metadata.source_files must be a list.")
        source_files = []
    if not isinstance(source_hashes, list):
        errors.append("metadata.source_hashes must be a list.")
    if not source_files:
        warnings.append("No source files are declared.")
    for index, source in enumerate(source_files, start=1):
        if not isinstance(source, dict):
            errors.append(f"Source record {index} must be an object.")
            continue
        if not source.get("path"):
            errors.append(f"Source record {index} is missing path.")
        if not (source.get("id") or source.get("source_id")):
            errors.append(f"Source record {index} is missing id.")

    source_verification, resolved_sources = verify_sources(route, route_path=route_path)
    if source_verification.get("missing_sources"):
        warnings.append(
            "Missing source files: " + ", ".join(source_verification["missing_sources"])
        )
    if source_verification.get("unhashed_sources"):
        warnings.append(
            "Source files without SHA-256: " + ", ".join(source_verification["unhashed_sources"])
        )
    if source_verification.get("hash_mismatches"):
        warnings.append(
            "Source hash mismatch: " + ", ".join(source_verification["hash_mismatches"])
        )
    if source_verification.get("duplicate_source_ids"):
        errors.append(
            "Duplicate source ids: " + ", ".join(source_verification["duplicate_source_ids"])
        )

    stage_ids = set()
    node_ids = set()
    assumption_node_ids = _assumption_node_ids(route)
    source_ids = declared_source_ids(route)
    verified_evidence_node_ids = set()
    evidence_issues = []

    for stage in stages:
        stage_id = stage.get("id")
        if not stage_id:
            errors.append("Stage missing id.")
            continue
        if stage_id in stage_ids:
            errors.append(f"Duplicate stage id: {stage_id}")
        stage_ids.add(stage_id)

        stage_nodes = stage.get("nodes") or []
        if not stage_nodes:
            warnings.append(f"Stage has no nodes: {stage_id}")
        if len(stage_nodes) < 2:
            warnings.append(f"Stage has fewer than 2 nodes: {stage_id}")
        if len(stage_nodes) > 6:
            errors.append(f"Stage has more than 6 nodes and cannot be rendered safely: {stage_id}")

        for node in stage_nodes:
            node_id = node.get("id")
            if not node_id:
                errors.append(f"Node in stage {stage_id} missing id.")
                continue
            if node_id in node_ids:
                errors.append(f"Duplicate node id: {node_id}")
            node_ids.add(node_id)

            if not node.get("label"):
                errors.append(f"Node missing label: {node_id}")
            if len(str(node.get("label") or "")) > 42:
                warnings.append(f"Long visible label: {node_id}")

            confidence = node.get("confidence")
            if confidence not in VALID_CONFIDENCE:
                errors.append(f"Invalid or missing node confidence for {node_id}: {confidence}")

            has_verified_evidence, evidence_errors, node_issues = _evidence_status(
                node, source_ids, resolved_sources
            )
            if evidence_errors:
                errors.extend(f"Node {node_id}: {message}." for message in evidence_errors)
            evidence_issues.extend(node_issues)
            if has_verified_evidence:
                verified_evidence_node_ids.add(node_id)
            is_inferred = node.get("is_inferred") is True
            if not has_verified_evidence and not is_inferred:
                warnings.append(f"Node has no verified evidence and is not marked inferred: {node_id}")
            if is_inferred and node_id not in assumption_node_ids:
                warnings.append(f"Inferred node is not linked from assumptions: {node_id}")

    for assumption in route.get("assumptions") or []:
        if not isinstance(assumption, dict):
            errors.append("Each assumption must be an object.")
            continue
        for node_id in assumption.get("node_ids") or []:
            if node_id not in node_ids:
                errors.append(f"Assumption references missing node: {node_id}")

    edge_ids = set()
    for index, edge in enumerate(route.get("edges") or [], start=1):
        edge_id = edge.get("id") or f"edge_{index}"
        if edge_id in edge_ids:
            errors.append(f"Duplicate edge id: {edge_id}")
        edge_ids.add(edge_id)
        source = edge.get("from") or edge.get("source")
        target = edge.get("to") or edge.get("target")
        if source not in node_ids or target not in node_ids:
            errors.append(f"Edge endpoint missing: {source} -> {target}")
        confidence = edge.get("confidence", "medium")
        if confidence not in VALID_CONFIDENCE:
            errors.append(f"Invalid edge confidence for {edge_id}: {confidence}")

    formats = selected_output_formats(route)
    if not formats:
        warnings.append("No selected_output_formats recorded in metadata.")
    for output_format in formats:
        if output_format not in SUPPORTED_FORMATS:
            errors.append(f"Unsupported output format in metadata: {output_format}")

    if not isinstance(route.get("assumptions", []), list):
        errors.append("assumptions must be a list.")
    if not isinstance(route.get("unresolved_questions", []), list):
        errors.append("unresolved_questions must be a list.")

    quality_report = build_quality_report(
        route,
        source_verification=source_verification,
        verified_evidence_node_ids=verified_evidence_node_ids,
        evidence_issues=evidence_issues,
    )
    for warning in quality_report.get("warnings") or []:
        if warning not in warnings:
            warnings.append(warning)

    return errors, warnings, quality_report


def strict_render_blockers(route, errors, quality_report):
    blockers = list(errors)
    if route.get("route_version") != ROUTE_VERSION:
        blockers.append(f"Route must use schema version {ROUTE_VERSION}.")
    if quality_report.get("domain_context_status") != "complete":
        blockers.append("Domain context must be complete before final rendering.")
    source = quality_report.get("source_verification") or {}
    if source.get("status") != "verified":
        blockers.append("Every declared source file must exist and match its SHA-256 hash.")
    if quality_report.get("evidence_coverage", 0.0) < 1.0:
        blockers.append("Every visible node must have verified source evidence.")
    if quality_report.get("inferred_node_count", 0):
        blockers.append("Inferred nodes remain; resolve or remove them before final rendering.")
    if quality_report.get("unresolved_question_count", 0):
        blockers.append("Unresolved questions remain.")
    if quality_report.get("evidence_issues"):
        blockers.append("One or more evidence locators failed verification.")
    return list(dict.fromkeys(blockers))


def format_validation_result(route, errors, warnings, quality_report):
    status = "Validation failed" if errors else "Validation OK"
    source = quality_report.get("source_verification") or {}
    lines = [
        status,
        f"Route version: {route.get('route_version', '')}",
        f"Preset: {route.get('selected_preset', '')}",
        f"Domain context: {quality_report.get('domain_context_status', 'missing')}",
        f"Stages: {quality_report.get('stage_count', 0)}",
        f"Nodes: {quality_report.get('node_count', 0)}",
        f"Edges: {quality_report.get('edge_count', 0)}",
        f"Evidence coverage: {quality_report.get('evidence_coverage', 0) * 100:.1f}%",
        f"Inferred coverage: {quality_report.get('inferred_coverage', 0) * 100:.1f}%",
        f"Accounted coverage: {quality_report.get('accounted_coverage', 0) * 100:.1f}%",
        f"Source verification: {source.get('status', 'not-checked')}",
    ]
    if errors:
        lines.append("Errors:")
        lines.extend([f"- {error}" for error in errors])
    lines.append("Warnings:")
    lines.extend([f"- {warning}" for warning in warnings] if warnings else ["- none"])
    return "\n".join(lines)


def validate_file(path):
    route_path = Path(path).resolve()
    route = load_route(route_path)
    errors, warnings, report = validate(route, route_path=route_path)
    return route, errors, warnings, report
