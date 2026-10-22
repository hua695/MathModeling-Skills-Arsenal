#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_pdf_tables.py — PDF 表格结构化提取（2026-08-16，解决 FD-682 教训）

背景：pymupdf 的 get_text() 提取多列表格会行列交错（2024B 表2 实测乱序），
需人工重排且可能出错。pymupdf 1.23+ 的 find_tables() 可结构化提取行列，
实测 2024B 表1/表2 与人工重排 100% 一致。

用法:
  python scripts/extract_pdf_tables.py <paper.pdf> [--out dir] [--json]
  # 默认输出每页表格的 Markdown 到 stdout；--out 落盘 <pdf名>_tables.md / .json
依赖: pymupdf >= 1.23
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def extract_tables(pdf_path: str) -> list[dict]:
    """返回 [{page, table_index, rows: [[str]]}]。"""
    import pymupdf
    out = []
    doc = pymupdf.open(pdf_path)
    for pno in range(len(doc)):
        page = doc[pno]
        try:
            tabs = page.find_tables()
        except AttributeError:
            sys.exit("[FATAL] pymupdf >= 1.23 才有 find_tables()，请升级: pip install -U pymupdf")
        for ti, t in enumerate(tabs.tables):
            rows = [[str(c) if c is not None else "" for c in row] for row in t.extract()]
            if rows:
                out.append({"page": pno + 1, "table": ti + 1, "rows": rows})
    return out


def to_markdown(table: dict) -> str:
    rows = table["rows"]
    lines = [f"### 第{table['page']}页 表{table['table']} ({len(rows)}行 x {len(rows[0])}列)", ""]
    for ri, row in enumerate(rows):
        cells = [c.replace("\n", " ") for c in row]
        lines.append("| " + " | ".join(cells) + " |")
        if ri == 0:
            lines.append("|" + "---|" * len(row))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="PDF 表格结构化提取")
    ap.add_argument("pdf", help="PDF 路径")
    ap.add_argument("--out", default=None, help="输出目录（默认仅打印 Markdown）")
    ap.add_argument("--json", action="store_true", help="同时落盘 JSON")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        sys.exit(f"[FATAL] 文件不存在: {args.pdf}")
    tables = extract_tables(args.pdf)
    if not tables:
        print("[WARN] 未检测到表格（find_tables 对复杂版式可能漏检，可人工核对）")
        return 0

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        base = os.path.splitext(os.path.basename(args.pdf))[0]
        md_path = os.path.join(args.out, base + "_tables.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {base} 表格提取（pymupdf find_tables）\n\n")
            f.write("\n\n".join(to_markdown(t) for t in tables))
            f.write("\n")
        print(f"[落盘] {md_path}（{len(tables)} 个表格）")
        if args.json:
            jp = os.path.join(args.out, base + "_tables.json")
            with open(jp, "w", encoding="utf-8") as f:
                json.dump(tables, f, ensure_ascii=False, indent=2)
            print(f"[落盘] {jp}")
    else:
        for t in tables:
            print(to_markdown(t))
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
