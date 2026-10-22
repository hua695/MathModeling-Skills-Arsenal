#!/usr/bin/env python3
"""verify_results.py — 验证论文中的数字与结果文件一致
v2 修复：单位 pattern 泛化，内置通用单位 + 支持 --extra-units 追加自定义单位；跳过代码块。
"""
import re, json, argparse
from pathlib import Path

# 内置通用单位 pattern：(regex, type_name)
# 注意：顺序敏感，更具体的 pattern 放前面
DEFAULT_UNIT_PATTERNS = [
    (r'(\d+\.?\d*)\s*元/件', 'profit_per_unit'),
    (r'(\d+\.?\d*)\s*kg/h', 'flow_rate'),
    (r'(\d+\.?\d*)\s*kg·h⁻¹', 'flow_rate'),
    (r'(\d+\.?\d*)\s*吨/天', 'flow_rate'),
    (r'(\d+\.?\d*)\s*万元', 'money'),
    (r'(\d+\.?\d*)\s*亿元', 'money'),
    (r'(\d+\.?\d*)\s*元', 'money'),
    (r'(\d+\.?\d*)\s*件', 'sample_count'),
    (r'(\d{1,3}(?:,\d{3})*)\s*个', 'count'),
    (r'(\d+\.?\d*)\s*%', 'percent'),
    (r'(\d+\.?\d*)\s*(?:kg|千克)', 'mass'),
    (r'(\d+\.?\d*)\s*(?:g|克)', 'mass'),
    (r'(\d+\.?\d*)\s*(?:mg|毫克)', 'mass'),
    (r'(\d+\.?\d*)\s*(?:t|吨)', 'mass'),
    (r'(\d+\.?\d*)\s*(?:km|千米)', 'length'),
    (r'(\d+\.?\d*)\s*(?:m|米)', 'length'),
    (r'(\d+\.?\d*)\s*(?:cm|厘米)', 'length'),
    (r'(\d+\.?\d*)\s*(?:mm|毫米)', 'length'),
    (r'(\d+\.?\d*)\s*(?:h|小时)', 'time'),
    (r'(\d+\.?\d*)\s*(?:min|分钟)', 'time'),
    (r'(\d+\.?\d*)\s*(?:s|秒)', 'time'),
    (r'(\d+\.?\d*)\s*(?:天|日)', 'time'),
    (r'(\d+\.?\d*)\s*(?:次|倍|轮|代)', 'iteration'),
]

def load_extra_units(extra_file):
    """从 JSON 文件加载额外单位 pattern：[{"type": "xxx", "pattern": "regex"}, ...]"""
    if not extra_file:
        return []
    data = json.loads(Path(extra_file).read_text(encoding='utf-8'))
    return [(item['pattern'], item['type']) for item in data]

def extract_numbers(content, patterns):
    nums = []
    in_code = False
    for i, line in enumerate(content.split('\n'), 1):
        if '\\begin{minted}' in line or '\\begin{verbatim}' in line or '\\begin{lstlisting}' in line:
            in_code = True
            continue
        if '\\end{minted}' in line or '\\end{verbatim}' in line or '\\end{lstlisting}' in line:
            in_code = False
            continue
        if in_code or line.strip().startswith('%'):
            continue
        for pat, typ in patterns:
            for m in re.finditer(pat, line):
                try:
                    val = float(m.group(1).replace(',', ''))
                except ValueError:
                    continue
                nums.append({'line': i, 'type': typ, 'value': val, 'ctx': line.strip()[:100]})
    return nums

def search_value(data, target, tolerance=0.01):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (int, float)) and abs(v - target) <= tolerance * max(1, abs(target)):
                return f'{k}={v}'
            r = search_value(v, target, tolerance)
            if r:
                return r
    elif isinstance(data, list):
        for item in data:
            r = search_value(item, target, tolerance)
            if r:
                return r
    return None

def main():
    parser = argparse.ArgumentParser(description='模型证据验证：对比论文数字与结果 JSON 文件')
    parser.add_argument('--tex-dir', required=True, help='TeX 源文件目录')
    parser.add_argument('--results-dir', required=True, help='结果 JSON 文件目录')
    parser.add_argument('--extra-units', default=None, help='额外单位 pattern JSON 文件路径（[{"type":"...","pattern":"regex"},...]）')
    parser.add_argument('--output', default='result_verification_report.md', help='输出报告路径')
    args = parser.parse_args()

    patterns = DEFAULT_UNIT_PATTERNS + load_extra_units(args.extra_units)

    results = {}
    for f in Path(args.results_dir).glob('*.json'):
        try:
            results[f.name] = json.loads(f.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    all_nums = []
    for f in sorted(Path(args.tex_dir).glob('*.tex')):
        all_nums.extend(extract_numbers(f.read_text(encoding='utf-8'), patterns))

    verified, unverified = [], []
    for n in all_nums:
        found = False
        for fname, data in results.items():
            if search_value(data, n['value']):
                n['source'] = fname
                verified.append(n)
                found = True
                break
        if not found:
            unverified.append(n)

    report = [
        '# 模型证据验证报告', '',
        f'- 提取数字：{len(all_nums)}',
        f'- 已验证：{len(verified)}',
        f'- 未验证：{len(unverified)}',
        f'- 使用单位 pattern 数：{len(patterns)}',
        '',
        '## 未验证数字', ''
    ]
    if unverified:
        report.append('| 行号 | 类型 | 数值 | 上下文 |')
        report.append('|---|---|---|---|')
        for n in unverified:
            report.append(f'| {n["line"]} | {n["type"]} | {n["value"]} | {n["ctx"]} |')
    else:
        report.append('无。')

    report.extend(['', '## 已验证数字（抽样）', ''])
    if verified:
        report.append('| 行号 | 类型 | 数值 | 来源文件 |')
        report.append('|---|---|---|---|')
        for n in verified[:30]:
            report.append(f'| {n["line"]} | {n["type"]} | {n["value"]} | {n.get("source","?")} |')
        if len(verified) > 30:
            report.append(f'| ... | ... | ... | （共 {len(verified)} 条，仅展示前 30 条） |')
    else:
        report.append('无。')

    Path(args.output).write_text('\n'.join(report), encoding='utf-8')
    print(f'报告已生成：{args.output}，已验证：{len(verified)}，未验证：{len(unverified)}')

if __name__ == '__main__':
    main()
