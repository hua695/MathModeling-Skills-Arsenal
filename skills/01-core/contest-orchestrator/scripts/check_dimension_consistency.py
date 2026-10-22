#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check opt-in, declarative dimensional consistency assertions.

This checker does not infer dimensions from arbitrary LaTeX.  A project may
declare dimension vectors and equation operations in ``model_contract.yaml``;
the checker then verifies those assertions deterministically and reports a
clear omission when a declared symbol is unknown.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def discover(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).resolve()
    for candidate in (root / "model_contract.yaml", root / "03_文档" / "model_contract.yaml",
                      root / "03_文档" / "paper" / "model_contract.yaml"):
        if candidate.exists():
            return candidate.resolve()
    return None


def load(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("缺少 PyYAML，无法读取模型契约")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError("model_contract.yaml 根节点必须是 mapping")
    return value


def _vector(raw: object) -> tuple[float, ...]:
    if isinstance(raw, (list, tuple)) and raw:
        return tuple(float(value) for value in raw)
    raise ValueError(f"量纲向量必须是非空数字列表: {raw!r}")


def _combine(vectors: list[tuple[float, ...]], operation: str) -> tuple[float, ...]:
    if not vectors:
        raise ValueError("rhs_terms 不能为空")
    if operation in {"add", "same"}:
        if any(vector != vectors[0] for vector in vectors[1:]):
            raise ValueError("相加项量纲不一致")
        return vectors[0]
    if operation == "multiply":
        width = len(vectors[0])
        if any(len(vector) != width for vector in vectors):
            raise ValueError("相乘项量纲向量长度不一致")
        return tuple(sum(vector[i] for vector in vectors) for i in range(width))
    if operation == "divide":
        if len(vectors) != 2 or len(vectors[0]) != len(vectors[1]):
            raise ValueError("divide 需要两个同长度量纲向量")
        return tuple(vectors[0][i] - vectors[1][i] for i in range(len(vectors[0])))
    raise ValueError(f"不支持的 operation: {operation}")


def validate(payload: dict, contract: Path, strict: bool = False) -> dict:
    report = {"schema_version": "1.0", "strict": strict, "passed": True,
              "gate_status": "PASS", "issues": [], "warnings": [], "equations": []}
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, dict):
        report["info"] = ["未配置 dimensions，量纲检查未启用"]
        report["contract"] = str(contract)
        return report
    symbols = dimensions.get("symbols")
    if not isinstance(symbols, dict) or not symbols:
        report["issues"].append("dimensions.symbols 必须是非空 mapping")
        symbols = {}
    vectors: dict[str, tuple[float, ...]] = {}
    for name, raw in symbols.items():
        try:
            vectors[str(name)] = _vector(raw)
        except Exception as exc:
            report["issues"].append(f"符号 {name} 的量纲无效: {exc}")
    equations = dimensions.get("equations", [])
    if not isinstance(equations, list):
        report["issues"].append("dimensions.equations 必须是列表")
        equations = []
    for index, equation in enumerate(equations, 1):
        row = {"index": index, "status": "PASS"}
        if not isinstance(equation, dict):
            row.update(status="FAIL", error="方程条目不是 mapping")
            report["issues"].append(f"量纲方程 {index} 不是 mapping")
            report["equations"].append(row)
            continue
        lhs = str(equation.get("lhs", ""))
        terms = equation.get("rhs_terms", [])
        operation = str(equation.get("operation", "same")).lower()
        try:
            if lhs not in vectors:
                raise KeyError(f"lhs 未声明: {lhs}")
            if not isinstance(terms, list) or not terms:
                raise ValueError("rhs_terms 必须是非空列表")
            missing = [str(term) for term in terms if str(term) not in vectors]
            if missing:
                raise KeyError(f"rhs 未声明: {missing}")
            expected = _combine([vectors[str(term)] for term in terms], operation)
            if expected != vectors[lhs]:
                raise ValueError(f"lhs={vectors[lhs]}，rhs={expected}")
            row.update(lhs=lhs, rhs_terms=terms, operation=operation, dimension=list(expected))
        except Exception as exc:
            row.update(status="FAIL", error=str(exc))
            report["issues"].append(f"量纲方程 {index} 不一致: {exc}")
        report["equations"].append(row)
    if report["issues"]:
        if strict or bool(dimensions.get("required", False)):
            report["passed"] = False
            report["gate_status"] = "BLOCK"
        else:
            report["warnings"] = list(report["issues"])
            report["issues"] = []
            report["gate_status"] = "WARN"
    report["contract"] = str(contract)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--contract", default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    contract = discover(root, args.contract)
    try:
        if contract is None:
            report = {"schema_version": "1.0", "strict": args.strict,
                      "passed": not args.strict, "gate_status": "BLOCK" if args.strict else "WARN",
                      "issues": ["缺少 model_contract.yaml"] if args.strict else [],
                      "warnings": [] if args.strict else ["缺少 model_contract.yaml，量纲检查未执行"]}
        else:
            report = validate(load(contract), contract, args.strict)
    except Exception as exc:
        report = {"schema_version": "1.0", "strict": args.strict, "passed": False,
                  "gate_status": "BLOCK", "issues": [str(exc)], "warnings": []}
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    out = Path(args.out).resolve() if args.out else root / "dimension_consistency_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
