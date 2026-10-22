#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字冻结机制（freeze_numbers.py）——实现 core/frozen_numbers.md

用法:
    python scripts/freeze_numbers.py freeze <结果目录> --out <frozen_numbers.json> [--competition cumcm]
        # 扫描结果目录的 .json/.csv，提取数值生成冻结表（含来源 sha256）
    python scripts/freeze_numbers.py check <论文目录> --frozen <frozen_numbers.json>
        # 扫描论文 .tex/.md 中出现的数字，对照冻结表：匹配 = OK，未匹配 = WARN 人工复核
    python scripts/freeze_numbers.py changelog <frozen_numbers.json> --reason "修正问题2数据清洗逻辑"

原则: 论文数字只来自冻结表；改数字必须先记 changelog 再重新冻结（借鉴 zhnnky329 的 G4 机制）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

NUM_RE = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_numbers(path: Path) -> list[float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [float(m) for m in NUM_RE.findall(text)]


def collect_numbers(obj, prefix: str, src: str, numbers: list) -> None:
    """递归提取嵌套 JSON 中的数值（2025B 实测：results_2025B.json 为多层嵌套）。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            collect_numbers(v, f"{prefix}.{k}" if prefix else str(k), src, numbers)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            collect_numbers(v, f"{prefix}[{i}]", src, numbers)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        numbers.append({"key": prefix, "value": float(obj), "source": src})


def freeze(results_dir: Path, out: Path, competition: str) -> dict:
    """扫描结果文件，生成冻结表。JSON 键名作为 key 的语义注释。"""
    numbers, sources = [], {}
    files = sorted(results_dir.rglob("*")) if results_dir.is_dir() else [results_dir]
    for f in files:
        if not f.is_file() or f.suffix.lower() not in (".json", ".csv"):
            continue
        sources[str(f.relative_to(results_dir) if results_dir.is_dir() else f.name)] = sha256(f)
        if f.suffix.lower() == ".json":
            try:
                # utf-8-sig：兼容 Windows 记事本/Excel 另存的带 BOM JSON
                data = json.loads(f.read_text(encoding="utf-8-sig", errors="replace"))
                collect_numbers(data, f.stem, f.name, numbers)
            except json.JSONDecodeError:
                pass
            continue
        # csv / 非 dict json：按出现顺序收数字（无语义 key）
        for val in extract_numbers(f):
            numbers.append({"key": f"{f.name}#{val}", "value": val, "source": str(f.name)})

    table = {"competition": competition,
             "frozen_at": datetime.now().isoformat(timespec="seconds"),
             "source_files": sources, "numbers": numbers,
             "policy": "改动须先记 changelog 再重新冻结"}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(table, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[冻结] {len(numbers)} 个数字 → {out}")
    return table


def load_frozen(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"[FATAL] 冻结表不存在: {path}（先跑 freeze 模式）")
    return json.loads(path.read_text(encoding="utf-8"))


def safe_print(s: str) -> str:
    """去除无法在 GBK 控制台打印的字符（如下标 ₀），防 Windows 终端崩溃。"""
    return re.sub(r"[^\u0000-\u007f\u4e00-\u9fff]", "?", s)


def check(paper_dir: Path, frozen: dict) -> int:
    """论文 .tex/.md 中的数字对照冻结表（容差 1e-6 相对误差）。"""
    frozen_vals = [n["value"] for n in frozen.get("numbers", [])]
    files = [p for p in sorted(paper_dir.rglob("*"))
             if p.is_file() and p.suffix.lower() in (".tex", ".md")]
    total, unmatched = 0, []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in NUM_RE.finditer(text):
            val = float(m.group())
            total += 1
            # 页码/年份/序号等整数的页码类放行：只对非平凡数字做严格匹配
            ok = any(abs(val - fv) <= 1e-6 * max(1.0, abs(fv)) for fv in frozen_vals)
            if not ok and abs(val) >= 0.001:  # 0.001 以下视为噪音
                s = max(0, m.start() - 20)
                unmatched.append((f.name, val, text[s:m.end() + 20].replace("\n", " ")))
    print(f"[校验] 论文 {len(files)} 个文件，扫描数字 {total} 个，冻结表 {len(frozen_vals)} 个")
    if not unmatched:
        print("[PASS] 所有非平凡数字均可在冻结表中找到来源")
        return 0
    print(f"[WARN] {len(unmatched)} 个数字未匹配冻结表（页码/公式编号等可忽略，关键结果需人工复核）:")
    for name, val, ctx in unmatched[:20]:
        print(f"  {name}: {val}  …{safe_print(ctx)}…")
    return 1


def changelog(frozen: dict, reason: str) -> None:
    """追加变更记录到 frozen_changelog.jsonl（重新冻结前必做）。"""
    path = Path(frozen.get("_path", ""))
    log = path.parent / "frozen_changelog.jsonl" if path else Path("frozen_changelog.jsonl")
    entry = {"time": datetime.now().isoformat(timespec="seconds"), "reason": reason}
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[changelog] 已记录: {reason} → {log}")


def main():
    ap = argparse.ArgumentParser(description="数字冻结机制")
    sub = ap.add_subparsers(dest="mode", required=True)
    p1 = sub.add_parser("freeze", help="扫描结果目录生成冻结表")
    p1.add_argument("results", help="结果文件或目录（.json/.csv）")
    p1.add_argument("--out", required=True, help="frozen_numbers.json 输出路径")
    p1.add_argument("--competition", default="cumcm")
    p2 = sub.add_parser("check", help="论文数字对照冻结表")
    p2.add_argument("paper_dir", help="论文目录（.tex/.md）")
    p2.add_argument("--frozen", required=True, help="frozen_numbers.json 路径")
    p3 = sub.add_parser("changelog", help="记录数字变更原因")
    p3.add_argument("frozen", help="frozen_numbers.json 路径")
    p3.add_argument("--reason", required=True, help="变更原因")
    args = ap.parse_args()

    if args.mode == "freeze":
        freeze(Path(args.results), Path(args.out), args.competition)
        return 0
    if args.mode == "check":
        return check(Path(args.paper_dir), load_frozen(Path(args.frozen)))
    if args.mode == "changelog":
        frozen = load_frozen(Path(args.frozen))
        frozen["_path"] = args.frozen
        changelog(frozen, args.reason)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
