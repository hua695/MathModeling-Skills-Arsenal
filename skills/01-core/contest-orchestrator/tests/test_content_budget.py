import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_content_budget.py"
REQUIRED = [
    "problem_goal", "modeling_idea", "model_selection_rationale", "assumptions",
    "variables_and_units", "original_relations", "derivation_chain", "final_model",
    "parameter_determination", "solver_or_algorithm", "result_provenance",
    "validation", "result_interpretation", "conclusion_mapping",
]


def plan(status="planned", solution_prediction=27):
    return {
        "schema_version": "1.0",
        "profile": "CUMCM_personal_25_30",
        "page_policy": {
            "planning_target": [25, 30],
            "delivery_target": [25, 30],
            "hard_max": 30,
            "short_paper_review_threshold": 25,
        },
        "content_budget": {
            "tolerance_pages": 1,
            "shared_sections": [{"id": "shared", "target_pages": 4}],
            "subproblems": [{"id": "Q1", "target_pages": 10, "evidence_units": REQUIRED,
                            "evidence_status": status}],
            "global_sections": [{"id": "validation", "target_pages": 5},
                                {"id": "evaluation", "target_pages": 8}],
        },
        "checkpoints": {
            "blueprint": {"predicted_body_pages": 27},
            "solution": {"predicted_body_pages": solution_prediction},
        },
        "padding_flags": [],
    }


class ContentBudgetTests(unittest.TestCase):
    def run_check(self, root, stage, *extra):
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(root), "--stage", stage, *extra],
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
        )

    def test_blueprint_accepts_planned_capacity(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "content_budget_plan.json").write_text(json.dumps(plan()), encoding="utf-8")
            result = self.run_check(root, "blueprint", "--strict")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "PASS")

    def test_solution_requires_completed_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "content_budget_plan.json").write_text(json.dumps(plan()), encoding="utf-8")
            result = self.run_check(root, "solution", "--strict")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("证据尚未完成", result.stdout)

    def test_solution_passes_after_evidence_completion(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "content_budget_plan.json").write_text(json.dumps(plan("complete")), encoding="utf-8")
            result = self.run_check(root, "solution", "--strict")
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_short_pdf_is_not_strict_pass(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "content_budget_plan.json").write_text(json.dumps(plan("complete")), encoding="utf-8")
            result = self.run_check(root, "pdf", "--body-pages", "23", "--strict")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["status"], "SHORT_PAPER_REVIEW")

    def test_short_pdf_exception_is_explicit(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "content_budget_plan.json").write_text(json.dumps(plan("complete")), encoding="utf-8")
            result = self.run_check(root, "pdf", "--body-pages", "23", "--strict", "--allow-short-exception")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "SHORT_PAPER_REVIEW")

    def test_missing_plan_warns_in_non_strict_and_blocks_in_strict(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            soft = self.run_check(root, "solution")
            hard = self.run_check(root, "solution", "--strict")
            self.assertEqual(soft.returncode, 0)
            self.assertEqual(json.loads(soft.stdout)["status"], "WARN")
            self.assertNotEqual(hard.returncode, 0)

    def test_page_profile_isolated_by_competition(self):
        spec = importlib.util.spec_from_file_location("delivery_all", ROOT / "scripts" / "delivery_all.py")
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        self.assertTrue(module.content_budget_enabled("guosai", None))
        self.assertFalse(module.content_budget_enabled("mcm_icm", None))
        self.assertTrue(module.content_budget_enabled("mcm_icm", "plan.yaml"))

    def test_evidence_first_plan_requires_derived_index_in_solution(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            enhanced = plan("complete")
            enhanced["schema_version"] = "1.1"
            enhanced["planning_contract"] = "evidence_first"
            enhanced["evidence_policy"] = {
                "source_of_truth": ".contest/evidence_index.json",
                "required_sources": ["model_contract", "derivation_registry", "modeling_solution_contract", "run_manifest"],
            }
            (root / "content_budget_plan.json").write_text(json.dumps(enhanced), encoding="utf-8")
            result = self.run_check(root, "solution", "--strict")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("evidence_index.json", result.stdout)


if __name__ == "__main__":
    unittest.main()
