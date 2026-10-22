#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时恢复测试文件中的 H4 状态设置，验证是否与失败有关"""
from pathlib import Path

file = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\tests\test_harness_control.py")
content = file.read_text(encoding="utf-8")

# 在第 38 行后恢复 H4 状态设置
old = '            payload["nodes"]["H3"]["status"] = "approved"\n            payload["harness_run_id"]'
new = '            payload["nodes"]["H3"]["status"] = "approved"\n            payload["nodes"]["H4"]["status"] = "approved"  # H4已并入H5，但状态历史校验需要\n            payload["harness_run_id"]'

if old in content:
    content = content.replace(old, new)
    file.write_text(content, encoding="utf-8")
    print("✓ 已恢复 H4 状态设置")
else:
    print("✗ 未找到匹配")
