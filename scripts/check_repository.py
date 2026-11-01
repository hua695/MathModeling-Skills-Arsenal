"""Check public documentation links, skill entrypoints and accidental secrets."""
import ast
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parents[1]


def main():
    failures = []
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode("utf-8").split("\0")
    paths = [ROOT / name for name in names if name and (ROOT / name).is_file()]
    secret_patterns = [r"ghp_[A-Za-z0-9]{36}", r"github_pat_[A-Za-z0-9_]{50,}", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]
    for path in paths:
        if path.suffix.lower() not in {".py", ".md", ".yaml", ".yml", ".json", ".txt", ".csv"}:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(re.search(pattern, text) for pattern in secret_patterns):
            failures.append(f"Possible secret: {path.relative_to(ROOT)}")
        if path.suffix == ".py":
            try:
                ast.parse(text, filename=str(path.relative_to(ROOT)))
            except SyntaxError as error:
                failures.append(f"Python syntax: {path.relative_to(ROOT)}:{error.lineno}")
    entrypoints = sorted(ROOT.glob("skills/*/*/SKILL.md"))
    for path in entrypoints:
        text = path.read_text(encoding="utf-8-sig")
        if not text.startswith("---"):
            failures.append(f"Missing frontmatter: {path.relative_to(ROOT)}")
            continue
        try:
            metadata = yaml.safe_load(text.split("---", 2)[1])
            if not isinstance(metadata, dict) or not metadata.get("name") or not metadata.get("description"):
                failures.append(f"Missing name/description: {path.relative_to(ROOT)}")
        except yaml.YAMLError:
            failures.append(f"Invalid YAML: {path.relative_to(ROOT)}")
    documents = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", *ROOT.glob("docs/*.md"), *ROOT.glob("examples/**/*.md")]
    for path in documents:
        text = path.read_text(encoding="utf-8-sig")
        for target in re.findall(r"\]\(([^\s)]+)\)", text):
            if target.startswith(("http:", "https:", "mailto:", "#")):
                continue
            local = unquote(target.split("#", 1)[0])
            if not (path.parent / local).exists():
                failures.append(f"Broken link: {path.relative_to(ROOT)} -> {local}")
    print(f"Checked {len(entrypoints)} skill entrypoints, {len(documents)} public documents and tracked source files.")
    for failure in failures:
        print(failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
