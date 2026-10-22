#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/benchmark_topic_selection.py — v3.8.1 选题层 Leave-One-Contest-Out 回放验证

评审（GPT）：自测是 in-database retrieval test（2023B 经验在库 → 覆盖高是必然，数据泄漏）。
真正的验证是 **Leave-One-Contest-Out**：把某场比赛当年沉淀的经验从库里移除，
再看选题层的覆盖信号是否仍然合理——区分"跨年份同类经验的真实覆盖"与"当年经验的泄漏回声"。

流程：
  全库 topic_score → 移除某场 source 相关条目 → 重算该题 profile → 对比 depth/specificity/排名
判定：
  - 移除后该题仍排前列、depth 跌幅小 → 覆盖信号稳健（库里有跨年份同类经验）
  - 移除后大幅跌落/掉出前列 → 覆盖依赖当年经验（纯泄漏，不可信）

用法:
  python scripts/benchmark_topic_selection.py          # 跑 2023A/B/C + 2020B 回放
  python scripts/benchmark_topic_selection.py --all    # 含更多年份（可扩展）
"""
import os
import re
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL)

from memory.retrieval import load_entries  # noqa: E402
from memory.topic_intelligence import score_topic  # noqa: E402

# 历史竞赛：id / 标题 / fingerprint / 当年 source 识别规则（关键词命中 source 才剔除）
CONTEST_FINGERPRINTS = [
    {'id': '2023B', 'title': '多波束测线(几何覆盖)',
     'fp': {'primary': '优化决策', 'subtype': ['几何覆盖'],
            'keywords': ['测线', '多波束', '覆盖宽度', '重叠率'], 'constraints': ['海底地形']},
     'remove_terms': ['2023', '多波束', '测线']},
    {'id': '2023A', 'title': '定日镜场(光学)',
     'fp': {'primary': '物理建模', 'subtype': ['光学'],
            'keywords': ['定日镜', '光线追踪', '光学效率', '热功率'], 'constraints': ['阴影遮挡']},
     'remove_terms': ['2023', '定日镜']},
    {'id': '2023C', 'title': '蔬菜定价(数据)',
     'fp': {'primary': '优化决策', 'subtype': ['定价'],
            'keywords': ['蔬菜', '损耗率', '批发价', '单品'], 'data_scale': 'medium'},
     'remove_terms': ['2023', '蔬菜']},
    {'id': '2020B', 'title': '穿越沙漠(决策)',
     'fp': {'primary': '优化决策', 'keywords': ['穿越沙漠', '路径', '资源', '天气']},
     'remove_terms': ['2020', '穿越沙漠']},
]


def is_contest_entry(e, terms):
    """source 是否同时含年份词与题面词（如 '2023'+'多波束'）→ 判定为该场沉淀经验。"""
    src = str(e.get('source', '')) or ''
    return all(t in src for t in terms)


def main():
    entries = load_entries()
    print(f'全库 {len(entries)} 条。Leave-One-Contest-Out 回放（剔除当年 source 经验后重算）：\n')
    print(f'{"竞赛":<10}{"维度":<12}{"全库":>8}{"移除后":>8}{"跌幅":>8}')
    print('-' * 52)
    for c in CONTEST_FINGERPRINTS:
        # 全库
        full_p = score_topic(c['fp'])
        # 剔除当年经验
        loo_entries = [e for e in entries if not is_contest_entry(e, c['remove_terms'])]
        removed = len(entries) - len(loo_entries)
        loo_p = score_topic(c['fp'], entries=loo_entries)
        for dim, key in [('depth', 'depth'), ('specificity', 'specificity'),
                         ('evidence_quality', 'evidence_quality')]:
            fv, lv = full_p[key], loo_p[key]
            drop = (fv - lv) / max(1e-6, fv)
            print(f'{c["id"]:<10}{dim:<12}{fv:>8.3f}{lv:>8.3f}{drop:>7.0%}')
        status_keep = '✓稳健' if loo_p['status'] in ('rich', 'normal') else '⚠崩塌'
        print(f'{"":<10}{"状态":<12}{full_p["status"]:>8}{loo_p["status"]:>8}'
              f'{removed:>7}条移除 {status_keep}')
        print('-' * 52)


if __name__ == '__main__':
    main()
