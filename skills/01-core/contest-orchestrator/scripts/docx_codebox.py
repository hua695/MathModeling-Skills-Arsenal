#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx_codebox.py — 代码块美化(2026-08-15, 用户参考图样式):
浅灰背景(#F5F5F5) + 细黑边框 + 块内连续灰色行号(1 起)。
兼容顺序: 先跑 docx_highlight.py(分词上色), 再跑本脚本(背景/边框/行号插入式, 不破坏高亮 run)。
用法: python scripts/docx_codebox.py <paper.docx>
"""
import sys
import docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def add_shading(p, fill='F5F5F5'):
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    pPr.append(shd)


def add_border(p):
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    for side in ['top', 'left', 'bottom', 'right']:
        el = OxmlElement('w:' + side)
        el.set(qn('w:val'), 'single')
        el.set(qn('w:sz'), '4')
        el.set(qn('w:space'), '4')
        el.set(qn('w:color'), '000000')
        pBdr.append(el)
    pPr.append(pBdr)


def make_num_run(lineno):
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), 'Consolas')
    rFonts.set(qn('w:hAnsi'), 'Consolas')
    rPr.append(rFonts)
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), '18')            # 9pt
    rPr.append(sz)
    color = OxmlElement('w:color')
    color.set(qn('w:val'), '999999')     # 浅灰行号
    rPr.append(color)
    r.append(rPr)
    t = OxmlElement('w:t')
    t.text = '%3d  ' % lineno
    t.set(qn('xml:space'), 'preserve')
    r.append(t)
    return r


def add_linenos(p):
    """在每行开头的 run 前插入灰色行号 run(不破坏高亮 run 的颜色)"""
    runs = p.runs
    if not runs:
        return
    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    inserts = []   # (run_element, lineno)
    lineno = 0
    at_line_start = True
    for r in runs:
        has_br = bool(r._r.findall(W + 'br'))
        if at_line_start and not has_br:
            lineno += 1
            inserts.append((r._r, lineno))
            at_line_start = False
        elif has_br:
            at_line_start = True
    for r_el, ln in reversed(inserts):
        r_el.addprevious(make_num_run(ln))


def main(path):
    doc = docx.Document(path)
    n = 0
    for p in doc.paragraphs:
        if p.style and 'Source Code' in p.style.name:
            add_shading(p)
            add_border(p)
            add_linenos(p)
            n += 1
    doc.save(path)
    print(f'代码块美化: {n} 个(浅灰底+细边框+灰色行号)')
    return 0


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'paper.docx'
    sys.exit(main(path))
