#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit declared paper numbers against result files (no invented values)."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

NUMBER = re.compile(r"(?<![A-Za-z])[-+]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?%?")


def pointer(value: object, raw: str) -> object:
    if not raw or raw == "/":
        return value
    current = value
    for part in raw.lstrip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise KeyError(raw)
    return current


def numeric(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    if isinstance(value, str):
        match = NUMBER.fullmatch(value.strip())
        if match:
            return float(match.group(0).rstrip("%"))
    return None


def find_map(root: Path, explicit: str | None) -> Path | None:
    candidates = [Path(explicit)] if explicit else [Path("numeric_source_map.json"), Path("05_输出与交付/numeric_source_map.json")]
    for candidate in candidates:
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
        if resolved.is_file():
            return resolved
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--paper", default=None, help="论文 TeX 文件或目录")
    parser.add_argument("--map", dest="source_map", default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-map", action="store_true", help="无数字来源表时失败")
    args = parser.parse_args()
    root = args.project_root.resolve()
    paper = (root / args.paper).resolve() if args.paper and not Path(args.paper).is_absolute() else Path(args.paper).resolve() if args.paper else root / "paper"
    tex_files = [paper] if paper.is_file() else sorted(paper.glob("*.tex"))
    tex_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in tex_files if path.exists())
    source_map = find_map(root, args.source_map)
    errors: list[str] = []
    warnings: list[str] = []
    claims_report: list[dict] = []
    if source_map is None:
        message = "未发现 numeric_source_map.json，论文数值尚未建立结果来源映射"
        (errors if args.require_map or args.strict else warnings).append(message)
    else:
        try:
            payload = json.loads(source_map.read_text(encoding="utf-8"))
            if payload.get("schema_version") != "1.0" or not isinstance(payload.get("claims"), list):
                raise ValueError("schema_version 必须为 1.0 且 claims 必须为数组")
            ids: set[str] = set()
            for index, claim in enumerate(payload["claims"]):
                label = f"claims[{index}]"
                if not isinstance(claim, dict):
                    errors.append(f"{label} 必须是对象")
                    continue
                claim_id = claim.get("id")
                if not isinstance(claim_id, str) or not claim_id.startswith("claim:") or claim_id in ids:
                    errors.append(f"{label}.id 无效或重复")
                ids.add(str(claim_id))
                source_raw = claim.get("source_file")
                try:
                    source = (root / Path(str(source_raw))).resolve()
                    source.relative_to(root)
                except (ValueError, OSError):
                    errors.append(f"{label}.source_file 必须是项目内相对路径")
                    continue
                if not source.is_file():
                    errors.append(f"{label} 来源文件不存在: {source_raw}")
                    continue
                try:
                    value = json.loads(source.read_text(encoding="utf-8"))
                    value = pointer(value, str(claim.get("json_pointer", "/")))
                except (OSError, json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
                    errors.append(f"{label} 无法读取 json_pointer: {exc}")
                    continue
                expected = numeric(claim.get("value"))
                actual = numeric(value)
                if expected is None or actual is None or not math.isclose(expected, actual, rel_tol=1e-9, abs_tol=1e-9):
                    errors.append(f"{label} 数值与来源不一致: declared={claim.get('value')} actual={value}")
                anchor = claim.get("text_anchor")
                if anchor and str(anchor) not in tex_text:
                    errors.append(f"{label} text_anchor 未在论文 TeX 中出现: {anchor}")
                claims_report.append({"id": claim_id, "value": expected, "source_file": str(source.relative_to(root)),
                                      "status": "PASS" if not errors or not errors[-1].startswith(label) else "FAIL"})
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"数字来源表无法解析: {exc}")
    payload = {"schema_version": "1.0", "checked_at": datetime.now(timezone.utc).isoformat(),
               "project_root": str(root), "source_map": str(source_map.relative_to(root)) if source_map else None,
               "claim_count": len(claims_report), "claims": claims_report, "issues": errors,
               "warnings": warnings, "passed": not errors}
    out = args.out.resolve() if args.out else root / ".contest" / "numeric_source_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
