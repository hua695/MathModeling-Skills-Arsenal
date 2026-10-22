#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build or validate a capability-driven appendix plan.

The planner never invents source files or results.  With an existing
``appendix_plan.yaml`` it validates the declared plan; otherwise it can derive
a DRAFT from ``model_blueprint.yaml`` and leaves material paths empty for the
project owner/agent to fill after the actual run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - the skill already uses PyYAML elsewhere
    yaml = None

CODE_CAPABILITIES = {"code", "numerical_fitting", "numerical_simulation", "machine_learning",
                     "optimization_solver"}
CODE_APPENDIX_MODES = {"not_applicable", "core_only", "full_source"}
FAMILY_CAPABILITIES = {
    "mechanistic": {"derivation"},
    "optimization": {"optimization"},
    "prediction": {"prediction"},
    "evaluation": {"evaluation"},
    "dynamics": {"simulation", "derivation"},
}
MODULE_ORDER = ["support_index", "source_code", "derivation", "algorithm", "optimization",
                "prediction", "evaluation", "simulation", "raw_data", "auxiliary_validation", "interface"]


def load_mapping(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        value = json.loads(raw)
    elif yaml is not None:
        value = yaml.safe_load(raw)
    else:
        raise RuntimeError("读取 YAML 需要 PyYAML；也可以提供 JSON 计划")
    if not isinstance(value, dict):
        raise ValueError(f"计划必须是对象: {path}")
    return value


def find_manifest(root: Path, names: tuple[str, ...]) -> Path | None:
    for search_root in (root, root / "01_需求与规划", root / "paper"):
        for name in names:
            candidate = search_root / name
            if candidate.exists():
                return candidate
    return None


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def capabilities_from_blueprint(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for subproblem in blueprint.get("subproblems", []):
        caps: set[str] = set()
        for model in subproblem.get("models", []):
            caps.update(FAMILY_CAPABILITIES.get(str(model.get("family", "")), set()))
            for modifier in model.get("modifiers", []) or []:
                name = str(modifier).strip().lower().replace("-", "_")
                if name in CODE_CAPABILITIES or name in {"uncertainty", "robustness", "interface", "raw_data"}:
                    caps.add(name)
        result.append({"id": subproblem.get("id"), "primary_type": subproblem.get("models", [{}])[0].get("family", "unknown"),
                       "capabilities": sorted(caps), "result_sources": []})
    return result


def build_draft(root: Path) -> dict[str, Any]:
    blueprint_path = find_manifest(root, ("model_blueprint.yaml", "model_blueprint.yml", "model_blueprint.json"))
    subproblems = capabilities_from_blueprint(load_mapping(blueprint_path)) if blueprint_path else []
    capabilities = {cap for item in subproblems for cap in item["capabilities"]}
    modules: list[dict[str, Any]] = []
    used_by: dict[str, list[str]] = {}
    for item in subproblems:
        for cap in item["capabilities"]:
            kind = "source_code" if cap in CODE_CAPABILITIES else (
                "auxiliary_validation" if cap in {"uncertainty", "robustness"} else cap)
            used_by.setdefault(kind, []).append(item["id"])
    for kind in sorted(used_by, key=lambda value: (MODULE_ORDER.index(value) if value in MODULE_ORDER else 99, value)):
        modules.append({"module_id": f"app-{kind}", "kind": kind, "used_by": sorted(set(used_by[kind])),
                        "required": True, "source_files": [], "paper_anchor": f"app:{kind}",
                        "include_in_pdf": True, "paper_role": "core_code" if kind == "source_code" else kind,
                        "support_materials": []})
    program_used = bool(capabilities & CODE_CAPABILITIES)
    return {
        "schema_version": "2.0", "status": "DRAFT", "problem_profile": "hybrid" if len(subproblems) > 1 else "single",
        "official_format": {"numbering": "official_abc_if_required", "appendix_ids": [], "order": MODULE_ORDER},
        "subproblems": subproblems, "appendix_modules": modules,
        "source_inputs": {"program_used": program_used,
                           "appendix_code_mode": "core_only" if program_used else "not_applicable",
                           "core_source_files": [], "full_source_files": [], "support_source_files": [],
                           "long_derivation_files": [], "raw_data_files": [], "support_material_files": []},
        "planning_source": str(blueprint_path) if blueprint_path else None,
    }


def validate(plan: dict[str, Any]) -> list[str]:
    errors = []
    if plan.get("schema_version") != "2.0":
        errors.append("schema_version 必须为 2.0")
    subproblems = plan.get("subproblems")
    modules = plan.get("appendix_modules")
    if not isinstance(subproblems, list) or not subproblems:
        errors.append("subproblems 不能为空")
    if not isinstance(modules, list):
        errors.append("appendix_modules 必须是列表")
    module_items = modules if isinstance(modules, list) else []
    ids = [item.get("module_id") for item in module_items if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("appendix_modules 存在重复 module_id")
    known_q = {item.get("id") for item in subproblems or [] if isinstance(item, dict)}
    for module in module_items:
        if not isinstance(module, dict):
            errors.append("appendix_modules 含非对象项")
            continue
        unknown = sorted(set(module.get("used_by", [])) - known_q)
        if unknown:
            errors.append(f"模块 {module.get('module_id')} 绑定了未知子问题: {unknown}")
        if module.get("required") and not module.get("paper_anchor"):
            errors.append(f"必填模块 {module.get('module_id')} 缺少 paper_anchor")
    if plan.get("planning_contract") == "coverage_first":
        matrix = plan.get("coverage_matrix")
        if not isinstance(matrix, list) or not matrix:
            errors.append("coverage_first 附录计划必须提供 coverage_matrix")
        else:
            by_question: dict[str, dict[str, Any]] = {}
            for row in matrix:
                if not isinstance(row, dict):
                    errors.append("coverage_matrix 含非对象项")
                    continue
                qid = row.get("subproblem_id")
                if qid not in known_q:
                    errors.append(f"coverage_matrix 绑定了未知子问题: {qid}")
                    continue
                if qid in by_question:
                    errors.append(f"coverage_matrix 重复登记子问题: {qid}")
                    continue
                if not row.get("main_section"):
                    errors.append(f"{qid} 缺少正文主章节锚点 main_section")
                by_question[str(qid)] = row
            missing_q = sorted(str(qid) for qid in known_q if qid not in by_question)
            if missing_q:
                errors.append("coverage_matrix 未覆盖子问题: " + ", ".join(missing_q))
            module_ids = set(ids)
            source = plan.get("source_inputs") if isinstance(plan.get("source_inputs"), dict) else {}
            program_used = bool(source.get("program_used"))
            for qid, row in by_question.items():
                for field in ("core_code_module", "long_derivation_module", "verification_module"):
                    module_id = row.get(field)
                    if module_id and module_id not in module_ids:
                        errors.append(f"{qid}.{field} 指向不存在模块: {module_id}")
                if program_used and not row.get("core_code_module") and not row.get("code_not_applicable_reason"):
                    errors.append(f"{qid} 使用程序时必须登记 core_code_module 或 code_not_applicable_reason")

    source = plan.get("source_inputs") if isinstance(plan.get("source_inputs"), dict) else {}
    program_used = bool(source.get("program_used"))
    mode_raw = source.get("appendix_code_mode")
    mode = str(mode_raw).strip().lower() if mode_raw is not None else None
    if mode is not None and mode not in CODE_APPENDIX_MODES:
        errors.append("source_inputs.appendix_code_mode 必须为 not_applicable、core_only 或 full_source")

    core_sources = set(as_list(source.get("core_source_files")))
    full_sources = set(as_list(source.get("full_source_files")))
    support_sources = set(as_list(source.get("support_source_files")))
    support_materials = set(as_list(source.get("support_material_files")))
    for module in module_items:
        if not isinstance(module, dict):
            continue
        kind = str(module.get("kind", "")).strip().lower()
        if kind in {"source_code", "code"} and module.get("include_in_pdf", True) is not False:
            core_sources.update(as_list(module.get("source_files")))
        if kind in {"source_code", "code"} and program_used and module.get("include_in_pdf") is False:
            errors.append(f"程序题核心代码模块 {module.get('module_id')} 必须 include_in_pdf: true")

    # A new READY/FINAL plan must distinguish the readable core code shown in
    # the paper from the complete runnable source retained in the support
    # package.  DRAFTs stay discoverable and may leave paths empty.
    if program_used and str(plan.get("status", "DRAFT")).upper() in {"READY", "FINAL"}:
        if mode is None:
            errors.append("程序题正式附录计划必须声明 source_inputs.appendix_code_mode")
        elif mode == "not_applicable":
            errors.append("程序题不能将 appendix_code_mode 设为 not_applicable")
        if not core_sources:
            errors.append("程序题正式附录计划必须提供 core_source_files 或核心代码模块 source_files")
        if not full_sources:
            errors.append("程序题正式附录计划必须提供完整的 full_source_files")
        for module in module_items:
            if not isinstance(module, dict):
                continue
            if (str(module.get("kind", "")).strip().lower() in {"source_code", "code"}
                    and module.get("required", False)
                    and module.get("include_in_pdf", True) is not False
                    and not as_list(module.get("source_files"))):
                errors.append(f"核心代码模块 {module.get('module_id')} 必须登记 source_files")
        missing_full = sorted(core_sources - full_sources)
        if missing_full:
            errors.append("core_source_files 必须属于 full_source_files: " + ", ".join(missing_full))
        if not support_sources:
            support_sources = full_sources & support_materials
        missing_support = sorted(full_sources - support_sources)
        if missing_support:
            errors.append("完整源码必须登记到 support_source_files 或 support_material_files: " + ", ".join(missing_support))
    elif not program_used and mode in {"core_only", "full_source"}:
        errors.append("未使用程序时 appendix_code_mode 必须为 not_applicable")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--out", default=None)
    parser.add_argument("--write", action="store_true", help="仅将缺失计划写入项目根目录；不会覆盖现有计划")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    existing = find_manifest(root, ("appendix_plan.yaml", "appendix_plan.yml", "appendix_plan.json"))
    plan = load_mapping(existing) if existing else build_draft(root)
    errors = validate(plan)
    warnings: list[str] = []
    if existing is None and not plan.get("subproblems"):
        # A planner run without a model blueprint is a useful discovery result,
        # not a formal failure; the appendix gate will still require a READY
        # plan before strict delivery.
        errors = []
        warnings.append("未发现 model_blueprint.yaml；仅输出空白 DRAFT，不能进入正式交付")
    if args.write and existing is None:
        target = root / "appendix_plan.yaml"
        if yaml is None:
            target = root / "appendix_plan.json"
            target.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            target.write_text(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False), encoding="utf-8")
        plan["written_to"] = str(target)
    plan_status = str(plan.get("status", "DRAFT")).upper()
    report_status = "BLOCK" if errors else ("DRAFT" if existing is None or plan_status == "DRAFT" else "READY")
    report = {"schema_version": "1.0", "status": report_status,
              "plan_path": str(existing) if existing else None, "errors": errors, "warnings": warnings, "plan": plan}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        output = Path(args.out).resolve(); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
