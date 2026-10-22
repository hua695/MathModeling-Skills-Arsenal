#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新 test_harness_control.py 中的 H4 引用为 H5（H4已并入H5）"""
from pathlib import Path

file = Path(r"C:\Users\USER\.agents\skills\contest-orchestrator\tests\test_harness_control.py")
content = file.read_text(encoding="utf-8")

changes = 0

# 第 39 行: 设置 H4 状态为 approved - H4已取消，删除这行（主循环会跳过H4）
old1 = '            payload["nodes"]["H4"]["status"] = "approved"\n'
if old1 in content:
    content = content.replace(old1, '')
    changes += 1
    print("✓ 第39行: 删除 H4 状态设置（H4已取消，主循环跳过）")

# 第 627 行: test_not_started_skips_binding - H4→H5
old2 = 'missing, failures = self._check("H4", {"status": "not_started"})'
new2 = 'missing, failures = self._check("H5", {"status": "not_started"})  # H4已并入H5'
if old2 in content:
    content = content.replace(old2, new2)
    changes += 1
    print("✓ test_not_started_skips_binding: H4→H5")

# 第 632 行: test_missing_skill_invocations_field_blocks - H4→H5
old3 = 'missing, _ = self._check("H4", {"status": "approved"})'
new3 = 'missing, _ = self._check("H5", {"status": "approved"})  # H4已并入H5'
if old3 in content:
    content = content.replace(old3, new3)
    changes += 1
    print("✓ test_missing_skill_invocations_field_blocks: H4→H5")

# 第 639-642 行: test_h4_must_call_selector - 改名并改成 H5
old4 = '''    def test_h4_must_call_selector(self):
        missing, _ = self._check(
            "H4", {"status": "approved", "skill_invocations": [{"skill": "pyomo"}]})
        self.assertTrue(any("必调子 skill" in item and "math-model-selector" in item for item in missing))'''
new4 = '''    def test_h5_must_call_selector(self):
        """H5 阶段一必须调用 math-model-selector（H4已并入H5）"""
        missing, _ = self._check(
            "H5", {"status": "approved", "skill_invocations": [{"skill": "pyomo"}]})
        self.assertTrue(any("必调子 skill" in item and "math-model-selector" in item for item in missing))'''
if old4 in content:
    content = content.replace(old4, new4)
    changes += 1
    print("✓ test_h4_must_call_selector → test_h5_must_call_selector")

# 第 751 行: 某个测试用例中的 H4→H5
old5 = 'checker._validate_skill_invocations(root, "H4", node, missing, failures)'
new5 = 'checker._validate_skill_invocations(root, "H5", node, missing, failures)  # H4已并入H5'
count5 = content.count(old5)
if count5 > 0:
    content = content.replace(old5, new5)
    changes += count5
    print(f"✓ _validate_skill_invocations: H4→H5 ({count5}处)")

# 第 763 行: test_missing_evidence_ref_blocks - H4→H5
old6 = '''            "H4", {"status": "approved", "skill_invocations": [
                {"skill": "math-model-selector"}]})'''
new6 = '''            "H5", {"status": "approved", "skill_invocations": [
                {"skill": "math-model-selector"}]})  # H4已并入H5'''
if old6 in content:
    content = content.replace(old6, new6)
    changes += 1
    print("✓ test_missing_evidence_ref_blocks: H4→H5")

if changes > 0:
    file.write_text(content, encoding="utf-8")
    print(f"\n总计: {changes} 处已更新")
else:
    print("✗ 未找到匹配")
