#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在主检查循环中跳过 H4 节点"""
from pathlib import Path

file = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\scripts\check_harness_control.py")
content = file.read_text(encoding="utf-8")

old = """    for node_id in checked_nodes:
        node = nodes.get(node_id)
        if not isinstance(node, dict):
            failures.append(f"{node_id}: 节点记录缺失")
            continue
        node_status = node.get("status")"""

new = """    for node_id in checked_nodes:
        node = nodes.get(node_id)
        if not isinstance(node, dict):
            failures.append(f"{node_id}: 节点记录缺失")
            continue
        # H4 节点已取消（v4.19 起并入 H5 阶段一），跳过其独立检查
        if node_id == "H4":
            continue
        node_status = node.get("status")"""

if old in content:
    content = content.replace(old, new)
    file.write_text(content, encoding="utf-8")
    print("✓ 主检查循环已添加 H4 跳过逻辑")
else:
    print("✗ 未找到匹配的代码段")
    # 打印附近内容帮助调试
    idx = content.find("for node_id in checked_nodes:")
    if idx >= 0:
        print("找到位置，附近内容：")
        print(content[idx:idx+300])
