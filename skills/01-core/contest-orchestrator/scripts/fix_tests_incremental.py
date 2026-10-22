#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新 test_incremental_verification.py 中的 H4 引用为 H5"""
from pathlib import Path

file = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\tests\test_incremental_verification.py")
content = file.read_text(encoding="utf-8")

changes = 0

# 第 51 行: L3 级别最早失效节点从 H4 改成 H5
old1 = '"earliest_invalid_node": earliest or {"L0": "H8", "L1": "H7", "L2": "H5", "L3": "H4"}[level],'
new1 = '"earliest_invalid_node": earliest or {"L0": "H8", "L1": "H7", "L2": "H5", "L3": "H5"}[level],  # H4已并入H5'
if old1 in content:
    content = content.replace(old1, new1)
    changes += 1
    print("✓ L3 最早失效节点已更新")

# 第 94 行: earliest="H4" 改成 earliest="H5"
old2 = 'card = self.make_card(root, "L3", "global_interface", affected=[], earliest="H4")'
new2 = 'card = self.make_card(root, "L3", "global_interface", affected=[], earliest="H5")  # H4已并入H5'
if old2 in content:
    content = content.replace(old2, new2)
    changes += 1
    print("✓ 测试用例 earliest 已更新")

# 第 97 行: 期望结果从 ["H4", "H5", ...] 改成 ["H5", ...]
old3 = 'self.assertEqual(plan["recheck_nodes"], ["H4", "H5", "H6", "H7", "H8"])'
new3 = 'self.assertEqual(plan["recheck_nodes"], ["H5", "H6", "H7", "H8"])  # H4已并入H5'
if old3 in content:
    content = content.replace(old3, new3)
    changes += 1
    print("✓ 期望结果已更新")

if changes > 0:
    file.write_text(content, encoding="utf-8")
    print(f"\n总计: {changes} 处已更新")
else:
    print("✗ 未找到匹配")
