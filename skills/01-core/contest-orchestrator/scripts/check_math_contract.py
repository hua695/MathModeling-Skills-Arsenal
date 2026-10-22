#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/check_math_contract.py — Math Structure Compliance 断言（数学感最低保障）

检查存在性而非替代人工质量评审：硬门禁核验编号公式、符号闭环和推导链；理论性质与极限/退化验证作为提示项。

用法:
    python scripts/check_math_contract.py <paper.md> [--problem-type 优化|机理|预测]
    python scripts/check_math_contract.py <paper.md> --json   # 机器可读输出

退出码:
    0 = 全部硬门禁通过
    1 = 硬门禁失败（block 项缺）
    2 = 用法错误
"""
import json
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ---- 硬门禁参数（阈值“必要但不充分”，防凑数）----
FORMULA_MIN_PER_QUESTION = 3   # 每问至少 3 条编号公式 (N)
SYMBOL_TABLE_MIN = 5           # 符号说明表至少 5 个符号（过少=没做符号化）
DERIVATION_CHAIN_MIN = 1       # 至少 1 处跨公式引用（由式(X)得式(Y)）

# 硬门禁正则
# 编号公式：形如 (1) (12) —— 行内或独立行，排除纯引用 "式(1)" 本身
_RE_FORMULA = re.compile(r'(?<![式由用从])\$?\((\d{1,2})\)\$?|\\tag\{(\d{1,2})\}')
# 跨公式引用（推导链）：由式(1)得/代入式(2)/联立式(3)与式(4) 等（允许"式 (1)"带空格）
_RE_CHAIN = re.compile(r'(?:由|代[入]|联立|将|把|利用|结合)[^。；\n]{0,40}式\s*\(\d{1,2}\)[^。；\n]{0,40}(?:式\s*\(\d{1,2}\)|得|可[得求]|即)')
# 符号说明表标题
_RE_SYMBOL_TABLE = re.compile(r'符号(?:说明|表|定义)|主要符号|变量说明')
# 理论性质小节（软）
_RE_THEORY = re.compile(r'(复杂度|收敛性|可行性|误差界|稳定性|可辨识性|最优性)')
# 极限/退化验证（软）
_RE_LIMIT = re.compile(r'(→\s*0|极限|退化|对称性|边界情形|平坦|无穷|趋近|退化情形|一致)')


def _strip_code(text):
    """去掉代码块（附录核心代码等），避免公式/符号统计被代码污染"""
    return re.sub(r'```.*?```', '', text, flags=re.S)


def _numbered_formulas(text):
    """提取编号公式号列表（去重、排序）"""
    nums = set()
    for m in _RE_FORMULA.finditer(text):
        n = m.group(1) or m.group(2)
        if n:
            nums.add(int(n))
    return sorted(nums)


def check_math_contract(paper_text, problem_type=None, n_questions=None):
    """返回结构化结果：硬门禁 + 软提示。不抛异常，失败项在 results['blocked']。"""
    text = _strip_code(paper_text)
    # 默认按题号 1~4 估（摘要/结论也可能带公式，这里只要求主体有）
    if n_questions is None:
        n_questions = 4
    formula_min = max(1, FORMULA_MIN_PER_QUESTION * n_questions) if n_questions else FORMULA_MIN_PER_QUESTION

    formulas = _numbered_formulas(text)
    n_formulas = len(formulas)
    # 连续性检查：1..n 是否完整（允许 1 个跳号容错，评审：编号断裂是硬伤）
    continuous = True
    if formulas:
        expected = list(range(1, formulas[-1] + 1))
        missing = [x for x in expected if x not in formulas]
        continuous = len(missing) <= 1  # 容错 1 个（可能公式在图片/附录）

    chains = _RE_CHAIN.findall(text)
    n_chains = len(chains)

    has_symbol_table = bool(_RE_SYMBOL_TABLE.search(text))
    # 符号闭环粗查：符号说明表出现 → 视为做了符号化（精确差集需 NLP，见评审待办）
    symbol_table_ok = has_symbol_table

    has_theory = bool(_RE_THEORY.search(text))
    has_limit = bool(_RE_LIMIT.search(text))

    # ---- 硬门禁（block）----
    blocks = []
    if n_formulas < formula_min:
        blocks.append({
            'id': 'MSG-001', 'name': '编号公式存在性',
            'detail': f'编号公式 {n_formulas} 条 < 阈值 {formula_min}（每问 ≥{FORMULA_MIN_PER_QUESTION}）',
        })
    elif not continuous:
        blocks.append({
            'id': 'MSG-001', 'name': '编号公式存在性',
            'detail': f'公式编号不连续，缺号：{missing}',
        })
    if not symbol_table_ok:
        blocks.append({
            'id': 'MSG-002', 'name': '符号表闭环',
            'detail': '未检测到符号说明表（标题含"符号说明/符号表/变量说明"）',
        })
    if n_chains < DERIVATION_CHAIN_MIN:
        blocks.append({
            'id': 'MSG-003', 'name': '推导链存在性',
            'detail': f'跨公式引用 {n_chains} 处 < 阈值 {DERIVATION_CHAIN_MIN}（无"由式(X)得式(Y)"式推导）',
        })

    # ---- 软提示（warn，不 block）----
    warns = []
    if not has_theory:
        warns.append({
            'id': 'MSG-004', 'name': '理论性质小节',
            'detail': '未检测到复杂度/收敛性/可行性/误差界/稳定性等理论性质表述（部分简单题可豁免）',
        })
    if not has_limit:
        warns.append({
            'id': 'MSG-005', 'name': '极限/退化验证',
            'detail': '未检测到退化情形验证（→0/极限/对称/边界/平坦等）（部分题无自然退化情形可豁免）',
        })

    passed = len(blocks) == 0
    return {
        'passed': passed,
        'blocked': blocks,
        'warnings': warns,
        'measures': {
            'n_formulas': n_formulas,
            'formula_ids': formulas,
            'formula_continuous': continuous,
            'n_chains': n_chains,
            'has_symbol_table': symbol_table_ok,
            'has_theory': has_theory,
            'has_limit': has_limit,
        },
    }


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return 2
    path = sys.argv[1]
    as_json = '--json' in sys.argv[2:]
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
    except OSError as e:
        print(f'读取失败: {e}', file=sys.stderr)
        return 2

    problem_type = None
    if '--problem-type' in sys.argv:
        i = sys.argv.index('--problem-type')
        if i + 1 < len(sys.argv):
            problem_type = sys.argv[i + 1]

    result = check_math_contract(text, problem_type=problem_type)
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        status = 'PASS' if result['passed'] else 'BLOCK'
        print(f'Math Structure Compliance: {status}')
        for b in result['blocked']:
            print(f"  [BLOCK] {b['id']} {b['name']}: {b['detail']}")
        for w in result['warnings']:
            print(f"  [warn]  {w['id']} {w['name']}: {w['detail']}")
        m = result['measures']
        print(f'  公式 {m["n_formulas"]} 条 / 连续 {m["formula_continuous"]} / '
              f'推导链 {m["n_chains"]} / 符号表 {m["has_symbol_table"]} / '
              f'理论 {m["has_theory"]} / 极限 {m["has_limit"]}')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
