#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create and validate a stable, hash-based delivery manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "2.0"
REQUIRED_PAPER = ("paper.tex", "paper.pdf", "ref.bib")
FIGURE_REGISTRY = "figure_registry.json"
TEMP_MARKERS = ("\\AppData\\Local\\Temp\\", "/AppData/Local/Temp/", "\\Temp\\", "/tmp/")
GENERATED_REPORTS = {"compile_report.json", "delivery_gate_report.json", "delivery_manifest.json",
                    "delivery_all_report.json", "latex_warning_report.json", "pdf_qa_report.json"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def is_under(path: Path, roots: list[Path]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def resolve_from_root(ws: Path, value: Path | None) -> Path | None:
    if value is None:
        return None
    return value.resolve() if value.is_absolute() else (ws / value).resolve()


def discover(ws: Path, paper_arg: Path | None = None,
             registry_arg: Path | None = None) -> tuple[Path, Path]:
    """Resolve standard and legacy project layouts without guessing silently."""
    explicit_paper = resolve_from_root(ws, paper_arg)
    if explicit_paper is not None:
        paper_dir = explicit_paper
    else:
        candidates = (ws / "03_文档" / "paper", ws / "paper", ws)
        paper_dir = next((path for path in candidates
                          if (path / "paper.tex").exists() or (path / "paper.pdf").exists()), ws)

    explicit_registry = resolve_from_root(ws, registry_arg)
    if explicit_registry is not None:
        registry = explicit_registry
    else:
        candidates = (ws / FIGURE_REGISTRY,
                      ws / "05_输出与交付" / FIGURE_REGISTRY,
                      paper_dir / FIGURE_REGISTRY)
        registry = next((path for path in candidates if path.exists()), candidates[0])
    return paper_dir, registry


def registry_summary(path: Path) -> tuple[int, list[str]]:
    if not path.exists():
        return 0, [f"缺少 {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return 0, [f"figure_registry.json 无法解析: {exc}"]
    entries = data.get("figures", data) if isinstance(data, dict) else None
    if not isinstance(entries, (dict, list)):
        return 0, ["figure_registry.json 必须是对象，figures 可为对象或数组"]
    return len(entries), []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--paper-dir", type=Path, default=None,
                        help="论文目录；相对路径按 workspace 解析")
    parser.add_argument("--figure-registry", type=Path, default=None,
                        help="图表注册表；相对路径按 workspace 解析")
    parser.add_argument("--strict", action="store_true", help="空图表注册表也视为失败")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    ws = args.workspace.resolve()
    paper_dir, registry = discover(ws, args.paper_dir, args.figure_registry)
    issues: list[str] = []
    warnings: list[str] = []
    files: dict[str, dict] = {}
    pdf = paper_dir / "paper.pdf"

    if not ws.is_dir() or not paper_dir.is_dir():
        print(f"交付根目录不完整: {ws}")
        return 2
    if any(marker.lower() in str(ws).lower() for marker in TEMP_MARKERS):
        issues.append(f"正式交付根目录不能位于临时目录: {ws}")

    for name in REQUIRED_PAPER:
        path = paper_dir / name
        if not path.exists():
            issues.append(f"缺少 {path}")
            continue
        files[name] = {"path": str(path), "relative_path": str(path.relative_to(ws)),
                       "size": path.stat().st_size, "mtime": iso_mtime(path), "sha256": sha256(path)}
    count, registry_issues = registry_summary(registry)
    issues.extend(registry_issues)
    if count == 0:
        (issues if args.strict else warnings).append("figure_registry.json 没有登记图表")
    elif registry.exists():
        files[FIGURE_REGISTRY] = {"path": str(registry), "relative_path": str(registry.relative_to(ws)),
                                  "size": registry.stat().st_size, "mtime": iso_mtime(registry),
                                  "sha256": sha256(registry)}

    # Include all sources that can change the final PDF, not just paper.tex.
    source_roots = [paper_dir]
    source_roots.extend(path for path in ws.glob("results*") if path.is_dir())
    for relative in ("04_代码", "05_输出与交付"):
        candidate = ws / relative
        if candidate.is_dir():
            source_roots.append(candidate)
    if (ws / "figures").is_dir():
        source_roots.append(ws / "figures")
    sources = []
    for source_root in source_roots:
        sources.extend(source_root.rglob("*.tex"))
        sources.extend(source_root.rglob("*.bib"))
        sources.extend(source_root.rglob("*.json"))
        sources.extend(source_root.rglob("*.csv"))
        sources.extend(source_root.rglob("*.png"))
        sources.extend(source_root.rglob("*.jpg"))
        sources.extend(source_root.rglob("*.jpeg"))
        sources.extend(source_root.rglob("*.pdf"))
    excluded_roots = [ws / "05_输出与交付" / "正式交付",
                      ws / "05_输出与交付" / "delivery_report",
                      ws / "05_输出与交付" / "reports",
                      ws / "05_输出与交付" / "critic_report",
                      ws / "tmp"]
    sources = sorted({path for path in sources
                      if path.name not in GENERATED_REPORTS and not is_under(path, excluded_roots)})
    if registry.exists():
        sources.append(registry)
    # v4.7: keep a complete hash inventory for every source that can affect the
    # PDF, not only the three headline paper files.
    artifacts = []
    for path in sorted(set(sources)):
        try:
            relative = str(path.relative_to(ws))
        except ValueError:
            relative = str(path)
        artifacts.append({"path": relative, "absolute_path": str(path),
                          "size": path.stat().st_size, "mtime": iso_mtime(path),
                          "sha256": sha256(path), "generator": "source"})
    if pdf.exists():
        pdf_mtime = pdf.stat().st_mtime
        stale = [str(path.relative_to(ws)) for path in sources if path != pdf and path.stat().st_mtime > pdf_mtime]
        if stale:
            issues.append(f"PDF 新鲜度检查失败（存在晚于 PDF 的源文件）: {stale}")

    version = None
    skill = Path(__file__).resolve().parents[1] / "SKILL.md"
    if skill.exists():
        match = re.search(r"^(?:version|\s+version):\s*[\"']?([^\"'\s]+)", skill.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
        version = match.group(1) if match else None
    report = {
        "schema_version": SCHEMA_VERSION,
        "skill_version": version,
        "workspace": str(ws),
        "canonical_root": str(ws),
        "canonical": not any(marker.lower() in str(ws).lower() for marker in TEMP_MARKERS),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "figure_count": count,
        "files": files,
        "artifacts": artifacts,
        "issues": issues,
        "warnings": warnings,
        "passed": not issues,
    }
    out = args.out.resolve() if args.out else paper_dir / "delivery_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
