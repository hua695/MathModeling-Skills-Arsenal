from collections import Counter

from .schema import ROUTE_VERSION, domain_context_missing_fields, domain_context_status, selected_output_formats


def iter_nodes(route):
    for stage in route.get("stages") or []:
        for node in stage.get("nodes") or []:
            yield stage, node


def declared_source_ids(route):
    source_ids = set()
    for index, source in enumerate((route.get("metadata") or {}).get("source_files") or [], start=1):
        if isinstance(source, dict):
            source_ids.add(str(source.get("id") or source.get("source_id") or f"source_{index}"))
    return source_ids


def valid_evidence_item(item, source_ids=None):
    if not isinstance(item, dict):
        return False
    if item.get("kind") != "source":
        return False
    source_id = str(item.get("source_id") or "")
    if not source_id or (source_ids is not None and source_id not in source_ids):
        return False
    if not str(item.get("locator") or "").strip():
        return False
    if not str(item.get("quote_or_note") or "").strip():
        return False
    return True


def _has_evidence(node, source_ids=None):
    evidence = node.get("evidence")
    return isinstance(evidence, list) and any(valid_evidence_item(item, source_ids) for item in evidence)


def _assumption_node_ids(route):
    linked = set()
    for assumption in route.get("assumptions") or []:
        if not isinstance(assumption, dict):
            continue
        for node_id in assumption.get("node_ids") or []:
            linked.add(node_id)
    return linked


def build_quality_report(
    route,
    source_verification=None,
    verified_evidence_node_ids=None,
    evidence_issues=None,
):
    stages = route.get("stages") or []
    nodes = list(iter_nodes(route))
    edges = route.get("edges") or []
    node_count = len(nodes)
    source_ids = declared_source_ids(route)
    assumption_node_ids = _assumption_node_ids(route)

    if verified_evidence_node_ids is None:
        evidence_node_ids = {
            node.get("id") for _, node in nodes if _has_evidence(node, source_ids)
        }
    else:
        evidence_node_ids = set(verified_evidence_node_ids)
    evidence_nodes = [node for _, node in nodes if node.get("id") in evidence_node_ids]
    inferred_nodes = [node for _, node in nodes if node.get("is_inferred") is True]
    linked_inferred_nodes = [
        node for node in inferred_nodes if node.get("id") in assumption_node_ids
    ]
    unlinked_inferred_nodes = [
        node.get("id", "") for node in inferred_nodes if node.get("id") not in assumption_node_ids
    ]
    missing_evidence_nodes = [
        node.get("id", "")
        for _, node in nodes
        if node.get("id") not in evidence_node_ids and node.get("is_inferred") is not True
    ]
    long_label_nodes = [
        node.get("id", "")
        for _, node in nodes
        if len(str(node.get("label") or "")) > 42
    ]
    stages_with_too_many_nodes = [
        stage.get("id", "") for stage in stages if len(stage.get("nodes") or []) > 6
    ]
    stages_with_too_few_nodes = [
        stage.get("id", "") for stage in stages if len(stage.get("nodes") or []) < 2
    ]
    confidence_counts = Counter(str(node.get("confidence") or "missing") for _, node in nodes)
    domain_status = domain_context_status(route)
    missing_domain_fields = domain_context_missing_fields(route)
    evidence_issues = list(evidence_issues or [])
    source_verification = source_verification or {
        "status": "not-checked",
        "declared_count": len(source_ids),
        "verified_count": 0,
        "missing_sources": [],
        "unhashed_sources": [],
        "hash_mismatches": [],
        "duplicate_source_ids": [],
        "records": [],
    }

    warnings = []
    if domain_status == "missing":
        warnings.append("Missing domain_context; ask for discipline and field-specific constraints before final rendering.")
    elif missing_domain_fields:
        warnings.append(f"Incomplete domain_context; missing: {', '.join(missing_domain_fields)}")
    if len(stages) < 4:
        warnings.append("Route has fewer than 4 stages; a technical route may be underspecified.")
    if len(stages) > 7:
        warnings.append("Route has more than 7 stages; consider grouping stages for readability.")
    for stage_id in stages_with_too_many_nodes:
        warnings.append(f"Stage has more than 6 nodes: {stage_id}")
    for stage_id in stages_with_too_few_nodes:
        warnings.append(f"Stage has fewer than 2 nodes: {stage_id}")
    for node_id in long_label_nodes:
        warnings.append(f"Long visible label: {node_id}")
    for node_id in missing_evidence_nodes:
        warnings.append(f"Node has no verified evidence and is not marked inferred: {node_id}")
    for node_id in unlinked_inferred_nodes:
        warnings.append(f"Inferred node is not linked from assumptions: {node_id}")
    if node_count and len(evidence_nodes) < node_count:
        warnings.append("Evidence coverage is below 100%; inferred nodes are reported separately and do not count as evidence.")
    if source_verification.get("status") != "verified":
        warnings.append(f"Source verification status: {source_verification.get('status', 'not-checked')}")
    warnings.extend(evidence_issues)

    evidence_coverage = len(evidence_nodes) / node_count if node_count else 0.0
    inferred_coverage = len(inferred_nodes) / node_count if node_count else 0.0
    accounted_ids = evidence_node_ids | {node.get("id") for node in linked_inferred_nodes}
    accounted_coverage = len(accounted_ids) / node_count if node_count else 0.0

    return {
        "route_version": route.get("route_version") or ROUTE_VERSION,
        "selected_preset": route.get("selected_preset") or "custom",
        "selected_output_formats": selected_output_formats(route),
        "domain_context_status": domain_status,
        "domain_context_missing_fields": missing_domain_fields,
        "domain_context": route.get("domain_context") if isinstance(route.get("domain_context"), dict) else {},
        "stage_count": len(stages),
        "node_count": node_count,
        "edge_count": len(edges),
        "evidence_node_count": len(evidence_nodes),
        "evidence_coverage": round(evidence_coverage, 4),
        "inferred_node_count": len(inferred_nodes),
        "inferred_coverage": round(inferred_coverage, 4),
        "linked_inferred_node_count": len(linked_inferred_nodes),
        "unlinked_inferred_nodes": unlinked_inferred_nodes,
        "accounted_coverage": round(accounted_coverage, 4),
        "unresolved_question_count": len(route.get("unresolved_questions") or []),
        "long_label_nodes": long_label_nodes,
        "stages_with_too_many_nodes": stages_with_too_many_nodes,
        "stages_with_too_few_nodes": stages_with_too_few_nodes,
        "missing_evidence_nodes": missing_evidence_nodes,
        "evidence_issues": evidence_issues,
        "source_verification": source_verification,
        "confidence_summary": dict(confidence_counts),
        "warnings": warnings,
        "suggested_manual_review": [
            "Check whether the diagram matches the stated discipline, subfield, research object, method family, constraints, and metrics.",
            "Check every technical term and evidence locator against the authoritative source.",
            "Replace or approve inferred nodes before treating the diagram as final.",
            "Check edge labels, route logic, spacing, text wrapping, and final deliverables.",
            "Edit the PPTX, SVG, or Draw.io output before publication; generated files are editable drafts.",
        ],
    }


def render_quality_report_markdown(report):
    evidence_coverage = report.get("evidence_coverage", 0.0) * 100
    inferred_coverage = report.get("inferred_coverage", 0.0) * 100
    accounted_coverage = report.get("accounted_coverage", 0.0) * 100
    source = report.get("source_verification") or {}
    lines = [
        "# Quality Report",
        "",
        "## Summary",
        "",
        f"- Route version: {report.get('route_version', '')}",
        f"- Selected preset: {report.get('selected_preset', '')}",
        f"- Output formats: {', '.join(report.get('selected_output_formats') or []) or 'not recorded'}",
        f"- Domain context: {report.get('domain_context_status', 'missing')}",
        f"- Stage count: {report.get('stage_count', 0)}",
        f"- Node count: {report.get('node_count', 0)}",
        f"- Edge count: {report.get('edge_count', 0)}",
        f"- Evidence coverage: {evidence_coverage:.1f}%",
        f"- Inferred coverage: {inferred_coverage:.1f}%",
        f"- Accounted coverage: {accounted_coverage:.1f}%",
        f"- Source verification: {source.get('status', 'not-checked')}",
        f"- Unresolved questions: {report.get('unresolved_question_count', 0)}",
        "",
        "## Structural Checks",
        "",
        f"- [{'x' if 4 <= report.get('stage_count', 0) <= 7 else ' '}] Main route has 4-7 stages.",
        f"- [{'x' if not report.get('stages_with_too_many_nodes') else ' '}] Each stage has at most 6 visible nodes.",
        f"- [{'x' if not report.get('long_label_nodes') else ' '}] Node labels are concise.",
        f"- [{'x' if report.get('domain_context_status') == 'complete' else ' '}] Domain context is complete.",
        "- [x] Edges connect existing nodes after validation.",
        "",
        "## Evidence Checks",
        "",
        f"- Verified source files: {source.get('verified_count', 0)}/{source.get('declared_count', 0)}",
        f"- Nodes with verified evidence: {report.get('evidence_node_count', 0)}",
        f"- Nodes marked as inferred: {report.get('inferred_node_count', 0)}",
        f"- Inferred nodes linked to assumptions: {report.get('linked_inferred_node_count', 0)}",
        f"- Nodes missing evidence: {len(report.get('missing_evidence_nodes') or [])}",
        f"- Evidence locator issues: {len(report.get('evidence_issues') or [])}",
        f"- Missing domain fields: {', '.join(report.get('domain_context_missing_fields') or []) or 'none'}",
        "",
        "## Layout Checks",
        "",
        f"- Long labels: {', '.join(report.get('long_label_nodes') or []) or 'none'}",
        f"- Dense stages: {', '.join(report.get('stages_with_too_many_nodes') or []) or 'none'}",
        "",
        "## Warnings",
        "",
    ]
    warnings = report.get("warnings") or []
    lines.extend([f"- {warning}" for warning in warnings] if warnings else ["- none"])
    lines.extend(["", "## Suggested Manual Review", ""])
    lines.extend([f"- {item}" for item in report.get("suggested_manual_review") or []])
    lines.append("")
    return "\n".join(lines)
