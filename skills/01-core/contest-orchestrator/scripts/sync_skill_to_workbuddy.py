# -*- coding: utf-8 -*-
"""同步技能到 workbuddy 运行副本。
workbuddy 从 ~/.workbuddy/skills/ 载入技能（不是 ~/.agents/skills/ 也不是 ~/.claude/skills/）。
每次更新源技能后运行本脚本，使运行副本与规范源一致。

⚠️ 只做"覆盖更新"，不做镜像清空：目标目录可能含运行时数据
   （项目 competition_replay/、_user_meta.json、memory/approved/），必须保留。

用法: python scripts/sync_skill_to_workbuddy.py
"""
import os
import shutil
import sys
import argparse

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 不复制到 workbuddy 的内容（证据/缓存保留在源端）
SKIP_DIRS = {'inbox', '__pycache__', '.cache', '.git', 'public_overrides', 'archive'}


def should_skip(rel: str, dirname: str) -> bool:
    """跳过缓存、历史覆盖和技能安装目录不应同步的运行产物。"""
    if dirname in SKIP_DIRS or dirname.startswith('competition_replay_backup_'):
        return True
    if rel.replace('\\', '/').startswith('scripts/') and dirname in {'archive', 'public_overrides'}:
        return True
    return False


def main(argv=None):
    parser = argparse.ArgumentParser(description='将 contest-orchestrator 同步到 WorkBuddy 运行副本。')
    parser.add_argument('--dry-run', action='store_true', help='只统计待同步文件，不写入目标目录。')
    parser.add_argument('--dst', default=None, help='覆盖目标目录；默认读取 WORKBUDDY_SKILL_ROOT。')
    args = parser.parse_args(argv)
    destination = os.path.expanduser(args.dst or os.environ.get(
        'WORKBUDDY_SKILL_ROOT', '~/.workbuddy/skills/contest-orchestrator'))
    if not os.path.exists(SRC):
        print('源不存在:', SRC)
        return 1
    if not args.dry_run:
        os.makedirs(destination, exist_ok=True)
    n = 0
    for root, dirs, files in os.walk(SRC):
        rel = os.path.relpath(root, SRC)
        # 剪枝跳过目录（inbox 原始证据 / 缓存 / git 元数据）
        dirs[:] = [d for d in dirs if not should_skip(rel, d)]
        target_dir = destination if rel == '.' else os.path.join(destination, rel)
        if not args.dry_run:
            os.makedirs(target_dir, exist_ok=True)
        for f in files:
            if not args.dry_run:
                shutil.copy2(os.path.join(root, f), os.path.join(target_dir, f))
            n += 1
    action = '待同步' if args.dry_run else '已同步'
    print(f'{action} {n} 个文件 → {destination}')
    print('（跳过 inbox/缓存/历史覆盖与技能内运行产物；目标项目的运行数据不清空）')


if __name__ == '__main__':
    sys.exit(main())
