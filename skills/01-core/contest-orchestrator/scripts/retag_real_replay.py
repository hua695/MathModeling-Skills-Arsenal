# -*- coding: utf-8 -*-
"""给已入库的真实实战 case（CM2023B/CM2024B/HSB2026C/SWAP001）补 source_quality=高 + memory_type=human_replay"""
import re, os, argparse
from pathlib import Path

PAT = re.compile(r'(2023高教社杯|2024高教社杯|2026华数杯)')
FENCE = '\n```'
CLOSE = '\nsource_quality: 高\nmemory_type: human_replay\n```'

def main(argv=None):
    parser = argparse.ArgumentParser(description='为真实 replay 经验补充来源质量标签；默认只预览。')
    parser.add_argument('--skill-root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--apply', action='store_true', help='确认后写回经验库。')
    parser.add_argument('--dry-run', action='store_true', help='只预览变更（默认行为）。')
    args = parser.parse_args(argv)
    apply_changes = bool(args.apply and not args.dry_run)
    dbs = {
        'FD': os.path.join(args.skill_root, 'failure_database.md'),
        'SD': os.path.join(args.skill_root, 'success_database.md'),
        'ST': os.path.join(args.skill_root, 'strategy_memory.md'),
        'DM': os.path.join(args.skill_root, 'memory', 'decision_memory.md'),
    }
    n = 0
    for kind, p in dbs.items():
        if not os.path.isfile(p):
            parser.error(f'经验库文件不存在: {p}')
        txt = open(p, encoding='utf-8').read()
        blocks = re.split(r'(?m)^(?=## )', txt)
        file_n = 0
        for i, b in enumerate(blocks):
            if 'source_quality' in b or not PAT.search(b):
                continue
            b2 = b.replace(FENCE, CLOSE)
            if b2 != b:
                blocks[i] = b2
                n += 1
                file_n += 1
        if apply_changes and file_n:
            # Only write the current file when this pass found a change in it.
            open(p, 'w', encoding='utf-8').write(''.join(blocks))
    print(f"{'已补标' if apply_changes else '预计补标'} {n} 条实战经验为 human_replay/source_quality高")


if __name__ == '__main__':
    main()
