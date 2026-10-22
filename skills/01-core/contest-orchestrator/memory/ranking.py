#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory/ranking.py — 经验检索排序

排序规则：
  相似度定档（A≥1.5 / B 0.9~1.5 / C 0.5~0.9 / D<0.5）
  → 档内有界 rank_score = sim × (0.5 + 0.5 × min(quality×reuse×freshness×bonus, 2))
  → × 来源多样性（同源 ≥3 条 ×0.8）
档内元数据只作为有界调制器参与排序，不能淹没相似度差异。

- similarity     : 检索相似度（fingerprint 匹配 / 语义 0~1）
- quality_score  : 来源质量(0.5) + 置信度(0.3) + 已验证(0.2)
- reuse_factor   : 复用越多越可靠，但用 sqrt 温和压制马太效应
- freshness      : 时间衰减（按 memory_type 分型 γ，老经验降权）
- exploration_bonus: 新经验（human_replay/theory 且复用<3）给探索奖励，破"新经验没人用"

向后兼容：旧条目缺省字段自动补默认值，不改历史数据。纯 Python 无第三方依赖。
"""
import math
import re

# 旧条目缺省值
DEFAULTS = {
    'memory_type': 'paper_extract',
    'source_quality': '中',
    'confidence': '中',
    'verified': False,
    'reuse_count': 0,
    'success_rate': None,
    'year': None,
}

_LEVEL = {'高': 1.0, '中': 0.6, '低': 0.3}

# 不同 memory_type 的时间衰减 γ（理论最稳，LLM 采集最快过时）
GAMMA = {'theory': 0.98, 'human_replay': 0.95, 'paper_extract': 0.9, 'llm_extract': 0.85}
# freshness floor：老经验不被完全埋没（theory 几乎不过时；LLM 经验最低但非零）
FLOOR = {'theory': 0.85, 'human_replay': 0.6, 'paper_extract': 0.5, 'llm_extract': 0.4}
# WR（写作经验库）专用衰减：写法类经验老化远慢于建模经验
#   "摘要要有数字""图表要有编号"这类要求 10 年不变，γ 比 paper_extract 更慢、floor 更高
WR_GAMMA = 0.95
WR_FLOOR = 0.70

CURRENT_YEAR = 2026


def _q(entry, key):
    """读 quality_score 子字段；缺省回落到顶层字段再回落到默认值"""
    qs = entry.get('quality_score') or {}
    v = qs.get(key)
    if v is None:
        v = entry.get(key, DEFAULTS.get(key))
    return v


def _year(entry):
    """从 quality_score.year / 顶层 year / source(最后一段数字) 提取年份"""
    y = _q(entry, 'year')
    if y is None:
        src = entry.get('source', '') or ''
        parts = src.split('|')
        if parts and parts[-1].strip().isdigit():
            y = parts[-1].strip()
    try:
        return int(y)
    except (TypeError, ValueError):
        return None


def quality_score(entry):
    """0~1：source_quality(0.5) + confidence(0.3) + verified(0.2)"""
    sq = _LEVEL.get(_q(entry, 'source_quality'), 0.6)
    cf = _LEVEL.get(_q(entry, 'confidence'), 0.6)
    vf = 1.0 if _q(entry, 'verified') else 0.5
    return 0.5 * sq + 0.3 * cf + 0.2 * vf


def reuse_factor(entry, max_reuse=1):
    """0~1：未复用=0.5；复用后 sqrt 温和上升（破马太，不抹杀复用价值）"""
    rc = _q(entry, 'reuse_count')
    try:
        rc = int(rc or 0)
    except (TypeError, ValueError):
        rc = 0
    sr = _q(entry, 'success_rate')
    sr = sr if isinstance(sr, (int, float)) else 0.5
    if rc <= 0:
        return 0.5
    rc_part = 0.4 * (math.sqrt(rc) / math.sqrt(max(1, max_reuse)))
    return min(1.0, 0.5 + rc_part + 0.1 * max(0.0, min(1.0, sr)))


def freshness(entry, current_year=CURRENT_YEAR):
    """时间衰减（含 floor）：0~1。
    无年份=1；年份越老按 memory_type 的 γ 指数衰减，但不低于该型 floor（老经验不埋没）。
    WR 条目（带 wr_id）使用更慢的衰减参数。"""
    y = _year(entry)
    if y is None:
        return 1.0
    age = current_year - y
    if age <= 0:
        return 1.0
    mt = _q(entry, 'memory_type')
    if entry.get('wr_id'):
        gamma, floor = WR_GAMMA, WR_FLOOR
    else:
        gamma = GAMMA.get(mt, 0.9)
        floor = FLOOR.get(mt, 0.5)
    return max(gamma ** age, floor)


def exploration_bonus(entry):
    """新经验探索奖励：human_replay/theory 且复用<3 → boost（随复用衰减）。
    WR 条目（wr_id）与 paper_extract 不享受探索奖励，避免低验证度经验被优先采用。"""
    mt = _q(entry, 'memory_type')
    rc = _q(entry, 'reuse_count')
    try:
        rc = int(rc or 0)
    except (TypeError, ValueError):
        rc = 0
    if entry.get('wr_id'):
        return 1.0
    if mt in ('human_replay', 'theory') and rc < 3:
        return 1.5 * math.exp(-0.3 * rc)
    return 1.0


def final_score(similarity, entry, max_reuse=1, current_year=CURRENT_YEAR):
    """综合分 = 相似度 × 质量 × 复用 × 新鲜度 × 探索奖励。"""
    return (float(similarity)
            * quality_score(entry)
            * reuse_factor(entry, max_reuse)
            * freshness(entry, current_year)
            * exploration_bonus(entry))


def rank_score(similarity, entry, max_reuse=1, current_year=CURRENT_YEAR, meta_floor=0.5):
    """检索排序分（retrieval.py 使用）：
    score = similarity × (meta_floor + (1-meta_floor) × min(metadata_product, 2))

    与 final_score 的区别：质量/复用/新鲜度/探索奖励被压成【有界调制器】，
    只在该层内部摆动（如 floor=0.5 → 因子 ∈ [0.6, 1.1]，比值 ≤1.83×），
    只在同一相关档内使用元数据排序，避免低质量元数据跨档改变语义相关性。"""
    meta = (quality_score(entry)
            * reuse_factor(entry, max_reuse)
            * freshness(entry, current_year)
            * exploration_bonus(entry))
    bounded = meta_floor + (1.0 - meta_floor) * min(meta, 2.0)
    return float(similarity) * bounded


def rank_entries(entries, similarity_fn=None, max_reuse=1, current_year=CURRENT_YEAR):
    """entries: [{id|*_id, quality_score{...}, reuse_count, success_rate, source, _sim?}]
    返回按综合分降序的 [{id, sim, quality, reuse, fresh, bonus, score}]"""
    out = []
    for e in entries:
        if similarity_fn is not None:
            sim = float(similarity_fn(e))
        else:
            sim = float(e.get('_sim', 0.5))
        eid = (e.get('id') or e.get('failure_id') or e.get('success_id')
               or e.get('strategy_id') or e.get('decision_id') or '?')
        out.append({
            'id': eid,
            'sim': round(sim, 4),
            'quality': round(quality_score(e), 4),
            'reuse': round(reuse_factor(e, max_reuse), 4),
            'fresh': round(freshness(e, current_year), 4),
            'bonus': round(exploration_bonus(e), 4),
            'score': round(final_score(sim, e, max_reuse, current_year), 6),
        })
    out.sort(key=lambda x: x['score'], reverse=True)
    return out


if __name__ == '__main__':
    demo = [
        {'id': 'FD-1', 'problem_type': '预测', 'quality_score': {'source_quality': '高', 'confidence': '高', 'verified': True, 'reuse_count': 5, 'success_rate': 1.0, 'memory_type': 'paper_extract'}, 'source': 'x|u|2023', '_sim': 0.9},
        {'id': 'FD-2', 'problem_type': '预测', 'quality_score': {'memory_type': 'human_replay', 'reuse_count': 0}, 'source': 'x|u|2026', '_sim': 0.8},
        {'id': 'FD-3', 'problem_type': '预测', '_sim': 0.85},  # 旧条目全缺省
    ]
    for r in rank_entries(demo):
        print(r)
