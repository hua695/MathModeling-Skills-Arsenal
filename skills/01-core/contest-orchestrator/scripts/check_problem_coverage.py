#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit a structured problem-condition ledger before modeling.

The checker validates traceability metadata; it does not claim to prove that a
semantic interpretation is mathematically correct.  Ambiguous conditions stay
visible as ``pending`` and must be resolved, bounded, or handled by scenarios
before a strict full-contest delivery.
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

ROLES = {"context", "entity", "definition", "mechanism", "given", "constraint", "task", "objective", "validation", "deliverable"}
LINKS = {"defines", "supplies", "restricts", "motivates", "extends", "reuses", "compares", "validates", "overrides"}
LEVELS = {"confirmed", "inferred", "pending"}
STATUSES = {"mapped", "unresolved", "excluded"}


def discover(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return (candidate if candidate.is_absolute() else root / candidate).resolve()
    for candidate in (root / "problem_condition_ledger.yaml", root / "03_文档" / "problem_condition_ledger.yaml",
                      root / "paper" / "problem_condition_ledger.yaml"):
        if candidate.exists():
            return candidate.resolve()
    return None


def _safe(root: Path, raw: object) -> Path:
    candidate = Path(str(raw))
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"题目源文件路径越出项目根目录: {raw}")
    return resolved


def load(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("缺少 PyYAML，无法读取 problem_condition_ledger.yaml")
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError("problem_condition_ledger.yaml 根节点必须是 mapping")
    return value


def validate(root: Path, ledger: Path | None, strict: bool = False, require: bool = False) -> dict:
    report = {"schema_version": "1.0", "strict": strict, "required": require,
              "passed": True, "gate_status": "PASS", "issues": [], "warnings": [],
              "source_units": [], "questions": [], "unresolved_conditions": []}
    if ledger is None or not ledger.exists():
        if require:
            report.update(passed=False, gate_status="BLOCK", issues=["缺少 problem_condition_ledger.yaml：严格全流程需要题目条件账本"])
        else:
            report["info"] = ["未配置 problem_condition_ledger.yaml，题目条件覆盖审计未启用"]
        return report
    try:
        payload = load(ledger)
    except Exception as exc:
        report.update(passed=False, gate_status="BLOCK", issues=[str(exc)], ledger=str(ledger))
        return report
    issues: list[str] = []
    source_raw = payload.get("source_file")
    if not source_raw:
        issues.append("source_file 不能为空")
    else:
        try:
            source = _safe(root, source_raw)
            if not source.is_file():
                issues.append(f"题目源文件不存在: {source_raw}")
            elif source.suffix.lower() in {".md", ".txt", ".tex"}:
                text = source.read_text(encoding="utf-8", errors="replace")
                title = str(payload.get("title_anchor", ""))
                if not title or title not in text:
                    issues.append("title_anchor 未在可读题目源文件中出现")
        except Exception as exc:
            issues.append(str(exc))
    if not str(payload.get("title_anchor", "")).strip():
        issues.append("title_anchor 不能为空；必须先定位实际题目标题")

    units = payload.get("source_units")
    if not isinstance(units, list) or not units:
        issues.append("source_units 必须是非空列表")
        units = []
    unit_ids: set[str] = set()
    unit_locations: set[tuple[str, str]] = set()
    question_ids: set[str] = set()
    for item in units:
        row = {"id": str(item.get("id", "")) if isinstance(item, dict) else "", "status": "PASS", "issues": []}
        if not isinstance(item, dict):
            row.update(status="FAIL", issues=["条件条目不是 mapping"])
            report["source_units"].append(row)
            issues.append("source_units 存在非 mapping 条目")
            continue
        uid = row["id"]
        required = ("id", "source_location", "source_text", "roles", "normalized_meaning",
                    "affected_questions", "downstream_evidence", "evidence_level", "status")
        missing = [key for key in required if key not in item or item.get(key) in (None, "")]
        if missing:
            row["issues"].append(f"缺少字段: {', '.join(missing)}")
        if uid in unit_ids:
            row["issues"].append(f"条件 ID 重复: {uid}")
        unit_ids.add(uid)
        location_key = (str(item.get("source_location", "")), str(item.get("source_text", "")))
        if location_key in unit_locations and item.get("status") != "excluded":
            row["issues"].append("相同来源位置与原文重复，可能重复登记")
        unit_locations.add(location_key)
        roles = item.get("roles") if isinstance(item.get("roles"), list) else []
        unknown_roles = sorted(set(str(value) for value in roles) - ROLES)
        if unknown_roles:
            row["issues"].append(f"未知 roles: {unknown_roles}")
        affected = item.get("affected_questions") if isinstance(item.get("affected_questions"), list) else []
        for qid in affected:
            qid = str(qid).upper()
            question_ids.add(qid)
            if not (qid.startswith("Q") and qid[1:].isdigit()):
                row["issues"].append(f"affected_questions 含非法小问: {qid}")
        evidence_level = str(item.get("evidence_level", ""))
        status = str(item.get("status", ""))
        if evidence_level not in LEVELS:
            row["issues"].append(f"未知 evidence_level: {evidence_level}")
        if status not in STATUSES:
            row["issues"].append(f"未知 status: {status}")
        if evidence_level == "pending" and status != "unresolved":
            row["issues"].append("pending 条件必须标记为 unresolved")
        if status == "mapped" and not item.get("downstream_evidence"):
            row["issues"].append("mapped 条件必须登记 downstream_evidence")
        link_type = item.get("link_type")
        if link_type is not None and str(link_type) not in LINKS:
            row["issues"].append(f"未知 link_type: {link_type}")
        row["status"] = "FAIL" if row["issues"] else "PASS"
        report["source_units"].append(row)
        issues.extend(f"{uid}: {message}" for message in row["issues"])

    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        issues.append("questions 必须是非空列表，不能只登记孤立条件")
        questions = []
    seen_questions: set[str] = set()
    for item in questions:
        row = {"id": str(item.get("id", "")).upper() if isinstance(item, dict) else "", "status": "PASS", "issues": []}
        if not isinstance(item, dict):
            row.update(status="FAIL", issues=["小问条目不是 mapping"])
            report["questions"].append(row)
            issues.append("questions 存在非 mapping 条目")
            continue
        qid = row["id"]
        if not qid.startswith("Q") or not qid[1:].isdigit() or qid in seen_questions:
            row["issues"].append(f"小问 ID 缺失、非法或重复: {qid}")
        seen_questions.add(qid)
        for key in ("source_unit_ids", "inputs", "task", "outputs"):
            if key not in item or item.get(key) in (None, "", []):
                row["issues"].append(f"{qid} 缺少 {key}")
        unknown_units = [str(uid) for uid in item.get("source_unit_ids", []) if str(uid) not in unit_ids]
        if unknown_units:
            row["issues"].append(f"{qid} 引用了不存在的条件: {unknown_units}")
        affected_by_units = {str(q).upper() for q in question_ids}
        if qid not in affected_by_units:
            row["issues"].append(f"{qid} 没有任何 source_unit 绑定")
        row["status"] = "FAIL" if row["issues"] else "PASS"
        report["questions"].append(row)
        issues.extend(row["issues"])
    if question_ids and seen_questions != question_ids:
        issues.append(f"source_units 与 questions 的小问集合不一致: units={sorted(question_ids)}, questions={sorted(seen_questions)}")
    expected = payload.get("expected_subquestions")
    if isinstance(expected, list) and {str(value).upper() for value in expected} != seen_questions:
        issues.append("expected_subquestions 与 questions.id 不一致")
    unresolved = payload.get("unresolved_conditions")
    if not isinstance(unresolved, list):
        issues.append("unresolved_conditions 必须是列表")
        unresolved = []
    report["unresolved_conditions"] = [str(value) for value in unresolved]
    pending_units = [row["id"] for row, item in zip(report["source_units"], units)
                     if isinstance(item, dict) and str(item.get("evidence_level")) == "pending"]
    if pending_units and not unresolved:
        issues.append(f"存在 pending 条件但 unresolved_conditions 为空: {pending_units}")
    if strict and (pending_units or unresolved):
        issues.append("严格模式下存在未解决题目条件，必须人工确认、做情景分析或明确排除理由")
    report["coverage"] = {"source_unit_count": len(units), "ledger_row_count": len(report["source_units"]),
                          "question_count": len(seen_questions), "questions": sorted(seen_questions),
                          "pending_unit_ids": pending_units}
    report["issues"] = issues
    report["ledger"] = str(ledger)
    if issues:
        report["passed"] = False
        report["gate_status"] = "BLOCK" if strict or require else "WARN"
        if not strict and not require:
            report["warnings"] = list(issues)
            report["issues"] = []
            report["passed"] = True
            report["gate_status"] = "WARN"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--ledger", default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-ledger", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    try:
        report = validate(root, discover(root, args.ledger), args.strict, args.require_ledger)
    except Exception as exc:
        report = {"schema_version": "1.0", "strict": args.strict, "required": args.require_ledger,
                  "passed": False, "gate_status": "BLOCK", "issues": [str(exc)], "warnings": []}
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    out = Path(args.out).resolve() if args.out else root / "problem_coverage_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
