#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert legacy figure_registry.json metadata to the v2 schema.

The migration preserves the recorded generator as `legacy_generator`; it never
pretends that a figure was produced by SciPilot or manually drawn.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def split_sources(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.replace("；", ",").split(",") if item.strip()]
    return []


def migrate(source: Path) -> dict:
    data = json.loads(source.read_text(encoding="utf-8"))
    raw = data.get("figures", data) if isinstance(data, dict) else data
    if isinstance(raw, list):
        raw = {str(item.get("id", i)): item for i, item in enumerate(raw) if isinstance(item, dict)}
    figures = {}
    for key, item in (raw.items() if isinstance(raw, dict) else []):
        item = item if isinstance(item, dict) else {}
        legacy = str(item.get("generated_by", item.get("generator", ""))).strip()
        figures[str(key)] = {
            "id": str(item.get("id", key)),
            "kind": item.get("kind", item.get("type", "")),
            "legacy_generator": legacy,
            "generator": item.get("generator", ""),
            "source_files": split_sources(item.get("source_files", item.get("data_source", []))),
            "script": item.get("script", item.get("code", "")),
            "formats": item.get("formats", []),
            "qa_status": item.get("qa_status", "review"),
            "qa_checks": item.get("qa_checks", []),
            "layout_mode": item.get("layout_mode", "single"),
            "layout_group": item.get("layout_group"),
            "layout_variant": item.get("layout_variant"),
            "wrap_side": item.get("wrap_side"),
            "max_height": item.get("max_height"),
        }
    return {"schema_version": "2.0", "migrated_at": datetime.now(timezone.utc).isoformat(), "figures": figures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    output = migrate(args.source.resolve())
    if args.check_only:
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    out = args.out.resolve() if args.out else args.source.with_name("figure_registry.v2.json")
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"迁移报告已写入: {out}")
    print("注意：legacy_generator 已保留；必须人工确认并补齐 generator、source_files 和 QA 后才能通过门禁。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
