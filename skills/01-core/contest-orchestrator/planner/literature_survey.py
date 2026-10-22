#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
planner/literature_survey.py — 文献调研模块（方案B核心）

输入：Problem Graph + Problem Fingerprint（来自 problem_parser.md）
输出：
  ① literature_report.md    — 五段式标准化文献调研审计报告（正文按需提炼，不整段复制）
  ② references.yaml         — 结构化参考文献列表（供写作阶段引用）
  ③ citation_map.json       — 章节→引用的映射表（D3 写作对照清单）
  ④ method_transfer_map.json — 文献方法→各子问题建模/求解的迁移与创新登记

文献来源：由用户负责检索和下载。主 Agent 只接收用户提交的题名、作者、来源、年份、DOI/链接、摘要
和文献 agent 的结构化全文总结，只基于这些回传内容做候选筛选、题目覆盖分析和引用登记；不主动联网检索，
不读取或解析文献全文。
文献数量和小问覆盖要求先写入 `literature_request.md` 与 `literature_request.yaml`；未收到用户文献元数据前保持 PAUSE。

流程：
  step1 → 生成中英文数量、角色和小问覆盖需求卡
  step2 → 等待用户提交文献元数据与摘要
  step3 → 仅基于摘要提炼 {core_method, applicable_to, key_result, limitation, strength}
  step4 → 按方法大类分类归纳（不按人名罗列）
  step5 → 识别研究缺口
  step6 → 生成五段式报告 + references.yaml + citation_map.json + method_transfer_map.json
  step7 → 写入 competition_replay/<竞赛>_<年份>_<题号>/ 目录

用法:
    from planner.literature_survey import run_survey
    results = run_survey(problem_graph, fingerprint, competition='cumcm', year=2026, qn='A')
"""

import argparse
import json
import os
import re
import hashlib
import tempfile
from datetime import datetime, timedelta
from collections import defaultdict

try:
    import urllib.request
    import urllib.parse
    import ssl
except ImportError:
    pass

try:
    import yaml
except ImportError:  # pragma: no cover - the health check reports this dependency
    yaml = None

try:
    # Windows consoles may default to GBK; literature metadata and pause
    # diagnostics contain Chinese text and must not crash the hard gate.
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

# ---- 配置 ----
API_TIMEOUT = 15  # 每个 API 请求超时秒数
MAX_RESULTS_PER_SOURCE = 8  # 每源最多取多少篇
MERGE_THRESHOLD = 0.8  # 标题相似度阈值（去重用）

# 文献分布规则（优先导向 + 运行时容错，非硬限制）
# 采用“期望目标 + 容错回退 + 诚实说明”，不将建议目标伪装成硬性配额。
# 原则：不伪造、不凑数、不足4篇时如实标注。
LIT_DISTRIBUTION = {
    'theoretical': {'target_min': 4, 'target_max': 7},  # 理论类期望值
    'application':  {'target_min': 3, 'target_max': 5},  # 应用类期望值
    'competition_paper': {'target_min': 0, 'target_max': 2},  # 竞赛论文可空缺
}
TOTAL_MIN = 6
TOTAL_MAX = 11
RECOMMENDED_TOTAL_MIN = 8
RECOMMENDED_TOTAL_MAX = 10
ENGLISH_MIN = 0

# ---- 分类用关键词表（_enforce_distribution_limits 内部引用） ----
_THEO_KEYWORDS = [
    'genetic algorithm', 'evolutionary', 'heuristic', 'simulated annealing',
    'particle swarm', 'integer program', 'mixed integer', 'mip', 'ilp',
    'dynamic programming', 'reinforcement learn', 'lstm', 'cnn',
    'transformer', 'bayesian', 'monte carlo', 'markov chain',
    'ode', 'pde', 'differential equation', 'system dynamics',
    'aHP', 'analytic hierarchy', 'tocosys', 'entropy weight',
    'robust optim', 'stochastic program', 'chance constra',
    'multi-objective', 'pareto', 'linear program', 'nonlinear program',
    'time series', 'ARIMA', 'prophet', 'forecasting',
]
_APP_KEYWORDS = [
    'supply chain', 'logistics', 'production scheduling', 'facility location',
    'vehicle routing', 'portfolio optimization', 'energy management',
    'healthcare', 'medical', 'financial', 'risk management',
    'manufacturing', 'process optimization', 'quality control',
    'transportation', 'traffic flow', 'telecommunication',
    'water management', 'electric power', 'renewable energy',
    'smart grid', 'cloud computing', 'data center',
    'project scheduling', ' workforce scheduling', 'staff scheduling',
    'inventory', 'warehouse', 'distribution network',
]
_COMP_KEYWORDS = [
    'mathematical modeling competition', 'cumcm', 'mcm', 'huashu cup',
    '全国大学生数学建模', '美国大学生数学建模', '华数杯',
    '优秀论文', '获奖论文', 'cumlcm',
]
# _THEO_KEYWORDS 等关键词表定义在 LIT_DISTRIBUTION 下方，供内部分类使用。

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_replay_root(replay_root: str | None) -> str:
    """Resolve a project-owned replay root without writing into the skill tree.

    Explicit caller input wins, followed by ``CONTEST_WORKSPACE_ROOT``.  The
    current working directory is only a convenience for callers that already
    run inside a project.  Running from the skill root without either input is
    rejected rather than silently recreating ``competition_replay/`` here.
    """
    candidate = replay_root or os.environ.get('CONTEST_WORKSPACE_ROOT') or os.getcwd()
    resolved = os.path.abspath(os.path.expanduser(candidate))
    if os.path.normcase(resolved) == os.path.normcase(SKILL_ROOT):
        raise ValueError(
            '缺少项目 replay 根目录：请传入 replay_root 或设置 '
            'CONTEST_WORKSPACE_ROOT；禁止把运行产物写入技能安装目录。'
        )
    return resolved


def _citation_key_for(title: object, authors: object, year: object, prefix: str = 'ref') -> str:
    """Build a deterministic BibTeX key when the user did not provide one."""
    raw = '|'.join(str(value or '').strip() for value in (title, authors, year))
    digest = hashlib.sha1(raw.encode('utf-8')).hexdigest()[:8]
    year_text = re.sub(r'[^0-9]', '', str(year or ''))[-4:] or 'nd'
    return f'{prefix}_{year_text}_{digest}'


def _method_pattern_hit(pattern: str, text: str) -> bool:
    """Match short ASCII abbreviations as tokens, not substrings.

    This prevents false positives such as ``ode`` inside ``model`` and ``sa``
    inside ``solar`` observed in the A题 replay.
    """
    pattern = str(pattern or '').strip()
    if not pattern:
        return False
    if _has_cjk(pattern):
        return pattern.lower() in text.lower()
    if len(pattern) <= 4:
        return bool(re.search(r'(?<![a-z0-9])' + re.escape(pattern) +
                              r'(?![a-z0-9])', text, re.I))
    return pattern.lower() in text.lower()


def _generate_search_queries(fingerprint):
    """从 Fingerprint 生成中英文检索关键词组。

    每个 query pair 对应一个研究方向，用于跨源并行搜索。
    """
    queries = []
    primary = fingerprint.get('primary', '')
    subtype = fingerprint.get('subtype', [])
    keywords = fingerprint.get('keywords', [])
    secondary = fingerprint.get('secondary', [])
    constraints = fingerprint.get('constraints', [])
    objective = fingerprint.get('objective', '')

    # --- 中文映射表 ---
    EN_TO_ZH = {
        'optimization': '优化',
        'prediction': '预测',
        'classification': '分类评价',
        'regression': '回归分析',
        'graph_model': '图模型',
        'mechanism_model': '机理建模',
        'physics_modeling': '物理建模',
        'scheduling': '排程调度',
        'location': '选址',
        'routing': '路径规划',
        'resource_allocation': '资源配置',
        'time_series': '时间序列',
        'deep_learning': '深度学习',
        'reinforcement_learning': '强化学习',
        'genetic_algorithm': '遗传算法启发式',
        'evolutionary_computation': '进化计算',
        'monte_carlo': '蒙特卡洛模拟',
        'integer_programming': '整数规划',
        'dynamic_programming': '动态规划',
        'linear_programming': '线性规划',
        'nonlinear_programming': '非线性规划',
        'multi_objective': '多目标',
        'robust_optimization': '鲁棒优化',
    }

    # 提取主题关键词
    zh_primary = EN_TO_ZH.get(primary.lower(), primary) if primary else ''
    sub_keywords = [s if isinstance(s, str) else '' for s in (subtype or [])]
    main_keywords = [k if isinstance(k, str) else '' for k in (keywords or [])]
    sec_keywords = [k if isinstance(k, str) else '' for k in (secondary or [])]
    const_keywords = [c if isinstance(c, str) else '' for c in (constraints or [])]

    all_kw = [zh_primary] + sub_keywords + main_keywords + sec_keywords + const_keywords
    all_kw = [k.strip() for k in all_kw if k.strip()]

    if not all_kw:
        return [{'en': 'mathematical modeling', 'zh': '数学建模'}]

    # 生成多个查询方向
    # 方向1：主类 + subtype（最精准）
    if all_kw:
        queries.append({
            'en': f'{" AND ".join(all_kw[:3])}',
            'zh': f'{" AND ".join(all_kw[:3])}',
            'direction_zh': f'{all_kw[0]}类问题的{all_kw[-1] if len(all_kw) > 1 else "通用"}方法',
        })

    # 方向2：主类 + 约束类型（广搜）
    if const_keywords:
        queries.append({
            'en': f'{EN_TO_ZH.get(const_keywords[0].lower(), const_keywords[0])} {" ".join(all_kw[:2])}',
            'zh': f'{const_keywords[0]} {all_kw[0]}',
            'direction_zh': f'带{const_keywords[0]}约束的{all_kw[0]}问题',
        })

    # 方向3：仅主类（兜底广搜）
    if zh_primary:
        queries.append({
            'en': zh_primary,
            'zh': zh_primary,
            'direction_zh': f'{zh_primary}相关问题综述或方法论',
        })

    return queries


def _fetch_arxiv(query_en, max_results=MAX_RESULTS_PER_SOURCE):
    """arXiv API — 免费，无需key，返回XML。"""
    url = f'http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query_en)}&max_results={max_results}&sortBy=submittedDate&sortOrder=descending'
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={'User-Agent': 'MathModel-Agent/1.0'})
        resp = urllib.request.urlopen(req, timeout=API_TIMEOUT, context=ctx)
        xml_data = resp.read().decode('utf-8')
        return _parse_arxiv_xml(xml_data)
    except Exception as e:
        print(f'[arXiv] 检索失败: {query_en[:50]}... → {str(e)[:80]}')
        return []


def _parse_arxiv_xml(xml_data):
    """解析 arXiv XML → 标准化列表。"""
    papers = []
    title_pat = re.compile(r'<title>(.*?)</title>')
    abstract_pat = re.compile(r'<summary>(.*?)</summary>', re.DOTALL)
    link_pat = re.compile(r'<id>(http[^<]+)</id>')
    published_pat = re.compile(r'<published>([^<]+)</published>')
    author_pat = re.compile(r'<name>([^<]+)</name>')

    # 简单分割 entry
    entries = re.split(r'<entry>', xml_data)
    for entry in entries[1:]:  # skip first dummy
        title_m = title_pat.search(entry)
        abstract_m = abstract_pat.search(entry)
        link_m = link_pat.search(entry)
        published_m = published_pat.search(entry)
        authors_m = author_pat.findall(entry)

        if not title_m:
            continue

        title = re.sub(r'\s+', ' ', title_m.group(1)).strip()
        abstract = re.sub(r'\s+', ' ', abstract_m.group(1)).strip() if abstract_m else ''
        link = link_m.group(1).strip() if link_m else ''
        pub_date = published_m.group(1).strip() if published_m else ''
        authors = [a.strip() for a in authors_m[:5]]

        # 提取年份
        year = ''
        if pub_date:
            m = re.search(r'(\d{4})', pub_date)
            if m:
                year = m.group(1)

        papers.append({
            'source': 'arxiv',
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'year': year,
            'link': link,
            'arxiv_id': link.split('/')[-1] if link else '',
        })

    return papers


def _fetch_crossref(query_en, max_results=MAX_RESULTS_PER_SOURCE):
    """CrossRef REST API — 免费，返回JSON，覆盖期刊论文。"""
    url = f'https://api.crossref.org/works?query={urllib.parse.quote(query_en)}&rows={max_results}&select=title,author,published-print,published-online,abstract,is-referenced-by-count,container-title,DOI&sort=published-print&order=desc'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'MathModel-Agent/1.0 (mathmodel-agent@example.com)',
            'Accept': 'application/json',
        })
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, timeout=API_TIMEOUT, context=ctx)
        data = json.loads(resp.read().decode('utf-8'))
        return _parse_crossref_response(data, query_en)
    except Exception as e:
        print(f'[CrossRef] 检索失败: {query_en[:50]}... → {str(e)[:80]}')
        return []


def _parse_crossref_response(data, original_query):
    """解析 CrossRef JSON → 标准化列表。"""
    papers = []
    items = data.get('message', {}).get('items', [])
    for item in items:
        titles = item.get('title', [])
        abstract = item.get('abstract', '')
        authors_list = item.get('author', [])
        authors = [f'{a.get("given", "")} {a.get("family", "")}'.strip()
                   for a in authors_list[:5] if a.get('family')]
        date_parts = item.get('published-print', {}).get('date-parts', [[]])
        year = str(date_parts[0][0]) if date_parts and date_parts[0] else ''
        journal = ', '.join(item.get('container-title', []))
        doi = item.get('DOI', '')
        cited_by = item.get('is-referenced-by-count', 0)

        titles_clean = [re.sub(r'\s+', ' ', t).strip() for t in titles if t.strip()]
        abstract_clean = re.sub(r'\s+', ' ', abstract).strip() if abstract else ''

        papers.append({
            'source': 'crossref',
            'title': titles_clean[0] if titles_clean else f'Unknown ({original_query})',
            'abstract': abstract_clean,
            'authors': authors,
            'year': year,
            'journal': journal,
            'doi': doi,
            'link': f'https://doi.org/{doi}' if doi else '',
            'cited_by': cited_by,
            'type': 'journal_article',
        })
    return papers


def _fetch_semantic_scholar(query_en, max_results=MAX_RESULTS_PER_SOURCE):
    """Semantic Scholar API — 免费，返回JSON。"""
    url = f'https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query_en)}&limit={max_results}&fields=title,abstract,authors,year,publicationTypes,citationCount,venue,externalIds'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'MathModel-Agent/1.0',
            'Accept': 'application/json',
        })
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, timeout=API_TIMEOUT, context=ctx)
        data = json.loads(resp.read().decode('utf-8'))
        return _parse_s2_response(data)
    except Exception as e:
        print(f'[SemanticScholar] 检索失败: {query_en[:50]}... → {str(e)[:80]}')
        return []


def _parse_s2_response(data):
    """解析 Semantic Scholar JSON → 标准化列表。"""
    papers = []
    for item in data.get('data', []):
        authors = [a.get('name', '') for a in (item.get('authors', [])[:5])]
        year = str(item.get('year', '')) or ''
        external_ids = item.get('externalIds', {})
        doi = external_ids.get('DOI', '')
        arxiv_id = external_ids.get('ArXiv', '')
        venue = item.get('venue', '')
        cited_by = item.get('citationCount', 0)

        papers.append({
            'source': 'semantic_scholar',
            'title': re.sub(r'\s+', ' ', item.get('title', '')).strip(),
            'abstract': re.sub(r'\s+', ' ', item.get('abstract', '') or '').strip(),
            'authors': authors,
            'year': year,
            'venue': venue,
            'doi': doi,
            'arxiv_id': arxiv_id,
            'link': f'https://www.semanticscholar.org/paper/{item.get("paperId", "")}'
                    if item.get('paperId') else '',
            'cited_by': cited_by,
            'type': 'conference' if item.get('publicationTypes') == ['Conference'] else 'other',
        })
    return papers


def _deduplicate(papers):
    """基于标题相似度的去重（Jaccard on character bigrams）。"""
    def _bigram(s):
        s = re.sub(r'[^\w\s\u4e00-\u9fff]', '', s.lower())
        return set(s[i:i+2] for i in range(len(s)-1))

    seen_titles = []
    unique = []
    for p in papers:
        is_dup = False
        pb = _bigram(p['title'])
        for st in seen_titles:
            sa = _bigram(st)
            if sa and len(sa & pb) / len(sa | pb) >= MERGE_THRESHOLD:
                is_dup = True
                break
        if not is_dup:
            seen_titles.append(p['title'])
            unique.append(p)
    return unique


def _rank_papers(papers):
    """综合评分排序：cited_by(0.4) + recency(0.3) + source_quality(0.3)。"""
    current_year = int(datetime.now().strftime('%Y'))

    def score(p):
        cited = p.get('cited_by', 0)
        # log-scale citations
        s_cite = min(1.0, (cited ** 0.4) / 10)

        # recency
        year = int(p.get('year', 0) or 0)
        if year >= current_year - 3:
            s_rec = 1.0
        elif year >= current_year - 5:
            s_rec = 0.7
        elif year >= current_year - 10:
            s_rec = 0.4
        else:
            s_rec = 0.1

        # source quality bonus
        source_bonus = {'crossref': 0.1, 'semantic_scholar': 0.05, 'arxiv': 0.0}
        s_source = source_bonus.get(p.get('source', ''), 0)

        return s_cite * 0.4 + s_rec * 0.3 + s_source * 0.3

    papers.sort(key=score, reverse=True)
    return papers


def _extract_insights(papers, problem_graph, fingerprint):
    """从摘要和用户文献 agent 的结构化全文总结中提取可迁移点。"""
    insights = []

    # --- 方法类别映射表（标题/摘要中常见的模式词 → 方法大类）---
    METHOD_PATTERNS = {
        '启发式优化': ['genetic', 'ga', 'evolut', 'heuristic', 'simulated annealing', 'sa',
                        'particle swarm', 'psoswa', 'ant colony', 'tabu search', 'immune',
                        'metaheuristic', 'adaptive search', '遗传算法', '差分进化', '启发式',
                        '元启发式', '模拟退火', '粒子群', '蚁群算法', '禁忌搜索', '引力搜索',
                        '白冠鸡', '灰狼', '鲸鱼', '萤火虫', '蝙蝠算法', '混合优化', '优化布置',
                        '优化布局', '布局优化'],
        '整数规划/MIP': ['integer program', 'mixed integer', 'mip', 'ilp', 'branch and bound',
                          'column generation', 'cutting plane', '整数规划', '混合整数', '线性规划'],
        '动态规划': ['dynamic programming', 'dp', 'markov decision', 'mdp', 'bellman', '动态规划', '状态决策'],
        '强化学习': ['reinforcement learn', 'rl', 'policy gradient', 'q-learning', 'dqn',
                      'actor-critic', 'multi-agent reinforcement'],
        '深度学习/NLP': ['deep learn', 'lstm', 'cnn', 'transformer', 'attention', 'bert',
                          'neural network', 'graph neural', 'gcn', 'gan', '深度学习', '神经网络'],
        '统计/回归': ['regress', 'bayesian', 'markov chain', 'monte carlo', 'mcmc',
                       'linear model', 'logistic', 'poisson', 'time series', '回归', '贝叶斯', '蒙特卡洛', '时间序列'],
        '图论/网络': ['graph', 'network', 'shortest path', 'matching', 'flow', 'spectral'],
        '微分方程/ODE/PDE': ['ode', 'pde', 'differential equation', 'continuous model',
                              'system dynamics', 'Lotka-Volterra'],
        '综合评价/多准则': ['aHP', 'analytic hierarchy', 'tocosys', 'entropy weight',
                             'evaluation index', 'decision making', 'multi-criteria', '层次分析', '熵权', '综合评价'],
        '鲁棒/随机优化': ['robust optim', 'stochastic program', 'chance constra',
                           'scenario-based', 'distributionally robust', 'uncertainty', '鲁棒优化', '随机规划', '情景分析', 'CVaR'],
    }

    PRIMARY_METHODS = {
        '优化决策': '启发式优化|整数规划|MIP|动态规划|整数规划',
        '预测': '深度学习/NLP|统计/回归|时间序列|ARIMA|LSTM|Prophet',
        '评价分类': '综合评价/多准则|聚类分析|判别分析|支持向量机',
        '物理建模': '微分方程/ODE/PDE|有限元|机理建模',
        '机理建模': '微分方程/ODE/PDE|系统动力学',
        '图模型': '图论/网络|谱聚类|社区发现',
    }

    for p in papers:
        text_lower = (p.get('title', '') + ' ' + p.get('abstract', '') + ' '
                      + p.get('method_summary', '') + ' ' + p.get('use_in_paper', '')).lower()

        # 1. 匹配方法类别
        matched_methods = list(p.get('methods', p.get('matched_methods', [])) or [])
        for method_name, patterns in METHOD_PATTERNS.items():
            for pat in patterns:
                if _method_pattern_hit(pat, text_lower):
                    matched_methods.append(method_name)
                    break
            if len(matched_methods) >= 2:
                break

        if not matched_methods:
            # 尝试与本题主类的默认方法匹配
            primary = fingerprint.get('primary', '')
            default_map = PRIMARY_METHODS.get(primary, '')
            if default_map:
                matched_methods = [default_map.split('|')[0]]

        matched_methods = list(dict.fromkeys(matched_methods))  # 去重保序

        # 2. 推断适用子问题（从 fingerprint 推导）
        declared_questions = p.get('candidate_questions', p.get('candidate_relevance', []))
        if isinstance(declared_questions, str):
            declared_questions = [declared_questions]
        applicable_to = list(dict.fromkeys(
            str(item).upper() for item in (declared_questions or [])
            if str(item).upper().startswith('Q')
        ))
        qn_list = problem_graph.get('questions', [])
        if not applicable_to and qn_list:
            for i, q in enumerate(qn_list, 1):
                q_text = str(q).lower()
                # 简单的关键词重叠判断
                fp_kw = fingerprint.get('keywords', [])
                overlap = sum(1 for kw in fp_kw if isinstance(kw, str) and kw.lower() in q_text)
                if overlap >= 1 or i <= 2:  # 前2问默认相关
                    applicable_to.append(f'Q{i}')

        if not applicable_to:
            applicable_to = ['Q1']  # 兜底

        # 3. 估算关键结果（从摘要中提取数字）
        key_result = ''
        numbers_in_abstract = re.findall(r'(\d+(?:\.\d+)?)\s*%', p.get('abstract', ''))
        if numbers_in_abstract:
            key_result = f'性能提升约 {numbers_in_abstract[0]}%'

        # 4. 主观局限推断
        limitation = p.get('limitations', '')
        abstract_lower = p.get('abstract', '').lower()
        if any(w in abstract_lower for w in ['limited', 'small sample', 'synthetic', 'toy',
                                                'simplified', 'idealized', 'assum']):
            limitation = '实验数据可能过于理想化，实际场景泛化性待验证'
        elif any(w in abstract_lower for w in ['future work', 'ongoing', 'preliminary',
                                                 'need further', 'remains open']):
            limitation = '作者自认工作不完整，核心结论可能有待补充'

        # 5. 优势推断
        strength = ''
        if p.get('cited_by', 0) > 50:
            strength = f'高被引({p["cited_by"]}次)，方法经广泛认可'
        elif p.get('year', '') and int(p.get('year', 0) or 0) >= int(datetime.now().strftime('%Y')) - 2:
            strength = '近期发表，反映最新研究进展'

        insights.append({
            'paper_index': len(insights) + 1,  # 临时索引，最终用 ref_ID
            'title': p['title'],
            'source': p.get('source', 'unknown'),
            'authors': ', '.join(p.get('authors', [])),
            'year': p.get('year', ''),
            'journal': p.get('journal', p.get('venue', '')),
            'volume_issue_pages': p.get('volume_issue_pages', ''),
            'link': p.get('link', ''),
            'doi': p.get('doi', ''),
            'citation_key': p.get('citation_key', ''),
            'language': p.get('language', 'en'),
            'candidate_relevance': p.get('candidate_relevance', p.get('applicable_to', [])),
            'verification_status': p.get('verification_status', 'abstract_inferred'),
            'matched_methods': matched_methods,
            'applicable_to': applicable_to,
            'method_summary': p.get('method_summary', ''),
            'full_text_summary': p.get('full_text_summary', ''),
            'data_summary': p.get('data_summary', ''),
            'evidence_locators': p.get('evidence_locators', []),
            'candidate_questions': p.get('candidate_questions', p.get('candidate_relevance', [])),
            'use_in_paper': p.get('use_in_paper', ''),
            'innovation_opportunity': p.get('innovation_opportunity', ''),
            'key_result': key_result,
            'limitation': limitation,
            'strength': strength,
            'confidence': 'high' if (p.get('cited_by', 0) > 20 and p.get('year', '0')
                                      and int(p.get('year', '0') or 0)
                                      >= int(datetime.now().strftime('%Y')) - 5) else 'medium',
            'needs_verification': not bool(p.get('full_text_summary')),
            'note': '摘要与外部全文总结仅用于候选分析；正文采用前须完成定位和方法迁移登记',
        })

    return insights


def _classify_by_method(insights):
    """按方法大类分组（非人名罗列）。"""
    groups = defaultdict(list)
    for ins in insights:
        for method in ins.get('matched_methods', []):
            groups[method].append(ins)
    return dict(groups)


def _classify_by_distribution_category(paper):
    """判断每篇文献属于哪个分布类别。"""
    text_lower = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()

    # Competition paper
    if any(kw.lower() in text_lower for kw in _COMP_KEYWORDS):
        return 'competition_paper'

    # Application: 有工程场景关键词就算
    if any(kw.lower() in text_lower for kw in _APP_KEYWORDS):
        return 'application'

    # Theoretical: 有算法/理论关键词
    if any(kw.lower() in text_lower for kw in _THEO_KEYWORDS):
        return 'theoretical'

    # 兜底归入理论类
    return 'theoretical'


_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_CONTEST_TITLE_RE = re.compile(r"数学建模竞赛|竞赛题|赛题|题目[：:]|竞赛组委会", re.I)


def _has_cjk(value: object) -> bool:
    return bool(_CJK_RE.search(str(value or "")))


def _source_value(item: dict, *names: str) -> str:
    for name in names:
        value = item.get(name)
        if value not in (None, "", []):
            if isinstance(value, list):
                return ", ".join(str(v) for v in value)
            return str(value).strip()
    return ""


def _literature_requirements(problem_graph: dict, fingerprint: dict, competition: str) -> dict:
    """Build the user-facing literature request before any source is read."""
    questions = problem_graph.get('questions', []) or []
    question_count = max(1, len(questions))
    chinese_min = question_count

    coverage = []
    for index, question in enumerate(questions or ['综合建模任务'], 1):
        if isinstance(question, dict):
            task = question.get('task', question.get('description', question.get('question', '')))
            keywords = question.get('keywords', []) or []
        else:
            task = question
            keywords = []
        merged_keywords = [str(item) for item in keywords if str(item).strip()]
        merged_keywords.extend(
            str(item) for item in (fingerprint.get('keywords', []) or [])[:8]
            if str(item).strip() and str(item) not in merged_keywords
        )
        coverage.append({
            'question_id': f'Q{index}',
            'task': str(task),
            'required_roles': ['method_basis', 'application_or_parameter_precedent'],
            'candidate_keywords': merged_keywords[:12],
        })
    return {
        'schema_version': '1.0',
        'ownership': 'user_sources_required',
        'agent_read_boundary': 'abstract_and_metadata_only',
        'competition_profile': competition,
        'counts': {
            'chinese': {'minimum': chinese_min, 'per_question_minimum': 1},
            'english': {'minimum': ENGLISH_MIN, 'coverage_recommended': True},
            'total': {
                'minimum': TOTAL_MIN, 'maximum': TOTAL_MAX,
                'recommended_minimum': RECOMMENDED_TOTAL_MIN,
                'recommended_maximum': RECOMMENDED_TOTAL_MAX,
            },
        },
        'coverage': coverage,
        'source_roles': [
            'method_basis: 模型或算法理论依据',
            'application_or_parameter_precedent: 应用场景、参数或测量先例',
            'comparison_boundary: 可选的对比方法与适用边界',
        ],
        'submission_fields': [
            'language', 'title', 'authors', 'venue', 'year', 'doi_or_url', 'abstract',
            'citation_key', 'full_text_summary', 'method_summary', 'data_summary',
            'limitations', 'evidence_locators', 'candidate_questions', 'use_in_paper',
        ],
        'forbidden_inputs': ['full_text', 'fulltext', 'pdf_text', 'body_text', '全文解析结果'],
    }


def _write_literature_request(output_dir: str, requirements: dict) -> list[str]:
    """Write the only request needed before the user supplies sources."""
    counts = requirements['counts']
    lines = [
        '# 文献需求卡',
        '',
        '文献检索、全文下载和来源初筛由用户完成。本流程不主动联网检索，不读取或解析文献全文。',
        '用户的文献 agent 阅读全文后回传摘要、方法、数据、适用边界和原文定位；主 Agent 只基于这些结构化内容判断方法、题目覆盖和引用作用。',
        '请将下方的 `literature_agent_prompt.md` 连同本需求卡交给负责阅读全文的 agent。',
        '',
        f"中文文献：每个小问至少 {counts['chinese']['per_question_minimum']} 篇，均须有可落地用途与原文定位。",
        (
            f"英文文献最低数量：{counts['english']['minimum']} 篇；建议覆盖全部小问，但不作为暂停条件。"
            if counts['english']['minimum'] > 0
            else "英文文献：不设硬性最低数量；建议覆盖全部小问，但不作为暂停条件。"
        ),
        f"文献总数硬范围：{counts['total']['minimum']}–{counts['total']['maximum']} 篇；推荐数量：{counts['total']['recommended_minimum']}–{counts['total']['recommended_maximum']} 篇。",
        '',
        '## 小问覆盖',
        '',
        '每个小问必须至少有 1 篇中文文献覆盖；每篇文献均须登记其模型、数据、参数、验证或结论的具体用途。',
    ]
    for item in requirements['coverage']:
        keywords = '、'.join(item['candidate_keywords']) or '按小问任务自定关键词'
        lines.append(f"- {item['question_id']}：{item['task']}；检索关键词：{keywords}")
    lines.extend([
        '',
        '## 提交格式',
        '',
        '请保存为项目 replay 目录中的 `literature_sources.yaml`，每条只填写以下字段：',
        '',
        '```yaml',
        '- language: zh  # zh 或 en',
        '  title: "完整题名"',
        '  authors: "作者"',
        '  venue: "期刊/会议/学位授予单位"',
        '  year: 2024',
        '  doi_or_url: "DOI 或官方详情页链接"',
        '  abstract: "原文摘要"',
        '  full_text_summary: "全文结构化总结，不粘贴全文"',
        '  method_summary: "模型、算法和适用条件"',
        '  data_summary: "数据来源、规模和参数"',
        '  limitations: "局限和适用边界"',
        '  evidence_locators: ["第X页/第Y节/表Z"]',
        '  candidate_questions: ["Q1"]',
        '  use_in_paper: "拟在 H5 登记的模型/数据/参数/验证/结论用途（原H4职责已并入H5）"',
        '  citation_key: "可选的 BibTeX 键"',
        '```',
        '',
        '不得提交竞赛题面、通知、博客、搜索结果页、占位条目或全文文本。',
    ])
    md_path = os.path.join(output_dir, 'literature_request.md')
    prompt_path = os.path.join(output_dir, 'literature_agent_prompt.md')
    yaml_path = os.path.join(output_dir, 'literature_request.yaml')
    with open(md_path, 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(lines) + '\n')
    prompt = f'''# 全文文献分析 Agent 提示词

你负责阅读用户已下载的文献全文，并把可核验信息回传给数学建模主控 Agent。

## 任务范围

1. 读取 `literature_request.yaml`，按 Q1、Q2 等小问和指定覆盖角色分析文献。
2. 依据需求卡检索并下载对应全文；若无法取得全文，保留官方详情页或 DOI，标记 `download_status: unavailable`，该条不能计入已完成覆盖。
3. 只处理已取得并明确提供的全文；不自行扩展检索范围，不补写不存在的结论。
4. 对每篇文献提取：题名、全部作者、期刊/会议/学位单位、年份、DOI或官方链接、原文摘要、研究对象、模型/算法、关键数据与参数、约束、结论、局限和可对应的小问。
5. 所有关键判断附原文定位，例如页码、章节、表号或公式号；找不到定位时填空并标记 `needs_user_check: true`。
6. 区分“原文明确说明”和“基于摘要或全文的推断”，不得把推断写成原文结论。

## 回传文件

将结果保存为项目 replay 目录中的 `literature_sources.yaml`。每条记录至少包含：

```yaml
- language: zh  # 或 en
  title: "完整题名"
  authors: "全部作者"
  venue: "期刊/会议/学位授予单位"
  year: 2024
  doi_or_url: "DOI 或官方详情页链接"
  abstract: "原文摘要"
  full_text_summary: "基于全文的结构化总结，不粘贴全文"
  method_summary: "模型、算法、关键步骤和适用条件"
  data_summary: "数据来源、规模、变量或参数信息"
  limitations: "原文明确的限制和适用边界"
  evidence_locators: ["第X页/第Y节/表Z"]
  candidate_questions: ["Q1"]
  use_in_paper: "可落地的模型、数据、参数、验证或结论用途"
  citation_key: "可选的 BibTeX 键"
```

每篇记录只保留总结和定位，不写入全文正文、长段落复制或无法核验的内容。完成后只返回该 YAML 文件路径及记录数量。
'''
    with open(prompt_path, 'w', encoding='utf-8') as handle:
        handle.write(prompt)
    requirements['agent_prompt_file'] = prompt_path
    if yaml is not None:
        with open(yaml_path, 'w', encoding='utf-8') as handle:
            yaml.safe_dump(requirements, handle, allow_unicode=True, sort_keys=False)
    else:
        with open(yaml_path, 'w', encoding='utf-8') as handle:
            json.dump(requirements, handle, ensure_ascii=False, indent=2)
    return [md_path, yaml_path, prompt_path]


def _load_user_literature_sources(path: str | None, output_dir: str) -> tuple[list[dict], list[str], str | None]:
    """Load user-provided metadata and abstracts; never open a full-text file."""
    candidates = []
    if path:
        candidates.append(os.path.abspath(path))
    for name in ('literature_sources.yaml', 'literature_sources.yml', 'literature_sources.json'):
        candidates.append(os.path.join(output_dir, name))
    source_path = next((candidate for candidate in candidates if os.path.isfile(candidate)), None)
    if source_path is None:
        return [], ['未提供用户文献元数据和摘要文件'], None
    try:
        with open(source_path, 'r', encoding='utf-8') as handle:
            raw_text = handle.read()
        if source_path.lower().endswith('.json'):
            payload = json.loads(raw_text)
        elif yaml is not None:
            payload = yaml.safe_load(raw_text)
        else:
            return [], ['缺少 PyYAML，无法读取文献 YAML'], source_path
    except Exception as exc:
        return [], [f'用户文献文件解析失败: {exc}'], source_path
    if isinstance(payload, dict):
        payload = payload.get('references', payload.get('sources', payload.get('items', [])))
    if not isinstance(payload, list):
        return [], ['文献文件必须是列表，或包含 references/sources/items 列表'], source_path

    valid, errors, seen = [], [], set()
    forbidden = {'full_text', 'fulltext', 'pdf_text', 'body_text', '全文解析结果'}
    for index, item in enumerate(payload, 1):
        if not isinstance(item, dict):
            errors.append(f'第{index}条不是对象')
            continue
        if forbidden.intersection(item):
            errors.append(f'第{index}条包含全文字段；只提交摘要和元数据')
            continue
        title = _source_value(item, 'title', '题名', '标题')
        authors = _source_value(item, 'authors', 'author', '作者')
        venue = _source_value(item, 'venue', 'journal', '期刊', '会议', '学位单位')
        year = _source_value(item, 'year', '年份')
        doi_or_url = _source_value(item, 'doi_or_url', 'doi', 'DOI', 'official_link', 'url', 'link')
        abstract = _source_value(item, 'abstract', '摘要')
        full_text_summary = _source_value(item, 'full_text_summary', '全文总结', '全文分析总结')
        method_summary = _source_value(item, 'method_summary', '研究对象和方法', '方法')
        data_summary = _source_value(item, 'data_summary', '数据摘要', '数据总结')
        limitations = _source_value(item, 'limitations', '局限', '适用边界')
        evidence_locators = item.get('evidence_locators', item.get('定位信息', []))
        candidate_questions = item.get('candidate_questions', item.get('candidate_relevance', item.get('applicable_question', [])))
        use_in_paper = _source_value(item, 'use_in_paper', '本题作用', '作用')
        language = _source_value(item, 'language', '语言').lower()
        if not language:
            language = 'zh' if _has_cjk(title + venue + authors) else 'en'
        if language in {'中文', 'chinese', 'zh-cn'}:
            language = 'zh'
        elif language not in {'zh', 'en'}:
            errors.append(f'第{index}条 language 必须是 zh 或 en')
            continue
        missing = [name for name, value in (
            ('题名', title), ('作者', authors), ('来源', venue), ('年份', year),
            ('DOI或官方链接', doi_or_url), ('摘要', abstract),
            ('全文总结', full_text_summary), ('方法总结', method_summary),
            ('数据总结', data_summary), ('局限/适用边界', limitations),
            ('本题实际用途', use_in_paper),
        ) if not value]
        if not isinstance(evidence_locators, list) or not evidence_locators:
            missing.append('原文定位信息')
        if not isinstance(candidate_questions, list) or not candidate_questions:
            missing.append('候选小问')
        if missing:
            errors.append(f'第{index}条缺少: {"、".join(missing)}')
            continue
        if _CONTEST_TITLE_RE.search(title):
            errors.append(f'第{index}条疑似题面/竞赛通知，不能作为学术文献')
            continue
        key = doi_or_url.lower() if doi_or_url else re.sub(r'\W', '', title).lower()
        if key in seen:
            errors.append(f'第{index}条与前文献 DOI/题名重复')
            continue
        seen.add(key)
        valid.append({
            'source': 'user_provided', 'language': language,
            'verification_status': 'user_metadata',
            'title': title, 'authors': [authors] if isinstance(authors, str) else authors,
            'venue': venue, 'journal': venue, 'year': year,
            'doi': doi_or_url if doi_or_url.startswith('10.') else '',
            'url': doi_or_url if not doi_or_url.startswith('10.') else f'https://doi.org/{doi_or_url}',
            'link': doi_or_url if not doi_or_url.startswith('10.') else f'https://doi.org/{doi_or_url}',
            'abstract': abstract,
            'method_summary': method_summary,
            'full_text_summary': full_text_summary,
            'data_summary': data_summary,
            'limitations': limitations,
            'evidence_locators': evidence_locators,
            'use_in_paper': use_in_paper,
            'innovation_opportunity': _source_value(item, 'innovation_opportunity', '创新点'),
            'candidate_relevance': candidate_questions,
            'candidate_questions': candidate_questions,
            'citation_key': _source_value(item, 'citation_key', 'bibtex_key', 'BibTeX键'),
        })
    return valid, errors, source_path


def _load_user_chinese_sources(path: str | None, output_dir: str) -> tuple[list[dict], list[str], str | None]:
    """Load and validate user-supplied Chinese academic references.

    The main agent does not discover Chinese sources. It accepts a user-
    provided YAML/JSON file with auditable metadata and a method summary.
    Applicability, paper role, and innovation are optional suggestions here;
    the main agent decides them after reading the actual problem graph.
    """
    candidates = []
    if path:
        candidates.append(os.path.abspath(path))
    for name in ("zh_literature.yaml", "references_zh.yaml", "references_request_zh_response.yaml", "zh_literature.json"):
        candidates.append(os.path.join(output_dir, name))
    source_path = next((candidate for candidate in candidates if os.path.isfile(candidate)), None)
    if source_path is None:
        return [], ["未提供中文文献元数据文件"], None
    try:
        with open(source_path, "r", encoding="utf-8") as handle:
            raw_text = handle.read()
        if source_path.lower().endswith(".json"):
            payload = json.loads(raw_text)
        elif yaml is not None:
            payload = yaml.safe_load(raw_text)
        else:
            return [], ["缺少 PyYAML，无法读取中文文献 YAML"], source_path
    except Exception as exc:
        return [], [f"中文文献文件解析失败: {exc}"], source_path
    if isinstance(payload, dict):
        payload = payload.get("references", payload.get("chinese_references", payload.get("items", [])))
    if not isinstance(payload, list):
        return [], ["中文文献文件必须是列表，或包含 references/chinese_references/items 列表"], source_path

    valid, errors, seen = [], [], set()
    for index, item in enumerate(payload, 1):
        if not isinstance(item, dict):
            errors.append(f"第{index}条不是对象")
            continue
        title = _source_value(item, "title", "题名", "标题")
        authors = _source_value(item, "authors", "author", "作者")
        journal = _source_value(item, "journal", "期刊")
        year = _source_value(item, "year", "年份")
        volume_issue_pages = _source_value(item, "volume_issue_pages", "卷(期):页码", "卷期页码")
        doi = _source_value(item, "doi", "DOI")
        link = _source_value(item, "official_link", "官网详情页链接", "link", "url")
        abstract = _source_value(item, "abstract", "摘要")
        method_summary = _source_value(item, "method_summary", "method", "研究对象和方法", "方法")
        use_in_paper = _source_value(item, "use_in_paper", "本题作用", "与本题对应关系", "作用")
        innovation = _source_value(item, "innovation_opportunity", "创新点", "可创新点")
        candidate_relevance = item.get("candidate_relevance", item.get("applicable_question", item.get("适用问题", [])))
        citation_key = _source_value(item, "citation_key", "bibtex_key", "BibTeX键")
        language = _source_value(item, "language", "语言") or "zh"
        key = (doi.lower() if doi else re.sub(r"\W", "", title).lower())
        missing = [name for name, value in (("题名", title), ("作者", authors), ("期刊", journal),
                                             ("年份", year), ("DOI或官网链接", doi or link),
                                             ("方法摘要", method_summary)) if not value]
        if missing:
            errors.append(f"第{index}条缺少: {', '.join(missing)}")
            continue
        if not _has_cjk(title + journal + authors) or str(language).lower() not in {"zh", "zh-cn", "中文", "chinese"}:
            errors.append(f"第{index}条无法确认是中文学术文献")
            continue
        if _CONTEST_TITLE_RE.search(title):
            errors.append(f"第{index}条疑似题面/竞赛通知，不能作为学术文献")
            continue
        if key in seen:
            errors.append(f"第{index}条与前文献 DOI/题名重复")
            continue
        seen.add(key)
        valid.append({
            "source": "user_provided_zh", "language": "zh", "verification_status": "user_metadata",
            "title": title, "authors": [authors] if isinstance(authors, str) else authors,
            "journal": journal, "year": year, "doi": doi, "link": link, "abstract": abstract,
            "volume_issue_pages": volume_issue_pages,
            "method_summary": method_summary, "use_in_paper": use_in_paper,
            "innovation_opportunity": innovation,
            "candidate_relevance": candidate_relevance,
            "citation_key": citation_key,
        })
    return valid, errors, source_path


def _build_literature_context(problem_graph: dict, fingerprint: dict) -> dict:
    """Create a compact handoff packet for an external Chinese-literature AI."""
    questions = problem_graph.get('questions', []) or []
    subproblems = []
    for i, question in enumerate(questions, 1):
        if isinstance(question, dict):
            task = question.get('task', question.get('description', question.get('question', '')))
            question_keywords = question.get('keywords', []) or []
        else:
            task = question
            question_keywords = []
        keywords = [str(keyword) for keyword in (question_keywords or []) if str(keyword).strip()]
        keywords.extend(str(keyword) for keyword in (fingerprint.get('keywords', []) or [])[:8]
                        if str(keyword).strip() and str(keyword) not in keywords)
        subproblems.append({'id': f'Q{i}', 'task': str(task), 'candidate_keywords': keywords[:12]})
    return {
        'schema_version': '1.0',
        'purpose': 'external_chinese_literature_search',
        'direction_zh': problem_graph.get('direction_zh', fingerprint.get('primary', '数学建模问题')),
        'problem_type': problem_graph.get('type', fingerprint.get('primary', '')),
        'objectives': problem_graph.get('objectives', [problem_graph.get('hidden_goal', '')]),
        'subproblems': subproblems,
        'constraints': problem_graph.get('constraints', problem_graph.get('real_world_constraints', [])),
        'data_summary': problem_graph.get('available_data', []),
        'fingerprint': fingerprint,
        'external_agent_boundary': [
            '只检索并核验中文学术文献，提取方法摘要；',
            'candidate_relevance 只能是初步建议；',
            'applicable_question、use_in_paper、innovation_opportunity 由主 Agent 根据本题最终确认。',
        ],
    }


def _write_chinese_pause(output_dir: str, problem_graph: dict, fingerprint: dict,
                         found: int, validation_errors: list[str], source_path: str | None,
                         required_min: int) -> list[str]:
    """Write a hard-stop request; no formal literature report is written."""
    direction = problem_graph.get("direction_zh", fingerprint.get("primary", "数学建模问题"))
    keywords = fingerprint.get("keywords", []) or []
    request_path = os.path.join(output_dir, "references_request_zh.md")
    context = _build_literature_context(problem_graph, fingerprint)
    context_path = os.path.join(output_dir, 'literature_context.yaml')
    if yaml is not None:
        with open(context_path, 'w', encoding='utf-8') as handle:
            yaml.safe_dump(context, handle, allow_unicode=True, sort_keys=False)
    else:
        context_path = os.path.join(output_dir, 'literature_context.json')
        with open(context_path, 'w', encoding='utf-8') as handle:
            json.dump(context, handle, ensure_ascii=False, indent=2)
    request = f"""# 中文文献补充请求（硬门禁）

当前题目方向：{direction}

正式论文要求至少提供 **{required_min} 篇可核验中文学术文献**。当前已核验中文文献：{found} 篇。
在补齐前不得进入文献综述、模型建立和论文正文生成。

请交给其他中文文献检索 AI，要求返回至少 {required_min} 篇与“{direction}”直接相关的中文期刊/学位/会议学术文献，
优先关键词：{"、".join(map(str, keywords[:8])) or direction}。

请同时把 `literature_context.yaml` 交给外部文献 AI。它只负责找文献和提取方法；
`applicable_question`、`use_in_paper`、`innovation_opportunity` 由主 Agent 在读完题目后确认，
外部 AI 可以返回 `candidate_relevance` 作为建议，但不能把猜测当成最终结论。

每篇必须返回以下核心字段：

```yaml
- title: "完整题名"
  authors: "全部作者"
  journal: "期刊/会议/学位授予单位"
  year: "年份"
  volume_issue_pages: "卷(期):页码"
  doi: "DOI；无 DOI 时填写官方详情页链接"
  official_link: "官方详情页或机构链接"
  method_summary: "研究对象、模型/算法、关键约束或结论"
  candidate_relevance: ["Q1", "Q2"]
  citation_key: "可选；若已有 BibTeX 键请保留"
```

禁止返回竞赛题面、竞赛通知、博客、搜索结果页或无法核验的占位条目。
请保存为 `zh_literature.yaml` 后交回，或直接把完整 YAML 粘贴给我。

## 当前校验问题

{chr(10).join(f"- {item}" for item in (validation_errors or ["中文文献数量不足"]))}
"""
    with open(request_path, "w", encoding="utf-8") as handle:
        handle.write(request)
    pause_payload = {
        "schema_version": "1.0", "status": "PAUSE", "reason": "chinese_literature_gate",
        "required_min": required_min, "verified_count": found,
        "source_file": source_path, "validation_errors": validation_errors,
        "resume_with": "zh_literature.yaml",
        "context_file": context_path,
    }
    pause_path = os.path.join(output_dir, "literature_pause.json")
    with open(pause_path, "w", encoding="utf-8") as handle:
        json.dump(pause_payload, handle, ensure_ascii=False, indent=2)
    return [request_path, context_path, pause_path]


def _mark_chinese_pause_resumed(output_dir: str, verified_count: int | None = None,
                                source_file: str | None = None) -> None:
    """Keep an audit trail without allowing a stale PAUSE marker to linger."""
    pause_path = os.path.join(output_dir, "literature_pause.json")
    if not os.path.isfile(pause_path):
        return
    try:
        with open(pause_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        payload.update({"status": "RESUMED", "resumed_at": datetime.now().isoformat()})
        if verified_count is not None:
            payload['verified_count'] = verified_count
        if source_file:
            payload['source_file'] = source_file
        with open(pause_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    except (OSError, ValueError, TypeError):
        # A malformed old marker is left visible; the delivery checker will
        # report it rather than silently deleting evidence.
        return


def _merge_chinese_sources(automatic: list[dict], chinese: list[dict]) -> list[dict]:
    """Keep all valid Chinese sources, then fill remaining slots from auto hits."""
    merged = list(chinese)
    seen = {re.sub(r"\W", "", str(item.get("title", "")).lower()) for item in merged}
    for item in automatic:
        key = re.sub(r"\W", "", str(item.get("title", "")).lower())
        if key and key not in seen:
            merged.append(item)
            seen.add(key)
    if len(merged) > TOTAL_MAX:
        # Never discard a user-supplied Chinese source merely because the
        # optional English pool is large.  Trim automatic records first; the
        # distribution stage may still report a coverage warning honestly.
        zh = [item for item in merged if item.get("language") == "zh"]
        other = [item for item in merged if item.get("language") != "zh"]
        merged = zh + other[:max(0, TOTAL_MAX - len(zh))]
    return merged


def _enforce_distribution_v43(all_papers, target_total=None):
    """弹性分布控制 — 优先导向 + 容错回退 + 诚实说明。

    规则变更：
    1. 不再是硬限制，而是"期望目标"——不足时允许放宽并如实标注
    2. 产出总数 ≥6 且 ≤12；有效文献 <4 时不强行凑数，返回 low_coverage 标记
    3. 不允许为凑配额而增删条目；只按命中率裁剪超限部分
    4. 纯英文结果多时，在 warnings 中提示用户论文2.1要写"国内公开资料有限"
    5. 高重复/同质化文献过滤（去重后已做此步）

    Returns:
        filtered_papers, distribution_stats, warnings, extra_notes
    """
    if not all_papers:
        needs_human = True  # 用户未提供可用文献 → 必须暂停
        return [], {'error': '无可用文献', 'needs_human_intervention': needs_human}, ['用户未提供可用文献'], [{'type': 'need_human', 'reason': 'user_sources_missing'}]

    total_raw = len(all_papers)

    # Step 1: 分类
    categorized = {k: [] for k in LIT_DISTRIBUTION}
    for p in all_papers:
        cat = _classify_by_distribution_category(p)
        categorized[cat].append(p)

    dist_before = {k: len(v) for k, v in categorized.items()}

    # Step 2: 按 target_max 裁剪（不要求满足 target_min）
    final = {}
    for cat_name, config in LIT_DISTRIBUTION.items():
        final[cat_name] = categorized[cat_name][:config['target_max']]

    # Step 3: 汇总检查
    warnings = []
    extra_notes = []
    total_final = sum(len(v) for v in final.values())

    # === 核心：是否需要人工介入？===
    needs_human_intervention = False
    human_intervention_reasons = []

    if total_final < 4:
        warnings.append(
            f'⚠️ 有效文献仅 {total_final} 篇（低于4篇）。'
            f'不在论文中强行凑数，在 2.1 文献调研如实说明用户提交的来源覆盖有限。'
        )
        needs_human_intervention = True
        human_intervention_reasons.append({
            'action': 'manual_cnki_search',
            'urgency': 'critical',  # 严重：连最低要求都达不到
            'message': f'用户提供的可用文献仅{total_final}篇，不足4篇底线。',
        })
    elif total_final < TOTAL_MIN:
        warnings.append(
            f'ℹ️ 检索总量{total_final}篇偏低（期望≥{TOTAL_MIN}），'
            f'如有能力可人工补充同类文献；不足部分不在文中虚构补齐。'
        )
        needs_human_intervention = True
        human_intervention_reasons.append({
            'action': 'optional_cnki_search',
            'urgency': 'normal',  # 一般：还能继续但偏少
            'message': f'用户提供的可用文献{total_final}篇，低于期望下限{TOTAL_MIN}。',
        })
    elif total_final > TOTAL_MAX:
        deficit = total_final - TOTAL_MAX
        cut_ratio = deficit / max(1, total_final)
        for cat_name in final:
            n_to_cut = int(len(final[cat_name]) * cut_ratio)
            final[cat_name] = final[cat_name][n_to_cut:]
        total_final = sum(len(v) for v in final.values())
        warnings.append(f'ℹ️ 用户提交 {dist_before["total"]} 篇，已裁剪至 {total_final} 篇')

    # 语言覆盖度分析
    foreign_count = sum(
        len(final[k]) for k in final if k != 'competition_paper'
    )
    comp_count = len(final.get('competition_paper', []))
    english_dominant = foreign_count >= comp_count + 3  # 外文比竞赛论文多3+篇
    if english_dominant and comp_count == 0:
        extra_notes.append(
            ('📝 提示：当前文献以英文来源为主；论文 2.1 节按实际中文覆盖情况表述。')
        )
        if total_final < TOTAL_MIN * 2:  # 英文为主 + 总数也偏少
            needs_human_intervention = True
            human_intervention_reasons.append({
                'action': 'optional_cnki_search',
                'urgency': 'normal',
                'message': '英文文献为主且总数偏低，请按需求卡补充用户检索的中文应用类文献。',
            })

    # 各类别与期望目标的差距（仅作告知，不构成 FAIL）
    for cat_name, config in LIT_DISTRIBUTION.items():
        actual = len(final[cat_name])
        tgt_min = config['target_min']
        tgt_max = config['target_max']
        if actual < tgt_min:
            warnings.append(
                f'ℹ️ [{cat_name}] 命中 {actual} 篇（期望{tgt_min}-{tgt_max}篇），来源不足属正常现象，'
                f'已在报告中如实反映，未伪造补齐。'
            )
        elif actual > tgt_max:
            warnings.append(
                f'ℹ️ [{cat_name}] 命中 {actual} 篇（期望{tgt_min}-{tgt_max}篇），已按上限裁剪。'
            )

    # Step 4: 扁平化输出
    flat = []
    for cat_name, papers in final.items():
        for p in papers:
            p['_distribution_category'] = cat_name
            flat.append(p)

    dist_after = {k: len(v) for k, v in final.items()}
    dist_after['total'] = total_final

    # 返回时带上是否需要人工介入的信号
    flat = []
    for cat_name, papers in final.items():
        for p in papers:
            p['_distribution_category'] = cat_name
            flat.append(p)

    result_stats = dict(dist_after)
    result_stats.update({
        'raw_hits': total_raw,
        'low_coverage': total_final < 4,
        'needs_human_intervention': needs_human_intervention,
        'intervention_reasons': human_intervention_reasons,
    })

    return flat, result_stats, warnings, extra_notes


def _print_pause_signal(intervention_reasons, total_final, total_min, total_max,
                        required_chinese_count=0):
    """输出硬暂停信号；调用方必须在补齐门禁前停止后续阶段。"""
    print(f'\n{"="*60}')
    print('🛑 [literature_survey] PAUSE — 用户文献数量不足，需要补充')
    print('='*60)
    print(f'用户提供的有效文献：{total_final} 篇（期望 {total_min}-{total_max} 篇）')
    print()
    print('当前状态：不生成正式报告、不进入模型建立，请先补齐中文文献：')
    print()
    print('【下一步】按 literature_agent_prompt.md 阅读已下载全文并回传 literature_sources.yaml')
    print('  主 Agent 不自行检索或编造文献，收到结构化摘要和全文总结后再分析')
    print()
    print('【恢复】将核验后的条目保存为 literature_sources.yaml，或直接粘贴完整 YAML；')
    print('  不允许通过题面条目或示例占位绕过文献数量和小问覆盖门禁。')
    print()
    for reason in intervention_reasons:
        urgency = '【严重】' if reason.get('urgency') == 'critical' else '【建议】'
        print(f'{urgency} {reason["message"]}')
    print()
    if required_chinese_count:
        print(f'程序不会自动继续；收到至少 {required_chinese_count} 篇通过元数据校验的中文文献后，重新运行调研阶段。')
    print('='*60 + '\n')


# 国赛中文文献门禁是阻塞式的：run_survey 在 guosai profile 未满足
# required_chinese_count 时返回 PAUSE；其他 profile 不因中文数量阻塞。


def _identify_gaps(insights, fingerprint, problem_graph):
    """从已检索文献中发现研究缺口。

    逻辑：对比已有方法的能力边界 vs 本题的特殊约束条件。
    """
    constraints = fingerprint.get('constraints', [])
    questions = problem_graph.get('questions', [])

    # 常见研究缺口模板
    gaps = []

    # 缺口1：如果题目有特殊约束但文献多假设标准情形
    if constraints:
        gap_text = f'已有文献对 {", ".join(str(c) for c in constraints[:3])} 约束的关注不足——多数模型在简化假设下运行，未充分处理实际场景中这些约束同时作用时的耦合效应。'
        gaps.append(gap_text)

    # 缺口2：如果有多问递进关系，很多文献只解决前置问
    if len(questions) > 1:
        gaps.append(
            '部分文献仅研究了单目标或单阶段的简化版本，对于本题多层级、多阶段的递进结构缺乏系统性处理方法。'
        )

    # 缺口3：方法单一
    method_counts = {}
    for ins in insights:
        for m in ins.get('matched_methods', []):
            method_counts[m] = method_counts.get(m, 0) + 1
    if method_counts:
        dominant_method = max(method_counts, key=method_counts.get)
        if method_counts[dominant_method] > len(insights) * 0.6:
            gaps.append(
                f'现有研究方法偏集中于 {dominant_method} 类方法，其他可能的技术路线（如互补的数据驱动方法、混合建模策略等）尚未得到充分探索。'
            )

    # 缺口4：现实约束缺失
    real_constraints = problem_graph.get('real_world_constraints', [])
    if real_constraints:
        gaps.append(
            f'上述文献的实验设置通常忽略了本题涉及的 {", ".join(real_constraints[:2])} 等现实约束条件。在实际应用中，这些条件的存在会显著影响模型的可行性和求解效率。'
        )

    if not gaps:
        gaps.append('已有文献为该领域奠定了良好基础，但针对本赛题特有的数据规模和约束组合，尚无文献提供直接的完整解决方案。')

    return gaps


def _generate_five_section_report(fingerprint, groups, gaps, insights, problem_graph, dist_stats=None):
    """生成五段式文献调研报告（v4.3 增加 dist_stats 参数）。

    dist_stats 来自 _enforce_distribution_v43，包含 before/after/low_coverage/english_dominant。
    """
    primary = fingerprint.get('primary', '')
    zh_primary = {'optimization': '优化决策', 'prediction': '预测', 'classification': '分类评价',
                  'regression': '回归分析', 'graph_model': '图模型', 'mechanism_model': '机理建模',
                  'physics_modeling': '物理建模', 'scheduling': '排程调度', 'location': '选址',
                  'routing': '路径规划', 'resource_allocation': '资源配置'}.get(primary.lower(), primary)

    direction_zh = problem_graph.get('direction_zh', f'{zh_primary}类相关问题')
    qn_count = len(problem_graph.get('questions', []))
    question_summaries = [str(q) if isinstance(q, str) else ''
                          for q in problem_graph.get('questions', [])[:4]]

    sections = []

    # === 第一段：检索来源、检索方向与覆盖说明 ===
    lang_note = ''
    coverage_note = ''
    if dist_stats:
        if dist_stats.get('english_dominant'):
            lang_note = '''

**文献语言覆盖说明：**本文按需求卡由用户提供中英文文献，中文与英文来源分别服务于本土应用背景、模型方法和适用边界的论证。'''
        if dist_stats.get('low_coverage'):
            after_total = dist_stats.get('after', {}).get('total', 0)
            coverage_note = f'''

**文献覆盖度说明：**用户提供并通过元数据与摘要校验的文献共计 {after_total} 篇；数量和小问覆盖按需求卡登记。'''

    sections.append(f'''### 2.1 文献调研

针对本赛题的研究方向，本文对相关学术文献进行了系统检索与梳理。检索覆盖的研究主题包括：同类数模赛题解法、{direction_zh}、该类模型（优化/预测/评价）相关文献。采用的检索关键词涵盖「{", ".join(fingerprint.get("keywords", [])[:3])}」等核心术语及其同义词。

文献由用户检索并下载全文，文献 agent 阅读全文后回传摘要、方法、数据、适用边界和原文定位；本文仅据此完成方法分类、题目覆盖和引用作用登记。{lang_note}{coverage_note}''')

    # === 第二段：现有研究现状梳理（分类归纳，非人名罗列）===
    if groups:
        sections.append('\n**研究方法分类归纳：**')
        for method_name, members in sorted(groups.items(), key=lambda x: -len(x[1])):
            sections.append(f'\n**- {method_name}**')

            # 总结该方法的特点
            common_traits = []
            strengths_found = []
            for m in members[:5]:
                if m.get('strength'):
                    strengths_found.append(m['strength'])
                y = m.get('year', '')
                if y:
                    common_traits.append(f'文献[{m["paper_index"]}]({y})')

            if common_traits:
                sections.append(f'  代表性工作：{", ".join(common_traits[:5])}。')

            if strengths_found:
                sections.append(f'  方法特点：{'，'.join(set(s.split('，')[0] for s in strengths_found if '，' in s))}。')

            # 各类方法的共同优点和局限
            if method_name == '启发式优化':
                sections.append('  这类方法的优势在于能有效处理大规模组合空间，但在复杂约束条件下的可行性保持仍具挑战。')
            elif method_name == '深度学习/NLP':
                sections.append('  这类方法的优势在于能捕捉非线性关系和高维模式，但通常需要较大数据量支撑，且可解释性较弱。')
            elif method_name == '整数规划/MIP':
                sections.append('  这类方法能提供精确的最优解保证，但对问题规模敏感，大规模实例的计算时间可能难以接受。')
            elif method_name == '强化学习':
                sections.append('  这类方法适合序贯决策和多步优化问题，但训练过程稳定性差、超参数敏感是普遍问题。')
            elif method_name == '动态规划':
                sections.append('  这类方法通过状态转移实现全局最优，但面临"维度灾难"，状态空间过大时不可行。')
            elif method_name == '统计/回归':
                sections.append('  这类方法可解释性强、实现简单，但对非线性关系的拟合能力有限。')
            elif method_name == '综合评价/多准则':
                sections.append('  这类方法适合多指标决策和排名问题，但权重分配的主观性是常见争议点。')
            elif method_name == '微分方程/ODE/PDE':
                sections.append('  这类方法能刻画连续变化过程的内在机理，但数值求解精度和收敛性高度依赖于初值设定。')
            elif method_name == '图论/网络':
                sections.append('  这类方法天然适配网络结构和拓扑优化问题，但对于动态变化的图结构需要额外设计更新机制。')
            elif method_name == '鲁棒/随机优化':
                sections.append('  这类方法能在不确定性条件下提供稳健解，但最坏情况分析可能导致保守估计。')
            else:
                sections.append('  具体特点需根据文献内容进一步补充。')

            limitations_found = [m.get('limitation') for m in members if m.get('limitation')]
            if limitations_found:
                unique_lim = list(set(limitations_found))
                sections.append(f'  局限性：{'；'.join(unique_lim[:2])}。')

    # === 第三段：研究缺口 ===
    sections.append('\n**研究缺口与创新点来源：**')
    for g in gaps:
        sections.append(f'\n- {g}')

    # === 第四段：与本文建模的关联 ===
    sections.append('\n**与本文建模的关联：**')
    sections.append('''本文借鉴了文献[1]的方法思路作为建模的基础框架，同时针对赛题涉及的实际约束条件做了以下修改与改进：''')

    # 为每问生成关联说明
    for i, q_text in enumerate(question_summaries[:4], 1):
        relevant_papers = [ins for ins in insights if f'Q{i}' in ins.get('applicable_to', [])]
        if relevant_papers:
            ref_ids = ', '.join(f'[{ins["paper_index"]}]' for ins in relevant_papers[:3])
            methods = relevant_papers[0].get('matched_methods') or ['XX方法']
            sections.append(f'''
- Q{i}建模参考了{ref_ids}的思路，将原始方法中的{methods[0]}扩展，引入了赛题特有的{'约束条件' if fingerprint.get('constraints') else '实际因素'}，改进了目标函数/算法设计。''')

    sections.append('\n具体而言，本文将文献中的通用模型针对本题数据规模和约束特征进行了定制化改造，详见后续各章建模过程。')

    # === 第五段：引言 + 强制提醒 ===
    sections.append('''

> **引用标记规范**：正文中凡借鉴文献观点、模型或思路之处，均在句子末尾用上角标`[1][2]`标注引用顺序。文末参考文献列表按 GB/T 7714 顺序编码制排列，与正文引用顺序严格一致。''')

    return '\n\n'.join(sections)


_RESEARCH_SOURCE_STATUSES = {'peer_reviewed', 'preprint', 'standard', 'dataset', 'software', 'web'}


def _research_status(ins: dict) -> str:
    """Classify a source without treating the classification as peer-review proof."""
    declared = str(ins.get('status', '')).strip().lower()
    if declared in _RESEARCH_SOURCE_STATUSES:
        return declared
    source = str(ins.get('source', '')).strip().lower()
    if source == 'arxiv' or ins.get('arxiv_id'):
        return 'preprint'
    if source in {'crossref', 'semantic_scholar', 'user_provided_zh'}:
        return 'peer_reviewed'
    if source in {'dataset', 'software', 'standard', 'web'}:
        return source
    return 'web'


def _research_relevance(ins: dict) -> str:
    value = ins.get('relevance', ins.get('candidate_relevance', ins.get('applicable_to', [])))
    if isinstance(value, list):
        return '；'.join(str(item) for item in value if str(item).strip())
    return str(value or '').strip()


def _research_used_in(ins: dict) -> list[str]:
    value = ins.get('used_in', ins.get('applicable_to', []))
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(item) for item in (value or []) if str(item).strip()]


def _research_verified_at(ins: dict) -> str:
    value = ins.get('verified_at', '')
    return str(value).strip() if value else ''


def _build_references_yaml(insights):
    """构建 references.yaml — 供写作阶段引用。"""
    refs = []
    role_by_category = {
        'theoretical': 'method_basis',
        'application': 'measurement_precedent',
        'competition_paper': 'comparison_boundary',
    }
    for ins in insights:
        source_class = ins.get('_distribution_category', 'theoretical')
        ref = {
            'ref_ID': ins.get('ref_ID', ins.get('paper_index')),
            'citation_key': ins.get('citation_key', ''),
            'title': ins.get('title', ''),
            'authors': ins.get('authors', ''),
            'year': ins.get('year', ''),
            'volume_issue_pages': ins.get('volume_issue_pages', ''),
            'source': ins.get('source', ''),
            'journal_venue': ins.get('journal', ins.get('venue', '')),
            'doi': ins.get('doi', ''),
            'link': ins.get('link', ''),
            # Research-evidence contract fields.  Legacy aliases above remain
            # for consumers that have not migrated to the canonical names.
            'venue': ins.get('venue', ins.get('journal', '')),
            'status': _research_status(ins),
            'url': ins.get('url', ins.get('link', '')),
            'relevance': _research_relevance(ins),
            'key_points': ins.get('key_points', ins.get('method_summary', '') or ins.get('key_result', '')),
            'limitations': ins.get('limitations', ins.get('limitation', '') or '当前元数据未明确适用边界'),
            'used_in': _research_used_in(ins),
            'verified_at': _research_verified_at(ins),
            'matched_methods': ins.get('matched_methods', []),
            'applicable_to': ins.get('applicable_to', []),
            'candidate_relevance': ins.get('candidate_relevance', []),
            'language': ins.get('language', 'en'),
            'method_summary': ins.get('method_summary', ''),
            'full_text_summary': ins.get('full_text_summary', ''),
            'data_summary': ins.get('data_summary', ''),
            'evidence_locators': ins.get('evidence_locators', []),
            'candidate_questions': ins.get('candidate_questions', ins.get('applicable_to', [])),
            'use_in_paper': ins.get('use_in_paper', ''),
            'innovation_opportunity': ins.get('innovation_opportunity', ''),
            'verification_status': ins.get('verification_status', 'abstract_inferred'),
            'source_class': source_class,
            'role': ins.get('role', role_by_category.get(source_class, 'method_basis')),
            'confidence': ins.get('confidence', 'medium'),
            'note': ins.get('note', ''),
        }
        refs.append(ref)
    return refs


def _build_method_transfer_map(insights, question_summaries, required_chinese_count=0):
    """Create an explicit literature→model transfer checklist.

    The map never claims that a method was adopted automatically.  Each
    subproblem entry remains ``pending_agent_decision`` until the writer records
    adopt/adapt/reject and explains the model delta in the modeling chapter.
    """
    chinese = [ins for ins in insights if str(ins.get('language', '')).lower() in {'zh', 'zh-cn', '中文', 'chinese'}]
    entries = []
    for ins in chinese:
        methods = ins.get('matched_methods', []) or [ins.get('method_summary', '')]
        if isinstance(methods, list):
            methods = '；'.join(str(item) for item in methods if str(item).strip())
        entries.append({
            'ref_ID': ins.get('ref_ID', ins.get('paper_index')),
            'citation_key': ins.get('citation_key', ''),
            'title': ins.get('title', ''),
            'authors': ins.get('authors', ''),
            'journal': ins.get('journal', ''),
            'year': ins.get('year', ''),
            'volume_issue_pages': ins.get('volume_issue_pages', ''),
            'doi': ins.get('doi', ''),
            'official_link': ins.get('link', ''),
            'venue': ins.get('venue', ins.get('journal', '')),
            'status': _research_status(ins),
            'url': ins.get('url', ins.get('link', '')),
            'relevance': _research_relevance(ins),
            'key_points': ins.get('key_points', ins.get('method_summary', '') or ins.get('key_result', '')),
            'limitations': ins.get('limitations', ins.get('limitation', '') or '当前元数据未明确适用边界'),
            'used_in': _research_used_in(ins),
            'verified_at': _research_verified_at(ins),
            'method': methods,
            'method_summary': ins.get('method_summary', ''),
            'full_text_summary': ins.get('full_text_summary', ''),
            'data_summary': ins.get('data_summary', ''),
            'evidence_locators': ins.get('evidence_locators', []),
            'provided_use_in_paper': ins.get('use_in_paper', ''),
            'provided_innovation_opportunity': ins.get('innovation_opportunity', ''),
            'candidate_relevance': ins.get('candidate_relevance', ins.get('applicable_to', [])),
            'verification_status': ins.get('verification_status', 'user_metadata'),
        })
    by_question = {}
    for i, _ in enumerate(question_summaries, 1):
        qid = f'Q{i}'
        # Put every Chinese reference in every subproblem checklist.  The
        # agent may mark an irrelevant method ``reject`` with a reason, but a
        # silent omission would make it impossible to audit whether the source
        # was considered.
        by_question[qid] = [{
            'ref_ID': entry['ref_ID'],
            'citation_key': entry['citation_key'],
            'method': entry['method'],
            'decision': 'pending_agent_decision',
            'required_record': 'adopt|adapt|reject; adapt/adopt must state model change and boundary',
        } for entry in entries]
    return {
        'schema_version': '1.0',
        'required_chinese_count': required_chinese_count,
        'verified_chinese_count': len(chinese),
        'status': 'pending_model_decisions',
        'references': entries,
        'by_subproblem': by_question,
        'instructions': '模型建立与求解前，逐个 Qn 将 pending_agent_decision 改为 adopt/adapt/reject，并在 model_contract 的 literature_basis 与 innovation_delta 中留下正文锚点。',
    }


def _build_citation_map(insights, question_summaries):
    """构建 citation_map.json — 章节到引用的映射表。"""
    cmap = {
        '_metadata': {
            'generated_at': datetime.now().isoformat(),
            'description': '章节→引用映射表，供 D3 写作时对照使用；每条引用必须说明作用',
            'research_evidence_version': '1.0',
        },
        # The writer fills this existing map with claim-level evidence after
        # the model and result files are frozen; no second claim database is
        # introduced.
        'claim_evidence': [],
        'section_2.1_literature_survey': ['_all_' ],  # 全部引用都在2.1节
        'roles': {
            str(ins.get('paper_index', ins.get('ref_ID'))): ins.get(
                'role',
                {'theoretical': 'method_basis',
                 'application': 'measurement_precedent',
                 'competition_paper': 'comparison_boundary'}.get(
                    ins.get('_distribution_category', 'theoretical'), 'method_basis'
                )
            )
            for ins in insights
        },
        'citation_keys': {
            str(ins.get('ref_ID', ins.get('paper_index'))): ins.get('citation_key', '')
            for ins in insights
        },
        'roles_by_citation_key': {
            ins.get('citation_key', ''): ins.get(
                'role',
                {'theoretical': 'method_basis',
                 'application': 'measurement_precedent',
                 'competition_paper': 'comparison_boundary'}.get(
                    ins.get('_distribution_category', 'theoretical'), 'method_basis'
                )
            )
            for ins in insights if ins.get('citation_key')
        },
        'method_transfer_required': True,
        'method_transfer_map': 'method_transfer_map.json',
    }

    for i, q_text in enumerate(question_summaries[:4], 1):
        section_key = f'section_Q{i}_modeling'
        relevant = [ins for ins in insights if f'Q{i}' in ins.get('applicable_to', [])]
        # Keep the original numeric list for compatibility with existing consumers;
        # expose the stable-key binding beside it for new traceability gates.
        cmap[section_key] = [str(ins.get('paper_index', ins.get('ref_ID'))) for ins in relevant]
        cmap[f'{section_key}_citations'] = [
            {'ref_ID': str(ins.get('paper_index', ins.get('ref_ID'))),
             'citation_key': ins.get('citation_key', '')}
            for ins in relevant
        ]

    return cmap


def run_survey(problem_graph, fingerprint, competition='cumcm', year=2026,
               qn='A', replay_root=None, chinese_sources_path=None,
               literature_sources_path=None):
    """运行完整文献调研流程。

    Args:
        problem_graph: dict, 包含 questions[], direction_zh, real_world_constraints[] 等
        fingerprint: dict, Problem Fingerprint
        competition: str, 竞赛名称缩写如 'cumcm', 'mcm', 'huashu'
        year: int, 比赛年份
        qn: str, 题目编号如 'A', 'B1', 'C'
        replay_root: str, 可选，指定项目-owned 输出根目录；未提供时读取
            CONTEST_WORKSPACE_ROOT，最后使用当前项目目录。技能目录本身不允许作为输出根目录。
        chinese_sources_path: str, 兼容旧参数；优先使用 literature_sources_path
        literature_sources_path: str, 用户提供的中英文文献元数据与摘要 YAML/JSON

    Returns:
        dict with keys:
          - report_md: str, 五段式文献调研报告（可直接粘贴到论文）
          - references: list, references.yaml 数据
          - citation_map: dict, citation_map.json 数据
          - search_summary: dict, 检索统计信息
    """
    requirements = _literature_requirements(problem_graph, fingerprint, competition)
    required_chinese_count = requirements['counts']['chinese']['minimum']
    required_english_count = requirements['counts']['english']['minimum']
    competition_dir = f'{competition}_{year}_{qn}'
    replay_root = _resolve_replay_root(replay_root)

    output_dir = os.path.join(replay_root, competition_dir)
    os.makedirs(output_dir, exist_ok=True)
    request_files = _write_literature_request(output_dir, requirements)
    source_input = literature_sources_path or chinese_sources_path
    user_sources, source_errors, user_source_path = _load_user_literature_sources(
        source_input, output_dir
    )
    chinese_sources = [item for item in user_sources if item.get('language') == 'zh']
    english_sources = [item for item in user_sources if item.get('language') == 'en']
    search_summary = {
        'queries_generated': 0,
        'directions': [item['task'] for item in requirements['coverage']],
        'competition_profile': competition,
        'required_chinese_count': required_chinese_count,
        'required_english_count': required_english_count,
        'source_ownership': 'user',
        'agent_read_boundary': 'abstract_and_metadata_only',
        'literature_request_files': request_files,
    }

    all_papers = user_sources
    search_summary['raw_papers'] = len(all_papers)
    search_summary['after_dedup'] = len(all_papers)
    search_summary['verified_chinese_count'] = len(chinese_sources)
    search_summary['verified_english_count'] = len(english_sources)
    search_summary['source_file'] = user_source_path

    policy_errors = []
    total_count = len(user_sources)
    if total_count < TOTAL_MIN:
        policy_errors.append(f'文献总数 {total_count} 篇，低于下限 {TOTAL_MIN} 篇')
    if total_count > TOTAL_MAX:
        policy_errors.append(f'文献总数 {total_count} 篇，超过上限 {TOTAL_MAX} 篇')
    if len(chinese_sources) < required_chinese_count:
        policy_errors.append(f'中文文献仅 {len(chinese_sources)} 篇，无法覆盖 {required_chinese_count} 个小问')
    if len(english_sources) < required_english_count:
        policy_errors.append(f'英文文献仅 {len(english_sources)} 篇，最低要求为 {required_english_count} 篇')
    required_questions = {item['question_id'] for item in requirements['coverage']}
    covered_questions = {
        str(question).upper()
        for source in user_sources
        for question in (source.get('candidate_questions', []) or [])
    }
    chinese_covered_questions = {
        str(question).upper()
        for source in chinese_sources
        for question in (source.get('candidate_questions', []) or [])
    }
    english_covered_questions = {
        str(question).upper()
        for source in english_sources
        for question in (source.get('candidate_questions', []) or [])
    }
    missing_chinese_questions = sorted(required_questions - chinese_covered_questions)
    if missing_chinese_questions:
        policy_errors.append(f'中文文献未覆盖小问: {", ".join(missing_chinese_questions)}')
    english_coverage_recommendation_met = required_questions.issubset(english_covered_questions)
    search_summary['covered_questions'] = sorted(required_questions & covered_questions)
    search_summary['missing_questions'] = sorted(required_questions - covered_questions)
    search_summary['literature_policy'] = {
        'total_count': total_count,
        'hard_total_range': [TOTAL_MIN, TOTAL_MAX],
        'recommended_total_range': [RECOMMENDED_TOTAL_MIN, RECOMMENDED_TOTAL_MAX],
        'recommended_total_met': RECOMMENDED_TOTAL_MIN <= total_count <= RECOMMENDED_TOTAL_MAX,
        'chinese_covered_questions': sorted(required_questions & chinese_covered_questions),
        'missing_chinese_questions': missing_chinese_questions,
        'english_covered_questions': sorted(required_questions & english_covered_questions),
        'english_coverage_recommendation_met': english_coverage_recommendation_met,
    }
    if not english_coverage_recommendation_met:
        search_summary['literature_policy']['recommendations'] = [
            '英文文献建议覆盖全部小问；当前不满足该建议，但不阻断后续节点。'
        ]
    if policy_errors or source_errors:
        reasons = source_errors + policy_errors
        pause_payload = {
            'schema_version': '1.0', 'status': 'PAUSE',
            'reason': 'user_literature_required',
            'requirements_file': request_files[1],
            'source_file': user_source_path,
            'validation_errors': reasons,
            'resume_with': 'literature_sources.yaml',
        }
        pause_path = os.path.join(output_dir, 'literature_pause.json')
        with open(pause_path, 'w', encoding='utf-8') as handle:
            json.dump(pause_payload, handle, ensure_ascii=False, indent=2)
        search_summary.update({
            'status': 'PAUSE', 'pause_reason': 'user_literature_required',
            'pause_files': request_files + [pause_path],
            'validation_errors': reasons,
        })
        return {
            'status': 'PAUSE', 'report_md': '', 'references': [], 'citation_map': {},
            'method_transfer_map': {}, 'search_summary': search_summary,
            'files_written': request_files + [pause_path],
        }

    # Step 3.5: 用户提交的硬范围已在上方校验；不为分布目标裁剪有效来源。
    final_papers, dist_stats, dist_warnings, dist_notes = [], {}, [], []
    if all_papers:
        final_papers = list(all_papers)
        dist_stats = {
            'raw_hits': total_count,
            'total': total_count,
            'recommended_total_met': RECOMMENDED_TOTAL_MIN <= total_count <= RECOMMENDED_TOTAL_MAX,
            'english_coverage_recommendation_met': english_coverage_recommendation_met,
            'needs_human_intervention': False,
        }
        search_summary['distribution_control'] = {
            'mode': 'user_hard_range_no_trimming',
            **dist_stats,
        }
        for w in dist_warnings:
            print(f'[literature_survey] {w}')
        for n in dist_notes:
            print(f'[literature_survey] ⚡ {n}')

    else:
        dist_stats = {'before': {'total': 0}, 'after': {'total': 0},
                      'needs_human_intervention': True}
        dist_notes.append('⚠️ 用户未提供可用文献，无法执行分布控制。')
        dist_stats['intervention_reasons'] = [{'action': 'manual_cnki_search', 'urgency': 'critical',
                                               'message': '所有API均未返回结果。'}]

    # Distribution targets are advisory; the two user-supplied Chinese
    # records are contractual and must survive category trimming.
    _mark_chinese_pause_resumed(output_dir, len(chinese_sources), user_source_path)

    # Step 4: 提炼可迁移点（用最终筛选后的文献列表）
    insights = _extract_insights(final_papers if final_papers else all_papers, problem_graph, fingerprint)
    if insights:
        # 给每条分配正式 ref_ID
        for i, ins in enumerate(insights, 1):
            ins['ref_ID'] = i
            ins['citation_key'] = ins.get('citation_key') or _citation_key_for(
                ins.get('title'), ins.get('authors'), ins.get('year'),
                'zh' if ins.get('language') in {'zh', 'zh-cn', '中文', 'chinese'} else 'ref'
            )

    search_summary['papers_analyzed'] = len(insights)

    # Step 5: 按方法类别分组
    groups = _classify_by_method(insights)
    search_summary['method_categories'] = list(groups.keys())

    # Step 6: 识别研究缺口
    gaps = _identify_gaps(insights, fingerprint, problem_graph)

    # Step 7: 生成五段式报告（传入 dist_stats 用于标注低覆盖率等）
    report_md = _generate_five_section_report(fingerprint, groups, gaps, insights, problem_graph, dist_stats)
    references_yaml = _build_references_yaml(insights)
    citation_map = _build_citation_map(insights, problem_graph.get('questions', []))
    method_transfer_map = _build_method_transfer_map(
        insights, problem_graph.get('questions', []), required_chinese_count
    )

    # Step 8: 写入文件
    report_path = os.path.join(output_dir, 'literature_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)
    print(f'[literature_survey] ✅ 文献调研报告已写入: {report_path}')

    refs_path = os.path.join(output_dir, 'references.yaml')
    refs_lines = ['# 自动生成的参考文献列表（由 planner/literature_survey.py 生成）\n']
    for r in references_yaml:
        refs_lines.append(f'- ref_ID: {r["ref_ID"]}')
        for k, v in r.items():
            if k != 'ref_ID':
                refs_lines.append(f'  {k}: "{v}"' if isinstance(v, str) else f'  {k}: {json.dumps(v, ensure_ascii=False)}')
    with open(refs_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(refs_lines))
    print(f'[literature_survey] ✅ 参考文献列表已写入: {refs_path}')

    cmap_path = os.path.join(output_dir, 'citation_map.json')
    with open(cmap_path, 'w', encoding='utf-8') as f:
        json.dump(citation_map, f, ensure_ascii=False, indent=2)
    print(f'[literature_survey] ✅ 引用映射表已写入: {cmap_path}')

    transfer_path = os.path.join(output_dir, 'method_transfer_map.json')
    with open(transfer_path, 'w', encoding='utf-8') as f:
        json.dump(method_transfer_map, f, ensure_ascii=False, indent=2)
    print(f'[literature_survey] ✅ 文献方法迁移表已写入: {transfer_path}')

    search_summary['status'] = 'READY'
    search_summary['method_transfer_status'] = method_transfer_map.get('status', 'pending_model_decisions')
    return {
        'status': 'READY',
        'report_md': report_md,
        'references': references_yaml,
        'citation_map': citation_map,
        'method_transfer_map': method_transfer_map,
        'search_summary': search_summary,
        'files_written': [report_path, refs_path, cmap_path, transfer_path],
    }


def _self_test() -> int:
    """Run the opt-in user-source contract self-test; no network access."""
    test_fingerprint = {
        'primary': '优化决策',
        'subtype': '排程调度',
        'keywords': ['时间窗', '资源瓶颈', '能耗平衡'],
        'secondary': ['启发式', '动态规划'],
        'constraints': ['integer', 'nonlinear', 'temporal'],
        'objective': 'single',
        'data_scale': 'medium',
    }
    test_problem_graph = {
        'primary': '优化决策',
        'subtype': '排程调度',
        'questions': [
            '确定初始设备布局方案，最小化总成本',
            '设计动态调度策略，满足时间窗和产能约束',
            '优化能耗分配，平衡效率与碳排放指标',
            '评估不同扰动情景下的鲁棒性表现',
        ],
        'direction_zh': '排程调度与资源优化',
        'real_world_constraints': ['时间窗硬性约束', '设备故障不确定性'],
    }

    print('=== 文献调研模块自测 ===')
    with tempfile.TemporaryDirectory(prefix='contest_literature_selftest_') as replay_root:
        result = run_survey(
            test_problem_graph, test_fingerprint, 'test', 2026, 'A', replay_root=replay_root
        )
    if result.get('status') == 'PAUSE':
        print('文献调研处于 PAUSE，已生成文献需求卡和全文分析提示词；未进入正式报告生成。')
        return 3
    print(f'\n用户提供 {result["search_summary"].get("raw_papers", 0)} 条文献，校验后 {result["search_summary"].get("after_dedup", 0)} 条')
    print(f'提炼 {result["search_summary"].get("papers_analyzed", 0)} 篇可迁移文献')
    print(f'分类方法域: {result["search_summary"].get("method_categories", [])}')
    print('\n--- 五段式报告预览（前 500 字）---')
    print(result['report_md'][:500])
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='文献调研模块；正式项目由 contest-orchestrator 调用 run_survey。'
    )
    parser.add_argument(
        '--self-test', action='store_true',
        help='显式运行用户文献契约自测（没有网络访问）',
    )
    args = parser.parse_args(argv)
    if not args.self_test:
        parser.print_help()
        return 0
    return _self_test()


if __name__ == '__main__':
    raise SystemExit(main())
