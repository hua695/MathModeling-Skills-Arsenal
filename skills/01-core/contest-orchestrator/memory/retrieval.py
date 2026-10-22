#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory/retrieval.py — Experience-driven Planning Layer 检索层

Problem Fingerprint → 多路召回 → ranking 精排 → 决策先验(decision prior)

分层混合检索：
  tier0 字符指纹（本文件 fingerprint_match_score）—— 结构主键，始终可用
  tier1 字符 n-gram TF-IDF（memory/semantic.py）   —— 同义改写召回 + 精排加分
  tier2 embedding 向量（可选，检测到模型/API 才启用）
  hybrid = char_sim + semantic_weight × tfidf_sim（+ emb_sim）
  语义高分但字符未命中的条目按 expand_floor 补入召回（上限 SEMANTIC_EXPAND_MAX）。

检索规则：字符指纹保证结构召回，n-gram TF-IDF 提供同义改写召回，可选 embedding 作为补充；相似度分档后再按质量和来源多样性排序。

用法:
    from memory.retrieval import retrieve
    prior = retrieve({'primary': '预测', 'keywords': ['时序'], 'data_scale': 'small'})
"""
import os
import re
from collections import Counter

try:
    from memory.ranking import final_score, rank_score
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ranking import final_score, rank_score

# ---- 检索参数 ----
SEMANTIC_GATE = 0.06       # 语义相似度绝对下限（查询短/条目长，余弦天然偏小）
SEMANTIC_REL = 0.6         # 相对下限：≥ 本查询最高 tfidf 的 60%（自适应查询长度）
SEMANTIC_WEIGHT = 0.7      # 混合分 = char_sim + weight × tfidf_sim
SEMANTIC_EXPAND_MAX = 8    # 语义补入条目的数量上限

# 分档排序：相似度定档，元数据只在档内竞争
BUCKET_A = 1.5             # 档A 高相关 sim≥1.5
BUCKET_B = 0.9             # 档B 中相关 0.9≤sim<1.5
BUCKET_C = 0.5             # 档C 弱相关 0.5≤sim<0.9；sim<0.5 为档D（仅补位）
# 来源多样性：同源第 3 条起降权，防单一来源占据候选集
DIVERSITY_SOURCE_MIN = 3   # 同一 source 出现 ≥3 次才触发
DIVERSITY_PENALTY = 0.8    # 拥挤来源的条目乘 0.8
# 冷启动/弱覆盖降级：系统必须区分已覆盖与未覆盖
STATUS_RICH = 20           # matched ≥20 → rich（历史=强先验）
STATUS_NORMAL = 5          # 5~19 → normal（参考+保留探索）
STATUS_WEAK = 1            # 1~4 → weak（仅避坑信息）
COLD_FILL = 4              # 冷启动时补入的通用条目上限
SEMANTIC_STRONG = 0.18     # 强语义线：char=0 且 tfidf≥此值才算"见过"
                           # 弱语义匹配不算已覆盖，冷启动时从强先验中剔除

# 用脚本相对路径定位 skill 根（不硬编码 ~/.claude/skills——workbuddy 装在 ~/.workbuddy/skills 会读空库）
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILES = {
    'FD': os.path.join(SKILL, 'failure_database.md'),
    'SD': os.path.join(SKILL, 'success_database.md'),
    'ST': os.path.join(SKILL, 'strategy_memory.md'),
    'DM': os.path.join(SKILL, 'memory', 'decision_memory.md'),
}

# 数据规模关键词
_SCALE_KW = {
    'small': ['小样本', '样本不足', '少量', '数据少', '样本量', '<100', '数据量小'],
    'medium': ['中等', '百级', '千级', '百个', '千个'],
    'large': ['大规模', '万级', '大样本', '海量', '大数据', '万条'],
}


def load_entries():
    """解析四个正式库为带 _kind 标签的 dict 列表"""
    entries = []
    for kind, path in DB_FILES.items():
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as memory_file:
            txt = memory_file.read()
        for b in re.findall(r'```yaml\n(.*?)\n```', txt, re.S):
            d = {}
            for line in b.splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    d[k.strip()] = v.strip()
            d['_kind'] = kind
            entries.append(d)
    return entries


def _text(e):
    return ' '.join(str(v) for k, v in e.items() if k not in ('_kind', 'failure_id', 'success_id', 'strategy_id', 'decision_id'))


def _bigrams(s):
    """双字重叠集合（描述性指纹 vs 库题型也能命中）"""
    s = re.sub(r'[（(].*?[)）]', '', str(s))
    s = s.replace('/', '')
    return {s[i:i + 2] for i in range(len(s) - 1) if s[i:i + 2].strip()}


def _strong_char_hit(e, fp):
    """强字符命中：仅当条目命中【结构身份】字段（subtype/keywords/secondary）
    或同题先例（source 含 keyword）才算"见过"。
    仅 primary 大类命中（如 problem_type='物理建模' 命中查询 primary='物理建模'）
    视为泛化命中，不计入 n_matched；仅结构信号和强语义命中计入覆盖统计。"""
    blob = _text(e)
    for st in fp.get('subtype', []):
        if st and st in blob:
            return True
    for kw in list(fp.get('keywords', [])) + list(fp.get('secondary', [])):
        if kw and kw in blob:
            return True
    src = e.get('source') or ''
    for kw in fp.get('keywords', []):
        if kw and kw in src:
            return True
    return False


def fingerprint_match_score(e, fp):
    """指纹匹配分：主类命中加分；subtype/keywords 强信号兜底。
    只有主类完全无关且无 subtype/keyword 命中时才剔除。
    ST/DM 条目优先使用 phase/context/scenario 作为类型字段；字段为空时不增加主类得分。"""
    et = (e.get('problem_type') or e.get('phase') or e.get('context') or e.get('scenario') or '').strip()
    primary = fp.get('primary', '')
    blob = _text(e)
    score = 0.0
    if primary:
        if et and (primary in et or et in primary):
            score += 1.0
        elif et:
            pb, eb = _bigrams(primary), _bigrams(et)
            if pb and eb and len(pb & eb) >= max(2, len(min(pb, eb, key=len)) // 2):
                score += 0.7   # 双字重叠过半（如'多目标组合优化' vs '多目标优化'）
    else:
        score += 0.5
    for st in fp.get('subtype', []):
        if st and st in blob:
            score += 0.5   # ⭐ 结构身份强权重（2024B: subtype='生产质检'；2023B: subtype='几何覆盖'）
    for kw in list(fp.get('keywords', [])) + list(fp.get('secondary', [])):
        if kw and kw in blob:
            score += 0.3
    ds = fp.get('data_scale', '')
    if ds in _SCALE_KW:
        for kw in _SCALE_KW[ds]:
            if kw in blob:
                score += 0.2
                break
    for c in fp.get('constraints', []):
        if c in blob:
            score += 0.15
    # ⭐ 同题先例 bonus（FD-522）：关键词命中 entry.source（题目含'穿越沙漠'等）→ 强 boost
    #   教训: ranking 的 reuse×freshness 把低复用/略旧的直接先例压出 TOP-12，被无关泛化条目占据
    src = e.get('source') or ''
    for kw in fp.get('keywords', []):
        if kw and kw in src:
            score += 0.8
            break
    # 主类没命中 + subtype/keywords 也没命中 → 无关，剔除
    return score if score > 0 else 0.0


def _aggregate(ranked, n_matched):
    """把精排后的条目聚合为决策先验"""
    successes = [e for e in ranked if e['_kind'] == 'SD']
    failures = [e for e in ranked if e['_kind'] == 'FD']
    strategies = [e for e in ranked if e['_kind'] == 'ST']
    counter = Counter(e.get('method', '') for e in successes if e.get('method'))
    success_total = len(successes) or 1
    return {
        'n_matched': n_matched,
        'n_top': len(ranked),
        'successful_patterns': [{'pattern': m, 'count': c, 'rate': round(c / success_total, 2)}
                                for m, c in counter.most_common(6)],
        'failed_patterns': [{'method': f.get('method', ''), 'lesson': f.get('lesson', ''),
                             'signal': f.get('signal', '')} for f in failures[:5]],
        'high_risk_actions': [f.get('method', '') for f in failures[:5] if f.get('method')],
        'strategies': [{'scenario': s.get('scenario', ''), 'strategy': s.get('strategy', '')}
                       for s in strategies[:5]],
    }


def _fingerprint_text(fp):
    """Fingerprint → 语义查询文本（primary 出现 3 次加权，突出判别主键）。"""
    parts = [str(fp.get('primary', ''))] * 3
    parts += [str(x) for x in (fp.get('subtype') or [])]
    parts += [str(x) for x in ((fp.get('keywords') or []) + (fp.get('secondary') or []))]
    parts += [str(x) for x in (fp.get('constraints') or [])]
    ds = fp.get('data_scale', '')
    if ds:
        parts.append(str(ds))
    return ' '.join(p for p in parts if p and p.strip())


def _semantic_tier(entries, fingerprint):
    """tier1/tier2 语义层：返回 (tfidf_sims, emb_sims, info)。
    不可用/无文本时返回 None —— 调用方自动回退纯字符检索。"""
    try:
        from memory.semantic import SemanticIndex
    except ModuleNotFoundError:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from semantic import SemanticIndex
    qtext = _fingerprint_text(fingerprint)
    if not qtext.strip():
        return None
    idx = SemanticIndex(entries).build(embedding=bool(os.environ.get('CONTEST_SEMANTIC_EMBEDDING')))
    n = len(entries)
    tfidf = [0.0] * n
    for sim, i in idx.query(qtext, top_k=0):
        tfidf[i] = sim
    emb = [0.0] * n
    if idx.embeddings is not None:
        for sim, i in idx.query_embedding(qtext, top_k=0):
            emb[i] = sim
    return tfidf, emb, {
        'tier': 'embedding' if idx.embeddings is not None else 'tfidf',
        'index_entries': n,
        'vocab': len(idx.idf),
        'build_ms': idx.build_ms,
    }


def _score_candidates(entries, fingerprint, use_semantic=True, current_year=2026):
    """共享打分管线：tier0 字符 + tier1/2 语义 → 混合分候选列表。
    返回 (scored, n_char, n_char_strong, n_expand, sem_info)。
    scored 元素 = (hybrid_sim, char_sim, tfidf_sim, emb_sim, entry)
    n_char：全部字符命中（含仅 primary 大类的泛化命中，诊断用）
    n_char_strong：强字符命中（结构身份或同题先例命中，用于状态计数）"""
    char_scores = [fingerprint_match_score(e, fingerprint) for e in entries]
    n_char = sum(1 for c in char_scores if c > 0)
    strong_flags = [_strong_char_hit(e, fingerprint) for e in entries]
    n_char_strong = sum(1 for c, s in zip(char_scores, strong_flags) if c > 0 and s)

    tfidf = emb = None
    sem_info = {'tier': 'off'}
    if use_semantic:
        try:
            tfidf, emb, sem_info = _semantic_tier(entries, fingerprint)
        except Exception as exc:  # 语义层任何故障都不应中断检索
            sem_info = {'tier': 'off', 'error': str(exc)[:120]}

    scored = []
    n_expand = 0
    tfidf_max = max(tfidf) if tfidf else 0.0
    expand_floor = max(SEMANTIC_GATE, SEMANTIC_REL * tfidf_max)
    for i, e in enumerate(entries):
        c = char_scores[i]
        t = tfidf[i] if tfidf else 0.0
        v = emb[i] if emb else 0.0
        if c > 0:
            scored.append((c + SEMANTIC_WEIGHT * t + 0.5 * v, c, t, v, e))
        elif use_semantic and t >= expand_floor and n_expand < SEMANTIC_EXPAND_MAX:
            n_expand += 1
            scored.append((SEMANTIC_WEIGHT * t + 0.5 * v, 0.0, t, v, e))
    return scored, n_char, n_char_strong, n_expand, sem_info


def _bucket_of(sim):
    """分档：相似度是绝对门槛。"""
    if sim >= BUCKET_A:
        return 0
    if sim >= BUCKET_B:
        return 1
    if sim >= BUCKET_C:
        return 2
    return 3


def _source_diversity(scored):
    """来源多样性：同一 source 在候选集出现 ≥3 次 → 该来源全部 ×0.8。
    评审证据：Q14 设施选址 top-12 被 7 条同一场华数杯 C 电力调度 DM 霸榜。"""
    from collections import Counter
    cnt = Counter(e.get('source', '') for _, _, _, _, e in scored)
    return {src: (DIVERSITY_PENALTY if c >= DIVERSITY_SOURCE_MIN else 1.0)
            for src, c in cnt.items()}


# ---- 竞赛类型过滤（Task 8）----
CONTEST_MATCH_WEIGHT = 1.10   # 匹配目标竞赛类型的档内加权
CONTEST_MISMATCH_WEIGHT = 0.95  # 不匹配目标竞赛类型的档内降权
CONTEST_UNKNOWN_WEIGHT = 1.0   # 未知竞赛类型保持中性


def _contest_match_weight(entry, contest_filter):
    """有界竞赛类型加权：只在同一相关档内参与排序，不跨档压过高相关条目。

    contest_filter=None → 全部中性 1.0；
    匹配（含 CM-* 通配）→ 1.10；不匹配 → 0.95；未知 → 1.0。
    """
    if not contest_filter:
        return CONTEST_UNKNOWN_WEIGHT
    entry_type = str(entry.get('contest_type', '') or '').strip()
    if not entry_type:
        return CONTEST_UNKNOWN_WEIGHT
    if contest_filter.endswith('*'):
        prefix = contest_filter[:-1]
        if entry_type.startswith(prefix):
            return CONTEST_MATCH_WEIGHT
        return CONTEST_MISMATCH_WEIGHT
    if entry_type == contest_filter:
        return CONTEST_MATCH_WEIGHT
    return CONTEST_MISMATCH_WEIGHT


def _contest_filter_stats(entries, contest_filter):
    """统计竞赛类型过滤结果：匹配数、不匹配数、未知数。"""
    if not contest_filter:
        return {'contest_filter': None, 'matched_contest_count': 0,
                'unmatched_contest_count': 0, 'unknown_contest_count': 0}
    matched = unmatched = unknown = 0
    for entry in entries:
        entry_type = str(entry.get('contest_type', '') or '').strip()
        if not entry_type:
            unknown += 1
        elif contest_filter.endswith('*') and entry_type.startswith(contest_filter[:-1]):
            matched += 1
        elif entry_type == contest_filter:
            matched += 1
        else:
            unmatched += 1
    return {
        'contest_filter': [contest_filter],
        'matched_contest_count': matched,
        'unmatched_contest_count': unmatched,
        'unknown_contest_count': unknown,
    }


def rank_and_cut(scored, top, current_year=2026, contest_filter=None):
    """分档 tie-breaker 排序：
    ① 相似度定档（A/B/C/D，绝对门槛）→ ② 档内按 rank_score（有界 metadata）× 来源多样性 × 竞赛类型加权 排序。
    元数据只在同一相关档内竞争，不能跨档否决语义相关性；档内使用有界 rank_score。
    contest_filter 只在档内参与加权，不改变候选集合和分档。"""
    div = _source_diversity(scored)
    scored.sort(key=lambda x: (_bucket_of(x[0]),
                               -rank_score(x[0], x[4], current_year=current_year)
                               * div.get(x[4].get('source', ''), 1.0)
                               * _contest_match_weight(x[4], contest_filter)))
    return scored


def _retrieval_status(n_matched):
    """覆盖置信度：rich/normal/weak/cold_start。
    Planner 行为随档位变化——系统必须知道自己没见过，不能假装见过。"""
    if n_matched >= STATUS_RICH:
        return 'rich'
    if n_matched >= STATUS_NORMAL:
        return 'normal'
    if n_matched >= STATUS_WEAK:
        return 'weak'
    return 'cold_start'


_STATUS_GUIDANCE = {
    'rich': '历史经验充足，可作为强先验：优先复用成功模式，严格规避失败警示。',
    'normal': '历史经验可参考：成功模式作候选，保留架构探索空间，失败警示仍须规避。',
    'weak': '历史覆盖弱：经验仅作避坑信息，不得作为强先验；建模以第一性原理为主。',
    'cold_start': '库中无相关经验：禁止生成"历史表明…"类强结论；走通用方法论+文献先行。',
}


def _generic_entries(entries, exclude_ids, k):
    """冷启动补位：候选不足时补通用条目（problem_type/scenario 含 任意/通用），
    让 Planner 至少拿到方法论级兜底，而非空先验。exclude_ids = {id(entry)}。"""
    out = []
    for e in entries:
        if id(e) in exclude_ids:
            continue
        pt = e.get('problem_type') or ''
        sc = e.get('scenario') or ''
        if '任意' in pt or '通用' in pt or '任意题' in sc:
            out.append(e)
            if len(out) >= k:
                break
    return out


def get_experience_coverage(fingerprint, top=12, current_year=2026, entries=None):
    """覆盖统计：
    回答"这道题我见过多少、经验有多深"。
    返回 dict：count / high_quality / verified / human_replay / decision_trace /
    failure / strategy / specific_count / top_source_ratio / actionability /
    confidence / retrieval_status。
    count = char 命中 + 强语义命中（弱语义匹配不算"见过"，与 retrieve() 状态口径一致）。
    specific_count = 候选里正文含 subtype/关键词的条目数——
    区分"泛化题型命中"（如'优化决策'类）与"题面特有经验"（如'测线'集群），选题层据此打分。
    top_source_ratio / actionability = 来源集中度 / 经验粒度可行动性（选题层用）。
    entries 可注入预加载条目，缺省使用 load_entries()。"""
    if entries is None:
        entries = load_entries()
    scored, n_char, n_char_strong, n_expand, _ = _score_candidates(entries, fingerprint, True, current_year)
    strong_sem = sum(1 for _, c, t, _, _ in scored if c == 0 and t >= SEMANTIC_STRONG)
    n_matched = n_char_strong + strong_sem
    ranked = rank_and_cut(scored, top, current_year)
    # 与 retrieve() 相同的降级口径：weak/cold 时只统计强相关条目
    st = _retrieval_status(n_matched)
    if st in ('weak', 'cold_start'):
        cand = [e for _, c, t, _, e in ranked[:top] if c > 0 or t >= SEMANTIC_STRONG]
    else:
        cand = [e for _, _, _, _, e in ranked[:top]]

    # 特异性：候选正文含 subtype/关键词（题面特有词）的条目数
    _specific_tokens = list(fingerprint.get('subtype') or []) \
        + list(fingerprint.get('keywords') or []) + list(fingerprint.get('secondary') or [])
    specific_count = 0
    if _specific_tokens:
        for e in cand:
            blob = ' '.join(str(v) for v in e.values() if v)
            if any(tok and tok in blob for tok in _specific_tokens):
                specific_count += 1

    def _q(e, key):
        qs = e.get('quality_score') or {}
        v = qs.get(key)
        return v if v is not None else e.get(key)

    high_quality = sum(1 for e in cand if _q(e, 'source_quality') == '高' or _q(e, 'quality') == '高')
    verified = sum(1 for e in cand if _q(e, 'verified'))
    human_replay = sum(1 for e in cand if e.get('memory_type') == 'human_replay')
    decision_trace = sum(1 for e in cand if e.get('_kind') == 'DM')
    failure = sum(1 for e in cand if e.get('_kind') == 'FD')
    strategy = sum(1 for e in cand if e.get('_kind') == 'ST')
    # 来源集中度：不依赖指纹质量
    #   top-12 里同一 source 的最大占比——经验集中=真的做过这类题；分散=泛化命中
    from collections import Counter
    src_counter = Counter(e.get('source', '') for e in cand)
    top_source_ratio = round(max(src_counter.values()) / max(1, len(cand)), 3) if cand else 0.0
    # 可行动性：区分同一覆盖档位内的经验粒度
    #   经验类型加权 DM=1.0 / ST=0.7 / FD=0.6 / SD=0.4（决策级最可行动，成功级最参考性）
    _TYPE_W = {'DM': 1.0, 'ST': 0.7, 'FD': 0.6, 'SD': 0.4}
    actionability = round(sum(_TYPE_W.get(e.get('_kind'), 0.5) for e in cand) / max(1, len(cand)), 3) if cand else 0.0
    status = _retrieval_status(n_matched)
    hq_ratio = (high_quality / len(cand)) if cand else 0.0
    confidence = round(min(1.0, n_matched / STATUS_RICH) * (0.5 + 0.5 * hq_ratio), 3)
    return {
        'count': n_matched,
        'high_quality_count': high_quality,
        'verified_count': verified,
        'human_replay_count': human_replay,
        'decision_trace_count': decision_trace,
        'failure_coverage': failure,
        'strategy_coverage': strategy,
        'specific_count': specific_count,
        'top_source_ratio': top_source_ratio,
        'actionability': actionability,
        'confidence': confidence,
        'retrieval_status': status,
    }


def retrieve(fingerprint, top=12, current_year=2026, use_semantic=True, entries=None, contest_filter=None):
    """入口：fingerprint 为 dict，见 problem_parser.md 的 Problem Fingerprint。
    use_semantic=False → 纯字符检索（A/B 对照用）。
    entries 可注入预加载条目（benchmark/测试用），缺省内部 load_entries()。
    contest_filter 可选竞赛类型过滤（如 'CM-B'、'CM-*'），只在同一相关档内参与排序加权，不改变候选集合和分档。
    输出 prior['retrieval_status']（rich/normal/weak/cold_start + 行为指引）、
    prior['experience_coverage']（覆盖分层统计，含 contest_filter 统计）。"""
    if entries is None:
        entries = load_entries()

    scored, n_char, n_char_strong, n_expand, sem_info = _score_candidates(entries, fingerprint, use_semantic, current_year)
    # 状态计数：强字符命中（结构身份/同题先例）+ 强语义命中
    strong_sem = sum(1 for _, c, t, _, _ in scored if c == 0 and t >= SEMANTIC_STRONG)
    n_matched = n_char_strong + strong_sem

    ranked_sorted = rank_and_cut(scored, top, current_year, contest_filter=contest_filter)
    ranked_all = [e for _, _, _, _, e in ranked_sorted[:top]]

    # ---- 冷启动/弱覆盖降级：保留通用方法论，剔除弱命中噪声 ----
    status = _retrieval_status(n_matched)
    if status in ('weak', 'cold_start'):
        # 仅保留强相关候选（char 命中 或 强语义），剔除弱语义命中（噪声）
        ranked = [e for _, c, t, _, e in ranked_sorted[:top]
                  if c > 0 or t >= SEMANTIC_STRONG]
        if len(ranked) < min(top, 6):
            ranked = ranked + _generic_entries(entries, {id(e) for e in ranked},
                                               min(top, COLD_FILL) - len(ranked))
    else:
        ranked = ranked_all

    prior = _aggregate(ranked, n_matched)
    prior['fingerprint_used'] = {
        'primary': fingerprint.get('primary', ''),
        'subtype': fingerprint.get('subtype', []),
        'keywords': list(fingerprint.get('keywords', [])) + list(fingerprint.get('secondary', [])),
        'data_scale': fingerprint.get('data_scale', ''),
    }
    prior['semantic'] = {
        **sem_info,
        'char_hits': n_char,
        'char_hits_strong': n_char_strong,
        'semantic_expansion': n_expand,
        'n_candidates': len(scored),
    }
    prior['retrieval_status'] = {
        'level': status,
        'n_matched': n_matched,
        'guidance': _STATUS_GUIDANCE[status],
    }
    prior['experience_coverage'] = get_experience_coverage(fingerprint, top, current_year)
    if contest_filter:
        prior['experience_coverage'].update(_contest_filter_stats(ranked, contest_filter))
    return prior


if __name__ == '__main__':
    # 自测：预测类 + 时序 + 小样本
    fp = {'primary': '预测', 'keywords': ['时序', '时间序列', 'LSTM', 'ARIMA'], 'data_scale': 'small',
          'constraints': ['非平稳']}
    prior = retrieve(fp)
    print('命中条目数:', prior['n_matched'])
    print('成功模式:', prior['successful_patterns'][:3])
    print('高风险动作:', prior['high_risk_actions'][:3])
    print('失败警示数:', len(prior['failed_patterns']))
    print('语义层:', prior['semantic'])
