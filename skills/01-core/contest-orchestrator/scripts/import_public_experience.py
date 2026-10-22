# -*- coding: utf-8 -*-
"""
公开经验库导入器：解析豆包采集的 dataset/public_replay/*/ 5-yaml 案例，
校验后写入 memory/inbox/（待人工审核），生成审核清单。
不入正式库——过 Human Review 后由 maintainer 手动/脚本并入。

用法:
    python scripts/import_public_experience.py <dataset目录> [--inbox <memory/inbox>]
"""
import os, sys, re, csv, json, argparse, shutil
from pathlib import Path

SKILL = str(Path(__file__).resolve().parents[1])
INBOX = os.path.join(SKILL, 'memory', 'inbox')


def parse_yaml_keyvals(text):
    """解析简单 yaml: key: value / - key: value 列表"""
    top = {}
    lists = {}
    current_list, current_item = None, None
    for line in text.splitlines():
        s = line.rstrip()
        if not s.strip() or s.startswith('#') or s.startswith('//'):
            continue
        stripped = s.lstrip()
        indent = len(s) - len(stripped)
        if s.startswith('- ') and indent > 0:
            body = stripped[2:].strip()
            if ':' in body:
                k, v = body.split(':', 1)
                if current_list is not None:
                    current_item = dict(current_item or {})
                    current_item[k.strip()] = v.strip().strip('"').strip("'")
                    lists.setdefault(current_list, []).append(current_item)
        elif indent == 0 and ':' in s:
            k, v = s.split(':', 1)
            k = k.strip(); v = v.strip()
            if not v:  # 列表开头
                current_list = k
                lists[k] = lists.get(k, [])
            else:
                top[k.strip()] = v.strip().strip('"').strip("'")
        elif indent > 0 and ':' in s and current_item is not None:
            k, v = stripped.split(':', 1)
            current_item[k.strip()] = v.strip().strip('"').strip("'")
    return top, lists


def safe_text(s):
    s = str(s or '')
    return s.replace('\n', ' ').strip()


def import_case(case_dir, case_id):
    """解析一个案例目录，返回 (问题画像, 模型, 决策, 失败, 策略)"""
    result = {'case_id': case_id, 'files': {}}
    for fname in ['problem_graph.yaml', 'model_choice.yaml', 'decision_trace.yaml',
                  'failure_memory.yaml', 'strategy.yaml']:
        fp = os.path.join(case_dir, fname)
        if os.path.exists(fp):
            txt = open(fp, encoding='utf-8', errors='ignore').read()
            top, lists = parse_yaml_keyvals(txt)
            result['files'][fname] = {'top': top, 'lists': lists}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description='导入公开经验到待审核 inbox；默认只预览，不写入。')
    parser.add_argument('ds', nargs='?', default='dataset/public_replay', help='公开回放目录。')
    parser.add_argument('--inbox', default=INBOX, help='待审核 inbox 目录。')
    parser.add_argument('--apply', action='store_true', help='确认后复制证据并写入审核清单。')
    parser.add_argument('--dry-run', action='store_true', help='只预览变更（默认行为）。')
    args = parser.parse_args(argv)
    apply_changes = bool(args.apply and not args.dry_run)
    ds = args.ds
    inbox = args.inbox
    if not os.path.isdir(ds):
        parser.error(f'公开回放目录不存在: {ds}')
    if apply_changes:
        os.makedirs(os.path.join(inbox, 'public_cases'), exist_ok=True)

    cases = []
    for d in sorted(os.listdir(ds)):
        dp = os.path.join(ds, d)
        if os.path.isdir(dp):
            cid = d
            cases.append((cid, dp))

    manifest = []
    valid = 0
    for cid, dp in cases:
        c = import_case(dp, cid)
        pg = c['files'].get('problem_graph.yaml', {}).get('top', {})
        mc = c['files'].get('model_choice.yaml', {}).get('top', {})
        fm = c['files'].get('failure_memory.yaml', {}).get('lists', {}).get('failures', [])
        st = c['files'].get('strategy.yaml', {}).get('lists', {}).get('strategies', [])
        src = pg.get('source', pg.get('来源', ''))
        conf = pg.get('confidence', '低')
        has_source = bool(src and src not in ('无', 'None', ''))
        manifest.append({
            'case_id': cid, 'problem_type': pg.get('problem_type', pg.get('type', '')),
            'domain': pg.get('domain', ''), 'model': mc.get('chosen', ''),
            'n_failures': len(fm), 'n_strategies': len(st),
            'source': safe_text(src), 'confidence': conf,
            'has_source': has_source, 'valid': has_source,
        })
        if has_source:
            valid += 1
        # 写入 inbox（原始证据，含来源）
        if apply_changes:
            os.makedirs(os.path.join(inbox, 'public_cases', cid), exist_ok=True)
        for fname in ['problem_graph.yaml', 'model_choice.yaml', 'decision_trace.yaml',
                      'failure_memory.yaml', 'strategy.yaml']:
            fp = os.path.join(dp, fname)
            if os.path.exists(fp):
                if apply_changes:
                    shutil.copy2(fp, os.path.join(inbox, 'public_cases', cid, fname))

    # 审核清单
    csv_path = os.path.join(inbox, 'public_review_manifest.csv')
    if apply_changes:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(manifest[0].keys()) if manifest else [])
            w.writeheader()
            w.writerows(manifest)

    no_src = [m['case_id'] for m in manifest if not m['has_source']]
    print(f'扫描案例: {len(cases)} | 有效(有来源): {valid} | 缺来源: {len(no_src)}')
    if no_src: print(f'  缺来源案例: {no_src[:10]}...')
    status = '已写入' if apply_changes else '预览完成，未写入'
    print(f'{status}。原始证据目标: {inbox}/public_cases/')
    print(f'审核清单目标: {csv_path}')


if __name__ == '__main__':
    main()
