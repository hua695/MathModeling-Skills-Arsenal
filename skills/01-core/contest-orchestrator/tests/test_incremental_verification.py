import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_module(relative_path: str, module_name: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class IncrementalValidationTests(unittest.TestCase):
    def make_card(self, root: Path, level: str, kind: str, *, affected=None,
                  earliest: str | None = None) -> dict:
        artifact = root / "paper" / "paper.tex"
        if kind == "figure":
            artifact = root / "figures" / "figure.svg"
        elif kind == "question_model":
            artifact = root / "results" / "Q1_results.yaml"
        elif kind == "global_interface":
            artifact = root / "global_interface_check.yaml"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("current evidence\n", encoding="utf-8")
        return {
            "schema_version": "1.0",
            "change_id": f"chg-{level.lower()}-001",
            "profile": "competition_fast",
            "impact_level": level,
            "reason": "controlled contest artifact update",
            "changed_artifacts": [{
                "path": artifact.relative_to(root).as_posix(),
                "before_sha256": "0" * 64,
                "after_sha256": sha256(artifact),
                "artifact_kind": kind,
            }],
            "affected_subproblems": affected if affected is not None else ["Q1"],
            "earliest_invalid_node": earliest or {"L0": "H8", "L1": "H7", "L2": "H5", "L3": "H5"}[level],  # H4已并入H5
            "protected_fields": ["model", "numbers", "citations", "figure_ids"],
        }

    def test_l0_routes_only_paper_checks_and_keeps_h9(self):
        router = load_module("scripts/validation_router.py", "validation_router_l0")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = self.make_card(root, "L0", "paper_prose")
            self.assertEqual(router.validate_change_impact(root, card), [])
            plan = router.build_validation_plan(card)
            self.assertEqual(plan["recheck_nodes"], ["H8"])
            self.assertEqual(plan["full_delivery_gate"], "H9")
            self.assertFalse(plan["run_skill_suite"])

    def test_l1_routes_figure_checks_without_solver_recheck(self):
        router = load_module("scripts/validation_router.py", "validation_router_l1")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = self.make_card(root, "L1", "figure")
            self.assertEqual(router.validate_change_impact(root, card), [])
            plan = router.build_validation_plan(card)
            self.assertEqual(plan["recheck_nodes"], ["H7"])
            self.assertTrue(plan["visual_check"])
            self.assertNotIn("H5", plan["recheck_nodes"])
            self.assertIn("visual_evidence_binding", plan["checks"])

    def test_l2_routes_targeted_question_chain(self):
        router = load_module("scripts/validation_router.py", "validation_router_l2")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = self.make_card(root, "L2", "question_model", affected=["Q2"])
            self.assertEqual(router.validate_change_impact(root, card), [])
            plan = router.build_validation_plan(card)
            self.assertEqual(plan["recheck_nodes"], ["H5", "H6", "H7", "H8"])
            self.assertEqual(plan["affected_subproblems"], ["Q2"])
            self.assertFalse(plan["run_skill_suite"])
            self.assertIn("refresh_visual_evidence_packet", plan["checks"])

    def test_l3_requires_global_recalculation_route(self):
        router = load_module("scripts/validation_router.py", "validation_router_l3")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = self.make_card(root, "L3", "global_interface", affected=[], earliest="H5")  # H4已并入H5
            self.assertEqual(router.validate_change_impact(root, card), [])
            plan = router.build_validation_plan(card)
            self.assertEqual(plan["recheck_nodes"], ["H5", "H6", "H7", "H8"])  # H4已并入H5
            self.assertEqual(plan["full_delivery_gate"], "H9")

    def test_l2_rejects_multiple_subproblems(self):
        router = load_module("scripts/validation_router.py", "validation_router_negative")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = self.make_card(root, "L2", "question_model", affected=["Q1", "Q2"])
            errors = router.validate_change_impact(root, card)
            self.assertTrue(any("L2" in error and "一个小问" in error for error in errors))

    def test_stale_node_requires_change_card_in_competition_profile(self):
        router = load_module("scripts/validation_router.py", "validation_router_control")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            errors, plan = router.validate_control_validation(root, {
                "validation": {
                    "profile": "competition_fast",
                    "change_impact_card": None,
                },
                "nodes": {"H8": {"status": "stale"}},
            })
            self.assertTrue(any("stale" in error and "change_impact_card" in error for error in errors))
            self.assertIsNone(plan)

    def test_h9_remains_mandatory_in_every_profile_plan(self):
        router = load_module("scripts/validation_router.py", "validation_router_h9")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = self.make_card(root, "L0", "paper_prose")
            plan = router.build_validation_plan(card)
            self.assertTrue(plan["h9_full_delivery_required"])

    def test_harness_checker_consumes_competition_profile_gate(self):
        checker = load_module("scripts/check_harness_control.py", "check_harness_control_integration")
        control = checker.default_control()
        control["nodes"]["H8"]["status"] = "stale"
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contest_dir = root / ".contest"
            contest_dir.mkdir()
            (contest_dir / "harness_control.yaml").write_text(
                yaml.safe_dump(control, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            report = checker.check_harness_control(root, "H0")
            self.assertTrue(any("stale" in error and "change_impact_card" in error for error in report["failures"]))
            self.assertIsNone(report["validation_plan"])


class H8ReadinessMatrixTests(unittest.TestCase):
    def test_v2_readiness_matrix_requires_every_evidence_cell(self):
        checker = load_module("scripts/check_harness_control.py", "check_harness_control_matrix")
        required = (*checker.MATERIAL_FIELDS, "sensitivity_or_robustness")
        readiness = {
            "schema_version": "2.0",
            "status": "PASS",
            "subproblems": [{"id": "Q1", "materials": {}}],
            "evidence_matrix": {
                "Q1": {field: "ready" for field in required},
                "global": {"target_length": "ready"},
            },
        }
        failures: list[str] = []
        checker._validate_evidence_matrix(readiness, [], failures)
        self.assertEqual(failures, [])

        readiness["evidence_matrix"]["Q1"].pop("derivation")
        checker._validate_evidence_matrix(readiness, [], failures)
        self.assertTrue(any("derivation" in error for error in failures))

    def test_v2_readiness_matrix_marks_detected_gap_without_claiming_ready(self):
        checker = load_module("scripts/check_harness_control.py", "check_harness_control_matrix_gap")
        required = (*checker.MATERIAL_FIELDS, "sensitivity_or_robustness")
        readiness = {
            "schema_version": "2.0",
            "status": "PAUSE",
            "subproblems": [{"id": "Q1", "materials": {}}],
            "evidence_matrix": {
                "Q1": {field: "ready" for field in required},
                "global": {"target_length": "ready"},
            },
        }
        failures: list[str] = []
        gaps = [{"subproblem_id": "Q1", "requirement": "derivation", "responsible_node": "H5"}]
        checker._validate_evidence_matrix(readiness, gaps, failures)
        self.assertTrue(any("derivation" in error for error in failures))

        readiness["evidence_matrix"]["Q1"]["derivation"] = "missing"
        failures.clear()
        checker._validate_evidence_matrix(readiness, gaps, failures)
        self.assertEqual(failures, [])


class ContractDocumentationTests(unittest.TestCase):
    def test_new_contracts_are_routed_from_entrypoint_and_templates(self):
        skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        harness_template = (ROOT / "templates" / "harness_control.yaml").read_text(encoding="utf-8")
        readiness_template = (ROOT / "templates" / "paper_material_readiness.yaml").read_text(encoding="utf-8")
        self.assertIn("change_impact_card", skill_text)
        self.assertIn("competition_fast", skill_text)
        self.assertIn("evidence_matrix", skill_text)
        self.assertIn("profile: competition_fast", harness_template)
        self.assertIn("schema_version: \"2.0\"", readiness_template)
        self.assertIn("evidence_matrix", readiness_template)

    def test_profile_template_is_machine_readable(self):
        profile_path = ROOT / "templates" / "competition_run_profile.yaml"
        payload = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["profile"], "competition_fast")
        self.assertTrue(payload["h9_full_delivery_required"])
        self.assertFalse(payload["run_skill_suite_on_project_change"])


if __name__ == "__main__":
    unittest.main()
