# -*- coding: utf-8 -*-
"""对有技能/无技能输出做可复现的结构化证据对照。

该工具不调用模型，也不声称完成独立 LLM 评测；它接收外部模型输出或 fixture，
按题型要求检查推导、单位、算法参数、结果来源和可靠性证据，适合作为回放接口。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def score_response(text: str, expected: dict[str, list[str]]) -> dict:
    text = str(text or "")
    features = {}
    hits = 0
    total = 0
    for name, anchors in expected.items():
        anchors = [str(anchor) for anchor in anchors]
        matched = [anchor for anchor in anchors if anchor in text]
        features[name] = {"matched": matched, "missing": [a for a in anchors if a not in matched]}
        hits += len(matched)
        total += len(anchors)
    return {"score": round(hits / total, 4) if total else 1.0,
            "hits": hits, "total": total, "features": features}


def evaluate(case: dict) -> dict:
    expected = case.get("expected_features", {})
    baseline = score_response(case.get("baseline_response", ""), expected)
    skilled = score_response(case.get("skill_response", ""), expected)
    required = set(case.get("required_features", expected.keys()))
    missing_required = [name for name in required
                        if skilled["features"].get(name, {}).get("missing")]
    return {
        "id": case.get("id", "unnamed"),
        "problem_type": case.get("problem_type", "unknown"),
        "baseline": baseline,
        "skill": skilled,
        "delta": round(skilled["score"] - baseline["score"], 4),
        "skill_not_worse": skilled["score"] >= baseline["score"],
        "missing_required_features": missing_required,
        "status": "PASS" if not missing_required and skilled["score"] >= baseline["score"] else "FAIL",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="对照评估外部模型输出的结构化建模证据。")
    parser.add_argument("input", help="JSONL 文件，每行一个对照案例。")
    parser.add_argument("--out", required=True, help="JSON 报告路径。")
    parser.add_argument("--strict", action="store_true", help="任一案例失败时返回非零。")
    args = parser.parse_args(argv)
    source = Path(args.input).resolve()
    if not source.is_file():
        parser.error(f"输入文件不存在: {source}")
    cases = []
    for line_no, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as exc:
            parser.error(f"第 {line_no} 行不是合法 JSONL: {exc}")
    results = [evaluate(case) for case in cases]
    payload = {
        "schema_version": "1.0",
        "source": str(source),
        "is_llm_benchmark": False,
        "note": "仅对提供的输出做结构化证据比较；未调用独立模型端点。",
        "cases": results,
        "passed": all(item["status"] == "PASS" for item in results),
    }
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["passed"] or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
