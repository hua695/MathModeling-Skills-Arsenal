#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check optional cross-subproblem symbol meaning and unit consistency."""
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
    candidates = [root / "model_contract.yaml", root / "03_文档" / "model_contract.yaml",
                  root / "03_文档" / "paper" / "model_contract.yaml"]
    return next((path for path in candidates if path.exists()), None)


def load(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("缺少 PyYAML，无法读取模型契约")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError("model_contract.yaml 根节点必须是 mapping")
    return value


def _entries(item: dict) -> list[dict]:
    values = item.get("symbols")
    if values is None and isinstance(item.get("evidence"), dict):
        symbols = item["evidence"].get("symbols_units")
        values = symbols.get("symbols") if isinstance(symbols, dict) else None
    if values is None:
        return []
    if isinstance(values, dict):
        values = [{"name": key, **(value if isinstance(value, dict) else {"meaning": value})}
                  for key, value in values.items()]
    result = []
    for value in values if isinstance(values, list) else []:
        if isinstance(value, str):
            result.append({"name": value})
        elif isinstance(value, dict):
            result.append(value)
    return result


def validate(payload: dict, contract: Path) -> dict:
    report = {"schema_version": "1.0", "passed": True, "gate_status": "PASS",
              "issues": [], "warnings": [], "symbols": []}
    seen: dict[str, list[dict]] = {}
    for item in payload.get("subproblems", []) if isinstance(payload.get("subproblems"), list) else []:
        if not isinstance(item, dict):
            continue
        qid = str(item.get("id", ""))
        for symbol in _entries(item):
            name = str(symbol.get("name", symbol.get("latex", ""))).strip()
            if not name:
                report["issues"].append(f"{qid} 存在缺少 name 的符号条目")
                continue
            entry = {"qid": qid, "name": name, "meaning": str(symbol.get("meaning", "")).strip(),
                     "unit": str(symbol.get("unit", "")).strip(), "scope": str(symbol.get("scope", "global"))}
            seen.setdefault(name, []).append(entry)
            report["symbols"].append(entry)
    for name, entries in seen.items():
        global_entries = [entry for entry in entries if entry["scope"] != "local"]
        meanings = {entry["meaning"] for entry in global_entries if entry["meaning"]}
        units = {entry["unit"] for entry in global_entries if entry["unit"]}
        if len(meanings) > 1 or len(units) > 1:
            report["issues"].append(f"符号 {name} 跨子问题含义或单位冲突: {entries}")
    report["contract"] = str(contract)
    if report["issues"]:
        report["passed"] = False
        report["gate_status"] = "BLOCK"
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
                  "issues": ["缺少 model_contract.yaml"] if args.strict else [],
                  "warnings": [] if args.strict else ["缺少 model_contract.yaml，符号检查未执行"]}
    else:
        try:
            report = validate(load(contract), contract)
        except Exception as exc:
            report = {"schema_version": "1.0", "passed": False, "gate_status": "BLOCK",
                      "issues": [str(exc)], "warnings": []}
    if report.get("issues") and not args.strict:
        report["warnings"] = list(report.get("warnings", [])) + list(report["issues"])
        report["issues"] = []
        report["passed"] = True
        report["gate_status"] = "WARN"
    out = Path(args.out).resolve() if args.out else root / "symbol_consistency_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
