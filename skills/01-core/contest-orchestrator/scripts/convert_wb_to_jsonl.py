# -*- coding: utf-8 -*-
"""
WorkBuddy 数据集转换器：dataset/public_replay/<P0xx_标题>/*.yaml (5文件/例)
→ 流水线 JSONL（与 import_public_jsonl.py 兼容的 schema）。
映射:
  problem_graph → case_card: category→problem_type, domain, objective, source(title|url|year), confidence
  model_choice  → SD: final_choice→model_chosen, reason→model_reason, limitations
  decision_trace→ DM: steps[{action,reason,abandoned}] → [{action,reason,alternative,result:''}]
  failure_memory→ FD: failures[{method,root_cause,signal,lesson}] → [{method,failure:root_cause,cause,signal,lesson}]
  strategy      → ST: {applicable_scenarios,strategy,why_effective} → [{scenario,strategy,reason}]
用法: python scripts/convert_wb_to_jsonl.py
"""
import os, json, argparse
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]

CAT = {'数据预测': '预测', '优化决策': '优化决策', '评价分类': '评价分类',
       '物理建模': '物理建模', '图模型': '图模型'}


def clean(s):
    return str(s or '').strip().strip('"').strip("'")


def parse_scalars(txt, keys):
    d = {}
    for line in txt.splitlines():
        s = line.rstrip()
        if not s or s.startswith('#'):
            continue
        if not s.startswith(' ') and ':' in s:
            k, v = s.split(':', 1)
            k = k.strip()
            if k in keys:
                d[k] = clean(v)
    return d


def parse_source(txt):
    res, sec = {}, False
    for line in txt.splitlines():
        s = line.rstrip()
        if s.startswith('source:'):
            sec = True
            continue
        if sec:
            if s[:2] == '  ' and ':' in s:
                k, v = s.strip().split(':', 1)
                res[k.strip()] = clean(v)
            elif s and not s.startswith(' ') and ':' in s:
                break
    return res


def parse_dict_list(txt, key):
    items, cur, in_key = [], None, False
    for line in txt.splitlines():
        s = line.rstrip()
        stripped = s.lstrip()
        if not stripped or stripped.startswith('#'):
            continue
        indent = len(s) - len(stripped)
        if stripped.startswith(key + ':') and indent == 0:
            in_key = True
            continue
        if not in_key:
            continue
        if stripped.startswith('- ') and indent > 0:
            if cur:
                items.append(cur)
            cur = {}
            body = stripped[2:].strip()
            if ':' in body:
                k, v = body.split(':', 1)
                cur[k.strip()] = clean(v)
        elif cur is not None and indent > 0 and ':' in stripped:
            k, v = stripped.split(':', 1)
            cur[k.strip()] = clean(v)
        elif indent == 0:
            if cur:
                items.append(cur)
                cur = None
            in_key = False
    if cur:
        items.append(cur)
    return items


def parse_scalar_list(txt, key):
    items, in_key = [], False
    for line in txt.splitlines():
        s = line.rstrip()
        stripped = s.lstrip()
        if not stripped or stripped.startswith('#'):
            continue
        indent = len(s) - len(stripped)
        if stripped.startswith(key + ':') and indent == 0:
            in_key = True
            continue
        if not in_key:
            continue
        if stripped.startswith('- ') and indent > 0:
            items.append(clean(stripped[2:]))
        elif indent == 0 and ':' in s:
            in_key = False
    return items


def convert(case_dir):
    def rd(fname):
        fp = os.path.join(case_dir, fname)
        return open(fp, encoding='utf-8', errors='replace').read() if os.path.exists(fp) else ''

    pg = parse_scalars(rd('problem_graph.yaml'), ['case_id', 'category', 'domain', 'objective', 'confidence'])
    src = parse_source(rd('problem_graph.yaml'))
    mc = parse_scalars(rd('model_choice.yaml'), ['final_choice', 'reason'])
    st_txt = rd('strategy.yaml')
    st = parse_scalars(st_txt, ['strategy', 'why_effective'])
    scenarios = parse_scalar_list(st_txt, 'applicable_scenarios')

    category = pg.get('category', '')
    failures = [{'method': it.get('method', ''), 'failure': it.get('root_cause', ''),
                 'cause': it.get('root_cause', ''), 'signal': it.get('signal', ''),
                 'lesson': it.get('lesson', '')}
                for it in parse_dict_list(rd('failure_memory.yaml'), 'failures')]
    decisions = [{'action': it.get('action', ''), 'reason': it.get('reason', ''),
                  'alternative': it.get('abandoned', ''), 'result': ''}
                 for it in parse_dict_list(rd('decision_trace.yaml'), 'steps')]
    source_str = '|'.join([x for x in [src.get('title', ''), src.get('url', ''), src.get('year', '')] if x])

    return {
        'case_id': pg.get('case_id', os.path.basename(case_dir).split('_')[0]),
        'problem_type': CAT.get(category, category),
        'domain': pg.get('domain', ''),
        'objective': pg.get('objective', ''),
        'model_chosen': mc.get('final_choice', ''),
        'model_reason': mc.get('reason', ''),
        'model_limitations': parse_scalar_list(rd('model_choice.yaml'), 'limitations'),
        'failures': failures,
        'strategies': [{'scenario': '；'.join(scenarios), 'strategy': st.get('strategy', ''),
                        'reason': st.get('why_effective', '')}],
        'decisions': decisions,
        'source': source_str,
        'confidence': pg.get('confidence', '中'),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description='将 WorkBuddy 5-yaml 案例转换为 JSONL。')
    parser.add_argument('base', nargs='?', default=str(SKILL_ROOT / 'dataset' / 'public_replay'),
                        help='案例目录，默认使用技能内 dataset/public_replay。')
    parser.add_argument('out', nargs='?', default=str(SKILL_ROOT / 'dataset' / 'public_replay' / 'raw' / 'cases_wb.jsonl'),
                        help='输出 JSONL，默认写入案例目录 raw/cases_wb.jsonl。')
    args = parser.parse_args(argv)
    base = Path(args.base).expanduser()
    out = Path(args.out).expanduser()
    if not base.is_dir():
        print(f'案例目录不存在: {base}')
        return 1
    dirs = sorted(os.listdir(base))
    cases, stat = [], {'no_pg': 0, 'no_model': 0, 'no_fail': 0, 'no_strat': 0, 'no_src': 0}
    for d in dirs:
        dp = str(base / d)
        if not os.path.isdir(dp):
            continue
        c = convert(dp)
        cases.append(c)
        if not c['problem_type']: stat['no_pg'] += 1
        if not c['model_chosen']: stat['no_model'] += 1
        if not c['failures']: stat['no_fail'] += 1
        if not c['strategies'][0]['strategy']: stat['no_strat'] += 1
        if not c['source']: stat['no_src'] += 1

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

    total_fd = sum(len(c['failures']) for c in cases)
    total_st = sum(len(c['strategies']) for c in cases)
    total_dm = sum(len(c['decisions']) for c in cases)
    print(f'转换案例: {len(cases)} → FD={total_fd} SD={len(cases)} ST={total_st} DM={total_dm}')
    print(f'缺problem_type: {stat["no_pg"]} | 缺模型: {stat["no_model"]} | 缺失败: {stat["no_fail"]} | 缺策略: {stat["no_strat"]} | 缺来源: {stat["no_src"]}')
    print(f'输出: {out}')
    if cases:
        print('样例(P001):', json.dumps(cases[0], ensure_ascii=False)[:400])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
