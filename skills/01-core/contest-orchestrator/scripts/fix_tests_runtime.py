#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新 test_runtime_hardening.py 中的 H4 引用"""
from pathlib import Path

file = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\tests\test_runtime_hardening.py")
content = file.read_text(encoding="utf-8")

changes = 0

# 测试用例1: test_dispatch_cannot_precede_predecessor_approval
# H5 的前驱从 H4 改成 H3
old1a = '"node_id": "H4", "from_status": "review_pending", "to_status": "approved",'
new1a = '"node_id": "H3", "from_status": "review_pending", "to_status": "approved",  # H4已并入H5，H5前驱是H3'
if old1a in content:
    content = content.replace(old1a, new1a)
    changes += 1
    print("✓ 测试用例1: 状态历史节点已更新 H4→H3")

old1b = 'self.assertTrue(any("H5" in item and "H4" in item for item in failures))'
new1b = 'self.assertTrue(any("H5" in item and "H3" in item for item in failures))  # H4已并入H5，H5前驱是H3'
if old1b in content:
    content = content.replace(old1b, new1b)
    changes += 1
    print("✓ 测试用例1: 错误消息检查已更新 H4→H3")

# 测试用例2: test_literature_sources_are_required_before_model_route
# 文献门从 H4 改成 H5
old2a = '"H4": {"status": "approved"},'
new2a = '"H5": {"status": "approved"},  # H4已并入H5，文献门在H5检查'
if old2a in content:
    content = content.replace(old2a, new2a)
    changes += 1
    print("✓ 测试用例2: 节点状态设置已更新 H4→H5")

old2b = 'checker.validate_literature_gate(root, nodes, "H4", missing, failures)'
new2b = 'checker.validate_literature_gate(root, nodes, "H5", missing, failures)  # H4已并入H5'
if old2b in content:
    content = content.replace(old2b, new2b)
    changes += 1
    print("✓ 测试用例2: 文献门调用已更新 H4→H5")

if changes > 0:
    file.write_text(content, encoding="utf-8")
    print(f"\n总计: {changes} 处已更新")
else:
    print("✗ 未找到匹配")
