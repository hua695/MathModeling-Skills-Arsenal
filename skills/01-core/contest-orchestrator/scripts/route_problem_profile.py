#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate and compile the two-axis contest problem profile.

The contest slot (A/B/C) is only a weak prior.  Each subproblem declares its
actual capabilities, which determine modeling and appendix requirements.  This
planner is intentionally read-only: it produces a routing report and never
edits a paper or invents missing capabilities.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

try:
    import yaml
except ImportError:  # pragma: no cover - the rest of the skill already requires PyYAML
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "planner" / "paper_profiles.yaml"
CAPABILITY_CONFIG = ROOT / "planner" / "capability_registry.yaml"
SCHEMA_VERSION = "1.0"


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("需要 PyYAML 才能解析 problem_profile.yaml")
    payload = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"YAML 根节点必须是对象: {path}")
    return payload


def discover_profile(project_root: Path, explicit: str | None = None) -> Path | None:
    if explicit:
        candidate = Path(explicit)
        return (project_root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    candidates = (project_root / "problem_profile.yaml",
                  project_root / "03_文档" / "problem_profile.yaml",
                  project_root / "paper" / "problem_profile.yaml")
    return next((path.resolve() for path in candidates if path.exists()), None)


def route(project_root: Path, profile_path: Path | None = None, strict: bool = False) -> dict[str, Any]:
    project_root = project_root.resolve()
    config = _load_yaml(CONFIG)
    capability_registry = _load_yaml(CAPABILITY_CONFIG)
    warnings: list[str] = []
    failures: list[str] = []
    infos: list[str] = []
    if profile_path is None:
        profile_path = discover_profile(project_root)
    if profile_path is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "INFO",
            "strict": strict,
            "project_root": str(project_root),
            "profile_path": None,
            "message": "未声明 problem_profile.yaml；保留现有 --profile 路由，不强制升级旧项目",
            "warnings": [], "failures": [], "routes": [],
        }
    if not profile_path.exists():
        failures.append(f"题型画像不存在: {profile_path}")
        return _report(project_root, profile_path, strict, warnings, failures, infos, [])
    try:
        payload = _load_yaml(profile_path)
    except Exception as exc:
        failures.append(str(exc))
        return _report(project_root, profile_path, strict, warnings, failures, infos, [])

    slot = str(payload.get("problem_slot", "unknown")).upper()
    if slot not in {"A", "B", "C", "D", "E", "UNKNOWN"}:
        failures.append(f"problem_slot 非法: {slot}")
    subproblems = payload.get("subproblems")
    if not isinstance(subproblems, dict) or not subproblems:
        failures.append("subproblems 必须是至少包含一个小问的对象")
        subproblems = {}

    capability_map = config.get("capabilities", {})
    registered_capabilities = capability_registry.get("capabilities", {})
    priors = config.get("slot_priors", {})
    slot_hints = set(priors.get(slot, {}).get("hints", [])) if isinstance(priors, dict) else set()
    routes: list[dict[str, Any]] = []
    all_caps: set[str] = set()
    for qid, item in subproblems.items():
        if not isinstance(item, dict):
            failures.append(f"{qid}: 小问配置必须是对象")
            continue
        caps = item.get("capabilities")
        if not isinstance(caps, list) or not caps:
            failures.append(f"{qid}: capabilities 必须是非空列表")
            continue
        qcaps = [str(cap).lower() for cap in caps]
        all_caps.update(qcaps)
        unknown = [cap for cap in qcaps if cap not in capability_map]
        if unknown:
            failures.append(f"{qid}: 未注册能力 {unknown}")
        registry_missing = [cap for cap in qcaps if cap not in registered_capabilities]
        if registry_missing:
            failures.append(f"{qid}: 能力注册表缺少 {registry_missing}")
        selected_profiles = sorted({capability_map[cap]["profile"] for cap in qcaps if cap in capability_map})
        appendix = sorted({module for cap in qcaps if cap in capability_map
                           for module in capability_map[cap].get("appendix", [])})
        routes.append({"subproblem_id": str(qid), "capabilities": qcaps,
                       "profiles": selected_profiles, "appendix_modules": appendix,
                       "inputs": item.get("inputs", []), "outputs": item.get("outputs", [])})
    if slot in priors and all_caps and not (slot_hints & all_caps):
        warnings.append(f"题号 {slot} 的常见先验与实际能力无交集；以逐小问能力为准")
    interfaces = payload.get("shared_interfaces", [])
    if interfaces is not None and not isinstance(interfaces, list):
        failures.append("shared_interfaces 必须是列表")
    if interfaces:
        infos.append(f"检测到 {len(interfaces)} 个跨小问接口，保持作用域隔离")
    infos.append("能力路由优先于 A/B/C 题号先验")
    return _report(project_root, profile_path, strict, warnings, failures, infos, routes)


def _report(project_root: Path, profile_path: Path | None, strict: bool,
            warnings: list[str], failures: list[str], infos: list[str], routes: list[dict[str, Any]]) -> dict[str, Any]:
    blocked = bool(failures) or (strict and any("未注册能力" in item for item in failures))
    return {"schema_version": SCHEMA_VERSION, "status": "FAIL" if blocked else ("WARN" if warnings else "PASS"),
            "strict": strict, "project_root": str(project_root),
            "profile_path": str(profile_path) if profile_path else None,
            "warnings": warnings, "failures": failures, "info": infos, "routes": routes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--profile", default=None, help="problem_profile.yaml 路径")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    try:
        report = route(args.project_root, discover_profile(args.project_root.resolve(), args.profile), args.strict)
    except Exception as exc:
        report = {"schema_version": SCHEMA_VERSION, "status": "FAIL", "strict": args.strict,
                  "failures": [str(exc)], "warnings": [], "routes": []}
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out = args.out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 1 if report.get("status") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
