#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare declared result JSON values with solver-code constants.

Projects opt in with ``result_code_map.json``.  The checker deliberately uses
an explicit map instead of guessing arbitrary print statements, so a mismatch
is actionable and reproducible rather than a fragile text heuristic.
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import sys
from pathlib import Path


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


def _derived_value(value: object, operation: str) -> object:
    operation = operation.lower()
    if not isinstance(value, list) or not value:
        raise ValueError("derived_checks 的 input_values 必须是非空列表")
    if not all(isinstance(item, (int, float)) for item in value):
        raise ValueError("derived_checks 只支持数值输入")
    if operation == "sum":
        return sum(value)
    if operation == "product":
        result = 1
        for item in value:
            result *= item
        return result
    if operation == "mean":
        return sum(value) / len(value)
    if operation == "difference":
        if len(value) != 2:
            raise ValueError("difference 需要两个输入值")
        return value[0] - value[1]
    if operation == "ratio":
        if len(value) != 2 or value[1] == 0:
            raise ValueError("ratio 需要两个输入值且分母不能为零")
        return value[0] / value[1]
    raise ValueError(f"不支持的派生操作: {operation}")


def _close(actual: object, expected: object, tolerance: float) -> bool:
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return math.isclose(float(actual), float(expected), rel_tol=tolerance, abs_tol=tolerance)
    return actual == expected


def check(root: Path, mapping_path: Path | None = None, strict: bool = False) -> dict:
    root = root.resolve()
    mapping_path = mapping_path or (root / "result_code_map.json")
    if not mapping_path.exists():
        return {"schema_version": "1.0", "passed": True, "gate_status": "PASS",
                "issues": [], "warnings": [], "info": ["未配置 result_code_map.json，结果—代码值核对未启用"]}
    payload = json.loads(mapping_path.read_text(encoding="utf-8"))
    checks = payload.get("checks") if isinstance(payload, dict) else None
    derived_checks = payload.get("derived_checks", []) if isinstance(payload, dict) else []
    if checks is None:
        checks = []
    issues: list[str] = []
    rows: list[dict] = []
    if (not isinstance(checks, list) or not checks) and not (isinstance(derived_checks, list) and derived_checks):
        issues.append("result_code_map.json 至少需要非空 checks 或 derived_checks")
    else:
        for index, item in enumerate(checks, 1):
            if not isinstance(item, dict):
                issues.append(f"检查项 {index} 不是 mapping")
                continue
            result_file = _safe_project_path(root, str(item.get("result_file", "")))
            code_file = _safe_project_path(root, str(item.get("code_file", "")))
            variable = str(item.get("code_variable", "RESULTS"))
            key = str(item.get("json_pointer", "/"))
            row = {"index": index, "result_file": str(result_file), "code_file": str(code_file),
                   "variable": variable, "json_pointer": key, "status": "PASS"}
            try:
                actual_result = _pointer(json.loads(result_file.read_text(encoding="utf-8")), key)
                actual_code = _pointer(_assignment(code_file, variable), key)
                if actual_result != actual_code:
                    row["status"] = "FAIL"
                    row["result_value"] = actual_result
                    row["code_value"] = actual_code
                    issues.append(f"检查项 {index} 结果与代码不一致: {key} ({actual_result!r} != {actual_code!r})")
            except Exception as exc:
                row["status"] = "FAIL"
                row["error"] = str(exc)
                issues.append(f"检查项 {index} 无法核对: {exc}")
            rows.append(row)
    if derived_checks is not None and not isinstance(derived_checks, list):
        issues.append("derived_checks 必须是列表")
        derived_checks = []
    for index, item in enumerate(derived_checks, 1):
        row = {"index": index, "kind": "derived", "status": "PASS"}
        try:
            if not isinstance(item, dict):
                raise ValueError("派生检查项不是 mapping")
            result_file = _safe_project_path(root, str(item.get("result_file", "")))
            payload_value = json.loads(result_file.read_text(encoding="utf-8"))
            target_pointer = str(item.get("target_pointer", ""))
            input_pointers = item.get("input_pointers")
            if not target_pointer or not isinstance(input_pointers, list) or not input_pointers:
                raise ValueError("派生检查需提供 target_pointer 和 input_pointers")
            values = [_pointer(payload_value, str(pointer)) for pointer in input_pointers]
            expected = _derived_value(values, str(item.get("operation", "")))
            actual = _pointer(payload_value, target_pointer)
            tolerance = float(item.get("tolerance", 1e-9))
            if not _close(actual, expected, tolerance):
                row.update(status="FAIL", actual=actual, expected=expected)
                issues.append(f"派生结果不一致: {target_pointer} ({actual!r} != {expected!r})")
            else:
                row.update(target_pointer=target_pointer, operation=item.get("operation"), value=actual)
        except Exception as exc:
            row.update(status="FAIL", error=str(exc))
            issues.append(f"派生检查 {index} 无法核对: {exc}")
        rows.append(row)
    report = {"schema_version": "1.0", "strict": strict, "passed": not issues,
              "gate_status": "BLOCK" if issues else "PASS", "issues": issues,
              "warnings": [], "checks": rows, "mapping": str(mapping_path)}
    if issues and not strict:
        report["warnings"] = issues
        report["issues"] = []
        report["passed"] = True
        report["gate_status"] = "WARN"
    return report


def _safe_project_path(root: Path, raw: str) -> Path:
    """Resolve a mapping path without allowing it to escape the project root."""
    candidate = Path(raw)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"映射路径越出项目根目录: {raw}")
    return resolved


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--map", default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    try:
        report = check(Path(args.project_root), Path(args.map).resolve() if args.map else None, args.strict)
    except Exception as exc:
        report = {"schema_version": "1.0", "strict": args.strict, "passed": False,
                  "gate_status": "BLOCK", "issues": [str(exc)], "warnings": []}
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out = Path(args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
