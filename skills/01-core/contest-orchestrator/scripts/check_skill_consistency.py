#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit versions, declared paths, runtime path portability and script routing."""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path
from typing import Any


def _load_yaml(path: Path) -> dict[str, Any]:
    import yaml
    value = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"YAML 根节点必须是对象: {path}")
    return value


def _patterns(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _matches(relative: str, pattern: str) -> bool:
    normalized = relative.replace("\\", "/")
    pattern = pattern.replace("\\", "/")
    if pattern.endswith("/"):
        return normalized.startswith(pattern)
    return fnmatch.fnmatch(normalized, pattern)


def _declared_paths(text: str) -> list[str]:
    values: list[str] = []
    for match in re.finditer(r"(?<![\w/])((?:scripts|core|planner|memory|references|schemas|templates|executor)/[A-Za-z0-9_.*/-]+)", text):
        value = match.group(1).rstrip("`.,;:)")
        if "*" not in value and not value.endswith("/"):
            values.append(value)
    return sorted(set(values))


def check(root: Path) -> dict[str, Any]:
    root = root.resolve()
    failures: list[str] = []
    warnings: list[str] = []
    info: list[str] = []
    version_file = (root / "VERSION").read_text(encoding="utf-8", errors="replace").strip() if (root / "VERSION").exists() else ""
    skill_text = (root / "SKILL.md").read_text(encoding="utf-8", errors="replace") if (root / "SKILL.md").exists() else ""
    manifest_text = (root / "manifest.yaml").read_text(encoding="utf-8", errors="replace") if (root / "manifest.yaml").exists() else ""
    versions = {"VERSION": version_file}
    for label, text in (("SKILL.md", skill_text), ("manifest.yaml", manifest_text)):
        match = re.search(r"(?:^|\n)\s*version:\s*[\"']?([^\"'\s]+)", text)
        versions[label] = match.group(1) if match else ""
    if len(set(versions.values())) != 1 or not version_file:
        failures.append(f"版本不一致: {versions}")
    else:
        info.append(f"version={version_file}")

    registry_path = root / "scripts" / "script_registry.yaml"
    if not registry_path.exists():
        failures.append("缺少 scripts/script_registry.yaml")
        registry: dict[str, Any] = {}
    else:
        try:
            registry = _load_yaml(registry_path)
        except Exception as exc:
            failures.append(f"脚本分类表无法解析: {exc}")
            registry = {}
    categories = registry.get("categories", {}) if isinstance(registry, dict) else {}
    allow_overlaps = set(_patterns(registry.get("allow_overlaps", []))) if isinstance(registry, dict) else set()
    runtime_policy = registry.get("runtime_policy", {}) if isinstance(registry, dict) else {}
    allow_path_literals = set(_patterns(runtime_policy.get("allow_path_literals", []))) if isinstance(runtime_policy, dict) else set()
    active_files = [p for p in (root / "scripts").rglob("*.py")
                    if "archive" not in p.parts and "public_overrides" not in p.parts and "__pycache__" not in p.parts]
    category_hits: dict[str, list[str]] = {}
    for path in active_files:
        relative = path.relative_to(root).as_posix()
        hits = [str(name) for name, values in categories.items()
                if any(_matches(relative, pattern) for pattern in _patterns(values))]
        if not hits:
            failures.append(f"活动脚本未分类: {relative}")
        category_hits[relative] = hits
        if len(hits) > 1 and relative not in allow_overlaps:
            warnings.append(f"脚本跨分类重叠: {relative} -> {','.join(hits)}")
    for name, values in categories.items():
        for pattern in _patterns(values):
            if "*" not in pattern and not (root / pattern).exists() and not pattern.endswith("/"):
                failures.append(f"分类表路径不存在: {pattern} ({name})")

    scan_files = [root / "SKILL.md", root / "manifest.yaml", root / "scripts" / "README.md",
                  root / "core" / "appendix_contract.md"]
    for file in scan_files:
        if not file.exists():
            continue
        for relative in _declared_paths(file.read_text(encoding="utf-8", errors="replace")):
            if not (root / relative).exists():
                warnings.append(f"文档声明路径不存在: {relative} ({file.relative_to(root)})")

    # Detect user-specific paths without embedding this workstation's account name.
    forbidden_path = re.compile(
        r"(?:[A-Za-z]:\\Users\\[^\\\s]+\\(?:\.claude|\.codex)"
        r"|~/?\.claude/skills/contest-orchestrator|/Users/[^/\s]+)",
        re.I,
    )
    for path in active_files:
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        if forbidden_path.search(text) and relative not in allow_path_literals:
            failures.append(f"活动脚本含个人/旧运行时路径: {path.relative_to(root)}")
    classified_count = sum(bool(v) for v in category_hits.values())
    info.append(f"active_scripts={len(active_files)}")
    info.append(f"classified_scripts={classified_count}")
    return {"schema_version": "1.0", "passed": not failures, "failures": failures,
            "warnings": warnings, "info": info, "versions": versions,
            "active_script_count": len(active_files),
            "classified_script_count": classified_count,
            "category_hits": category_hits}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = check(args.root)
    if args.strict and report["warnings"]:
        report["failures"].extend(report["warnings"])
        report["warnings"] = []
        report["passed"] = False
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.out.resolve().write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
