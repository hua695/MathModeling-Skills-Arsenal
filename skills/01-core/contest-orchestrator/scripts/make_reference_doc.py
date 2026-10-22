#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 pandoc reference.docx 样式模板，不在 import 时写文件。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor


def _set_fonts(style, cn_font="宋体", en_font="Times New Roman", size=12,
               bold=None, color=None, align=None) -> None:
    font = style.font
    font.size = Pt(size)
    if bold is not None:
        font.bold = bold
    if color:
        font.color.rgb = RGBColor(*color)
    properties = style.element.get_or_add_rPr()
    fonts = properties.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        properties.append(fonts)
    fonts.set(qn("w:ascii"), en_font)
    fonts.set(qn("w:hAnsi"), en_font)
    fonts.set(qn("w:eastAsia"), cn_font)
    if align is not None:
        style.paragraph_format.alignment = align


def create_reference_doc(output: str | Path) -> Path:
    """Create one reference document at the caller-provided path."""
    destination = Path(output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = docx.Document()
    _set_fonts(document.styles["Normal"], size=12)
    document.styles["Normal"].paragraph_format.line_spacing = 1.3

    black = (0, 0, 0)
    for style_name, size in (("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 12)):
        _set_fonts(document.styles[style_name], "黑体", "Times New Roman", size,
                   bold=True, color=black, align=WD_ALIGN_PARAGRAPH.LEFT)

    _set_fonts(document.styles["Caption"], "宋体", "Times New Roman", 9,
               align=WD_ALIGN_PARAGRAPH.CENTER)
    for style_name in ("Image Caption", "Table Caption"):
        try:
            _set_fonts(document.styles[style_name], "宋体", "Times New Roman", 9,
                       align=WD_ALIGN_PARAGRAPH.CENTER)
        except KeyError:
            pass
    try:
        _set_fonts(document.styles["Source Code"], "宋体", "Consolas", 9)
    except KeyError:
        pass

    document.save(destination)
    print(f"reference.docx -> {destination}")
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path.cwd() / "reference.docx",
        help="输出模板路径；默认写入当前工作目录",
    )
    args = parser.parse_args(argv)
    create_reference_doc(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
