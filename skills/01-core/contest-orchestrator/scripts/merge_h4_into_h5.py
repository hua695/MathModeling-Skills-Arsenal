#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 contest-orchestrator 的 H4 节点取消，其职责并入 H5。
只修改 check_harness_control.py 的核心逻辑，保留 H4 在节点列表中（标记为已并入）。
"""
import re
from pathlib import Path

FILE = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\scripts\check_harness_control.py")
content = FILE.read_text(encoding="utf-8")

# 1. ROLE_BY_NODE: H4 角色标记为已并入
content = content.replace(
    '"H4": "主 agent", "H5": "解题 agent"',
    '"H4": "已并入H5（蓝图设计）", "H5": "解题 agent"'
)

# 2. STAGE_PREDECESSORS: H5 的前驱从 (H3, H4) 改成 (H3,)
content = content.replace(
    '"H5": ("H3", "H4"),',
    '"H5": ("H3",),  # H4 已并入 H5，前驱只需 H3'
)

# 3. validate_literature_gate 函数中的 H4 检查
# 把 "before H4 route selection and H5 solving" 改成 "before H5 route selection and solving"
content = content.replace(
    '"""Enforce user-returned literature before H4 route selection and H5 solving."""',
    '"""Enforce user-returned literature before H5 route selection and solving (H4已并入H5)."""'
)

# 把 if NODES.index(through) >= NODES.index("H4") 改成 H5
content = content.replace(
    'if NODES.index(through) >= NODES.index("H4"):\n        _require_node_file(root, h3, "literature_sources", "H3", missing)',
    'if NODES.index(through) >= NODES.index("H5"):\n        _require_node_file(root, h3, "literature_sources", "H3", missing)'
)

# 把错误消息中的 H4 改成 H5
content = content.replace(
    'missing.append(f"H4: 文献输入门尚未获批，H3 status 必须为 approved/frozen（当前: {h3_status}）")',
    'missing.append(f"H5: 文献输入门尚未获批，H3 status 必须为 approved/frozen（当前: {h3_status}）")'
)

# 把检查 H4 文件的逻辑改成检查 H5 文件
old_h4_check = '''    if NODES.index(through) >= NODES.index("H5"):
        h4 = nodes.get("H4", {})
        for field in ("method_transfer_map", "model_blueprint", "chart_requirements"):
            _require_node_file(root, h4, field, "H4", missing)'''
new_h5_check = '''    if NODES.index(through) >= NODES.index("H5"):
        h5 = nodes.get("H5", {})
        for field in ("method_transfer_map", "model_blueprint", "chart_requirements"):
            _require_node_file(root, h5, field, "H5", missing)'''
content = content.replace(old_h4_check, new_h5_check)

# 4. SKILL_BINDING_BY_NODE: 删除 H4，把 math-model-selector 加到 H5
old_binding = '''SKILL_BINDING_BY_NODE = {
    "H4": {"must_call": ["math-model-selector"]},
    "H5": {"at_least_one": ["heuristic-algorithms", "data-science-stack", "pyomo"]},'''
new_binding = '''SKILL_BINDING_BY_NODE = {
    "H5": {"must_call": ["math-model-selector"], "at_least_one": ["heuristic-algorithms", "data-science-stack", "pyomo"]},  # H4已并入H5，math-model-selector 为阶段一必调'''
content = content.replace(old_binding, new_binding)

# 5. 节点初始化: 把 H4 的字段初始化移到 H5
# 先找到 nodes["H4"].update(...) 的部分，改成 H5
old_init = '''    nodes["H4"].update({
        "method_transfer_map": None,
        "model_blueprint": None,
        "chart_requirements": None,
    })'''
new_init = '''    nodes["H5"].update({
        "method_transfer_map": None,
        "model_blueprint": None,
        "chart_requirements": None,
    })  # H4已并入H5，这些字段由H5阶段一产出'''
content = content.replace(old_init, new_init)

# 6. 注释中的 H4 改成 H5
content = content.replace(
    '"""叙事蓝图校验：H4 产出 method/innovation/problem_solved，H5 回填 key_result，H6 核验。"""',
    '"""叙事蓝图校验：H5阶段一产出 method/innovation/problem_solved，H5阶段二-四回填 key_result，H6 核验。（H4已并入H5）"""'
)

FILE.write_text(content, encoding="utf-8")
print("check_harness_control.py 修改完成")

# 验证：统计剩余 H4 引用
remaining = len(re.findall(r'H4', content))
print(f"剩余 H4 引用: {remaining} 处（大部分应为注释/说明性文字）")
