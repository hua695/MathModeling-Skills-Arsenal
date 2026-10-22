#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新测试文件中的 H4 引用"""
from pathlib import Path

# test_harness_hardening.py: 删除遍历中的 H4
file1 = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\tests\test_harness_hardening.py")
content1 = file1.read_text(encoding="utf-8")
old1 = 'for node_id in ("H2", "H3", "H4", "H5", "H6", "H7", "H8"):'
new1 = 'for node_id in ("H2", "H3", "H5", "H6", "H7", "H8"):  # H4已并入H5，跳过'
if old1 in content1:
    content1 = content1.replace(old1, new1)
    file1.write_text(content1, encoding="utf-8")
    print("✓ test_harness_hardening.py 已更新")
else:
    print("✗ test_harness_hardening.py 未找到匹配")

# test_harness_state_machine.py: 删除遍历中的 H4，并更新 H4 节点设置
file2 = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\tests\test_harness_state_machine.py")
content2 = file2.read_text(encoding="utf-8")

# 第 104 行和 125 行: control["nodes"]["H4"] = _make_node("H4", "approved")
# 这些是设置 H4 状态为 approved，用于测试状态转移。现在 H4 被跳过了，可以改成 H5
old2a = 'control["nodes"]["H4"] = _make_node("H4", "approved")'
new2a = 'control["nodes"]["H5"] = _make_node("H5", "approved")  # H4已并入H5'
count2a = content2.count(old2a)
if count2a > 0:
    content2 = content2.replace(old2a, new2a)
    print(f"✓ test_harness_state_machine.py H4节点设置已更新 ({count2a}处)")

# 第 151 行: for nid in ["H1", "H2", "H3", "H4", "H5", "H6", "H7"]:
old2b = 'for nid in ["H1", "H2", "H3", "H4", "H5", "H6", "H7"]:'
new2b = 'for nid in ["H1", "H2", "H3", "H5", "H6", "H7"]:  # H4已并入H5，跳过'
if old2b in content2:
    content2 = content2.replace(old2b, new2b)
    print("✓ test_harness_state_machine.py 遍历列表已更新")

file2.write_text(content2, encoding="utf-8")

print("\n测试文件更新完成")
