#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/index_memory.py — v3.7 记忆索引维护工具

构建/报告语义检索索引（tier1 TF-IDF），并给出检索调参依据：
  - 每库条目数、索引构建耗时、词表大小
  - tier1 相似度分布（gate/weight 调参用：查询短/条目长 → 余弦天然偏小）
  - 可选 --embedding 预构建 tier2 向量缓存（需 sentence-transformers 或 EMBEDDING_API_URL）

用法:
  python scripts/index_memory.py             # 报告 + 构建耗时
  python scripts/index_memory.py --embedding # 尝试预构建 embedding 缓存
  python scripts/index_memory.py --check     # 校验 tier2 缓存与库规模一致
"""
import os
import sys
import time

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL)

from memory.retrieval import load_entries, DB_FILES  # noqa: E402
from memory.semantic import SemanticIndex, CACHE_DIR  # noqa: E402

PER_DB = ['FD', 'SD', 'ST', 'DM']


def main():
    t0 = time.time()
    entries = load_entries()
    load_ms = int((time.time() - t0) * 1000)

    # 每库条目数
    print(f'经验库条目（{len(entries)} 条，解析 {load_ms}ms）：')
    for kind, path in DB_FILES.items():
        n = sum(1 for e in entries if e.get('_kind') == kind)
        print(f'  {kind:<4} {n:<6} {os.path.basename(path)}')

    # tier1 索引
    t1 = time.time()
    idx = SemanticIndex(entries).build()
    build_ms = int((time.time() - t1) * 1000)
    print(f'\ntier1 TF-IDF 索引：{build_ms}ms 构建，词表 {len(idx.idf)}，'
          f'向量 {len(idx.docs)} 篇（纯标准库，每次进程内构建，无需缓存）')

    # tier1 相似度分布（给 SEMANTIC_GATE 调参的直观依据）
    demo_qs = [
        ('预测+时序+小样本', '预测 预测 预测 时序 时间序列 LSTM ARIMA 小样本'),
        ('几何覆盖+测线', '优化决策 优化决策 优化决策 几何覆盖 测线 多波束 覆盖宽度 重叠率 海底地形'),
        ('数据一致性+复现', '任意 任意 任意 数据一致性 复现 结果溯源 参数口径'),
    ]
    print('\ntier1 查询相似度分布（top-5 / 超过 max(0.06, 0.6×max) 的候选数）：')
    for name, q in demo_qs:
        hits = idx.query(q, top_k=0)
        if not hits:
            continue
        mx = hits[0][0]
        floor = max(0.06, 0.6 * mx)
        n_above = sum(1 for s, _ in hits if s >= floor)
        top = ' '.join(f'{semantic_id(entries[i])}:{s:.3f}' for s, i in hits[:5])
        print(f'  [{name}] max={mx:.3f} floor={floor:.3f} 候选>floor={n_above}')
        print(f'      top5: {top}')

    # tier2 可选
    if '--embedding' in sys.argv:
        print('\n预构建 tier2 embedding 缓存…')
        idx.build(embedding=True)
        if idx.embeddings is not None:
            print(f'  OK：{len(idx.embeddings)} 条向量已缓存 → {os.path.join(CACHE_DIR, "embeddings.json")}')
        else:
            print('  跳过：无 sentence-transformers，也未配置 EMBEDDING_API_URL/KEY')
    if '--check' in sys.argv:
        import json
        cache = os.path.join(CACHE_DIR, 'embeddings.json')
        if os.path.exists(cache):
            with open(cache, encoding='utf-8') as f:
                data = json.load(f)
            ok = data.get('n') == len(entries)
            print(f'\ntier2 缓存校验：{data.get("n")} vs 条目 {len(entries)} → '
                  f'{"一致" if ok else "不一致（--embedding 重建）"}')
        else:
            print('\ntier2 缓存不存在（未预构建）')


def semantic_id(e):
    for k in ('failure_id', 'success_id', 'strategy_id', 'decision_id', 'wr_id', 'id'):
        v = e.get(k)
        if v:
            return str(v)
    return e.get('_id') or '?'


if __name__ == '__main__':
    main()
