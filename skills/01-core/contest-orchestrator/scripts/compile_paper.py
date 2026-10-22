#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compile a paper with a deterministic latexmk/XeLaTeX fallback and report."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WINDOWS_TOOL_DIRS = (
    Path(r"C:\Program Files\Inkscape\bin"),
    Path(r"C:\Program Files (x86)\Inkscape\bin"),
)

# Windows PowerShell may expose a GBK stdout even when the paper/toolchain
# emits UTF-8 diagnostics.  Reconfigure the entrypoint itself, not only child
# processes, so the JSON report can always be printed without masking the real
# compile result with a UnicodeEncodeError.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def utf8_subprocess_env() -> dict[str, str]:
    """Return a child-process environment that is stable on Windows consoles."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    if os.name == "nt":
        path_key = next((key for key in env if key.lower() == "path"), "Path")
        current = env.get(path_key, "")
        existing = [str(path) for path in WINDOWS_TOOL_DIRS if path.is_dir()]
        current_parts = [part for part in current.split(os.pathsep) if part]
        managed = {item.lower() for item in existing}
        unmanaged = [part for part in current_parts if part.lower() not in managed]
        if existing:
            # Keep configured tool directories first even when the parent
            # process already exposes them later in PATH.
            env[path_key] = os.pathsep.join(existing + unmanaged)
    return env


def run_command(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> dict:
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=1800,
                                env=env or utf8_subprocess_env())
        output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
        return {"command": cmd, "returncode": result.returncode, "tail": output[-2000:]}
    except subprocess.TimeoutExpired:
        return {"command": cmd, "returncode": 124, "tail": "command timed out after 1800s"}
    except OSError as exc:
        return {"command": cmd, "returncode": 127, "tail": str(exc)}


def latexmkrc_risks(workspace: Path) -> list[str]:
    """Find POSIX-only constructs that can break latexmk on Windows.

    The project rc file is user-owned and is never edited here.  When such a
    construct is found, the caller uses the deterministic XeLaTeX fallback.
    """
    if os.name != "nt":
        return []
    patterns = {
        r"\bcommand\s+-v\b": "command -v",
        r"\bwhich\s+": "which",
        r"/usr/bin|/bin/sh|/bin/bash": "POSIX absolute path",
        r"\bsource\s+": "source command",
    }
    risks: list[str] = []
    for filename in ("latexmkrc", ".latexmkrc"):
        path = workspace / filename
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern, label in patterns.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                risks.append(f"{filename}: {label}")
    return risks


def toolchain_snapshot(workspace: Path) -> dict:
    """Record executable availability without making missing Perl a failure."""
    paths = {name: shutil.which(name) for name in
             ("xelatex", "latexmk", "perl", "bibtex", "bibtex8", "biber", "latexminted")}
    snapshot = {
        "platform": sys.platform,
        "executables": paths,
        "latexmk_usable": bool(paths["latexmk"] and paths["perl"]),
        "fallback_expected": not bool(paths["latexmk"] and paths["perl"]),
    }
    pygments = run_command([sys.executable, "-X", "utf8", "-m", "pygments", "-V"], workspace)
    snapshot["pygments"] = {
        "available": pygments["returncode"] == 0,
        "version_output": pygments["tail"].splitlines()[-1] if pygments["tail"] else "",
    }
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--tex", default="paper.tex")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    tex = Path(args.tex)
    tex_path = tex if tex.is_absolute() else workspace / tex
    report = {"workspace": str(workspace), "tex": str(tex_path), "started_at": datetime.now(timezone.utc).isoformat(),
              "method": None, "commands": [], "passed": False, "issues": [], "warnings": []}
    if not workspace.is_dir() or not tex_path.exists():
        report["issues"].append(f"论文目录或 TeX 文件不存在: {tex_path}")
    else:
        report["toolchain"] = toolchain_snapshot(workspace)
        tex_source = tex_path.read_text(encoding="utf-8", errors="replace")
        needs_shell_escape = bool(re.search(r"\\(?:usepackage(?:\[[^]]*\])?\{minted\}|inputminted|begin\{minted\})", tex_source))
        engine_flags = ["-shell-escape"] if needs_shell_escape else []
        uses_bibliography_backend = bool(re.search(r"\\(?:bibliography|addbibresource)\b", tex_source))
        latexmk = shutil.which("latexmk")
        perl = shutil.which("perl")
        rc_risks = latexmkrc_risks(workspace)
        if rc_risks:
            report["warnings"].append(
                "Windows latexmkrc 含 POSIX 构造，已安全降级到 XeLaTeX 回退链: " + ", ".join(rc_risks)
            )
        if latexmk and perl and not rc_risks:
            report["method"] = "latexmk-xelatex"
            engine = "xelatex -shell-escape %O %S" if needs_shell_escape else "xelatex %O %S"
            report["commands"].append(run_command([latexmk, f"-xelatex={engine}", "-interaction=nonstopmode",
                                                     "-halt-on-error", "-file-line-error", tex_path.name], workspace))
        else:
            xelatex = shutil.which("xelatex")
            bibtex = shutil.which("bibtex")
            bibtex8 = shutil.which("bibtex8")
            report["method"] = "xelatex-bibtex-fallback"
            if not perl and latexmk:
                report["warnings"].append("检测到 latexmk 但未检测到 Perl；按设计使用 XeLaTeX/BibTeX 回退链")
            elif rc_risks:
                report["warnings"].append("未直接调用 latexmk，以避免 Windows 解析项目 latexmkrc 失败")
            if not xelatex:
                report["issues"].append("找不到 xelatex，无法编译论文")
            else:
                report["commands"].append(run_command([xelatex, *engine_flags, "-interaction=nonstopmode", "-halt-on-error",
                                                         "-file-line-error", tex_path.name], workspace))
                aux = tex_path.with_suffix(".aux")
                if bibtex and aux.exists() and uses_bibliography_backend:
                    bib_result = run_command([bibtex, tex_path.stem], workspace)
                    report["commands"].append(bib_result)
                    if bib_result["returncode"] != 0 and bibtex8:
                        # Some Windows MiKTeX distributions crash in bibtex.exe
                        # on UTF-8 records although the bundled bibtex8 works.
                        bib_result["allow_failure"] = True
                        report["commands"].append(run_command([bibtex8, tex_path.stem], workspace))
                for _ in range(2):
                    report["commands"].append(run_command([xelatex, *engine_flags, "-interaction=nonstopmode", "-halt-on-error",
                                                             "-file-line-error", tex_path.name], workspace))
        failed_commands = [item for item in report["commands"]
                           if item["returncode"] != 0 and not item.get("allow_failure")]
        if failed_commands:
            report["issues"].append(f"编译命令失败 {len(failed_commands)} 个")
        pdf = tex_path.with_suffix(".pdf")
        if not pdf.exists():
            report["issues"].append(f"编译未生成 PDF: {pdf}")
        elif pdf.stat().st_mtime < tex_path.stat().st_mtime:
            report["issues"].append("生成的 PDF 早于 TeX，属于过期产物")
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["passed"] = not report["issues"]
    out = args.json_out.resolve() if args.json_out else workspace / "compile_report.json"
    if workspace.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
