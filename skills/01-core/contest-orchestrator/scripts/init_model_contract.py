#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create a reviewable enhanced modeling contract skeleton without inventing evidence."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from check_modeling_contract import expand_inputs, locate_tex

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def chinese_number(value: str) -> int | None:
    """Parse common Chinese question numbering, including 十一 and 二十."""
    if value.isdigit():
        return int(value)
    digits = {char: index for index, char in enumerate("一二三四五六七八九", 1)}
    if value == "十":
        return 10
    if value.startswith("十"):
        return 10 + digits.get(value[1:], 0)
    if "十" in value:
        left, right = value.split("十", 1)
        return digits.get(left, 0) * 10 + digits.get(right, 0)
    return digits.get(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_or_paper")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.project_or_paper).resolve()
    tex_root = root if list(root.glob("*.tex")) else root / "03_文档" / "paper"
    tex = locate_tex(tex_root)
    text = expand_inputs(tex.read_text(encoding="utf-8", errors="replace"), tex.parent)
    import re
    headings = re.findall(r"\\subsection\*?\{([^{}]*(?:问题\s*[一二三四五六七八九十\d]+|Q\s*[1-9]))[^{}]*\}", text, re.I)
    ids = []
    for title in headings:
        match = re.search(r"Q\s*([0-9]+)|问题\s*([一二三四五六七八九十]+)", title, re.I)
        if match:
            number = match.group(1) or str(chinese_number(match.group(2)) or "")
            qid = f"Q{number}"
            if qid not in ids:
                ids.append(qid)
    if not ids:
        raise SystemExit("未识别到问题子节，请先补充 \\subsection{问题一} 等明确边界")
    payload = {
        "schema_version": "2.1",
        "contract_version": "v4.13",
        "evidence_quality": "enhanced",
        "reader_evidence_version": "1.0",
        "status": "draft",
        "subproblems": [
            {
                "id": qid,
                "primary_capability": "REVIEW_REQUIRED",
                "capabilities": [],
                "text_anchor": qid,
                "evidence": {
                    "problem_mapping": {"status": "pending", "text_anchors": [], "source_files": []},
                    "assumptions": {"status": "pending", "text_anchors": [], "source_files": []},
                    "symbols_units": {"status": "pending", "text_anchors": [], "source_files": []},
                    "route_comparison": {"status": "pending", "text_anchors": [], "source_files": []},
                    "algorithm_card": {"status": "pending", "text_anchors": [], "source_files": []},
                    "intermediate_results": {"status": "pending", "text_anchors": [], "source_files": []},
                    "literature_basis": {"status": "pending", "text_anchors": [], "source_files": []},
                    "innovation_delta": {"status": "pending", "text_anchors": [], "source_files": []},
                    "result_source": {"status": "pending", "text_anchors": [], "source_files": []},
                    "reliability": {"status": "pending", "text_anchors": [], "source_files": []}
                },
                "reader_evidence": {
                    "problem_need": "",
                    "model_choice_reason": "",
                    "data_scope": {
                        "mode": "hybrid",
                        "shared_inputs": [],
                        "question_specific_inputs": [],
                        "placement_rationale": "",
                    },
                    "assumption_traceability": [],
                    "derivation_arc": [],
                    "final_model_reading": "",
                    "evaluation": {
                        "strengths": [],
                        "limitations": [],
                        "improvements": [],
                    },
                },
            } for qid in ids
        ]
    }
    out = Path(args.out).resolve() if args.out else root / "model_contract.yaml"
    if out.exists():
        raise SystemExit(f"目标已存在，为避免覆盖用户内容而停止: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
