# -*- coding: utf-8 -*-
"""去重：删除 W9 已覆盖题目的旧 WBP（占位版）条目，只留最好的。
按 case ID 匹配：W9 案例 ID 集合 → 找 wb_src 对应案例的旧 source → 删正式库中 source 匹配的块。
只删 W9 覆盖题的旧 WBP，其余 33 题旧 WBP 保留。
"""
import os, re, argparse
from pathlib import Path

SKILL = str(Path(__file__).resolve().parents[1])
parser = argparse.ArgumentParser(description='按外部回放目录去重经验库；不会猜测用户目录。')
parser.add_argument('--wb-src', required=True, help='历史 wb_src 案例目录')
parser.add_argument('--wb9', required=True, help='W9 案例目录')
parser.add_argument('--apply', action='store_true', help='确认后删除正式库中的重复条目。')
parser.add_argument('--dry-run', action='store_true', help='只预览删除数量（默认行为）。')
args = parser.parse_args()
APPLY = bool(args.apply and not args.dry_run)
WB_SRC = os.path.abspath(args.wb_src)
WB9 = os.path.abspath(args.wb9)
if not os.path.isdir(WB_SRC) or not os.path.isdir(WB9):
    parser.error('--wb-src 与 --wb9 必须是存在的目录')
DBS = {
    'FD': os.path.join(SKILL, 'failure_database.md'),
    'SD': os.path.join(SKILL, 'success_database.md'),
    'ST': os.path.join(SKILL, 'strategy_memory.md'),
    'DM': os.path.join(SKILL, 'memory', 'decision_memory.md'),
}


def parse_source(case_dir):
    pg = os.path.join(case_dir, 'problem_graph.yaml')
    if not os.path.exists(pg):
        return None
    txt = open(pg, encoding='utf-8', errors='ignore').read()
    res, sec = {}, False
    for line in txt.splitlines():
        s = line.rstrip()
        if s.startswith('source:'):
            sec = True
            continue
        if sec and s[:2] == '  ' and ':' in s:
            k, v = s.strip().split(':', 1)
            res[k.strip()] = v.strip().strip('"')
    title = res.get('title', '').strip('"')
    url = res.get('url', '')
    year = res.get('year', '')
    parts = [x for x in [title, url, year] if x]
    return '|'.join(parts) if parts else None


def case_id_of(dirname):
    return dirname.split('_')[0]


# W9 已覆盖的 case ID（剔除 P072 部分）
w9_ids = {case_id_of(d) for d in os.listdir(WB9) if os.path.isdir(os.path.join(WB9, d))}
w9_ids.discard('P072')

# 找 wb_src 里这些 ID 的旧 source
old_sources = set()
matched_ids = set()
for d in os.listdir(WB_SRC):
    dp = os.path.join(WB_SRC, d)
    if not os.path.isdir(dp):
        continue
    cid = case_id_of(d)
    if cid in w9_ids:
        src = parse_source(dp)
        if src:
            old_sources.add(src)
            matched_ids.add(cid)

print(f'W9 覆盖 {len(w9_ids)} 题 → 匹配到 wb_src 旧 source {len(old_sources)} 个')
missing = w9_ids - matched_ids
if missing:
    print('未匹配到旧 source 的 ID:', sorted(missing))

removed = {k: 0 for k in DBS}
for kind, path in DBS.items():
    txt = open(path, encoding='utf-8').read()
    # 分块：## ID ... 到下一个 ## 或文件尾
    blocks = re.split(r'(?m)^(?=## )', txt)
    keep = []
    for b in blocks:
        m = re.search(r'source:\s*(.+)', b)
        drop = False
        if m and m.group(1).strip() in old_sources:
            drop = True
        if drop:
            removed[kind] += 1
        else:
            keep.append(b)
    if APPLY:
        open(path, 'w', encoding='utf-8').write(''.join(keep))

print(f"{'已删除' if APPLY else '预计删除'}旧WBP条目:", removed)
