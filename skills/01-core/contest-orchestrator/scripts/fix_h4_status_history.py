#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复状态历史校验中的 H4 跳过逻辑"""
from pathlib import Path

file = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\scripts\check_harness_control.py")
content = file.read_text(encoding="utf-8")

old = '        if node_id in ("H0",) or node_id not in node_current:'
new = '        if node_id in ("H0", "H4") or node_id not in node_current:  # H4已并入H5，跳过'

if old in content:
    content = content.replace(old, new)
    file.write_text(content, encoding="utf-8")
    print("✓ 状态历史校验已添加 H4 跳过逻辑")
else:
    print("✗ 未找到匹配的代码段")
