import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_visual_evidence.py"


def plan(status="required"):
    return {
        "visual_policy": {"table_to_figure_review_ratio": 1.5},
        "content_budget": {"subproblems": [{
            "id": "Q1", "visual_decision": {"status": status, "rationale": "fixture rationale"},
            "visual_evidence": [{"id": "q1-result", "figure_id": "fig_q1", "claim": "fixture claim",
                                 "role": "primary", "source": "results/q1.json", "target_section": "6.1"}],
        }]},
    }


class VisualEvidenceTests(unittest.TestCase):
    def test_solution_requires_registered_primary_figure(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "content_budget_plan.json").write_text(json.dumps(plan()), encoding="utf-8")
            bad = subprocess.run([sys.executable, str(CHECKER), str(root), "--stage", "solution"],
                                 capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(bad.returncode, 0)
            (root / "results").mkdir()
            (root / "results" / "q1.json").write_text("{}", encoding="utf-8")
            (root / "plot.py").write_text("# fixture\n", encoding="utf-8")
            (root / "figure_registry.json").write_text(json.dumps({"figures": {
                "fig_q1": {"qa_status": "pass", "kind": "data", "generator": "scipilot",
                           "source_files": ["results/q1.json"], "script": "plot.py", "formats": ["png"]}
            }}), encoding="utf-8")
            good = subprocess.run([sys.executable, str(CHECKER), str(root), "--stage", "solution"],
                                  capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(good.returncode, 0, good.stdout)

    def test_paper_balance_is_review_warning_not_fixed_count_failure(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            payload = plan()
            payload["content_budget"]["subproblems"].append({
                "id": "Q2", "visual_decision": {"status": "required", "rationale": "fixture rationale"},
                "visual_evidence": [{"id": "q2-result", "figure_id": "fig_q2", "claim": "fixture claim",
                                     "role": "primary", "source": "results/q2.json", "target_section": "6.2"}],
            })
            (root / "content_budget_plan.json").write_text(json.dumps(payload), encoding="utf-8")
            (root / "figure_registry.json").write_text(json.dumps({"figures": {
                "fig_q1": {"qa_status": "pass", "source_files": ["results/q1.json"]},
                "fig_q2": {"qa_status": "pass", "source_files": ["results/q2.json"]}
            }}), encoding="utf-8")
            (root / "paper.tex").write_text("\\begin{table}x\\end{table}\n" * 3, encoding="utf-8")
            result = subprocess.run([sys.executable, str(CHECKER), str(root), "--stage", "paper", "--tex", str(root / "paper.tex")],
                                    capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "WARN")


if __name__ == "__main__":
    unittest.main()
