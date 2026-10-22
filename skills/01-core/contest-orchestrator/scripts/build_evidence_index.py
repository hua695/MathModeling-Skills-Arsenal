#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a read-only, project-side index over existing contest evidence.

The index is a derived view, not a second source of truth.  It records the
presence, hashes, and small structural summaries of contracts and run
artifacts already produced by the workflow.  It never edits those inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover - JSON-only installations remain usable
    yaml = None


CORE_NAMES = {
    "content_budget_plan": ("content_budget_plan.yaml", "content_budget_plan.yml", "content_budget_plan.json"),
    "model_contract": ("model_contract.yaml", "model_contract.yml", "model_contract.json"),
    "derivation_registry": ("derivation_registry.yaml", "derivation_registry.yml", "derivation_registry.json"),
    "modeling_solution_contract": (
        "modeling_solution_contract.yaml", "modeling_solution_contract.yml", "modeling_solution_contract.json"
    ),
    "model_blueprint": ("model_blueprint.yaml", "model_blueprint.yml", "model_blueprint.json"),
    "numeric_source_map": ("numeric_source_map.json",),
    "figure_registry": ("figure_registry.json",),
    "citation_map": ("citation_map.json",),
}

REQUIRED_BY_STAGE = {
    "blueprint": ("content_budget_plan",),
    "solution": ("model_contract", "derivation_registry", "modeling_solution_contract", "run_manifest"),
    "delivery": (
        "model_contract", "derivation_registry", "modeling_solution_contract", "run_manifest",
        "numeric_source_map", "figure_registry", "citation_map",
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def load_structured(path: Path) -> object:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        return json.loads(raw)
    if yaml is None:
        raise RuntimeError("读取 YAML 证据需要 PyYAML")
    return yaml.safe_load(raw)


def _candidate_paths(root: Path, names: tuple[str, ...]) -> list[Path]:
    candidates: list[Path] = []
    search_roots = (root, root / "01_需求与规划", root / "03_文档", root / "paper", root / "05_输出与交付")
    for folder in search_roots:
        if not folder.is_dir():
            continue
        for name in names:
            candidate = folder / name
            if candidate.is_file() and candidate.resolve() not in candidates:
                candidates.append(candidate.resolve())
    return candidates


def discover(root: Path) -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {}
    for kind, names in CORE_NAMES.items():
        candidates = _candidate_paths(root, names)
        if candidates:
            found[kind] = candidates[:1]
    run_manifests = sorted((root / ".contest" / "runs").glob("*/run_manifest.json"))
    if run_manifests:
        found["run_manifest"] = [path.resolve() for path in run_manifests]
    return found


def summarize(kind: str, payload: object) -> dict:
    if not isinstance(payload, dict):
        return {"shape": type(payload).__name__}
    summary: dict[str, object] = {"keys": sorted(str(key) for key in payload)[:40]}
    if kind == "model_contract":
        items = payload.get("subproblems", [])
        if isinstance(items, list):
            summary["subproblem_ids"] = [item.get("id") for item in items if isinstance(item, dict) and item.get("id")]
    elif kind == "derivation_registry":
        items = payload.get("formulas", payload.get("steps", []))
        if isinstance(items, list):
            summary["entry_count"] = len(items)
    elif kind == "modeling_solution_contract":
        items = payload.get("subproblems", [])
        if isinstance(items, list):
            summary["subproblem_ids"] = [item.get("id") for item in items if isinstance(item, dict) and item.get("id")]
    elif kind == "run_manifest":
        summary.update({"run_id": payload.get("run_id"), "status": payload.get("status"),
                        "exit_code": payload.get("exit_code")})
    elif kind == "content_budget_plan":
        summary["profile"] = payload.get("profile")
        summary["planning_contract"] = payload.get("planning_contract")
    return summary


def build(root: Path, stage: str, strict: bool, out: Path | None) -> tuple[dict, int]:
    root = root.resolve()
    found = discover(root)
    errors: list[str] = []
    warnings: list[str] = []
    sources: list[dict] = []
    kind_status: dict[str, str] = {}
    for kind, paths in found.items():
        for path in paths:
            item = {"kind": kind, "path": rel(root, path), "sha256": sha256(path), "status": "present"}
            try:
                payload = load_structured(path)
                item["summary"] = summarize(kind, payload)
            except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
                item["status"] = "invalid"
                item["error"] = str(exc)
                errors.append(f"{item['path']} 无法解析: {exc}")
            sources.append(item)
        kind_status[kind] = "present" if all(item["status"] == "present" for item in sources if item["kind"] == kind) else "invalid"
    for kind in REQUIRED_BY_STAGE[stage]:
        if kind not in found:
            (errors if strict else warnings).append(f"缺少证据来源: {kind}")
            kind_status[kind] = "missing"
    if stage in {"solution", "delivery"} and "run_manifest" in found:
        for item in sources:
            if item["kind"] == "run_manifest" and item.get("summary", {}).get("status") != "completed":
                (errors if strict else warnings).append(f"运行清单未成功完成: {item['path']}")
    index = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "stage": stage,
        "derived": True,
        "source_of_truth": "existing project contracts and run manifests",
        "kinds": kind_status,
        "sources": sources,
        "errors": errors,
        "warnings": warnings,
        # A warning means the derived view is incomplete even though the
        # non-strict command remains usable; callers must not treat it as a
        # successful evidence snapshot.
        "passed": not errors and not warnings,
    }
    destination = out.resolve() if out else root / ".contest" / "evidence_index.json"
    try:
        destination.relative_to(root)
    except ValueError:
        return {"passed": False, "errors": ["evidence index 输出必须位于项目根目录内"]}, 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index, 0 if not errors else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--stage", choices=tuple(REQUIRED_BY_STAGE), default="solution")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    payload, code = build(args.project_root, args.stage, args.strict, args.out)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
