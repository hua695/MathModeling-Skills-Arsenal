#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical compile → audit → package pipeline for a contest paper."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS.parent
TEMP_MARKERS = ("\\AppData\\Local\\Temp\\", "/AppData/Local/Temp/", "\\Temp\\", "/tmp/")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def emit(value: str) -> None:
    try:
        print(value, flush=True)
    except UnicodeEncodeError:
        print(value.encode("utf-8", "replace").decode("utf-8", "replace"), flush=True)


def structured_warning(text: str) -> bool:
    """Detect explicit tool WARN records without treating deprecation noise as a gate."""
    patterns = (r"^\s*\[WARN\]", r"^\s*WARN(?:\b|:)", r"\b状态\s*[:：]\s*WARN\b",
                r"\b结果\s*[:：]\s*WARN\b", r"\bWARN\s*$",
                r"\"(?:gate_status|status|result)\"\s*:\s*\"WARN\"")
    return any(re.search(pattern, text, re.MULTILINE | re.IGNORECASE) for pattern in patterns)


def verify_scope_plan(path: Path, expected_scope: str) -> tuple[bool, str, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"scope plan 无法解析: {exc}", None
    digest = payload.get("plan_digest")
    unsigned = dict(payload)
    unsigned.pop("plan_digest", None)
    canonical = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    actual = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if not digest or digest != actual:
        return False, "scope plan digest 不匹配，禁止执行", digest
    if payload.get("scope") != expected_scope or payload.get("execution_status") != "READY":
        return False, "scope plan 与入口范围或 input_gate 不匹配", digest
    return True, "scope plan 已验证", digest


def find_paper_dir(root: Path, explicit: str | None) -> Path:
    if explicit:
        candidate = Path(explicit)
        return (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    if (root / "paper.tex").exists() or (root / "paper_pandoc.tex").exists():
        return root
    if (root / "paper").is_dir():
        return root / "paper"
    return root


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def refresh_compiled_paper_evidence(root: Path, tex: Path, pdf: Path) -> dict:
    """Refresh only paper artifacts that this invocation has just compiled.

    Solver inputs, code, configurations, and numerical outputs are deliberately
    untouched, so stale-evidence gates still catch any model-side drift.
    """
    targets = {tex.resolve(): _sha256(tex), pdf.resolve(): _sha256(pdf)}
    updated: list[str] = []
    errors: list[str] = []
    run_root = root / ".contest" / "runs"
    if not run_root.is_dir():
        return {"updated": updated, "errors": errors}
    for manifest_path in sorted(run_root.glob("*/run_manifest.json")):
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            outputs = payload.get("outputs", [])
            if not isinstance(outputs, list):
                raise ValueError("outputs 必须是数组")
            changed = False
            for item in outputs:
                if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                    continue
                candidate = (root / item["path"]).resolve()
                if candidate in targets and item.get("sha256") != targets[candidate]:
                    item["sha256"] = targets[candidate]
                    updated.append(f"{manifest_path.relative_to(root)}:{item['path']}")
                    changed = True
            if changed:
                manifest_path.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{manifest_path.relative_to(root)}: {exc}")
    return {"updated": updated, "errors": errors}


def sync_formal_delivery(root: Path, tex: Path, pdf: Path, report_dir: Path) -> dict:
    """Create or refresh a formal package after all content gates have passed.

    This is intentionally called only through the explicit
    ``--sync-formal-delivery`` release action. Compilation may change PDF
    metadata even when source content is unchanged, so copying before compile
    makes the later drift check fail by construction.
    """
    formal = root / "05_输出与交付" / "正式交付"
    formal.mkdir(parents=True, exist_ok=True)
    delivery_root = root / "05_输出与交付"
    sources = [
        (pdf, formal / "final_submission.pdf"),
        (tex, formal / "paper.tex"),
        (tex.parent / "delivery_manifest.json", formal / "delivery_manifest.json"),
        (root / "references.yaml", formal / "references.yaml"),
    ]
    # Projects commonly keep generated registries under the standard output
    # directory rather than the repository root.  Resolve both layouts before
    # declaring an optional artifact missing.
    registry_candidates = (
        root / "figure_registry.json",
        delivery_root / "figure_registry.json",
        tex.parent / "figure_registry.json",
    )
    registry = next((path for path in registry_candidates if path.is_file()), None)
    if registry is not None:
        sources.append((registry, formal / "figure_registry.json"))
    citation_candidates = (root / "citation_map.json", root / "01_需求与规划" / "citation_map.json")
    citation = next((path for path in citation_candidates if path.is_file()), None)
    if citation is not None:
        sources.append((citation, formal / "citation_map.json"))
    archive_candidates = list(delivery_root.glob("support_materials_*.zip"))
    archive_candidates.extend(delivery_root.glob("support_materials_*.rar"))
    archive_candidates.extend(tex.parent.glob("support_materials_*.zip"))
    archive_candidates.extend(tex.parent.glob("support_materials_*.rar"))
    seen_archives: set[Path] = set()
    for archive in sorted(archive_candidates):
        archive = archive.resolve()
        if archive in seen_archives:
            continue
        seen_archives.add(archive)
        sources.append((archive, formal / archive.name))

    copied: list[str] = []
    missing: list[str] = []
    for source, destination in sources:
        if source.is_file():
            shutil.copy2(source, destination)
            copied.append(destination.name)
        else:
            missing.append(str(source.relative_to(root)))

    reports_target = formal / "reports"
    reports_target.mkdir(exist_ok=True)
    for source in sorted(report_dir.glob("*")):
        if source.is_file():
            shutil.copy2(source, reports_target / source.name)

    roles = {
        "final_submission.pdf": "正式论文 PDF",
        "paper.tex": "LaTeX 源文件",
        "figure_registry.json": "图表来源与 QA 注册表",
        "references.yaml": "文献元数据",
        "citation_map.json": "正文引用作用映射",
        "delivery_manifest.json": "生成过程的文件清单",
    }
    for archive in sorted(formal.glob("support_materials_*.zip")):
        roles[archive.name] = "完整源码、结果 JSON 与绘图脚本"
    for archive in sorted(formal.glob("support_materials_*.rar")):
        roles[archive.name] = "完整源码、结果 JSON 与绘图脚本"
    lines = [
        "# 正式交付文件索引",
        "",
        "本目录由严格交付流程在全部内容门禁通过后生成。所有条目均以 SHA-256 固化；提交前若任一文件发生变化，须重新执行严格交付流程并更新本索引。",
        "",
        "| 文件 | 作用 | SHA-256 |",
        "|---|---|---|",
    ]
    for name, role in roles.items():
        artifact = formal / name
        if artifact.is_file():
            lines.append(f"| `{name}` | {role} | `{_sha256(artifact).upper()}` |")
    lines.extend(["", "`reports/` 保存本次严格回放的阶段性报告；它们用于复核，不替代上述正式材料。", ""])
    (formal / "FINAL_INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    return {"formal_dir": str(formal), "copied": copied, "missing_optional": missing}


def resolve_report_dir(root: Path, raw: str | None) -> Path:
    """Resolve reports inside the project, never relative to the skill process cwd."""
    candidate = Path(raw) if raw else Path("05_输出与交付/delivery_report")
    resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    skill_root = SCRIPTS.parent.resolve()
    if resolved == skill_root or skill_root in resolved.parents:
        raise ValueError(f"报告目录不能位于技能安装目录: {resolved}")
    if any(marker.lower() in str(resolved).lower() for marker in TEMP_MARKERS):
        raise ValueError(f"报告目录不能位于临时目录: {resolved}")
    return resolved


def content_budget_enabled(competition: str, explicit_plan: str | None) -> bool:
    """Enable the personal 25--30 page profile only where it is declared."""
    return competition == "guosai" or explicit_plan is not None


def _blueprint_path(root: Path, explicit: str | None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    candidates = (root / "model_blueprint.yaml", root / "03_文档" / "model_blueprint.yaml",
                  root / "03_文档" / "paper" / "model_blueprint.yaml")
    return next((path.resolve() for path in candidates if path.exists()), None)


def resolve_blueprint_route(root: Path, explicit: str | None = None,
                            requested_strict: bool = False) -> dict:
    """Make hybrid blueprints strict while keeping single-family checks shadow-only."""
    path = _blueprint_path(root, explicit)
    if requested_strict:
        return {"mode": "explicit-strict", "strict": True, "blueprint": str(path) if path else None,
                "reason": "用户显式传入 --blueprint-strict"}
    if path is None:
        return {"mode": "shadow-missing", "strict": False, "blueprint": None,
                "reason": "未发现 model_blueprint.yaml，保留单题影子检查"}
    try:
        import yaml
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        project = payload.get("project") if isinstance(payload, dict) else {}
        composition = project.get("composition") if isinstance(project, dict) else None
        hybrid = composition == "hybrid"
        if not hybrid:
            for item in payload.get("subproblems", []) if isinstance(payload, dict) else []:
                models = item.get("models", []) if isinstance(item, dict) else []
                families = {str(model.get("family")) for model in models if isinstance(model, dict)}
                if len(families) > 1:
                    hybrid = True
                    break
        if hybrid:
            return {"mode": "auto-strict-hybrid", "strict": True, "blueprint": str(path),
                    "reason": "蓝图声明 hybrid 或同一子问题包含多个模型族"}
    except Exception as exc:
        return {"mode": "shadow-unreadable", "strict": False, "blueprint": str(path),
                "reason": f"蓝图暂不能预解析，交由编译器报告: {exc}"}
    return {"mode": "shadow-single", "strict": False, "blueprint": str(path),
            "reason": "单模型族题目保留影子检查"}


def run_step(number: int, name: str, command: list[str], timeout: int = 3600) -> dict:
    emit(f"\n===== [{number}] {name} =====")
    emit("$ " + " ".join(f'"{part}"' if " " in part else part for part in command))
    started = datetime.now(timezone.utc)
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=timeout)
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        combined = (stdout + ("\n[stderr]\n" + stderr if stderr else "")).strip()
        status = "PASS" if result.returncode == 0 else "FAIL"
        if status == "PASS" and structured_warning(combined):
            status = "WARN"
    except subprocess.TimeoutExpired as exc:
        combined = f"timeout after {timeout}s\n{exc}"
        result = None
        status = "FAIL"
    except OSError as exc:
        combined = str(exc)
        result = None
        status = "FAIL"
    finished = datetime.now(timezone.utc)
    item = {"number": number, "name": name, "command": command, "status": status,
            "returncode": 0 if result is None and status == "PASS" else (result.returncode if result else 127),
            "started_at": started.isoformat(), "finished_at": finished.isoformat(),
            "duration_seconds": round((finished - started).total_seconds(), 3),
            "tail": combined[-3000:]}
    # DOI network-unavailable is a visible WARN, not a false PASS.
    if status == "PASS" and name.startswith("DOI") and '"status": "WARN"' in combined:
        item["status"] = "WARN"
    emit(item["tail"][-1200:] if item["tail"] else f"[{item['status']}]")
    emit(f"[{item['status']}] {name}")
    return item


def skipped_step(number: int, name: str, reason: str) -> dict:
    """Record an explicit opt-in skip without treating it as a PASS."""
    now = datetime.now(timezone.utc).isoformat()
    item = {"number": number, "name": name, "status": "SKIPPED",
            "returncode": 0, "started_at": now, "finished_at": now,
            "duration_seconds": 0, "tail": reason,
            "blocking_on_warn": False, "force_block": False}
    emit(f"\n[SKIPPED] {name}: {reason}")
    return item


def is_blocking(item: dict, strict: bool) -> bool:
    """Separate visible advisory WARNs from WARNs that are allowed to block."""
    return item.get("status") == "FAIL" or (
        item.get("status") == "WARN"
        and (strict or item.get("force_block", False))
        and item.get("blocking_on_warn", True)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", help="stable project/replay root")
    parser.add_argument("--competition", default="guosai", choices=("guosai", "huashu", "mcm_icm"))
    parser.add_argument("--scope", default="FULL_CONTEST",
                        choices=("FULL_CONTEST", "PLAN_ONLY", "SUBPROBLEM", "DELIVERY_AUDIT"))
    parser.add_argument("--scope-plan", default=None, help="scope_router.py 生成的已签名执行计划")
    parser.add_argument("--paper-dir", default=None)
    parser.add_argument("--doi-online", action="store_true")
    parser.add_argument("--skip-docx", action="store_true")
    parser.add_argument("--visual-check", action="store_true",
                        help="显式启用自动视觉质检与版面检查；默认跳过，由用户肉眼检查")
    parser.add_argument("--gate-config", default=None, help="project-specific competition-gate YAML; supplied official rules override defaults")
    parser.add_argument("--hard-requirements", default=None, help="project-specific paper hard-requirements JSON")
    parser.add_argument("--profile", default="mechanistic_optimization",
                        help="题型 profile：mechanistic_optimization/data_prediction/evaluation_decision/simulation_dynamics/hybrid")
    parser.add_argument("--problem-profile", default=None,
                        help="逐小问能力画像 problem_profile.yaml；A/B/C题号仅作弱先验")
    parser.add_argument("--strict", action="store_true", help="WARN also blocks final PASS")
    parser.add_argument("--mode", choices=("AUTO", "COLLAB", "LOCK"), default="AUTO",
                        help="协作模式；COLLAB 在 G0/G1/G2/G4/G5/G6 等决策包处暂停等待用户确认")
    parser.add_argument("--collab-policy", default=None,
                        help="项目侧 collab_gate_policy.yaml；COLLAB/LOCK 必填")
    parser.add_argument("--approval-log", default=None,
                        help="项目侧用户批准记录；默认 .contest/approval_log.yaml")
    parser.add_argument("--contract-strict", action="store_true",
                        help="按题型 profile 对每个 6.x 子问题执行完整证据门禁")
    parser.add_argument("--appendix-contract", default=None,
                        help="LaTeX 附录输入契约（appendix_contract.yaml/json；默认自动发现）")
    parser.add_argument("--appendix-plan", default=None,
                        help="能力驱动附录计划（appendix_plan.yaml/json；优先于旧版契约）")
    parser.add_argument("--content-budget-plan", default=None,
                        help="正文内容预算计划（content_budget_plan.yaml/json；默认自动发现）")
    parser.add_argument("--evidence-index", default=None,
                        help="项目侧派生证据索引；默认写入 .contest/evidence_index.json")
    parser.add_argument("--research-evidence-strict", action="store_true",
                        help="启用来源记录、主张映射、限制链和复现性严格门禁")
    parser.add_argument("--allow-short-paper", action="store_true",
                        help="人工确认且证据完整时允许正文低于25页进入短论文例外")
    parser.add_argument("--legacy-diagnostics", action="store_true",
                        help="额外运行附录/代码兼容诊断；不作为主契约")
    parser.add_argument("--blueprint-strict", action="store_true",
                        help="严格执行 model_blueprint.yaml 影子编译器；默认仅记录 WARN")
    parser.add_argument("--sync-formal-delivery", action="store_true",
                        help="在全部内容门禁通过后生成/刷新正式交付包，再执行漂移复核")
    parser.add_argument("--all", action="store_true", help="continue after failure for diagnostics")
    parser.add_argument("--report-dir", default=None)
    args = parser.parse_args()

    if args.scope != "FULL_CONTEST":
        emit("delivery_all.py 只接受 FULL_CONTEST；PLAN_ONLY/SUBPROBLEM 使用范围内执行器，"
             "DELIVERY_AUDIT 使用 scripts/audit_project.py。")
        return 2
    plan_digest = None
    if args.scope_plan:
        plan_path = Path(args.scope_plan).resolve()
        if not plan_path.exists():
            emit(f"[FATAL] scope plan 不存在: {plan_path}")
            return 2
        valid, message, plan_digest = verify_scope_plan(plan_path, args.scope)
        if not valid:
            emit(f"[FATAL] {message}")
            return 2
        emit(f"[PASS] {message}")

    root = Path(args.project_root).resolve()
    fatal: list[str] = []
    try:
        root.relative_to(SKILL_ROOT)
        fatal.append(f"技能安装目录不能作为正式项目根目录: {root}")
    except ValueError:
        pass
    if not root.is_dir():
        fatal.append(f"项目根目录不存在: {root}")
    if any(marker.lower() in str(root).lower() for marker in TEMP_MARKERS):
        fatal.append(f"正式交付根目录不能位于临时目录: {root}")
    if fatal:
        emit("\n".join(f"[FATAL] {item}" for item in fatal))
        return 2
    paper_dir = find_paper_dir(root, args.paper_dir) if not fatal else root
    if not paper_dir.is_dir():
        fatal.append(f"论文目录不存在: {paper_dir}")
    tex_files = sorted(paper_dir.glob("paper*.tex")) if paper_dir.is_dir() else []
    tex = tex_files[0] if tex_files else (paper_dir / "paper.tex")
    if not tex.exists():
        fatal.append(f"论文目录缺少 TeX: {tex}")
    if fatal:
        emit("\n".join(f"[FATAL] {item}" for item in fatal))
        return 2

    try:
        report_dir = resolve_report_dir(root, args.report_dir)
    except ValueError as exc:
        emit(f"[FATAL] {exc}")
        return 2
    report_dir.mkdir(parents=True, exist_ok=True)
    blueprint_route = resolve_blueprint_route(root, None, args.blueprint_strict)
    route_level = "PASS" if blueprint_route["strict"] else "WARN"
    emit(f"[{route_level}] 蓝图路由: {blueprint_route['mode']} — {blueprint_route['reason']}")

    py = sys.executable
    results: list[dict] = []
    step_no = 1
    def step(name: str, command: list[str], timeout: int = 3600,
             blocking_on_warn: bool = True, force_block: bool = False) -> None:
        nonlocal step_no
        result = run_step(step_no, name, command, timeout)
        result["blocking_on_warn"] = blocking_on_warn
        result["force_block"] = force_block
        results.append(result)
        step_no += 1

    def collab_step(gate: str, *, activate: bool = False) -> bool:
        """Run a user-decision gate only when the chosen mode requires it."""
        if args.mode == "AUTO":
            return True
        command = [py, str(SCRIPTS / "collab_gate.py"), str(root), "--gate", gate,
                   "--mode", args.mode,
                   "--out", str(report_dir / f"collab_{gate}.json")]
        if args.collab_policy:
            command.extend(["--policy", args.collab_policy])
        if args.approval_log:
            command.extend(["--approval-log", args.approval_log])
        if activate:
            command.append("--activate")
        step(f"{gate} COLLAB decision gate", command, force_block=True)
        return results[-1]["status"] == "PASS"

    def stop_for_collab(gate: str) -> int:
        """Persist a recoverable PAUSE report instead of continuing past user review."""
        report = {
            "schema_version": "2.0", "project_root": str(root), "paper_dir": str(paper_dir),
            "competition": args.competition, "scope": args.scope, "mode": args.mode,
            "status": "PAUSE", "paused_at_gate": gate,
            "message": f"{gate} 决策包未获当前版本批准；流程已停止，等待用户确认。",
            "results": results,
        }
        out = report_dir / "delivery_all_report.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        emit(f"[PAUSE] {gate} 未获批准，未进入后续阶段。报告: {out}")
        return 2

    # 25--30 页是个人国赛 profile 的内容规划，不应无意继承到美赛/华数杯。
    # 其他竞赛只有在显式提供 --content-budget-plan 时才启用同一门禁。
    content_budget_is_enabled = content_budget_enabled(args.competition, args.content_budget_plan)
    if content_budget_is_enabled:
        # 先检查内容预算和小问证据状态，避免论文写完后才发现容量不足。
        # 严格正式交付缺计划或未完成证据直接阻断。
        content_solution_cmd = [py, str(SCRIPTS / "check_content_budget.py"), str(root),
                                "--stage", "solution",
                                "--out", str(report_dir / "content_budget_solution_report.json")]
        if args.content_budget_plan:
            content_solution_cmd.extend(["--plan", args.content_budget_plan])
        if args.evidence_index:
            content_solution_cmd.extend(["--evidence-index", args.evidence_index])
        if args.strict:
            content_solution_cmd.append("--strict")
        step("F0.2 content budget and evidence sufficiency", content_solution_cmd,
             force_block=args.strict)
    else:
        emit("[INFO] 非国赛且未提供内容预算计划，跳过 25--30 页 profile 门禁")

    # These checks cannot replace stage-time pauses in interactive work, but
    # they make a strict replay reject an unapproved or changed decision packet.
    # G4/G5/G6 are called later, after their evidence actually exists.
    if not collab_step("G0"):
        return stop_for_collab("G0")
    if not collab_step("G1"):
        return stop_for_collab("G1")
    if not collab_step("G2"):
        return stop_for_collab("G2")

    evidence_index_target = None
    if args.evidence_index:
        raw_index = Path(args.evidence_index)
        evidence_index_target = raw_index.resolve() if raw_index.is_absolute() else (root / raw_index).resolve()
    evidence_index_cmd = [py, str(SCRIPTS / "build_evidence_index.py"), str(root),
                          "--stage", "solution", "--out",
                          str(evidence_index_target or (root / ".contest" / "evidence_index.json"))]
    if args.strict:
        evidence_index_cmd.append("--strict")
    step("F0.25 derived evidence index", evidence_index_cmd, force_block=args.strict)

    # Validate the installed skill itself before touching a project paper.
    step("F0 skill consistency", [py, str(SCRIPTS / "check_skill_consistency.py"),
                                  str(SCRIPTS.parent), "--strict"])
    profile_cmd = [py, str(SCRIPTS / "route_problem_profile.py"), str(root),
                   "--out", str(report_dir / "problem_profile_route_report.json")]
    if args.problem_profile:
        profile_cmd.extend(["--profile", args.problem_profile])
    if args.strict:
        profile_cmd.append("--strict")
    # A slot-prior mismatch is advisory: the capability declaration remains
    # authoritative and must not be blocked merely because a B/C/A prior differs.
    step("F0.1 two-axis problem profile routing", profile_cmd, blocking_on_warn=False)
    if args.competition == "guosai":
        margin_cmd = [py, str(SCRIPTS / "check_page_margins.py"), str(paper_dir),
                      "--competition", "guosai",
                      "--out", str(report_dir / "page_margin_report.json")]
        if args.strict:
            margin_cmd.append("--strict")
        step("F0.15 guosai page-margin contract", margin_cmd, force_block=args.strict)
    # Compile is first project step so a stale PDF cannot silently pass later gates.
    step("compile_paper", [py, str(SCRIPTS / "compile_paper.py"), str(paper_dir), "--tex", tex.name])
    preferred = paper_dir / "paper.pdf"
    if not preferred.exists():
        preferred = tex.with_suffix(".pdf")
    pdfs = sorted(paper_dir.glob("*.pdf"), key=lambda path: path.stat().st_mtime, reverse=True)
    pdf = preferred if preferred.exists() else (pdfs[0] if pdfs else paper_dir / "paper.pdf")

    if content_budget_is_enabled:
        content_pdf_cmd = [py, str(SCRIPTS / "check_content_budget.py"), str(root),
                           "--stage", "pdf", "--pdf", str(pdf),
                           "--out", str(report_dir / "content_budget_pdf_report.json")]
        if args.content_budget_plan:
            content_pdf_cmd.extend(["--plan", args.content_budget_plan])
        if args.allow_short_paper:
            content_pdf_cmd.append("--allow-short-exception")
        if args.strict:
            content_pdf_cmd.append("--strict")
        step("F0.3 compiled PDF content budget", content_pdf_cmd,
             force_block=args.strict)
    else:
        emit("[INFO] 非国赛且未提供内容预算计划，跳过编译后篇幅门禁")

    refresh = refresh_compiled_paper_evidence(root, tex, pdf) if pdf.is_file() else {"updated": [], "errors": []}
    if refresh["updated"]:
        emit("[INFO] 已刷新本次编译的论文证据哈希: " + ", ".join(refresh["updated"]))
    if refresh["errors"]:
        emit("[WARN] 论文证据哈希刷新失败: " + "; ".join(refresh["errors"]))
    if pdfs and pdf not in {paper_dir / "paper.pdf", tex.with_suffix(".pdf")}:
        emit(f"\n[WARN] 未找到标准论文 PDF，回退使用: {pdf}")
        results.append({"number": step_no, "name": "PDF selection", "status": "WARN",
                        "returncode": 127, "started_at": datetime.now(timezone.utc).isoformat(),
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                        "duration_seconds": 0, "tail": f"回退 PDF: {pdf}"})
        step_no += 1
    bib = next(iter(sorted(paper_dir.glob("*.bib"))), paper_dir / "ref.bib")

    manifest_cmd = [py, str(SCRIPTS / "delivery_manifest.py"), str(root),
                    "--paper-dir", str(paper_dir)]
    if args.strict:
        manifest_cmd.append("--strict")
    step("delivery_manifest(preflight)", manifest_cmd)
    coverage_cmd = [py, str(SCRIPTS / "check_problem_coverage.py"), str(root),
                    "--out", str(report_dir / "problem_coverage_report.json")]
    if args.strict:
        coverage_cmd.append("--strict")
        if args.scope == "FULL_CONTEST":
            coverage_cmd.append("--require-ledger")
    step("F0.5 problem condition coverage", coverage_cmd)
    evidence_manifest_cmd = [py, str(SCRIPTS / "check_run_manifest.py"), str(root)]
    stale_evidence_cmd = [py, str(SCRIPTS / "check_stale_evidence.py"), str(root)]
    numeric_audit_cmd = [py, str(SCRIPTS / "audit_numeric_sources.py"), str(root),
                         "--paper", str(tex)]
    # FULL_CONTEST records executable evidence before model and paper gates.
    # In strict mode missing manifests/maps block; normal replay keeps visible WARNs.
    if args.strict:
        evidence_manifest_cmd.append("--strict")
        stale_evidence_cmd.append("--strict")
        numeric_audit_cmd.extend(["--strict", "--require-map"])
    step("F0.6 run manifest and evidence IDs", evidence_manifest_cmd, force_block=args.strict)
    step("F0.7 stale evidence propagation", stale_evidence_cmd, force_block=args.strict)
    step("F0.8 numeric result source audit", numeric_audit_cmd, force_block=args.strict)
    if args.research_evidence_strict:
        research_cmd = [py, str(SCRIPTS / "check_research_evidence.py"), str(root),
                        "--strict", "--out", str(report_dir / "research_evidence_report.json")]
        step("F0.9 research evidence chain", research_cmd, force_block=True)
    else:
        emit("[INFO] 未启用研究证据链严格门禁；现有来源、数字和运行清单门禁继续执行")
    step("F1 check_core_execution", [py, str(SCRIPTS / "check_core_execution.py"), str(root)])
    step("F2 consistency_check", [py, str(SCRIPTS / "consistency_check.py"), str(paper_dir)])
    result_code_cmd = [py, str(SCRIPTS / "check_result_code_consistency.py"), str(root),
                       "--out", str(report_dir / "result_code_consistency_report.json")]
    if args.strict:
        result_code_cmd.append("--strict")
    step("F2.1 result-code consistency", result_code_cmd)
    step("F2.5 paper_check", [py, str(SCRIPTS / "paper_check.py"), str(paper_dir), "--competition", args.competition])
    step("F2.6 TeX layout pattern check", [py, str(SCRIPTS / "check_tex_layout_patterns.py"), str(paper_dir), "--strict"])
    step("F2.7 TeX reference integrity", [py, str(SCRIPTS / "check_tex_references.py"), str(paper_dir)])
    evidence_cmd = [py, str(SCRIPTS / "check_model_evidence.py"), str(root)]
    derivation_cmd = [py, str(SCRIPTS / "check_derivation_chain.py"), str(root)]
    if args.strict:
        evidence_cmd.append("--strict")
        derivation_cmd.append("--strict")
    step("F2.8 model evidence graph", evidence_cmd)
    solution_contract_cmd = [py, str(SCRIPTS / "check_modeling_solution_contract.py"), str(root),
                             "--out", str(report_dir / "modeling_solution_contract_report.json")]
    solution_contract_strict = args.strict or args.contract_strict
    if solution_contract_strict:
        solution_contract_cmd.append("--strict")
    step("F2.8.1 modeling-solution input and derivation contract", solution_contract_cmd,
         force_block=solution_contract_strict)
    step("F2.9 derivation chain", derivation_cmd)
    blueprint_cmd = [py, str(SCRIPTS / "compile_model_blueprint.py"), str(root)]
    if blueprint_route["strict"]:
        blueprint_cmd.append("--strict")
    step("F2.10 model blueprint compiler (auto-routed)", blueprint_cmd,
         blocking_on_warn=blueprint_route["strict"], force_block=blueprint_route["strict"])
    symbol_cmd = [py, str(SCRIPTS / "check_symbol_consistency.py"), str(root)]
    interface_cmd = [py, str(SCRIPTS / "check_interface_contract.py"), str(root)]
    if blueprint_route["strict"]:
        symbol_cmd.append("--strict")
        interface_cmd.append("--strict")
    step("F2.11 symbol consistency (auto-routed)", symbol_cmd,
         blocking_on_warn=blueprint_route["strict"], force_block=blueprint_route["strict"])
    step("F2.12 interface contract (auto-routed)", interface_cmd,
         blocking_on_warn=blueprint_route["strict"], force_block=blueprint_route["strict"])
    algorithm_cmd = [py, str(SCRIPTS / "check_algorithm_manifest.py"), str(root),
                     "--out", str(report_dir / "algorithm_manifest_report.json")]
    if args.strict:
        algorithm_cmd.append("--strict")
    step("F2.13 algorithm configuration lock", algorithm_cmd)
    dimension_cmd = [py, str(SCRIPTS / "check_dimension_consistency.py"), str(root),
                     "--out", str(report_dir / "dimension_consistency_report.json")]
    if args.strict:
        dimension_cmd.append("--strict")
    step("F2.14 declarative dimension consistency", dimension_cmd)

    pandoc_tex = next((candidate for candidate in (paper_dir / "paper_pandoc.tex", tex) if candidate.exists()), None)
    if args.skip_docx or pandoc_tex is None:
        reason = ("已由 --skip-docx 明确跳过辅助 DOCX；正式提交件为 PDF"
                  if args.skip_docx else "无 DOCX 输入源；正式提交件为 PDF")
        emit(f"\n[PASS] {reason}")
        results.append({"number": step_no, "name": "F3 docx_pipeline", "status": "PASS",
                        "returncode": 0, "started_at": datetime.now(timezone.utc).isoformat(),
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                        "duration_seconds": 0, "tail": reason})
        step_no += 1
    else:
        out_docx = paper_dir / "paper.docx"
        docx_cmd = [py, str(SCRIPTS / "docx_pipeline.py"), str(pandoc_tex), str(pdf), "-o", str(out_docx)]
        if args.visual_check:
            docx_cmd.append("--visual-check")
        step("F3 docx_pipeline", docx_cmd)
        if args.visual_check:
            step("F3 check_visual_contract(docx)", [py, str(SCRIPTS / "check_visual_contract.py"), str(out_docx)])
        else:
            results.append(skipped_step(
                step_no, "F3 check_visual_contract(docx)",
                "SKIPPED_USER_OPT_IN: automatic visual QA is disabled by default; user visual review is the substitute"))
            step_no += 1

    hard_cmd = [py, str(SCRIPTS / "check_paper_hard_requirements.py"), str(pdf)]
    if args.hard_requirements:
        hard_cmd.extend(["--profile", str(Path(args.hard_requirements).resolve())])
    step("F4 check_paper_hard_requirements", hard_cmd)
    abstract_cmd = [py, str(SCRIPTS / "check_abstract_contract.py"), str(pdf),
                    "--project-root", str(root),
                    "--out", str(report_dir / "abstract_contract_report.json")]
    if args.strict:
        abstract_cmd.append("--strict")
    step("F4.1 abstract evidence and numeric provenance", abstract_cmd)
    # F4.2 论文叙事质量检查：防止"建模手写论文"（非建模章节公式堆砌、结果数值无解释、建模求解章节缺小节、算法细节在正文、连续公式无文字衔接）
    narrative_cmd = [py, str(SCRIPTS / "check_paper_narrative.py"), str(paper_dir),
                     "--out", str(report_dir / "paper_narrative_report.json")]
    if args.strict:
        narrative_cmd.append("--strict")
    step("F4.2 paper narrative quality (anti modeling-log)", narrative_cmd, blocking_on_warn=False)
    # F4.3 代码注释质量检查：防止AI生成代码缺少必要注释、注释包含元话语/负向回响
    code_dir = root / "code" if (root / "code").is_dir() else root
    code_comments_cmd = [py, str(SCRIPTS / "check_code_comments.py"), str(code_dir),
                         "--out", str(report_dir / "code_comments_report.json")]
    if args.strict:
        code_comments_cmd.append("--strict")
    step("F4.3 code comment quality (anti AI-no-comments)", code_comments_cmd, blocking_on_warn=False)
    # F4.4 数值合理性检查：防止"代码运行了但结果是错的"（inf/nan、目标值量级异常、结果不完整、决策变量超出物理范围）
    numerical_sanity_cmd = [py, str(SCRIPTS / "check_numerical_sanity.py"), str(root),
                             "--out", str(report_dir / "numerical_sanity_report.json")]
    if args.strict:
        numerical_sanity_cmd.append("--strict")
    step("F4.4 numerical sanity check (anti code-ran-but-wrong)", numerical_sanity_cmd, blocking_on_warn=False)
    # F4.5 写作风格客观检查：用六项客观指标检测AI生成感（句长均匀度、段落长度均匀度、列表堆砌、机械过渡词、跨章节短语重复、套话密度）
    style_check_script = SKILL_ROOT.parent / "academic-writing" / "scripts" / "style_check.py"
    if style_check_script.exists():
        style_cmd = [py, str(style_check_script), str(paper_dir),
                     "--out", str(report_dir / "style_report.json")]
        if args.strict:
            style_cmd.append("--strict")
        step("F4.5 writing style objective check (anti AI-generated feel)", style_cmd, blocking_on_warn=False)
    else:
        emit(f"\n[WARN] 未找到 academic-writing style_check.py: {style_check_script}")
        results.append({"number": step_no, "name": "F4.5 writing style objective check", "status": "WARN",
                        "returncode": 127, "started_at": datetime.now(timezone.utc).isoformat(),
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                        "duration_seconds": 0, "tail": f"未找到 academic-writing/scripts/style_check.py"})
        step_no += 1
    if bib.exists():
        doi_cmd = [py, str(SCRIPTS / "verify_doi.py"), str(bib)]
        if args.doi_online:
            doi_cmd.append("--doi-online")
        step("DOI citation verification", doi_cmd)
    else:
        emit(f"\n[WARN] 未找到参考文献库: {bib}")
        results.append({"number": step_no, "name": "DOI citation verification", "status": "WARN",
                        "returncode": 127, "started_at": datetime.now(timezone.utc).isoformat(),
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                        "duration_seconds": 0, "tail": f"未找到参考文献库: {bib}"})
        step_no += 1
    citation_cmd = [py, str(SCRIPTS / "check_literature_citation.py"), str(pdf)]
    if args.strict:
        citation_cmd.append("--strict")
    step("F4.x literature citation usage", citation_cmd)
    contract_cmd = [py, str(SCRIPTS / "check_modeling_contract.py"), str(paper_dir),
                    "--profile", args.profile, "--competition", args.competition,
                    "--pdf", str(pdf),
                    "--config", str(Path(args.gate_config).resolve()) if args.gate_config else
                    str(SCRIPTS.parent / "core" / "competition_gates.yaml")]
    if args.contract_strict:
        contract_cmd.append("--contract-strict")
    elif args.strict:
        # FULL_CONTEST strict delivery must enforce the per-subproblem
        # modeling evidence contract; a soft structural warning is not enough
        # to authorize a final paper.
        contract_cmd.append("--contract-strict")
    # The contract script returns PASS with an advisory WARN when the model
    # chapter exceeds the preferred 45--55% share.  In strict mode, missing
    # evidence or structural issues still return FAIL and block delivery;
    # an over-target share is a review signal, not a false hard failure.
    step("F4.y modeling chapter contract", contract_cmd, blocking_on_warn=False)
    trace_cmd = [py, str(SCRIPTS / "check_model_traceability.py"), str(root),
                 "--competition", args.competition]
    if args.strict:
        trace_cmd.append("--strict")
    step("F4.y model traceability", trace_cmd)
    step("F4.y submission metadata scan", [py, str(SCRIPTS / "check_submission_meta_text.py"), str(paper_dir)])
    if args.competition == "guosai":
        ai_cmd = [py, str(SCRIPTS / "check_ai_compliance.py"), str(root),
                  "--paper-dir", str(paper_dir),
                  "--out", str(report_dir / "ai_compliance_report.json")]
        step("F4.y guosai 2026 AI compliance", ai_cmd)
    latex_appendix_cmd = [py, str(SCRIPTS / "check_latex_appendix_contract.py"), str(paper_dir),
                          "--project-root", str(root),
                          "--out", str(report_dir / "latex_appendix_contract_report.json")]
    if args.appendix_contract:
        latex_appendix_cmd.extend(["--contract", args.appendix_contract])
    if args.appendix_plan:
        latex_appendix_cmd.extend(["--plan", args.appendix_plan])
    if args.strict or args.contract_strict:
        latex_appendix_cmd.append("--strict")
    step("F4.y LaTeX appendix evidence contract", latex_appendix_cmd)
    if args.legacy_diagnostics:
        appendix_cmd = [py, str(SCRIPTS / "check_appendix_contract.py"), str(paper_dir)]
        step("F4.y legacy appendix diagnostic", appendix_cmd)
        code_cmd = [py, str(SCRIPTS / "check_code_appendix.py"), str(paper_dir)]
        step("F4.y legacy code appendix diagnostic", code_cmd)
    anonymity_cmd = [py, str(SCRIPTS / "check_anonymity.py"), str(paper_dir), "--pdf", str(pdf)]
    step("F4.y anonymity scan", anonymity_cmd)
    registry = root / "figure_registry.json"
    if not registry.exists():
        registry = paper_dir / "figure_registry.json"
    if not registry.exists():
        registry = root / "05_输出与交付" / "figure_registry.json"
    step("figure_registry provenance", [py, str(SCRIPTS / "figure_registry.py"), str(registry), "--workspace", str(root)])
    visual_cmd = [py, str(SCRIPTS / "check_visual_evidence.py"), str(root),
                  "--stage", "paper", "--tex", str(tex),
                  "--out", str(report_dir / "visual_evidence_report.json")]
    if args.content_budget_plan:
        visual_cmd.extend(["--plan", args.content_budget_plan])
    step("F4.y visual evidence coverage", visual_cmd, blocking_on_warn=False)
    if not collab_step("G4"):
        return stop_for_collab("G4")
    step("F4.y appendix coverage plan", [py, str(SCRIPTS / "appendix_planner.py"), str(root),
                                         "--out", str(report_dir / "appendix_plan_report.json")])
    if not collab_step("G5"):
        return stop_for_collab("G5")
    step("LaTeX warning classification", [py, str(SCRIPTS / "latex_warning_check.py"), str(paper_dir)])
    gate_cmd = [py, str(SCRIPTS / "delivery_gate.py"), str(paper_dir),
                "--competition", args.competition, "--pdf", str(pdf),
                "--project-root", str(root)]
    if args.gate_config:
        gate_cmd.extend(["--config", str(Path(args.gate_config).resolve())])
    if args.visual_check:
        gate_cmd.append("--visual-check")
    step("F5 delivery_gate", gate_cmd)
    if args.visual_check:
        step("F5 visual_critic(pdf)", [py, str(SCRIPTS / "visual_critic.py"), str(pdf)])
    else:
        results.append(skipped_step(
            step_no, "F5 visual_critic(pdf)",
            "SKIPPED_USER_OPT_IN: automatic visual QA is disabled by default; user visual review is the substitute"))
        step_no += 1
    step("delivery_manifest(final)", manifest_cmd)
    if not collab_step("G6"):
        return stop_for_collab("G6")
    if args.sync_formal_delivery:
        started = datetime.now(timezone.utc)
        pre_sync_blocking = [item for item in results if is_blocking(item, args.strict)]
        if pre_sync_blocking:
            payload = {"skipped": True, "reason": "前置门禁尚未全部通过"}
            status = "FAIL"
        else:
            try:
                payload = sync_formal_delivery(root, tex, pdf, report_dir)
                status = "PASS"
            except (OSError, ValueError) as exc:
                payload = {"error": str(exc)}
                status = "FAIL"
        finished = datetime.now(timezone.utc)
        item = {"number": step_no, "name": "F5 formal delivery sync", "status": status,
                "returncode": 0 if status == "PASS" else 1,
                "started_at": started.isoformat(), "finished_at": finished.isoformat(),
                "duration_seconds": round((finished - started).total_seconds(), 3),
                "tail": json.dumps(payload, ensure_ascii=False)}
        item["blocking_on_warn"] = True
        item["force_block"] = True
        results.append(item)
        step_no += 1
        emit(f"[{status}] F5 formal delivery sync: {item['tail']}")
    formal_cmd = [py, str(SCRIPTS / "check_formal_delivery_drift.py"), str(root), "--pdf", str(pdf)]
    if args.strict:
        formal_cmd.append("--strict")
    step("F5 formal delivery drift", formal_cmd)
    readiness_cmd = [py, str(SCRIPTS / "compute_readiness.py"), str(root)]
    step("F6 evidence readiness", readiness_cmd, force_block=args.strict)

    blocking = [item for item in results if is_blocking(item, args.strict)]
    report = {"schema_version": "2.0", "project_root": str(root), "paper_dir": str(paper_dir),
              "pdf": str(pdf), "competition": args.competition,
              "started_at": results[0]["started_at"] if results else datetime.now(timezone.utc).isoformat(),
              "finished_at": datetime.now(timezone.utc).isoformat(), "strict": args.strict,
              "scope": args.scope, "scope_plan": str(Path(args.scope_plan).resolve()) if args.scope_plan else None,
              "scope_plan_digest": plan_digest, "blueprint_route": blueprint_route,
              "mode": args.mode,
              "visual_check_requested": args.visual_check,
              "visual_check_status": "EXECUTED" if args.visual_check else "SKIPPED_USER_OPT_IN",
              "content_budget_enabled": content_budget_is_enabled,
              "research_evidence_strict": args.research_evidence_strict,
              "passed": not blocking,
              "blocking_steps": [item["name"] for item in blocking],
              "results": results}
    out = report_dir / "delivery_all_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.sync_formal_delivery:
        formal_report = root / "05_输出与交付" / "正式交付" / "reports"
        if formal_report.is_dir():
            shutil.copy2(out, formal_report / out.name)
    emit(f"\n===== 总结: {'PASS 可交付' if not blocking else 'FAIL 禁止交付'} =====")
    emit(f"通过/警告/失败: {sum(r['status']=='PASS' for r in results)}/{sum(r['status']=='WARN' for r in results)}/{sum(r['status']=='FAIL' for r in results)}")
    emit(f"报告: {out}")
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
