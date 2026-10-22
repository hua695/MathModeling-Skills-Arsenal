#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the v2 figure provenance registry used by delivery gates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_FORMATS = {"png", "svg"}
IMAGE_KINDS = {"data", "chart", "plot", "flow", "flowchart", "schematic", "drawio"}
DATA_GENERATORS = {"modelviz"}
FLOW_GENERATORS = {"tech-route-maker"}
SCHEMATIC_GENERATORS = {"tikz-scientific-figures"}
DRAWIO_GENERATORS = {"drawio-diagram"}
FLOW_ROLES = {"problem_analysis_flowchart", "technical_roadmap"}
LAYOUT_MODES = {"single", "side_by_side", "wrap_short", "tall_constrained"}
LAYOUT_VARIANTS = {"table_text", "figure_text", "algorithm_flow"}
WRAP_SIDES = {"left", "right"}
TEMPLATE_STATUSES = {"native", "external_adapted", "custom_required"}


def layout_validation_errors(key: str, item: dict) -> list[str]:
    """Validate page-layout metadata without changing figure-generation metadata."""
    errors: list[str] = []
    prefix = f"{key}: "
    mode = item.get("layout_mode")
    if not isinstance(mode, str) or not mode.strip():
        return [prefix + "missing layout_mode"]
    mode = mode.strip().lower()
    if mode not in LAYOUT_MODES:
        return [prefix + f"invalid layout_mode: {mode}"]
    if mode == "side_by_side":
        group = item.get("layout_group")
        if not isinstance(group, str) or not group.strip():
            errors.append(prefix + "side_by_side requires layout_group")
        variant = item.get("layout_variant")
        if variant not in LAYOUT_VARIANTS:
            errors.append(prefix + "side_by_side requires layout_variant=table_text, figure_text, or algorithm_flow")
    elif mode == "wrap_short":
        side = item.get("wrap_side")
        if side not in WRAP_SIDES:
            errors.append(prefix + "wrap_short requires wrap_side=left or right")
    elif mode == "tall_constrained":
        max_height = item.get("max_height")
        if not isinstance(max_height, str) or not max_height.strip():
            errors.append(prefix + "tall_constrained requires max_height")
    return errors


def entries_from(data):
    entries = data.get("figures", data) if isinstance(data, dict) else data
    if isinstance(entries, list):
        entries = {str(item.get("id", i)): item for i, item in enumerate(entries) if isinstance(item, dict)}
    return entries if isinstance(entries, dict) else {}


def validate(registry: Path, workspace: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"passed": False, "errors": [f"registry parse error: {exc}"], "warnings": []}
    if isinstance(data, dict) and data.get("schema_version") not in {"2.0", 2.0}:
        errors.append("registry schema_version must be 2.0; run migrate_figure_registry.py for legacy files")
    entries = entries_from(data)
    if not entries:
        errors.append("registry contains no figure entries")
    for key, item in entries.items():
        if not isinstance(item, dict):
            errors.append(f"{key}: metadata must be an object")
            continue
        kind = str(item.get("kind", item.get("type", ""))).lower()
        generator = str(item.get("generator", item.get("generated_by", ""))).lower()
        generation_route = str(item.get("generation_route", "")).lower().strip()
        template_status = str(item.get("template_status", "")).lower().strip()
        sources = item.get("source_files", item.get("data_source", []))
        if isinstance(sources, str):
            sources = [item.strip() for item in sources.replace("；", ",").split(",") if item.strip()]
        required = {"kind": kind, "generator": generator, "source_files": sources,
                    "script": item.get("script"), "formats": item.get("formats"), "qa_status": item.get("qa_status")}
        if kind in IMAGE_KINDS:
            required["insertion_format"] = item.get("insertion_format")
            errors.extend(layout_validation_errors(key, item))
        if kind in {"data", "chart", "plot"}:
            required["semantic_qa"] = item.get("semantic_qa")
            required["decision_card"] = item.get("decision_card")
            required["decision_author"] = item.get("decision_author")
        for field, value in required.items():
            if not value:
                errors.append(f"{key}: missing {field}")
        if generation_route and generation_route != generator:
            errors.append(f"{key}: generation_route must match generator")
        if template_status and template_status not in TEMPLATE_STATUSES:
            errors.append(f"{key}: invalid template_status")
        if kind in {"data", "chart", "plot"} and generator not in DATA_GENERATORS:
            errors.append(f"{key}: data figure must use generator=modelviz")
        if kind in {"flow", "flowchart"} and generator not in FLOW_GENERATORS:
            errors.append(f"{key}: flowchart generator must be tech-route-maker")
        if kind == "schematic" and generator not in SCHEMATIC_GENERATORS:
            errors.append(f"{key}: schematic generator must be tikz-scientific-figures")
        if kind == "drawio" and generator not in DRAWIO_GENERATORS:
            errors.append(f"{key}: Draw.io artifact must use generator=drawio-diagram")
        if kind in {"data", "chart", "plot"} and item.get("semantic_qa") != "scipilot-figure-skill":
            errors.append(f"{key}: data figure must record semantic_qa=scipilot-figure-skill")
        if kind in {"data", "chart", "plot"} and item.get("decision_author") != "scipilot-figure-skill":
            errors.append(f"{key}: data figure must record decision_author=scipilot-figure-skill")
        if generator == "tech-route-maker":
            role = str(item.get("diagram_role", "")).lower()
            if role not in FLOW_ROLES:
                errors.append(f"{key}: tech-route-maker requires diagram_role=problem_analysis_flowchart or technical_roadmap")
            script = str(item.get("script", ""))
            if not script.lower().endswith(".json"):
                errors.append(f"{key}: tech-route-maker script must retain tech-route.json source")
            formats = {str(value).lower() for value in item.get("formats", []) or []}
            if formats != {"png", "svg"}:
                errors.append(f"{key}: tech-route-maker image outputs must be exactly SVG and PNG")
        if generator == "tikz-scientific-figures" and not str(item.get("script", "")).lower().endswith(".tex"):
            errors.append(f"{key}: tikz-scientific-figures script must retain .tex source")
        if generator == "drawio-diagram" and item.get("user_requested") is not True:
            errors.append(f"{key}: Draw.io artifact requires user_requested=true")
        formats = {str(value).lower() for value in item.get("formats", []) or []}
        if kind in IMAGE_KINDS:
            if str(item.get("insertion_format", "")).lower() != "svg":
                errors.append(f"{key}: image insertion_format must be SVG")
            if formats != {"svg", "png"}:
                errors.append(f"{key}: image formats must be exactly SVG and PNG; PDF is not allowed")
        for fmt in item.get("formats", []) or []:
            if str(fmt).lower() not in ALLOWED_FORMATS:
                errors.append(f"{key}: unsupported format {fmt}")
        if item.get("qa_status") not in {"pass", "reviewed"}:
            errors.append(f"{key}: qa_status must be pass or reviewed")
        for source in sources or []:
            candidate = workspace / str(source)
            if not candidate.exists():
                errors.append(f"{key}: source file not found: {source}")
        script = item.get("script")
        if script:
            script_path = workspace / str(script)
            if not script_path.exists():
                errors.append(f"{key}: plotting script not found: {script}")
        decision_card = item.get("decision_card")
        if decision_card:
            decision_card_path = workspace / str(decision_card)
            if not decision_card_path.exists():
                errors.append(f"{key}: decision card not found: {decision_card}")
    return {"schema_version": data.get("schema_version") if isinstance(data, dict) else None,
            "count": len(entries), "passed": not errors, "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--workspace", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()
    registry = args.registry.resolve()
    workspace = (args.workspace or registry.parent).resolve()
    if not registry.exists():
        report = {"passed": False, "errors": [f"missing registry: {registry}"], "warnings": []}
    else:
        report = validate(registry, workspace)
    if args.strict and report.get("warnings"):
        report["errors"] = report.get("errors", []) + report["warnings"]
        report["warnings"] = []
        report["passed"] = False
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
