import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts" / "check_harness_control.py"
AGENT_NODES = ("H1", "H5", "H6", "H7", "H8")
MATERIAL_FIELDS = (
    "problem_mapping", "assumptions", "symbols", "derivation",
    "algorithm_and_parameters", "quantified_results", "validation",
    "figures_or_tables", "literature_use", "conclusion_and_boundary",
)


def load_checker():
    spec = importlib.util.spec_from_file_location("check_harness_control", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def source_ref(root: Path, relative: str, content: str = "frozen evidence\n") -> dict:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"path": relative, "sha256": sha256(path)}


def build_ready_harness(root: Path, checker) -> tuple[dict, dict]:
    control = checker.default_control()
    control["problem_scope"] = {"subproblems": ["Q1"]}
    control["solver_instance_id"] = "solver-001"
    control["dispatch_records"] = []
    control["bootstrap"]["invocations"] = [{
        "skill": "superpowers:using-superpowers",
        "task_id": "H0-bootstrap",
        "completed": True,
    }]

    card_paths: dict[str, str] = {}
    runtime_by_node = {
        "H1": ("gpt-5.6-terra", "medium"),
        "H5": ("gpt-5.6-sol", "high"),
        "H6": ("gpt-5.6-sol", "high"),
        "H7": ("gpt-5.6-terra", "medium"),
        "H8": ("gpt-5.6-sol", "high"),
    }
    for node_id in AGENT_NODES:
        input_ref = source_ref(root, f"inputs/{node_id}.md")
        card = {
            "task_id": f"{node_id}-task-001",
            "node_id": node_id,
            "owner_role": control["nodes"][node_id]["owner_role"],
            "objective": "controlled node task",
            "inputs": [input_ref],
            "scope": "authorized scope",
            "required_outputs": ["node artifact"],
            "verification": ["node check"],
            "prohibited_actions": ["out-of-scope action"],
            "evidence_handoff": ["verifiable handoff"],
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
            control["nodes"][node_id]["solver_instance_id"] = "solver-001"
        card_path = root / ".contest" / "task_cards" / f"{node_id}.yaml"
        write_yaml(card_path, card)
        relative = f".contest/task_cards/{node_id}.yaml"
        card_paths[node_id] = relative
        control["nodes"][node_id]["task_card"] = relative
        control["nodes"][node_id]["agent_instance_id"] = f"{node_id.lower()}-agent-001"
        control["nodes"][node_id]["status"] = "approved"
        control["dispatch_records"].append({
            "task_id": card["task_id"],
            "node_id": node_id,
            "owner_role": card["owner_role"],
            "agent_instance_id": control["nodes"][node_id]["agent_instance_id"],
            "model": card["model"],
            "reasoning_effort": card["reasoning_effort"],
            "dispatched_at": "2026-08-31T12:00:00+00:00",
            "task_card_path": relative,
            "task_card_sha256": sha256(card_path),
            "solver_instance_id": "solver-001" if node_id == "H5" else None,
        })

    interface_path = root / ".contest" / "global_interface_check.yaml"
    h6_card_path = root / ".contest" / "task_cards" / "H6.yaml"
    write_yaml(interface_path, {
        "status": "PASS",
        "verified_by": "H6",
        "verification_agent_instance_id": "h6-agent-001",
        "task_card_path": ".contest/task_cards/H6.yaml",
        "task_card_sha256": sha256(h6_card_path),
        "per_subproblem": [
            {"subproblem_id": "Q1", "interface_fields": [
                {"field": "shared_symbols", "unit": "dimensionless", "time_scale": "static",
                 "source_path": "materials/Q1/symbols.md", "comparison_status": "pass"},
                {"field": "units", "unit": "mixed", "time_scale": "static",
                 "source_path": "materials/Q1/symbols.md", "comparison_status": "pass"},
                {"field": "parameters", "unit": "mixed", "time_scale": "static",
                 "source_path": "materials/Q1/algorithm_and_parameters.md", "comparison_status": "pass"},
            ]},
        ],
        "checks": {
            "shared_symbols": True,
            "units": True,
            "data_versions": True,
            "upstream_downstream_fields": True,
            "time_scales": True,
            "parameters": True,
            "cross_question_constraints": True,
            "conclusions": True,
            "provenance": True,
        },
        "issues": [],
    })
    control["nodes"]["H6"]["global_interface_check"] = ".contest/global_interface_check.yaml"

    materials = {
        field: source_ref(root, f"materials/Q1/{field}.md")
        for field in MATERIAL_FIELDS
    }
    # P0-03: 增加 sensitivity_or_robustness 字段
    materials["sensitivity_or_robustness"] = source_ref(root, "materials/Q1/sensitivity_report.yaml")
    readiness_path = root / ".contest" / "paper_material_readiness.yaml"
    readiness = {
        "status": "PASS",
        "prepared_by": "主 agent",
        "verified_by": "H6",
        "verification_agent_instance_id": "h6-agent-001",
        "target_length": {
            "sections": [{
                "section_id": "modeling-and-results",
                "capacity_status": "adequate",
                "material_refs": [materials["derivation"], materials["quantified_results"]],
            }],
        },
        "subproblems": [{"id": "Q1", "materials": materials}],
        "claim_requirements": [
            {"id": "Q1-conclusion", "type": "conclusion"},
            {"id": "Q1-result", "type": "quantified_result"},
            {"id": "Q1-figure", "type": "figure_claim"},
            {"id": "Q1-citation", "type": "citation_use"},
        ],
    }
    write_yaml(readiness_path, readiness)

    coverage_path = root / ".contest" / "paper_claim_coverage.yaml"
    coverage = {
        "status": "PASS",
        "readiness_sha256": sha256(readiness_path),
        "claims": [
            {
                "id": "Q1-conclusion",
                "type": "conclusion",
                "paper_anchor": "Q1 conclusion",
                "evidence_refs": [materials["quantified_results"], materials["validation"]],
            },
            {
                "id": "Q1-result",
                "type": "quantified_result",
                "paper_anchor": "Q1 result",
                "evidence_refs": [materials["quantified_results"]],
            },
            {
                "id": "Q1-figure",
                "type": "figure_claim",
                "paper_anchor": "Figure 1",
                "evidence_refs": [materials["figures_or_tables"], materials["quantified_results"]],
            },
            {
                "id": "Q1-citation",
                "type": "citation_use",
                "paper_anchor": "Method basis",
                "evidence_refs": [materials["literature_use"]],
            },
        ],
    }
    write_yaml(coverage_path, coverage)
    # P1-05: 创建论文源文件，用于核对 paper_anchor 实际存在性
    paper_source_path = root / "paper.tex"
    paper_source_path.write_text(
        "\\documentclass{article}\n\\begin{document}\n"
        "Q1 conclusion\nQ1 result\nFigure 1\nMethod basis\n"
        "\\end{document}\n", encoding="utf-8")
    control["nodes"]["H8"].update({
        "paper_material_readiness": ".contest/paper_material_readiness.yaml",
        "paper_claim_coverage": ".contest/paper_claim_coverage.yaml",
        "paper_source": "paper.tex",
        "paper_source_sha256": sha256(paper_source_path),
        "writing_started": False,
    })

    approval_log = {"approvals": []}
    for node_id in ("H2", "H3", "H5", "H6", "H7", "H8"):  # H4已并入H5，跳过
        packet_path = root / ".contest" / "reviews" / f"{node_id}.yaml"
        artifacts = []
        if node_id == "H6":
            artifacts = [{"path": ".contest/global_interface_check.yaml", "sha256": sha256(interface_path)}]
        elif node_id == "H7":
            artifacts = [materials["figures_or_tables"]]
        write_yaml(packet_path, {
            "node_id": node_id,
            "summary": f"{node_id} review",
            "important_artifacts": artifacts,
            "checks": ["contract check"],
            "requested_decision": "approve",
            "proposed_next_node": "H9" if node_id == "H8" else f"H{int(node_id[1:]) + 1}",
        })
        relative = f".contest/reviews/{node_id}.yaml"
        control["nodes"][node_id]["review_packet"] = relative
        approval_log["approvals"].append({
            "gate": node_id,
            "decision": "approved",
            "artifact_digests": {relative: sha256(packet_path)},
        })
    write_yaml(root / ".contest" / "approval_log.yaml", approval_log)
    write_yaml(root / ".contest" / "harness_control.yaml", control)
    return control, {"readiness": readiness_path, "coverage": coverage_path, "interface": interface_path, "materials": materials}


def add_h5_dispatch(root: Path, control: dict, task_id: str, agent_instance_id: str,
                    dispatch_kind: str, solver_instance_id: str | None = None,
                    authority: dict | None = None) -> None:
    input_ref = source_ref(root, f"inputs/{task_id}.md")
    card = {
        "task_id": task_id,
        "node_id": "H5",
        "owner_role": "解题 agent" if dispatch_kind == "primary_solver" else "辅助 agent",
        "objective": "controlled H5 task",
        "inputs": [input_ref],
        "scope": "authorized local computation",
        "required_outputs": ["verifiable evidence"],
        "verification": ["node check"],
        "prohibited_actions": ["out-of-scope action"],
        "evidence_handoff": ["verifiable handoff"],
        "model": "gpt-5.6-sol",
        "reasoning_effort": "high",
        "dispatch_kind": dispatch_kind,
        "authority": authority or {
            "may_change_model_route": False,
            "may_write_final_results": dispatch_kind == "primary_solver",
            "may_aggregate_conclusions": dispatch_kind == "primary_solver",
        },
    }
    if dispatch_kind == "primary_solver":
        card["solver_instance_id"] = solver_instance_id
    else:
        card["parent_solver_instance_id"] = "solver-001"
        card["allowed_output_kinds"] = ["local_computation_evidence"]
    relative = f".contest/task_cards/{task_id}.yaml"
    card_path = root / relative
    write_yaml(card_path, card)
    control["dispatch_records"].append({
        "task_id": task_id,
        "node_id": "H5",
        "owner_role": card["owner_role"],
        "agent_instance_id": agent_instance_id,
        "model": card["model"],
        "reasoning_effort": card["reasoning_effort"],
        "dispatched_at": "2026-08-31T12:01:00+00:00",
        "task_card_path": relative,
        "task_card_sha256": sha256(card_path),
        "solver_instance_id": solver_instance_id,
    })


class HarnessHardeningTests(unittest.TestCase):
    def test_primary_solver_must_cover_every_registered_subproblem(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, _ = build_ready_harness(root, checker)
            control["problem_scope"]["subproblems"].append("Q2")
            write_yaml(root / ".contest" / "harness_control.yaml", control)
            report = checker.check_harness_control(root, through="H8")
            self.assertEqual(report["status"], "BLOCK")

    def test_single_primary_solver_is_required(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, _ = build_ready_harness(root, checker)
            add_h5_dispatch(root, control, "H5-task-002", "solver-002", "primary_solver", "solver-002")
            write_yaml(root / ".contest" / "harness_control.yaml", control)
            report = checker.check_harness_control(root, through="H8")
            self.assertEqual(report["status"], "BLOCK")

    def test_dispatch_records_cannot_introduce_another_solver_instance(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, _ = build_ready_harness(root, checker)
            next(record for record in control["dispatch_records"] if record["node_id"] == "H6")["solver_instance_id"] = "solver-002"
            write_yaml(root / ".contest" / "harness_control.yaml", control)
            report = checker.check_harness_control(root, through="H8")
            self.assertEqual(report["status"], "BLOCK")

    def test_support_agent_cannot_claim_solver_authority(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, _ = build_ready_harness(root, checker)
            add_h5_dispatch(root, control, "H5-support-001", "support-001", "conditional_support", None, {
                "may_change_model_route": False,
                "may_write_final_results": False,
                "may_aggregate_conclusions": True,
            })
            write_yaml(root / ".contest" / "harness_control.yaml", control)
            report = checker.check_harness_control(root, through="H8")
            self.assertEqual(report["status"], "BLOCK")

    def test_missing_material_keeps_readiness_paused(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, paths = build_ready_harness(root, checker)
            readiness = yaml.safe_load(paths["readiness"].read_text(encoding="utf-8"))
            readiness["status"] = "PAUSE"
            readiness["subproblems"][0]["materials"].pop("derivation")
            write_yaml(paths["readiness"], readiness)
            coverage = yaml.safe_load(paths["coverage"].read_text(encoding="utf-8"))
            coverage["readiness_sha256"] = sha256(paths["readiness"])
            write_yaml(paths["coverage"], coverage)
            write_yaml(root / ".contest" / "harness_control.yaml", control)
            report = checker.check_harness_control(root, through="H8")
            self.assertEqual(report["status"], "PAUSE")

    def test_gap_matrix_must_cover_every_detected_gap(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, paths = build_ready_harness(root, checker)
            readiness = yaml.safe_load(paths["readiness"].read_text(encoding="utf-8"))
            readiness["status"] = "PAUSE"
            readiness["subproblems"][0]["materials"].pop("derivation")
            readiness["subproblems"][0]["materials"].pop("validation")
            write_yaml(paths["readiness"], readiness)
            matrix_path = root / ".contest" / "evidence_gap_matrix.yaml"
            write_yaml(matrix_path, {
                "readiness_sha256": sha256(paths["readiness"]),
                "gaps": [{
                    "gap_id": "GAP-001",
                    "subproblem_id": "Q1", "requirement": "derivation", "responsible_node": "H5",
                    "required_artifact": "derivation evidence", "acceptance_criteria": "auditable derivation", "return_to": "H5",
                }],
            })
            control["nodes"]["H8"]["evidence_gap_matrix"] = ".contest/evidence_gap_matrix.yaml"
            write_yaml(root / ".contest" / "harness_control.yaml", control)
            report = checker.check_harness_control(root, through="H8")
            self.assertEqual(report["status"], "BLOCK")

    def test_writing_cannot_start_before_material_admission(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, paths = build_ready_harness(root, checker)
            readiness = yaml.safe_load(paths["readiness"].read_text(encoding="utf-8"))
            readiness["status"] = "PAUSE"
            write_yaml(paths["readiness"], readiness)
            control["nodes"]["H8"]["writing_started"] = True
            write_yaml(root / ".contest" / "harness_control.yaml", control)
            report = checker.check_harness_control(root, through="H8")
            self.assertEqual(report["status"], "BLOCK")

    def test_interface_inconsistency_pauses_harness(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, paths = build_ready_harness(root, checker)
            interface = yaml.safe_load(paths["interface"].read_text(encoding="utf-8"))
            interface["status"] = "PAUSE"
            interface["checks"]["units"] = False
            interface["issues"] = ["Q1 to Q2 unit mismatch"]
            write_yaml(paths["interface"], interface)
            write_yaml(root / ".contest" / "harness_control.yaml", control)
            report = checker.check_harness_control(root, through="H8")
            self.assertEqual(report["status"], "PAUSE")

    def test_dispatch_record_must_match_task_card_and_route(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, _ = build_ready_harness(root, checker)
            control["dispatch_records"][0]["model"] = "gpt-5.6-sol"
            write_yaml(root / ".contest" / "harness_control.yaml", control)
            report = checker.check_harness_control(root, through="H8")
            self.assertEqual(report["status"], "BLOCK")

    def test_paper_claim_without_evidence_mapping_blocks_h8(self):
        checker = load_checker()
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control, paths = build_ready_harness(root, checker)
            coverage = yaml.safe_load(paths["coverage"].read_text(encoding="utf-8"))
            coverage["claims"][0]["evidence_refs"] = []
            write_yaml(paths["coverage"], coverage)
            write_yaml(root / ".contest" / "harness_control.yaml", control)
            report = checker.check_harness_control(root, through="H8")
            self.assertEqual(report["status"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
