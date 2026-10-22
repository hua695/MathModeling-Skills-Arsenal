#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only structural and dependency health check for contest-orchestrator."""
from __future__ import annotations

import argparse
import json
import re
import os
import subprocess
import sys
import tokenize
from datetime import datetime, timezone
from pathlib import Path


def _read_python_source(path: Path) -> str:
    """Read a Python source file with BOM and coding-cookie detection.

    Uses tokenize.open() so that UTF-8 BOM files and explicit coding
    declarations are decoded correctly.  Falls back to UTF-8 with
    replacement on any decoding error so the health check never crashes
    on a malformed file; compile() will still report syntax errors.
    """
    try:
        with tokenize.open(str(path)) as fh:
            return fh.read()
    except (SyntaxError, UnicodeDecodeError, OSError):
        return path.read_text(encoding="utf-8", errors="replace")

try:
    from check_skill_consistency import check as check_skill_consistency
except ImportError:
    check_skill_consistency = None

REQUIRED_FILES = (
    "SKILL.md", "manifest.yaml", "VERSION", "token_policy.md", "AGENTS.md", "MEMORY.md",
    "planner/problem_parser.md", "memory/retrieval.py", "memory/blueprint_retrieval.py",
    "scripts/check_core_execution.py", "scripts/delivery_all.py", "scripts/delivery_gate.py",
    "scripts/check_abstract_contract.py", "scripts/check_result_code_consistency.py",
    "scripts/check_modeling_solution_contract.py", "scripts/replay_profiles.py",
    "scripts/check_latex_appendix_contract.py", "schemas/appendix_contract.schema.json",
    "scripts/collab_gate.py", "scripts/check_visual_evidence.py", "schemas/visual_argument_plan.schema.json",
    "schemas/visual_evidence_packet.schema.json", "templates/visual_evidence_packet.yaml",
    "references/collab_gate_policy.md", "references/appendix_coverage_policy.md",
    "references/incremental_validation_policy.md", "schemas/change_impact_card.schema.json",
    "templates/change_impact_card.yaml", "templates/competition_run_profile.yaml",
    "templates/collab_gate_policy.yaml", "templates/visual_argument_plan.yaml",
    "templates/visual_plan_review_packet.yaml", "templates/b_project_template/visual_evidence_packet.yaml",
    "scripts/check_skill_consistency.py", "scripts/script_registry.yaml",
    "scripts/delivery_manifest.py", "scripts/compile_paper.py", "scripts/verify_doi.py",
    "scripts/latex_warning_check.py", "scripts/scope_router.py", "scripts/audit_project.py",
    "scripts/capture_run.py", "scripts/check_run_manifest.py", "scripts/check_h5_result_traceability.py", "scripts/check_stale_evidence.py",
    "scripts/audit_numeric_sources.py", "scripts/compute_readiness.py", "scripts/validation_router.py",
    "schemas/run_manifest.schema.json", "schemas/numeric_source_map.schema.json", "schemas/readiness.schema.json",
)
REQUIRED_DEPENDENCIES = (
    "data-science-stack", "pyomo", "heuristic-algorithms", "modelviz", "scipilot-figure-skill",
    "tech-route-maker", "tikz-scientific-figures", "drawio-diagram", "mathmodel-latex-skill",
    "bzd-review-paper", "academic-writing", "web-access", "math-model-selector", "humanizer-zh",
)
FORBIDDEN_REQUIRED_DEPENDENCIES = ("figure-generation", "fireworks-tech-graph")


def version(text: str) -> str | None:
    match = re.search(r"^(?:version|\s+version):\s*[\"']?([^\"'\s]+)", text, re.MULTILINE)
    return match.group(1) if match else None


def check(root: Path, strict: bool = False, smoke: bool = False) -> dict:
    root = root.resolve()
    skill_root = root.parent
    failures: list[str] = []
    warnings: list[str] = []
    info: list[str] = []
    if check_skill_consistency is not None:
        consistency = check_skill_consistency(root)
        failures.extend(consistency.get("failures", []))
        warnings.extend(consistency.get("warnings", []))
        info.extend(f"consistency: {item}" for item in consistency.get("info", []))
    for relative in REQUIRED_FILES:
        if not (root / relative).exists():
            failures.append(f"missing required file: {relative}")

    skill_text = (root / "SKILL.md").read_text(encoding="utf-8", errors="replace") if (root / "SKILL.md").exists() else ""
    manifest_text = (root / "manifest.yaml").read_text(encoding="utf-8", errors="replace") if (root / "manifest.yaml").exists() else ""
    skill_version = version(skill_text)
    manifest_version = version(manifest_text)
    version_file = (root / "VERSION").read_text(encoding="utf-8", errors="replace").strip() if (root / "VERSION").exists() else ""
    if not skill_version or not manifest_version or skill_version != manifest_version or version_file != skill_version:
        failures.append("SKILL.md, manifest.yaml, and VERSION must contain the same version")
    else:
        info.append(f"version={skill_version}")

    manifest_schema = re.search(r"^schema_version:\s*[\"']?([^\"'\s]+)", manifest_text, re.MULTILINE)
    if not manifest_schema:
        failures.append("manifest.yaml is missing schema_version")

    for dependency in REQUIRED_DEPENDENCIES:
        if not (skill_root / dependency / "SKILL.md").exists():
            failures.append(f"missing required dependency: {dependency}")
    for dependency in FORBIDDEN_REQUIRED_DEPENDENCIES:
        if re.search(rf"^\s*-\s+{re.escape(dependency)}\s*$", manifest_text, re.MULTILINE):
            failures.append(f"deprecated dependency remains required: {dependency}")

    if ("modelviz" not in skill_text or "scipilot-figure-skill" not in skill_text
            or "tech-route-maker" not in skill_text or "tikz-scientific-figures" not in skill_text):
        failures.append("figure routing policy is not explicit in SKILL.md")
    if "scripts/scope_router.py" not in skill_text:
        failures.append("SKILL.md does not expose the executable scope router")
    if any(name in skill_text for name in ("diagram-design", "fireworks-tech-graph", "generator=manual")):
        failures.append("SKILL.md still contains a deprecated or ambiguous figure route")

    for path in sorted(root.rglob("*.py")):
        if "archive" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            compile(_read_python_source(path), str(path), "exec")
        except SyntaxError as exc:
            failures.append(f"syntax error: {path.relative_to(root)}:{exc.lineno}")

    hardcoded = re.compile(r"(?:C:\\\\Users\\\\USER|/Users/USER|/home/USER)", re.IGNORECASE)
    for part in ("scripts", "planner", "executor", "memory"):
        path = root / part
        if not path.exists():
            continue
        for file in path.rglob("*.py"):
            if "archive" in file.parts or "__pycache__" in file.parts:
                continue
            if file.name in {"skill_health_check.py", "public_sync.py"}:
                continue
            if hardcoded.search(_read_python_source(file)):
                failures.append(f"profile-specific absolute path: {file.relative_to(root)}")

    archive_dir = root / "scripts" / "archive"
    if archive_dir.exists():
        archived = sum(1 for path in archive_dir.rglob("*") if path.is_file())
        info.append(f"historical scripts isolated from active path scan: {archived} files")
        readme = archive_dir / "README.md"
        if not readme.exists():
            failures.append("scripts/archive 缺少隔离说明 README.md")

    for raw in re.findall(r"^\s*-\s+([^#\n]+)", manifest_text, re.MULTILINE):
        candidate = raw.strip().strip("'\"").split(" #", 1)[0].strip()
        if not candidate or candidate.startswith("<") or "[" in candidate or "*" in candidate or any(ch in candidate for ch in (":", "|")):
            continue
        if not (root / candidate).exists() and not any((root / candidate).glob("*")):
            warnings.append(f"manifest reference not found: {candidate}")

    for path in root.glob("SKILL_v*_backup.md"):
        if path.name not in manifest_text or "never_auto_load" not in manifest_text:
            info.append(f"historical backup isolated from auto-load routes: {path.name}")
    if smoke:
        smoke_script = root / "scripts" / "smoke_test.py"
        if not smoke_script.exists():
            failures.append("requested smoke check but scripts/smoke_test.py is missing")
        else:
            smoke_env = os.environ.copy()
            smoke_env["PYTHONUTF8"] = "1"
            smoke_env["PYTHONIOENCODING"] = "utf-8"
            smoke_env["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = subprocess.run(
                [sys.executable, str(smoke_script)],
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=smoke_env,
            )
            if completed.returncode:
                tail = ((completed.stdout or "") + (completed.stderr or ""))[-500:].strip()
                failures.append(f"full smoke failed (exit {completed.returncode}): {tail}")
            else:
                info.append("full smoke=PASS")
    if strict:
        failures.extend(warnings)
        warnings = []
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(), "root": str(root),
        "version": skill_version, "passed": not failures,
        "failures": failures, "warnings": warnings, "info": info,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--smoke", action="store_true", help="run the full non-mutating smoke suite")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()
    report = check(args.root, strict=args.strict, smoke=args.smoke)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS" if report["passed"] else "FAIL")
    for item in report["info"]:
        print(f"- INFO: {item}")
    for item in report["warnings"]:
        print(f"- WARN: {item}")
    for item in report["failures"]:
        print(f"- FAIL: {item}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
