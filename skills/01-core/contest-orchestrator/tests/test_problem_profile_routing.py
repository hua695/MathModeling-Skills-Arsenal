import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "route_problem_profile.py"


class ProblemProfileRoutingTests(unittest.TestCase):
    def run_profile(self, body: str, strict: bool = True):
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            (project / "problem_profile.yaml").write_text(body, encoding="utf-8")
            cmd = [sys.executable, str(SCRIPT), str(project)]
            if strict:
                cmd.append("--strict")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                    env={**__import__('os').environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
            return result, json.loads(result.stdout)

    def test_mixed_problem_routes_each_subproblem_independently(self):
        result, report = self.run_profile(
            """competition: cumcm
problem_slot: B
subproblems:
  Q1:
    capabilities: [mechanistic, inverse]
  Q2:
    capabilities: [optimization]
  Q3:
    capabilities: [uncertainty]
shared_interfaces: []
"""
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["routes"]), 3)
        self.assertIn("mechanistic_optimization", report["routes"][0]["profiles"])
        self.assertIn("optimization", report["routes"][1]["capabilities"])

    def test_slot_is_not_authoritative_for_c_problem(self):
        result, report = self.run_profile(
            """competition: cumcm
problem_slot: C
subproblems:
  Q1:
    capabilities: [mechanistic]
"""
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["status"], "WARN")
        self.assertTrue(any("以逐小问能力为准" in item for item in report["warnings"]))

    def test_unknown_capability_blocks_strict(self):
        result, report = self.run_profile(
            """competition: cumcm
problem_slot: A
subproblems:
  Q1:
    capabilities: [made_up_type]
"""
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["status"], "FAIL")

    def test_absent_profile_preserves_legacy_route(self):
        with tempfile.TemporaryDirectory() as raw:
            result = subprocess.run([sys.executable, str(SCRIPT), raw, "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                                    env={**__import__('os').environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
            report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["status"], "INFO")


if __name__ == "__main__":
    unittest.main()
