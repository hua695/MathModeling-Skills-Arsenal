#!/usr/bin/env python3
"""Validate the permitted trigger and bounded scope of an H6 verification."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


MANDATORY_CHECKS = {"contract_anchors", "cross_question_interfaces", "result_interpretation_cards"}
INITIAL_TRIGGERS = {"h5_result_freeze"}
TARGETED_TRIGGERS = {"model_change", "data_change", "key_result_change", "interpretation_card_change"}
NON_H6_TRIGGERS = {"ordinary_prose_change", "layout_change", "figure_style_change", "appendix_format_change"}


def load_scope(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("验证范围卡必须为 YAML 对象")
    return data


def check_scope(scope: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if scope.get("schema_version") != "1.0":
        failures.append("schema_version 必须为 1.0")
    mode = scope.get("mode")
    if mode not in {"initial_review", "targeted_recheck"}:
        failures.append("mode 必须为 initial_review 或 targeted_recheck")
    trigger = scope.get("trigger")
    if trigger in NON_H6_TRIGGERS:
        failures.append(f"trigger={trigger} 不触发 H6；该改动不应派发独立验证 agent")
    elif mode == "initial_review" and trigger not in INITIAL_TRIGGERS:
        failures.append("initial_review 只能由 h5_result_freeze 触发")
    elif mode == "targeted_recheck" and trigger not in TARGETED_TRIGGERS:
        failures.append("targeted_recheck 只能由模型、数据、关键结果或结果解释卡变化触发")

    mandatory_checks = scope.get("mandatory_checks")
    if not isinstance(mandatory_checks, list) or not MANDATORY_CHECKS.issubset(set(mandatory_checks)):
        failures.append("mandatory_checks 必须包含 contract_anchors、cross_question_interfaces、result_interpretation_cards")
    changed = scope.get("changed_artifacts")
    if mode == "initial_review":
        if changed not in ([], None):
            failures.append("initial_review 的 changed_artifacts 必须为空列表或省略")
    elif mode == "targeted_recheck":
        if not isinstance(changed, list) or not changed:
            failures.append("targeted_recheck 必须提供非空 changed_artifacts")
        else:
            for index, item in enumerate(changed):
                if not isinstance(item, dict) or not str(item.get("path", "")).strip() or not str(item.get("sha256", "")).strip():
                    failures.append(f"changed_artifacts[{index}] 必须包含 path 与 sha256")
    samples = scope.get("deep_sample_refs")
    if not isinstance(samples, list):
        failures.append("deep_sample_refs 必须为列表")
    elif mode == "initial_review" and not samples:
        failures.append("initial_review 必须登记至少一个深度抽查锚点")
    return {"schema_version": "1.0", "passed": not failures, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        report = check_scope(load_scope(args.scope))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        report = {"schema_version": "1.0", "passed": False, "failures": [str(exc)]}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
