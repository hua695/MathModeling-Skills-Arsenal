#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 ROLE_BY_NODE['H4'] 改回主 agent，避免固定角色检查报错"""
from pathlib import Path

file = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\scripts\check_harness_control.py")
content = file.read_text(encoding="utf-8")

old = '"H4": "已并入H5（蓝图设计）", "H5": "解题 agent"'
new = '"H4": "主 agent", "H5": "解题 agent"  # H4已并入H5，角色保留为主agent避免固定角色检查报错'

if old in content:
    content = content.replace(old, new)
    file.write_text(content, encoding="utf-8")
    print("✓ ROLE_BY_NODE['H4'] 已改回主 agent")
else:
    print("✗ 未找到匹配")
