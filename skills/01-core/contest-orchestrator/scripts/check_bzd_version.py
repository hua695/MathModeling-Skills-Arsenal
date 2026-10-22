#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/check_bzd_version.py — BZD 版本漂移监控（Phase 4 任务 7 · 原创代码）

读 VERSION_PIN.md 的锁定 commit → git ls-remote 对比远端 main HEAD：
  一致 = OK；不一致 = ⚠ 提示人工评估（不自动升级）。

VERSION_PIN.md 位置：~/.agents/skills/bzd-review-paper/ 或 ~/.workbuddy/skills/bzd-review-paper/
锁定行格式：Git: https://github.com/<org>/<repo> @ <40位sha>

用法：
    python scripts/check_bzd_version.py
退出码：0 = OK/跳过；2 = 版本漂移（供 CI/自动化调用）

红线：本脚本只报告差异，绝不自动 git pull / 修改 VERSION_PIN.md。
"""
import os
import re
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
CANDIDATES = [
    HOME / '.agents' / 'skills' / 'bzd-review-paper' / 'VERSION_PIN.md',
    HOME / '.workbuddy' / 'skills' / 'bzd-review-paper' / 'VERSION_PIN.md',
]
PIN_RE = re.compile(r'https?://github\.com/(?P<repo>[^\s@]+) @ (?P<sha>[0-9a-fA-F]{40})')


def find_pin():
    for p in CANDIDATES:
        if p.exists():
            return p
    return None


def parse_pin(path):
    for enc in ('utf-8-sig', 'utf-8', 'gbk'):
        try:
            txt = path.read_text(encoding=enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        txt = path.read_text(encoding='utf-8', errors='replace')
    m = PIN_RE.search(txt)
    if not m:
        return None, None
    repo = m.group('repo').rstrip('/')
    if repo.endswith('.git'):
        repo = repo[:-4]
    return f'https://github.com/{repo}.git', m.group('sha')


def remote_head(repo_url):
    """git ls-remote refs/heads/main（自动走用户全局 insteadOf 代理）。"""
    try:
        out = subprocess.run(
            ['git', 'ls-remote', repo_url, 'refs/heads/main'],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode != 0:
            return None, f'git ls-remote 失败: {out.stderr.strip()[:200]}'
        m = re.search(r'^([0-9a-fA-F]{40})\s+refs/heads/main', out.stdout, re.M)
        if not m:
            return None, '远端无 refs/heads/main 分支'
        return m.group(1).lower(), None
    except subprocess.TimeoutExpired:
        return None, 'ls-remote 超时(60s)'
    except FileNotFoundError:
        return None, '本机无 git 命令'


def main():
    pin = find_pin()
    if not pin:
        print('SKIP: 未找到 VERSION_PIN.md（bzd-review-paper 未安装或路径变更），跳过版本检查')
        return 0

    repo, pinned = parse_pin(pin)
    if not repo:
        print('ERROR: VERSION_PIN.md 格式无法解析（期望: Git: https://github.com/... @ <40hex>）')
        return 2

    head, err = remote_head(repo)
    if err:
        print(f'⚠ 无法对比远端（{err}）—— 保持本地锁定版本，不自动升级；请人工核实网络/代理。')
        print(f'  锁定: {pinned}')
        return 0

    print(f'VERSION_PIN.md : {pin}')
    print(f'锁定 commit    : {pinned}')
    print(f'远端 main HEAD : {head}')

    if pinned.lower() == head:
        print('\n✅ OK：本地锁定版本与远端一致，无版本漂移。')
        return 0
    else:
        print('\n⚠ VERSION 漂移：远端已有新提交，本地仍为锁定版本。')
        print('   ⚠ 提示人工评估（不自动升级）：')
        print('     1) 查看远端更新内容（git log 或 GitHub 对比页面）')
        print('     2) 评估是否影响评审口径/评分逻辑（rubric 变化需回归测试）')
        print('     3) 若需升级：人工 clone/更新 + 更新 VERSION_PIN.md + 重跑回归验证')
        return 2


if __name__ == '__main__':
    sys.exit(main())
