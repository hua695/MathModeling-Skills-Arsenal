#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/benchmark_retrieval.py — v3.7 检索 A/B 基准（语义检索升级的证据工具）

用"手工标注的 golden 集"对比新旧检索：
  OLD = retrieve(use_semantic=False)  # v3.6 纯字符指纹
  NEW = retrieve(use_semantic=True)   # v3.7 字符指纹 + 字符 n-gram TF-IDF（+可选 embedding）

指标：
  recall@12 : 每条查询 top-12 中是否出现 ≥1 个标注相关条目（"能想起相关经验"）
  MRR       : 第一个相关条目的排名的倒数均值（"相关经验排多靠前"）
  expansion : 语义召回扩展命中（字符匹配根本漏掉的条目）

用法:
  python scripts/benchmark_retrieval.py           # 跑基准
  python scripts/benchmark_retrieval.py --list    # 列出各查询的候选条目（人工标注辅助）
  python scripts/benchmark_retrieval.py --show Q1 # 单查询新旧 top-12 明细
"""
import os
import re
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL)

from memory.retrieval import retrieve, load_entries  # noqa: E402

DB_FILES = {
    'FD': os.path.join(SKILL, 'failure_database.md'),
    'SD': os.path.join(SKILL, 'success_database.md'),
    'ST': os.path.join(SKILL, 'strategy_memory.md'),
    'DM': os.path.join(SKILL, 'memory', 'decision_memory.md'),
}

_ID_RE = re.compile(r'^#+\s*(FD|SD|ST|DM)-(\d+)')


def load_entries_with_ids():
    """与 load_entries() 相同解析，但把标题里的 id（## FD-001 ...）注入 _id，
    供 ST 这类 yaml 内无 id 的条目也有稳定标签。"""
    entries = []
    for kind, path in DB_FILES.items():
        if not os.path.exists(path):
            continue
        txt = open(path, encoding='utf-8').read()
        cur_id = None
        lines = txt.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            m = _ID_RE.match(line.strip())
            if m:
                cur_id = f'{m.group(1)}-{m.group(2)}'
            elif line.strip().startswith('```yaml') and cur_id:
                block = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    block.append(lines[i])
                    i += 1
                d = {}
                for bl in block:
                    if ':' in bl:
                        k, v = bl.split(':', 1)
                        d[k.strip()] = v.strip()
                d['_kind'] = kind
                d['_id'] = cur_id
                entries.append(d)
            i += 1
    return entries


# ---- golden 集：人工标注（依据条目内容与真实竞赛题对应关系）----
# 标注原则：条目内容确实命中该查询的主题/场景（problem_type/标题/正文可验证），
# 与检索算法无关的独立判断。每条 ≥2 个相关条目才入集。
GOLDEN = [
    {
        'name': 'Q1 多波束测线(2023B 几何覆盖)',
        'fp': {'primary': '优化决策', 'subtype': ['几何覆盖'], 'keywords': ['测线', '多波束', '覆盖宽度', '重叠率'],
               'constraints': ['海底地形']},
        'labels': ['FD-648', 'FD-649', 'FD-650', 'SD-347', 'ST-40', 'ST-336',
                   'SD-363', 'SD-364', 'SD-366', 'SD-408', 'SD-409', 'SD-411'],  # 2026-08-16 golden 更新：50篇提取新增 2023B 多波束条目
    },
    {
        'name': 'Q2 穿越沙漠(2020B 多阶段决策)',
        'fp': {'primary': '优化决策', 'keywords': ['穿越沙漠', '路径', '资源', '天气'], 'constraints': ['多阶段']},
        'labels': ['FD-21', 'FD-22', 'FD-318', 'SD-14', 'SD-208', 'ST-18', 'ST-211', 'DM-620'],
    },
    {
        'name': 'Q3 CT成像标定(2017A)',
        'fp': {'primary': '物理建模', 'keywords': ['CT', '成像', '标定', '反演'], 'constraints': ['模板']},
        'labels': ['FD-337', 'FD-571', 'FD-572', 'SD-227', 'SD-329', 'ST-230', 'ST-315', 'DM-682'],
    },
    {
        'name': 'Q4 信号频谱反演',
        'fp': {'primary': '物理建模', 'subtype': ['信号处理'], 'keywords': ['频谱', '反演', '光学厚度', '干涉']},
        'labels': ['FD-008', 'SD-004', 'ST-007'],
    },
    {
        'name': 'Q5 图模型/网络流',
        'fp': {'primary': '图模型', 'subtype': ['网络流'], 'keywords': ['网络流', '仿真', '路径']},
        'labels': ['FD-606', 'FD-607', 'FD-608', 'SD-337'],
    },
    {
        'name': 'Q6 组合优化几何布图',
        'fp': {'primary': '组合优化', 'subtype': ['几何布图'], 'keywords': ['装箱', '布图', '死区率', 'skyline']},
        'labels': ['FD-001', 'FD-13', 'FD-14', 'SD-001', 'SD-7', 'DM-001', 'ST-002'],
    },
    {
        'name': 'Q7 预测+时序+小样本',
        'fp': {'primary': '预测', 'keywords': ['时序', '时间序列', 'LSTM', 'ARIMA'], 'data_scale': 'small'},
        'labels': ['FD-45', 'FD-46', 'FD-52', 'SD-33', 'SD-34', 'SD-40', 'ST-001',
                   'FD-697', 'FD-698', 'FD-751', 'FD-752', 'DM-1209', 'DM-1297'],  # 2026-08-16 golden 更新：50篇提取新增时序条目
    },
    {
        'name': 'Q8 光学物理机理',
        'fp': {'primary': '物理建模', 'subtype': ['光学'], 'keywords': ['材料参数', '单位换算', '吸收带']},
        'labels': ['FD-006', 'FD-007', 'FD-36', 'FD-110', 'SD-24', 'ST-006'],
    },
    {
        'name': 'Q9 数据一致性/复现',
        'fp': {'primary': '任意', 'keywords': ['数据一致性', '复现', '结果溯源', '参数口径']},
        'labels': ['FD-003', 'FD-002'],
    },
    {
        'name': 'Q10 AIGC/论文写作',
        'fp': {'primary': '任意', 'keywords': ['AIGC', '降重', '人话', '模板句']},
        'labels': ['FD-005'],
    },
    # Retrieval benchmark coverage: strategy/decision cases, paraphrases, rare terms and cold start.
    {
        'name': 'Q11 电力调度储能(ST/DM重)',
        'fp': {'primary': '优化决策', 'keywords': ['储能', '电力', '调度', '新能源'], 'constraints': ['多目标']},
        'labels': ['ST-330', 'ST-331', 'ST-332', 'ST-333', 'DM-1140', 'DM-1141', 'DM-1142', 'DM-1143'],
    },
    {
        'name': 'Q12 图像识别目标检测',
        'fp': {'primary': '评价分类', 'subtype': ['图像识别'], 'keywords': ['目标检测', '图像', '识别']},
        'labels': ['FD-111', 'FD-189', 'FD-190', 'FD-365'],
    },
    {
        'name': 'Q13 排队论服务台',
        'fp': {'primary': '优化决策', 'keywords': ['排队', '服务台', '等待时间', '队列']},
        'labels': ['FD-73', 'FD-225', 'FD-367', 'FD-611'],
    },
    {
        'name': 'Q14 设施选址警力调度',
        'fp': {'primary': '优化决策', 'subtype': ['选址优化'], 'keywords': ['选址', '警力', '调度', '覆盖约束']},
        'labels': ['FD-227', 'FD-380', 'FD-591', 'FD-592', 'FD-96'],
    },
    {
        'name': 'Q15 生产排班路径优化',
        'fp': {'primary': '图模型', 'subtype': ['排班'], 'keywords': ['排班', '路径', '巡检']},
        'labels': ['FD-340', 'FD-601', 'FD-602'],
    },
    {
        'name': 'Q16 条带扫描海底测绘(同义改写)',
        'fp': {'primary': '优化决策', 'keywords': ['条带', '声呐', '测绘', '航迹'], 'constraints': ['重叠率']},
        'labels': ['ST-336', 'SD-347', 'FD-648'],
    },
    {
        'name': 'Q17 帕累托多目标权衡(中英混排)',
        'fp': {'primary': '优化决策', 'keywords': ['NSGA-II', 'Pareto', '多目标', '权衡'], 'constraints': ['非支配']},
        'labels': ['DM-1141', 'SD-002', 'SD-003', 'ST-005',
                   'SD-372', 'SD-417', 'SD-344'],  # 2026-08-16 golden 更新：50篇提取新增 NSGA-II 混合编码条目
    },
    {
        'name': 'Q18 电池寿命预测(冷门预测)',
        'fp': {'primary': '预测', 'keywords': ['电池', '循环', '老化', '寿命'], 'data_scale': 'medium'},
        'labels': ['FD-61', 'FD-93', 'FD-129', 'FD-359'],
    },
    {
        'name': 'Q19 无人机测绘航线',
        'fp': {'primary': '优化决策', 'keywords': ['无人机', '航线', '测绘', '重叠率']},
        'labels': ['FD-88', 'FD-402', 'FD-403'],
        # 2026-08-16 已知边界案例：50 篇提取后新增大量"无人机"条目（2022B 编队定位/2025A 烟幕遮蔽），
        # 它们命中"无人机"关键词霸榜 top-12，把 FD-88（测绘航线，sim 2.117，排名第 15）挤出。
        # 属库膨胀后的排名拥挤，非检索 bug；FD-88 若扩 top-15 即可命中。暂保持 top-12 口径。
    },
    {
        'name': 'Q20 量子物理调度(冷启动)',
        'fp': {'primary': '量子物理', 'subtype': ['量子计算'], 'keywords': ['量子比特', '退相干', '量子门']},
        'labels': [],  # 库外题型 → 期望 weak/cold_start，测降级路径
    },
    {
        'name': 'Q21 脑机接口信号(冷启动)',
        'fp': {'primary': '神经科学', 'keywords': ['脑机接口', '脑电', 'EEG', '神经信号']},
        'labels': [],  # 库外题型 → 期望 weak/cold_start，测降级路径
    },
    {
        'name': 'Q22 LSTM时序预测(中英混排)',
        'fp': {'primary': '预测', 'keywords': ['LSTM', 'RNN', '时序', '神经网络'], 'data_scale': 'small'},
        'labels': ['SD-16', 'SD-33', 'SD-145', 'ST-45', 'ST-65'],
    },
]


def entry_title(e):
    """条目可读标签：id + problem_type/scenario 摘要"""
    pt = e.get('problem_type') or e.get('scenario') or e.get('context') or ''
    return f"{e.get('_id') or e.get('_kind')}·{str(pt)[:30]}"


def list_candidates():
    entries = load_entries_with_ids()
    for g in GOLDEN:
        qtext = ' '.join([g['fp'].get('primary', '')] + (g['fp'].get('subtype') or [])
                         + (g['fp'].get('keywords') or []))
        hits = []
        for e in entries:
            blob = ' '.join(str(v) for k, v in e.items() if k not in ('_kind', '_id'))
            if qtext and any(tok and tok in blob for tok in qtext.split()):
                hits.append(e)
        print(f"\n### {g['name']}")
        for e in hits[:14]:
            print('   ', entry_title(e))
        print('    候选数:', len(hits))


def _run_query(g, entries, use_semantic):
    """（基准主逻辑在 main() 内联实现，保留此函数作为 retrieve 正确性冒烟）"""
    prior = retrieve(g['fp'], top=12, use_semantic=use_semantic, entries=entries)
    return prior


def main():
    if '--list' in sys.argv:
        list_candidates()
        return
    entries = load_entries_with_ids()
    from memory import retrieval as R
    from memory.ranking import final_score

    def legacy_char_score(e, fp):
        """复刻 v3.6 原版 fingerprint_match_score（含空 problem_type 恒命中 bug）"""
        et = (e.get('problem_type') or '')
        primary = fp.get('primary', '')
        blob = ' '.join(str(v) for k, v in e.items() if k not in ('_kind', 'failure_id', 'success_id', 'strategy_id', 'decision_id'))
        score = 0.0
        if primary:
            if primary in et or et in primary:
                score += 1.0
            else:
                pb, eb = R._bigrams(primary), R._bigrams(et)
                if pb and eb and len(pb & eb) >= max(2, len(min(pb, eb, key=len)) // 2):
                    score += 0.7
        else:
            score += 0.5
        for st in fp.get('subtype', []):
            if st and st in blob:
                score += 0.5
        for kw in list(fp.get('keywords', [])) + list(fp.get('secondary', [])):
            if kw and kw in blob:
                score += 0.3
        ds = fp.get('data_scale', '')
        if ds in R._SCALE_KW:
            for kw in R._SCALE_KW[ds]:
                if kw in blob:
                    score += 0.2
                    break
        for c in fp.get('constraints', []):
            if c in blob:
                score += 0.15
        src = e.get('source') or ''
        for kw in fp.get('keywords', []):
            if kw and kw in src:
                score += 0.8
                break
        return score if score > 0 else 0.0

    def eid(e):
        return e.get('_id') or e.get('failure_id') or e.get('success_id') \
            or e.get('strategy_id') or e.get('decision_id') or '?'

    def top12_ids(g, mode):
        """mode: v36(复刻原版) / fix(修复+分档) / sem(修复+语义+分档)。
        fix/sem 直接复用生产代码 R._score_candidates + R.rank_and_cut（避免复刻漂移）；
        v36 复刻仅作对照（含空 problem_type 恒命中 bug + final_score 无界 metadata）。"""
        fp = g['fp']
        if mode == 'v36':
            scored = []
            for e in entries:
                c = legacy_char_score(e, fp)
                if c > 0:
                    scored.append((c, e))
            scored.sort(key=lambda x: final_score(x[0], x[1]), reverse=True)
            return [eid(e) for _, e in scored[:12]], 0
        scored, _n_char, _n_char_strong, n_expand, _info = R._score_candidates(entries, fp, use_semantic=(mode == 'sem'))
        ranked = R.rank_and_cut(scored, 12)
        return [eid(e) for _, _, _, _, e in ranked[:12]], n_expand

    print(f'{"查询":<28}{"v36召回":>8}{"fix召回":>8}{"sem召回":>8}{"v36MRR":>8}{"fixMRR":>8}{"semMRR":>8}{"v36#":>5}{"fix#":>5}{"sem#":>5}')
    print('-' * 88)
    total = {'v36_r': 0, 'fix_r': 0, 'sem_r': 0, 'v36_m': 0.0, 'fix_m': 0.0, 'sem_m': 0.0,
             'v36_c': 0, 'fix_c': 0, 'sem_c': 0}
    n_q = 0
    n_cold = 0
    for g in GOLDEN:
        lab = set(g['labels'])
        if not lab:
            # 冷启动探针（无相关经验）：不计入召回均值，单列
            v36_ids, _ = top12_ids(g, 'v36')
            sem_ids, n_exp = top12_ids(g, 'sem')
            n_cold += 1
            print(f'{g["name"]:<28}{"-":<8}{"-":<8}{"-":<8}{"-":<8}{"-":<8}{"-":<8}'
                  f'{"":<5}{"":<5}{"":<5} (冷启动探针)')
            continue
        n_q += 1
        v36_ids, _ = top12_ids(g, 'v36')
        fix_ids, _ = top12_ids(g, 'fix')
        sem_ids, n_exp = top12_ids(g, 'sem')

        def recall(ids): return 1.0 if lab & set(ids) else 0.0
        def mrr(ids):
            for rank, i in enumerate(ids, 1):
                if i in lab:
                    return 1.0 / rank
            return 0.0
        def count(ids): return len(lab & set(ids))
        r36, rf, rs = recall(v36_ids), recall(fix_ids), recall(sem_ids)
        m36, mf, ms = mrr(v36_ids), mrr(fix_ids), mrr(sem_ids)
        c36, cf, cs = count(v36_ids), count(fix_ids), count(sem_ids)
        total['v36_r'] += r36; total['fix_r'] += rf; total['sem_r'] += rs
        total['v36_m'] += m36; total['fix_m'] += mf; total['sem_m'] += ms
        total['v36_c'] += c36; total['fix_c'] += cf; total['sem_c'] += cs
        print(f'{g["name"]:<28}{r36:<8.0f}{rf:<8.0f}{rs:<8.0f}{m36:<8.3f}{mf:<8.3f}{ms:<8.3f}{c36:<5}{cf:<5}{cs:<5}')
    print('-' * 88)
    if n_q:
        print(f'{"均值":<28}{total["v36_r"]/n_q:<8.2f}{total["fix_r"]/n_q:<8.2f}{total["sem_r"]/n_q:<8.2f}'
              f'{total["v36_m"]/n_q:<8.3f}{total["fix_m"]/n_q:<8.3f}{total["sem_m"]/n_q:<8.3f}'
              f'{total["v36_c"]/n_q:<5.1f}{total["fix_c"]/n_q:<5.1f}{total["sem_c"]/n_q:<5.1f}')
        print(f'（均值基于 {n_q} 条有标签查询；冷启动探针 {n_cold} 条不计入）')
    # 单查询明细
    show = None
    for a in sys.argv:
        if a.startswith('--show'):
            show = a.split('=')[1] if '=' in a else 'Q1'
    if show:
        for g in GOLDEN:
            if g['name'].startswith(show + ' '):
                o, _ = top12_ids(g, 'v36')
                f, _ = top12_ids(g, 'fix')
                n, n_exp = top12_ids(g, 'sem')
                lab = set(g['labels'])
                print(f"\n{show} 明细 (标注: {sorted(lab)})")
                print('v36:', ' '.join(o))
                print('fix:', ' '.join(f))
                print('sem:', ' '.join(n), f'| 语义扩展 {n_exp} 条')


if __name__ == '__main__':
    main()
