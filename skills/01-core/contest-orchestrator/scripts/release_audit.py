#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create a non-destructive release baseline and protected-state inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SECRET = re.compile(r"(?i)(?:api[_-]?key|password|private[_-]?key)\s*[:=]\s*[\"'][^\"']{12,}[\"']|(?:token|secret)\s*[:=]\s*[\"'][A-Za-z0-9_\-]{16,}[\"']")
EXCLUDE = {".git", "__pycache__"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read_skill_version(root: Path) -> str:
    version_file = root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8", errors="replace").strip()
    skill = root / "SKILL.md"
    match = re.search(r"^\s+version:\s*[\"']?([^\"'\s]+)", skill.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
    return match.group(1) if match else "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    files = []
    secret_candidates = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in EXCLUDE for part in path.parts):
            continue
        rel = str(path.relative_to(root))
        files.append({"path": rel, "size": path.stat().st_size, "sha256": digest(path)})
        if path.suffix.lower() in {".py", ".yaml", ".yml", ".json", ".toml", ".md"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if SECRET.search(text) and not path.name in {"AGENTS.md", "MEMORY.md"}:
                secret_candidates.append(rel)
    try:
        status = subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True,
                                text=True, encoding="utf-8", errors="replace").stdout.splitlines()
    except OSError:
        status = []
    report = {
        "schema_version": "1.0", "created_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root), "git_status": status, "file_count": len(files),
        "files": files, "protected_patterns": ["competition_replay/**", "*_backup*", "untracked user files"],
        "secret_candidates": secret_candidates,
        "passed": not secret_candidates,
    }
    release = read_skill_version(root)
    report["skill_version"] = release
    out = args.out.resolve() if args.out else root / "docs" / "audits" / f"v{release}" / "baseline_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("root", "file_count", "passed", "secret_candidates")}, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
