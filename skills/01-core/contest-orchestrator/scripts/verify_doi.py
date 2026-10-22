#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify BibTeX DOI syntax and optionally resolve DOI URLs.

Offline syntax errors are failures. Network unavailability is an explicit WARN,
never an online PASS; use --strict-online to make unverified online checks fail.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

DOI = re.compile(r"^10\.\d{4,9}/\S+$")


def skill_version() -> str:
    """Use the canonical VERSION file in diagnostics instead of a stale literal."""
    version_file = Path(__file__).resolve().parents[1] / "VERSION"
    try:
        value = version_file.read_text(encoding="utf-8").strip()
        return value or "unknown"
    except OSError:
        return "unknown"


def extract(text: str) -> list[str]:
    values = re.findall(r"\bdoi\s*=\s*[\{\"]([^}\"\n]+)[}\"]", text, flags=re.I)
    return [value.strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/") for value in values]


def resolve(doi: str) -> tuple[str, str | None]:
    request = urllib.request.Request(f"https://doi.org/{doi}", method="HEAD",
                                     headers={"User-Agent": f"contest-orchestrator/{skill_version()}"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return ("resolved" if 200 <= response.status < 400 else "not_found", response.geturl())
    except urllib.error.HTTPError as exc:
        return ("not_found", None if exc.code >= 400 else str(exc.code))
    except (urllib.error.URLError, TimeoutError, OSError):
        return ("unverified", None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bib", type=Path)
    parser.add_argument("--online", "--doi-online", action="store_true")
    parser.add_argument("--strict-online", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()
    if not args.bib.exists():
        print(json.dumps({"status": "FAIL", "passed": False, "issues": [f"missing: {args.bib}"]}, ensure_ascii=False))
        return 2
    dois = extract(args.bib.read_text(encoding="utf-8", errors="replace"))
    results = []
    seen: set[str] = set()
    for doi in dois:
        duplicate = doi in seen
        seen.add(doi)
        item = {"doi": doi, "syntax": bool(DOI.match(doi)), "duplicate": duplicate,
                "online": None, "resolved_url": None}
        if args.online and item["syntax"]:
            item["online"], item["resolved_url"] = resolve(doi)
        results.append(item)
    syntax_bad = [r for r in results if not r["syntax"] or r["duplicate"]]
    not_found = [r for r in results if r["online"] == "not_found"]
    unverified = [r for r in results if r["online"] == "unverified"]
    status = "FAIL" if syntax_bad or not_found else ("WARN" if unverified else "PASS")
    report = {
        "bib": str(args.bib.resolve()), "count": len(results), "results": results,
        "passed": not syntax_bad and not not_found,
        "strict_online_passed": not syntax_bad and not not_found and not unverified,
        "status": status,
        "warnings": ["网络不可用或 DOI 未能在线核验" for _ in [unverified] if unverified],
        "issues": (["DOI 语法错误或重复"] if syntax_bad else []) + (["DOI 无法解析"] if not_found else []),
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if status == "FAIL" or (args.strict_online and status == "WARN") else 0


if __name__ == "__main__":
    raise SystemExit(main())
