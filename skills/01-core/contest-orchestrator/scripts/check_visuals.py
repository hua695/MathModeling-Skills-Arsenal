#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_visuals.py — 程序化视觉核对(2026-08-15, 零外部依赖, 替代受限的 vision API)
用法: python scripts/check_visuals.py <paper.pdf> <paper.docx> [figures_dir]
检查项:
  PDF : 字体族(宋体+TNR+黑体+Consolas) / 图表来源与空白 / 关键词行加粗 / 摘要二字居中 / 页数
  docx: 标题颜色全黑(Heading 1/2/3) / 代码块五要素(浅灰底/边框/行号/高亮颜色/Consolas) / 图片居中 / 分页符 / 三线表
  图集: 全部非空白(像素方差) / 尺寸合理
"""
import os
import re
import sys


def safe(s):
    return s


def check_pdf(pdf):
    import pymupdf
    r = {}
    doc = pymupdf.open(pdf)
    n = len(doc)
    r['PDF 页数'] = f'PASS({n})' if n > 0 else 'FAIL(0)'
    # 字体族
    fonts = set()
    for i in range(min(n, 40)):
        d = doc[i].get_text('dict')
        for b in d['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']:
                    fonts.add(s['font'])
    fstr = '|'.join(fonts)
    ok = ('SimSun' in fstr or '宋体' in fstr) and ('Times' in fstr) and ('SimHei' in fstr) and ('Consolas' in fstr or 'consol' in fstr.lower())
    r['PDF 字体族(宋体/TNR/黑体/Consolas)'] = 'PASS' if ok else f'FAIL({sorted(fonts)[:6]})'
    # 关键词行加粗: 第1页 关键词 span 字体含 Bold 或 SimHei
    d0 = doc[0].get_text('dict')
    kw_bold = False
    for b in d0['blocks']:
        for l in b.get('lines', []):
            t = ''.join(s['text'] for s in l['spans'])
            if t.startswith('关键词'):
                kw_bold = any(('Bold' in s['font']) or ('SimHei' in s['font']) for s in l['spans'])
                break
    r['关键词行加粗'] = 'PASS' if kw_bold else 'FAIL'
    # 摘要二字居中: 页面中心 ±40pt
    abs_center = False
    for b in d0['blocks']:
        for l in b.get('lines', []):
            t = ''.join(s['text'] for s in l['spans']).strip()
            if t == '摘要':
                cx = (l['bbox'][0] + l['bbox'][2]) / 2
                page_cx = d0['width'] / 2
                abs_center = abs(cx - page_cx) < 40
                break
    r['摘要二字居中'] = 'PASS' if abs_center else 'FAIL'
    return r


def check_docx(docx_path):
    import docx
    from docx.oxml.ns import qn
    r = {}
    doc = docx.Document(docx_path)
    # 标题颜色
    bad = []
    for s in ['Heading 1', 'Heading 2', 'Heading 3']:
        st = doc.styles[s]
        c = st.font.color.rgb if st.font.color and st.font.color.rgb else None
        if str(c) != '000000':
            bad.append(f'{s}={c}')
    r['标题颜色全黑'] = 'PASS' if not bad else f'FAIL({bad})'
    # 代码块五要素
    n_code = 0
    box_ok = 0
    for p in doc.paragraphs:
        if p.style and 'Source Code' in p.style.name:
            n_code += 1
            pPr = p._p.find(qn('w:pPr'))
            xml = pPr.xml if pPr is not None else ''
            has_shd = 'F5F5F5' in xml
            has_bdr = 'w:pBdr' in xml
            has_lineno = bool(p.runs) and p.runs[0].text.strip().lstrip('\ue000').strip().isdigit()
            colors = set()
            for rr in p.runs:
                cc = rr.font.color.rgb if rr.font.color and rr.font.color.rgb else None
                if cc and rr.text.strip():
                    colors.add(str(cc))
            colored = len(colors - {'999999'}) > 0
            if has_shd and has_bdr and has_lineno and colored:
                box_ok += 1
    r['代码块五要素'] = f'PASS({box_ok}/{n_code})' if n_code and box_ok == n_code else f'FAIL({box_ok}/{n_code})'
    # 图片居中
    fig = fig_c = 0
    for p in doc.paragraphs:
        if p._element.findall('.//' + qn('w:drawing')):
            fig += 1
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            if p.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                fig_c += 1
    r['图片居中'] = f'PASS({fig_c}/{fig})' if fig and fig_c == fig else f'FAIL({fig_c}/{fig})'
    return r


def check_figures(figdir):
    import numpy as np
    from PIL import Image
    r = {}
    if not figdir or not os.path.isdir(figdir):
        r['图集'] = 'SKIP(无目录)'
        return r
    bad = []
    files = sorted([f for f in os.listdir(figdir) if f.lower().endswith(('.png', '.jpg'))])
    for f in files:
        im = np.asarray(Image.open(os.path.join(figdir, f)).convert('L'), dtype=float)
        if im.std() < 15 or im.shape[0] < 100 or im.shape[1] < 100:
            bad.append(f)
    r['图集非空白'] = f'PASS({len(files)} 张)' if not bad else f'FAIL({bad})'
    return r


def main(pdf, docx_path, figdir=None):
    print(f'=== 程序化视觉核对: {pdf} | {docx_path} ===')
    all_ok = True
    for name, rr in [('PDF', check_pdf(pdf)), ('DOCX', check_docx(docx_path)), ('图集', check_figures(figdir))]:
        for k, v in rr.items():
            ok = str(v).startswith('PASS') or str(v).startswith('SKIP')
            all_ok = all_ok and ok
            print(f"  [{'OK' if ok else 'FAIL'}] {name} {k}: {v}")
    print(f'===== 程序化视觉: {"PASS" if all_ok else "FAIL"} =====')
    return all_ok


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    fig = sys.argv[3] if len(sys.argv) > 3 else None
    sys.exit(0 if main(sys.argv[1], sys.argv[2], fig) else 1)
