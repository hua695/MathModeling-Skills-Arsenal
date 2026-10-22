import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_ai_compliance.py"
SPEC = importlib.util.spec_from_file_location("check_ai_compliance", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AiComplianceTests(unittest.TestCase):
    def profile(self):
        return json.loads((ROOT / "planner" / "competition_profiles" / "guosai_2026_ai.json").read_text(encoding="utf-8"))

    def test_before_effective_date_is_info(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper"
            paper.mkdir()
            (paper / "paper.tex").write_text("正文。", encoding="utf-8")
            report = MODULE.check(root, paper, self.profile(), date(2026, 8, 25))
            self.assertEqual(report["status"], "INFO")

    def test_after_effective_date_requires_declaration(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper"
            paper.mkdir()
            (paper / "paper.tex").write_text("正文。\\section{参考文献}", encoding="utf-8")
            report = MODULE.check(root, paper, self.profile(), date(2026, 9, 1))
            self.assertEqual(report["status"], "BLOCK")

    def test_no_ai_declaration_before_references_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper"
            paper.mkdir()
            (paper / "paper.tex").write_text(
                "AI工具使用声明：本参赛队在竞赛过程中未使用任何AI工具。\\section{参考文献}",
                encoding="utf-8",
            )
            report = MODULE.check(root, paper, self.profile(), date(2026, 9, 1))
            self.assertEqual(report["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
