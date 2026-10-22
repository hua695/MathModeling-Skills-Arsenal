#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create a deterministic, project-relative run manifest from a JSON spec.

This helper records an already executed run; it deliberately does not execute
user commands.  The manifest is a provenance sidecar, not a second result
database.  All paths stored in it are relative to the supplied project root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,63}$")
EVIDENCE_ID = re.compile(r"^ev:[A-Za-z0-9_.-]+$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel_path(root: Path, raw: str) -> str:
    path = Path(raw)
    if path.is_absolute():
        resolved = path.resolve()
        try:
            path = resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"路径不在项目根目录内: {raw}") from exc
    normalized = path.as_posix()
    if normalized == "":
        normalized = "."
    if normalized.startswith("../") or "/../" in f"/{normalized}":
        raise ValueError(f"禁止项目外路径: {raw}")
    return normalized


def artifact(root: Path, value: object, default_role: str) -> dict:
    if isinstance(value, str):
        payload = {"path": value}
    elif isinstance(value, dict):
        payload = dict(value)
    else:
        raise ValueError(f"artifact 必须是路径字符串或对象: {value!r}")
    path = rel_path(root, str(payload.get("path", "")))
    source = root / Path(path)
    if not source.is_file():
        raise ValueError(f"artifact 文件不存在: {path}")
    evidence_id = str(payload.get("evidence_id", f"ev:artifact.{path.replace('/', '.')}"))
    if not EVIDENCE_ID.fullmatch(evidence_id):
        raise ValueError(f"无效 evidence_id: {evidence_id}")
    result = {"path": path, "sha256": sha256(source), "evidence_id": evidence_id,
              "role": str(payload.get("role", default_role))}
    source_ids = payload.get("source_ids")
    if source_ids is not None:
        if not isinstance(source_ids, list) or not all(isinstance(item, str) for item in source_ids):
            raise ValueError(f"source_ids 必须是字符串数组: {path}")
        result["source_ids"] = source_ids
    return result


def reproducibility(root: Path, value: object) -> dict:
    """Validate and normalize the optional research reproduction record."""
    if not isinstance(value, dict):
        raise ValueError("reproducibility 必须是对象")
    required = ("entrypoint", "inputs", "parameters", "seed", "command",
                "outputs", "figure_scripts", "result_paper_map")
    missing = [name for name in required if name not in value]
    if missing:
        raise ValueError(f"reproducibility 缺少字段: {', '.join(missing)}")
    command = value.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command):
        raise ValueError("reproducibility.command 必须是非空字符串数组")
    normalized = dict(value)
    normalized["entrypoint"] = rel_path(root, str(value["entrypoint"]))
    for field in ("inputs", "outputs", "figure_scripts"):
        paths = value.get(field)
        if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
            raise ValueError(f"reproducibility.{field} 必须是字符串数组")
        normalized[field] = [rel_path(root, item) for item in paths]
    mappings = value.get("result_paper_map")
    if not isinstance(mappings, list) or not mappings:
        raise ValueError("reproducibility.result_paper_map 必须是非空数组")
    normalized["result_paper_map"] = []
    for item in mappings:
        if not isinstance(item, dict):
            raise ValueError("result_paper_map 中的项必须是对象")
        if not all(str(item.get(key, "")).strip() for key in ("claim_id", "output_evidence_id", "paper_location")):
            raise ValueError("result_paper_map 每项必须含 claim_id/output_evidence_id/paper_location")
        normalized["result_paper_map"].append(dict(item))
    return normalized


def make_manifest(root: Path, spec: dict) -> dict:
    run_id = str(spec.get("run_id", ""))
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("run_id 必须是 3-64 位字母、数字、点、下划线或短横线")
    command = spec.get("command") or {}
    argv = command.get("argv") if isinstance(command, dict) else None
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
        raise ValueError("command.argv 必须是非空字符串数组")
    cwd = rel_path(root, str(command.get("cwd", ".")))
    status = str(spec.get("status", "completed"))
    if status not in {"completed", "failed", "cancelled"}:
        raise ValueError(f"无效 run status: {status}")
    inputs = [artifact(root, item, "input") for item in spec.get("inputs", [])]
    code = [artifact(root, item, "code") for item in spec.get("code", [])]
    configs = [artifact(root, item, "config") for item in spec.get("configs", [])]
    outputs = [artifact(root, item, "result") for item in spec.get("outputs", [])]
    evidence = []
    for item in spec.get("evidence", []):
        if not isinstance(item, dict):
            raise ValueError("evidence 必须是对象数组")
        evidence_id = str(item.get("evidence_id", ""))
        source_ids = item.get("source_ids", [])
        if not EVIDENCE_ID.fullmatch(evidence_id) or not isinstance(source_ids, list):
            raise ValueError(f"evidence 缺少合法 evidence_id/source_ids: {item!r}")
        evidence.append({"evidence_id": evidence_id, "kind": str(item.get("kind", "claim")),
                         "source_ids": [str(value) for value in source_ids],
                         **({"claim": str(item["claim"])} if "claim" in item else {})})
    manifest = {
        "schema_version": "1.0", "run_id": run_id, "status": status,
        "command": {"argv": argv, "cwd": cwd}, "inputs": inputs, "code": code,
        "configs": configs, "outputs": outputs, "evidence": evidence,
        "seed": spec.get("seed"), "environment": spec.get("environment", {}),
        "started_at": spec.get("started_at", datetime.now(timezone.utc).isoformat()),
        "finished_at": spec.get("finished_at", datetime.now(timezone.utc).isoformat()),
        "exit_code": int(spec.get("exit_code", 0 if status == "completed" else 1)),
        "stdout_log": rel_path(root, spec["stdout_log"]) if spec.get("stdout_log") else None,
        "stderr_log": rel_path(root, spec["stderr_log"]) if spec.get("stderr_log") else None,
    }
    if "reproducibility" in spec:
        manifest["reproducibility"] = reproducibility(root, spec["reproducibility"])
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--spec", required=True, type=Path, help="运行记录 JSON 规格")
    parser.add_argument("--out", required=True, type=Path, help="项目内 run_manifest.json 输出路径")
    args = parser.parse_args()
    root = args.project_root.resolve()
    spec_path = args.spec.resolve()
    out = args.out.resolve()
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        if not isinstance(spec, dict):
            raise ValueError("spec 根节点必须是对象")
        manifest = make_manifest(root, spec)
        out.relative_to(root)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(json.dumps({"status": "PASS", "run_id": manifest["run_id"], "path": out.relative_to(root).as_posix()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
