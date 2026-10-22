#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_docx_consistency.py — docx↔PDF 质量兜底(2026-08-15)
1) 数字一致性: 从 PDF 与 docx 分别提取数值, 比对差异(防转换丢内容/乱码)
2) 公式残留检测: 扫描 docx 文本中的 LaTeX 命令残留(降级公式清单)
用法: python scripts/check_docx_consistency.py <paper.pdf> <paper.docx>
"""
import re
import sys

LATEX_RESIDUE = [
    r'\\frac', r'\\sum', r'\\int', r'\\sqrt', r'\\boxed', r'\\begin\{',
    r'\\end\{', r'\\alpha', r'\\beta', r'\\gamma', r'\\delta', r'\\sigma',
    r'\\mu', r'\\Phi', r'\\phi', r'\\times', r'\\leq', r'\\geq', r'\\in',
    r'\\to', r'\\rightarrow', r'\\left', r'\\right', r'\\mathbb', r'\\mathrm',
    r'\\text', r'\\hat', r'\\bar', r'\\overline', r'\\displaystyle', r'\\frac',
    r'\\dfrac', r'\\bm', r'\\boldsymbol', r'\^\{\}', r'_\{',
]

def extract_numbers(text, min_abs=0.1):
    """提取文本中的数值(≥min_abs, 排除年份/页码/编号)"""
    nums = set()
    for m in re.finditer(r'-?\d+\.\d{2,6}', text):
        v = float(m.group(0))
        if abs(v) >= min_abs:
            nums.add(round(v, 4))
    return nums

def main(pdf_path, docx_path):
    import pymupdf
    import docx as docxlib
    r = {}

    # ---- 1) 文本提取 ----
    pdf_doc = pymupdf.open(pdf_path)
    pdf_text = ''.join(pdf_doc[i].get_text() for i in range(len(pdf_doc)))
    # docx: 用 XML 层提取可见文本(含 OMML 公式 m:t 与表格文本; 只取文本节点, 排除属性)
    import zipfile
    z = zipfile.ZipFile(docx_path)
    xml = z.read('word/document.xml').decode('utf-8')
    docx_text = ' '.join(a or b for a, b in
                         re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>|<m:t(?:\s[^>]*)?>([^<]*)</m:t>', xml))

    # ---- 2) 数字一致性 ----
    pdf_nums = extract_numbers(pdf_text)
    docx_nums = extract_numbers(docx_text)
    # 数字含义受页码/编号干扰, 只报"docx 缺失而 PDF 有"的明显差异
    missing = sorted(pdf_nums - docx_nums)
    extra = sorted(docx_nums - pdf_nums)
    # 过滤: 页码/图号/表号等 1-99 的小整数序列不去重(只比小数)
    missing = [x for x in missing if x >= 1 or x <= -1 or '.' in str(x)]
    r['数字一致性'] = f'PASS(PDF {len(pdf_nums)} / docx {len(docx_nums)} 个数值, 缺失 {len(missing)} 个)' if len(missing) <= 8 else f'FAIL(缺失 {len(missing)} 个: {missing[:8]})'
    if missing:
        r['_缺失数值示例'] = str(missing[:8])

    # ---- 3) 公式残留检测(仅可见文本 w:t/m:t; 属性如 tblCaption 不计) ----
    hits = {}
    for pat in LATEX_RESIDUE:
        n = len(re.findall(pat, docx_text))
        if n:
            hits[pat] = n
    r['公式残留检测'] = f'PASS(可见文本无 LaTeX 命令残留)' if not hits else f'WARN(可见文本残留 {sum(hits.values())} 处: {hits})'

    # ---- 4) 乱码字符检测 ----
    garbled = re.findall(r'[\ufffd\u037e\u2423]', docx_text)
    r['乱码字符'] = f'PASS(无)' if not garbled else f'FAIL({len(garbled)} 处 U+FFFD/U+037E/U+2423)'

    print(f'=== Docx Consistency: {docx_path} vs {pdf_path} ===')
    all_ok = True
    for k, v in r.items():
        ok = str(v).startswith('PASS')
        warn = str(v).startswith('WARN')
        if not k.startswith('_'):
            all_ok = all_ok and (ok or warn)  # WARN 不阻塞; _ 前缀为信息行, 不计门禁
        print(f"  [{'OK' if ok else ('WARN' if warn else 'FAIL')}] {k}: {v}")
    print(f'===== docx 质量兜底: {"PASS" if all_ok else "FAIL"} =====')
    return all_ok

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法: python check_docx_consistency.py <paper.pdf> <paper.docx>')
        sys.exit(1)
    sys.exit(0 if main(sys.argv[1], sys.argv[2]) else 1)
