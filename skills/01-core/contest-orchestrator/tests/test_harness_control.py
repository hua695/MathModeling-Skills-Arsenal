import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts" / "check_harness_control.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_harness_control", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class HarnessControlTests(unittest.TestCase):
    def test_h8_evidence_gap_blocks_progress_and_routes_to_material_nodes(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control = root / ".contest" / "harness_control.yaml"
            control.parent.mkdir(parents=True)
            (root / "problem_statement.md").write_text("题面预载", encoding="utf-8")
            (root / "original_problem.pdf").write_bytes("原始题面内容".encode("utf-8"))
            payload = checker.default_control()
            payload["problem_scope"] = {"subproblems": ["Q1"]}
            payload["solver_instance_id"] = "solver-001"
            payload["nodes"]["H3"]["status"] = "approved"
            payload["harness_run_id"] = "run-20260831-001"
            runtime_by_node = {
                "H1": ("gpt-5.6-terra", "medium"),
                "H5": ("gpt-5.6-sol", "high"),
                "H6": ("gpt-5.6-sol", "high"),
                "H7": ("gpt-5.6-terra", "medium"),
                "H8": ("gpt-5.6-sol", "high"),
            }
            payload["bootstrap"]["invocations"] = [
                {"skill": "superpowers:using-superpowers", "task_id": "H0-bootstrap", "purpose": "bootstrap",
                 "completed": True, "status": "completed", "created": ["H1"], "agent_ids": {"H1": "H1-agent-01"}},
                {"skill": "superpowers:using-superpowers", "task_id": "sp-spawn-001", "purpose": "spawn_roles",
                 "completed": True, "status": "completed", "after_node": "H1",
                 "created": ["H5", "H6", "H7", "H8"],
                 "agent_ids": {"H5": "H5-agent-01", "H6": "H6-agent-01", "H7": "H7-agent-01", "H8": "H8-agent-01"}},
            ]
            cards = root / ".contest" / "task_cards"
            cards.mkdir(parents=True)
            (root / "problem_statement.md").write_text("题面预载", encoding="utf-8")
            (root / "unified_problem_package.yaml").write_text("subproblems: [Q1]", encoding="utf-8")
            for node_id in ("H1", "H5", "H6", "H7", "H8"):
                input_file = root / f"{node_id}_input.md"
                input_file.write_text("frozen input\n", encoding="utf-8")
                payload["nodes"][node_id]["task_card"] = f".contest/task_cards/{node_id}.yaml"
                payload["nodes"][node_id]["agent_instance_id"] = f"{node_id}-agent-01"
                payload["nodes"][node_id]["status"] = "approved"
                if node_id == "H1":
                    payload["nodes"][node_id]["problem_statement"] = "problem_statement.md"
                    payload["nodes"][node_id]["unified_problem_package"] = "unified_problem_package.yaml"
                    payload["nodes"][node_id]["original_problem_file"] = "original_problem.pdf"
                    payload["nodes"][node_id]["original_problem_sha256"] = sha256(root / "original_problem.pdf")
                card = {
                    "task_id": f"{node_id}-task-001", "node_id": node_id,
                    "owner_role": payload["nodes"][node_id]["owner_role"], "objective": "节点任务",
                    "inputs": [{"path": input_file.name, "sha256": sha256(input_file)}],
                    "scope": "受控范围", "required_outputs": ["节点产物"],
                    "verification": ["节点检查"], "prohibited_actions": ["越权"],
                    "evidence_handoff": ["回流记录"],
                    "model": runtime_by_node[node_id][0],
                    "reasoning_effort": runtime_by_node[node_id][1],
                }
                if node_id == "H5":
                    card.update({
                        "dispatch_kind": "primary_solver",
                        "solver_instance_id": "solver-001",
                        "covered_subproblems": ["Q1"],
                        "cross_question_interface": True,
                        "authority": {
                            "may_change_model_route": False,
                            "may_write_final_results": True,
                            "may_aggregate_conclusions": True,
                        },
                    })
                    payload["nodes"][node_id]["solver_instance_id"] = "solver-001"
                card_path = cards / f"{node_id}.yaml"
                card_path.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
                payload["dispatch_records"].append({
                    "task_id": card["task_id"], "node_id": node_id, "owner_role": card["owner_role"],
                    "agent_instance_id": payload["nodes"][node_id]["agent_instance_id"],
                    "model": card["model"], "reasoning_effort": card["reasoning_effort"],
                    "dispatched_at": "2026-08-31T12:00:00+00:00",
                    "task_card_path": f".contest/task_cards/{node_id}.yaml",
                    "task_card_sha256": sha256(card_path),
                    "solver_instance_id": "solver-001" if node_id == "H5" else None,
                    "harness_run_id": "run-20260831-001",
                    "spawn_receipt": {
                        "task_id": card["task_id"],
                        "agent_instance_id": payload["nodes"][node_id]["agent_instance_id"],
                        "task_card_sha256": sha256(card_path),
                        "model": card["model"],
                        "reasoning_effort": card["reasoning_effort"],
                        "spawned_at": "2026-08-31T12:00:01+00:00",
                    },
                })
            payload["agent_instances"] = {
                "H1": {"agent_instance_id": "H1-agent-01", "preloaded": ["problem_statement.md"]},
                "H5": {"agent_instance_id": "H5-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h5_solver_warmup.md"]},
                "H6": {"agent_instance_id": "H6-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h6_verifier_warmup.md"]},
                "H7": {"agent_instance_id": "H7-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h7_figure_warmup.md"]},
                "H8": {"agent_instance_id": "H8-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h8_writer_warmup.md", "references/h8_writer_first_protocol.md", "references/model_summary_protocol.md"]},
            }
            interface_path = root / ".contest" / "global_interface_check.yaml"
            h6_card_path = cards / "H6.yaml"
            interface_path.write_text(yaml.safe_dump({
                "status": "PASS", "issues": [], "checks": {
                    "shared_symbols": True, "units": True, "data_versions": True,
                    "upstream_downstream_fields": True, "time_scales": True, "parameters": True,
                    "cross_question_constraints": True, "conclusions": True, "provenance": True,
                },
                "verified_by": "H6",
                "verification_agent_instance_id": "H6-agent-01",
                "task_card_path": ".contest/task_cards/H6.yaml",
                "task_card_sha256": sha256(h6_card_path),
                "per_subproblem": [
                    {"subproblem_id": "Q1", "interface_fields": [
                        {"field": "shared_symbols", "unit": "dimensionless", "time_scale": "static", "comparison_status": "pass"},
                        {"field": "units", "unit": "mixed", "time_scale": "static", "comparison_status": "pass"},
                        {"field": "parameters", "unit": "mixed", "time_scale": "static", "comparison_status": "pass"},
                    ]},
                ],
            }, allow_unicode=True, sort_keys=False), encoding="utf-8")
            payload["nodes"]["H6"]["global_interface_check"] = ".contest/global_interface_check.yaml"
            payload["nodes"]["H8"]["outcome"] = "evidence_gap"
            payload["nodes"]["H8"]["return_to"] = "H6"
            control.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

            report = checker.check_harness_control(root, through="H8")
            self.assertEqual(report["status"], "PAUSE")
            self.assertIn("H8", report["evidence_gaps"])
            self.assertIn("H6", report["return_nodes"])

    def test_h2_through_h9_need_review_packet_and_matching_user_approval(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control = root / ".contest" / "harness_control.yaml"
            reviews = root / ".contest" / "reviews"
            reviews.mkdir(parents=True)
            (root / "problem_statement.md").write_text("题面预载", encoding="utf-8")
            (root / "unified_problem_package.yaml").write_text("subproblems: [Q1]", encoding="utf-8")
            (root / "original_problem.pdf").write_bytes("原始题面内容".encode("utf-8"))
            payload = checker.default_control()
            payload["problem_scope"] = {"subproblems": ["Q1"]}
            payload["solver_instance_id"] = "solver-001"
            runtime_by_node = {
                "H1": ("gpt-5.6-terra", "medium"),
                "H5": ("gpt-5.6-sol", "high"),
                "H6": ("gpt-5.6-sol", "high"),
                "H7": ("gpt-5.6-terra", "medium"),
                "H8": ("gpt-5.6-sol", "high"),
            }
            payload["bootstrap"]["invocations"] = [
                {"skill": "superpowers:using-superpowers", "task_id": "H0-bootstrap", "purpose": "bootstrap",
                 "completed": True, "status": "completed", "created": ["H1"], "agent_ids": {"H1": "H1-agent-01"}},
                {"skill": "superpowers:using-superpowers", "task_id": "sp-spawn-001", "purpose": "spawn_roles",
                 "completed": True, "status": "completed", "after_node": "H1",
                 "created": ["H5", "H6", "H7", "H8"],
                 "agent_ids": {"H5": "H5-agent-01", "H6": "H6-agent-01", "H7": "H7-agent-01", "H8": "H8-agent-01"}},
            ]
            cards = root / ".contest" / "task_cards"
            cards.mkdir(parents=True)
            (root / "problem_statement.md").write_text("题面预载", encoding="utf-8")
            (root / "unified_problem_package.yaml").write_text("subproblems: [Q1]", encoding="utf-8")
            for node_id in ("H1", "H5", "H6", "H7", "H8"):
                input_file = root / f"{node_id}_input.md"
                input_file.write_text("frozen input\n", encoding="utf-8")
                payload["nodes"][node_id]["task_card"] = f".contest/task_cards/{node_id}.yaml"
                payload["nodes"][node_id]["agent_instance_id"] = f"{node_id}-agent-01"
                payload["nodes"][node_id]["status"] = "approved"
                if node_id == "H1":
                    payload["nodes"][node_id]["problem_statement"] = "problem_statement.md"
                    payload["nodes"][node_id]["unified_problem_package"] = "unified_problem_package.yaml"
                    payload["nodes"][node_id]["original_problem_file"] = "original_problem.pdf"
                    payload["nodes"][node_id]["original_problem_sha256"] = sha256(root / "original_problem.pdf")
                card = {
                    "task_id": f"{node_id}-task-001", "node_id": node_id,
                    "owner_role": payload["nodes"][node_id]["owner_role"], "objective": "节点任务",
                    "inputs": [{"path": input_file.name, "sha256": sha256(input_file)}],
                    "scope": "受控范围", "required_outputs": ["节点产物"],
                    "verification": ["节点检查"], "prohibited_actions": ["越权"],
                    "evidence_handoff": ["回流记录"],
                    "model": runtime_by_node[node_id][0],
                    "reasoning_effort": runtime_by_node[node_id][1],
                }
                if node_id == "H5":
                    card.update({
                        "dispatch_kind": "primary_solver",
                        "solver_instance_id": "solver-001",
                        "covered_subproblems": ["Q1"],
                        "cross_question_interface": True,
                        "authority": {
                            "may_change_model_route": False,
                            "may_write_final_results": True,
                            "may_aggregate_conclusions": True,
                        },
                    })
                    payload["nodes"][node_id]["solver_instance_id"] = "solver-001"
                card_path = cards / f"{node_id}.yaml"
                card_path.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
                payload["dispatch_records"].append({
                    "task_id": card["task_id"], "node_id": node_id, "owner_role": card["owner_role"],
                    "agent_instance_id": payload["nodes"][node_id]["agent_instance_id"],
                    "model": card["model"], "reasoning_effort": card["reasoning_effort"],
                    "dispatched_at": "2026-08-31T12:00:00+00:00",
                    "task_card_path": f".contest/task_cards/{node_id}.yaml",
                    "task_card_sha256": sha256(card_path),
                    "solver_instance_id": "solver-001" if node_id == "H5" else None,
                    "harness_run_id": "run-20260831-001",
                    "spawn_receipt": {
                        "task_id": card["task_id"],
                        "agent_instance_id": payload["nodes"][node_id]["agent_instance_id"],
                        "task_card_sha256": sha256(card_path),
                        "model": card["model"],
                        "reasoning_effort": card["reasoning_effort"],
                        "spawned_at": "2026-08-31T12:00:01+00:00",
                    },
                })
            payload["agent_instances"] = {
                "H1": {"agent_instance_id": "H1-agent-01", "preloaded": ["problem_statement.md"]},
                "H5": {"agent_instance_id": "H5-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h5_solver_warmup.md"]},
                "H6": {"agent_instance_id": "H6-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h6_verifier_warmup.md"]},
                "H7": {"agent_instance_id": "H7-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h7_figure_warmup.md"]},
                "H8": {"agent_instance_id": "H8-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h8_writer_warmup.md", "references/h8_writer_first_protocol.md", "references/model_summary_protocol.md"]},
            }
            # P1-01: 创建状态转移历史
            status_history = root / ".contest" / "status_history.yaml"
            transitions = []
            base_time = "2026-08-31T11:"
            for i, node_id in enumerate(("H1", "H5", "H6", "H7", "H8")):
                transitions.extend([
                    {"node_id": node_id, "from_status": "not_started", "to_status": "draft",
                     "timestamp": f"{base_time}{i*10:02d}:00+00:00", "executor": f"{node_id}-agent-01"},
                    {"node_id": node_id, "from_status": "draft", "to_status": "review_pending",
                     "timestamp": f"{base_time}{i*10+1:02d}:00+00:00", "executor": f"{node_id}-agent-01"},
                    {"node_id": node_id, "from_status": "review_pending", "to_status": "approved",
                     "timestamp": f"{base_time}{i*10+2:02d}:00+00:00", "executor": "user"},
                ])
            status_history.write_text(yaml.safe_dump({"transitions": transitions}, allow_unicode=True, sort_keys=False), encoding="utf-8")
            control.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

            blocked = checker.check_harness_control(root, through="H2")
            self.assertEqual(blocked["status"], "PAUSE")
            self.assertTrue(any("H2" in item for item in blocked["missing"]))

            packet = reviews / "H2_review_packet.yaml"
            packet.write_text(yaml.safe_dump({
                "node_id": "H2",
                "summary": "规格冻结审查包",
                "important_artifacts": [],
                "checks": ["规格完整性"],
                "requested_decision": "approve",
                "proposed_next_node": "H3",
            }, allow_unicode=True, sort_keys=False), encoding="utf-8")
            log = root / ".contest" / "approval_log.yaml"
            log.write_text(yaml.safe_dump({"approvals": [{
                "gate": "H2", "decision": "approved",
                "artifact_digests": {".contest/reviews/H2_review_packet.yaml": sha256(packet)},
            }]}, allow_unicode=True, sort_keys=False), encoding="utf-8")
            payload["nodes"]["H2"]["review_packet"] = ".contest/reviews/H2_review_packet.yaml"
            control.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")

            passed = checker.check_harness_control(root, through="H2")
            self.assertEqual(passed["status"], "PASS", passed)
            (root / "H1_input.md").write_text("changed input\n", encoding="utf-8")
            stale = checker.check_harness_control(root, through="H2")
            self.assertEqual(stale["status"], "PAUSE")
            self.assertTrue(any("H1" in item and "哈希" in item for item in stale["missing"]))

            h1_input = root / "H1_input.md"
            h1_input.write_text("frozen input\n", encoding="utf-8")
            h1_card = cards / "H1.yaml"
            h1_payload = yaml.safe_load(h1_card.read_text(encoding="utf-8"))
            h1_payload["inputs"][0]["sha256"] = sha256(h1_input)
            h1_payload["model"] = "gpt-5.6-sol"
            h1_card.write_text(yaml.safe_dump(h1_payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
            mismatched = checker.check_harness_control(root, through="H2")
            self.assertEqual(mismatched["status"], "BLOCK")
            self.assertTrue(any("H1" in item and "模型路由" in item for item in mismatched["failures"]))

    def test_h0_invocation_with_failed_status_blocks(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".contest").mkdir()
            control = checker.default_control()
            control["bootstrap"]["invocations"] = [
                {"skill": "superpowers:using-superpowers", "task_id": "t1",
                 "purpose": "bootstrap", "completed": True, "status": "failed",
                 "created": ["H1"], "agent_ids": {"H1": "h1-agent"}}
            ]
            (root / ".contest" / "harness_control.yaml").write_text(
                yaml.safe_dump(control, allow_unicode=True), encoding="utf-8")
            result = checker.check_harness_control(root, through="H0")
            self.assertTrue(any("缺少 superpowers" in item for item in result["missing"]))

    def test_unknown_claim_type_blocks(self):
        checker = load_checker()
        failures: list[str] = []
        missing: list[str] = []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            readiness = {"claim_requirements": [{"id": "c1", "type": "made_up_type"}]}
            readiness_path = root / "readiness.yaml"
            readiness_path.write_text(yaml.safe_dump(readiness), encoding="utf-8")
            coverage = {"status": "PASS", "readiness_sha256": sha256(readiness_path),
                        "claims": [{"id": "c1", "type": "made_up_type", "paper_anchor": "sec1",
                                    "evidence_refs": [{"path": "r.yaml", "sha256": "a" * 64}]}]}
            coverage_path = root / "paper_claim_coverage.yaml"
            coverage_path.write_text(yaml.safe_dump(coverage), encoding="utf-8")
            node = {"paper_claim_coverage": "paper_claim_coverage.yaml"}
            checker._validate_claim_coverage(root, node, readiness_path, {}, readiness, missing, failures)
        self.assertTrue(any("未知主张类型" in item for item in failures))


class HarnessSpawnConstraintsTests(unittest.TestCase):
    """H1 后一次性创建全部固定角色 + superpowers 调用溯源硬约束。"""

    def _agent_ids(self):
        return {"H1": "H1-agent-01", "H5": "H5-agent-01", "H6": "H6-agent-01",
                "H7": "H7-agent-01", "H8": "H8-agent-01"}

    def _instances(self, overrides=None):
        instances = {
            "H1": {"agent_instance_id": "H1-agent-01", "preloaded": ["problem_statement.md"]},
            "H5": {"agent_instance_id": "H5-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h5_solver_warmup.md"]},
            "H6": {"agent_instance_id": "H6-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h6_verifier_warmup.md"]},
            "H7": {"agent_instance_id": "H7-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h7_figure_warmup.md"]},
            "H8": {"agent_instance_id": "H8-agent-01", "preloaded": ["problem_statement.md", "references/warmup/h8_writer_warmup.md", "references/h8_writer_first_protocol.md", "references/model_summary_protocol.md"]},
        }
        if overrides:
            for role, patch in overrides.items():
                instances[role].update(patch)
        return instances

    def test_spawn_roles_invocation_must_cover_all_roles(self):
        checker = load_checker()
        failures, missing = [], []
        control = {"bootstrap": {"invocations": [
            {"task_id": "t1", "purpose": "spawn_roles", "status": "completed", "created": ["H5"]},
        ]}}
        checker._validate_spawn_invocations(control, "H5", missing, failures)
        self.assertTrue(any("覆盖角色" in item for item in missing))

    def test_invocation_without_task_id_is_not_a_call(self):
        checker = load_checker()
        failures, missing = [], []
        control = {"bootstrap": {"invocations": [
            {"purpose": "spawn_roles", "status": "completed", "created": ["H5", "H6", "H7", "H8"],
             "agent_ids": self._agent_ids()},
        ]}}
        checker._validate_spawn_invocations(control, "H5", missing, failures)
        self.assertTrue(any("task_id" in item for item in failures))

    def test_instance_must_trace_to_superpowers_return(self):
        checker = load_checker()
        failures, missing = [], []
        control = {"agent_instances": self._instances(overrides={"H1": {"agent_instance_id": "not-traced"}})}
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "problem_statement.md").write_text("x", encoding="utf-8")
            checker._validate_agent_instances(root, control, "H5", self._agent_ids(), missing, failures)
        self.assertTrue(any("无法溯源" in item for item in failures))

    def test_preloaded_must_contain_problem_statement(self):
        checker = load_checker()
        failures, missing = [], []
        control = {"agent_instances": self._instances(overrides={"H1": {"preloaded": ["other.md"]}})}
        with tempfile.TemporaryDirectory() as raw:
            checker._validate_agent_instances(Path(raw), control, "H5", self._agent_ids(), missing, failures)
        self.assertTrue(any("preloaded" in item for item in failures))

    def test_h8_preloaded_must_contain_writer_first_protocol(self):
        checker = load_checker()
        failures, missing = [], []
        control = {"agent_instances": self._instances(overrides={
            "H8": {"preloaded": ["problem_statement.md", "references/warmup/h8_writer_warmup.md"]}
        })}
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "problem_statement.md").write_text("x", encoding="utf-8")
            checker._validate_agent_instances(root, control, "H5", self._agent_ids(), missing, failures)
        self.assertTrue(any("writer_first_protocol" in item for item in failures))

    def test_h6_must_differ_from_h5(self):
        checker = load_checker()
        failures, missing = [], []
        agent_ids = self._agent_ids()
        agent_ids["H6"] = "same-as-h5"
        control = {"agent_instances": self._instances(
            overrides={"H5": {"agent_instance_id": "same-as-h5"}, "H6": {"agent_instance_id": "same-as-h5"}})}
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "problem_statement.md").write_text("x", encoding="utf-8")
            checker._validate_agent_instances(root, control, "H5", agent_ids, missing, failures)
        self.assertTrue(any("H6" in item and "不同" in item for item in failures))

    def test_legal_instances_pass_without_noise(self):
        checker = load_checker()
        failures, missing = [], []
        control = {"agent_instances": self._instances()}
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "problem_statement.md").write_text("x", encoding="utf-8")
            checker._validate_agent_instances(root, control, "H5", self._agent_ids(), missing, failures)
        self.assertEqual(failures, [])
        self.assertEqual(missing, [])

    def test_reflow_reuses_instance_without_new_registration(self):
        # 回流复用同一实例：agent_instances 不变、dispatch_records 新增派发记录，实例注册校验不误报
        checker = load_checker()
        failures, missing = [], []
        control = {"agent_instances": self._instances()}
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "problem_statement.md").write_text("x", encoding="utf-8")
            checker._validate_agent_instances(root, control, "H5", self._agent_ids(), missing, failures)
        self.assertEqual(failures, [])
        self.assertEqual(missing, [])

    def test_narrative_missing_key_result_blocks(self):
        checker = load_checker()
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            narrative = root / "paper_narrative.yaml"
            narrative.write_text(yaml.safe_dump({
                "status": "draft",
                "narrative": {"Q1": {"method": "AHP", "innovation": "x", "problem_solved": "y", "key_result": ""}},
            }, allow_unicode=True, sort_keys=False), encoding="utf-8")
            nodes = {"H5": {"paper_narrative": "paper_narrative.yaml"}}
            checker._validate_narrative(root, nodes, "H6", missing, failures)
        self.assertTrue(any("key_result" in item for item in failures))

    def test_narrative_missing_method_blocks(self):
        checker = load_checker()
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            narrative = root / "paper_narrative.yaml"
            narrative.write_text(yaml.safe_dump({
                "status": "results_filled",
                "narrative": {"Q1": {"method": "", "innovation": "x", "problem_solved": "y", "key_result": "0.87"}},
            }, allow_unicode=True, sort_keys=False), encoding="utf-8")
            nodes = {"H5": {"paper_narrative": "paper_narrative.yaml"}}
            checker._validate_narrative(root, nodes, "H6", missing, failures)
        self.assertTrue(any("method" in item for item in failures))

    def test_narrative_requires_a_global_paper_spine(self):
        checker = load_checker()
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            narrative = root / "paper_narrative.yaml"
            narrative.write_text(yaml.safe_dump({
                "status": "results_filled",
                "narrative": {
                    "global": {"storyline": "问题到模型再到结论", "validation_story": "独立核验"},
                    "Q1": {"method": "AHP", "innovation": "x", "problem_solved": "y", "key_result": "0.87"},
                },
            }, allow_unicode=True, sort_keys=False), encoding="utf-8")
            checker._validate_narrative(
                root, {"H5": {"paper_narrative": "paper_narrative.yaml"}}, "H6", missing, failures,
            )
        self.assertTrue(any("paper_spine" in item for item in failures))

    def test_narrative_requires_an_edge_for_each_adjacent_chapter(self):
        checker = load_checker()
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            narrative = root / "paper_narrative.yaml"
            narrative.write_text(yaml.safe_dump({
                "status": "results_filled",
                "narrative": {
                    "global": {
                        "storyline": "问题到模型再到结论", "validation_story": "独立核验",
                        "paper_spine": {
                            "core_chapters": ["Q1"],
                            "support_chapters": ["problem_analysis"],
                            "chapter_order": ["problem_analysis", "Q1"],
                            "chapter_edges": [],
                        },
                    },
                    "Q1": {"method": "AHP", "innovation": "x", "problem_solved": "y", "key_result": "0.87"},
                },
            }, allow_unicode=True, sort_keys=False), encoding="utf-8")
            checker._validate_narrative(
                root, {"H5": {"paper_narrative": "paper_narrative.yaml"}}, "H6", missing, failures,
            )
        self.assertTrue(any("chapter_edges" in item or "相邻" in item for item in failures))

    def test_validation_contract_empty_blocks(self):
        checker = load_checker()
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract = root / "validation_contract.yaml"
            contract.write_text(yaml.safe_dump({
                "status": "draft", "key_conclusions": [], "interface_values": {},
                "symbol_definitions": [], "self_verified": [],
            }, allow_unicode=True, sort_keys=False), encoding="utf-8")
            nodes = {"H5": {"validation_contract": "validation_contract.yaml"}}
            checker._validate_validation_contract(root, nodes, "H6", missing, failures)
        self.assertTrue(any("key_conclusions" in item for item in failures))

    def test_h8_required_inputs_include_narrative_and_readiness(self):
        checker = load_checker()
        self.assertEqual(
            checker.REQUIRED_INPUT_BY_NODE["H8"],
            [
                "problem_statement.md",
                "paper_narrative.yaml",
                "result_interpretation_cards.yaml",
                "paper_argument_blueprint.yaml",
                "paper_material_readiness.yaml",
                "paper_claim_coverage.yaml",
                "chart_requirements.yaml",
                "visual_argument_plan.yaml",
                "abstract_argument_card.yaml",
            ],
        )

    def test_result_interpretation_card_without_meaning_blocks_h6(self):
        checker = load_checker()
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence = root / "results.yaml"
            evidence.write_text("metric: 0.87\n", encoding="utf-8")
            cards = root / "result_interpretation_cards.yaml"
            cards.write_text(yaml.safe_dump({
                "schema_version": "1.0", "status": "verified", "created_by": "H5",
                "verified_by": "H6", "verification_agent_instance_id": "h6-01",
                "cards": [{
                    "card_id": "Q1-result-01", "subproblem_id": "Q1",
                    "result_statement": "准确率为 0.87", "meaning": "",
                    "reasoning_basis": "与基准组的冻结结果比较",
                    "supported_scope": "给定测试集", "evidence_refs": [{
                        "path": "results.yaml", "sha256": sha256(evidence),
                    }],
                }],
            }, allow_unicode=True, sort_keys=False), encoding="utf-8")
            nodes = {
                "H5": {"result_interpretation_cards": "result_interpretation_cards.yaml"},
                "H6": {"agent_instance_id": "h6-01"},
            }
            checker._validate_result_interpretation_cards(root, nodes, "H6", missing, failures)
        self.assertTrue(any("meaning" in item for item in failures))

    def test_argument_blueprint_without_central_thesis_blocks_h8(self):
        checker = load_checker()
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence = root / "results.yaml"
            evidence.write_text("metric: 0.87\n", encoding="utf-8")
            narrative = root / "paper_narrative.yaml"
            narrative.write_text("status: verified\n", encoding="utf-8")
            cards = root / "result_interpretation_cards.yaml"
            cards.write_text(yaml.safe_dump({"cards": [{"card_id": "Q1-result-01"}]}, allow_unicode=True), encoding="utf-8")
            blueprint = root / "paper_argument_blueprint.yaml"
            reference = {"path": "results.yaml", "sha256": sha256(evidence)}
            blueprint.write_text(yaml.safe_dump({
                "status": "draft", "prepared_by": "academic-writing",
                "narrative_sha256": sha256(narrative), "interpretation_cards_sha256": sha256(cards),
                "global": {"central_thesis": "", "reader_journey": "从问题到结论"},
                "chapters": [{
                    "section_id": "analysis", "reader_question": "问题是什么？", "chapter_answer": "给出范围。",
                    "argument_ids": ["arg-01"], "evidence_refs": [reference], "figure_roles": [], "excluded_material": [],
                }],
                "arguments": [{
                    "argument_id": "arg-01", "subproblem_id": "Q1", "claim": "模型满足约束。",
                    "result_card_id": "Q1-result-01", "why_it_matters": "可用于决策。",
                    "supported_scope": "给定数据", "evidence_refs": [reference],
                }],
            }, allow_unicode=True, sort_keys=False), encoding="utf-8")
            nodes = {
                "H5": {"paper_narrative": "paper_narrative.yaml", "result_interpretation_cards": "result_interpretation_cards.yaml"},
                "H8": {"paper_argument_blueprint": "paper_argument_blueprint.yaml", "writing_started": False},
            }
            checker._validate_argument_blueprint(root, nodes, missing, failures)
        self.assertTrue(any("central_thesis" in item for item in failures))

    def test_h1_missing_unified_problem_package_blocks(self):
        checker = load_checker()
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            ps = root / "problem_statement.md"
            ps.write_text("# 题面\n", encoding="utf-8")
            node = {"status": "draft", "problem_statement": "problem_statement.md"}
            checker._validate_h1_problem_statement(root, node, missing, failures)
        self.assertTrue(any("unified_problem_package" in item for item in missing))


class SkillBindingTests(unittest.TestCase):
    """节点-子 skill 绑定硬约束：能力下沉后绑定子 skill 必须到点调用。"""

    def _check(self, node_id, node):
        checker = load_checker()
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            checker._validate_skill_invocations(root, node_id, node, missing, failures)
        return missing, failures

    def test_not_started_skips_binding(self):
        missing, failures = self._check("H5", {"status": "not_started"})  # H4已并入H5
        self.assertEqual(missing, [])
        self.assertEqual(failures, [])

    def test_missing_skill_invocations_field_blocks(self):
        missing, _ = self._check("H5", {"status": "approved"})  # H4已并入H5
        self.assertTrue(any("skill_invocations" in item for item in missing))

    def test_empty_skill_invocations_blocks(self):
        missing, _ = self._check("H8", {"status": "approved", "skill_invocations": []})
        self.assertTrue(any("skill_invocations 为空" in item for item in missing))

    def test_h5_must_call_selector(self):
        """H5 阶段一必须调用 math-model-selector（H4已并入H5）"""
        missing, _ = self._check(
            "H5", {"status": "approved", "skill_invocations": [{"skill": "pyomo"}]})
        self.assertTrue(any("必调子 skill" in item and "math-model-selector" in item for item in missing))

    def test_h8_must_call_academic_writing(self):
        missing, _ = self._check(
            "H8", {"status": "approved", "skill_invocations": [{"skill": "math-model-selector"}]})
        self.assertTrue(any("必调子 skill" in item and "academic-writing" in item for item in missing))

    def test_h8_must_call_mathmodel_latex_skill(self):
        missing, _ = self._check(
            "H8", {"status": "approved", "skill_invocations": [
                {"skill": "academic-writing", "evidence_ref": "paper/paper.tex"},
            ]})
        self.assertTrue(any("必调子 skill" in item and "mathmodel-latex-skill" in item for item in missing))

    def test_h9_must_call_mathmodel_latex_skill(self):
        missing, _ = self._check(
            "H9", {"status": "approved", "skill_invocations": [
                {"skill": "bzd-review-paper", "evidence_ref": "delivery_report.yaml"},
            ]})
        self.assertTrue(any("必调子 skill" in item and "mathmodel-latex-skill" in item for item in missing))

    def test_h8_h9_latex_binding_cannot_be_marked_not_applicable(self):
        for node_id, supporting_skill in (("H8", "academic-writing"), ("H9", "bzd-review-paper")):
            missing, _ = self._check(
                node_id, {"status": "approved", "skill_invocations": [
                    {"skill": supporting_skill, "evidence_ref": "paper.tex"},
                    {"skill": "mathmodel-latex-skill", "not_applicable": True,
                     "reason": "temporary reason"},
                ]})
            self.assertTrue(
                any("必调子 skill" in item and "mathmodel-latex-skill" in item for item in missing),
                node_id,
            )

    def test_fake_skill_name_blocks(self):
        _, failures = self._check(
            "H5", {"status": "approved", "skill_invocations": [{"skill": "made-up-skill"}]})
        self.assertTrue(any("未登记 skill" in item for item in failures))

    def test_at_least_one_not_called_blocks(self):
        missing, _ = self._check(
            "H5", {"status": "approved", "skill_invocations": [{"skill": "academic-writing"}]})
        self.assertTrue(any("至少调用一个" in item for item in missing))

    def test_h6_missing_verified_by_blocks(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "iface.yaml").write_text(yaml.safe_dump({
                "status": "PASS", "issues": [], "checks": {"shared_symbols": True},
            }), encoding="utf-8")
            nodes = {"H6": {"global_interface_check": "iface.yaml", "agent_instance_id": "h6-01"},
                     "H5": {"agent_instance_id": "h5-01"}}
            failures, missing = [], []
            checker._validate_h6_interface(root, nodes, {}, missing, failures)
        self.assertTrue(any("verified_by" in item for item in failures))

    def test_review_packet_empty_checks_blocks(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "packet.yaml").write_text(yaml.safe_dump({
                "node_id": "H6", "summary": "x", "important_artifacts": ["a.md"],
                "checks": [], "requested_decision": "approve",
            }), encoding="utf-8")
            failures, missing = [], []
            checker._validate_review(root, "H6", {"review_packet": "packet.yaml"},
                                     {"approvals": [{"gate": "H6", "decision": "approved",
                                                      "artifact_digests": {"packet.yaml": "x"}}]},
                                     missing, failures)
        self.assertTrue(any("checks" in item and "空" in item for item in failures))

    def test_body_pages_over_30_blocks(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "readiness.yaml").write_text(yaml.safe_dump({
                "status": "PASS", "prepared_by": "H8", "verified_by": "H6",
                "verification_agent_instance_id": "h6-01",
                "subproblems": [{"id": "Q1", "method": "m", "key_result": "r", "evidence_refs": []}],
                "claim_requirements": [],
                "target_length": {"sections": [
                    {"name": "问题重述", "page_count": 32, "chapter_type": "evidence",
                     "capacity_status": "adequate", "material_refs": []},
                ]},
            }), encoding="utf-8")
            nodes = {"H8": {"paper_material_readiness": "readiness.yaml"},
                     "H6": {"agent_instance_id": "h6-01"}}
            failures, missing = [], []
            checker._validate_paper_materials(root, nodes, {"subproblems": [{"id": "Q1"}]},
                                              missing, failures)
        self.assertTrue(any("正文" in item and "30" in item for item in failures))

    def test_at_least_one_not_applicable_with_reason_passes(self):
        missing, failures = self._check(
            "H5", {"status": "approved", "skill_invocations": [
                {"skill": "data-science-stack", "not_applicable": True, "reason": "纯机理题，无数据链路"}]})
        self.assertFalse(any("至少调用一个" in item for item in missing))
        self.assertEqual(failures, [])

    def test_legal_binding_passes(self):
        checker = load_checker()
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            bp = root / "model_blueprint.yaml"
            bp.write_text("model: baseline\n", encoding="utf-8")
            node = {"status": "approved", "skill_invocations": [
                {"skill": "math-model-selector", "evidence_ref": "model_blueprint.yaml"}]}
            checker._validate_skill_invocations(root, "H5", node, missing, failures)  # H4已并入H5
        self.assertFalse(any("skill_invocations" in item or "必调子 skill" in item for item in missing))
        self.assertEqual(failures, [])

    def test_na_without_reason_blocks(self):
        _, failures = self._check(
            "H5", {"status": "approved", "skill_invocations": [
                {"skill": "data-science-stack", "not_applicable": True}]})
        self.assertTrue(any("not_applicable 必须带 reason" in item for item in failures))

    def test_missing_evidence_ref_blocks(self):
        missing, _ = self._check(
            "H5", {"status": "approved", "skill_invocations": [
                {"skill": "math-model-selector"}]})  # H4已并入H5
        self.assertTrue(any("缺少 evidence_ref" in item for item in missing))

    def test_evidence_ref_nonexistent_file_blocks(self):
        checker = load_checker()
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            node = {"status": "approved", "skill_invocations": [
                {"skill": "math-model-selector", "evidence_ref": "nonexistent.yaml"}]}
            checker._validate_skill_invocations(root, "H5", node, missing, failures)  # H4已并入H5
        self.assertTrue(any("evidence_ref 文件不存在" in item for item in missing))


    def test_figure_kind_generator_mismatch_blocks(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "registry.yaml").write_text(yaml.safe_dump({
                "pipeline_audit": {
                    "scipilot_decision": {"status": "passed"},
                    "modelviz_generation": {"status": "passed"},
                    "scipilot_qa": {"status": "passed"},
                },
                "figures": [{
                    "figure_id": "F1", "kind": "schematic", "generator": "modelviz",
                    "formats": ["svg", "png"], "source": "model_contract.yaml",
                    "qa_status": "reviewed", "insertion_format": "svg", "visual_qa": "passed",
                    "caption_claim": "测试图注", "paper_location": "4.1",
                }],
            }), encoding="utf-8")
            failures, missing = [], []
            checker._validate_h7_figures(root, {"figure_registry": "registry.yaml"}, missing, failures)
        self.assertTrue(any("generator" in item for item in failures))

    def test_figure_data_requires_scipilot_qa_blocks(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "registry.yaml").write_text(yaml.safe_dump({
                "pipeline_audit": {
                    "scipilot_decision": {"status": "passed"},
                    "modelviz_generation": {"status": "passed"},
                    "scipilot_qa": {"status": "passed"},
                },
                "figures": [{
                    "figure_id": "F1", "kind": "data", "generator": "modelviz",
                    "formats": ["svg", "png"], "source": "results/result.json",
                    "qa_status": "reviewed", "insertion_format": "svg", "visual_qa": "passed",
                    "decision_author": "scipilot-figure-skill", "decision_card": "figures/F1.decision.json",
                    "caption_claim": "测试图注", "paper_location": "5.2",
                }],
            }), encoding="utf-8")
            (root / "figures").mkdir(exist_ok=True)
            (root / "figures" / "F1.decision.json").write_text("{}", encoding="utf-8")
            failures, missing = [], []
            checker._validate_h7_figures(root, {"figure_registry": "registry.yaml"}, missing, failures)
        self.assertTrue(any("semantic_qa" in item for item in failures))

    def test_figure_drawio_requires_user_request_blocks(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "registry.yaml").write_text(yaml.safe_dump({
                "pipeline_audit": {
                    "scipilot_decision": {"status": "passed"},
                    "modelviz_generation": {"status": "passed"},
                    "scipilot_qa": {"status": "passed"},
                },
                "figures": [{
                    "figure_id": "F1", "kind": "drawio", "generator": "drawio-diagram",
                    "formats": ["svg", "png"], "source": "model_contract.yaml",
                    "qa_status": "reviewed", "insertion_format": "svg", "visual_qa": "passed",
                    "caption_claim": "测试图注", "paper_location": "6.1",
                }],
            }), encoding="utf-8")
            failures, missing = [], []
            checker._validate_h7_figures(root, {"figure_registry": "registry.yaml"}, missing, failures)
        self.assertTrue(any("user_requested" in item for item in failures))

    def test_spawn_roles_missing_after_node_blocks(self):
        checker = load_checker()
        failures, missing = [], []
        checker._validate_spawn_invocations({
            "bootstrap": {"invocations": [{
                "skill": "superpowers:using-superpowers", "task_id": "sp-1", "purpose": "spawn_roles",
                "completed": True, "status": "completed",
                "created": ["H5", "H6", "H7", "H8"],
                "agent_ids": {"H5": "a", "H6": "b", "H7": "c", "H8": "d"},
            }]},
        }, "H2", missing, failures)
        self.assertTrue(any("after_node" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
