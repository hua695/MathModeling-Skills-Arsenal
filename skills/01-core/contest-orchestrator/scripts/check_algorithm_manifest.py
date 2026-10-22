#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate an opt-in algorithm configuration lock.

The manifest links each subproblem's declared algorithm and parameters to the
actual code/config files.  It never guesses values from arbitrary source text;
projects must provide explicit JSON pointers or Python constant names.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import re
import sys
from pathlib import Path

from check_modeling_contract import expand_inputs, locate_tex

try:
    import yaml
except Exception:
    yaml = None

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def _discover(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return (candidate if candidate.is_absolute() else root / candidate).resolve()
    for candidate in (root / "algorithm_manifest.yaml", root / "03_文档" / "algorithm_manifest.yaml",
                      root / "paper" / "algorithm_manifest.yaml"):
        if candidate.exists():
            return candidate.resolve()
    return None


def _load(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("缺少 PyYAML，无法读取 algorithm_manifest.yaml")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError("algorithm_manifest.yaml 根节点必须是 mapping")
    return value


def _safe(root: Path, raw: object) -> Path:
    candidate = Path(str(raw))
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"算法清单路径越出项目根目录: {raw}")
    return resolved


def _pointer(value: object, pointer: str) -> object:
    current = value
    for token in pointer.lstrip("/").split("/") if pointer and pointer != "/" else []:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            raise KeyError(pointer)
    return current


def _assignment(source: Path, variable: str) -> object:
    tree = ast.parse(source.read_text(encoding="utf-8", errors="replace"), filename=str(source))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == variable for target in node.targets):
            return ast.literal_eval(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == variable and node.value is not None:
            return ast.literal_eval(node.value)
    raise ValueError(f"代码文件未找到可解析的变量赋值: {variable}")


def _same(actual: object, expected: object, tolerance: float) -> bool:
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return math.isclose(float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance)
    return actual == expected


def _tex_text(root: Path) -> str:
    tex_root = root if list(root.glob("*.tex")) else (root / "paper" if (root / "paper").is_dir() else root)
    tex = locate_tex(tex_root)
    return expand_inputs(tex.read_text(encoding="utf-8", errors="replace"), tex.parent)


def validate(root: Path, manifest: Path | None, strict: bool = False) -> dict:
    report = {"schema_version": "1.0", "strict": strict, "passed": True,
              "gate_status": "PASS", "issues": [], "warnings": [], "subproblems": []}
    if manifest is None or not manifest.exists():
        report["info"] = ["未配置 algorithm_manifest.yaml，算法—配置锁未启用"]
        report["manifest"] = None
        return report
    try:
        payload = _load(manifest)
        tex = _tex_text(root)
    except Exception as exc:
        report.update({"passed": False, "gate_status": "BLOCK", "issues": [str(exc)],
                       "manifest": str(manifest)})
        return report
    required = bool(payload.get("required", False))
    items = payload.get("subproblems")
    if not isinstance(items, list) or not items:
        report["issues"].append("algorithm_manifest.yaml 的 subproblems 必须是非空列表")
        items = []
    seen: set[str] = set()
    for item in items:
        row = {"id": str(item.get("id", "")) if isinstance(item, dict) else "", "issues": [], "checks": {}}
        if not isinstance(item, dict):
            row["issues"].append("子问题条目不是 mapping")
            report["subproblems"].append(row)
            continue
        qid = row["id"].upper()
        if not re.fullmatch(r"Q[0-9]+", qid) or qid in seen:
            row["issues"].append(f"子问题 id 缺失、格式错误或重复: {qid}")
        seen.add(qid)
        algorithm = item.get("algorithm") if isinstance(item.get("algorithm"), dict) else {}
        name = str(algorithm.get("name", "")).strip()
        row["checks"]["name"] = bool(name) and name in tex
        if not row["checks"]["name"]:
            row["issues"].append(f"{qid} 算法名称未在正文中出现: {name or '<empty>'}")
        for raw in algorithm.get("code_sources", []) if isinstance(algorithm.get("code_sources"), list) else []:
            try:
                path = _safe(root, raw)
                if not path.is_file():
                    row["issues"].append(f"{qid} 算法代码来源不存在: {raw}")
            except Exception as exc:
                row["issues"].append(str(exc))
        parameters = algorithm.get("parameters") if isinstance(algorithm.get("parameters"), list) else []
        if not parameters:
            row["issues"].append(f"{qid} 算法锁缺少 parameters")
        for parameter in parameters:
            if not isinstance(parameter, dict):
                row["issues"].append(f"{qid} 算法参数不是 mapping")
                continue
            pname = str(parameter.get("name", "")).strip()
            if not pname or "expected" not in parameter:
                row["issues"].append(f"{qid} 算法参数必须包含 name 和 expected: {parameter}")
                continue
            source_raw = parameter.get("source_file")
            pointer = parameter.get("json_pointer")
            variable = parameter.get("code_variable")
            if not source_raw or not (pointer or variable):
                row["issues"].append(f"{qid} 参数 {pname} 缺少 source_file 与 json_pointer/code_variable")
                continue
            try:
                source = _safe(root, source_raw)
                if not source.is_file():
                    raise FileNotFoundError(source)
                value = json.loads(source.read_text(encoding="utf-8")) if pointer else _assignment(source, str(variable))
                actual = _pointer(value, str(pointer)) if pointer else value
                expected = parameter.get("expected")
                tolerance = float(parameter.get("tolerance", 1e-9))
                if not _same(actual, expected, tolerance):
                    row["issues"].append(f"{qid} 参数 {pname} 与运行配置不一致: {actual!r} != {expected!r}")
            except Exception as exc:
                row["issues"].append(f"{qid} 参数 {pname} 无法核对: {exc}")
        anchor = str(item.get("paper_anchor", "")).strip()
        if anchor and anchor not in tex:
            row["issues"].append(f"{qid} paper_anchor 未在正文出现: {anchor}")
        row["passed"] = not row["issues"]
        report["subproblems"].append(row)
    for row in report["subproblems"]:
        report["issues"].extend(row["issues"])
    if report["issues"]:
        if strict or required:
            report["passed"] = False
            report["gate_status"] = "BLOCK"
        else:
            report["warnings"] = list(report["issues"])
            report["issues"] = []
            report["gate_status"] = "WARN"
    report["manifest"] = str(manifest)
    report["required"] = required
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    try:
        report = validate(root, _discover(root, args.manifest), args.strict)
    except Exception as exc:
        report = {"schema_version": "1.0", "strict": args.strict, "passed": False,
                  "gate_status": "BLOCK", "issues": [str(exc)], "warnings": []}
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    out = Path(args.out).resolve() if args.out else root / "algorithm_manifest_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
