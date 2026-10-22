#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公开版生成与泄漏扫描（public_sync.py）

从私有版生成"削弱版"（白名单复制 + 自动脱敏），并在发布前扫描泄漏。

用法:
    python public_sync.py build <私有版路径> <公开版输出路径>
        # 白名单复制 → 脱敏替换 → 黑名单剔除 → 输出后自动 check
    python public_sync.py check <公开版路径>
        # 扫描: 本地路径 / 用户名 / workbuddy / Kimi / GPT评审 / 用户要求 / 私有文件名

白名单 = 可公开的框架与通用脚本（黑名单目录整体剔除，含私有经验/存档/评审记录）。
脱敏 = 替换表 + 正则（覆盖路径/内部称呼/评审措辞）。
注意: 清单外的"需人工改写"文件（delivery_gate.md 等 workbuddy 密集文档）由 check 报告,
      构建后必须人工处理到 check 输出空。
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

# ---------------------------------------------------------------- 配置
# 公开版白名单（相对私有版根目录）；目录=整个复制，文件=单个复制
WHITELIST = [
    "SKILL.md",
    "README.md",           # 需重写为通用叙事（人工）
    "LICENSE",
    "core",                # 目录内文件级别过滤见 PRUNE_FILES
    "planner",
    "executor",
    "critic",
    "team",
    "scripts",
]

# 黑名单目录/文件（无论是否在白名单内，一律剔除）
BLACKLIST_DIRS = [
    "contribution",        # 内部评审/AB 实验/征求意见——最大痕迹源
    "competition_replay",  # 私有比赛存档
    "simulations",         # 实战求解存档
    "dataset",             # 经验采集库
    "memory",              # 全部私有经验库（writing/failure/success/decision/strategy/calibration/blueprints）
    "docs",                # 内部架构文档（含私有演进史）——按需人工精选
    ".github",
]
BLACKLIST_FILES = [
    "failure_database.md", "success_database.md", "strategy_memory.md",
    "manifest.yaml",       # 机器路由含私有库清单，公开版不携带（SKILL.md 引用已自动清理）
    "token_policy.md",     # 私有加载策略，公开版不携带
]

# core/ 内需剔除的文件
PRUNE_CORE = []  # competition_gates.yaml 已提供公开版通用模板（core/competition_gates.yaml 由 build 自带白名单复制）

# critic/ 内需剔除的文件（依赖已剔除的私有校准库）
PRUNE_CRITIC = ["score_calibration.py"]

# scripts/ 内仅保留纯工具/门禁类（经验库维护类依赖私有 memory，剔除）
PRUNE_SCRIPTS = [
    "import_experience.py", "import_public_experience.py", "import_public_jsonl.py",
    "extract_wr.py", "retag_real_replay.py",
    "convert_wb_to_jsonl.py",
    "extract_and_import_batch.py", "extract_paper_texts.py", "install_skill.py",
    "sync_skill_to_workbuddy.py", "index_memory.py", "merge_inbox_to_memory.py",
    "retrieval_audit.py", "benchmark_retrieval.py", "benchmark_topic_selection.py",
    "coverage_matrix.py",
    "psr_measure.py", "regression_guard.py",
    "check_bzd_version.py",
    "public_sync.py",      # 私有发布工具，含全部敏感词表，永不进公开版
    "sync_skill.sh",       # 私有部署脚本
]
# 已归档的一次性脚本（scripts/archive/）由 PRUNE_ANY 整体剔除，无需逐名列

PRUNE_ANY = ["__pycache__", "public_overrides", "archive"]  # 编译缓存 + 人工改写覆盖目录 + 一次性迁移脚本归档（均不进公开版）

# 脱敏替换表（逐字替换，先长后短）
REPLACE = [
    (r"C:\\Users\\USER[^\"')\s]*", "<user-home>"),
    (r"D:\\[^\"')\s]*", "<workspace>"),
    (r"~/?\.workbuddy[^\"')\s]*", "<agent-home>"),
    (r"\bworkbuddy\b", "执行器"),
    (r"\bWorkBuddy\b", "执行器"),
    (r"\bKimi\b", "外部评审"),
    (r"\bGPT\b", "评审模型"),
    (r"用户金标准", "人工判定"),
    (r"用户要求", "需求"),
    (r"用户偏好", "人工偏好"),
    (r"用户建议", "建议"),
    (r"你拍板", "人工拍板"),
    (r"你睡觉", "夜间"),
    (r"你醒", "日间"),
    (r"Claude Code", "宿主Agent"),
    # 悬空引用清理：被剔除的私有路径 → 通用说法（保证公开版自洽，无断裂引用）
    (r"`memory/[a-z_]+\.md`", "经验库"),
    (r"memory/[a-z_]+\.md", "经验库"),
    (r"memory/calibration_db/", "校准库"),
    (r"memory/calibration_db", "校准库"),
    (r"`writing_database\.md`", "WR 库"),
    (r"writing_database\.md", "WR 库"),
    (r"`failure_database\.md`|`success_database\.md`|`strategy_memory\.md`", "经验库"),
    (r"competition_replay/[^\s`\"'）)]*", "比赛存档目录"),
    (r"contribution/[A-Za-z0-9_./]+\.md", "评审记录"),
    (r"contribution/", ""),
    (r"`extract_wr\.py`", "经验提取脚本"),
    (r"extract_wr\.py", "经验提取脚本"),
    (r"`manifest\.yaml`", ""),
    (r"`token_policy\.md`", ""),
    (r"（2026-\d{2}-\d{2}[^）]*）", ""),
    (r"2026-\d{2}-\d{2}", "近期"),
    (r"\d{4}年\d{1,2}月\d{1,2}日", "近期"),
]

# 需要人工确认的文件
NEEDS_MANUAL = ["core/delivery_gate.md"]


def is_pruned(rel: Path) -> bool:
    parts = rel.parts
    if any(p in PRUNE_ANY for p in parts):
        return True
    if any(parts[0] == d for d in BLACKLIST_DIRS):
        return True
    if rel.name in BLACKLIST_FILES or str(rel) in BLACKLIST_FILES:
        return True
    if len(parts) > 1 and parts[0] == "core" and rel.name in PRUNE_CORE:
        return True
    if len(parts) > 1 and parts[0] == "critic" and rel.name in PRUNE_CRITIC:
        return True
    if len(parts) > 1 and parts[0] == "scripts" and rel.name in PRUNE_SCRIPTS:
        return True
    return False


def sanitize(text: str) -> str:
    for pat, repl in REPLACE:
        text = re.sub(pat, repl, text)
    return text


def build(src: Path, dst: Path) -> None:
    # 保留目标目录的 .git（公开版仓库历史不被重建破坏）；其余内容清空重建
    if dst.exists():
        for item in dst.iterdir():
            if item.name == ".git":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    dst.mkdir(parents=True, exist_ok=True)
    copied = 0
    for item in WHITELIST:
        p = src / item
        if not p.exists():
            print(f"  [skip] 白名单项不存在: {item}")
            continue
        for f in (p.rglob("*") if p.is_dir() else [p]):
            if not f.is_file():
                continue
            rel = f.relative_to(src)
            if is_pruned(Path(rel)):
                continue
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if f.suffix.lower() in (".md", ".yaml", ".yml", ".txt", ".py"):
                target.write_text(sanitize(f.read_text(encoding="utf-8", errors="replace")),
                                  encoding="utf-8")
            else:
                shutil.copy2(f, target)
            copied += 1
    # 人工改写覆盖（public_overrides/ 内的最终叙事版，覆盖 build 的脱敏版）
    overrides = src / "scripts" / "public_overrides"
    if overrides.exists():
        for f in overrides.rglob("*"):
            if not f.is_file():
                continue
            rel = f.relative_to(overrides)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, target)
            print(f"  [override] {rel}")
    print(f"[build] 复制 {copied} 个文件 → {dst}")
    check(dst)


def check(root: Path) -> int:
    patterns = [
        (r"USER", "用户名"),
        (r"[A-Za-z]:\\Users\\", "本地路径"),
        (r"\.workbuddy", "私有环境"),
        (r"\bworkbuddy\b", "内部称呼"),
        (r"\bKimi\b", "评审模型名"),
        (r"\bGPT\b", "评审模型名"),
        (r"用户金标准|用户要求|用户偏好", "私有需求措辞"),
        (r"competition_replay|simulations|contribution/", "私有目录引用"),
        (r"writing_database|failure_database|success_database|strategy_memory|decision_memory", "私有库引用"),
        (r"math_blueprints|calibration_db|public_replay", "私有资产引用"),
    ]
    hits = 0
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in (".md", ".yaml", ".yml", ".txt", ".py"):
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for pat, label in patterns:
            for m in re.finditer(pat, text, flags=re.IGNORECASE):
                s = max(0, m.start() - 25)
                ctx = text[s:m.end() + 25].replace("\n", " ")
                print(f"  [LEAK:{label}] {f.relative_to(root)}: …{ctx}…")
                hits += 1
    for rel in NEEDS_MANUAL:
        if (root / rel).exists():
            print(f"  [MANUAL] {rel} 需人工改写（workbuddy 密集/叙事重写）——"
                  f"若已由 public_overrides 覆盖可忽略此提示")
    print(f"[check] 泄漏命中 {hits} 处" + (" → 全部清理后才能发布" if hits else " → 可发布"))
    return 1 if hits else 0


def main():
    ap = argparse.ArgumentParser(description="公开版生成与泄漏扫描")
    sub = ap.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("build", help="生成公开版并扫描")
    b.add_argument("src")
    b.add_argument("dst")
    c = sub.add_parser("check", help="扫描泄漏")
    c.add_argument("path")
    args = ap.parse_args()
    if args.mode == "build":
        build(Path(args.src), Path(args.dst))
    else:
        return check(Path(args.path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
