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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def interface_case(root: Path, *, include_source_path: bool = True,
                   include_source_sha256: bool = True) -> tuple[dict, dict]:
    source = root / "evidence.md"
    source.write_text("frozen interface evidence\n", encoding="utf-8")
    field = {
        "field": "shared_symbols",
        "unit": "dimensionless",
        "time_scale": "static",
        "comparison_status": "passed",
    }
    if include_source_path:
        field["source_path"] = "evidence.md"
    if include_source_sha256:
        field["source_sha256"] = digest(source)
    card = root / ".contest" / "task_cards" / "H6.yaml"
    card.parent.mkdir(parents=True, exist_ok=True)
    card.write_text("task_id: H6-001\n", encoding="utf-8")
    report = {
        "status": "PASS",
        "verified_by": "H6",
        "verification_agent_instance_id": "h6-001",
        "task_card_path": ".contest/task_cards/H6.yaml",
        "task_card_sha256": digest(card),
        "checks": {name: True for name in (
            "shared_symbols", "units", "data_versions", "upstream_downstream_fields",
            "time_scales", "parameters", "cross_question_constraints", "conclusions",
            "provenance",
        )},
        "issues": [],
        "per_subproblem": [{"subproblem_id": "Q1", "interface_fields": [field]}],
    }
    nodes = {
        "H5": {"agent_instance_id": "h5-001", "solver_instance_id": "solver-001"},
        "H6": {
            "agent_instance_id": "h6-001",
            "global_interface_check": "global_interface_check.yaml",
        },
    }
    write_yaml(root / "global_interface_check.yaml", report)
    return nodes, {"subproblems": ["Q1"]}


def h7_binding_case(root: Path, *, card_hash: str | None = None,
                    dispatched_at: str = "2026-09-14T10:01:00+00:00") -> tuple[dict, dict, dict]:
    plan = root / "visual_argument_plan.yaml"
    write_yaml(plan, {"schema_version": "1.0", "status": "approved"})
    plan_hash = digest(plan)
    approved_hash = card_hash if card_hash is not None else plan_hash
    card = root / ".contest" / "task_cards" / "H7-generate.yaml"
    write_yaml(card, {
        "task_id": "H7-generate-001",
        "node_id": "H7",
        "scope": {
            "phase": "H7_generate",
            "approved_visual_plan_sha256": approved_hash,
        },
    })
    control = {
        "dispatch_records": [{
            "task_id": "H7-generate-001",
            "node_id": "H7",
            "task_card_path": ".contest/task_cards/H7-generate.yaml",
            "task_card_sha256": digest(card),
            "dispatched_at": dispatched_at,
        }],
    }
    log = {"approvals": [{
        "gate": "H7_VISUAL_PLAN",
        "decision": "approved",
        "timestamp": "2026-09-14T10:00:00+00:00",
        "artifact_digests": {"visual_argument_plan.yaml": plan_hash},
    }]}
    node = {"visual_argument_plan": "visual_argument_plan.yaml"}
    return control, node, log


def h5_traceability_case(root: Path, *, complete: bool = True) -> None:
    result = root / "results" / "result.json"
    formal = root / "results" / "formal.json"
    contract = root / "model_contract.yaml"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text('{"objective": 1.0}\n', encoding="utf-8")
    formal.write_text('{"case": "A", "value": 1}\n', encoding="utf-8")
    contract.write_text("schema_version: '1.0'\n", encoding="utf-8")
    contract_hash = digest(contract)
    manifest = {
        "schema_version": "1.0",
        "status": "verified",
        "node_id": "H5",
        "seed": 7,
        "offline_run": {
            "command": "python solve.py",
            "result": {"path": "results/result.json", "sha256": digest(result)},
        },
        "formal_tests": {
            "record_fields": ["case_code", "result_file"],
            "Q1": {"records": [{
                "case_code": "A",
                "result_file": {"path": "results/formal.json", "sha256": digest(formal)},
            }]},
        },
        "formal_interpretation_boundary": "The formal record covers the tested cases only.",
        "model_contract_sha256": contract_hash,
    }
    sensitivity = {
        "schema_version": "1.0",
        "status": "verified",
        "model_contract_sha256": contract_hash,
        "method": "seeded perturbation",
        "results": [{
            "subproblem_id": "Q1",
            "parameter": "p",
            "perturbation_points": [{"value": 1, "objective": 2.0}],
        }],
    }
    canonical = root / "results" / "canonical_sensitivity.yaml"
    canonical.write_text("canonical sensitivity evidence\n", encoding="utf-8")
    sensitivity["canonical_report"] = {
        "path": "results/canonical_sensitivity.yaml",
        "sha256": digest(canonical),
    }
    if not complete:
        manifest.pop("model_contract_sha256")
        manifest.pop("formal_interpretation_boundary")
        manifest["offline_run"].pop("command")
        manifest.pop("formal_tests")
        sensitivity["results"] = []
    write_yaml(root / "run_manifest.yaml", manifest)
    write_yaml(root / "sensitivity_report.yaml", sensitivity)


class HarnessReplayAbsorptionTests(unittest.TestCase):
    def test_h6_interface_requires_source_path_and_sha256(self):
        checker = load_module("scripts/check_harness_control.py", "harness_replay_checker_h6")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            nodes, scope = interface_case(root, include_source_path=False, include_source_sha256=False)
            missing, failures = [], []
            checker._validate_h6_interface(root, nodes, scope, missing, failures)
        messages = missing + failures
        self.assertTrue(any("source_path" in item for item in messages), messages)
        self.assertTrue(any("source_sha256" in item for item in messages), messages)

    def test_h6_interface_accepts_matching_source_provenance(self):
        checker = load_module("scripts/check_harness_control.py", "harness_replay_checker_h6_pass")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            nodes, scope = interface_case(root)
            missing, failures = [], []
            checker._validate_h6_interface(root, nodes, scope, missing, failures)
        self.assertFalse(any("source_path" in item or "source_sha256" in item for item in missing + failures))

    def test_h7_generation_requires_approved_plan_hash(self):
        checker = load_module("scripts/check_harness_control.py", "harness_replay_checker_h7_missing")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, node, log = h7_binding_case(root, card_hash="")
            missing, failures = [], []
            checker._validate_h7_generation_binding(root, control, node, log, missing, failures)
        self.assertTrue(any("approved_visual_plan_sha256" in item for item in missing), missing + failures)

    def test_h7_generation_rejects_hash_mismatch_and_early_dispatch(self):
        checker = load_module("scripts/check_harness_control.py", "harness_replay_checker_h7_block")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, node, log = h7_binding_case(root, card_hash="0" * 64,
                                                 dispatched_at="2026-09-14T09:59:00+00:00")
            missing, failures = [], []
            checker._validate_h7_generation_binding(root, control, node, log, missing, failures)
        self.assertTrue(any("哈希" in item or "hash" in item.lower() for item in failures), failures)
        self.assertTrue(any("批准" in item or "approval" in item.lower() for item in failures), failures)

    def test_h7_generation_accepts_matching_hash_after_approval(self):
        checker = load_module("scripts/check_harness_control.py", "harness_replay_checker_h7_pass")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, node, log = h7_binding_case(root)
            missing, failures = [], []
            checker._validate_h7_generation_binding(root, control, node, log, missing, failures)
        self.assertEqual(missing, [])
        self.assertEqual(failures, [])

    def test_h5_result_traceability_requires_complete_evidence(self):
        checker = load_module("scripts/check_h5_result_traceability.py", "harness_replay_checker_h5_missing")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            h5_traceability_case(root, complete=False)
            report = checker.validate_h5_result_traceability(root)
        self.assertNotEqual(report["status"], "PASS")
        self.assertTrue(any("command" in item or "formal" in item or "model_contract" in item
                            for item in report["missing"] + report["failures"]), report)

    def test_h5_result_traceability_accepts_verified_package(self):
        checker = load_module("scripts/check_h5_result_traceability.py", "harness_replay_checker_h5_pass")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            h5_traceability_case(root)
            report = checker.validate_h5_result_traceability(root)
        self.assertEqual(report["status"], "PASS", report)

    def test_h5_result_traceability_requires_canonical_sensitivity_report(self):
        checker = load_module("scripts/check_h5_result_traceability.py", "harness_replay_checker_h5_canonical")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            h5_traceability_case(root)
            path = root / "sensitivity_report.yaml"
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            payload.pop("canonical_report")
            write_yaml(path, payload)
            report = checker.validate_h5_result_traceability(root)
        self.assertEqual(report["status"], "PAUSE", report)
        self.assertTrue(any("canonical_report" in item for item in report["missing"]), report)

    def test_h5_result_traceability_rejects_stale_output_hash(self):
        checker = load_module("scripts/check_h5_result_traceability.py", "harness_replay_checker_h5_stale")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            h5_traceability_case(root)
            (root / "results" / "result.json").write_text('{"objective": 2.0}\n', encoding="utf-8")
            report = checker.validate_h5_result_traceability(root)
        self.assertEqual(report["status"], "BLOCK", report)
        self.assertTrue(any("sha256" in item.lower() or "哈希" in item for item in report["failures"]), report)

    def test_harness_gate_requires_h5_traceability_registration(self):
        checker = load_module("scripts/check_harness_control.py", "harness_replay_checker_h5_registration")
        missing, failures = [], []
        checker._validate_h5_result_traceability_registration(
            Path.cwd(), {"status": "approved"}, missing, failures,
        )
        self.assertTrue(any("run_manifest" in item for item in missing), missing + failures)


if __name__ == "__main__":
    unittest.main()
