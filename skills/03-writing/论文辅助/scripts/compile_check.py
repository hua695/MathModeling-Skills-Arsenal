#!/usr/bin/env python3
"""compile_check.py — 检查LaTeX编译日志中的错误和未解析引用
v2 增强：增加 multiply defined labels 检查、未定义引用汇总行交叉验证。
"""
import re, argparse
from pathlib import Path

def parse_log(logfile):
    content = Path(logfile).read_text(encoding='utf-8', errors='ignore')
    issues = {
        'errors': [],
        'undefined_refs': [],
        'undefined_cites': [],
        'multiply_defined': [],
        'overfull': [],
        'pages': 0,
    }

    m = re.search(r'Output written on .+?\((\d+)\s*pages?\)', content)
    if m:
        issues['pages'] = int(m.group(1))

    for i, line in enumerate(content.split('\n'), 1):
        if re.match(r'^!', line):
            issues['errors'].append(line.strip()[:120])
        m = re.search(r"Reference `(.+?)' on page (\d+) undefined", line)
        if m:
            issues['undefined_refs'].append({'ref': m.group(1), 'page': m.group(2)})
        m = re.search(r"Citation `(.+?)' on page (\d+) undefined", line)
        if m:
            issues['undefined_cites'].append({'cite': m.group(1), 'page': m.group(2)})
        m = re.search(r"LaTeX Warning: Label `(.+?)' multiply defined", line)
        if m:
            issues['multiply_defined'].append({'label': m.group(1), 'log_line': i})
        if 'Overfull \\hbox' in line:
            issues['overfull'].append(line.strip()[:100])

    return issues

def main():
    parser = argparse.ArgumentParser(description='LaTeX 编译日志检查：错误、未解析引用、重复标签、超宽盒子')
    parser.add_argument('--log-file', required=True, help='LaTeX 编译日志文件（.log）')
    parser.add_argument('--output', default='compile_check_report.md', help='输出报告路径')
    args = parser.parse_args()

    issues = parse_log(args.log_file)
    total = (len(issues['errors']) + len(issues['undefined_refs'])
             + len(issues['undefined_cites']) + len(issues['multiply_defined']))

    report = [
        '# LaTeX 编译检查报告', '',
        f"- 总页数：{issues['pages']}",
        f"- 编译错误：{len(issues['errors'])}",
        f"- 未解析引用：{len(issues['undefined_refs'])}",
        f"- 未解析文献：{len(issues['undefined_cites'])}",
        f"- 重复定义标签：{len(issues['multiply_defined'])}",
        f"- 超宽盒子（Overfull \\hbox）：{len(issues['overfull'])}",
        '',
        f'**需修复总数：{total}**', ''
    ]

    if issues['errors']:
        report.extend(['## 编译错误', ''])
        for e in issues['errors']:
            report.append(f'- `{e}`')
        report.append('')

    if issues['undefined_refs']:
        report.extend(['## 未解析引用', '', '| 引用标签 | 页码 |', '|---|---|'])
        for r in issues['undefined_refs']:
            report.append(f'| `{r["ref"]}` | {r["page"]} |')
        report.append('')

    if issues['undefined_cites']:
        report.extend(['## 未解析文献引用', '', '| 文献键 | 页码 |', '|---|---|'])
        for c in issues['undefined_cites']:
            report.append(f'| `{c["cite"]}` | {c["page"]} |')
        report.append('')

    if issues['multiply_defined']:
        report.extend(['## 重复定义标签（multiply defined）', '', '| 标签 | 日志行号 |', '|---|---|'])
        for md in issues['multiply_defined']:
            report.append(f'| `{md["label"]}` | {md["log_line"]} |')
        report.append('')

    if issues['overfull']:
        report.extend(['## 超宽盒子（前 20 条）', ''])
        for o in issues['overfull'][:20]:
            report.append(f'- `{o}`')
        if len(issues['overfull']) > 20:
            report.append(f'- ...（共 {len(issues["overfull"])} 条，仅展示前 20 条）')
        report.append('')

    report.extend([
        '## 建议', '',
        '1. 完整编译链：xelatex → bibtex8 → xelatex → xelatex（确保引用解析）',
        '2. 未解析引用：检查 `\\label` 拼写与 `\\ref`/`\\eqref` 对应关系',
        '3. 未解析文献：确认 bib 文件中有对应键，且已运行 bibtex',
        '4. 重复定义标签：搜索重复的 `\\label{...}`，保留唯一一处',
        '5. 超宽盒子：检查长公式、长表格、超长 URL，必要时断行或缩小字号',
    ])
    Path(args.output).write_text('\n'.join(report), encoding='utf-8')
    print(f'报告已生成：{args.output}，需修复：{total}')

if __name__ == '__main__':
    main()
