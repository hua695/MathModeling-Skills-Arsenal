# -*- coding: utf-8 -*-
"""公开经验 JSONL 导入器：豆包采集的案例 → memory/inbox 待审核条目。
每案例拆成 FD(失败) / SD(成功模型) / ST(策略) / DM(决策)，带 source+confidence。
"""
import os, sys, json, re, csv, argparse

# 用脚本相对路径定位 skill 根（不硬编码 ~/.claude——workbuddy 装在 ~/.workbuddy 会写错 inbox，同类坑见 retrieval.py）
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(SKILL, 'memory', 'inbox')


def clean(s):
    return str(s or '').replace('\n', ' ').strip()


def yaml_block(pid, d):
    lines = [f'## {pid}（公开经验库，待审核）', '', '```yaml']
    for k, v in d.items():
        lines.append(f'{k}: {v}')
    lines += ['```', '']
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description='将公开经验 JSONL 导入待审核 inbox；默认只预览。')
    parser.add_argument('jsonl', nargs='?', default='dataset/public_replay/raw/cases_batch1.jsonl')
    parser.add_argument('--prefix', default='')
    parser.add_argument('--source', default='公开')
    parser.add_argument('--apply', action='store_true', help='确认后写入 inbox 和审核清单。')
    parser.add_argument('--dry-run', action='store_true', help='只预览数量（默认行为）。')
    args = parser.parse_args(argv)
    apply_changes = bool(args.apply and not args.dry_run)
    jl = args.jsonl
    prefix = args.prefix
    source_name = args.source
    if not os.path.isfile(jl):
        parser.error(f'JSONL 文件不存在: {jl}')
    cases = [json.loads(l) for l in open(jl, encoding='utf-8') if l.strip()]
    if prefix:
        for c in cases:
            c['case_id'] = prefix + c['case_id']
    if not apply_changes:
        total = {
            'FD': sum(len(c.get('failures', [])) for c in cases),
            'SD': sum(1 for c in cases if c.get('model_chosen')),
            'ST': sum(len(c.get('strategies', [])) for c in cases),
            'DM': sum(len(c.get('decisions', [])) for c in cases),
        }
        print(f'预览完成，未写入：案例 {len(cases)} | FD={total["FD"]} SD={total["SD"]} ST={total["ST"]} DM={total["DM"]}')
        return 0
    os.makedirs(os.path.join(INBOX, 'public_cases'), exist_ok=True)
    manifest = []
    total = {'FD': 0, 'SD': 0, 'ST': 0, 'DM': 0}

    for c in cases:
        cid = c['case_id']
        src = clean(c.get('source', ''))
        conf = c.get('confidence', '低')
        ptype = c.get('problem_type', '')
        has_src = bool(src and src not in ('无', 'None'))
        d = os.path.join(INBOX, 'public_cases', cid)
        os.makedirs(d, exist_ok=True)

        # 原始卡片
        card = {'case_id': cid, 'problem_type': ptype, 'domain': c.get('domain', ''),
                'objective': c.get('objective', ''), 'model_chosen': c.get('model_chosen', ''),
                'source': src, 'confidence': conf}
        with open(os.path.join(d, 'case_card.yaml'), 'w', encoding='utf-8') as f:
            f.write(yaml_block(f'P-{cid}', card))

        # FD 失败
        for i, fm in enumerate(c.get('failures', [])):
            pid = f'FD-PUB-{cid}-{i+1}'
            entry = {'failure_id': pid, 'problem_type': ptype, 'domain': c.get('domain', ''),
                     'method': clean(fm.get('method', '')), 'failure': clean(fm.get('failure', '')),
                     'cause': clean(fm.get('cause', '')), 'signal': clean(fm.get('signal', '')),
                     'lesson': clean(fm.get('lesson', '')), 'avoid': clean(fm.get('avoid', '')),
                     'source': src, 'confidence': conf}
            with open(os.path.join(d, f'fd_{i+1}.yaml'), 'w', encoding='utf-8') as f:
                f.write(yaml_block(pid, entry))
            total['FD'] += 1

        # SD 成功模型
        if c.get('model_chosen'):
            pid = f'SD-PUB-{cid}'
            entry = {'success_id': pid, 'problem_type': ptype, 'method': c.get('model_chosen', ''),
                     'why_success': c.get('model_reason', ''), 'result': c.get('objective', ''),
                     'limitations': '；'.join(c.get('model_limitations', []))[:200],
                     'source': src, 'confidence': conf}
            with open(os.path.join(d, 'sd_model.yaml'), 'w', encoding='utf-8') as f:
                f.write(yaml_block(pid, entry))
            total['SD'] += 1

        # ST 策略
        for i, st in enumerate(c.get('strategies', [])):
            pid = f'ST-PUB-{cid}-{i+1}'
            entry = {'strategy_id': pid, 'scenario': clean(st.get('scenario', '')),
                     'strategy': clean(st.get('strategy', '')), 'reason': clean(st.get('reason', '')),
                     'recommend': clean(st.get('recommend', '')), 'source': src, 'confidence': conf}
            with open(os.path.join(d, f'st_{i+1}.yaml'), 'w', encoding='utf-8') as f:
                f.write(yaml_block(pid, entry))
            total['ST'] += 1

        # DM 决策
        for i, dm in enumerate(c.get('decisions', [])):
            pid = f'DM-PUB-{cid}-{i+1}'
            entry = {'decision': clean(dm.get('action', '')), 'phase': ptype,
                     'reason': clean(dm.get('reason', '')), 'alternative': clean(dm.get('alternative', '')),
                     'result': clean(dm.get('result', '')), 'source': src, 'confidence': conf}
            with open(os.path.join(d, f'dm_{i+1}.yaml'), 'w', encoding='utf-8') as f:
                f.write(yaml_block(pid, entry))
            total['DM'] += 1

        manifest.append({'case_id': cid, 'problem_type': ptype, 'domain': c.get('domain', ''),
                         'n_fd': len(c.get('failures', [])), 'n_st': len(c.get('strategies', [])),
                         'n_dm': len(c.get('decisions', [])), 'confidence': conf, 'has_source': has_src})

    csv_path = os.path.join(INBOX, 'public_review_manifest.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        w.writeheader(); w.writerows(manifest)

    no_src = [m['case_id'] for m in manifest if not m['has_source']]
    print(f'处理案例: {len(cases)} | FD={total["FD"]} SD={total["SD"]} ST={total["ST"]} DM={total["DM"]}')
    print(f'缺来源: {len(no_src)} {no_src if no_src else ""}')
    print(f'inbox: {INBOX}/public_cases/')
    print(f'审核清单: {csv_path}')



if __name__ == '__main__':
    main()
