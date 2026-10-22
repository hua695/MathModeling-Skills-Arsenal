import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_skill_consistency.py"


class SkillConsistencyTests(unittest.TestCase):
    def test_current_skill_passes_strict_consistency_audit(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(ROOT), "--strict"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["failures"], [])
        self.assertEqual(report["warnings"], [])
        self.assertGreaterEqual(report["active_script_count"], 1)
        self.assertEqual(
            report["active_script_count"], report["classified_script_count"]
        )

    def test_unregistered_active_script_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "scripts").mkdir()
            (root / "SKILL.md").write_text("metadata:\n  version: '4.15'\n", encoding="utf-8")
            (root / "manifest.yaml").write_text(
                "version: '4.15'\nschema_version: '2.0'\n", encoding="utf-8"
            )
            (root / "VERSION").write_text("4.15\n", encoding="utf-8")
            (root / "scripts" / "script_registry.yaml").write_text(
                "schema_version: '1.0'\ncategories:\n  canonical_entrypoints: []\n",
                encoding="utf-8",
            )
            (root / "scripts" / "rogue.py").write_text("print('x')\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root), "--strict"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
            )
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertFalse(report["passed"])
            self.assertTrue(any("未分类" in item for item in report["failures"]))


if __name__ == "__main__":
    unittest.main()
