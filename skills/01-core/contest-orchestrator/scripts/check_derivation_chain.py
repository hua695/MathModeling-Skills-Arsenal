#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check the auditable derivation registry for key modeling equations."""
from __future__ import annotations

import argparse
import json
import re
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

from check_modeling_contract import expand_inputs, locate_tex


def discover_registry(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).resolve()
    candidates = [root / "derivation_registry.yaml", root / "01_需求与规划" / "derivation_registry.yaml",
                  root / "03_文档" / "derivation_registry.yaml",
                  root / "03_文档" / "paper" / "derivation_registry.yaml"]
    return next((path for path in candidates if path.exists()), None)


def load_registry(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("缺少 PyYAML，无法读取 derivation_registry.yaml")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError("推导登记根节点必须是 mapping")
    return value


def tex_root(root: Path) -> Path:
    if list(root.glob("*.tex")):
        return root
    return next((candidate for candidate in (root / "03_文档" / "paper", root / "paper")
                 if candidate.is_dir()), root)


def _step_anchor(step: object) -> str:
    if isinstance(step, dict):
        return str(step.get("text_anchor", step.get("text", "")) or "")
    return str(step)


def _step_expression(step: object) -> str:
    if isinstance(step, dict):
        return str(step.get("expression", step.get("output_expr", "")) or "")
    return str(step)


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    visiting, visited = set(), set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(dep) for dep in graph.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def _source_exists(source: str, root: Path, registry_path: Path) -> bool:
    roots = [root.resolve(), registry_path.parent.resolve()]
    for candidate in ((root / source).resolve(), (registry_path.parent / source).resolve()):
        if candidate.exists() and any(candidate == base or base in candidate.parents for base in roots):
            return True
    return False


def validate(root: Path, registry_path: Path | None, strict: bool) -> dict:
    report = {"schema_version": "1.0", "strict": strict, "passed": True,
              "gate_status": "PASS", "issues": [], "warnings": [], "equations": []}
    if registry_path is None or not registry_path.exists():
        message = "缺少 derivation_registry.yaml（推导链登记）"
        (report["issues"] if strict else report["warnings"]).append(message)
        report["passed"] = not strict
        report["gate_status"] = "BLOCK" if strict else "WARN"
        return report
    try:
        payload = load_registry(registry_path)
        tex = locate_tex(tex_root(root))
        text = expand_inputs(tex.read_text(encoding="utf-8", errors="replace"), tex.parent)
    except Exception as exc:
        report["issues"].append(str(exc))
        report["passed"] = False
        report["gate_status"] = "BLOCK"
        return report
    equations = payload.get("equations")
    if not isinstance(equations, list) or not equations:
        report["issues"].append("derivation_registry.yaml 缺少非空 equations 列表")
        report["passed"] = False
        report["gate_status"] = "BLOCK"
        return report
    labels = set(re.findall(r"\\label\{([^{}]+)\}", text))
    equation_ids = {str(item.get("id", "")) for item in equations if isinstance(item, dict)}
    duplicate_ids = len(equation_ids) != len(equations)
    if duplicate_ids:
        report["issues"].append("equation id 必须唯一")
    positions = {str(item.get("id", "")): index for index, item in enumerate(equations)
                 if isinstance(item, dict)}
    graph = {str(item.get("id", "")): [str(dep) for dep in (item.get("depends_on", item.get("based_on", [])) or [])]
             for item in equations if isinstance(item, dict)}
    if _has_cycle(graph):
        report["issues"].append("公式依赖图存在环，推导顺序不可审计")
    for item in equations:
        if not isinstance(item, dict):
            report["issues"].append("equations 中存在非 mapping 项")
            continue
        eqid = str(item.get("id", ""))
        kind = str(item.get("kind", item.get("status", ""))).lower()
        label = str(item.get("tex_label", item.get("label", "")))
        depends = item.get("depends_on", item.get("based_on", [])) or []
        steps = item.get("derivation_steps", item.get("steps", [])) or []
        assumptions = item.get("assumptions", []) or []
        symbols = item.get("symbols", []) or []
        citations = item.get("citation_keys", item.get("citations", [])) or []
        source_files = item.get("source_files", item.get("code_reference", [])) or []
        if isinstance(source_files, str):
            source_files = [source_files]
        item_report = {"id": eqid, "kind": kind, "label": label,
                       "depends_on": depends, "steps": len(steps), "symbols": symbols}
        report["equations"].append(item_report)
        if not eqid or kind not in {"derived", "given", "cited", "definition"}:
            report["issues"].append(f"{eqid or '<missing>'} 缺少合法 kind（derived/given/cited/definition）")
        if not label:
            report["issues"].append(f"{eqid or '<missing>'} 缺少 label")
        if label and label not in labels:
            report["issues"].append(f"{eqid} 的 TeX 标签不存在: {label}")
        if kind == "derived":
            if len(depends) < 1:
                report["issues"].append(f"{eqid} 是 derived，但没有前置公式 depends_on")
            def meaningful_step(step: object) -> bool:
                if not isinstance(step, str):
                    return False
                value = step.strip()
                minimum = 2 if any("\u4e00" <= char <= "\u9fff" for char in value) else 4
                return len(value) >= minimum
            if len(steps) < 2 or any(not meaningful_step(step) for step in steps):
                report["issues"].append(f"{eqid} 的 derivation_steps 少于 2 步或存在空步骤")
            if not assumptions and re.search(r"近似|忽略|条件|边界", " ".join(map(str, steps))):
                report["issues"].append(f"{eqid} 使用近似/边界步骤但未登记 assumptions")
        if kind == "cited":
            if not citations:
                report["issues"].append(f"{eqid} 是 cited，但没有 citation_keys")
            elif not any(re.search(r"\\cite\{[^}]*" + re.escape(str(key)), text) for key in citations):
                report["issues"].append(f"{eqid} 的 citation_keys 未在正文出现: {citations}")
        for dep in depends:
            if str(dep) not in equation_ids:
                report["issues"].append(f"{eqid} 依赖不存在的公式: {dep}")
            elif positions.get(str(dep), -1) >= positions.get(eqid, len(equations)):
                report["issues"].append(f"{eqid} 依赖后置公式，推导顺序错误: {dep}")
        for step in steps:
            anchor = _step_anchor(step)
            expression = _step_expression(step)
            compact_step = re.sub(r"\s+", "", anchor)
            compact_text = re.sub(r"\s+", "", text)
            if isinstance(step, dict) and not anchor:
                report["issues"].append(f"{eqid} 的结构化步骤缺少 text_anchor")
            elif compact_step and compact_step not in compact_text:
                report["issues"].append(f"{eqid} 的推导步骤未在正文找到锚点: {anchor}")
            if isinstance(step, dict) and not expression:
                report["issues"].append(f"{eqid} 的结构化步骤缺少 expression")
        for source in source_files:
            if not _source_exists(str(source), root, registry_path):
                report["issues"].append(f"{eqid} 的来源文件不存在: {source}")
    registry_labels = {str(item.get("label", item.get("tex_label", ""))) for item in equations
                       if isinstance(item, dict)}
    unregistered = sorted(label for label in labels if label.startswith("eq:") and label not in registry_labels)
    if unregistered:
        report["issues"].append("存在未登记的 eq: 标签: " + ", ".join(unregistered))
    if report["issues"] and not strict:
        report["warnings"] = list(report["issues"])
        report["issues"] = []
        report["gate_status"] = "WARN"
    elif report["issues"]:
        report["passed"] = False
        report["gate_status"] = "BLOCK"
    report["registry"] = str(registry_path)
    report["tex"] = str(tex)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_or_paper")
    parser.add_argument("--registry", default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.project_or_paper).resolve()
    report = validate(root, discover_registry(root, args.registry), args.strict)
    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
