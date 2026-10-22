import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_page_margins.py"


class PageMarginTests(unittest.TestCase):
    def run_check(self, paper, *extra):
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(paper), *extra],
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
        )

    def test_guosai_explicit_four_sides_pass(self):
        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw)
            (paper / "paper.tex").write_text(
                "\\usepackage{geometry}\n\\geometry{top=2.5cm,bottom=2.5cm,left=2.6cm,right=2.5cm}\n",
                encoding="utf-8",
            )
            result = self.run_check(paper, "--strict")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "PASS")

    def test_geometry_margin_shorthand_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw)
            (paper / "paper.tex").write_text(
                "\\usepackage[a4paper,margin=2.5cm]{geometry}\n", encoding="utf-8"
            )
            result = self.run_check(paper, "--strict")
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_guosai_missing_declaration_blocks_strict(self):
        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw)
            (paper / "paper.tex").write_text("\\documentclass{article}\n", encoding="utf-8")
            result = self.run_check(paper, "--strict")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("未明确声明", result.stdout)

    def test_guosai_missing_declaration_is_visible_warn_non_strict(self):
        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw)
            (paper / "paper.tex").write_text("\\documentclass{article}\n", encoding="utf-8")
            result = self.run_check(paper)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "WARN")

    def test_other_competitions_do_not_inherit_gate(self):
        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw)
            result = self.run_check(paper, "--competition", "mcm_icm", "--strict")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "INFO")


if __name__ == "__main__":
    unittest.main()
