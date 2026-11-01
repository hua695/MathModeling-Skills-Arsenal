"""Behavioral regressions for the opt-in MathorCup execution contract."""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_mathorcup_control import MathorCupFixture, checker


class PostmortemTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.fixture = MathorCupFixture(Path(temp.name))
        self.root = self.fixture.root

    def requirement_case(self, count=50):
        source = self.fixture.put("inputs/requirements.txt", "Return three records for every target.")
        kpi = {"subproblems": {"Q1": {
            "source": source, "locator": "Question 1", "requirement_text": "Every target",
            "final_carrier": "results/outputs.yaml",
            "targets": [f"t{i}" for i in range(count)], "outputs_per_target": 3,
            "constraints": [{"constraint_id": "chemical", "object": "concentration", "unit": "mg/L"}],
        }}}
        rows = [{"target_id": f"t{i}", "output_id": str(j)} for i in range(count) for j in range(3)]
        artifact = self.fixture.put("results/outputs.yaml", {"outputs": rows})
        coverage = {"Q1": {"output_artifact": artifact, "constraints": [{
            "constraint_id": "chemical", "status": "PASS", "evaluation_kind": "original",
            "object": "concentration", "unit": "mg/L", "evidence": source,
        }]}}
        return kpi, coverage, rows

    def check_coverage(self, kpi, coverage):
        errors = []
        checker._check_requirement_coverage(self.root, kpi, coverage, ["Q1"], errors)
        return errors

    def test_full_target_set_passes(self):
        kpi, coverage, _ = self.requirement_case()
        self.assertEqual(self.check_coverage(kpi, coverage), [])

    def test_45_target_subset_is_not_50_target_delivery(self):
        kpi, coverage, rows = self.requirement_case()
        coverage["Q1"]["output_artifact"] = self.fixture.put("results/outputs.yaml", {"outputs": rows[:135]})
        self.assertTrue(self.check_coverage(kpi, coverage))

    def test_equal_row_count_with_duplicates_still_fails(self):
        kpi, coverage, rows = self.requirement_case()
        rows[-1] = copy.deepcopy(rows[-2])
        coverage["Q1"]["output_artifact"] = self.fixture.put("results/outputs.yaml", {"outputs": rows})
        self.assertTrue(self.check_coverage(kpi, coverage))

    def test_minimal_supplement_preserves_original_rows(self):
        kpi, coverage, rows = self.requirement_case()
        original = copy.deepcopy(rows[:135])
        supplemented = original + rows[135:]
        coverage["Q1"]["output_artifact"] = self.fixture.put("results/outputs.yaml", {"outputs": supplemented})
        self.assertEqual(supplemented[:135], original)
        self.assertEqual(self.check_coverage(kpi, coverage), [])

    def test_proxy_cannot_pass_original_constraint(self):
        kpi, coverage, _ = self.requirement_case(2)
        coverage["Q1"]["constraints"][0].update(evaluation_kind="proxy", object="sensory_prediction")
        self.assertTrue(self.check_coverage(kpi, coverage))

    def test_unknown_units_cannot_be_certified(self):
        kpi, coverage, _ = self.requirement_case(2)
        coverage["Q1"]["constraints"][0].update(status="UNKNOWN", unit=None)
        self.assertTrue(self.check_coverage(kpi, coverage))

    def test_target_dimensions_are_not_contest_constants(self):
        kpi, coverage, _ = self.requirement_case(7)
        self.assertEqual(self.check_coverage(kpi, coverage), [])

    def reproduction_case(self):
        script = self.fixture.put("src/train.py", "print('train')")
        data = self.fixture.put("data/raw.csv", "x,y\n1,2\n")
        manifest = {"training_entrypoint": {"script": script, "command": ["python", "src/train.py"],
                                             "raw_inputs": [data], "config_refs": []},
                    "reproduction_plan": {"required_units": ["fold-1", "fold-2"], "minimum_level": "refit"}}
        result = self.fixture.put("results/metrics.json", '{"mae": 0.1}')
        report = {"level": "refit", "claim": "partial", "clean_directory": True,
                  "required_units": ["fold-1", "fold-2"], "completed_units": ["fold-1"],
                  "runs": [{"unit_id": "fold-1", "level": "refit", "exit_code": 0,
                            "command": ["python", "src/train.py"], "result_refs": [result]}]}
        return manifest, report

    def test_partial_refit_is_honest_but_not_full_retraining(self):
        manifest, report = self.reproduction_case()
        errors = []
        checker._check_reproduction(self.root, manifest, report, errors)
        self.assertEqual(errors, [])
        report["claim"] = "full"
        checker._check_reproduction(self.root, manifest, report, errors)
        self.assertTrue(errors)

    def test_saved_prediction_check_cannot_claim_refit(self):
        manifest, report = self.reproduction_case()
        report["runs"][0]["level"] = "saved_results"
        errors = []
        checker._check_reproduction(self.root, manifest, report, errors)
        self.assertTrue(errors)

    def test_training_input_cannot_depend_on_approval(self):
        manifest, report = self.reproduction_case()
        manifest["training_entrypoint"]["config_refs"] = [self.fixture.put(".contest/approval.json", "{}")]
        errors = []
        checker._check_reproduction(self.root, manifest, report, errors)
        self.assertTrue(errors)

    def test_approval_named_business_data_is_not_a_workflow_approval(self):
        manifest, report = self.reproduction_case()
        manifest["training_entrypoint"]["raw_inputs"] = [self.fixture.put("data/loan_approval.csv", "x,y\n1,2\n")]
        errors = []
        checker._check_reproduction(self.root, manifest, report, errors)
        self.assertEqual(errors, [])

    def test_declared_raw_data_entry_runs_without_original_project_state(self):
        script = self.fixture.put("src/train.py", "\n".join([
            "import csv, json",
            "from pathlib import Path",
            "rows = list(csv.DictReader(Path('data/raw.csv').open()))",
            "mean = sum(float(r['y']) for r in rows) / len(rows)",
            "Path('results').mkdir(exist_ok=True)",
            "Path('results/model.json').write_text(json.dumps({'mean': mean}))",
        ]))
        raw = self.fixture.put("data/raw.csv", "x,y\n1,2\n2,4\n")
        with tempfile.TemporaryDirectory() as directory:
            clean = Path(directory)
            for ref in (script, raw):
                target = clean / ref["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(self.root / ref["path"], target)
            run = subprocess.run([sys.executable, "src/train.py"], cwd=clean, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads((clean / "results/model.json").read_text()), {"mean": 3.0})
            self.assertFalse((clean / ".contest").exists())

    def test_full_retraining_requires_all_executed_units(self):
        manifest, report = self.reproduction_case()
        report["claim"] = "full"
        second = copy.deepcopy(report["runs"][0])
        second["unit_id"] = "fold-2"
        report["runs"].append(second)
        report["completed_units"].append("fold-2")
        errors = []
        checker._check_reproduction(self.root, manifest, report, errors)
        self.assertEqual(errors, [])

    def test_report_cannot_shrink_frozen_experiment_scope(self):
        manifest, report = self.reproduction_case()
        report.update(required_units=["fold-1"], claim="full")
        errors = []
        checker._check_reproduction(self.root, manifest, report, errors)
        self.assertTrue(errors)

    def test_new_protocol_m1_works_with_only_one_registered_role(self):
        control, record = self.registry_case()
        self.fixture.m1()
        data = self.fixture.control["agent_instances"]["data"]
        record["agent_instance_id"] = data["agent_instance_id"]
        record.update(created_at="2026-10-15T22:00:00+08:00", registered_at="2026-10-15T22:00:01+08:00")
        self.fixture.put(".contest/agent_registry.yaml", {"instances": [record]})
        self.fixture.control.update(execution_protocol="2.0", agent_instances={"data": data}, solver_instance_id=None)
        kpi, _, _ = self.requirement_case(2)
        self.fixture.complete("M1", {
            "problem_statement": self.fixture.problem,
            "data_overview": self.fixture.put("data_overview.yaml", {"sample_count": 2}),
            "task_kpi": self.fixture.put("task_kpi.yaml", kpi),
            "literature_request": self.fixture.put("literature_request.yaml", {"Q1": "method"}),
        }, ["math-model-selector"], 1)
        dispatch = self.fixture.control["dispatch_records"][0]
        path = dispatch["task_card"]
        card = yaml.safe_load((self.root / path).read_text(encoding="utf-8"))
        source = self.fixture.put(".contest/human_message.json", {
            "role": "user", "message_id": "human-start", "content": "Analyze the task",
            "task_ids": [card["task_id"]], "roles": ["data"], "created_at": "2026-10-15T23:00:00+08:00"})
        card["authorization"] = {"source": source, "message_id": "human-start"}
        dispatch["task_card_sha256"] = self.fixture.put(path, card)["sha256"]
        self.fixture.save()
        result = checker.check(self.root, through="M1")
        self.assertEqual(result["status"], "PASS", result)

    def registry_case(self):
        instance = "runtime-data"
        record = {"role": "data", "agent_instance_id": instance, "thread_id": str(uuid.uuid4()),
                  "user_accessible": True, "created_by": "main", "created_at": "2026-10-30T10:00:00+08:00",
                  "registered_at": "2026-10-30T10:00:01+08:00", "effective_from": "M1",
                  "model": "gpt-6-luna", "reasoning_effort": "max", "status": "active"}
        control = {"agent_instances": {"data": {"agent_instance_id": instance}}, "dispatch_records": []}
        self.fixture.put(".contest/agent_registry.yaml", {"instances": [record]})
        return control, record

    def check_registry(self, control):
        errors = []
        checker._check_role_registry(self.root, control, "M1", errors)
        return errors

    def test_user_accessible_registered_role_passes(self):
        control, _ = self.registry_case()
        self.assertEqual(self.check_registry(control), [])

    def test_native_only_role_is_rejected(self):
        control, record = self.registry_case()
        record.update(user_accessible=False, thread_id=None)
        self.fixture.put(".contest/agent_registry.yaml", {"instances": [record]})
        self.assertTrue(self.check_registry(control))

    def test_all_instances_including_support_must_be_registered(self):
        control, _ = self.registry_case()
        control["dispatch_records"].append({"agent_instance_id": "unregistered-support", "owner_role": "support",
                                             "node_id": "M1", "called_at": "2026-10-30T10:01:00+08:00"})
        self.assertTrue(self.check_registry(control))

    def test_duplicate_thread_for_distinct_instances_is_rejected(self):
        control, record = self.registry_case()
        other = {**record, "agent_instance_id": "different-runtime", "role": "verifier"}
        self.fixture.put(".contest/agent_registry.yaml", {"instances": [record, other]})
        self.assertTrue(self.check_registry(control))

    def test_same_role_runtime_recovery_can_reuse_its_accessible_chat(self):
        control, record = self.registry_case()
        successor = {**record, "agent_instance_id": "recovered-data", "replaces": record["agent_instance_id"],
                     "created_at": "2026-10-30T11:00:00+08:00", "registered_at": "2026-10-30T11:00:01+08:00"}
        record["status"] = "superseded"
        self.fixture.put(".contest/agent_registry.yaml", {"instances": [record, successor]})
        self.assertEqual(self.check_registry(control), [])

    def test_dispatch_before_registration_is_rejected(self):
        control, record = self.registry_case()
        control["dispatch_records"] = [{"agent_instance_id": record["agent_instance_id"], "owner_role": "data",
                                         "node_id": "M1", "called_at": record["created_at"]}]
        self.assertTrue(self.check_registry(control))

    def test_pending_creation_is_retained_but_not_an_execution_identity(self):
        control, record = self.registry_case()
        pending = {"status": "pending", "client_thread_id": "client-pending"}
        self.fixture.put(".contest/agent_registry.yaml", {"instances": [record, pending]})
        self.assertEqual(self.check_registry(control), [])
        control["agent_instances"]["solver"] = {"agent_instance_id": "client-pending"}
        self.assertTrue(self.check_registry(control))

    def test_final_carrier_is_not_optional(self):
        kpi, coverage, _ = self.requirement_case(2)
        del kpi["subproblems"]["Q1"]["final_carrier"]
        self.assertTrue(self.check_coverage(kpi, coverage))

    def test_malformed_constraint_id_is_a_failure_not_an_exception(self):
        kpi, coverage, _ = self.requirement_case(2)
        kpi["subproblems"]["Q1"]["constraints"][0]["constraint_id"] = []
        self.assertTrue(self.check_coverage(kpi, coverage))

    def test_csv_output_membership_is_checked(self):
        kpi, coverage, rows = self.requirement_case(3)
        text = "target_id,output_id\n" + "\n".join(f"{r['target_id']},{r['output_id']}" for r in rows)
        coverage["Q1"]["output_artifact"] = self.fixture.put("results/outputs.csv", text)
        self.assertEqual(self.check_coverage(kpi, coverage), [])

    def test_m1_does_not_require_idle_roles(self):
        self.fixture.m1()
        self.fixture.control["agent_instances"] = {"data": self.fixture.control["agent_instances"]["data"]}
        self.fixture.control["solver_instance_id"] = None
        errors = []
        checker._check_instances(self.root, self.fixture.control, errors, {"data"})
        self.assertEqual(errors, [])

    def test_human_authorization_can_be_reused_without_reasking(self):
        source = self.fixture.put(".contest/human_message.json", {
            "role": "user", "message_id": "human-1", "content": "Start figure task",
            "task_ids": ["figure-1"], "roles": ["figure"],
            "created_at": "2026-10-30T10:00:00+08:00"})
        card = {"task_id": "figure-1", "owner_role": "figure",
                "authorization": {"source": source, "message_id": "human-1"}}
        errors = []
        checker._check_human_authorization(self.root, card, "2026-10-30T11:00:00+08:00", errors)
        self.assertEqual(errors, [])
        message = yaml.safe_load((self.root / source["path"]).read_text(encoding="utf-8"))
        message["role"] = "assistant"
        card["authorization"]["source"] = self.fixture.put(source["path"], message)
        checker._check_human_authorization(self.root, card, "2026-10-30T11:00:00+08:00", errors)
        self.assertTrue(errors)

    def figure_case(self):
        svg = self.fixture.put("figures/FIG7.svg", "<svg>new</svg>")
        copy_ref = self.fixture.put("paper/figures/FIG7.svg", "<svg>new</svg>")
        source = self.fixture.put("paper/main.tex", r"\label{fig:transfer}\includesvg{figures/FIG7}")
        figure = {"figure_id": "FIG7", "paper_label": "fig:transfer", "paper_number": 13,
                  "selected_version": "v2", "selected_asset": svg, "paper_copy": copy_ref,
                  "paper_source": source, "integration_status": "integrated",
                  "canvas": {"width": 8, "height": 5, "unit": "cm"},
                  "insertion": {"width": 8, "unit": "cm"}}
        return {"figures": [figure]}

    def test_asset_id_is_independent_from_paper_number(self):
        errors = []
        checker._check_figure_integration(self.root, self.figure_case(), errors)
        self.assertEqual(errors, [])

    def test_stale_paper_copy_is_localized(self):
        registry = self.figure_case()
        registry["figures"][0]["paper_copy"] = self.fixture.put("paper/figures/FIG7.svg", "<svg>old</svg>")
        errors = []
        checker._check_figure_integration(self.root, registry, errors)
        self.assertTrue(any("FIG7" in error for error in errors))

    def test_registered_copy_must_actually_be_referenced_in_source(self):
        registry = self.figure_case()
        registry["figures"][0]["paper_source"] = self.fixture.put("paper/main.tex", r"\includesvg{figures/FIG6}")
        errors = []
        checker._check_figure_integration(self.root, registry, errors)
        self.assertTrue(errors)

    def test_new_protocol_m5_checks_actual_artifacts_end_to_end(self):
        self.fixture.m5()
        self.fixture.control["execution_protocol"] = "2.0"
        kpi, coverage, _ = self.requirement_case(7)
        self.fixture.put("task_kpi.yaml", kpi)
        self.fixture.put("model_summary_cards.yaml", {"requirement_coverage": coverage})
        manifest, reproduction = self.reproduction_case()
        old_manifest = yaml.safe_load((self.root / "run_manifest.yaml").read_text(encoding="utf-8"))
        self.fixture.put("run_manifest.yaml", {**old_manifest, **manifest})
        old_report = yaml.safe_load((self.root / "reproducibility_report.yaml").read_text(encoding="utf-8"))
        self.fixture.put("reproducibility_report.yaml", {**old_report, **reproduction})
        integration = self.figure_case()["figures"][0]
        registry = yaml.safe_load((self.root / "figure_registry.yaml").read_text(encoding="utf-8"))
        registry["figures"][0].update(integration)
        self.fixture.put("figure_registry.yaml", registry)
        records = []
        for role, instance in self.fixture.control["agent_instances"].items():
            records.append({"role": role, "agent_instance_id": instance["agent_instance_id"],
                            "thread_id": str(uuid.uuid4()), "user_accessible": True, "created_by": "main",
                            "created_at": "2026-10-15T20:00:00+08:00",
                            "registered_at": "2026-10-15T20:01:00+08:00", "effective_from": "M1",
                            "model": instance["model"], "reasoning_effort": instance["reasoning_effort"],
                            "status": "active"})
        self.fixture.put(".contest/agent_registry.yaml", {"instances": records})
        dispatches = self.fixture.control["dispatch_records"]
        source = self.fixture.put(".contest/human_message.json", {
            "role": "user", "message_id": "human-start", "content": "Execute the scoped fixture",
            "task_ids": [d["task_id"] for d in dispatches], "roles": list(checker.ROUTES),
            "created_at": "2026-10-15T23:00:00+08:00"})
        for dispatch in dispatches:
            path = dispatch["task_card"]
            card = yaml.safe_load((self.root / path).read_text(encoding="utf-8"))
            card["authorization"] = {"source": source, "message_id": "human-start"}
            dispatch["task_card_sha256"] = self.fixture.put(path, card)["sha256"]
        self.fixture.save()

        # Refresh the fixture's dependency references from leaves to review/control files.
        def refresh(value):
            if isinstance(value, list):
                return [refresh(item) for item in value]
            if not isinstance(value, dict):
                return value
            result = {key: refresh(item) for key, item in value.items()}
            if isinstance(result.get("path"), str) and "sha256" in result:
                path = self.root / result["path"]
                if path.is_file():
                    result["sha256"] = checker._digest(path)
            for key in result:
                if key.endswith("_sha256") and isinstance(result.get(key[:-7]), str):
                    path = self.root / result[key[:-7]]
                    if path.is_file():
                        result[key] = checker._digest(path)
            if isinstance(result.get("artifact_digests"), dict):
                result["artifact_digests"] = {path: checker._digest(self.root / path)
                                              for path in result["artifact_digests"]}
            return result

        for _ in range(10):
            changed = False
            for path in self.root.rglob("*.yaml"):
                value = yaml.safe_load(path.read_text(encoding="utf-8"))
                updated = refresh(value)
                if value != updated:
                    path.write_text(yaml.safe_dump(updated, allow_unicode=True, sort_keys=False), encoding="utf-8")
                    changed = True
            if not changed:
                break
        result = checker.check(self.root, through="M5")
        self.assertEqual(result["status"], "PASS", result)
        # A stale final paper copy is found by the normal checker, not only a unit helper.
        (self.root / "paper/figures/FIG7.svg").write_text("<svg>outdated</svg>", encoding="utf-8")
        result = checker.check(self.root, through="M5")
        self.assertEqual(result["status"], "BLOCK", result)
        self.assertTrue(any("FIG7" in error for error in result["failures"]), result)


if __name__ == "__main__":
    unittest.main()
