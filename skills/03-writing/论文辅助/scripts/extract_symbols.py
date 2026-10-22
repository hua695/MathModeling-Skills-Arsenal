#!/usr/bin/env python3
"""extract_symbols.py — 从TeX源文件中提取数学符号，与符号表对比
v2 修复：符号表也解析为 token 粒度，分级输出（未定义 / token级匹配需确认 / 完整匹配），避免假阳性刷屏。
"""
import re, argparse
from pathlib import Path

# LaTeX 结构命令与运算符（不是变量，跳过）
_SKIP_CMDS = {
    'begin','end','label','ref','eqref','text','mathrm','mathbf','mathcal','mathbb',
    'left','right','frac','sqrt','sum','int','lim','max','min','infty','partial',
    'nabla','forall','exists','cdot','times','quad','qquad',
    'approx','le','ge','neq','pm','mp','ast','star',
    'overline','underline','hat','tilde','bar','vec',
    'langle','rangle','lbrace','rbrace','lbrack','rbrack',
    'sim','simeq','cong','equiv','propto','in','notin',
    'subset','supset','subseteq','supseteq','subsetneq','supsetneq',
    'cap','cup','emptyset','dots','cdots','ldots','vdots','ddots',
    'circ','bullet','angle','perp','parallel',
    'wedge','vee','neg','land','lor','therefore','because',
    'to','mapsto','uparrow','downarrow','leftarrow','rightarrow',
    'leftrightarrow','Rightarrow','Leftarrow','Leftrightarrow',
    'log','ln','exp','sin','cos','tan','arg','inf','sup',
    'det','dim','ker','mod','pmod','bmod',
}

def normalize_math(math):
    """规范化数学表达式：去多余空白，用于完整匹配"""
    return re.sub(r'\s+', '', math)

def extract_from_math(math):
    """从单个数学片段中提取 token 集合（命令 + 单字母变量）"""
    symbols = set()
    for cmd in re.findall(r'\\([a-zA-Z]+)', math):
        if cmd not in _SKIP_CMDS:
            symbols.add(f'\\{cmd}')
    for letter in re.findall(r'(?<![a-zA-Z])([a-zA-Z])(?![a-zA-Z])', math):
        if letter not in ('d', 'e', 'i', 'j'):
            symbols.add(letter)
    return symbols

def extract_math_fragments(tex_content):
    """提取所有数学片段，返回 [(原始片段, 规范化片段, token集合)]"""
    fragments = []
    for pattern in [
        r'\$([^$]+)\$',
        r'\\\[(.+?)\\\]',
        r'\\begin\{equation\*?\}(.+?)\\end\{equation\*?\}',
    ]:
        for math in re.findall(pattern, tex_content, re.DOTALL):
            fragments.append((math.strip(), normalize_math(math), extract_from_math(math)))
    return fragments

def load_symbol_table(symbol_file):
    """加载符号表，返回 (完整表达式集合, token集合)"""
    content = Path(symbol_file).read_text(encoding='utf-8')
    full_exprs = set()
    all_tokens = set()
    for math in re.findall(r'\$([^$]+)\$', content):
        full_exprs.add(normalize_math(math))
        all_tokens.update(extract_from_math(math))
    for math in re.findall(r'\\begin\{equation\*?\}(.+?)\\end\{equation\*?\}', content, re.DOTALL):
        full_exprs.add(normalize_math(math))
        all_tokens.update(extract_from_math(math))
    return full_exprs, all_tokens

def main():
    parser = argparse.ArgumentParser(description='符号完整性检查：对比正文数学符号与符号表')
    parser.add_argument('--tex-dir', required=True, help='TeX 源文件目录')
    parser.add_argument('--symbol-file', required=True, help='符号表文件')
    parser.add_argument('--output', default='symbol_check_report.md', help='输出报告路径')
    args = parser.parse_args()

    full_exprs, table_tokens = load_symbol_table(args.symbol_file)

    undefined = []    # HIGH: 完整表达式不在符号表，且有 token 不在符号表 token 集合
    token_only = []   # MEDIUM: 完整表达式不在符号表，但所有 token 都在（复合符号变体，需人工确认）
    ok_count = 0
    total = 0

    seen_undef = set()
    seen_token = set()

    for f in sorted(Path(args.tex_dir).glob('*.tex')):
        content = f.read_text(encoding='utf-8')
        for orig, norm, tokens in extract_math_fragments(content):
            total += 1
            if norm in full_exprs:
                ok_count += 1
                continue
            missing = tokens - table_tokens
            if missing:
                key = (norm, tuple(sorted(missing)))
                if key not in seen_undef:
                    seen_undef.add(key)
                    undefined.append((f.name, orig, sorted(missing)))
            else:
                if norm not in seen_token:
                    seen_token.add(norm)
                    token_only.append((f.name, orig))

    report = [
        '# 符号完整性检查报告', '',
        f'- 符号表完整表达式数：{len(full_exprs)}',
        f'- 符号表 token 数：{len(table_tokens)}',
        f'- 正文数学片段总数：{total}',
        f'- 完整匹配（OK）：{ok_count}',
        f'- 未定义（HIGH）：{len(undefined)}',
        f'- token 级匹配需确认（MEDIUM）：{len(token_only)}',
        '',
        '## 未定义符号（HIGH）', '',
        '> 完整表达式不在符号表，且包含符号表中没有的 token。',
        ''
    ]
    if undefined:
        report.append('| 文件 | 正文片段 | 缺失 token |')
        report.append('|---|---|---|')
        for fname, orig, missing in undefined:
            display = orig if len(orig) <= 80 else orig[:77] + '...'
            report.append(f'| {fname} | `${display}` | {", ".join(f"`{m}`" for m in missing)} |')
    else:
        report.append('无。')

    report.extend([
        '', '## token 级匹配需确认（MEDIUM）', '',
        '> 完整表达式不在符号表，但所有组成 token 都在符号表中（可能是复合符号的变体或下标组合，需人工确认是否需要补登）。',
        ''
    ])
    if token_only:
        report.append('| 文件 | 正文片段 |')
        report.append('|---|---|')
        for fname, orig in token_only:
            display = orig if len(orig) <= 100 else orig[:97] + '...'
            report.append(f'| {fname} | `${display}` |')
    else:
        report.append('无。')

    Path(args.output).write_text('\n'.join(report), encoding='utf-8')
    print(f'报告已生成：{args.output}')
    print(f'  未定义(HIGH)：{len(undefined)}，token级需确认(MEDIUM)：{len(token_only)}，完整匹配：{ok_count}')

if __name__ == '__main__':
    main()
