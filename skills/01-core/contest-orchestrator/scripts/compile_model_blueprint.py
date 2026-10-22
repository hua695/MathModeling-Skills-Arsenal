#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compile a typed model blueprint into a reviewable shadow contract report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

try:
    import yaml
except Exception:
    yaml = None

MODEL_FAMILIES = {
    "mechanistic": ["mechanism_mapping", "formula_derivation"],
    "optimization": ["decision_variables", "objective", "constraints", "feasibility_check"],
    "prediction": ["preprocessing", "data_split", "baseline", "metrics"],
    "evaluation": ["indicator_meaning", "normalization", "weight_source", "ranking_rule"],
    "dynamics": ["state_equation", "initial_boundary", "numerical_method"],
}
MODIFIERS = {"uncertainty", "robustness", "multiobjective", "inverse_identification",
             "nonlinear_fitting", "simulation"}
COMPOSITION_MODES = {"alternative", "sequential", "joint", "validation"}


def load_yaml(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("缺少 PyYAML，无法读取 model_blueprint.yaml")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("model_blueprint.yaml 根节点必须是 mapping")
    return payload


def discover(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).resolve()
    candidates = [root / "model_blueprint.yaml", root / "03_文档" / "model_blueprint.yaml",
                  root / "03_文档" / "paper" / "model_blueprint.yaml"]
    return next((path for path in candidates if path.exists()), None)


def discover_contract(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).resolve()
    candidates = [root / "model_contract.yaml", root / "model_evidence_card.yaml",
                  root / "03_文档" / "model_contract.yaml",
                  root / "03_文档" / "paper" / "model_contract.yaml"]
    return next((path for path in candidates if path.exists()), None)


def _contract_binding_issues(root: Path, compiled: list[dict], contract: Path | None) -> list[str]:
    """Ensure a typed blueprint cannot silently bypass the paper evidence contract."""
    if contract is None:
        return ["存在 model_blueprint.yaml，但缺少 model_contract.yaml，模型蓝图无法绑定正文证据"]
    try:
        payload = load_yaml(contract)
    except Exception as exc:
        return [f"无法读取模型证据契约: {exc}"]
    items = payload.get("subproblems")
    if not isinstance(items, list):
        return ["model_contract.yaml 缺少 subproblems，无法绑定模型蓝图"]
    by_id = {str(item.get("id", "")): item for item in items if isinstance(item, dict)}
    issues = []
    for item in compiled:
        qid = item["id"]
        contract_item = by_id.get(qid)
        if not contract_item:
            issues.append(f"{qid} 在 model_blueprint.yaml 中声明但未在 model_contract.yaml 出现")
            continue
        evidence = contract_item.get("evidence") if isinstance(contract_item.get("evidence"), dict) else {}
        declared = set(str(key) for key in evidence)
        missing = sorted(set(item["required_evidence"]) - declared)
        if missing:
            issues.append(f"{qid} 蓝图要求的证据未在契约声明: {', '.join(missing)}")
    blueprint_ids = {item["id"] for item in compiled}
    extra = sorted(set(by_id) - blueprint_ids)
    if extra:
        issues.append("model_contract.yaml 含蓝图未声明的子问题: " + ", ".join(extra))
    return issues


def validate(payload: dict, blueprint: Path, contract: Path | None = None) -> dict:
    report = {"schema_version": "1.0", "passed": True, "gate_status": "PASS",
              "issues": [], "warnings": [], "subproblems": [], "blueprint": str(blueprint)}
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    composition = project.get("composition")
    if composition not in {"single", "hybrid"}:
        report["issues"].append("project.composition 必须是 single 或 hybrid")
    items = payload.get("subproblems")
    if not isinstance(items, list) or not items:
        report["issues"].append("model_blueprint.yaml 缺少非空 subproblems")
        return _finish(report)
    ids = [str(item.get("id", "")) for item in items if isinstance(item, dict)]
    if len(ids) != len(set(ids)) or any(not item.startswith("Q") for item in ids):
        report["issues"].append("subproblems.id 必须唯一并使用 Qn 格式")
    expected = project.get("expected_subproblems")
    if isinstance(expected, list) and set(map(str, expected)) != set(ids):
        report["issues"].append("project.expected_subproblems 与 subproblems.id 不一致")
    compiled = []
    for item in items:
        if not isinstance(item, dict):
            report["issues"].append("subproblems 存在非 mapping 项")
            continue
        qid = str(item.get("id", ""))
        models = item.get("models")
        if not isinstance(models, list) or not models:
            report["issues"].append(f"{qid} 缺少 models")
            continue
        model_ids, families, requirements = set(), [], []
        for model in models:
            if not isinstance(model, dict):
                report["issues"].append(f"{qid} 存在非 mapping 模型节点")
                continue
            model_id, family = str(model.get("id", "")), str(model.get("family", ""))
            if not model_id or model_id in model_ids:
                report["issues"].append(f"{qid} 模型节点 id 缺失或重复: {model_id}")
            model_ids.add(model_id)
            if family not in MODEL_FAMILIES:
                report["issues"].append(f"{qid}/{model_id} 未知模型 family: {family}")
                continue
            families.append(family)
            requirements.extend(MODEL_FAMILIES[family])
            for modifier in model.get("modifiers", []) or []:
                modifier = str(modifier)
                if modifier not in MODIFIERS:
                    report["issues"].append(f"{qid}/{model_id} 未注册 modifier: {modifier}")
                elif modifier == "multiobjective" and family != "optimization":
                    report["issues"].append(f"{qid}/{model_id} multiobjective 只能修饰 optimization")
        mode = item.get("composition_mode")
        if len(set(families)) > 1:
            if mode not in COMPOSITION_MODES:
                report["issues"].append(f"{qid} 多模型节点必须声明 composition_mode")
            if mode in {"sequential", "joint"} and not item.get("connections"):
                report["issues"].append(f"{qid} 的 {mode} 组合必须声明 connections")
        compiled.append({"id": qid, "families": families, "required_evidence": list(dict.fromkeys(requirements)),
                         "composition_mode": mode or "single", "model_ids": sorted(model_ids)})
    report["subproblems"] = compiled
    report["compiled_contract"] = {"composition": composition, "subproblems": compiled}
    report["contract"] = str(contract) if contract else None
    report["issues"].extend(_contract_binding_issues(blueprint.parent, compiled, contract))
    return _finish(report)


def _finish(report: dict) -> dict:
    if report["issues"]:
        report["passed"] = False
        report["gate_status"] = "BLOCK"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--blueprint", default=None)
    parser.add_argument("--contract", default=None, help="模型证据契约；默认自动发现")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    blueprint = discover(root, args.blueprint)
    contract = discover_contract(root, args.contract)
    if blueprint is None:
        report = {"schema_version": "1.0", "passed": not args.strict,
                  "gate_status": "BLOCK" if args.strict else "WARN",
                  "issues": ["缺少 model_blueprint.yaml（影子编译器输入）"] if args.strict else [],
                  "warnings": [] if args.strict else ["缺少 model_blueprint.yaml（影子模式未执行）"]}
    else:
        try:
            report = validate(load_yaml(blueprint), blueprint, contract)
        except Exception as exc:
            report = {"schema_version": "1.0", "passed": False, "gate_status": "BLOCK",
                      "issues": [str(exc)], "warnings": [], "blueprint": str(blueprint)}
    if report.get("issues") and not args.strict:
        report["warnings"] = list(report.get("warnings", [])) + list(report["issues"])
        report["issues"] = []
        report["passed"] = True
        report["gate_status"] = "WARN"
    out = Path(args.out).resolve() if args.out else root / "model_blueprint_compile_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
