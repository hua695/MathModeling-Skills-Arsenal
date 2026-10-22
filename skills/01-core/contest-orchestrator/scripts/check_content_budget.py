#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check pre-writing content capacity and final body-page target.

This is a planning/delivery guard, not a text generator.  It never pads a
paper and never treats page count as a substitute for modeling evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_REQUIRED_EVIDENCE = (
    "problem_goal", "modeling_idea", "model_selection_rationale", "assumptions",
    "variables_and_units", "original_relations", "derivation_chain", "final_model",
    "parameter_determination", "solver_or_algorithm", "result_provenance",
    "validation", "result_interpretation", "conclusion_mapping",
)
KNOWN_PROFILES = {
    "mechanistic_optimization", "data_prediction", "evaluation_decision",
    "simulation_dynamics", "hybrid", "statistical_inference", "classification",
    "grouping_threshold", "network_graph", "uncertainty",
}
VALIDATION_SCOPES = {"local", "global", "both"}


def emit_json(payload: dict, out: Path | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text, end="")


def load_payload(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        value = json.loads(raw)
    else:
        try:
            import yaml
        except ImportError as exc:
            raise ValueError("读取 YAML 计划需要 PyYAML") from exc
        value = yaml.safe_load(raw)
    if not isinstance(value, dict):
        raise ValueError("content_budget_plan 必须是对象")
    return value


def find_plan(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    candidates = (
        root / "content_budget_plan.yaml", root / "content_budget_plan.yml",
        root / "content_budget_plan.json", root / "01_需求与规划" / "content_budget_plan.yaml",
        root / "01_需求与规划" / "content_budget_plan.yml",
        root / "01_需求与规划" / "content_budget_plan.json",
        root / "paper" / "content_budget_plan.yaml",
        root / "paper" / "content_budget_plan.json",
    )
    return next((path.resolve() for path in candidates if path.is_file()), None)


def find_evidence_index(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
        return resolved if resolved.is_file() else None
    candidates = (root / ".contest" / "evidence_index.json", root / "evidence_index.json",
                  root / "05_输出与交付" / "evidence_index.json")
    return next((path.resolve() for path in candidates if path.is_file()), None)


def _range(policy: dict, key: str, fallback: tuple[float, float]) -> tuple[float, float]:
    value = policy.get(key, fallback)
    if isinstance(value, dict):
        value = (value.get("min"), value.get("max"))
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"page_policy.{key} 必须是 [min,max]")
    low, high = float(value[0]), float(value[1])
    if low > high:
        raise ValueError(f"page_policy.{key} 的最小值不能大于最大值")
    return low, high


def _numeric(value, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} 必须是数字") from exc
    if result <= 0:
        raise ValueError(f"{name} 必须大于0")
    return result


def budget_total(plan: dict) -> float:
    budget = plan.get("content_budget") or {}
    total = 0.0
    for key in ("shared_sections", "subproblems", "global_sections"):
        items = budget.get(key) or []
        if not isinstance(items, list):
            raise ValueError(f"content_budget.{key} 必须是数组")
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"content_budget.{key} 含有非对象项")
            total += _numeric(item.get("target_pages"), f"{key}.target_pages")
    return round(total, 3)


def problem_checks(plan: dict, stage: str) -> list[str]:
    issues: list[str] = []
    budget = plan.get("content_budget") or {}
    problems = budget.get("subproblems") or []
    if not problems:
        issues.append("缺少 content_budget.subproblems")
        return issues
    seen: set[str] = set()
    for item in problems:
        if not isinstance(item, dict) or not item.get("id"):
            issues.append("存在缺少 id 的小问预算")
            continue
        qid = str(item["id"])
        if qid in seen:
            issues.append(f"小问重复登记: {qid}")
        seen.add(qid)
        try:
            _numeric(item.get("target_pages"), f"{qid}.target_pages")
        except ValueError as exc:
            issues.append(str(exc))
        units = item.get("evidence_units") or []
        if not isinstance(units, list):
            issues.append(f"{qid}.evidence_units 必须是数组")
            continue
        missing = [name for name in DEFAULT_REQUIRED_EVIDENCE if name not in units]
        if missing:
            issues.append(f"{qid} 缺少证据单元: {','.join(missing)}")
        if stage == "solution" and str(item.get("evidence_status", "planned")) not in {"complete", "verified"}:
            issues.append(f"{qid} 证据尚未完成: {item.get('evidence_status', 'planned')}")
        profile = item.get("capability_profile")
        if profile is not None and str(profile) not in KNOWN_PROFILES:
            issues.append(f"{qid} capability_profile 未知: {profile}")
        validation_scope = item.get("validation_scope")
        if validation_scope is not None and str(validation_scope) not in VALIDATION_SCOPES:
            issues.append(f"{qid} validation_scope 必须是 local/global/both")
        visuals = item.get("visual_evidence")
        if visuals is not None:
            if not isinstance(visuals, list):
                issues.append(f"{qid}.visual_evidence 必须是数组")
            else:
                for index, visual in enumerate(visuals):
                    if not isinstance(visual, dict):
                        issues.append(f"{qid}.visual_evidence[{index}] 必须是对象")
                        continue
                    if not str(visual.get("purpose", "")).strip():
                        issues.append(f"{qid}.visual_evidence[{index}] 缺少 purpose")
                    if not str(visual.get("source", "")).strip():
                        issues.append(f"{qid}.visual_evidence[{index}] 缺少 source")
    return issues


def planning_contract_checks(plan: dict, stage: str, evidence_index: Path | None,
                             strict: bool) -> list[str]:
    """Validate the optional evidence-first extension without breaking v1 plans."""
    if str(plan.get("planning_contract", "")).lower() != "evidence_first":
        return []
    issues: list[str] = []
    policy = plan.get("evidence_policy")
    if not isinstance(policy, dict):
        issues.append("evidence_first 计划缺少 evidence_policy")
    else:
        source = str(policy.get("source_of_truth", "")).strip()
        if source != ".contest/evidence_index.json":
            issues.append("evidence_policy.source_of_truth 必须为 .contest/evidence_index.json")
        required = policy.get("required_sources", [])
        if not isinstance(required, list) or not required:
            issues.append("evidence_policy.required_sources 必须是非空数组")
    if stage in {"solution", "pdf"} and evidence_index is None:
        issues.append("evidence_first 计划在求解/交付阶段缺少 .contest/evidence_index.json")
    if evidence_index is not None:
        try:
            payload = json.loads(evidence_index.read_text(encoding="utf-8"))
            if payload.get("derived") is not True:
                issues.append("evidence_index.json 必须标记 derived=true")
            if stage in {"solution", "pdf"} and not payload.get("passed", False):
                issues.append("evidence_index.json 存在未通过的证据来源")
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            issues.append(f"evidence_index.json 无法解析: {exc}")
    return issues if strict else []


def _standalone_heading(text: str, markers: tuple[str, ...]) -> bool:
    return any(re.search(r"(?:^|\n)\s*" + re.escape(marker) + r"\s*(?:\n|$)", text) for marker in markers)


def estimate_body_pages(pdf: Path) -> tuple[float | None, str]:
    try:
        import pymupdf
        doc = pymupdf.open(str(pdf))
    except (ImportError, OSError, RuntimeError) as exc:
        return None, f"无法读取 PDF: {exc}"
    texts = [page.get_text() or "" for page in doc]
    ref_index = next((i for i, text in enumerate(texts) if _standalone_heading(text, ("参考文献", "文献资料", "References", "REFERENCES"))), None)
    if ref_index is None:
        return None, "未找到独立参考文献标题，无法稳定估算正文页数"
    # 正文页数不应把摘要页机械计入。若能找到“关键词”行，按其后首个页面
    # 到参考文献标题页之前的页数估算；同时在说明中保留物理页数，便于人工复核。
    keyword_index = next(
        (i for i, text in enumerate(texts[:ref_index])
         if re.search(r"(?:^|\n)\s*关键词\s*[:：]", text)),
        None,
    )
    if keyword_index is not None and keyword_index < ref_index:
        analytical_pages = max(0, ref_index - keyword_index - 1)
        return float(analytical_pages), (
            f"按关键词页之后至参考文献标题页之前估算正文页数；"
            f"物理参考文献前页数={ref_index}"
        )
    # 没有可识别的摘要/关键词边界时，采用保守的参考文献前物理页数。
    return float(ref_index), "未识别关键词边界，按PDF参考文献标题页之前的物理页数保守估算"


def run(root: Path, stage: str, plan_path: Path | None, pdf: Path | None,
        body_pages: float | None, strict: bool, allow_short_exception: bool,
        evidence_index_path: Path | None = None) -> tuple[dict, int]:
    report: dict = {"schema_version": "1.0", "stage": stage, "project_root": str(root), "status": "BLOCK"}
    if plan_path is None or not plan_path.is_file():
        report["issues"] = ["缺少 content_budget_plan.yaml/json；无法执行前置内容预算门禁"]
        if not strict and stage != "pdf":
            report["status"] = "WARN"
            return report, 0
        return report, 1
    try:
        plan = load_payload(plan_path)
        report["plan_path"] = str(plan_path)
        policy = plan.get("page_policy") or {}
        planning = _range(policy, "planning_target", (25.0, 30.0))
        delivery = _range(policy, "delivery_target", planning)
        hard_max = float(policy.get("hard_max", delivery[1]))
        short_threshold = float(policy.get("short_paper_review_threshold", delivery[0]))
        total = budget_total(plan)
        tolerance = float((plan.get("content_budget") or {}).get("tolerance_pages", 1.0))
        evidence_index = evidence_index_path or find_evidence_index(root, None)
        report.update({"target": {"planning": planning, "delivery": delivery, "hard_max": hard_max,
                       "short_paper_review_threshold": short_threshold},
                      "budget_total": total, "budget_tolerance": tolerance,
                      "planning_contract": plan.get("planning_contract", "legacy"),
                      "evidence_index": str(evidence_index) if evidence_index else None})
        issues = problem_checks(plan, "solution" if stage == "solution" else "blueprint")
        issues.extend(planning_contract_checks(plan, stage, evidence_index, strict))
        if total < planning[0] - tolerance or total > planning[1] + tolerance:
            issues.append(f"内容预算合计 {total:.2f} 页不在规划区间 {planning[0]:.2f}–{planning[1]:.2f} 页附近")
        checkpoint = (plan.get("checkpoints") or {}).get(stage) or {}
        predicted = checkpoint.get("predicted_body_pages")
        actual = checkpoint.get("actual_body_pages")
        report["checkpoint"] = checkpoint
        if stage in {"blueprint", "solution"}:
            value = predicted
            if value is not None:
                value = float(value)
                report["predicted_body_pages"] = value
                if value < planning[0] - tolerance:
                    issues.append(f"{stage} 预计正文 {value:.2f} 页低于目标下限 {planning[0]:.2f} 页")
                if value > hard_max:
                    issues.append(f"{stage} 预计正文 {value:.2f} 页超过硬上限 {hard_max:.2f} 页")
            elif stage == "solution":
                issues.append("solution checkpoint 缺少 predicted_body_pages")
        if stage == "pdf":
            if body_pages is None and actual is not None:
                body_pages = float(actual)
            if body_pages is None and pdf is not None:
                body_pages, method = estimate_body_pages(pdf)
                report["measurement_method"] = method
            if body_pages is None:
                issues.append("缺少实际正文页数；请提供 --body-pages 或可识别参考文献标题的 PDF")
            else:
                report["actual_body_pages"] = float(body_pages)
                if body_pages > hard_max:
                    issues.append(f"实际正文 {body_pages:.2f} 页超过硬上限 {hard_max:.2f} 页")
                elif body_pages < short_threshold:
                    report["status"] = "SHORT_PAPER_REVIEW"
                    if not allow_short_exception:
                        issues.append(f"实际正文 {body_pages:.2f} 页低于短论文复核阈值 {short_threshold:.2f} 页")
        padding = plan.get("padding_flags") or []
        if padding:
            issues.append("计划登记了凑页风险: " + "; ".join(map(str, padding)))
        report["issues"] = issues
        if not issues and report["status"] != "SHORT_PAPER_REVIEW":
            report["status"] = "PASS"
        elif report["status"] != "SHORT_PAPER_REVIEW":
            report["status"] = "BLOCK"
        code = 0 if not issues or (report["status"] == "SHORT_PAPER_REVIEW" and allow_short_exception) else 1
        if not strict and stage != "pdf" and report["status"] == "BLOCK":
            code = 0
        return report, code
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report["issues"] = [str(exc)]
        return report, 0 if not strict else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root")
    parser.add_argument("--stage", choices=("blueprint", "solution", "pdf"), default="blueprint")
    parser.add_argument("--plan", default=None)
    parser.add_argument("--pdf", default=None)
    parser.add_argument("--body-pages", type=float, default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--evidence-index", default=None,
                        help="项目侧派生证据索引；evidence_first 计划在 solution/pdf 阶段自动发现")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--allow-short-exception", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    plan = find_plan(root, args.plan)
    pdf = Path(args.pdf).resolve() if args.pdf else None
    evidence_index = find_evidence_index(root, args.evidence_index)
    report, code = run(root, args.stage, plan, pdf, args.body_pages, args.strict,
                       args.allow_short_exception, evidence_index)
    emit_json(report, Path(args.out).resolve() if args.out else None)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
