import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mode_router.py"


class ModeRouterTests(unittest.TestCase):
    def run_router(self, *args):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        payload = json.loads(result.stdout)
        return result, payload

    def test_missing_mode_requires_user_selection_without_loading_mode_files(self):
        result, payload = self.run_router()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "ASK_USER")
        self.assertEqual(payload["read_files"], [])
        self.assertIn("full-contest", payload["choices"])

    def test_full_contest_without_variant_requires_submode(self):
        result, payload = self.run_router("--mode", "full-contest")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "ASK_USER")
        self.assertEqual(payload["read_files"], [])
        self.assertEqual(
            payload["choices"],
            ["full-contest-legacy", "full-contest-4-18", "full-contest-harness", "full-contest-mathorcup"],
        )

    def test_selected_harness_loads_only_harness_mode_file(self):
        result, payload = self.run_router("--mode", "full-contest-harness")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "READY")
        self.assertEqual(payload["active_mode"], "full-contest-harness")
        self.assertEqual(
            payload["read_files"],
            ["references/modes/full-contest-harness.md"],
        )
        self.assertNotIn("full-contest-legacy.md", payload["read_files"])
        self.assertNotIn("full-contest-4-18.md", payload["read_files"])

    def test_full_contest_variant_form_selects_the_same_mode(self):
        result, payload = self.run_router("--mode", "full-contest", "--variant", "4.18")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "READY")
        self.assertEqual(payload["active_mode"], "full-contest-4-18")
        self.assertEqual(
            payload["read_files"],
            ["references/modes/full-contest-4-18.md"],
        )

    def test_rc_alias_preserves_backward_compatibility(self):
        result, payload = self.run_router("--mode", "full-contest-4-18rc")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["active_mode"], "full-contest-4-18")

    def test_mathorcup_alias_loads_only_its_mode_file(self):
        result, payload = self.run_router("--mode", "mathorcup")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["active_mode"], "full-contest-mathorcup")
        self.assertEqual(payload["read_files"], ["references/modes/full-contest-mathorcup.md"])

    def test_all_is_comparison_only_and_does_not_select_execution_mode(self):
        result, payload = self.run_router("--mode", "all")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "COMPARE_ONLY")
        self.assertIsNone(payload["active_mode"])
        self.assertEqual(payload["execution_allowed"], False)
        self.assertEqual(len(payload["read_files"]), 9)


if __name__ == "__main__":
    unittest.main()
