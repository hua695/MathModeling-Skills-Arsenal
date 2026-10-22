#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
coverage_matrix.py — WR 库覆盖矩阵（v3.6.14 GPT/Kimi 共识：覆盖决定停止，不是条数）

统计 section × context_type × competition_family 的 pattern/trap 数，标出空白/不足单元格。

用法:
  python scripts/coverage_matrix.py            # 活跃库矩阵（排除华为杯冷存）
  python scripts/coverage_matrix.py --all      # 含华为杯
"""
import os
import re
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(REPO, 'memory', 'writing_database.md')

SECTIONS = ['摘要', '引言', '问题重述', '模型假设', '符号说明', '模型建立', '求解',
            '结果分析', '灵敏度分析', '问题改进', '模型评价', '结论', '附录']
CTYPES = ['优化', '预测', '评价', '机理', '图模型', '数据', '通用']
FAMILIES = ['guosai', 'huashu', 'huaweibei', '(无)']


def load():
    entries = []
    txt = open(DB, encoding='utf-8').read()
    for b in re.findall(r'```yaml\n(.*?)\n```', txt, re.S):
        d = {}
        for line in b.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                d[k.strip()] = v.strip()
        if d.get('wr_id'):
            entries.append(d)
    return entries


def main():
    all_fam = '--all' in sys.argv
    entries = load()
    if not all_fam:
        entries = [e for e in entries if e.get('competition_family') != 'huaweibei']
    # section × context_type
    grid = Counter()
    traps = Counter()
    for e in entries:
        s = e.get('section', '?')
        c = e.get('context_type', '?')
        grid[(s, c)] += 1
        if e.get('kind') == 'trap':
            traps[(s, c)] += 1
    # 输出矩阵
    print(f'覆盖矩阵（{len(entries)} 条活跃 WR） 数字=pattern数, 括号=trap数')
    print(f'{"section":<10}', end='')
    for c in CTYPES:
        print(f'{c:<10}', end='')
    print('合计')
    total = 0
    gaps = []
    for s in SECTIONS:
        row_total = 0
        print(f'{s:<10}', end='')
        for c in CTYPES:
            n = grid.get((s, c), 0)
            t = traps.get((s, c), 0)
            row_total += n
            cell = f'{n}({t})' if t else f'{n}'
            flag = '⚠️' if n == 0 else ('·' if n < 3 else ' ')
            print(f'{cell:<9}{flag}', end='')
        total += row_total
        print(f'{row_total}')
    print(f'\n活跃库合计: {total} 条')
    # 缺口：section×context_type 空白单元格（通用可容忍）
    blank = [(s, c) for s in SECTIONS for c in CTYPES
             if grid.get((s, c), 0) == 0 and c != '通用']
    print(f'空白单元格（pattern=0，非通用）: {len(blank)} 个')
    for s, c in blank[:12]:
        print(f'  - {s} × {c}')
    print('\n目标（GPT/Kimi 共识）：每个非通用单元格 ≥3 pattern + ≥1 trap → 优先补高影响题型')


if __name__ == '__main__':
    main()
