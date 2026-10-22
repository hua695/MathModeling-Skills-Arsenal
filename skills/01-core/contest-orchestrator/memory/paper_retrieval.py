#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory/paper_retrieval.py — Presentation Intelligence Layer 检索层

论文上下文(Paper Context) → 呈现先验(Presentation Prior)

与 memory/retrieval.py（问题指纹 → 决策先验）的分工：
  问题检索：键 = Problem Fingerprint（主类/题型/关键词）→ 决定"做什么模型"
  论文检索：键 = 论文上下文（章节/题型/场景）→ 决定"怎么写这章节"

产出"呈现先验"：
  - patterns : 该章节该用的写法（每条带 why + 真实论文 example 可引用）
  - traps    : 该章节要躲的坑（评审扣分点）
Writer 写每章前、Paper-Critic 审前调用；拿到的先验必须逐条用上或说明为何不用（防摆设）。

用法:
    from memory.paper_retrieval import retrieve_paper
    prior = retrieve_paper({'section': '摘要', 'context_type': '优化', 'situation': ['多问递进', '结果多']})
    # stage 过滤：draft/revise/polish；LOCK 阶段传 'polish' 可滤掉“需补内容”类 pattern
    prior = retrieve_paper({'section': '结果分析'}, stage='polish')
"""
import os
import sys

try:
    from memory.ranking import final_score
except ModuleNotFoundError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ranking import final_score

# 用脚本相对路径定位 skill 根（与 retrieval.py 一致，兼容 ~/.workbuddy 与 ~/.claude 双安装）
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WR_DB = os.path.join(SKILL, 'memory', 'writing_database.md')

# 章节同义词表：key=规范章节名，values=别名（匹配时都用）
SECTION_SYNONYMS = {
    '摘要': ['摘要', 'abstract', '摘要部分'],
    '引言': ['引言', '背景', '问题背景', '研究意义', '研究背景'],
    '问题重述': ['问题重述', '问题解读', '重述', '问题分析'],
    '模型假设': ['模型假设', '假设', '模型假设与符号'],
    '符号说明': ['符号说明', '符号', '主要符号'],
    '模型建立': ['模型建立', '建模', '模型构建', '模型的建立与求解', '问题一模型'],
    '求解': ['求解', '模型求解', '算法', '求解与分析', '结果求解'],
    '结果分析': ['结果分析', '结果', '结果与讨论', '模型结果'],
    '灵敏度分析': ['灵敏度分析', '灵敏度', '稳定性分析', '稳健性'],
    '问题改进': ['问题改进', '找问题', '模型改进', '模型评价与改进'],
    '模型评价': ['模型评价', '优缺点', '评价与推广', '模型评价与推广', '模型优缺点'],
    '结论': ['结论', '总结', '结束语'],
    '附录': ['附录', '代码', '附录代码', '附件'],
}

# 题型：context_type 匹配。'通用' 对所有题型都给分但权重略低。
CONTEXT_TYPES = ['优化', '预测', '评价', '机理', '图模型', '数据', '通用']


def load_wr_entries():
    """解析 writing_database.md 为 dict 列表（带 _kind 标签）"""
    entries = []
    if not os.path.exists(WR_DB):
        return entries
    import re
    txt = open(WR_DB, encoding='utf-8').read()
    for b in re.findall(r'```yaml\n(.*?)\n```', txt, re.S):
        d = {}
        for line in b.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                d[k.strip()] = v.strip()
        if d.get('wr_id'):
            entries.append(d)
    return entries


def _section_alias_map():
    """别名 → 规范章节名 的查表"""
    m = {}
    for canonical, aliases in SECTION_SYNONYMS.items():
        m[canonical] = canonical
        for a in aliases:
            m[a] = canonical
    return m


def match_wr(e, ctx, alias_map):
    """WR 条目 vs 论文上下文 匹配分。
    层级检索：section/stage 是【硬过滤】条件（不匹配直接剔除），
    题型/赛制/场景/质量是【层内软排序】维度。🔒 不要改成软加权——否则 300 条后
    通用条目会靠 quality 挤进 top-8，同章节噪声爆炸。
    """
    score = 0.0
    # 1) 章节匹配（硬过滤主键）：不匹配直接剔除，绝不降权放行
    e_section = e.get('section', '')
    c_section = (ctx.get('section') or '').strip()
    if c_section:
        c_canon = alias_map.get(c_section, c_section)          # 查询章节 → 规范名
        if e_section == c_canon:
            score += 1.0
        elif e_section == '通用' or e_section in SECTION_SYNONYMS.get(c_canon, []):
            score += 0.8
        elif c_section in SECTION_SYNONYMS.get(e_section, []):
            score += 0.8                                       # 条目章节规范名，查询是别名
        else:
            return 0.0                                         # 章节完全无关 → 剔除
    else:
        score += 0.5                                           # 未指定章节：降权但不剔除
    # 2) 题型匹配（“机理-仿真”条目同时命中查询父类“机理”，反之亦然）
    e_ctx = e.get('context_type', '')
    c_ctx = (ctx.get('context_type') or '').strip()
    if c_ctx:
        if e_ctx == c_ctx:
            score += 0.5
        elif e_ctx == '通用':
            score += 0.3
        elif e_ctx and '-' in e_ctx and e_ctx.split('-')[0] == c_ctx:
            score += 0.3   # 子类条目命中父类查询（机理-仿真 命中 机理）
        elif c_ctx and '-' in c_ctx and c_ctx.split('-')[0] == e_ctx:
            score += 0.3   # 父类条目命中子类查询（机理 命中 机理-仿真）
    # 3) 赛制匹配：competition_family 相同 +0.3；通用条目/不匹配不扣分
    cf = (ctx.get('competition_family') or '').strip()
    if cf and (e.get('competition_family') or '').strip() == cf:
        score += 0.3
    # 4) 场景关键词匹配（重叠越多分越高，封顶）
    hits = 0
    for kw in ctx.get('situation', []) or []:
        if kw and kw in (e.get('situation') or ''):
            hits += 1
    score += 0.3 * min(hits, 3)
    return score if score > 0 else 0.0


def _stage_ok(e, stage):
    """stage 过滤：条目无 stage=任何阶段可用；有 stage 则必须与查询阶段一致。
    语义：LOCK 阶段传 'polish'，可滤掉标了 stage=draft 的“需补内容”类 pattern。"""
    if not stage:
        return True
    es = (e.get('stage') or '').strip()
    return (not es) or es == stage


def _dedup_display(patterns, max_same=2):
    """检索去重展示：同 pattern 前 15 字的分组最多展示 2 条
    （最高分 1 条 + 1 条变体），既去冗余又保多样性。不做主动清理，只影响展示。"""
    groups = {}
    for p in patterns:
        key = (p.get('pattern') or '')[:15]
        groups.setdefault(key, []).append(p)
    out = []
    for g in groups.values():
        out.extend(g[:max_same])
    return out


_DEFAULT_EXCLUDE_FAMILY = ['huaweibei']  # 默认排除华为杯（研究生赛与本科赛差异大）


def _source_filter_ok(e, source_filter):
    """来源硬过滤：默认排除 huaweibei；source_filter 显式指定时按列表。
    None/未指定 → 排除 huaweibei；['all'] → 全含；['guosai','huashu'] → 只含这些。"""
    if source_filter == ['all']:
        return True
    fam = e.get('competition_family', '')
    if source_filter is None:
        return fam not in _DEFAULT_EXCLUDE_FAMILY
    return fam in source_filter


def retrieve_paper(paper_context, top=8, current_year=2026, stage=None,
                   dedup_display=True, source_filter=None):
    """入口：paper_context 为 dict {section, context_type, situation:[...]}
    stage：draft/revise/polish（可选；LOCK 阶段传 polish 过滤补内容类 pattern）
    dedup_display：同 pattern 前缀最多展示 2 条（默认开，Writer 写作时用）
    source_filter：来源硬过滤（默认排除华为杯）——None=排除huaweibei / ['all']=全含 / 列表=只含
    返回呈现先验 {n_wr, patterns:[{wr_id, pattern, template, why, example, source}],
    traps:[...], context_used:{...}}"""
    entries = load_wr_entries()
    alias_map = _section_alias_map()
    scored = []
    for e in entries:
        if not _stage_ok(e, stage):
            continue
        if not _source_filter_ok(e, source_filter):
            continue
        sim = match_wr(e, paper_context, alias_map)
        if sim > 0:
            scored.append((sim, e))
    scored.sort(key=lambda x: final_score(x[0], x[1], current_year=current_year), reverse=True)
    ranked = [e for _, e in scored[:top]]
    patterns = [{'wr_id': e.get('wr_id'), 'pattern': e.get('pattern', ''),
                 'template': e.get('template', ''), 'why': e.get('why', ''),
                 'example': e.get('example', ''), 'source': e.get('source', ''),
                 'expression_variants': e.get('expression_variants', ''),
                 'aigc_risk': e.get('aigc_risk', ''),
                 'competition_family': e.get('competition_family', ''),
                 'feedback': e.get('feedback', ''), 'provenance': e.get('provenance', '')}
                for e in ranked if e.get('kind', 'pattern') != 'trap']
    if dedup_display:
        patterns = _dedup_display(patterns)
    # traps 从全量匹配项提取，避免与 patterns 争用 top-N 名额。
    traps = [{'wr_id': e.get('wr_id'), 'pattern': e.get('pattern', ''),
              'why': e.get('why', ''), 'bad_example': e.get('bad_example', ''),
              'fix_example': e.get('fix_example', ''), 'source': e.get('source', ''),
              'competition_family': e.get('competition_family', '')}
             for _, e in scored if e.get('kind') == 'trap']
    return {
        'n_wr': len(scored),
        'n_top': len(ranked),
        'patterns': patterns,
        'traps': traps,
        'coverage': _coverage_level(len(scored)),
        'context_used': {
            'section': paper_context.get('section', ''),
            'context_type': paper_context.get('context_type', ''),
            'situation': paper_context.get('situation', []),
            'competition_family': paper_context.get('competition_family', ''),
            'stage': stage,
        },
    }


def _coverage_level(n_matched):
    """覆盖置信度：新题型覆盖不足时提示 Writer 不要把历史经验当作规范。
    cold_start: <10 条，历史经验覆盖严重不足，启用降级模式
    low: <30 条，覆盖弱，历史先验仅参考
    medium: <80 条，覆盖一般
    high: ≥80 条，覆盖充分"""
    if n_matched < 10:
        return {'n_matched': n_matched, 'level': 'cold_start',
                'note': '历史经验覆盖不足，勿把检索到的零散条目当规范；启用通用规则+谨慎置信度语言'}
    if n_matched < 30:
        return {'n_matched': n_matched, 'level': 'low',
                'note': '覆盖弱，历史先验仅作参考，不强行套用'}
    if n_matched < 80:
        return {'n_matched': n_matched, 'level': 'medium'}
    return {'n_matched': n_matched, 'level': 'high'}


if __name__ == '__main__':
    # 自测：写摘要前的呈现先验
    ctx = {'section': '摘要', 'context_type': '优化', 'situation': ['多问递进', '结果数字多']}
    prior = retrieve_paper(ctx)
    print('库命中条目数:', prior['n_wr'])
    print('章节:', prior['context_used'])
    print('--- 该用的写法 ---')
    for p in prior['patterns'][:4]:
        print(f"[{p['wr_id']}] {p['pattern'][:50]}")
    print('--- 要躲的坑 ---')
    for t in prior['traps'][:3]:
        print(f"[{t['wr_id']}] {t['pattern'][:50]}")
