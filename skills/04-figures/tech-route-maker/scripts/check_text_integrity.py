"""Fail on invalid UTF-8 or common Chinese mojibake signatures."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".drawio",
    ".html",
    ".json",
    ".md",
    ".mmd",
    ".py",
    ".svg",
    ".toml",
    ".xml",
    ".yaml",
    ".yml",
}
SKIP_PARTS = {".git", ".venv", "__pycache__", "build", "dist", "output"}
SUSPICIOUS = ("\ufffd", "鎴愭", "锛", "绾垮", "妫€", "瀛︿", "涓", "鍥惧", "璇佹", "")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    errors = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        if relative.as_posix() == "scripts/check_text_integrity.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"Invalid UTF-8: {relative}: {exc}")
            continue
        hits = [token for token in SUSPICIOUS if token in text]
        if hits:
            errors.append(f"Possible mojibake in {relative}: {', '.join(hits)}")
    if errors:
        print("Text integrity check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Text integrity check OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
