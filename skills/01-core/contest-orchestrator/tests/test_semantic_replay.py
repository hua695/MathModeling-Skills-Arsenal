import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SemanticReplayTests(unittest.TestCase):
    def test_fixture_shows_skill_evidence_gain(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "semantic_report.json"
            command = [sys.executable, str(ROOT / "scripts" / "semantic_replay.py"),
                       str(ROOT / "tests" / "fixtures" / "semantic_cases.jsonl"),
                       "--out", str(out), "--strict"]
            result = subprocess.run(command, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(report["passed"])
            self.assertTrue(all(item["delta"] > 0 for item in report["cases"]))
            self.assertFalse(report["is_llm_benchmark"])


if __name__ == "__main__":
    unittest.main()
