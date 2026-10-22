# -*- coding: utf-8 -*-
"""
Regression Guard — 论文格式防倒退检测(WR-748 落地)
每次转换后运行, 断言关键格式资产未丢失:
  ① 关键词内容加粗  ② 假设编号 A1-A6 加粗  ③ 正文加粗 run >= 20
  ④ 公式内 LaTeX 函数带反斜杠  ⑤ 单位统一  ⑥ 无内部标记
用法: python regression_guard.py [paper.md] [paper.docx]
"""
import re
import sys
import docx

def check_md(md_path):
    print(f"=== [MD] {md_path} ===")
    text = open(md_path, encoding='utf-8').read()
    issues = []

    # ① 关键词加粗(源稿标记)
    kw_line = [l for l in text.split('\n') if '关键词' in l]
    kw_ok = any('**关键词**' in l and '**' in l.split('**:',1)[1] if '**:' in l else False for l in kw_line)
    print(f"  ① 关键词加粗标记: {'OK' if kw_ok else 'FAIL'}")
    if not kw_ok: issues.append('关键词未加粗')

    # ② 假设编号加粗
    assum = text.split('## 2 模型假设')[1].split('## 3 符号说明')[0]
    a_bold = len(re.findall(r'\*\*A\d\*\*', assum))
    print(f"  ② 假设编号加粗: {a_bold}/6 {'OK' if a_bold>=6 else 'FAIL'}")
    if a_bold < 6: issues.append(f'假设编号加粗不足({a_bold}/6)')

    # ③ 正文加粗
    body = text.split('## 4 模型建立与求解')[1].split('## 7 结论')[0]
    bolds = len(re.findall(r'\*\*([^*]{2,30})\*\*', body))
    print(f"  ③ 正文加粗: {bolds} 处 {'OK' if bolds>=20 else 'FAIL'}")
    if bolds < 20: issues.append(f'正文加粗不足({bolds})')

    # ④ LaTeX 函数反斜杠(先剔除代码块内容, 且排除跨行卷进表格/正文的段: 含 | 或超长即非公式)
    text_no_code = re.sub(r'```.*?```', '', text, flags=re.S)
    formulas = [f for f in re.findall(r'\$[^$]+\$', text_no_code)
                if '|' not in f and len(f) < 300]
    funcs = ['sin','cos','tan','arctan','log','ln','exp']
    bad = []
    for f in formulas:
        for func in funcs:
            if re.search(rf'(?<![\\a-zA-Z]){func}(?![a-zA-Z])', f):
                bad.append((func, f[:50]))
    print(f"  ④ 公式缺反斜杠: {len(bad)} {'OK' if len(bad)==0 else 'FAIL ' + str(bad[:3])}")
    if bad: issues.append(f'LaTeX 缺反斜杠 {len(bad)} 处')

    # ⑤ 单位统一
    hl = len(re.findall(r'海里', text))
    nm = len(re.findall(r'\bNM\b', text))
    print(f"  ⑤ 单位: 海里={hl} NM={nm} {'OK' if hl==0 or nm==0 else 'WARN(混用)'}")
    if hl > 0 and nm > 0: issues.append(f'单位混用(海里{hl}/NM{nm})')

    # ⑥ 内部标记
    internal = len(re.findall(r'FD-\d+|SD-\d+|ST-\d+|DM-\d+', text))
    print(f"  ⑥ 内部标记: {internal} {'OK' if internal==0 else 'FAIL'}")
    if internal: issues.append(f'内部标记残留 {internal} 处')

    # ⑦ 摘要自我评价
    m = re.search(r'\*\*摘要\*\*(.*?)\*\*关键词', text, re.S)
    if m:
        abs_text = m.group(1)
        self_eval = re.findall(r'(模型[^,。]*清晰|结果[^,。]*较好|具有[^,。]*参考价值|效果[^,。]*良好)', abs_text)
        print(f"  ⑦ 摘要自我评价: {len(self_eval)} {'OK' if len(self_eval)==0 else 'FAIL ' + str(self_eval[:2])}")
        if self_eval: issues.append(f'摘要自我评价 {self_eval[:2]}')

    print(f"  => MD 问题数: {len(issues)}")
    return issues

def check_docx(docx_path):
    print(f"\n=== [DOCX] {docx_path} ===")
    doc = docx.Document(docx_path)
    issues = []

    # 关键词段加粗
    kw_para = None
    for p in doc.paragraphs:
        if p.text.strip().startswith('关键词'):
            kw_para = p
            break
    kw_bold = False
    if kw_para:
        # 只统计有实际文字内容的词条 run(排除 ':'、空格等分隔符 run, 它们可能 bold=None)
        content_runs = [r for r in kw_para.runs
                        if r.text.strip() and r.text.strip() not in (':', '：')
                        and '关键词' not in r.text]
        if content_runs:
            kw_bold = all(r.font.bold for r in content_runs)
    print(f"  ① 关键词内容加粗: {'OK' if kw_bold else 'FAIL'}")
    if not kw_bold: issues.append('关键词内容未加粗')

    # 假设编号加粗
    a_bold = sum(1 for p in doc.paragraphs if re.match(r'^A[1-6]\s', p.text.strip())
                 and p.runs and p.runs[0].font.bold)
    print(f"  ② 假设编号加粗: {a_bold}/6 {'OK' if a_bold>=6 else 'FAIL'}")
    if a_bold < 6: issues.append(f'假设编号加粗不足({a_bold}/6)')

    # 正文加粗
    bold_cnt = 0
    for p in doc.paragraphs:
        if p.style and 'Heading' in p.style.name:
            continue
        if p.text.strip().startswith('关键词'):
            continue
        for r in p.runs:
            if r.font.bold and r.text.strip():
                bold_cnt += 1
    print(f"  ③ 正文加粗 run: {bold_cnt} {'OK' if bold_cnt>=20 else 'FAIL'}")
    if bold_cnt < 20: issues.append(f'正文加粗不足({bold_cnt})')

    print(f"  => DOCX 问题数: {len(issues)}")
    return issues

if __name__ == '__main__':
    md_path = sys.argv[1] if len(sys.argv) > 1 else 'paper.md'
    docx_path = sys.argv[2] if len(sys.argv) > 2 else 'paper.docx'
    md_issues = check_md(md_path)
    dx_issues = check_docx(docx_path)
    total = len(md_issues) + len(dx_issues)
    print(f"\n===== Regression Guard 结果: {'PASS' if total==0 else f'{total} 个问题'} =====")
    for i in md_issues: print(f"  [MD] {i}")
    for i in dx_issues: print(f"  [DOCX] {i}")
    sys.exit(0 if total == 0 else 1)
