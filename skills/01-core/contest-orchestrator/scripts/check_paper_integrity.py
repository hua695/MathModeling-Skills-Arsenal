#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Candidate v4.18 paper-integrity gate.

Checks current TeX/PDF text for internal process leakage, validates symbol
table entries against first body use, and detects temporary artifacts in a
declared delivery directory. The gate is intentionally opt-in until v4.18
is promoted.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


DEFAULT_NEGATIVE_ECHO = (
    "原方案", "之前考虑过", "弃用", "本来打算", "上一版", "刚才的错误",
    "我们排除了", "不适用于旧版本", "调试报错", "失败尝试", "中间备选",
)

DEFAULT_INTERNAL_META = (
    r"根据(?:评审|审稿|用户|子\s*Agent|agent)(?:意见|建议|要求|反馈)?",
    r"(?:用户|子\s*Agent|agent)(?:确认|建议|要求)",
    r"本轮(?:检查|修复|修改|审阅|迭代)",
    r"(?:我们|本文作者)(?:修改|删除|保留|排除|修复)了",
    r"提示词",
    r"内部(?:交流|讨论|过程)",
)

PACKAGING_SEGMENTS = {
    "before", "after", "tmp", "snapshot", "snapshots", "logs", "log",
    "prompts", "prompt", "review", "reviews", "debug", "调试", "审稿",
}
DEFINITION_MARKERS = re.compile(
    r"定义|表示|记为|记作|设|令|其中|分别为|为|denote|define|let",
    re.IGNORECASE,
)


def _tex_files(root: Path, excluded: set[str] | None = None) -> list[Path]:
    excluded = {item.lower() for item in (excluded or set())}
    return [
        path for path in sorted(root.rglob("*.tex"))
        if not any(part.lower() in excluded for part in path.parts)
    ]


def _line_hits(text: str, path: Path, category: str, patterns: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    lines = text.splitlines()
    for line_no, line in enumerate(lines, 1):
        for pattern in patterns:
            matched = re.search(pattern, line) if category == "internal_meta" else pattern in line
            if matched:
                hits.append({
                    "file": str(path),
                    "line": line_no,
                    "category": category,
                    "pattern": pattern,
                    "text": line.strip(),
                })
    return hits


def _read_artifact(path: Path) -> str:
    if path.suffix.lower() != ".pdf":
        return path.read_text(encoding="utf-8", errors="replace")
    try:
        import pymupdf
    except Exception as exc:
        raise RuntimeError(f"读取 PDF 需要 PyMuPDF: {path}") from exc
    document = pymupdf.open(str(path))
    try:
        return "\n".join(page.get_text() for page in document)
    finally:
        document.close()


def _load_symbols(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    if path.suffix.lower() == ".md":
        return _load_markdown_symbols(path)
    try:
        import yaml
    except Exception as exc:
        return [], [f"缺少 PyYAML，无法读取符号契约: {exc}"]
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    except Exception as exc:
        return [], [f"符号契约无法解析: {exc}"]
    entries: list[dict[str, str]] = []
    issues: list[str] = []
    subproblems = payload.get("subproblems", []) if isinstance(payload, dict) else []
    if not isinstance(subproblems, list):
        return [], ["符号契约的 subproblems 必须是列表"]
    for item in subproblems:
        if not isinstance(item, dict):
            continue
        qid = str(item.get("id", ""))
        values = item.get("symbols")
        if values is None and isinstance(item.get("evidence"), dict):
            evidence = item["evidence"].get("symbols_units")
            values = evidence.get("symbols") if isinstance(evidence, dict) else None
        if isinstance(values, dict):
            values = [{"name": key, **(value if isinstance(value, dict) else {"meaning": value})}
                      for key, value in values.items()]
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, str):
                value = {"name": value}
            if not isinstance(value, dict):
                continue
            name = str(value.get("latex", value.get("symbol", value.get("name", "")))).strip()
            meaning = str(value.get("meaning", "")).strip()
            if not name:
                issues.append(f"{qid} 存在缺少 name/latex 的符号条目")
                continue
            if not meaning:
                issues.append(f"{qid}:{name} 缺少 meaning")
            entries.append({"qid": qid, "name": name, "meaning": meaning})
    return entries, issues


def _load_markdown_symbols(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    entries: list[dict[str, str]] = []
    issues: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= {"-", ":"} or cells[0] in {"符号", "symbol"}:
            continue
        meaning = cells[1]
        names = [item.strip().strip("$").strip() for item in re.split(r",\s*", cells[0])]
        for name in names:
            if not name:
                continue
            if not meaning:
                issues.append(f"{path}:{line_no}:{name} 缺少 meaning")
            entries.append({"qid": "symbol_table", "name": name, "meaning": meaning})
    if not entries:
        issues.append(f"符号表未解析出有效条目: {path}")
    return entries, issues


def _symbol_variants(name: str) -> set[str]:
    variants = {name, re.sub(r"([_^])\{([^{}]+)\}", r"\1\2", name)}
    return {item for item in variants if item}


def _find_symbol(text: str, name: str) -> re.Match[str] | None:
    for variant in _symbol_variants(name):
        escaped = re.escape(variant)
        if re.fullmatch(r"[A-Za-z0-9]+", variant):
            match = re.search(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", text)
        else:
            match = re.search(escaped, text)
        if match:
            return match
    return None


def _body_text(text: str) -> str:
    environments = r"table|table\*|tabular|tabularx|minted|verbatim|lstlisting"
    return re.sub(
        rf"\\begin\{{(?:{environments})\}}.*?\\end\{{(?:{environments})\}}",
        "",
        text,
        flags=re.DOTALL,
    )


def _check_symbols(
    symbols_path: Path,
    paper_root: Path,
    symbol_table: Path | None,
    strict_first_use: bool,
) -> dict[str, Any]:
    entries, issues = _load_symbols(symbols_path)
    warnings: list[str] = []
    excluded = {"before", "after", "tmp", "snapshot", "snapshots"}
    files = _tex_files(paper_root, excluded)
    if symbol_table:
        symbol_table = symbol_table.resolve()
        files = [path for path in files if path.resolve() != symbol_table]
    checks: list[dict[str, Any]] = []
    for entry in entries:
        first: dict[str, Any] | None = None
        for path in files:
            text = _body_text(path.read_text(encoding="utf-8", errors="replace"))
            match = _find_symbol(text, entry["name"])
            if match:
                line_no = text.count("\n", 0, match.start()) + 1
                lines = text.splitlines()
                window = "\n".join(lines[max(0, line_no - 4):line_no])
                first = {"file": str(path), "line": line_no, "context": window}
                if not DEFINITION_MARKERS.search(window):
                    message = (
                        f"{entry['qid']}:{entry['name']} 首次正文出现缺少定义语句 "
                        f"({path}:{line_no})"
                    )
                    if strict_first_use:
                        issues.append(message)
                    elif symbol_table is None:
                        warnings.append(message)
                break
        if first is None:
            warnings.append(f"{entry['qid']}:{entry['name']} 未在正文 TeX 中出现（符号表保留项）")
        checks.append({**entry, "first_body_use": first})
    return {"symbols_file": str(symbols_path), "checks": checks, "issues": issues,
            "warnings": warnings, "scanned_files": [str(path) for path in files]}


def _check_packaging(delivery_dir: Path) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in sorted(delivery_dir.rglob("*")):
        relative = path.relative_to(delivery_dir)
        bad_parts = [part for part in relative.parts[:-1] if part.lower() in PACKAGING_SEGMENTS]
        if path.is_dir() and path.name.lower() in PACKAGING_SEGMENTS:
            bad_parts.append(path.name)
        if bad_parts:
            hits.append({"path": str(path), "reason": "internal_or_temporary_path"})
    return hits


def scan(
    paper_root: Path,
    pdf_text: Path | None = None,
    symbols: Path | None = None,
    symbol_table: Path | None = None,
    delivery_dir: Path | None = None,
    allow: list[str] | None = None,
    strict_first_use: bool = False,
) -> dict[str, Any]:
    paper_root = paper_root.resolve()
    allow_set = set(allow or [])
    echo_patterns = [item for item in DEFAULT_NEGATIVE_ECHO if item not in allow_set]
    meta_patterns = [item for item in DEFAULT_INTERNAL_META if item not in allow_set]
    scanned: list[Path] = _tex_files(paper_root, {"before", "after", "tmp", "snapshot", "snapshots"})
    if pdf_text:
        scanned.append(pdf_text.resolve())
    echo_hits: list[dict[str, Any]] = []
    meta_hits: list[dict[str, Any]] = []
    for path in scanned:
        text = _read_artifact(path)
        echo_hits.extend(_line_hits(text, path, "negative_echo", echo_patterns))
        meta_hits.extend(_line_hits(text, path, "internal_meta", meta_patterns))
    symbol_report = None
    if symbols:
        symbol_report = _check_symbols(symbols.resolve(), paper_root, symbol_table, strict_first_use)
    packaging_hits = _check_packaging(delivery_dir.resolve()) if delivery_dir else []
    issues = echo_hits + meta_hits + packaging_hits
    if symbol_report:
        issues.extend({"category": "symbol_first_use", "text": item}
                      for item in symbol_report["issues"])
    warnings = list(symbol_report["warnings"]) if symbol_report else []
    return {
        "schema_version": "0.1",
        "version": "4.18",
        "passed": not issues,
        "gate_status": "PASS" if not issues else "BLOCK",
        "warnings": warnings,
        "negative_echo_hits": echo_hits,
        "internal_meta_hits": meta_hits,
        "packaging_hits": packaging_hits,
        "symbol_report": symbol_report,
        "scanned_files": [str(path) for path in scanned],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper_root", type=Path)
    parser.add_argument("--pdf-text", type=Path, default=None)
    parser.add_argument("--pdf", type=Path, default=None, help="直接读取 PDF 文本层")
    parser.add_argument("--symbols", type=Path, default=None)
    parser.add_argument("--symbol-table", type=Path, default=None)
    parser.add_argument("--delivery-dir", type=Path, default=None)
    parser.add_argument("--allow", action="append", default=[])
    parser.add_argument("--strict-first-use", action="store_true",
                        help="将首次正文出现缺少定义语句升级为阻断")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    try:
        pdf_text = args.pdf or args.pdf_text
        report = scan(args.paper_root, pdf_text, args.symbols, args.symbol_table,
                      args.delivery_dir, args.allow, args.strict_first_use)
    except Exception as exc:
        report = {"schema_version": "0.1", "version": "4.18", "passed": False,
                  "gate_status": "BLOCK", "errors": [str(exc)]}
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.out.resolve().write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
