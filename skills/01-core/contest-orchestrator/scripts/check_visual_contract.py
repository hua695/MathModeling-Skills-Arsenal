#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_visual_contract.py — 视觉排版合同自动核对(core/output_contract.md)
用法: python scripts/check_visual_contract.py <paper.docx>
返回每项 PASS/FAIL, 供 Paper-Critic polish 阶段使用(WR-766/746/759/760/747/742/743/744/763 联动)
"""
import sys, re, zipfile
import docx
from docx.oxml.ns import qn

def check(path):
    doc = docx.Document(path)
    z = zipfile.ZipFile(path)
    xml = z.read('word/document.xml').decode('utf-8')
    results = {}

    # 1. 标题居中: 首页首段(题目)
    title_ok = False
    for p in doc.paragraphs[:5]:
        if p.text.strip() and len(p.text.strip()) > 8:
            title_ok = (p.alignment is not None and p.alignment == 1)  # CENTER=1
            break
    results['title_center'] = 'PASS' if title_ok else 'FAIL'

    # 2. 图片居中
    fig_total = fig_center = 0
    for p in doc.paragraphs:
        if p._element.findall('.//' + qn('w:drawing')):
            parent_tag = p._element.getparent().tag
            if parent_tag.endswith('}tc'):
                continue  # 表格内图片跳过
            fig_total += 1
            if p.alignment == 1:
                fig_center += 1
    results['fig_center'] = f'PASS({fig_center}/{fig_total})' if fig_total and fig_center == fig_total else f'FAIL({fig_center}/{fig_total})'

    # 3. 图题 10.5pt
    cap_ok = True
    for p in doc.paragraphs:
        t = p.text.strip()
        if re.match(r'^图\d', t) or t.startswith('图 0'):
            sz = p.runs[0].font.size.pt if p.runs and p.runs[0].font.size else None
            if sz != 10.5:
                cap_ok = False
                break
    results['caption_10_5'] = 'PASS' if cap_ok else 'FAIL'

    # 4. 三线表
    tbl_ok = True
    for t in doc.tables:
        tblPr = t._tbl.tblPr
        jc = tblPr.find(qn('w:jc'))
        if jc is None or jc.get(qn('w:val')) != 'center':
            tbl_ok = False
            break
        borders = tblPr.find(qn('w:tblBorders'))
        if borders is not None:
            for side in ['left', 'right', 'insideV']:
                el = borders.find(qn('w:' + side))
                if el is not None and el.get(qn('w:val')) != 'none':
                    tbl_ok = False
                    break
    results['table_3line_center'] = 'PASS' if tbl_ok else 'FAIL'

    # 5. 分页符：只检查可疑的连续分页，不以数量反向要求凑页。
    n_pagebreak = xml.count('w:type="page"')
    consecutive = bool(re.search(r'(?:w:type="page"\s*){2,}', xml))
    if consecutive or n_pagebreak > 12:
        results['pagebreaks'] = f'FAIL(suspicious={n_pagebreak}, consecutive={consecutive})'
    else:
        results['pagebreaks'] = f'PASS({n_pagebreak}; structural breaks only)'

    # 6. 全文黑色(跳过代码段: 代码高亮为用户确认的美化, 豁免黑色检查)
    black = nonblack = 0
    for p in doc.paragraphs:
        if p.style and 'Source Code' in p.style.name:
            continue
        for r in p.runs:
            c = r.font.color.rgb if r.font.color and r.font.color.rgb else None
            if c is None or str(c) == '000000':
                black += 1
            else:
                nonblack += 1
    results['black_text'] = f'PASS(非黑={nonblack})' if nonblack == 0 else f'FAIL(非黑={nonblack})'

    # 7. 代码块 Consolas 9pt
    code_ok = 0
    for p in doc.paragraphs:
        if p.style and 'Source Code' in p.style.name and p.runs:
            r = p.runs[0]
            if r.font.name == 'Consolas' and r.font.size and r.font.size.pt == 9:
                code_ok += 1
    results['code_consolas'] = f'PASS({code_ok})' if code_ok > 0 else 'FAIL(0)'

    return results

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'paper.docx'
    r = check(path)
    print(f'=== Visual Contract: {path} ===')
    all_ok = True
    for k, v in r.items():
        ok = str(v).startswith('PASS')
        all_ok = all_ok and ok
        print(f"  [{'OK' if ok else 'FAIL'}] {k}: {v}")
    print(f'===== Visual Contract 结果: {"PASS" if all_ok else "FAIL"} =====')
    raise SystemExit(0 if all_ok else 1)
