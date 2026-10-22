# -*- coding: utf-8 -*-
"""
比赛经验导入器 v2：兼容编程手实际导出格式。
支持 replay.json / decision_log.json / failures.yaml / successes.yaml / strategies.yaml / parameters.json
字段自动映射到 MathModel-Agent 记忆库 schema。
"""
import os, sys, json, re, datetime, argparse
from pathlib import Path

SKILL_DIR = str(Path(__file__).resolve().parents[1])
FD = os.path.join(SKILL_DIR, 'failure_database.md')
SD = os.path.join(SKILL_DIR, 'success_database.md')
ST = os.path.join(SKILL_DIR, 'strategy_memory.md')
DM = os.path.join(SKILL_DIR, 'memory', 'decision_memory.md')
IDX = os.path.join(SKILL_DIR, 'memory', 'index.yaml')
APPLY = False


def parse_yaml_items(text, list_key):
    """解析 YAML: 顶层 `list_key:` 下 `- field: value` 列表项"""
    items, current, in_list = [], None, False
    for line in text.splitlines():
        s = line.rstrip()
        if not s.strip() or s.startswith('#') or s.startswith('//'):
            continue
        stripped = s.lstrip()
        indent = len(s) - len(stripped)
        if indent == 0 and ':' in s and not s.startswith('-'):
            key = s.split(':', 1)[0].strip()
            in_list = (key == list_key)
            continue
        if in_list and stripped.startswith('- '):
            if current: items.append(current)
            current = {}
            body = stripped[2:].strip()
            if ':' in body:
                k, v = body.split(':', 1)
                current[k.strip()] = v.strip().strip('"').strip("'")
        elif in_list and current is not None and ':' in s:
            k, v = stripped.split(':', 1)
            current[k.strip()] = v.strip().strip('"').strip("'")
    if current: items.append(current)
    return items


def next_id(path, prefix):
    txt = open(path, encoding='utf-8').read()
    nums = [int(m) for m in re.findall(rf'{prefix}-(\d+)', txt)]
    return max(nums) + 1 if nums else 1


def yaml_block(pid, d):
    lines = [f'## {pid}', '', '```yaml']
    for k, v in d.items():
        lines.append(f'{k}: {v}')
    lines.append('```')
    lines.append('')
    return '\n'.join(lines)


def append(path, block):
    if not APPLY:
        return
    with open(path, 'a', encoding='utf-8') as f:
        f.write('\n---\n\n' + block)


def main(argv=None):
    global APPLY
    parser = argparse.ArgumentParser(description='导入经验到正式记忆库；默认只预览，不写入。')
    parser.add_argument('src', nargs='?', default='.', help='经验来源目录。')
    parser.add_argument('--source', default='外部贡献', help='来源标签。')
    parser.add_argument('--apply', action='store_true', help='确认后写入正式记忆库。')
    parser.add_argument('--dry-run', action='store_true', help='只预览变更（默认行为）。')
    args = parser.parse_args(argv)
    APPLY = bool(args.apply and not args.dry_run)
    src = args.src
    source = args.source
    imported = []

    # ---- decision_log.json → DM（决策记忆，价值最高）----
    dp = os.path.join(src, 'decision_log.json')
    if os.path.exists(dp):
        log = json.load(open(dp, encoding='utf-8'))
        decs = log.get('decisions', log if isinstance(log, list) else [])
        for d in decs:
            did = f'DM-{next_id(DM, "DM")}'
            block = (f'## {did}\n\n```yaml\ndecision: {d.get("decision","")}\n'
                     f'phase: {d.get("phase","")}\ncontext: {d.get("context","")}\n'
                     f'reason: {d.get("rationale","")}\n'
                     f'params: {json.dumps(d.get("params",{}), ensure_ascii=False)}\n'
                     f'evidence: {d.get("evidence","")}\nresult: {d.get("result","")}\n```\n')
            append(DM, block)
            imported.append(f'决策 {did}: {d.get("decision","")[:30]}')
        print(f'[decision_log.json] 导入 {len(decs)} 条决策')

    # ---- YAML 三类：字段映射 ----
    # FD: method/failure/cause/signal/lesson/avoid
    fp = os.path.join(src, 'failures.yaml')
    if os.path.exists(fp):
        items = parse_yaml_items(open(fp, encoding='utf-8').read(), 'failures')
        for it in items:
            pid = f'FD-{next_id(FD, "FD")}'
            m = {'failure_id': pid, 'problem_type': '华数杯B·布图',
                 'method': it.get('method', ''), 'failure': it.get('failure', ''),
                 'cause': it.get('cause', ''), 'signal': it.get('signal', ''),
                 'lesson': it.get('lesson', ''), 'avoid': it.get('avoid', '')}
            append(FD, yaml_block(pid, m))
            imported.append(f'失败 {pid}: {it.get("method","")[:30]}')
        print(f'[failures.yaml] 导入 {len(items)} 条失败')

    # SD: method/outcome/why_it_worked/reproduce
    fp = os.path.join(src, 'successes.yaml')
    if os.path.exists(fp):
        items = parse_yaml_items(open(fp, encoding='utf-8').read(), 'successes')
        for it in items:
            pid = f'SD-{next_id(SD, "SD")}'
            m = {'success_id': pid, 'problem_type': '华数杯B·布图',
                 'method': it.get('method', ''), 'why_success': it.get('why_it_worked', ''),
                 'result': it.get('outcome', ''), 'reuse': it.get('reproduce', '')}
            append(SD, yaml_block(pid, m))
            imported.append(f'成功 {pid}: {it.get("method","")[:30]}')
        print(f'[successes.yaml] 导入 {len(items)} 条成功')

    # ST: name/when_to_use/how_to_apply/expected_gain/risk/example
    fp = os.path.join(src, 'strategies.yaml')
    if os.path.exists(fp):
        items = parse_yaml_items(open(fp, encoding='utf-8').read(), 'strategies')
        for it in items:
            pid = f'ST-{next_id(ST, "ST")}'
            m = {'strategy_id': pid, 'scenario': it.get('when_to_use', ''),
                 'strategy': it.get('name', ''), 'reason': it.get('expected_gain', ''),
                 'recommend': it.get('how_to_apply', ''), 'risk': it.get('risk', ''),
                 'example': it.get('example', '')}
            append(ST, yaml_block(pid, m))
            imported.append(f'策略 {pid}: {it.get("name","")[:30]}')
        print(f'[strategies.yaml] 导入 {len(items)} 条策略')

    # ---- replay.json（记录来源 + 汇总）----
    rp = os.path.join(src, 'replay.json')
    if os.path.exists(rp):
        rep = json.load(open(rp, encoding='utf-8'))
        print(f'[replay.json] 记录比赛: {rep.get("competition","")} | '
              f'角色: {rep.get("role","")} | 工具: {rep.get("ai_tools",[])}')

    # ---- index.yaml 登记来源 ----
    if os.path.exists(IDX):
        idx = open(IDX, encoding='utf-8').read()
        if source not in idx:
            if APPLY:
                with open(IDX, 'a', encoding='utf-8') as f:
                    f.write(f'\n  {source}:\n    failure: [外部导入]\n    success: [外部导入]\n    strategy: [外部导入]\n')
        index_status = '已登记来源' if APPLY else '待登记来源'
        print(f'[index.yaml] {index_status}: {source}')

    mode = '已写入' if APPLY else '预览完成，未写入'
    print(f'\n{mode}：共识别 {len(imported)} 条经验。来源: {source}')


if __name__ == '__main__':
    main()
