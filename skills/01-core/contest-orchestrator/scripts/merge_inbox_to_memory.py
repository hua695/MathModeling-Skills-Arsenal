# -*- coding: utf-8 -*-
"""
择优合并：把 inbox 待审核经验（多来源）择优并入正式记忆库。
策略：
  1. 来源优先级 Kimi(P*) > 豆包(DP*) > WorkBuddy(WBP*) > 千问(QWP*) > GLM(GP*)
  2. 同赛题跨来源去重，保留优先级最高的
  3. GLM 占位(recommend:是) / 模糊来源(未知) 降权或剔除
  4. 重新分配正式 FD/SD/ST/DM ID 并入 .md 库
用法: python scripts/merge_inbox_to_memory.py
"""
import os, re, glob, csv

# 技能根用脚本相对路径定位（兼容 ~/.claude/skills、~/.agents/skills、~/.workbuddy/skills 多安装位）
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(SKILL, 'memory', 'inbox', 'public_cases')
FD = os.path.join(SKILL, 'failure_database.md')
SD = os.path.join(SKILL, 'success_database.md')
ST = os.path.join(SKILL, 'strategy_memory.md')
DM = os.path.join(SKILL, 'memory', 'decision_memory.md')
IDX = os.path.join(SKILL, 'memory', 'index.yaml')

# 已知跨来源重复（低优先级源 → 保留高优先级源）
# 格式: 低优先级case → 保留的高优先级case（None=剔除）
DEDUP = {
    'GP019': 'P002',   # 沙漠(动态规划) 重复
    'GP013': 'P017',   # 乙醇(C4烯烃) 重复
    'GP017': 'P007',   # 波浪能 重复
    'GP016': 'P008',   # 供应链 重复
    'GP008': 'P004',   # 交易策略 重复
    'DP008': 'P006',   # 农作物 重复
}
# 模糊来源关键词（GLM 常见）
VAGUE = ['CSDN文库', '未知', 'MATLAB实用程序', '汪国强']


# 来源注册表：前缀 → (rank, tag, filter_placeholder, source_quality默认, memory_type默认)
# rank 越小优先级越高；内容冲突时保留 rank 小的来源
# filter_placeholder=True 时对空/占位 recommend 过滤（GLM 特有）
# 真实实战(human_replay)默认 source_quality=高 + memory_type=human_replay（检索 rank 优先）
SOURCES = [
    ('P',      0, 'Kimi',      False, '中', 'paper_extract'),
    ('DP',     1, '豆包',      False, '中', 'paper_extract'),
    ('SWAP',   1, '互换',      False, '高', 'human_replay'),
    ('HSB2026', 1, '华数杯实战', False, '高', 'human_replay'),
    ('CM2024B', 1, '国赛实战', False, '高', 'human_replay'),
    ('CM2023B', 1, '国赛实战', False, '高', 'human_replay'),
    ('CM2021B', 1, '国赛实战', False, '高', 'human_replay'),
    ('CM2011B', 1, '国赛实战', False, '高', 'human_replay'),
    ('WBP',    2, 'WorkBuddy', False, '中', 'paper_extract'),
    ('W9P',    2, 'WorkBuddy9', False, '中', 'paper_extract'),
    ('QWP',    3, '千问',      False, '低', 'llm_extract'),
    ('HYP',    3, '混元',      False, '中', 'llm_extract'),
    ('GP',     4, 'GLM',       True,  '低', 'llm_extract'),
]


def source_info(cid):
    for prefix, rank, tag, filter_ph, sq, mt in SOURCES:
        if cid.startswith(prefix):
            return rank, tag, filter_ph, sq, mt
    return 9, '公开', False, '中', 'paper_extract'


def source_rank(cid):
    return source_info(cid)[0]


def read_yaml_block(path):
    txt = open(path, encoding='utf-8').read()
    m = re.search(r'```yaml\n(.*?)\n```', txt, re.S)
    return m.group(1) if m else ''


def parse_yaml_fields(block):
    d = {}
    for line in block.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            d[k.strip()] = v.strip()
    return d


def next_id(path, prefix):
    txt = open(path, encoding='utf-8').read()
    nums = [int(m) for m in re.findall(rf'{prefix}-(\d+)', txt)]
    return max(nums) + 1 if nums else 1


def append_block(path, pid, d):
    block = f'## {pid}（公开经验库·{d.pop("source_tag", "")}）\n\n```yaml\n'
    for k, v in d.items():
        block += f'{k}: {v}\n'
    block += '```\n'
    with open(path, 'a', encoding='utf-8') as f:
        f.write('\n---\n\n' + block)


def quality_ok(d, cid):
    """质量门：来源可信 + 非占位（占位启发式仅作用于 GLM 来源）"""
    src = d.get('source', '')
    if any(v in src for v in VAGUE):
        return False
    _, _, filter_ph, _, _ = source_info(cid)
    if filter_ph and 'recommend' in d and (d.get('recommend', '') == '是' or d.get('recommend', '').strip() == ''):
        return False  # 占位来源过滤
    return True


def load_existing(path):
    """读取 .md 库现有条目为 dict 列表"""
    txt = open(path, encoding='utf-8').read()
    entries = []
    for b in re.findall(r'```yaml\n(.*?)\n```', txt, re.S):
        d = {}
        for line in b.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                d[k.strip()] = v.strip()
        entries.append(d)
    return entries


def fingerprint(d, kind):
    """内容指纹：同一库内相同内容视为重复（幂等 + 库内去重）"""
    if kind == 'FD':
        return (d.get('method', ''), d.get('failure', ''), d.get('lesson', ''))
    if kind == 'SD':
        return (d.get('method', ''), d.get('why_success', ''))
    if kind == 'ST':
        return (d.get('scenario', ''), d.get('strategy', ''))
    return (d.get('decision', ''), d.get('reason', ''))


def main():
    cases = {}
    for case_dir in sorted(os.listdir(INBOX)):
        cid = case_dir
        card_p = os.path.join(INBOX, case_dir, 'case_card.yaml')
        if not os.path.exists(card_p):
            continue
        card = parse_yaml_fields(read_yaml_block(card_p))
        cases[cid] = {'card': card, 'dir': os.path.join(INBOX, case_dir)}

    # 排序：按来源优先级
    ordered = sorted(cases.keys(), key=source_rank)

    # 去重：同一低优先级 case 若被 DEDUP 映射，跳过
    selected = []
    for cid in ordered:
        if cid in DEDUP:
            print(f'[去重] {cid} 与 {DEDUP[cid]} 重复，保留高优先级 {DEDUP[cid]}')
            continue
        selected.append(cid)

    total = {'FD': 0, 'SD': 0, 'ST': 0, 'DM': 0}
    merged = []
    # 现有库内容指纹（幂等 + 库内去重）
    seen = {k: {fingerprint(e, k) for e in load_existing(p)}
            for k, p in [('FD', FD), ('SD', SD), ('ST', ST), ('DM', DM)]}
    for cid in selected:
        cd = cases[cid]['dir']
        card = cases[cid]['card']
        src = card.get('source', '')
        tag = f"{card.get('source_tag','')}"
        for f in ['fd_', 'sd_', 'st_', 'dm_']:
            for y in sorted(glob.glob(os.path.join(cd, f + '*.yaml'))):
                d = parse_yaml_fields(read_yaml_block(y))
                d['source'] = src
                d['confidence'] = card.get('confidence', '中')
                if not d.get('source_quality'):
                    d['source_quality'] = source_info(cid)[3]  # 来源默认质量（实战=高）
                if not d.get('memory_type'):
                    d['memory_type'] = source_info(cid)[4]     # 来源默认类型（实战=human_replay）
                if not quality_ok(d, cid):
                    print(f'[过滤] {cid}/{os.path.basename(y)}: 质量不达标（占位/模糊来源）')
                    continue
                kind = f.upper()[:2]
                fp = fingerprint(d, kind)
                if fp in seen[kind]:
                    print(f'[去重] {cid}/{os.path.basename(y)}: 与现有库重复，跳过')
                    continue
                seen[kind].add(fp)
                if f == 'fd_':
                    pid = f'FD-{next_id(FD,"FD")}'
                    d['failure_id'] = pid; d['source_tag'] = source_info(cid)[1]
                    append_block(FD, pid, d); total['FD'] += 1
                elif f == 'sd_':
                    pid = f'SD-{next_id(SD,"SD")}'
                    d['success_id'] = pid; d['source_tag'] = '公开'
                    append_block(SD, pid, d); total['SD'] += 1
                elif f == 'st_':
                    pid = f'ST-{next_id(ST,"ST")}'
                    d['strategy_id'] = pid; d['source_tag'] = '公开'
                    append_block(ST, pid, d); total['ST'] += 1
                elif f == 'dm_':
                    pid = f'DM-{next_id(DM,"DM")}'
                    d['decision_id'] = pid; d['source_tag'] = '公开'
                    append_block(DM, pid, d); total['DM'] += 1
        merged.append(cid)

    print(f'\n择优并入: {len(selected)} 案例 → FD={total["FD"]} SD={total["SD"]} ST={total["ST"]} DM={total["DM"]}')
    print(f'合并案例: {merged}')



if __name__ == '__main__':
    main()
