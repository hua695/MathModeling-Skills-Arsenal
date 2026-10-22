# -*- coding: utf-8 -*-
"""一次性修复：把 WorkBuddy 入库时误标为 GLM 的 FD-115~FD-314 重新打标为 WorkBuddy。
（ID 区间由 WBP 合并批次精确对应：入库前 FD=114，WBP 批次 +200 → 115..314）
"""
import re, argparse
from pathlib import Path

def main(argv=None):
    parser = argparse.ArgumentParser(description='修正 WorkBuddy 经验来源标签；默认只预览。')
    parser.add_argument('--skill-root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--apply', action='store_true', help='确认后写回 failure_database.md。')
    parser.add_argument('--dry-run', action='store_true', help='只预览变更（默认行为）。')
    args = parser.parse_args(argv)
    apply_changes = bool(args.apply and not args.dry_run)
    p = Path(args.skill_root) / 'failure_database.md'
    txt = open(p, encoding='utf-8').read()

    def repl(m):
        n = int(m.group(1))
        tag = 'WorkBuddy' if 115 <= n <= 314 else m.group(2)
        return f'## FD-{n}（公开经验库·{tag}）'

    new = re.sub(r'^## FD-(\d+)（公开经验库·(Kimi|豆包|GLM|WorkBuddy)）', repl, txt, flags=re.M)
    if apply_changes:
        open(p, 'w', encoding='utf-8').write(new)
    n = len(re.findall(r'^## FD-1(1[5-9]|[2-9][0-9])（公开经验库·WorkBuddy）', new, re.M))
    print(f"{'完成' if apply_changes else '预计修正'}。修正条数: {n}")


if __name__ == '__main__':
    main()
