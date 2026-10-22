import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AI_SCRIPT = ROOT / "scripts" / "check_ai_compliance.py"
HARD_SCRIPT = ROOT / "scripts" / "check_paper_hard_requirements.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AI = load_module("check_ai_compliance_2026", AI_SCRIPT)
HARD = load_module("check_paper_hard_requirements_2026", HARD_SCRIPT)


class Guosai2026RuleTests(unittest.TestCase):
    def test_authoritative_profile_contains_2026_submission_rules(self):
        profile = json.loads(
            (ROOT / "planner" / "competition_profiles" / "guosai_2026_ai.json")
            .read_text(encoding="utf-8")
        )
        self.assertTrue(profile["paper"]["non_image_pdf_required"])
        self.assertEqual(profile["paper"]["max_size_mb"], 20)
        self.assertFalse(profile["paper"]["toc_allowed"])
        self.assertEqual(profile["paper"]["body_max_pages"], 30)
        self.assertTrue(profile["paper"]["body_includes_references"])
        self.assertFalse(profile["ai"]["reference_entry_required"])
        self.assertTrue(profile["ai"]["truthful_disclosure_required"])
        self.assertEqual(profile["registration_deadline"], "2026-09-07T20:00+08:00")

    def test_ai_detail_missing_required_field_blocks_after_effective_date(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper"
            paper.mkdir()
            (paper / "paper.tex").write_text(
                "AI工具使用声明：本参赛队在竞赛过程中使用了 AI 工具，主要用于语言润色；"
                "\\section{参考文献}",
                encoding="utf-8",
            )
            (root / "AI工具使用详情.pdf").write_bytes(b"not a readable pdf")
            report = AI.check(root, paper, self._profile(), date(2026, 9, 1))
            self.assertIn(report["status"], {"WARN", "BLOCK"})
            self.assertNotIn("reference", json.dumps(report, ensure_ascii=False).lower())

    def test_body_page_count_includes_reference_pages_when_configured(self):
        texts = [
            "摘要\n正文",
            "模型建立与求解",
            "参考文献\n[1] source",
            "附录A 支撑材料文件列表",
            "附录B 源程序代码说明",
        ]
        self.assertEqual(HARD.body_page_count(texts, include_references=True), 3)
        self.assertEqual(HARD.body_page_count(texts, include_references=False), 2)
        self.assertEqual(HARD.body_page_count(texts, include_references=True, include_abstract=False), 2)
        self.assertEqual(HARD.body_page_count(texts, include_references=False, include_abstract=False), 1)

    def test_hard_checker_maps_nested_profile_page_rules(self):
        profile = HARD.load_profile(
            str(ROOT / "planner" / "competition_profiles" / "guosai_2026_ai.json")
        )
        self.assertFalse(profile["body_includes_abstract"])
        self.assertTrue(profile["body_includes_references"])
        self.assertEqual(profile["body_pages"]["max"], 30)
        self.assertEqual(profile["whole_paper_max_pages"], 51)

    @staticmethod
    def _profile():
        return json.loads(
            (ROOT / "planner" / "competition_profiles" / "guosai_2026_ai.json")
            .read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
