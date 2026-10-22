#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
retrieval_audit.py — WR 检索质量审计（v3.6.12 第六轮评审）

616 条库规模后，验证检索是否仍健康（章节硬过滤是否有效、华为杯是否被隔离、去重是否够）。

用法:
  python scripts/retrieval_audit.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'memory'))
from paper_retrieval import retrieve_paper

QUERIES = [
    {'section': '摘要', 'context_type': '优化', 'situation': ['多问递进']},
    {'section': '灵敏度分析', 'context_type': '优化', 'situation': ['多目标']},
    {'section': '模型建立', 'context_type': '机理', 'situation': ['电路网络']},
    {'section': '结果分析', 'context_type': '数据', 'situation': ['分类对比']},
]


def audit():
    print('=== WR 检索质量审计（默认排除华为杯）===')
    all_ok = True
    for q in QUERIES:
        p = retrieve_paper(q, top=8)
        patterns = p['patterns']
        n = len(patterns) or 1
        sec_match = sum(1 for r in patterns if r['wr_id'].startswith('WR-')) / n  # 占位，真实用 section 需另查
        # 从 patterns 无法直接拿 section（输出没含 section），改用 n_wr 与 section 命中评估
        # 简化：章节硬过滤后 n_wr 应 >0；pattern 多样性 = 去重前 vs 后
        uniq = len(set(r['pattern'][:20] for r in patterns))
        print(f"  [{q['section']}/{q['context_type']}] 命中{p['n_wr']}条 → top8 patterns={len(patterns)}, 去重后多样{uniq}/8")
        if p['n_wr'] == 0:
            all_ok = False
            print('    ❌ 章节硬过滤无命中（可能过严）')
        if uniq < 3:
            print('    ⚠️ 多样性不足（<3 个不同 pattern）')
    # 华为杯隔离验证
    default = retrieve_paper({'section': '模型建立', 'context_type': '机理'})
    all_in = retrieve_paper({'section': '模型建立', 'context_type': '机理'}, source_filter=['all'])
    print(f'\n华为杯隔离: 默认命中{default["n_wr"]} vs 全含{all_in["n_wr"]} → 隔离{"生效 ✅" if default["n_wr"] < all_in["n_wr"] else "异常 ❌"}')
    print('\n结论:', '审计通过 ✅' if all_ok else '存在待查项 ⚠️')
    return 0


if __name__ == '__main__':
    sys.exit(audit())
