#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键安装/更新 contest-orchestrator 技能（替代手动复制）

设计原则（v3.5.3 公开化之后）：
  技能 = 整个仓库（框架核心 + 4 个经验库 DB + 数据集 + 脚本 + 文档），
  全部从仓库根同步。不再维护"框架项清单"或"经验库清单"——整仓复制，
  新增/改名文件自动纳入，不会再发生"漏掉第 4 个 DB (decision_memory.md)"这类事故。

同步策略（安全）：
  source → target 单向复制（shutil.copy2），覆盖同名文件；
  但【绝不删除】target 中独有的文件（如 WorkBuddy 的 _user_meta.json、旧备份等），
  避免误删宿主环境的技能元数据导致技能失效。

排除项：
  .git / __pycache__（仓库元数据、缓存）
  提交给workbuddy.md（内部交接文档，勿外发）
  .gitignore（对纯技能副本无意义）

用法:
  # 1) 装到默认目标（自动探测 ~/.workbuddy/skills 或 ~/.claude/skills 中已存在的）
  python scripts/install_skill.py

  # 2) 显式指定多个目标（你的日常：同时更新 claude 与 workbuddy 两份）
  python scripts/install_skill.py --to ~/.workbuddy/skills/contest-orchestrator ~/.claude/skills/contest-orchestrator

  # 3) 别人用你的（先 clone，再一条命令装好）
  git clone https://github.com/hua695/MathModel-Agent.git
  cd MathModel-Agent && python scripts/install_skill.py

  # 4) 以后更新
  cd MathModel-Agent && git pull && python scripts/install_skill.py

  # 5) 只预览将要复制的内容（不实际写入）
  python scripts/install_skill.py --dry
"""
import os
import shutil
import sys
import argparse

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 不复制的相对路径（相对仓库根）；.git / __pycache__ 在遍历时单独剪枝
EXCLUDE_REL = {
    '.gitignore',
    '提交给workbuddy.md',
}
# 不遍历的目录（匹配目录名）
EXCLUDE_DIRS = {'.git', '__pycache__'}


def should_skip(rel_path):
    """rel_path 为相对仓库根的路径（用 os.sep 分隔）。"""
    parts = rel_path.split(os.sep)
    if parts[-1] in EXCLUDE_REL:
        return True
    if rel_path.replace(os.sep, '/') in EXCLUDE_REL:
        return True
    return False


def sync_dir(src_root, dst_root):
    """整仓同步：复制 src_root 下所有文件到 dst_root，跳过排除项。
    返回复制的文件数；绝不删除 dst 独有文件。"""
    n = 0
    for root, dirs, files in os.walk(src_root):
        # 原地剪枝，避免进入 .git / __pycache__
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), src_root)
            if should_skip(rel):
                continue
            s = os.path.join(root, f)
            d = os.path.join(dst_root, rel)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
            n += 1
    return n


def detect_default_targets():
    """探测本机已存在的技能目录，优先 workbuddy，其次 claude。
    若都未建过，默认 workbuddy 路径（当前主用环境）。"""
    candidates = [
        os.path.expanduser('~/.workbuddy/skills/contest-orchestrator'),
        os.path.expanduser('~/.claude/skills/contest-orchestrator'),
    ]
    existing = [c for c in candidates if os.path.isdir(os.path.dirname(c))]
    if existing:
        return existing
    return [candidates[0]]


def read_version(target):
    vf = os.path.join(target, 'manifest.yaml')
    if not os.path.exists(vf):
        return ''
    for line in open(vf, encoding='utf-8'):
        if line.strip().startswith('version:'):
            return line.strip()
    return ''


def main():
    ap = argparse.ArgumentParser(description='安装/更新 contest-orchestrator 技能（整仓同步）')
    ap.add_argument('--to', nargs='+', default=None,
                    help='目标 skill 目录（可多个）。默认自动探测已存在的技能目录。')
    ap.add_argument('--dry', action='store_true', help='只打印将要同步的统计，不实际写入')
    args = ap.parse_args()

    targets = [os.path.expanduser(t) for t in (args.to or detect_default_targets())]

    for t in targets:
        if args.dry:
            # 干跑：统计源文件数（排除项外）
            count = 0
            for root, dirs, files in os.walk(REPO_ROOT):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for f in files:
                    rel = os.path.relpath(os.path.join(root, f), REPO_ROOT)
                    if should_skip(rel):
                        continue
                    count += 1
            print(f'[DRY] 将同步 {REPO_ROOT}\n      → {t}\n      （约 {count} 文件，覆盖不删除；4 个经验库 DB 全部含入）')
            continue

        os.makedirs(t, exist_ok=True)
        n = sync_dir(REPO_ROOT, t)
        ver = read_version(t)
        print(f'安装完成 → {t}（{n} 文件）{ver}')

    if not args.dry:
        print('说明：本次为整仓同步（框架+4个经验库DB+数据集+脚本+文档），只覆盖不删除；')
        print('      目标目录里 WorkBuddy 的 _user_meta.json / 旧备份等独有文件会保留。')
        print('以后更新：改仓库 → git pull → 重跑本脚本。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
