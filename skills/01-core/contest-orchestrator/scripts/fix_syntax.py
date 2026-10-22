#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 ROLE_BY_NODE 的语法错误"""
from pathlib import Path

file = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\scripts\check_harness_control.py")
content = file.read_text(encoding="utf-8")

old = '''    "H4": "主 agent", "H5": "解题 agent"  # H4已并入H5，角色保留为主agent避免固定角色检查报错, "H6": "验证 agent", "H7": "图表 agent",
    "H8": "论文 agent", "H9": "主 agent",'''

new = '''    "H4": "主 agent", "H5": "解题 agent", "H6": "验证 agent", "H7": "图表 agent",
    "H8": "论文 agent", "H9": "主 agent",'''

if old in content:
    content = content.replace(old, new)
    file.write_text(content, encoding="utf-8")
    print("✓ 语法错误已修复")
else:
    print("✗ 未找到匹配")
