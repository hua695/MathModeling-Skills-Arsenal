#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量替换 planner 文件中的 H4 引用为 H5"""
from pathlib import Path

ROOT = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\planner")

replacements = [
    (ROOT / "problem_essence_taxonomy.md", [
        ("H1 拆题和 H4 路由前", "H1 拆题和 H5 路由前（原H4已并入H5阶段一）"),
        ("H4：按需调 `math-model-selector`", "H5 阶段一：按需调 `math-model-selector`（原H4职责）"),
    ]),
    (ROOT / "literature_survey.py", [
        ('拟在 H4 登记的模型/数据/参数/验证/结论用途', '拟在 H5 登记的模型/数据/参数/验证/结论用途（原H4职责已并入H5）'),
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
            print(f"  {filepath.name}: '{old[:40]}...' → {count} 处")
    if file_changes > 0:
        filepath.write_text(content, encoding="utf-8")
        total_changes += file_changes
        print(f"  ✓ {filepath.name}: {file_changes} 处已修改")

print(f"\n总计: {total_changes} 处修改")
