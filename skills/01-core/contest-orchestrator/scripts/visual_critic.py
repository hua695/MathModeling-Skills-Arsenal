#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
visual_critic.py — 论文视觉质检（v3.6.14 扩展：支持 PDF/txt/docx）

PDF/txt：文本检查（乱码字符 / LaTeX 残留 / 错别字 / 首页参赛队抬头 / 内部流程词）
DOCX  ：结构检查（分页符 / 表格三线表 / 正文加粗数 / 摘要分段 / 关键词加粗 / 抬头 / 内部流程词）

用法:
  python scripts/visual_critic.py <论文.pdf 或 提取的.txt 或 论文.docx>
"""
import re
import sys
import os

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass

# 乱码字符块（LaTeX 中文编码失败常见产物）
GARBLED = re.compile(r'[囹囵囫図圄圉囿圂圅圇圊圌団図圎圐園圔圕圗圙圛圝圞�□■▯▢]')
# LaTeX 残留
LATEX_RESIDUE = re.compile(r'\\[a-zA-Z]+\b|[\{\}]\\|\\text|\\frac|f\^|kmathrm|mathbb|mathtt|vec|betweenho')
# 常见错别字
# Keep the list limited to observed misspellings.  “参数化” is a valid
# mathematical-modeling term and must not be treated as a typo.
TYPO = re.compile(r'可题|王要付号|附 录|主 要')
# 参赛队抬头
TEAM_HEADER = re.compile(r'参赛队|参赛编号|数学建模.*(?:队|年)|参赛学校')
# 内部流程词
INTERNAL = re.compile(r'经验库|呈现先验|skills|Agent|提示词|检索系统')
# 不得进入正式论文的内部交付/占位文字。与普通“内部流程词”不同，
# 这些命中会直接阻断交付，因为它们通常来自模板占位符或审计索引页。
FORBIDDEN_ARTIFACT = re.compile(r'参考文献索引|交付索引|交付前核对清单|数学建模竞赛论文')


def check_text(text):
    """文本检查（PDF提取/txt）：乱码/LaTeX残留/错别字/抬头/内部流程词"""
    issues = []
    for m in GARBLED.finditer(text):
        s = max(0, m.start() - 20)
        ctx = text[s:m.end() + 20].replace('\n', ' ')
        issues.append(('P0', '乱码字符', ctx))
    for m in LATEX_RESIDUE.finditer(text):
        s = max(0, m.start() - 15)
        ctx = text[s:m.end() + 15].replace('\n', ' ')
        issues.append(('P0', 'LaTeX残留', ctx))
    for m in TYPO.finditer(text):
        s = max(0, m.start() - 15)
        ctx = text[s:m.end() + 15].replace('\n', ' ')
        issues.append(('P0', '错别字', ctx))
    head = text[:1500]
    for m in TEAM_HEADER.finditer(head):
        s = max(0, m.start() - 15)
        ctx = head[s:m.end() + 15].replace('\n', ' ')
        issues.append(('P0', '首页参赛队抬头', ctx))
    for m in INTERNAL.finditer(text):
        s = max(0, m.start() - 15)
        ctx = text[s:m.end() + 15].replace('\n', ' ')
        issues.append(('P1', '内部流程词', ctx))
    for m in FORBIDDEN_ARTIFACT.finditer(text):
        s = max(0, m.start() - 20)
        ctx = text[s:m.end() + 20].replace('\n', ' ')
        issues.append(('P0', '论文内部交付文字/占位字段', ctx))
    seen = set()
    uniq = []
    for sev, cat, ctx in issues:
        key = (cat, ctx[:30])
        if key not in seen:
            seen.add(key)
            uniq.append((sev, cat, ctx))
    return uniq


def _page_breaks(doc):
    """统计 docx 分页符数（run br type=page + 段落 page_break_before）"""
    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    n = 0
    for p in doc.paragraphs:
        if p.paragraph_format.page_break_before:
            n += 1
        for r in p.runs:
            for br in r._r.findall(W + 'br'):
                if br.get(W + 'type') == 'page':
                    n += 1
    # 表格内段落的分页符
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        for br in r._r.findall(W + 'br'):
                            if br.get(W + 'type') == 'page':
                                n += 1
    return n


def _tables_are_3line(doc):
    """检查所有表格是否三线表（无竖线 insideV / 无内部横线 insideH / 无左右边框）"""
    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    bad = []
    for i, tbl in enumerate(doc.tables):
        xml = tbl._tbl.xml
        has_v = bool(re.search(r'insideV', xml) or re.search(r'w:(left|right)[^/]*w:val="(single|thickThinSmallGap|double)"', xml))
        has_inside_h = bool(re.search(r'insideH[^>]*w:val="(?!none)[^"]*"', xml))
        if has_v or has_inside_h:
            bad.append(f'表{i+1}（含竖线/内横线，非三线表）')
    return bad


def _bold_count(doc):
    """统计正文加粗 run 数（排除表格/标题判断简化：数全文 bold run）"""
    n = 0
    for p in doc.paragraphs:
        for r in p.runs:
            if r.text.strip() and r.bold:
                n += 1
    return n


def _abstract_info(doc):
    """摘要：字数 + 分段数 + 关键词加粗 + 摘要-关键词空行"""
    raw = doc.paragraphs
    abs_idx = kw_idx = None
    for i, p in enumerate(raw):
        t = re.sub(r'\s+', '', p.text)
        if t == '摘要' and abs_idx is None:
            abs_idx = i
        if t.startswith('关键词') and kw_idx is None:
            kw_idx = i
    if abs_idx is None or kw_idx is None:
        return None
    between = [p for p in raw[abs_idx + 1:kw_idx] if p.text.strip()]
    abs_len = len(re.sub(r'\s+', '', ''.join(p.text for p in between)))
    n_seg = len(between)
    kw_bold = any(r.bold for r in raw[kw_idx].runs if r.text.strip())
    blank = (kw_idx > abs_idx + 1 and raw[kw_idx - 1].text.strip() == '')
    return {'abs_len': abs_len, 'n_seg': n_seg, 'kw_bold': kw_bold, 'blank': blank}


def check_docx(doc, source=''):
    """docx 结构检查：分页符/表格三线表/加粗/摘要分段/关键词加粗/抬头/内部流程词"""
    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    full = '\n'.join(p.text for p in doc.paragraphs)
    issues = []
    # 1. 分页符：分页数量不是质量目标，禁止因数量不足诱导强制分页。
    # 仅阻断连续分页或异常多分页；语义上的章节分页由模板自行决定。
    pb = _page_breaks(doc)
    raw_xml = doc._element.getroottree().getroot().xml
    consecutive = bool(re.search(r'(?:w:type="page"\s*){2,}', raw_xml))
    if consecutive or pb > 12:
        issues.append(('P0', f'分页符结构可疑（{pb} 个，consecutive={consecutive}）', ''))
    else:
        issues.append(('OK', f'分页符 {pb} 个（仅作信息，不以数量凑页）', ''))
    # 2. 表格三线表
    bad_tbl = _tables_are_3line(doc)
    if bad_tbl:
        issues.append(('P0', '表格非三线表', '；'.join(bad_tbl)))
    else:
        issues.append(('OK', f'表格 {len(doc.tables)} 个均为三线表', ''))
    # 3. 正文加粗数（≥20）
    bc = _bold_count(doc)
    if bc < 20:
        issues.append(('P1', f'正文加粗 {bc} 处（应≥20）', ''))
    else:
        issues.append(('OK', f'正文加粗 {bc} 处', ''))
    # 4. 摘要
    ai = _abstract_info(doc)
    if ai:
        if not (550 <= ai['abs_len'] <= 800):
            issues.append(('P1', f"摘要 {ai['abs_len']} 字（应550-800）", ''))
        if ai['n_seg'] <= 1:
            issues.append(('P0', f"摘要 {ai['n_seg']} 段未分段（应3-6段逐问）", ''))
        if not ai['kw_bold']:
            issues.append(('P0', '关键词未加粗', ''))
        if not ai['blank']:
            issues.append(('P1', '摘要与关键词之间无空行', ''))
    # 5. 抬头/内部流程词
    for m in TEAM_HEADER.finditer(full[:1500]):
        issues.append(('P0', '首页参赛队抬头', ''))
    for m in INTERNAL.finditer(full):
        issues.append(('P1', '内部流程词', full[max(0, m.start() - 15):m.end() + 15].replace('\n', ' ')))
    return issues


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = sys.argv[1]
    ext = src.lower().rsplit('.', 1)[-1]
    if ext == 'pdf':
        import pymupdf
        doc = pymupdf.open(src)
        # 只检查“参考文献”标题之前的正文页；附录源代码不参与 LaTeX 残留扫描。
        pages = []
        for index, page in enumerate(doc):
            page_text = page.get_text()
            if '参考文献' in page_text:
                before = page_text.split('参考文献', 1)[0]
                pages.append(before)
                break
            # 某些中文字体的 PDF 文本层无法提取“参考文献/附录”汉字；
            # 代码附录通常以 code/、solve_and_plot.py 或 results/qN 开头，
            # 从此页起停止正文 LaTeX 残留扫描，避免把源代码误报为排版残留。
            if index > 0 and re.search(r"(?:code/|solve_and_plot\.py|results/q\d_)", page_text):
                break
            pages.append(page_text)
        text = ''.join(pages)
        issues = check_text(text)
    elif ext == 'docx':
        import docx
        d = docx.Document(src)
        issues = check_docx(d)
    else:  # txt
        text = open(src, encoding='utf-8', errors='ignore').read()
        issues = check_text(text)

    if not issues:
        print(f'[PASS] 视觉质检通过（{src}）')
        return 0
    print(f'[WARN] 视觉质检（{ext.upper()}）发现 {len(issues)} 项：')
    p0 = 0
    for sev, cat, ctx in issues:
        if sev == 'OK':
            print(f'  [OK] {cat} {ctx}')
        else:
            print(f'  [{sev}] {cat} {("..." + ctx + "...") if ctx else ""}')
            if sev == 'P0':
                p0 += 1
    print(f'\nP0（必须修）: {p0} 处 → 门禁 FAIL' if p0 else '\n无 P0（仅 P1 建议）')
    return 0 if p0 == 0 else 2


if __name__ == '__main__':
    sys.exit(main())
