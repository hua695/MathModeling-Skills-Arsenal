#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run read-only paper audits against an isolated copy of a project.

The source project is never compiled or written.  Reports are written only to
the explicit ``--out`` path (or stdout when omitted).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
AUDIT_IGNORED_NAMES = {
    ".git", "node_modules", "__pycache__", ".learnings", ".work", "tmp",
    "logs", "log", "review", "reviews", "debug",
}
AUDIT_IGNORED_MARKERS = ("snapshot", "before", "after", "快照", "历史")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def paper_dir(root: Path, explicit: str | None) -> Path:
    if explicit:
        return (root / explicit).resolve() if not Path(explicit).is_absolute() else Path(explicit).resolve()
    if (root / "paper" / "paper.pdf").exists() or (root / "paper" / "paper.tex").exists():
        return root / "paper"
    return root


def isolated_copy_ignore(path: str, names: list[str]) -> set[str]:
    """Keep recursive snapshots and diagnostics out of the audit copy."""
    ignored = set()
    for name in names:
        lowered = name.casefold()
        if lowered in AUDIT_IGNORED_NAMES or any(marker in lowered for marker in AUDIT_IGNORED_MARKERS):
            ignored.add(name)
    return ignored


def run(name: str, command: list[str], cwd: Path) -> dict:
    started = datetime.now(timezone.utc)
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=900)
        output = (result.stdout + ("\n[stderr]\n" + result.stderr if result.stderr else "")).strip()
        status = "PASS" if result.returncode == 0 else "FAIL"
        if status == "PASS" and re.search(r"^\s*\[WARN\]|\b状态\s*[:：]\s*WARN\b", output, re.MULTILINE):
            status = "WARN"
    except subprocess.TimeoutExpired as exc:
        output, status, result = f"timeout: {exc}", "FAIL", None
    except OSError as exc:
        output, status, result = str(exc), "FAIL", None
    return {
        "name": name,
        "status": status,
        "returncode": result.returncode if result is not None else 127,
        "output_tail": output[-4000:],
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }


def visual_audit_result(pdf: Path, cwd: Path, enabled: bool) -> dict:
    """Run the expensive visual critic only after explicit opt-in."""
    if not enabled:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "name": "visual_critic",
            "status": "SKIPPED",
            "returncode": 0,
            "output_tail": "SKIPPED_USER_OPT_IN: visual inspection is disabled by default; user visual review is the default substitute",
            "started_at": now,
            "finished_at": now,
        }
    return run("visual_critic", [sys.executable, str(SCRIPTS / "visual_critic.py"), str(pdf)], cwd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--paper-dir", default=None)
    parser.add_argument("--competition", default="guosai", choices=("guosai", "huashu", "mcm_icm"))
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--research-evidence-strict", action="store_true",
                        help="在只读隔离副本中启用研究证据链严格门禁")
    parser.add_argument("--visual-check", action="store_true",
                        help="显式启用自动视觉质检；默认跳过，由用户肉眼检查")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    source = args.workspace.resolve()
    if not source.is_dir():
        print(f"[FAIL] workspace not found: {source}")
        return 2
    source_paper = paper_dir(source, args.paper_dir)
    if not source_paper.is_dir():
        print(f"[FAIL] paper directory not found: {source_paper}")
        return 2
    pdfs = sorted(source_paper.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    pdf = pdfs[0] if pdfs else None
    if pdf is None:
        print(f"[FAIL] no PDF found in {source_paper}")
        return 2

    source_hashes = {str(path.relative_to(source)): digest(path) for path in
                     (source_paper / "paper.tex", pdf, source_paper / "ref.bib") if path.exists()}
    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="contest-audit-") as raw:
        isolated = Path(raw) / source.name
        shutil.copytree(source, isolated, ignore=isolated_copy_ignore)
        isolated_paper = paper_dir(isolated, args.paper_dir)
        isolated_pdf = isolated_paper / pdf.name
        delivery_cmd = [sys.executable, str(SCRIPTS / "delivery_gate.py"),
                        str(isolated_paper), "--competition", args.competition,
                        "--pdf", str(isolated_pdf)]
        if args.visual_check:
            delivery_cmd.append("--visual-check")
        results.append(run("delivery_gate", delivery_cmd, isolated))
        results.append(run("paper_hard_requirements", [sys.executable, str(SCRIPTS / "check_paper_hard_requirements.py"),
                                                         str(isolated_pdf)], isolated))
        results.append(visual_audit_result(isolated_pdf, isolated, args.visual_check))
        results.append(run("latex_warning_check", [sys.executable, str(SCRIPTS / "latex_warning_check.py"),
                                                    str(isolated_paper)], isolated))
        citation_args = [sys.executable, str(SCRIPTS / "check_literature_citation.py"), str(isolated_pdf),
                         "--replay-dir", str(isolated)]
        results.append(run("literature_citation", citation_args, isolated))
        if args.research_evidence_strict:
            results.append(run(
                "research_evidence",
                [sys.executable, str(SCRIPTS / "check_research_evidence.py"), str(isolated), "--strict"],
                isolated,
            ))

    warnings = [item for item in results if item["status"] == "PASS" and "WARN" in item["output_tail"]]
    blocking = [item["name"] for item in results if item["status"] == "FAIL"]
    if args.strict:
        blocking.extend(item["name"] for item in warnings)
    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workspace": str(source),
        "paper_dir": str(source_paper),
        "read_only": True,
        "source_hashes": source_hashes,
        "strict": args.strict,
        "visual_check_requested": args.visual_check,
        "visual_check_status": "EXECUTED" if args.visual_check else "SKIPPED_USER_OPT_IN",
        "research_evidence_strict": args.research_evidence_strict,
        "passed": not blocking,
        "blocking_steps": blocking,
        "results": results,
    }
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out = args.out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
    try:
        print(payload, end="")
    except UnicodeEncodeError:
        print(payload.encode("ascii", "backslashreplace").decode("ascii"), end="")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
