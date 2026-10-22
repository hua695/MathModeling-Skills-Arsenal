from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeepCleanupContractTests(unittest.TestCase):
    def test_operational_docs_have_no_historical_debug_markers(self):
        forbidden = {
            "core/controller.md": ["拒绝 Transformer", "切 skyline", "旧记录 → archive/"],
            "core/frozen_numbers.md": ["v4.1 新增", "改 bug 后"],
            "core/paper_postfix_checklist.md": [
                "实战返工最多",
                "fix_lst",
                "apply_minted",
                "fix_vrb_font",
                "v4.9",
            ],
            "core/time_engine.md": ["v3.4", "原 72h 参考", "Kimi 评审", "v4.1：国赛 74h"],
            "manifest.yaml": ["🆕", "v3.4", "v4.15", "v4.17", "legacy 兼容诊断"],
        }
        for relative, markers in forbidden.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            for marker in markers:
                self.assertNotIn(marker, text, f"历史或调试标记仍存在: {relative}: {marker}")

    def test_runtime_tree_excludes_case_artifacts_and_has_clean_replay_template(self):
        self.assertFalse((ROOT / "examples" / "huashu2026_replay.md").exists())
        self.assertFalse((ROOT / "simulations" / "2025_cumcm_B").exists())
        template = ROOT / "references" / "replay_template.md"
        self.assertTrue(template.exists())
        text = template.read_text(encoding="utf-8")
        self.assertNotIn("你睡觉", text)
        self.assertNotIn("弃用", text)

    def test_authoritative_routes_and_quality_policy_remain(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for marker in (
            "主会话—fork 协作",
            "academic-writing",
            "humanizer-zh",
            "画图默认做视觉检查",
            "非画图默认不做视觉检查",
            "模型、数据、结果、引用、图表",
        ):
            self.assertIn(marker, skill)


if __name__ == "__main__":
    unittest.main()
