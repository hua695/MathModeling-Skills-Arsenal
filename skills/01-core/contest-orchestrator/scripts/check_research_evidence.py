#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the optional research-evidence contract for a contest project.

The checker reuses the project's existing references.yaml, citation_map.json,
model_contract.yaml and .contest/runs/*/run_manifest.json.  It does not create
another source or result database.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except Exception:  # pragma: no cover - reported as a contract failure
    yaml = None


SOURCE_FIELDS = (
    "citation_key", "title", "authors", "venue", "year", "status", "doi",
    "url", "relevance", "key_points", "limitations", "used_in", "verified_at",
)
SOURCE_STATUSES = {"peer_reviewed", "preprint", "standard", "dataset", "software", "web"}
LIMITATION_FIELDS = (
    "assumptions", "applicable_conditions", "failure_conditions",
    "impact_direction", "mitigation",
)
REPRO_FIELDS = (
    "entrypoint", "inputs", "parameters", "seed", "command", "outputs",
    "figure_scripts", "result_paper_map",
)


def _nonempty(value: object) -> bool:
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return value is not None and bool(str(value).strip())


def _safe_path(root: Path, raw: object) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw)
    if candidate.is_absolute():
        return None
    try:
        resolved = (root / candidate).resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return resolved


def _find(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        path = root / name
        if path.is_file():
            return path
    return None


def _load_yaml(path: Path) -> object:
    if yaml is None:
        raise RuntimeError("缺少 PyYAML，无法读取研究证据契约")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_references(path: Path) -> list[dict]:
    payload = _load_yaml(path)
    if not isinstance(payload, list):
        raise ValueError("references.yaml 根节点必须是数组")
    return [item for item in payload if isinstance(item, dict)]


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} 根节点必须是对象")
    return payload


def _source_record_issues(refs: list[dict]) -> list[str]:
    issues: list[str] = []
    if not refs:
        return ["source records 不能为空"]
    keys: set[str] = set()
    for index, ref in enumerate(refs):
        label = f"source record[{index}]"
        missing = [field for field in SOURCE_FIELDS if field not in ref]
        if missing:
            issues.append(f"{label} 缺少字段: {', '.join(missing)}")
        key = str(ref.get("citation_key", "")).strip()
        if not key:
            issues.append(f"{label}.citation_key 不能为空")
        elif key in keys:
            issues.append(f"citation_key 重复: {key}")
        keys.add(key)
        status = str(ref.get("status", "")).strip()
        if status not in SOURCE_STATUSES:
            issues.append(f"{label}.status 必须属于 {sorted(SOURCE_STATUSES)}")
        for field in ("title", "authors", "venue", "year", "relevance", "key_points", "limitations", "used_in"):
            if not _nonempty(ref.get(field)):
                issues.append(f"{label}.{field} 不能为空")
        if not _nonempty(ref.get("doi")) and not _nonempty(ref.get("url")):
            issues.append(f"{label} 至少需要 doi 或 url")
        verification = str(ref.get("verification_status", "")).lower()
        if verification in {"verified", "user_metadata", "complete", "manual_verified"} and not _nonempty(ref.get("verified_at")):
            issues.append(f"{label}.verified_at 在已核验记录中不能为空")
    return issues


def _claim_issues(root: Path, payload: dict, known_ids: set[str]) -> list[str]:
    issues: list[str] = []
    metadata = payload.get("_metadata")
    if not isinstance(metadata, dict) or not str(metadata.get("research_evidence_version", "")).strip():
        issues.append("citation_map._metadata.research_evidence_version 缺失")
    claims = payload.get("claim_evidence")
    if not isinstance(claims, list) or not claims:
        return issues + ["claim_evidence 必须是非空数组"]
    for index, item in enumerate(claims):
        label = f"claim_evidence[{index}]"
        if not isinstance(item, dict):
            issues.append(f"{label} 必须是对象")
            continue
        for field in ("claim_id", "claim", "evidence", "location", "use"):
            if not _nonempty(item.get(field)):
                issues.append(f"{label}.{field} 缺失或为空")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            continue
        for eidx, evidence_item in enumerate(evidence):
            e_label = f"{label}.evidence[{eidx}]"
            if not isinstance(evidence_item, dict):
                issues.append(f"{e_label} 必须是对象")
                continue
            for field in ("source_id", "locator", "use"):
                if not _nonempty(evidence_item.get(field)):
                    issues.append(f"{e_label}.{field} 缺失或为空")
            source_id = evidence_item.get("source_id")
            if source_id not in known_ids:
                issues.append(f"{e_label}.source_id 未在运行证据中登记: {source_id}")
        location = item.get("location")
        if isinstance(location, dict):
            location_file = _safe_path(root, location.get("file"))
            if location_file is None or not location_file.is_file():
                issues.append(f"{label}.location.file 不存在或超出项目根目录")
            if not _nonempty(location.get("anchor")):
                issues.append(f"{label}.location.anchor 缺失或为空")
        if str(item.get("claim_type", "direct")).lower() == "derived":
            relation = item.get("recomputable_from")
            if not isinstance(relation, list) or not relation:
                issues.append(f"{label}.recomputable_from 必须记录可复算关系")
    return issues


def _limitation_issues(path: Path) -> list[str]:
    try:
        payload = _load_yaml(path)
    except Exception as exc:
        return [f"model_contract.yaml 无法解析: {exc}"]
    if not isinstance(payload, dict):
        return ["model_contract.yaml 根节点必须是对象"]
    if not str(payload.get("research_evidence_version", "")).strip():
        return ["model_contract.research_evidence_version 缺失"]
    items = payload.get("subproblems")
    if not isinstance(items, list) or not items:
        return ["model_contract.subproblems 必须是非空数组"]
    issues: list[str] = []
    for index, item in enumerate(items):
        label = f"subproblems[{index}]"
        limitations = item.get("limitations") if isinstance(item, dict) else None
        if not isinstance(limitations, dict):
            issues.append(f"{label}.limitations 缺失")
            continue
        missing = [field for field in LIMITATION_FIELDS if field not in limitations]
        if missing:
            issues.append(f"{label}.limitations 缺少字段: {', '.join(missing)}")
        for field in LIMITATION_FIELDS:
            if field in limitations and not _nonempty(limitations[field]):
                issues.append(f"{label}.limitations.{field} 不能为空")
    return issues


def _manifest_issues(root: Path, path: Path) -> tuple[list[str], set[str]]:
    try:
        payload = _load_json(path)
    except Exception as exc:
        return [f"{path.name} 无法解析: {exc}"], set()
    issues: list[str] = []
    known_ids: set[str] = set()
    for group in ("inputs", "code", "configs", "outputs", "evidence"):
        for item in payload.get(group, []) if isinstance(payload.get(group), list) else []:
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str):
                known_ids.add(item["evidence_id"])
    reproducibility = payload.get("reproducibility")
    if not isinstance(reproducibility, dict):
        return [f"{path.relative_to(root).as_posix()}: reproducibility 缺失"], known_ids
    missing = [field for field in REPRO_FIELDS if field not in reproducibility]
    issues.extend(f"{path.relative_to(root).as_posix()}.reproducibility 缺少字段: {field}" for field in missing)
    if not _nonempty(reproducibility.get("entrypoint")):
        issues.append(f"{path.name}.reproducibility.entrypoint 不能为空")
    entrypoint = _safe_path(root, reproducibility.get("entrypoint"))
    if entrypoint is None or not entrypoint.is_file():
        issues.append(f"{path.name}.reproducibility.entrypoint 不存在或超出项目根目录")
    command = reproducibility.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(value, str) for value in command):
        issues.append(f"{path.name}.reproducibility.command 必须是非空字符串数组")
    for field in ("inputs", "outputs", "figure_scripts"):
        values = reproducibility.get(field)
        if not isinstance(values, list):
            continue
        for value in values:
            candidate = _safe_path(root, value)
            if candidate is None or not candidate.is_file():
                issues.append(f"{path.name}.reproducibility.{field} 文件不存在或超出项目根目录: {value}")
    mappings = reproducibility.get("result_paper_map")
    if not isinstance(mappings, list) or not mappings:
        issues.append(f"{path.name}.reproducibility.result_paper_map 必须是非空数组")
    else:
        for index, mapping in enumerate(mappings):
            if not isinstance(mapping, dict):
                issues.append(f"{path.name}.result_paper_map[{index}] 必须是对象")
                continue
            for field in ("claim_id", "output_evidence_id", "paper_location"):
                if not _nonempty(mapping.get(field)):
                    issues.append(f"{path.name}.result_paper_map[{index}].{field} 缺失或为空")
            if mapping.get("output_evidence_id") not in known_ids:
                issues.append(f"{path.name}.result_paper_map[{index}] 输出证据 ID 未登记")
    return issues, known_ids


def validate(root: Path, strict: bool = False) -> dict:
    issues: list[str] = []
    warnings: list[str] = []
    refs_path = _find(root, ("references.yaml", "01_需求与规划/references.yaml", "03_文档/references.yaml"))
    cmap_path = _find(root, ("citation_map.json", "01_需求与规划/citation_map.json", "03_文档/citation_map.json"))
    model_path = _find(root, ("model_contract.yaml", "01_需求与规划/model_contract.yaml", "03_文档/model_contract.yaml"))
    cmap = None
    if not refs_path:
        issues.append("未找到 references.yaml")
    else:
        try:
            issues.extend(_source_record_issues(_load_references(refs_path)))
        except Exception as exc:
            issues.append(f"references.yaml 无法解析: {exc}")
    if not cmap_path:
        issues.append("未找到 citation_map.json")
    else:
        try:
            cmap = _load_json(cmap_path)
        except Exception as exc:
            issues.append(f"citation_map.json 无法解析: {exc}")
            cmap = None
    if not model_path:
        issues.append("未找到 model_contract.yaml")
    else:
        issues.extend(_limitation_issues(model_path))
    manifest_paths = sorted((root / ".contest" / "runs").glob("*/run_manifest.json")) if (root / ".contest" / "runs").is_dir() else []
    if not manifest_paths:
        issues.append("未找到 .contest/runs/*/run_manifest.json")
    known_ids: set[str] = set()
    for manifest_path in manifest_paths:
        manifest_issues, manifest_ids = _manifest_issues(root, manifest_path)
        issues.extend(manifest_issues)
        known_ids.update(manifest_ids)
    if cmap is not None:
        issues.extend(_claim_issues(root, cmap, known_ids))
    if not strict and issues:
        warnings = list(issues)
        issues = []
    return {
        "schema_version": "1.0", "strict": strict,
        "status": "PASS" if not issues else "FAIL",
        "passed": not issues, "issues": issues, "warnings": warnings,
        "files": {"references": str(refs_path) if refs_path else None,
                   "citation_map": str(cmap_path) if cmap_path else None,
                   "model_contract": str(model_path) if model_path else None,
                   "run_manifests": [str(path) for path in manifest_paths]},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = validate(args.project_root.resolve(), args.strict)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.out.resolve().write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
