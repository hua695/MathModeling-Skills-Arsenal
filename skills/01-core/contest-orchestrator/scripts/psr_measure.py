#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
psr_measure.py — WR 板块量化验证（Presentation Score Ratio）

L1 执行层：pattern 命中率（检索返回的写法被实际采用比例）+ trap 规避率（踩坑占比）
L3 结果层：auto presentation_score（Critic 自动初评，人工只复核，不自动打分）

用法:
  python scripts/psr_measure.py <wr_usage.json> [--csv out.csv]

wr_usage.json 格式（一场比赛结束后记录）:
{
  "competition": "2026华数杯B",
  "retrieved_patterns": ["WR-001","WR-003","WR-004"],   # Writer 收到的 patterns
  "adopted_patterns":  ["WR-001","WR-003"],             # 实际采用的 patterns
  "checked_traps":     ["WR-005","WR-032"],             # Paper-Critic 检查过的 traps
  "triggered_traps":   [{"wr_id":"WR-005","severity":"high"}],  # 踩中的坑（含严重度）
  "critic_issues_total": 12                              # 本场 Critic 总问题数（L2 对比用，可选）
}

验收线：
  L1: 综合命中率(采用率) ≥ 60% + 锚点 trap 规避率 ≥ 80%
  L2: 使用“验收通过率 + P0 复发率”（见 core/delivery_gate.md）
  L3: auto_score ≥ 7.5（参考，人工复核 trap 非误报）
  附加: guosai 命中率 ≥40%（跨赛制迁移）/ 华为杯命中 =0（隔离）
  ⚠️ 52% 是采用率（adopted/retrieved），非检索质量；retrieval_quality 待测区分"检索贴不贴"与"用不用"
"""
import csv
import json
import sys

SEVERITY_PENALTY = {'critical': 1.5, 'high': 1.0, 'medium': 0.5}


def auto_score(adopted_n, triggered):
    """Critic 自动初评：基准 6.0 + 有效 pattern（封顶 8 条）+0.3 − 踩坑惩罚，封顶 [1,10]。
    adopted 数量只计入真正影响写作的有效采纳，最多计 8 条，避免数量饱和失去区分度。"""
    s = 6.0 + 0.3 * min(adopted_n, 8)
    for t in triggered:
        s -= SEVERITY_PENALTY.get(t.get('severity', 'medium'), 0.5)
    return round(min(max(s, 1.0), 10.0), 2)


def calibrated_auto_score(adopted_n, triggered, cap=0.9):
    """校准版 auto_score（raw 与 calibrated 分层，L1/L2 验收线保持不变）。
    raw(1-10) × 90% 评委封顶 → 0-9 口径——评委满分保留，非论文缺陷。
    与 auto_score 并存：PSR L1/L2 继续读 raw 版；calibrated 作补充维度供 Score Calibration Layer 消费。"""
    raw = auto_score(adopted_n, triggered)
    return round(raw * cap, 2)


def measure(usage):
    """trap 度量：规避率只用【机器锚点】PASS/总数，
    纯语义 SUSPECTED 单列不进分母（防 Paper-Critic 自评幻觉——第一场 100% 规避但实际命中）。
    sections 分章节格式兼容，统一平铺为 retrieved/adopted/checked。"""
    # sections 分章节格式 → 平铺（兼容 workbuddy 华数杯2021A 那类 wr_usage）
    if not usage.get('adopted_patterns') and usage.get('sections'):
        secs = usage['sections']
        ret = sum(s.get('n_top', 0) for s in secs) or 1
        adopted = [p['wr_id'] for s in secs for p in s.get('used_patterns', [])]
        checked = [{'trap_id': t['wr_id'], 'status': 'PASS', 'anchor': True}
                   for s in secs for t in s.get('used_traps', [])]
    else:
        ret = len(usage.get('retrieved_patterns', [])) or 1
        adopted = usage.get('adopted_patterns', [])
        checked = usage.get('checked_traps', [])
    hit = len(adopted) / ret
    # checked_traps 支持两种格式：旧字符串列表（默认 anchor+status=PASS 兼容）/ 新对象列表
    anchor_total = 0
    anchor_pass = 0
    suspected = []
    failed = []
    for t in checked:
        if isinstance(t, dict):
            tid = str(t.get('trap_id', '?'))
            status = str(t.get('status', 'PASS')).upper()
            anchor = bool(t.get('anchor', False))
        else:  # 旧格式：字符串，默认视为锚点 PASS（向后兼容）
            tid = str(t)
            status = 'PASS'
            anchor = True
        if anchor:
            anchor_total += 1
            if status == 'PASS':
                anchor_pass += 1
        if status == 'FAIL':
            failed.append(tid)
        if status == 'SUSPECTED':
            suspected.append(tid)
    avoid = anchor_pass / anchor_total if anchor_total else 1.0
    score = auto_score(len(adopted), usage.get('triggered_traps', []))
    # PSR 第三场新增：来源命中指标（v3.6.13 第七轮评审）
    #   guosai_hit_rate  ≥40% → 国赛风格条目被实际调用（跨赛制迁移成立）
    #   huaweibei_hit    =0  → 华为杯隔离生效
    fam = _load_family_map()
    adopted_fams = [fam.get(w, '') for w in adopted]
    guosai_hit = sum(1 for f in adopted_fams if f == 'guosai') / len(adopted) if adopted else 0.0
    huaweibei_hit = sum(1 for f in adopted_fams if f == 'huaweibei')
    return {
        'competition': usage.get('competition', '?'),
        'n_retrieved': ret,
        'n_adopted': len(adopted),
        'pattern_hit_rate': round(hit, 3),
        'adoption_rate': round(hit, 3),    # 采用率 = adopted/retrieved（workbuddy 用了多少返回的）
        'retrieval_quality': None,         # 待测：检索返回里贴题的比例（需 wr_usage 提供全量返回+匹配标注）
        'anchor_trap_total': anchor_total,
        'anchor_trap_pass': anchor_pass,
        'trap_avoid_rate': round(avoid, 3),
        'guosai_hit_rate': round(guosai_hit, 3),       # 国赛来源条目命中占比（≥40% 跨赛制迁移成立）
        'huaweibei_hit': huaweibei_hit,                # 华为杯命中数（必须 =0，隔离生效）
        'suspected_traps': suspected,      # 语义判断项，单独列（如灵敏度流于形式）
        'confirmed_failed_traps': failed,  # 机器锚点 FAIL（真实命中）
        'auto_presentation_score': score,
        'critic_issues_total': usage.get('critic_issues_total'),
        'status': 'PASS' if (hit >= 0.6 and avoid >= 0.8 and not failed
                            and huaweibei_hit == 0) else 'CHECK',
    }


def _load_family_map():
    """读主库建 wr_id → competition_family 映射（PSR 第三场来源指标用）"""
    import re
    import os
    DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      'memory', 'writing_database.md')
    fam = {}
    if os.path.exists(DB):
        txt = open(DB, encoding='utf-8').read()
        for b in re.findall(r'```yaml\n(.*?)\n```', txt, re.S):
            d = {}
            for line in b.splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    d[k.strip()] = v.strip()
            if d.get('wr_id'):
                fam[d['wr_id']] = d.get('competition_family', '')
    return fam


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    usage = json.load(open(sys.argv[1], encoding='utf-8'))
    m = measure(usage)
    print(f"=== PSR 验证 | {m['competition']} | {m['status']} ===")
    print(f"综合命中率(采用率): {m['n_adopted']}/{m['n_retrieved']} = {m['pattern_hit_rate']:.1%} (达标线 ≥60%；=adopted/retrieved，反映 workbuddy 用不用)")
    print(f"retrieval_quality: {m['retrieval_quality']}（待测：需 wr_usage 提供全量检索返回+匹配标注，区分'检索贴不贴'与'用不用'）")
    print(f"锚点 trap 规避: {m['anchor_trap_pass']}/{m['anchor_trap_total']} = {m['trap_avoid_rate']:.1%}（机器锚点 PASS/总数，达标线 ≥80%）")
    print(f"guosai 命中率: {m['guosai_hit_rate']:.1%}（国赛来源条目命中占比，跨赛制迁移 ≥40% 达标）")
    print(f"华为杯命中: {m['huaweibei_hit']}（必须=0，隔离生效；>0 说明隔离有 bug）")
    if m['confirmed_failed_traps']:
        print(f"⚠️ 机器锚点 FAIL（真实命中）: {m['confirmed_failed_traps']}")
    if m['suspected_traps']:
        print(f"⚠️ SUSPECTED（语义判断，待人工复核）: {m['suspected_traps']}")
    print(f"auto_score:    {m['auto_presentation_score']}/10（参考线 ≥7.5，人工复核确认 trap 非误报）")
    if m.get('critic_issues_total') is not None:
        print(f"L2 参考: 本场 Critic 问题数 {m['critic_issues_total']}（与 v3.5 对比应下降 ≥40%）")
    if len(sys.argv) > 2 and sys.argv[2] == '--csv':
        with open('psr_output.csv', 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(m.keys()))
            w.writeheader(); w.writerow(m)
        print('CSV: psr_output.csv')
    return 0


if __name__ == '__main__':
    sys.exit(main())
