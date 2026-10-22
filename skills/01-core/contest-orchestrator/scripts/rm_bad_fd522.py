# -*- coding: utf-8 -*-
"""删除被 bash 引号坑写坏的空 FD-522（自研·检索系统）块"""
import os, re, argparse
from pathlib import Path

def main(argv=None):
    parser = argparse.ArgumentParser(description='删除损坏的 FD-522 空块；默认只预览。')
    parser.add_argument('--skill-root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--apply', action='store_true', help='确认后写回 failure_database.md。')
    parser.add_argument('--dry-run', action='store_true', help='只预览变更（默认行为）。')
    args = parser.parse_args(argv)
    apply_changes = bool(args.apply and not args.dry_run)
    p = Path(args.skill_root) / 'failure_database.md'
    txt = open(p, encoding='utf-8').read()
    # 匹配 "## FD-522（自研·检索系统）" 开头、内容为空的块（到 --- 或下一个 ## 为止）
    new = re.sub(r'## FD-522（自研·检索系统）\n+(?:---\s*\n+)?', '', txt, count=1)
    if apply_changes:
        open(p, 'w', encoding='utf-8').write(new)
    print(f"{'已删除' if apply_changes else '预计删除'}空块。剩余 FD-522 计数: {len(re.findall(r'^## FD-522\b', new, re.M))}")


if __name__ == '__main__':
    main()
