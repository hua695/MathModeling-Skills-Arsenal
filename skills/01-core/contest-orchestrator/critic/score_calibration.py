#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
critic/score_calibration.py — v3.9 Score Calibration Layer（评分校准层）

Evidence → Raw Score(0-100) → Calibration(90% 封顶·可配置) → Calibrated Score(0-90) → 校准分位(区间)

规则：raw_score 与 calibrated_score 分离；资格门禁与连续质量评分分离；校准分位输出区间；practice 只出分，retrospective 才允许历史分位；任何位次推断都必须带 provenance、置信度和限制说明。

用法:
    from critic.score_calibration import review_report
    rep = review_report(
        evidence={'hard_violations': [], 'criteria': [
            {'criterion': '摘要', 'weight': 10, 'earned': 8,
             'note': '逐问带数字，但无总评段'},
            ...
        ]},
        context={'contest': 'cumcm', 'year': 2023, 'division': '本科', 'problem': 'B'},
        mode='practice',        # practice/retrospective
    )
"""
import os
import sys

# ---- 可配置标定参数（评审：90% 封顶是标定规则，可配置）----
DEFAULT_CAP = 0.9          # 评委满分保留：每项 earned ≤ cap × weight
# 资格门禁硬规则（命中即 FAIL，不进评分池）——关键词组匹配（防字面变体漏检）
GATE_HARD_RULES = {
    '身份泄露': ['身份', '参赛队', '参赛编号', '队员姓名', '队员', '学校', '姓名'],
    '无实质模型': ['无模型', '无实质', '无结果', '不可读'],
    '核心模型数学无效': ['模型无效', '数学无效', '推导错误', '结论不成立', '核心模型错误'],
}
# 校准分位锚点（L0 冷启动——待赛后真实结果校准，见 calibration_db 规划）
# 结构：contest -> {anchor_score: percentile}（样本内分布，非官方真值）
# L0-2026-08-14: 5 篇自评样本内分布（3 原稿 + 2 合成变体，Blom 分位），待 L2 校准
#   样本: v_final(84.9->P90) v_mid_r1(76.4->P70) v_mid(73.4->P50) v_low2(61.5->P30) v_low(57.0->P10)
CUMCM_ANCHORS_L0 = {
    57.0: 10, 61.5: 30, 73.4: 50, 76.4: 70, 84.9: 90,
}
ANCHOR_YEAR_L0 = 2026   # 锚点数据年份（评审：年度衰减——锚点对后续年份参考价值递减）
SMALL_CONTEST_UNIFORM = {'lo': 10, 'hi': 90}  # 小竞赛近似均匀分布（声明不代表实际名次）

# provenance 分级
PROVENANCE_LEVELS = [
    'exact_contest_exact_year_exact_problem',  # 同赛同年同题同组真实样本
    'same_contest_same_problem',               # 同赛同题（跨年）
    'same_contest_historical',                 # 同赛历史分布
    'cross_contest',                           # 跨赛近似
    'generic_model',                           # 通用模型（最不可信）
]


def eligibility_gate(violations, hard_rules=None):
    """资格门禁（布尔，前置）：硬规则违规 → 不合格，不进评分池。
    hard_rules 为 None 用 GATE_HARD_RULES 关键词组；也可传自定义 {rule: [keywords]}。"""
    rules = hard_rules or GATE_HARD_RULES
    hits = []
    for v in (violations or []):
        for rule, kws in rules.items():
            if any(kw in v for kw in kws):
                hits.append(f'{rule}（{v}）')
                break
    return {
        'eligible': len(hits) == 0,
        'hard_violations': hits,
        'rule': '硬规则违规(身份泄露/无实质模型/核心模型数学无效) → 直接不合格，不参与百分制评分',
    }


def score_criteria(criteria, cap=DEFAULT_CAP):
    """逐条评分：raw(0-100) 与 calibrated(0-90) 分离。
    criteria: [{criterion, weight, earned, note}]，earned ≤ weight（raw 口径）。
    calibrated = earned × cap（每项封顶，评委满分保留——不是论文缺陷）。"""
    raw_total = 0.0
    cal_total = 0.0
    weight_total = 0.0
    rows = []
    for c in criteria:
        w = float(c.get('weight', 0))
        e = min(float(c.get('earned', 0)), w)   # raw 不超权重
        ceiling = w * cap
        ce = min(e, ceiling)                    # calibrated 封顶
        raw_total += e
        cal_total += ce
        weight_total += w
        rows.append({
            'criterion': c.get('criterion', '?'),
            'weight': round(w, 1),
            'raw_earned': round(e, 1),
            'ceiling': round(ceiling, 1),
            'calibrated_earned': round(ce, 1),
            'note': c.get('note', ''),
            'capped': e > ceiling,
        })
    return {
        'raw_score': round(raw_total, 1),          # 0-100（无封顶口径）
        'calibrated_score': round(cal_total, 1),   # 0-90（封顶口径）
        'weight_total': round(weight_total, 1),
        'rows': rows,
        'cap': cap,
        'cap_note': '评委满分保留（每项 90% 封顶），非论文缺陷',
    }


def _percentile_from_anchors(score, anchors):
    """锚点插值 → 百分位（区间）。anchors: {score: percentile} 升序。"""
    pts = sorted(anchors.items())
    if not pts:
        return None
    if score <= pts[0][0]:
        lo = hi = pts[0][1]
    elif score >= pts[-1][0]:
        lo = hi = pts[-1][1]
    else:
        for i in range(len(pts) - 1):
            s0, p0 = pts[i]
            s1, p1 = pts[i + 1]
            if s0 <= score <= s1:
                f = (score - s0) / max(1e-6, (s1 - s0))
                lo = p0 + f * (p1 - p0)
                hi = lo
                break
    # 区间化：±5 分位带（防数字伪精确）
    lo = max(0, int(lo) - 5)
    hi = min(100, int(hi) + 5)
    return f'P{lo}–P{hi}'


def estimate_percentile(calibrated, context=None, mode='retrospective', anchors=None):
    """校准分位（区间输出，非单点）。
    mode: practice → 禁用位次；retrospective/competition → 允许（带 provenance）。
    context: {contest, year, division, problem} → provenance 分级。"""
    if mode == 'practice':
        return {'allowed': False,
                'note': '练习稿模式：不存在相同竞争分布，禁用校准分位；仅输出质量分与修改清单。'}
    if calibrated <= 0:
        return {'allowed': True, 'band': 'P0–P5', 'confidence': '低',
                'provenance': 'generic_model', 'note': '分数过低，位次无参考意义'}
    ctx = context or {}
    contest = (ctx.get('contest') or 'unknown').lower()
    if contest == 'cumcm':
        anc = anchors or CUMCM_ANCHORS_L0
        band = _percentile_from_anchors(calibrated, anc)
        prov = 'same_contest_historical'
        conf = '低（L0 自评样本内锚点，未经真实结果校准）'
        year_note = f'（锚点数据 {ANCHOR_YEAR_L0} 年，对后续年份参考价值递减）'
    elif contest in ('mcm', 'mcm_icm', 'mcmicm', '美赛'):
        # 美赛英文隔离：无美赛校准数据 → 国赛口径均匀近似，明确降可信度（不实现美赛锚点）
        lo, hi = SMALL_CONTEST_UNIFORM['lo'], SMALL_CONTEST_UNIFORM['hi']
        p = int(lo + (calibrated / 100.0) * (hi - lo))
        band = f'P{max(0, p - 5)}–P{min(100, p + 5)}'
        prov = 'cross_contest'
        conf = '极低（美赛无校准数据，国赛近似参考，可信度低）'
        return {
            'allowed': True,
            'band': band,
            'confidence': conf,
            'provenance': prov,
            'note': '美赛无校准数据，以下位次为国赛口径近似参考，不可信；仅用于内部质量定位，非美赛排名承诺',
        }
    else:
        # 小竞赛均匀近似
        lo, hi = SMALL_CONTEST_UNIFORM['lo'], SMALL_CONTEST_UNIFORM['hi']
        p = int(lo + (calibrated / 100.0) * (hi - lo))
        band = f'P{max(0, p - 5)}–P{min(100, p + 5)}'
        prov = 'cross_contest'
        conf = '极低（小竞赛均匀近似，不代表实际名次）'
        year_note = ''
    return {
        'allowed': True,
        'band': band,
        'confidence': conf,
        'provenance': prov,
        'note': '历史分布定位，非排名承诺；未考虑当年竞争强度/评阅组差异/同题质量波动' + year_note,
    }


def review_report(evidence, context=None, mode='practice', cap=DEFAULT_CAP):
    """评分校准层入口（单向：只消费 evidence，不反向影响 Paper-Critic）。
    evidence: {hard_violations: [], criteria: [{criterion, weight, earned, note}]}"""
    gate = eligibility_gate(evidence.get('hard_violations', []))
    if not gate['eligible']:
        return {
            'gate': gate,
            'scoring': None,
            'percentile': None,
            'verdict': '资格门禁 FAIL：' + '；'.join(gate['hard_violations']) + '，不参与百分制评分',
        }
    scoring = score_criteria(evidence.get('criteria', []), cap)
    percentile = estimate_percentile(scoring['calibrated_score'], context, mode)
    return {
        'gate': gate,
        'scoring': scoring,
        'percentile': percentile,
        'context': context or {},
        'mode': mode,
        'verdict': _verdict(scoring['raw_score'], scoring['calibrated_score'], percentile),
    }


def _verdict(raw, cal, pct):
    parts = [f'原始 {raw}/100 → 校准 {cal}/90（每项 90% 封顶口径）']
    if pct and pct.get('allowed'):
        parts.append(f'历史分布定位 {pct["band"]}（置信度 {pct["confidence"]}）')
    if pct and not pct.get('allowed'):
        parts.append(pct['note'])
    return '；'.join(parts)


if __name__ == '__main__':
    # 自测：用 2023B 评审证据（对应 WR 自查发现，映射到 11 维 rubric）
    evidence = {
        'hard_violations': [],
        'criteria': [
            {'criterion': '摘要(10)', 'weight': 10, 'earned': 8.5,
             'note': '逐问带数字684字4段，但总评段可再凝练'},
            {'criterion': '格式(10)', 'weight': 10, 'earned': 8.0,
             'note': '修复后无乱码/分页符/加粗/参考文献达标'},
            {'criterion': '问题理解与目标(6)', 'weight': 6, 'earned': 5.5, 'note': '四问目标清单清晰'},
            {'criterion': '假设与抽象(6)', 'weight': 6, 'earned': 5.0, 'note': 'A1-A6 物理依据充分'},
            {'criterion': '数据与预处理(8)', 'weight': 8, 'earned': 7.0, 'note': '251x201 网格正确解析'},
            {'criterion': '模型设计(20)', 'weight': 20, 'earned': 17.0, 'note': '统一几何框架贯穿四问'},
            {'criterion': '求解与复现(10)', 'weight': 10, 'earned': 8.5, 'note': '附录完整代码6段'},
            {'criterion': '验证灵敏度(12)', 'weight': 12, 'earned': 10.0, 'note': '参数扰动+临界坡度1.70°'},
            {'criterion': '结果与任务(8)', 'weight': 8, 'earned': 7.0, 'note': '四问全答带数字'},
            {'criterion': '创新与洞察(5)', 'weight': 5, 'earned': 4.0, 'note': '临界坡度发现是亮点'},
            {'criterion': '表达与呈现(5)', 'weight': 5, 'earned': 4.5, 'note': '6图全解读/三线表'},
        ],
    }  # 权重合计 = 100
    for mode in ('practice', 'retrospective'):
        print(f'=== mode={mode} ===')
        rep = review_report(evidence,
                            context={'contest': 'cumcm', 'year': 2023, 'division': '本科', 'problem': 'B'},
                            mode=mode)
        print('门禁:', rep['gate']['eligible'])
        print('评分:', rep['scoring']['raw_score'], '→', rep['scoring']['calibrated_score'], '/90')
        print('位次:', rep['percentile'])
        print('结论:', rep['verdict'], '\n')
