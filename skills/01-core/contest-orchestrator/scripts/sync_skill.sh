#!/usr/bin/env bash
# sync_skill.sh — contest-orchestrator 技能「会话自动拉取」同步器
#
# 背景: 该技能是 hua695/MathModel-Agent 的本地 git clone(经 ghproxy)。
#       本环境下 origin/main 远程跟踪引用无法持久化(沙箱/OneDrive 会丢弃
#       .git/refs/remotes/* 松散引用), 因此比对不能用 origin/main, 改用
#       `git ls-remote` 直接问远端拿 tip, 完全不碰本地 .git/refs, 最稳。
#
# 用法:
#   ./sync_skill.sh            # 比对, 落后则 ff-pull 再继续
#   ./sync_skill.sh --check    # 仅比对并打印状态, 不拉取 (不阻塞)
#
# 退出码: 0=成功/已最新; 2=远端不可达(已跳过, 不视为失败); 其他=拉取出错

set -u

SKILL_DIR="${SKILL_DIR:-$HOME/.workbuddy/skills/contest-orchestrator}"
CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

# 校验目录是 git 仓库
if ! git -C "$SKILL_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: $SKILL_DIR 不是 git 仓库" >&2
  exit 3
fi

LOCAL=$(git -C "$SKILL_DIR" rev-parse HEAD 2>/dev/null)
echo "LOCAL  : $LOCAL"

# 直接问远端拿 main 分支 tip —— 不依赖本地 origin/main 引用
REMOTE=$(git -C "$SKILL_DIR" ls-remote origin refs/heads/main 2>/dev/null | awk '{print $1}')

if [ -z "$REMOTE" ]; then
  echo "WARN  : 远端不可达 (网络 / ghproxy 超时) —— 保留本地, 不阻塞本次会话"
  exit 2
fi
echo "REMOTE : $REMOTE"

if [ "$LOCAL" = "$REMOTE" ]; then
  echo "STATUS : UP-TO-DATE @ $LOCAL —— 无需拉取"
  exit 0
fi

echo "STATUS : BEHIND (local=$LOCAL -> remote=$REMOTE)"

if [ "$CHECK_ONLY" -eq 1 ]; then
  echo "INFO  : --check 模式, 跳过拉取"
  exit 0
fi

echo "ACTION : fetch + ff-only merge ..."
git -C "$SKILL_DIR" fetch origin 2>&1
if git -C "$SKILL_DIR" merge --ff-only FETCH_HEAD 2>&1; then
  NEW=$(git -C "$SKILL_DIR" rev-parse HEAD)
  echo "DONE  : 已更新到 $NEW"
  exit 0
else
  echo "ERROR : ff-merge 失败, 可能本地有改动导致非快进; 请手动处理" >&2
  exit 1
fi
