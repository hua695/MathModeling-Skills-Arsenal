#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build an evidence-aware execution plan for contest-orchestrator.

This command only plans and reports. It never solves, compiles, edits a paper,
or silently upgrades a task into FULL_CONTEST.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0"
SCOPES = ("PLAN_ONLY", "SUBPROBLEM", "FULL_CONTEST", "DELIVERY_AUDIT")
TEMP_MARKERS = ("\\appdata\\local\\temp\\", "\\temp\\", "/tmp/", "/var/tmp/")
EXCLUDED_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "build", "dist", "cache", "reports"}
SKILL_ROOT = Path(__file__).resolve().parents[1]

SCOPE_PLAN = {
    "PLAN_ONLY": {
        "strictness": "STANDARD",
        "phases": ["A1", "A1.5", "A2", "A5"],
        "gates": ["input declaration", "assumptions and variables traceability"],
        "forbidden": ["solve", "write full paper", "delivery gate", "replay"],
        "read_only": True,
    },
    "SUBPROBLEM": {
        "strictness": "STANDARD",
        "phases": ["targeted execution", "result provenance", "sensitivity or feasibility"],
        "gates": ["reproducible code", "units/bounds/magnitude", "result source"],
        "forbidden": ["silent full-paper generation", "full delivery package"],
        "read_only": False,
    },
    "FULL_CONTEST": {
        "strictness": "STRICT",
        "phases": list("ABCDEFG"),
        "gates": ["all phase checkpoints", "consistency", "figures", "citations", "PDF", "stable delivery"],
        "forbidden": ["skip a failed gate", "fabricate evidence", "use temporary root as formal delivery"],
        "read_only": False,
    },
    "DELIVERY_AUDIT": {
        "strictness": "STANDARD",
        "phases": ["F4", "F4.x", "F5"],
        "gates": ["evidence existence", "text layer", "page/layout", "citations", "gate status"],
        "forbidden": ["re-solve", "redraw", "edit or overwrite the audited project"],
        "read_only": True,
    },
}


def read_skill_version() -> str | None:
    root = Path(__file__).resolve().parents[1]
    version_file = root / "VERSION"
    if version_file.exists():
        value = version_file.read_text(encoding="utf-8", errors="replace").strip()
        if re.fullmatch(r"\d+\.\d+(?:\.\d+)?", value):
            return value
    skill = root / "SKILL.md"
    match = re.search(r"^\s+version:\s*[\"']?([^\"'\s]+)", skill.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
    return match.group(1) if match else None


def is_inside_skill_root(path: Path | None) -> bool:
    """Return whether path is the skill install root or one of its children."""
    if path is None:
        return False
    try:
        path.resolve().relative_to(SKILL_ROOT)
        return True
    except ValueError:
        return False


def infer_scope(prompt: str) -> str:
    text = prompt.lower()
    explicit = re.search(r"\b(plan_only|subproblem|full_contest|delivery_audit)\b", text)
    if explicit:
        return explicit.group(1).upper()
    paper_full = any(word in text for word in ("写", "生成", "完成", "撰写")) and "论文" in text
    if any(word in text for word in ("正式提交", "正式交付", "完整论文", "全流程", "开始建模")) or (
        paper_full and any(word in text for word in ("完整", "全文", "交付", "验证", "严格", "提交"))
    ):
        return "FULL_CONTEST"
    if any(word in text for word in ("审计", "检查", "模拟评审", "找问题")):
        return "DELIVERY_AUDIT"
    if any(word in text for word in ("求解", "敏感性", "出图", "改一个章节", "问题二")):
        return "SUBPROBLEM"
    return "PLAN_ONLY"


def classify_evidence(root: Path | None) -> dict:
    evidence = {"problem": [], "data": [], "results": [], "paper": [], "audit": []}
    if root is None or not root.exists():
        return {key: [] for key in evidence}
    # The skill installation contains fixtures, replay archives and historical
    # papers. They are not a user project and must never satisfy an input gate.
    if is_inside_skill_root(root):
        return evidence
    if root.is_file():
        candidates = [root]
    else:
        candidates = [path for path in root.rglob("*") if path.is_file()
                      and not any(part.lower() in EXCLUDED_DIRS for part in path.parts)]
    for path in candidates:
        name = path.name.lower()
        rel = str(path.relative_to(root)) if path != root else path.name
        if path.suffix.lower() in {".pdf", ".docx"} and any(token in name for token in ("题", "problem", "附件")):
            evidence["problem"].append(rel)
        elif path.suffix.lower() in {".xlsx", ".xls", ".csv", ".tsv"}:
            evidence["data"].append(rel)
        elif path.suffix.lower() in {".json", ".csv", ".xlsx", ".xls", ".parquet"} and any(
                token in name for token in ("result", "sensitivity", "baseline", "figure_registry")):
            evidence["results"].append(rel)
        elif path.suffix.lower() in {".tex", ".bib", ".pdf", ".docx"}:
            evidence["paper"].append(rel)
        if any(token in name for token in ("report", "manifest", "audit", "log")):
            evidence["audit"].append(rel)
    return {key: sorted(set(value)) for key, value in evidence.items()}


def has_required_evidence(scope: str, evidence: dict) -> tuple[bool, str]:
    if scope == "PLAN_ONLY":
        return True, "允许无真实文件，但必须在输出中标记抽象规划"
    if scope == "SUBPROBLEM":
        ok = bool(evidence["problem"] or evidence["data"] or evidence["results"])
        return ok, "需要题面、数据或结果文件" if not ok else "已找到子问题执行证据"
    if scope == "FULL_CONTEST":
        ok = bool(evidence["problem"] or evidence["data"])
        return ok, "需要题面或附件，缺失时禁止虚构并停止" if not ok else "已找到全流程输入证据"
    ok = bool(evidence["paper"] or evidence["results"] or evidence["audit"])
    return ok, "需要 PDF/TeX/DOCX/结果或审计报告" if not ok else "已找到审计证据"


def build_plan(scope: str, workspace: Path | None, prompt: str = "", strict: bool = False,
               mode: str | None = None) -> dict:
    if scope not in SCOPES:
        raise ValueError(f"unknown scope: {scope}")
    evidence = classify_evidence(workspace)
    evidence_ok, evidence_message = has_required_evidence(scope, evidence)
    canonical = bool(workspace) and not any(marker in str(workspace).lower() for marker in TEMP_MARKERS + ("\\tmp\\",))
    warnings = []
    if is_inside_skill_root(workspace):
        canonical = False
        warnings.append("项目根目录位于技能安装目录：技能内的 replay/历史产物不会作为正式项目输入")
    if scope == "PLAN_ONLY" and not any(evidence.values()):
        warnings.append("未读取真实题面或附件：仅输出抽象计划，不得声称已验证数据")
    if scope != "PLAN_ONLY" and is_inside_skill_root(workspace):
        evidence_ok = False
        evidence_message = "技能安装目录不能作为项目根目录，请使用独立项目工作区"
    elif scope == "FULL_CONTEST" and not canonical:
        warnings.append("当前根目录不是稳定项目路径：可用于测试，但不能作为正式交付根目录")
    if strict and warnings:
        evidence_ok = False
    plan = SCOPE_PLAN[scope]
    phases = plan["phases"]
    gates = plan["gates"]
    if mode == "full-contest-mathorcup":
        if scope != "FULL_CONTEST":
            evidence_ok = False
            warnings.append("MathorCup 模式只能用于 FULL_CONTEST 范围")
        else:
            phases = ["M1", "M2", "M3", "M4", "M5"]
            gates = ["node approval", "independent verification", "literature source gate",
                     "visual and writing plan approval", "chapter approval", "reproducibility and delivery"]
    return {
        "schema_version": SCHEMA_VERSION,
        "skill_version": read_skill_version(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "active_mode": mode,
        "strictness": "STRICT" if strict else plan["strictness"],
        "prompt": prompt,
        "workspace": str(workspace) if workspace else None,
        "canonical_workspace": canonical,
        "read_only": plan["read_only"],
        "evidence": evidence,
        "input_gate": {"status": "PASS" if evidence_ok else "FAIL", "message": evidence_message},
        "phases": phases,
        "gates": gates,
        "forbidden_actions": plan["forbidden"],
        "warnings": warnings,
        "execution_status": "READY" if evidence_ok else "BLOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=SCOPES, default=None)
    parser.add_argument("--mode", choices=("full-contest-mathorcup",), default=None)
    parser.add_argument("--prompt", default="")
    parser.add_argument("--workspace", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    scope = args.scope or ("FULL_CONTEST" if args.mode == "full-contest-mathorcup" else infer_scope(args.prompt))
    workspace = args.workspace.resolve() if args.workspace else None
    report = build_plan(scope, workspace, args.prompt, args.strict, args.mode)
    canonical = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    report["plan_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    console_utf8 = "utf" in str(getattr(sys.stdout, "encoding", "")).lower()
    payload = json.dumps(report, ensure_ascii=not console_utf8, indent=2) + "\n"
    if args.out:
        out = args.out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["execution_status"] == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
