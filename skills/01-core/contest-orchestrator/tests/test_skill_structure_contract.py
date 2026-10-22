from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class SkillStructureContractTests(unittest.TestCase):
    def test_manifest_is_valid_and_all_active_paths_resolve(self):
        manifest_path = ROOT / "manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        self.assertIsInstance(manifest, dict)
        self.assertEqual(manifest["entry"]["skill"], "SKILL.md")
        self.assertEqual(manifest["entry"]["version_file"], "VERSION")

        paths = [manifest["entry"]["skill"], manifest["entry"]["version_file"]]
        paths.extend(manifest.get("references", []))
        for module in manifest.get("modules", {}).values():
            paths.extend(module.get("always", []))
            paths.extend(module.get("files", []))
        lookup = manifest.get("memory_lookup", {})
        paths.extend(lookup.get("always", []))
        paths.extend(lookup.get("on_hit", []))

        missing = [path for path in paths if not (ROOT / path).exists()]
        self.assertEqual(missing, [], f"活动 manifest 路径不存在: {missing}")

    def test_active_instructions_do_not_expose_maintenance_history(self):
        targets = {
            "scripts/paper_check.py": ("第5轮", "第6轮", "第10轮", "第50轮", "此前清单"),
            "scripts/e2e_docx_test.py": ("第44轮", "round 15", "round 40", "round 43"),
            "scripts/replay_profiles.py": ("调试记录确定",),
            "memory/ranking.py": ("已废弃", "评审共识"),
            "memory/retrieval.py": ("评审共识", "修复 v3.7", "评审核心建议"),
            "references/modes/full-contest-harness.md": ("尚未完全确认", "原方案设计"),
        }
        for relative, markers in targets.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            for marker in markers:
                self.assertNotIn(marker, text, f"活动文件仍包含维护过程话语: {relative}: {marker}")

    def test_harness_requires_using_superpowers_and_multi_agent_dispatch(self):
        entry = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        harness = (ROOT / "references/modes/full-contest-harness.md").read_text(encoding="utf-8")
        legacy = (ROOT / "references/modes/full-contest-legacy.md").read_text(encoding="utf-8")
        stable = (ROOT / "references/modes/full-contest-4-18.md").read_text(encoding="utf-8")

        self.assertIn("full-contest-harness", entry)
        self.assertIn("superpowers:using-superpowers", entry)
        self.assertIn("superpowers:using-superpowers", harness)
        self.assertRegex(harness, r"(?i)(必须|MUST).{0,240}(superpowers:using-superpowers)")
        self.assertRegex(harness, r"(?i)(固定角色|多 agent).{0,240}(任务卡|调度|派发|dispatch|create)")
        self.assertRegex(harness, r"(?i)(不可用|未调用|无法建立|失败).{0,160}(BLOCKED_INPUT|PAUSE)")
        self.assertNotIn("superpowers:using-superpowers", legacy)
        self.assertNotIn("superpowers:using-superpowers", stable)

    def test_modeling_waits_for_user_literature_package(self):
        entry = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        harness = (ROOT / "references/modes/full-contest-harness.md").read_text(encoding="utf-8")

        h3 = harness.index("| `H3`")
        h5 = harness.index("| `H5`")  # H4已并入H5，文献门在 H3-H5 之间
        literature_gate = harness.index("literature_sources.yaml", h3)
        self.assertLess(h3, literature_gate)
        self.assertLess(literature_gate, h5)
        self.assertIn("PAUSE", harness[h3:h5])
        self.assertRegex(harness[h3:h5], r"(?i)(数量|语言|覆盖).{0,160}(校验|通过)")
        self.assertRegex(harness[h3:h5], r"(?i)(返回|提交).{0,160}literature_sources\.yaml")
        self.assertRegex(entry, r"(?s)建模前.{0,240}literature_sources\.yaml.{0,240}PAUSE")

    def test_harness_uses_literature_before_route_and_figure_requirements(self):
        harness = (ROOT / "references/modes/full-contest-harness.md").read_text(encoding="utf-8")
        h3 = harness.index("| `H3`")
        h5 = harness.index("| `H5`")  # H4已并入H5
        literature_stage = harness[h3:h5]
        route_stage = harness[h5:h5+3000]  # 路线/蓝图阶段现在在 H5 阶段一

        self.assertIn("不得在本节点确定模型路线、模型蓝图、baseline 或图表需求清单", literature_stage)
        self.assertRegex(route_stage, r"(?i)(文献方法|method_transfer_map\.json).{0,240}(模型路线|模型蓝图)")
        self.assertRegex(route_stage, r"(?i)(数据|参数).{0,160}(使用|来源|迁移|data)")
        self.assertIn("图表需求清单", route_stage)
        self.assertIn("不定义数据图图型、视觉编码或版式", route_stage)
        self.assertRegex(route_stage, r"(?i)(adopt|adapt|采用|改造).{0,200}(小问|模型)")

    def test_harness_has_fixed_roles_and_h2_user_review_gate(self):
        harness = (ROOT / "references/modes/full-contest-harness.md").read_text(encoding="utf-8")
        for role in ("主 agent", "题意理解 agent", "解题 agent", "验证 agent", "图表 agent", "论文 agent"):
            self.assertIn(role, harness)
        self.assertIn("harness_control.yaml", harness)
        self.assertIn("owner_role", harness)
        self.assertIn("H2–H9", harness)
        self.assertIn("review_packet", harness)
        self.assertIn("user_approval", harness)
        self.assertIn("controller_only", harness)
        self.assertIn("conditional", harness)

    def test_h8_returns_evidence_gaps_instead_of_filler(self):
        harness = (ROOT / "references/modes/full-contest-harness.md").read_text(encoding="utf-8")
        h8 = harness[harness.index("## H8"):]
        for marker in ("evidence_gap", "H5/H6/H7", "重复表述", "泛泛背景", "空洞评价", "文献堆砌"):
            self.assertIn(marker, h8)

    def test_harness_declares_node_level_model_routing(self):
        harness = (ROOT / "references/modes/full-contest-harness.md").read_text(encoding="utf-8")
        template = (ROOT / "templates/harness_task_card.yaml").read_text(encoding="utf-8")
        for marker in ("H1", "H5", "H6", "H7", "H8", "gpt-5.6-sol", "gpt-5.6-terra", "reasoning_effort"):
            self.assertIn(marker, harness)
        self.assertIn("model:", template)
        self.assertIn("reasoning_effort:", template)

    def test_stable_memory_records_harness_contract(self):
        memory = (ROOT / "MEMORY.md").read_text(encoding="utf-8")
        for marker in (
            "full-contest-harness",
            "H0–H9",
            "fixed roles",
            "SHA-256",
            "H8",
            "evidence_gap",
        ):
            self.assertIn(marker, memory)


if __name__ == "__main__":
    unittest.main()
