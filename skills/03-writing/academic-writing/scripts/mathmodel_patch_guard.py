#!/usr/bin/env python3
"""Guard mathematical-modeling papers against unsafe prose-polish changes.

The guard compares a before/after project copy. Ordinary prose may change, but
mathematics, citations, numbers, table structure, figures, and bibliography
files must remain identical. It intentionally uses deterministic extraction;
the result is a safety gate, not a semantic proof of correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


PROTECTED_SUFFIXES = {".tex", ".bib"}
DATA_SUFFIXES = {".csv", ".json", ".yaml", ".yml"}

MATH_ENV = re.compile(
    r"\\begin\{(?:equation|align|gather|multline|split|cases)(?:\*)?\}.*?"
    r"\\end\{(?:equation|align|gather|multline|split|cases)(?:\*)?\}",
    re.S,
)
INLINE_MATH = re.compile(r"\$(?:\\.|[^$])*\$|\\\((?:\\.|[^)])*\\\)|\\\[(?:\\.|[^]])*\\\]", re.S)
REFERENCE = re.compile(
    r"\\(?:cite[a-z]*|parencite|textcite|autocite|ref|eqref|pageref|label)"
    r"\s*(?:\[[^\]]*\])?\s*\{[^}]*\}"
)
TABLE = re.compile(
    r"\\(?:begin|end)\{(?:table|tabular|tabularx|longtable|threeparttable)(?:\*|\})[^\n]*"
    r"|\\(?:toprule|midrule|bottomrule|cmidrule)(?:\[[^\]]*\])?"
)
FIGURE = re.compile(r"\\(?:includegraphics|caption|label)\s*(?:\[[^\]]*\])?\s*\{[^}]*\}")
NUMBER = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?\s*%?")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def norm(value: str) -> str:
    return re.sub(r"\s+", "", value)


def protected_tokens(text: str) -> dict[str, list[str]]:
    return {
        "math": sorted(norm(x) for x in MATH_ENV.findall(text) + INLINE_MATH.findall(text)),
        "references": sorted(norm(x) for x in REFERENCE.findall(text)),
        "tables": sorted(norm(x) for x in TABLE.findall(text)),
        "figures": sorted(norm(x) for x in FIGURE.findall(text)),
        "numbers": sorted(norm(x) for x in NUMBER.findall(text)),
    }


def files_by_suffix(root: Path, suffixes: set[str]) -> dict[str, Path]:
    return {
        str(p.relative_to(root)).replace("\\", "/"): p
        for p in root.rglob("*")
        if p.is_file() and p.suffix.lower() in suffixes
    }


def compare(before: Path, after: Path, include_data: bool = False) -> dict:
    issues: list[str] = []
    details: list[dict] = []
    suffixes = set(PROTECTED_SUFFIXES)
    if include_data:
        suffixes.update(DATA_SUFFIXES)
    before_files = files_by_suffix(before, suffixes)
    after_files = files_by_suffix(after, suffixes)
    if not any(Path(k).suffix.lower() == ".tex" for k in before_files):
        issues.append("before project has no .tex source")

    for rel in sorted(set(before_files) | set(after_files)):
        left = before_files.get(rel)
        right = after_files.get(rel)
        if left is None or right is None:
            issues.append(f"protected file added or removed: {rel}")
            continue
        suffix = Path(rel).suffix.lower()
        if suffix == ".bib" or (include_data and suffix in DATA_SUFFIXES):
            if digest(left) != digest(right):
                issues.append(f"protected file changed: {rel}")
            continue
        left_tokens = protected_tokens(left.read_text(encoding="utf-8"))
        right_tokens = protected_tokens(right.read_text(encoding="utf-8"))
        for category in left_tokens:
            if left_tokens[category] != right_tokens[category]:
                issues.append(f"{category} changed: {rel}")
        if left.read_text(encoding="utf-8") != right.read_text(encoding="utf-8"):
            details.append({"file": rel, "prose_changed": not issues or True})

    return {
        "schema_version": "1.0",
        "passed": not issues,
        "issues": sorted(set(issues)),
        "changed_files": details,
        "before": str(before.resolve()),
        "after": str(after.resolve()),
        "include_data": include_data,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--strict", action="store_true", help="return non-zero when a protected item changes")
    parser.add_argument("--include-data", action="store_true", help="also freeze csv/json/yaml files")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if not args.before.is_dir() or not args.after.is_dir():
        print("FAIL: before and after must be directories")
        return 1
    report = compare(args.before, args.after, args.include_data)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PASS" if report["passed"] else "FAIL")
    for issue in report["issues"]:
        print(f"- {issue}")
    return 0 if report["passed"] or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
