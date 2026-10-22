#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量替换 references 文件中的 H4 引用为 H5（原H4已并入）"""
from pathlib import Path

ROOT = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\references")

# 需要修改的文件和替换规则
replacements = [
    # figure_policy.md
    (ROOT / "figure_policy.md", [
        ("identified at H4", "identified at H5 (stage 1, formerly H4)"),
    ]),
    # citation_policy.md
    (ROOT / "citation_policy.md", [
        ("和 H4 的实际落位记录", "和 H5 的实际落位记录（原H4职责已并入H5阶段一）"),
    ]),
    # content_budget_policy.md
    (ROOT / "content_budget_policy.md", [
        ("只记录 H4 的主张级初步需求", "只记录 H5 阶段一的主张级初步需求（原H4职责）"),
        ("H4 的 `required`", "H5 的 `required`"),
    ]),
    # warmup/h7_figure_warmup.md
    (ROOT / "warmup" / "h7_figure_warmup.md", [
        ("H4 主张清单", "H5 主张清单（原H4职责已并入H5阶段一）"),
        ("H4 的主张清单", "H5 的主张清单"),
        ("图表需求清单（H4 产出", "图表需求清单（H5 阶段一产出"),
    ]),
]

total_changes = 0
for filepath, rules in replacements:
    if not filepath.exists():
        print(f"跳过（不存在）: {filepath}")
        continue
    content = filepath.read_text(encoding="utf-8")
    file_changes = 0
    for old, new in rules:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            file_changes += count
            print(f"  {filepath.name}: '{old[:30]}...' → {count} 处")
    if file_changes > 0:
        filepath.write_text(content, encoding="utf-8")
        total_changes += file_changes
        print(f"  ✓ {filepath.name}: {file_changes} 处已修改")
    else:
        print(f"  - {filepath.name}: 无匹配")

print(f"\n总计: {total_changes} 处修改")
