#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check competition-specific AI disclosure evidence without judging AI style.

This is a profile-gated compliance check.  It verifies the 2026 CUMCM
disclosure location and supporting PDF after the official effective date; it
does not attempt to classify prose as AI-generated.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = SKILL_ROOT / "planner" / "competition_profiles" / "guosai_2026_ai.json"
REFERENCE_MARKERS = ("参考文献", "文献资料", "References", "REFERENCES")
NO_AI_PATTERNS = ("未使用任何AI工具", "未使用任何 AI 工具", "未使用人工智能工具")
USE_AI_PATTERNS = ("使用了AI工具", "使用了 AI 工具", "使用人工智能工具")


def load_profile(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("AI profile must be a JSON object")
    return payload


def text_from_path(path: Path) -> str:
    if path.is_file() and path.suffix.lower() in {".tex", ".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if path.is_dir():
        chunks = []
        for candidate in sorted(path.rglob("*.tex")):
            chunks.append(candidate.read_text(encoding="utf-8", errors="replace"))
        for candidate in sorted(path.rglob("*.txt")):
            chunks.append(candidate.read_text(encoding="utf-8", errors="replace"))
        if chunks:
            return "\n".join(chunks)
        pdfs = sorted(path.glob("*.pdf"), key=lambda item: item.stat().st_mtime, reverse=True)
        if pdfs:
            return text_from_pdf(pdfs[0])
    if path.suffix.lower() == ".pdf":
        return text_from_pdf(path)
    return ""


def text_from_pdf(path: Path) -> str:
    try:
        import pymupdf
        with pymupdf.open(path) as document:
            return "\n".join(page.get_text() for page in document)
    except Exception:
        return ""


def before_references(text: str) -> str:
    positions = [text.find(marker) for marker in REFERENCE_MARKERS if text.find(marker) >= 0]
    return text[:min(positions)] if positions else text


def find_detail_pdf(root: Path, filename: str) -> Path | None:
    target = filename.casefold()
    candidates = [path for path in root.rglob("*") if path.is_file() and path.name.casefold() == target]
    return sorted(candidates, key=lambda item: len(item.parts))[0] if candidates else None


def check(root: Path, paper: Path, profile: dict, as_of: date | None = None) -> dict:
    today = as_of or date.today()
    effective = date.fromisoformat(str(profile["effective_date"]))
    report = {
        "schema_version": "1.0",
        "profile_id": profile.get("profile_id"),
        "competition": profile.get("competition"),
        "effective_date": effective.isoformat(),
        "checked_date": today.isoformat(),
        "official_source": profile.get("official_source"),
        "issues": [],
        "warnings": [],
    }
    if today < effective:
        report["status"] = "INFO"
        report["message"] = "官方 AI 规定尚未到生效日期；本次仅登记，不阻断交付。"
        return report

    paper_text = before_references(text_from_path(paper))
    no_ai = any(pattern in paper_text for pattern in NO_AI_PATTERNS)
    used_ai = any(pattern in paper_text for pattern in USE_AI_PATTERNS)
    declaration_heading = str(profile.get("declaration_heading", "AI工具使用声明"))
    heading_present = declaration_heading in paper_text or "AI 工具使用声明" in paper_text
    report["declaration"] = {"heading": heading_present, "no_ai": no_ai, "used_ai": used_ai}

    if not heading_present or not (no_ai or used_ai):
        report["issues"].append("参考文献前缺少可识别的 AI 工具使用声明")
    if no_ai and used_ai:
        report["issues"].append("同时出现未使用 AI 与使用 AI 的互斥声明")
    if used_ai:
        detail_name = str(profile.get("detail_filename", "AI工具使用详情.pdf"))
        detail = find_detail_pdf(root, detail_name)
        report["detail_file"] = str(detail) if detail else None
        if detail is None:
            report["issues"].append(f"使用 AI 时缺少支撑材料: {detail_name}")
        else:
            detail_text = text_from_pdf(detail)
            expected = {
                "tool_name_and_version": ("工具", "版本", "型号"),
                "purpose_and_stage": ("用途", "环节", "目的"),
                "prompt_or_interaction_summary": ("提示", "交互", "过程"),
                "adoption_and_human_review": ("人工", "核验", "修改", "采纳"),
            }
            configured_fields = profile.get("detail_fields") or list(expected)
            missing = [key for key in configured_fields
                       if key in expected and detail_text
                       and not any(term in detail_text for term in expected[key])]
            if detail_text and missing:
                report["issues"].append("AI 工具详情 PDF 缺少必填字段: " + ", ".join(missing))
            elif not detail_text:
                report["warnings"].append("AI 工具详情 PDF 无可提取文本，需人工确认内容")

    if report["issues"]:
        report["status"] = "BLOCK"
    elif report["warnings"]:
        report["status"] = "WARN"
    else:
        report["status"] = "PASS"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--paper-dir", type=Path, default=None)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--as-of", default=None, help="测试用日期 YYYY-MM-DD；默认使用今天")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    root = args.project_root.resolve()
    paper = (root / args.paper_dir).resolve() if args.paper_dir and not args.paper_dir.is_absolute() else (args.paper_dir.resolve() if args.paper_dir else root)
    try:
        as_of = date.fromisoformat(args.as_of) if args.as_of else None
        report = check(root, paper, load_profile(args.profile.resolve()), as_of)
    except Exception as exc:
        report = {"schema_version": "1.0", "status": "BLOCK", "issues": [str(exc)]}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.out.resolve().write_text(payload, encoding="utf-8")
    print(f"[{report['status']}] AI 合规 profile: {report.get('profile_id', 'unknown')}")
    print(payload, end="")
    return 1 if report["status"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
