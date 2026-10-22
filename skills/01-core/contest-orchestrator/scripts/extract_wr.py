#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_wr.py — WR 经验追加工具（Presentation Intelligence Layer）

给 writing_database.md 追加 WR 条目：自动分配 WR-ID、按 pattern 去重、必填校验。

用法:
  # 追加一条（JSON，字段用双引号）
  python scripts/extract_wr.py --json "{\"section\":\"摘要\",\"context_type\":\"通用\",\"pattern\":\"...\",\"why\":\"...\",\"example\":\"...\",\"source\":\"...\"}"

  # 从 JSONL 批量追加（每行一条，同上字段）
  python scripts/extract_wr.py --file cases_wr.jsonl

  # 开源模型批量采集：先进 inbox 待审，不直接改主库
  python scripts/extract_wr.py --file kimi_wr.jsonl --inbox --prefix K1 --source "Kimi batch1"

  # 审核后并入主库
  python scripts/extract_wr.py --merge memory/inbox/wr/K1 --source "Kimi batch1"

  # 只查当前库统计 / 检查重复
  python scripts/extract_wr.py --stats

必填字段: section, pattern, example, source
可选字段: context_type(默认通用), situation, kind(pattern|trap), why, quality(默认中), memory_type(默认paper_extract),
         template(可填槽句式), stage(draft/revise/polish), bad_example+fix_example(kind=trap 时必填),
         expression_variants, provenance, feedback, competition_family

诚实规则: example 必须来自真实论文原文/明确转述；source 必须标竞赛|年份|题号|参赛编号。
"""
import argparse
import csv
import json
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Git Bash 下 __file__ 可能带有盘符前缀；归一化时去掉多余的盘符片段。
if os.name == 'nt':
    import re as _re
    _m = _re.match(r'^([A-Za-z]):\\c\\(.+)$', REPO, _re.IGNORECASE)
    if _m:
        REPO = f'{_m.group(1)}:\\{_m.group(2)}'
WR_DB = os.path.join(REPO, 'memory', 'writing_database.md')

REQUIRED = ['section', 'pattern', 'example', 'source']
OPTIONAL = ['context_type', 'situation', 'kind', 'why', 'quality', 'memory_type',
            'template', 'stage', 'bad_example', 'fix_example',
            'expression_variants', 'linked_fingerprint', 'linked_model_decision',
            'provenance', 'feedback', 'competition_family', 'aigc_risk']


def load_entries():
    if not os.path.exists(WR_DB):
        return []
    txt = open(WR_DB, encoding='utf-8').read()
    out = []
    for b in re.findall(r'```yaml\n(.*?)\n```', txt, re.S):
        d = {}
        for line in b.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                d[k.strip()] = v.strip()
        if d.get('wr_id'):
            out.append(d)
    return out


def next_id(entries):
    nums = [int(m) for m in re.findall(r'WR-(\d+)', open(WR_DB, encoding='utf-8').read())]
    return max(nums) + 1 if nums else 1


def validate(d):
    miss = [k for k in REQUIRED if not d.get(k)]
    if miss:
        raise ValueError(f'缺少必填字段: {miss}')
    # trap 类必须有反例和正例，供 Paper-Critic 自动扫描素材。
    if d.get('kind') == 'trap':
        for k in ('bad_example', 'fix_example'):
            if not d.get(k):
                raise ValueError(f'trap 条目缺必填字段: {k}（反例/正例是自动扫描素材）')
    if not (d['example'].strip().startswith('"') or len(d['example'].strip()) > 10):
        pass  # example 太短无法作为证据，下面单独警告
    return d


def dedup_conflict(new, entries):
    """按 pattern 前 20 字 + section 判重，返回已存在的 wr_id 或 None"""
    key = (new.get('section', ''), new.get('pattern', '').strip()[:20])
    for e in entries:
        if e.get('section') == key[0] and (e.get('pattern') or '').strip().startswith(new.get('pattern', '').strip()[:20]):
            return e.get('wr_id')
    return None


def _finalize(d, entries):
    """补缺省字段 + 分配正式 ID + 校验。返回可写入主库的完整 dict"""
    d = validate(d)
    conflict = dedup_conflict(d, entries)
    if conflict:
        print(f'跳过: 与 {conflict} 重复（同章节+同 pattern 前缀）')
        return None
    # 冲突检测：列出同 section 与 context_type 的已有条目，供人工判断是否矛盾或过泛。
    peers = [e['wr_id'] for e in entries
             if e.get('section') == d.get('section') and e.get('context_type') == d.get('context_type')
             and e.get('wr_id')]
    if peers:
        print(f'同类条目（同章节+同题型，人工对照风格一致性）: {", ".join(peers[:6])}')
    wid = f'WR-{next_id(entries):03d}'
    d['wr_id'] = wid
    d.setdefault('context_type', '通用')
    d.setdefault('kind', 'pattern')
    d.setdefault('quality', '中')
    d.setdefault('memory_type', 'paper_extract')
    d.setdefault('reuse_count', 0)
    d.setdefault('situation', '')
    d.setdefault('why', '')
    return d


def append_one(d, entries):
    d = _finalize(d, entries)
    if not d:
        return None
    wid = d['wr_id']
    yaml = '\n'.join(f'{k}: {v}' for k, v in d.items())
    entry = f'\n---\n\n## {wid} {d["pattern"][:24]}\n\n```yaml\n{yaml}\n```\n'
    with open(WR_DB, 'a', encoding='utf-8') as f:
        f.write(entry)
    print(f'已追加 {wid}（{d["section"]} / {d["kind"]}）')
    return wid


def inbox_write(d, prefix, entries):
    """写一条进 inbox 待审（不修改主库）。校验+主库查重只警告，留到 merge 时裁决。"""
    try:
        d = validate(d)
    except ValueError as e:
        print(f'校验失败: {e} → 丢弃')
        return False
    conflict = dedup_conflict(d, entries)
    status = f'与{conflict}重复' if conflict else 'OK'
    wid = f'WR-PUB-{prefix}-{len(os.listdir(_inbox_dir(prefix))) + 1:02d}'
    d.setdefault('wr_id', wid)
    d.setdefault('context_type', '通用')
    d.setdefault('kind', 'pattern')
    d.setdefault('quality', '中')
    d.setdefault('memory_type', 'paper_extract')
    d.setdefault('reuse_count', 0)
    d.setdefault('situation', '')
    d.setdefault('why', '')
    yaml = '\n'.join(f'{k}: {v}' for k, v in d.items())
    with open(os.path.join(_inbox_dir(prefix), f'{wid}.yaml'), 'w', encoding='utf-8') as f:
        f.write(f'## {wid}（待审核）\n\n```yaml\n{yaml}\n```\n')
    print(f'进 inbox: {wid}（{d["section"]} / {d["kind"]}）[{status}]')
    return True


def _inbox_dir(prefix):
    d = os.path.join(REPO, 'memory', 'inbox', 'wr', prefix)
    os.makedirs(d, exist_ok=True)
    return d


def merge_inbox(dirpath, source_name=''):
    """审核后并入主库：读 inbox 目录全部 yaml → 校验+查重 → append 主库 → 归档已并目录"""
    if not os.path.isdir(dirpath):
        print(f'inbox 目录不存在: {dirpath}')
        return 0
    entries = load_entries()
    merged = 0
    skipped = 0
    for fn in sorted(os.listdir(dirpath)):
        if not fn.endswith('.yaml'):
            continue
        fp = os.path.join(dirpath, fn)
        txt = open(fp, encoding='utf-8').read()
        d = {}
        for b in re.findall(r'```yaml\n(.*?)\n```', txt, re.S):
            for line in b.splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    d[k.strip()] = v.strip()
        d.pop('wr_id', None)          # 去掉待审临时 ID
        if source_name and not d.get('source'):
            d['source'] = source_name  # 只在缺 source 时补，不覆盖已有参赛编号（2026-08-13 教训：merge 曾覆盖108条source）
        if not append_one(d, entries):
            skipped += 1
            continue
        merged += 1
        entries = load_entries()      # 刷新
        # 归档已并条目（不删除，留痕）
        arch = os.path.join(dirpath, '_merged')
        os.makedirs(arch, exist_ok=True)
        shutil.move(fp, os.path.join(arch, fn))
    print(f'merge 完成：并入 {merged} 条，跳过 {skipped} 条 → {WR_DB}')
    return merged


def main():
    ap = argparse.ArgumentParser(description='WR 经验工具：追加 / 开源采集 inbox / 审核 merge')
    ap.add_argument('--json', help='单条 WR 字段 JSON')
    ap.add_argument('--file', help='JSONL 批量文件（每行一条）')
    ap.add_argument('--stats', action='store_true', help='统计当前库')
    ap.add_argument('--inbox', action='store_true', help='进 inbox 待审（不直接改主库）')
    ap.add_argument('--prefix', help='inbox 来源前缀（目录名，如 K1=Kimi批次1）')
    ap.add_argument('--merge', metavar='DIR', help='审核后并入主库（读 inbox 目录）')
    ap.add_argument('--source', default='', help='来源名（merge 时覆盖条目 source）')
    args = ap.parse_args()

    entries = load_entries()
    if args.stats:
        from collections import Counter
        sections = Counter(e.get('section', '?') for e in entries)
        kinds = Counter(e.get('kind', 'pattern') for e in entries)
        fam = Counter(e.get('competition_family', '(无)') for e in entries)
        active = sum(1 for e in entries if e.get('competition_family', '') != 'huaweibei')
        cold = sum(1 for e in entries if e.get('competition_family', '') == 'huaweibei')
        print(f'共 {len(entries)} 条 WR 经验')
        print(f'活跃库 {active} 条（默认检索，软上限400/硬600）| 华为杯冷存 {cold} 条（隔离不计入）')
        print('来源分布:', dict(fam))
        print('章节分布:', dict(sections))
        print('类型分布:', dict(kinds))
        return 0

    if args.merge:
        merge_inbox(args.merge, args.source)
        return 0

    added = 0
    skipped = 0
    if args.json:
        d = json.loads(args.json)
        ok = inbox_write(d, args.prefix or 'S', entries) if args.inbox else append_one(d, entries)
        if ok:
            added += 1
    if args.file:
        with open(args.file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    print(f'跳过(JSON 解析失败): {line[:60]}')
                    skipped += 1
                    continue
                ok = inbox_write(d, args.prefix or 'S', entries) if args.inbox else append_one(d, entries)
                if ok:
                    added += 1
                    if not args.inbox:
                        entries = load_entries()  # 直接入库时刷新，避免自相重复
    if skipped:
        print(f'共跳过 {skipped} 行（JSON 格式问题），其余已处理')
    if not any([args.stats, args.json, args.file, args.merge]):
        ap.print_help()
        return 1
    if added and not args.inbox:
        print(f'完成：新增 {added} 条 WR 经验 → {WR_DB}')
    if added and args.inbox:
        print(f'完成：{added} 条进 inbox 待审 → {_inbox_dir(args.prefix or "S")}')
        print('审核后并入：python scripts/extract_wr.py --merge <该目录> --source "<来源名>"')
    return 0


if __name__ == '__main__':
    sys.exit(main())
