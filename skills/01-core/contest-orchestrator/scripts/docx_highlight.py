#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx_highlight.py — docx 代码段 Pygments 高亮(与 PDF minted 同引擎同配色, 2026-08-15)
用法: python scripts/docx_highlight.py <paper.docx>
对 Source Code 样式段落: 逐行 Pygments 分词 -> 按 token 颜色写 runs(Consolas 保留)。
"""
import re
import sys
import docx
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.styles import get_style_by_name


def token_color(style, ttype):
    """沿 token 父链查找颜色(与 minted 默认 style 一致)"""
    t = ttype
    while t is not None:
        if t in style.styles:
            spec = style.styles[t]
            m = re.search(r'#([0-9a-fA-F]{6})', str(spec))
            if m:
                return m.group(1)
            return None
        t = getattr(t, 'parent', None)
    return None


def highlight_paragraph(p, style):
    text = p.text
    if not text.strip():
        return 0
    # 清空原 runs
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    lexer = PythonLexer()
    first = True
    for line in text.split('\n'):
        if not first:
            run = p.add_run()
            run.add_break()
        first = False
        for ttype, value in lex(line, lexer):
            color = token_color(style, ttype)
            run = p.add_run(value)
            run.font.name = 'Consolas'
            run.font.size = Pt(9)
            rpr = run._element.get_or_add_rPr()
            rfonts = rpr.find(qn('w:rFonts'))
            if rfonts is None:
                rfonts = OxmlElement('w:rFonts')
                rpr.append(rfonts)
            rfonts.set(qn('w:ascii'), 'Consolas')
            rfonts.set(qn('w:hAnsi'), 'Consolas')
            if color:
                run.font.color.rgb = RGBColor.from_string(color)
    return 1


def main(path):
    doc = docx.Document(path)
    style = get_style_by_name('default')
    n = 0
    for p in doc.paragraphs:
        if p.style and 'Source Code' in p.style.name:
            n += highlight_paragraph(p, style)
    doc.save(path)
    print(f'高亮完成: {n} 个代码段(与 PDF minted 同引擎同配色)')
    return 0


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'paper.docx'
    sys.exit(main(path))
