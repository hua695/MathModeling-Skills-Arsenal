#!/usr/bin/env python3
"""scan_language.py — 统一表达质量扫描（合并元话语 + 负向回声）
读取 lint_patterns.yaml，输出候选项（不直接判定 HIGH/BLOCKER，需人工确认）
支持 --filter 只扫描某一类型。
"""
import re, argparse, json
from pathlib import Path
from collections import defaultdict

def load_patterns(f):
    text = Path(f).read_text(encoding='utf-8')
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _parse_simple_yaml(text)

def _parse_simple_yaml(text):
    """解析本 skill 使用的 YAML 子集，支持三层嵌套和连字符 key。"""
    result = {}
    current_key = None
    current_sub = None
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        # 顶层 key
        m = re.match(r'^([a-zA-Z0-9_-]+):\s*(.*)$', line)
        if m and not line.startswith(' '):
            current_key = m.group(1)
            val = m.group(2).strip()
            if val.startswith('[') and val.endswith(']'):
                result[current_key] = re.findall(r'["\']([^"\']+)["\']', val)
            elif val:
                result[current_key] = val
            else:
                result[current_key] = {}
            current_sub = None
            continue
        # 二级 key
        m = re.match(r'^\s+([a-zA-Z0-9_-]+):\s*(.*)$', line)
        if m and current_key and isinstance(result.get(current_key), dict):
            current_sub = m.group(1)
            val = m.group(2).strip()
            if val.startswith('[') and val.endswith(']'):
                result[current_key][current_sub] = re.findall(r'["\']([^"\']+)["\']', val)
            elif val:
                result[current_key][current_sub] = val
            else:
                result[current_key][current_sub] = []
            continue
        # 列表项
        m = re.match(r'^\s+-\s+["\']?(.+?)["\']?\s*$', line)
        if m and current_key:
            target = result[current_key]
            item = m.group(1).strip()
            if isinstance(target, list):
                target.append(item)
            elif isinstance(target, dict) and current_sub:
                if isinstance(target.get(current_sub), list):
                    target[current_sub].append(item)
            continue
    return result

_CODE_ENV_STARTS = [r'\\begin\{minted\}', r'\\begin\{verbatim\}', r'\\begin\{lstlisting\}', r'\\begin\{Verbatim\}']
_CODE_ENV_ENDS = [r'\\end\{minted\}', r'\\end\{verbatim\}', r'\\end\{lstlisting\}', r'\\end\{Verbatim\}']

def _is_code_start(line):
    return any(re.search(p, line) for p in _CODE_ENV_STARTS)

def _is_code_end(line):
    return any(re.search(p, line) for p in _CODE_ENV_ENDS)

def scan_file(content, patterns, fname, filter_type=None):
    findings = []
    lines = content.split('\n')
    is_appendix = '\\appendix' in content or 'appendix' in fname.lower()

    for cat, data in patterns.get('rules', patterns).items():
        if cat in ('storage_rules', 'self_check_logic', 'schema_version', 'description'):
            continue
        if not isinstance(data, dict):
            continue
        rule_type = data.get('type', '')
        if filter_type and rule_type != filter_type:
            continue
        pats = data.get('patterns', [])
        severity_cap = data.get('severity_cap', 'MEDIUM')
        requires_human = data.get('requires_human', True)
        if isinstance(requires_human, str):
            requires_human = requires_human.lower() == 'true'
        judgement = data.get('judgement', [])
        if isinstance(judgement, list):
            judgement_str = '；'.join(judgement)
        else:
            judgement_str = str(judgement) if judgement else ''

        in_code = False
        for i, line in enumerate(lines, 1):
            if _is_code_start(line):
                in_code = True
                continue
            if _is_code_end(line):
                in_code = False
                continue
            if in_code:
                continue
            if line.strip().startswith('%'):
                continue
            for pat in pats:
                flags = re.IGNORECASE if re.match(r'^[a-zA-Z]', pat) else 0
                if re.search(re.escape(pat), line, flags):
                    # 附录中 process_description 的片段引导语可保留
                    if is_appendix and cat == 'process_description' and pat in ('下列片段', '上述片段', '以下片段'):
                        continue
                    findings.append({
                        'line': i,
                        'rule': cat,
                        'type': rule_type,
                        'pattern': pat,
                        'severity_cap': severity_cap,
                        'requires_human': requires_human,
                        'context': line.strip()[:120],
                        'judgement': judgement_str,
                    })
    return findings

def main():
    parser = argparse.ArgumentParser(description='表达质量统一扫描：元话语 + 负向回声（候选项，需人工确认）')
    parser.add_argument('--tex-dir', required=True, help='TeX 源文件目录')
    parser.add_argument('--patterns', required=True, help='lint_patterns.yaml 路径')
    parser.add_argument('--output', default='language_scan_report.md', help='输出报告路径')
    parser.add_argument('--filter', choices=['meta_discourse', 'negative_echo'], default=None, help='只扫描指定类型')
    parser.add_argument('--json', action='store_true', help='同时输出 JSON 格式')
    args = parser.parse_args()

    patterns = load_patterns(args.patterns)
    all_findings = defaultdict(list)
    for f in sorted(Path(args.tex_dir).glob('*.tex')):
        all_findings[f.name] = scan_file(f.read_text(encoding='utf-8'), patterns, f.name, args.filter)

    total = sum(len(v) for v in all_findings.values())
    meta_count = sum(1 for v in all_findings.values() for x in v if x['type'] == 'meta_discourse')
    echo_count = sum(1 for v in all_findings.values() for x in v if x['type'] == 'negative_echo')

    report = ['# 表达质量扫描报告', '']
    report.append(f'- 候选项总数：{total}（元话语 {meta_count}，负向回声 {echo_count}）')
    report.append('- 注意：以下均为候选项，requires_human=true 的必须人工确认后才能定为问题')
    report.append('')
    for fname, finds in sorted(all_findings.items()):
        if not finds:
            continue
        report.append(f'### {fname}（{len(finds)}处）')
        report.append('| 行号 | 类型 | 规则 | 模式 | 严重度上限 | 需人工 | 上下文 |')
        report.append('|---|---|---|---|---|---|---|')
        for x in sorted(finds, key=lambda x: x['line']):
            human = '是' if x['requires_human'] else '否'
            report.append(f'| {x["line"]} | {x["type"]} | {x["rule"]} | `{x["pattern"]}` | {x["severity_cap"]} | {human} | {x["context"]} |')
        report.append('')
    Path(args.output).write_text('\n'.join(report), encoding='utf-8')
    print(f'报告已生成：{args.output}，候选项：{total}（元话语 {meta_count}，负向回声 {echo_count}）')

    if args.json:
        json_path = args.output.rsplit('.', 1)[0] + '.json'
        json.dump({fname: finds for fname, finds in all_findings.items()},
                  open(json_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'JSON 已生成：{json_path}')

if __name__ == '__main__':
    main()
