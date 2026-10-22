#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory/topic_intelligence.py — Topic Intelligence Layer（选题层）

本层约束：输出经验覆盖、证据质量、风险标签和不确定性，不预测获奖概率；题目选择仍须结合题面、时间、数据和队伍能力。
用法:
    from memory.topic_intelligence import topic_score
    result = topic_score([{'id': 'A', 'title': '...', 'fingerprint': {...}}, ...])
"""
import math
import os
import sys

try:
    from memory.retrieval import get_experience_coverage
except ModuleNotFoundError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from retrieval import get_experience_coverage

# ---- 档位（status 只作标签，不进连续计分——评审：count 双重计权修复）----
_STATUS_SCORE = {'rich': 1.0, 'normal': 0.6, 'weak': 0.3, 'cold_start': 0.0}
# ---- depth 对数归一的参考量（≈ 本库查询覆盖量的 P90，库扩到万级后应重标定）----
COUNT_REF = 500
# ---- 指纹质量检查 ----
_GENERIC_WORDS = {'优化', '模型', '分析', '问题', '数据', '方法', '预测', '决策', '评价'}
MIN_KEYWORDS = 3
# ---- evidence_quality 权重 ----
W_ACTION = 0.5
W_QUALITY = 0.5
# ---- specificity 权重：来源集中度为主（稳健），lexical 为辅 ----
W_SOURCE = 0.7
W_LEXICAL = 0.3
# ---- 短板乘法 heuristic（标注：非理论公式，leave-one-contest-out 校准前仅作排序用）----
UNC_FACTOR = 0.3   # 不确定性区间宽度 = (1 - fingerprint_quality) × UNC_FACTOR


def check_fingerprint_quality(fp):
    """P0 指纹质量门（评审：坏指纹→坏检索→坏选题的错误放大链）。
    检查：关键词数量 / 泛化词占比 / subtype 缺失。
    返回 {quality_score(0~1), issues[], recommendation}。"""
    issues = []
    kw = list(fp.get('keywords') or []) + list(fp.get('secondary') or [])
    if len(kw) < MIN_KEYWORDS:
        issues.append(f'关键词过少（{len(kw)} < {MIN_KEYWORDS}），覆盖召回可能不足')
    if kw:
        generic = sum(1 for k in kw if k in _GENERIC_WORDS)
        ratio = generic / len(kw)
        if ratio > 0.5:
            issues.append(f'泛化词占比 {ratio:.0%}（{generic}/{len(kw)}），specificity 可能失真')
    if not fp.get('subtype'):
        issues.append('无 subtype，题型判别力下降（来源集中度仍可兜底）')
    if not fp.get('primary'):
        issues.append('无 primary 主类，检索主键缺失')
    quality = max(0.0, 1.0 - 0.2 * len(issues))
    return {
        'quality_score': round(quality, 2),
        'issues': issues,
        'recommendation': '可用' if len(issues) <= 1 else '建议人工复核指纹后重评',
    }


def _depth(count):
    """对数归一覆盖深度（评审：count 线性饱和过早，20 条后无区分）。
    log 让 10/50/100/300/500 仍有递减区分；count=0 → 0。"""
    if count <= 0:
        return 0.0
    return round(min(1.0, math.log(1 + count) / math.log(1 + COUNT_REF)), 3)


def _risk_label(status, evidence_quality, specificity):
    """风险标签（评审：区分「低分」与「低置信度」）：
    冷启动=高；rich 但证据质量/特异性低 = 中高（表面安全实则盲区）。"""
    if status == 'cold_start':
        return '高'
    if status == 'weak':
        return '高'
    if evidence_quality < 0.4 or specificity < 0.4:
        return '中'
    if evidence_quality < 0.6 or specificity < 0.6:
        return '中低'
    return '低'


def score_topic(fingerprint, top=12, current_year=2026, entries=None):
    """单题 → ExperienceProfile（评审：不合成一个分，输出结构）。
    返回 {status, depth, specificity, evidence_quality, fingerprint_quality,
          heuristic_score(短板乘法·标注 baseline), risk_label, uncertainty, coverage, verdict}。
    entries 可注入（Leave-One-Contest-Out 回放基准用），缺省全库。"""
    cov = get_experience_coverage(fingerprint, top, current_year, entries)
    status = cov['retrieval_status']
    n = max(1, top)

    depth = _depth(cov['count'])
    # specificity：来源集中度为主（不依赖指纹质量）+ lexical 辅助
    lexical = cov['specific_count'] / n
    specificity = round(W_SOURCE * cov['top_source_ratio'] + W_LEXICAL * lexical, 3)
    # evidence_quality：可行动性（DM/ST/FD/SD 粒度）× 质量占比
    quality_ratio = cov['high_quality_count'] / n
    evidence_quality = round(W_ACTION * cov['actionability'] + W_QUALITY * quality_ratio, 3)
    fq = check_fingerprint_quality(fingerprint)

    # 短板乘法 heuristic（GPT 评审：线性加和允许一维极差被补回；乘法=短板效应）
    # 冷启动 depth=0 → 分自动归零，天然不排前
    heuristic = round(depth * evidence_quality * (0.5 + 0.5 * specificity), 3)
    uncertainty = round((1 - fq['quality_score']) * UNC_FACTOR, 3)
    risk = _risk_label(status, evidence_quality, specificity)

    verdict = {
        'rich': '经验覆盖充足：历史路径清晰，按经验推进胜率期望高（≠题容易）。',
        'normal': '经验覆盖一般：成功模式作候选，保留架构探索空间。',
        'weak': '经验覆盖弱：历史仅避坑参考，建模以第一性原理为主。',
        'cold_start': '零历史参照：无经验加成，需文献先行+探索预算；除非有队员专长优势。',
    }[status]

    return {
        'status': status,
        'depth': depth,
        'specificity': specificity,
        'evidence_quality': evidence_quality,
        'fingerprint_quality': fq,
        'heuristic_score': heuristic,
        'risk_label': risk,
        'uncertainty': uncertainty,
        'coverage': cov,
        'verdict': verdict,
    }


def _diverse_enough(a, b):
    """异质判定：两题的题型主键（primary/subtype）不同即为方法空间差异候选。"""
    pa = a.get('fingerprint', {}).get('primary', '')
    pb = b.get('fingerprint', {}).get('primary', '')
    sa = tuple(a.get('fingerprint', {}).get('subtype') or [])
    sb = tuple(b.get('fingerprint', {}).get('subtype') or [])
    return pa != pb or (sa and sb and sa != sb)


def topic_score(problems, top=12, current_year=2026):
    """多题入口 → 经验主推荐 + 经验异质备选 + 冷启动清单。
    返回 {ranked: [ExperienceProfile+id/title], recommendation}。
    命名遵循评审：经验主推荐 / 经验异质备选——本层不判断获奖概率。"""
    scored = []
    for p in problems:
        s = score_topic(p['fingerprint'], top, current_year)
        scored.append({
            'id': p.get('id', '?'),
            'title': p.get('title', ''),
            'profile': s,
        })
    # 排序：短板乘法 heuristic（标注 baseline，非理论公式）
    scored.sort(key=lambda x: x['profile']['heuristic_score'], reverse=True)

    primary = scored[0] if scored else None
    # 异质备选：与主推题型主键不同（方法空间差异）且覆盖≥weak 的最高分题
    exploration = None
    for s in scored[1:]:
        p = next(p for p in problems if p.get('id') == s['id'])
        prim_p = next(p for p in problems if p.get('id') == primary['id'])
        if s['profile']['status'] != 'cold_start' and _diverse_enough(p, prim_p):
            exploration = s
            break
    if exploration is None and len(scored) > 1:
        exploration = scored[1]  # 无题型差异候选时退化为次深

    cold_starts = [s for s in scored if s['profile']['status'] == 'cold_start']
    recommendation = {
        'primary': primary,
        'exploration': exploration,
        'cold_starts': cold_starts,
        'note': ('本层只估计经验先验优势，不预测获奖概率；'
                 '最终选题结合四维启发式（数据可得性/擅长/可行性/获奖潜力）与队员专长。'
                 if primary else ''),
    }
    if primary and primary['profile']['status'] == 'cold_start':
        recommendation['note'] = ('四题均无经验覆盖：本层不构成推荐依据，回归四维启发式；'
                                  '若选冷启动题，预留文献+探索预算。')
    return {'ranked': scored, 'recommendation': recommendation}


def format_for_planner(result, max_show=6):
    """评审：Planner 注入用结构化块，不传标量分数。
    返回 markdown 文本（TOPIC INTELLIGENCE 块）。"""
    r = result['recommendation']
    lines = ['## TOPIC INTELLIGENCE（经验先验，非获奖预测）', '']
    if r['primary']:
        s = r['primary']
        pr = s['profile']
        lines += [f"经验主推荐: {s['id']} {s['title']}",
                  f"- status: {pr['status']} | depth: {pr['depth']} | specificity: {pr['specificity']} "
                  f"| evidence_quality: {pr['evidence_quality']}",
                  f"- 风险: {pr['risk_label']} | 指纹质量: {pr['fingerprint_quality']['quality_score']}"
                  f"{' ⚠ ' + '；'.join(pr['fingerprint_quality']['issues']) if pr['fingerprint_quality']['issues'] else ''}",
                  f"- 解读: {pr['verdict']}", '']
    if r['exploration']:
        s = r['exploration']
        pr = s['profile']
        lines += [f"经验异质备选: {s['id']} {s['title']}（方法空间与主推不同）",
                  f"- status: {pr['status']} | specificity: {pr['specificity']} | 风险: {pr['risk_label']}", '']
    if r['cold_starts']:
        ids = ', '.join(f"{s['id']}({s['profile']['risk_label']})" for s in r['cold_starts'])
        lines += [f"冷启动(零经验): {ids}", '']
    if r['note']:
        lines += [r['note'], '']
    return '\n'.join(lines)


if __name__ == '__main__':
    # 自测：2023 国赛 A/B/C + 2020B + 库外题
    demo = [
        {'id': 'A', 'title': '2023A 定日镜场(光学)',
         'fingerprint': {'primary': '物理建模', 'subtype': ['光学'],
                         'keywords': ['定日镜', '光线追踪', '光学效率', '热功率'],
                         'constraints': ['阴影遮挡']}},
        {'id': 'B', 'title': '2023B 多波束测线(几何覆盖)',
         'fingerprint': {'primary': '优化决策', 'subtype': ['几何覆盖'],
                         'keywords': ['测线', '多波束', '覆盖宽度', '重叠率'],
                         'constraints': ['海底地形']}},
        {'id': 'C', 'title': '2023C 蔬菜定价(数据)',
         'fingerprint': {'primary': '优化决策', 'subtype': ['定价'],
                         'keywords': ['蔬菜', '损耗率', '批发价', '单品'],
                         'data_scale': 'medium'}},
        {'id': 'D', 'title': '2020B 穿越沙漠(决策)',
         'fingerprint': {'primary': '优化决策', 'keywords': ['穿越沙漠', '路径', '资源', '天气']}},
        {'id': 'E', 'title': '量子计算调度(库外)',
         'fingerprint': {'primary': '量子物理', 'keywords': ['量子比特', '退相干']}},
    ]
    r = topic_score(demo)
    print(f'{"题":<4}{"heuristic":>10}{"status":<12}{"depth":>6}{"spec":>6}{"evid":>6}{"风险":>4}{"指纹质":>6}')
    for s in r['ranked']:
        pr = s['profile']
        print(f'{s["id"]:<4}{pr["heuristic_score"]:>10.3f}{pr["status"]:<12}{pr["depth"]:>6.3f}'
              f'{pr["specificity"]:>6.3f}{pr["evidence_quality"]:>6.3f}{pr["risk_label"]:>4}'
              f'{pr["fingerprint_quality"]["quality_score"]:>6.2f} {s["title"]}')
    print()
    print(format_for_planner(r))
