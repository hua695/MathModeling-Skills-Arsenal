#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/extract_and_import_batch.py — 国赛优秀论文批次提取+入库（一键流程）

用法:
    python scripts/extract_and_import_batch.py --batch 2023     # 提取指定批次文本
    python scripts/extract_and_import_batch.py --extract <dir>  # 对已提取文本运行结构化提取
    python scripts/extract_and_import_batch.py --import-json <dir>  # 汇总 extracted/*.json → 入库（蓝图归并 + FD/SD/ST/DM + WR inbox）

实际流程：
1. PDF → 文本（pymupdf 文本版 / rapidocr 扫描版）→ dataset/paper_texts/
2. 结构化提取 → dataset/extracted/*.json
3. 汇总 + 分类入库：
   - blueprint.propositions → memory/math_blueprints/MB-00X.yaml（题型修正后归并）
   - wr → memory/inbox（extract_wr.py --inbox）
   - fd/sd/st → 对应库文件
   - dm → memory/decision_memory.md
"""
import json
import os
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def summarize_extracted(ext_dir, out_path):
    """汇总 extracted/*.json → 六库清单（含题型修正）"""
    all_wr, all_fd, all_sd, all_st, all_dm, all_prop = [], [], [], [], [], []
    TYPE_FIX = {'2023国赛B': '机理', '2024国赛B': '机理'}
    for f in sorted(os.listdir(ext_dir)):
        if not f.endswith('.json'):
            continue
        j = json.load(open(os.path.join(ext_dir, f), encoding='utf-8'))
        src = j.get('source', '')
        for w in j.get('wr', []):
            w['src_paper'] = src
            all_wr.append(w)
        for x in j.get('fd_sd_st', []):
            x['src_paper'] = src
            {'FD': all_fd, 'SD': all_sd, 'ST': all_st}.get(x.get('kind'), []).append(x)
        for d in j.get('dm', []):
            d['src_paper'] = src
            all_dm.append(d)
        bp = j.get('blueprint', {})
        bt = bp.get('problem_type', '?')
        for prefix, fix in TYPE_FIX.items():
            if src.startswith(prefix):
                bt = fix
        for p in bp.get('propositions', []):
            p['src_paper'] = src
            p['bp_type'] = bt
            all_prop.append(p)
    summary = {'wr': all_wr, 'fd': all_fd, 'sd': all_sd, 'st': all_st,
               'dm': all_dm, 'prop': all_prop}
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    print(f'汇总: WR {len(all_wr)} / FD {len(all_fd)} / SD {len(all_sd)} / '
          f'ST {len(all_st)} / DM {len(all_dm)} / props {len(all_prop)}')
    return summary


def merge_blueprint_props(summary):
    """propositions 归并进母蓝图（MB_MAP 题型→蓝图）"""
    MB_MAP = {'优化': 'MB-001', '机理': 'MB-002', '预测': 'MB-003'}
    FILES = {'MB-001': 'MB-001_optimization.yaml', 'MB-002': 'MB-002_mechanism.yaml',
             'MB-003': 'MB-003_prediction.yaml'}
    by_mb = {'MB-001': [], 'MB-002': [], 'MB-003': []}
    for p in summary['prop']:
        by_mb[MB_MAP.get(p.get('bp_type', ''), 'MB-001')].append(p)

    total = 0
    for mb, props in by_mb.items():
        path = os.path.join(SKILL, 'memory', 'math_blueprints', FILES[mb])
        text = open(path, encoding='utf-8').read()
        lines = text.split('\n')
        prop_idx = next((i for i, ln in enumerate(lines) if ln.strip() == 'propositions:'), None)
        if prop_idx is None:
            print(f'[WARN] {mb} 无 propositions 段')
            continue
        insert_at = len(lines)
        for j in range(prop_idx + 1, len(lines)):
            if re.match(r'^[a-z_]+:', lines[j]):
                insert_at = j
                break
        existing = set(re.findall(r'^  - name: (.+)$', '\n'.join(lines[prop_idx:insert_at]), re.M))
        added = 0
        new_lines = []
        for p in props:
            name = p.get('name', '')
            if not name or name in existing:
                continue
            tpl = p.get('template', '').replace('\n', ' ')
            new_lines.append(f'  - name: {name}\n    template: "{tpl}"\n'
                             f'    provenance: "{p.get("src_paper", "")}"\n')
            existing.add(name)
            added += 1
        if new_lines:
            lines.insert(insert_at, '\n'.join(new_lines))
            open(path, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
            total += added
            print(f'{mb}: +{added} props')
    print(f'蓝图归并合计: +{total}')


def main():
    args = sys.argv[1:]
    if '--summary' in args:
        ext_dir = args[args.index('--summary') + 1]
        out = args[args.index('--out') + 1] if '--out' in args else \
            os.path.join(os.environ.get('TEMP', '.'), 'batch_summary.json')
        s = summarize_extracted(ext_dir, out)
        if '--merge-bp' in args:
            merge_blueprint_props(s)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
