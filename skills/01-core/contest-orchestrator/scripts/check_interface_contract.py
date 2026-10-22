#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check cross-subproblem interface artifacts and JSON pointers."""
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


def discover(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).resolve()
    candidates = [root / "interface_contract.yaml", root / "03_文档" / "interface_contract.yaml",
                  root / "03_文档" / "paper" / "interface_contract.yaml"]
    return next((path for path in candidates if path.exists()), None)


def load(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("缺少 PyYAML，无法读取 interface_contract.yaml")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError("interface_contract.yaml 根节点必须是 mapping")
    return value


def _within(path: Path, root: Path) -> bool:
    candidate, base = path.resolve(), root.resolve()
    return candidate == base or base in candidate.parents


def _pointer(value: object, pointer: str) -> bool:
    if not pointer or pointer == "/":
        return True
    current = value
    for token in pointer.lstrip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return False
    return True


def validate(payload: dict, root: Path, contract: Path) -> dict:
    report = {"schema_version": "1.0", "passed": True, "gate_status": "PASS",
              "issues": [], "warnings": [], "interfaces": []}
    edges = payload.get("interfaces", payload.get("edges", []))
    if not isinstance(edges, list):
        report["issues"].append("interfaces 必须是列表")
        return report
    for index, edge in enumerate(edges, 1):
        if not isinstance(edge, dict):
            report["issues"].append(f"接口 {index} 不是 mapping")
            continue
        source = str(edge.get("source_file", edge.get("source", "")))
        pointer = str(edge.get("key_path", edge.get("pointer", "")))
        item = {"index": index, "from": edge.get("from"), "to": edge.get("to"),
                "source_file": source, "pointer": pointer}
        report["interfaces"].append(item)
        if not source:
            report["issues"].append(f"接口 {index} 缺少 source_file")
            continue
        source_path = (root / source).resolve()
        if not source_path.exists() or not _within(source_path, root):
            report["issues"].append(f"接口 {index} 来源文件不存在或越界: {source}")
            continue
        if pointer and source_path.suffix.lower() == ".json":
            try:
                if not _pointer(json.loads(source_path.read_text(encoding="utf-8")), pointer):
                    report["issues"].append(f"接口 {index} JSON pointer 不存在: {pointer}")
            except Exception as exc:
                report["issues"].append(f"接口 {index} JSON 无法解析: {exc}")
    if report["issues"]:
        report["passed"] = False
        report["gate_status"] = "BLOCK"
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
    if contract is None:
        report = {"schema_version": "1.0", "passed": not args.strict,
                  "gate_status": "BLOCK" if args.strict else "WARN",
                  "issues": ["缺少 interface_contract.yaml"] if args.strict else [],
                  "warnings": [] if args.strict else ["缺少 interface_contract.yaml，接口检查未执行"]}
    else:
        try:
            report = validate(load(contract), root, contract)
        except Exception as exc:
            report = {"schema_version": "1.0", "passed": False, "gate_status": "BLOCK",
                      "issues": [str(exc)], "warnings": []}
    if report.get("issues") and not args.strict:
        report["warnings"] = list(report.get("warnings", [])) + list(report["issues"])
        report["issues"] = []
        report["passed"] = True
        report["gate_status"] = "WARN"
    out = Path(args.out).resolve() if args.out else root / "interface_contract_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
