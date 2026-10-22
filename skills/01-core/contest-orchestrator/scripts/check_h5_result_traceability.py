#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the evidence package produced by a Harness H5 solver run."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator

try:
    import yaml
except Exception:  # pragma: no cover - reported in the command result
    yaml = None


SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def _resolve_project_path(root: Path, raw: Any) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_mapping(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("缺少 PyYAML，无法读取 H5 结果证据")
    payload = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"配置根节点必须为对象: {path}")
    return payload


def _first_nonempty(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None and value != "":
            return value
    return None


def _iter_result_file_refs(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        ref = value.get("result_file")
        if isinstance(ref, dict):
            yield ref
        for child in value.values():
            yield from _iter_result_file_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_result_file_refs(child)


def _check_file_ref(root: Path, ref: Any, label: str,
                    missing: list[str], failures: list[str]) -> Path | None:
    if not isinstance(ref, dict):
        failures.append(f"{label} 必须为含 path/sha256 的对象")
        return None
    raw_path = ref.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        missing.append(f"{label} 缺少 path")
        return None
    path = _resolve_project_path(root, raw_path)
    if path is None:
        failures.append(f"{label}.path 必须为项目内相对路径: {raw_path}")
        return None
    if not path.is_file():
        failures.append(f"{label}.path 文件不存在: {raw_path}")
        return None
    expected = ref.get("sha256")
    if not isinstance(expected, str) or not expected.strip():
        missing.append(f"{label} 缺少 sha256")
    elif not SHA256_PATTERN.fullmatch(expected.strip()):
        failures.append(f"{label}.sha256 必须为 64 位十六进制字符串")
    elif _digest(path).lower() != expected.strip().lower():
        failures.append(f"{label}.sha256 与文件不匹配: {raw_path}")
    return path


def _command_present(manifest: dict[str, Any]) -> bool:
    offline = manifest.get("offline_run")
    reproducibility = manifest.get("reproducibility")
    values = [
        manifest.get("command"),
        offline.get("command") if isinstance(offline, dict) else None,
        reproducibility.get("command") if isinstance(reproducibility, dict) else None,
    ]
    for value in values:
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, list) and value and all(isinstance(item, str) and item.strip() for item in value):
            return True
    return False


def _result_ref(manifest: dict[str, Any]) -> Any:
    offline = manifest.get("offline_run")
    if isinstance(offline, dict) and isinstance(offline.get("result"), dict):
        return offline["result"]
    if isinstance(manifest.get("result"), dict):
        return manifest["result"]
    reproducibility = manifest.get("reproducibility")
    if isinstance(reproducibility, dict):
        outputs = reproducibility.get("outputs")
        if isinstance(outputs, list) and outputs:
            return outputs[0]
    return None


def _model_contract_path(root: Path, manifest: dict[str, Any]) -> Path | None:
    raw = _first_nonempty(manifest, ("model_contract_path", "model_contract"))
    if raw is None:
        reproducibility = manifest.get("reproducibility")
        if isinstance(reproducibility, dict):
            raw = _first_nonempty(reproducibility, ("model_contract_path", "model_contract"))
    if raw is None:
        raw = "model_contract.yaml"
    if isinstance(raw, dict):
        raw = raw.get("path")
    return _resolve_project_path(root, raw)


def _sensitivity_candidates(root: Path, explicit: str | None) -> list[Path]:
    raw_candidates = [explicit] if explicit else []
    raw_candidates.extend([
        "sensitivity_report.yaml", "results/sensitivity_report.yaml",
        "robustness_report.yaml", "results/robustness_report.yaml",
    ])
    paths: list[Path] = []
    seen: set[Path] = set()
    for raw in raw_candidates:
        path = _resolve_project_path(root, raw)
        if path is not None and path not in seen:
            seen.add(path)
            paths.append(path)
    return paths


def validate_h5_result_traceability(root: Path, *, run_manifest: str | None = None,
                                    sensitivity_report: str | None = None) -> dict[str, Any]:
    """Return a deterministic PASS/PAUSE/BLOCK report for H5 evidence."""
    root = root.resolve()
    missing: list[str] = []
    failures: list[str] = []
    checks: list[dict[str, Any]] = []
    manifest_path = _resolve_project_path(root, run_manifest or "run_manifest.yaml")
    if manifest_path is None or not manifest_path.is_file():
        missing.append(f"H5: run manifest 文件不存在: {run_manifest or 'run_manifest.yaml'}")
        return {
            "schema_version": "1.0", "status": "PAUSE", "checks": checks,
            "missing": missing, "failures": failures, "root": str(root),
        }
    try:
        manifest = _load_mapping(manifest_path)
    except Exception as exc:
        failures.append(f"H5: run manifest 不可读: {exc}")
        return {
            "schema_version": "1.0", "status": "BLOCK", "checks": checks,
            "missing": missing, "failures": failures, "root": str(root),
        }

    checks.append({"name": "run_manifest", "path": str(manifest_path.relative_to(root).as_posix()), "status": "read"})
    if manifest.get("schema_version") != "1.0":
        failures.append("H5: run manifest schema_version 必须为 1.0")
    if manifest.get("status") != "verified":
        failures.append(f"H5: run manifest status 必须为 verified（当前: {manifest.get('status')}）")
    if manifest.get("node_id") not in (None, "H5"):
        failures.append(f"H5: run manifest node_id 必须为 H5（当前: {manifest.get('node_id')}）")
    if "seed" not in manifest:
        missing.append("H5: run manifest 必须显式登记 seed；确定性运行填 null")
    if not _command_present(manifest):
        missing.append("H5: run manifest 必须登记可执行 command")

    result_ref = _result_ref(manifest)
    _check_file_ref(root, result_ref, "H5: 主结果", missing, failures)

    contract_path = _model_contract_path(root, manifest)
    if contract_path is None or not contract_path.is_file():
        failures.append("H5: model_contract.yaml 文件不存在")
        contract_digest = None
    else:
        contract_digest = _digest(contract_path)
    registered_contract_digest = manifest.get("model_contract_sha256")

    formal = manifest.get("formal_tests")
    if not isinstance(formal, dict):
        missing.append("H5: formal_tests 必须为对象，登记正式记录字段和结果文件")
    else:
        record_fields = formal.get("record_fields")
        if not isinstance(record_fields, list) or not record_fields or any(
            not isinstance(item, str) or not item.strip() for item in record_fields
        ):
            missing.append("H5: formal_tests.record_fields 必须为非空字符串列表")
        refs = list(_iter_result_file_refs(formal))
        for index, ref in enumerate(refs):
            _check_file_ref(root, ref, f"H5: formal_tests.result_file[{index}]", missing, failures)
        if not refs:
            missing.append("H5: formal_tests 必须包含至少一个带哈希的 result_file 正式记录")
    boundary = _first_nonempty(manifest, ("formal_interpretation_boundary", "formal_boundary"))
    if not isinstance(boundary, str) or not boundary.strip():
        missing.append("H5: 必须登记 formal_interpretation_boundary")

    sensitivity_path = next((path for path in _sensitivity_candidates(root, sensitivity_report) if path.is_file()), None)
    if sensitivity_path is None:
        missing.append("H5: 缺少 sensitivity_report.yaml 或 robustness_report.yaml")
        sensitivity = None
    else:
        try:
            sensitivity = _load_mapping(sensitivity_path)
        except Exception as exc:
            failures.append(f"H5: 敏感性/鲁棒性报告不可读: {exc}")
            sensitivity = None
    sensitivity_digest = None
    if isinstance(sensitivity, dict):
        canonical_report = sensitivity.get("canonical_report")
        if canonical_report is None:
            missing.append("H5: 敏感性/鲁棒性报告必须登记 canonical_report 路径和哈希")
        else:
            _check_file_ref(
                root, canonical_report, "H5: sensitivity.canonical_report", missing, failures,
            )
        sensitivity_digest = sensitivity.get("model_contract_sha256")
        if sensitivity.get("schema_version") != "1.0":
            failures.append("H5: 敏感性/鲁棒性报告 schema_version 必须为 1.0")
        if sensitivity.get("status") != "verified":
            failures.append(f"H5: 敏感性/鲁棒性报告 status 必须为 verified（当前: {sensitivity.get('status')}）")
        if not isinstance(sensitivity.get("method"), str) or not sensitivity["method"].strip():
            missing.append("H5: 敏感性/鲁棒性报告必须登记 method")
        results = sensitivity.get("results")
        if not isinstance(results, list) or not results:
            missing.append("H5: 敏感性/鲁棒性报告 results 必须为非空列表")
        else:
            for index, item in enumerate(results):
                if not isinstance(item, dict):
                    failures.append(f"H5: sensitivity.results[{index}] 必须为对象")
                    continue
                points = item.get("perturbation_points")
                if not isinstance(points, list) or not points:
                    missing.append(f"H5: sensitivity.results[{index}] 缺少非空 perturbation_points")

    if not isinstance(registered_contract_digest, str) or not registered_contract_digest.strip():
        registered_contract_digest = sensitivity_digest
    if not isinstance(registered_contract_digest, str) or not registered_contract_digest.strip():
        missing.append("H5: 结果包必须登记 model_contract_sha256")
    elif not SHA256_PATTERN.fullmatch(registered_contract_digest.strip()):
        failures.append("H5: model_contract_sha256 必须为 64 位十六进制字符串")
    elif contract_digest is not None and registered_contract_digest.lower() != contract_digest.lower():
        failures.append("H5: model_contract_sha256 与 model_contract.yaml 不匹配")
    if isinstance(manifest.get("model_contract_sha256"), str) and isinstance(sensitivity_digest, str):
        if manifest["model_contract_sha256"].lower() != sensitivity_digest.lower():
            failures.append("H5: run manifest 与敏感性/鲁棒性报告的 model_contract_sha256 不一致")

    status = "BLOCK" if failures else "PAUSE" if missing else "PASS"
    return {
        "schema_version": "1.0", "status": status,
        "run_manifest": manifest_path.relative_to(root).as_posix(),
        "sensitivity_report": sensitivity_path.relative_to(root).as_posix() if sensitivity_path else None,
        "checks": checks, "missing": missing, "failures": failures, "root": str(root),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--run-manifest", default=None)
    parser.add_argument("--sensitivity-report", default=None)
    parser.add_argument("--strict", action="store_true", help="保留统一的严格门禁命名")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    try:
        report = validate_h5_result_traceability(
            args.project_root,
            run_manifest=args.run_manifest,
            sensitivity_report=args.sensitivity_report,
        )
    except Exception as exc:
        report = {
            "schema_version": "1.0", "status": "BLOCK",
            "checks": [], "missing": [], "failures": [f"检查器内部异常: {type(exc).__name__}: {exc}"],
            "root": str(args.project_root.resolve()),
        }
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.out.resolve().write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "PASS" else 2 if report["status"] == "PAUSE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
