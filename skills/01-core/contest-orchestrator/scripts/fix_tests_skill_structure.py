#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新 test_skill_structure_contract.py 中的 H4 引用为 H5（H4已并入H5）"""
from pathlib import Path

file = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\tests\test_skill_structure_contract.py")
content = file.read_text(encoding="utf-8")

# 测试用例1: test_modeling_waits_for_user_literature_package
# 把 h4 改成 h5，因为 H4 已取消，文献门在 H3-H5 之间
old1 = """        h3 = harness.index("| `H3`")
        h4 = harness.index("| `H4`")
        literature_gate = harness.index("literature_sources.yaml", h3)
        self.assertLess(h3, literature_gate)
        self.assertLess(literature_gate, h4)
        self.assertIn("PAUSE", harness[h3:h4])
        self.assertRegex(harness[h3:h4], r"(?i)(数量|语言|覆盖).{0,160}(校验|通过)")
        self.assertRegex(harness[h3:h4], r"(?i)(返回|提交).{0,160}literature_sources\\.yaml")"""

new1 = """        h3 = harness.index("| `H3`")
        h5 = harness.index("| `H5`")  # H4已并入H5，文献门在 H3-H5 之间
        literature_gate = harness.index("literature_sources.yaml", h3)
        self.assertLess(h3, literature_gate)
        self.assertLess(literature_gate, h5)
        self.assertIn("PAUSE", harness[h3:h5])
        self.assertRegex(harness[h3:h5], r"(?i)(数量|语言|覆盖).{0,160}(校验|通过)")
        self.assertRegex(harness[h3:h5], r"(?i)(返回|提交).{0,160}literature_sources\\.yaml")"""

# 测试用例2: test_harness_uses_literature_before_route_and_figure_requirements
# H4 已取消，路线阶段并入 H5
old2 = """        h3 = harness.index("| `H3`")
        h4 = harness.index("| `H4`")
        h5 = harness.index("| `H5`")
        literature_stage = harness[h3:h4]
        route_stage = harness[h4:h5]"""

new2 = """        h3 = harness.index("| `H3`")
        h5 = harness.index("| `H5`")  # H4已并入H5
        literature_stage = harness[h3:h5]
        route_stage = harness[h5:h5+3000]  # 路线/蓝图阶段现在在 H5 阶段一"""

changes = 0
if old1 in content:
    content = content.replace(old1, new1)
    changes += 1
    print("✓ 测试用例1已更新")
else:
    print("✗ 测试用例1未找到匹配")

if old2 in content:
    content = content.replace(old2, new2)
    changes += 1
    print("✓ 测试用例2已更新")
else:
    print("✗ 测试用例2未找到匹配")

if changes > 0:
    file.write_text(content, encoding="utf-8")
    print(f"\n总计: {changes} 个测试用例已更新")
