import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_mathorcup_control as checker


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MathorCupFixture:
    def __init__(self, root):
        self.root = root
        self.control = yaml.safe_load((ROOT / "templates" / "mathorcup_control.yaml").read_text(encoding="utf-8"))
        self.log = {"approvals": []}
        self.control["problem_scope"]["subproblems"] = ["Q1"]
        self.source = self.put("inputs/problem.txt", "Predict the target.")
        rules = self.put("inputs/official_rules.txt", "Official rule snapshot")
        profile = self.put("competition_profile.yaml", {"official_rules_source": rules})
        self.control["competition_profile"] = profile
        self.problem = self.put("problem_statement.md", "Problem: predict target from inputs.")
        self.evidence = self.put("evidence/check.txt", "Checked result and source.")
        instances = {}
        for role, (model, effort) in checker.ROUTES.items():
            instances[role] = {
                "agent_instance_id": f"agent-{role}", "model": model,
                "reasoning_effort": effort,
                "preloaded": [self.source if role == "data" else self.problem],
            }
        self.control["agent_instances"] = instances
        self.control["solver_instance_id"] = "agent-solver"

    def put(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        elif isinstance(content, (dict, list)):
            path.write_text(yaml.safe_dump(content, allow_unicode=True, sort_keys=False), encoding="utf-8")
        else:
            path.write_text(content, encoding="utf-8")
        return {"path": relative, "sha256": digest(path)}

    def dispatch(self, node, role, hour, inputs=None, phase=None, chapter_id=None):
        sequence = 1 + sum(record["node_id"] == node and record["owner_role"] == role
                           for record in self.control["dispatch_records"])
        task_id = f"{node}-{role}-{sequence}"
        model, effort = checker.ROUTES[role]
        card = {
            "task_id": task_id, "node_id": node, "owner_role": role,
            "agent_instance_id": f"agent-{role}", "model": model,
            "reasoning_effort": effort, "objective": f"Produce {node} evidence",
            "inputs": inputs or [self.problem],
            "scope": ({"phase": phase or "plan", **({"chapter_id": chapter_id} if chapter_id else {})} if node == "M4" else
                      {"phase": "node-work", "subproblems": ["Q1"],
                       "cross_question_interface": node == "M3" and role == "solver"}),
            "prohibited_actions": ["Do not change the frozen route"],
        }
        ref = self.put(f".contest/task_cards/{task_id}.yaml", card)
        self.control["dispatch_records"].append({
            "task_id": task_id, "node_id": node, "owner_role": role,
            "agent_instance_id": f"agent-{role}", "model": model,
            "reasoning_effort": effort, "called_at": f"2026-10-16T{hour:02d}:00:00+08:00",
            "task_card": ref["path"], "task_card_sha256": ref["sha256"],
        })

    def approval(self, gate, packet_ref, artifacts, hour):
        refs = [packet_ref, *artifacts]
        self.log["approvals"].append({
            "gate": gate, "decision": "approve", "approved_by": "user",
            "approved_at": f"2026-10-16T{hour:02d}:00:00+08:00",
            "artifact_digests": {ref["path"]: ref["sha256"] for ref in refs},
        })

    def review(self, gate, artifacts, hour):
        packet = {
            "node_id": gate.split(":", 1)[0].split("_", 1)[0],
            "summary": f"{gate} evidence",
            "important_artifacts": artifacts,
            "checks": [{"name": "evidence", "status": "PASS",
                        "evidence_ref": self.evidence["path"],
                        "evidence_sha256": self.evidence["sha256"]}],
            "requested_decision": "approve",
        }
        ref = self.put(f".contest/reviews/{gate.replace(':', '_')}.yaml", packet)
        self.approval(gate, ref, artifacts, hour)
        return ref

    def complete(self, node, artifacts, skills, hour):
        record = self.control["nodes"][node]
        record["status"] = "approved"
        record.update(artifacts)
        record["skill_invocations"] = [
            {"skill": skill, "status": "completed", "evidence_ref": self.evidence["path"],
             "evidence_sha256": self.evidence["sha256"]} for skill in skills
        ]
        record["review_packet"] = self.review(node, list(artifacts.values()), hour)

    def m1(self):
        self.dispatch("M1", "data", 0, [self.source])
        self.complete("M1", {
            "problem_statement": self.problem,
            "data_overview": self.put("data_overview.yaml", {"sample_count": 10}),
            "task_kpi": self.put("task_kpi.yaml", {"Q1": "RMSE"}),
            "literature_request": self.put("literature_request.yaml", {"Q1": "Find method and data precedents"}),
        }, ["math-model-selector"], 1)

    def m2(self):
        self.m1()
        self.dispatch("M2", "data", 2)
        self.dispatch("M2", "verifier", 2)
        features = self.put("features.yaml", {"features": ["x"]})
        audit = self.put("leakage_audit.yaml", {
            "status": "PASS", "verification_agent_instance_id": "agent-verifier",
            "dataset_sha256": self.source["sha256"],
            "feature_pipeline_sha256": features["sha256"],
            "split_policy": "group-aware holdout",
            "checks": [{"name": name, "status": "PASS", "evidence_ref": self.evidence["path"],
                        "evidence_sha256": self.evidence["sha256"]} for name in sorted(checker.LEAKAGE_CHECKS)],
        })
        literature_summary = self.put("literature/Q1_summary.md", "Method, data, scope and source location.")
        literature_sources = self.put("literature_sources.yaml", {
            "status": "PASS", "sources": [{
                "citation_key": "study-q1", "subproblems": ["Q1"], "user_supplied": True,
                "locator": "source section 2", "use": "method baseline",
                "summary_ref": literature_summary,
            }],
        })
        self.complete("M2", {
            "eda_report": self.put("eda_report.md", "Data distribution and missingness."),
            "features": features, "leakage_audit": audit,
            "literature_sources": literature_sources,
        }, ["data-science-stack"], 3)

    def m3(self):
        self.m2()
        self.dispatch("M3", "solver", 4)
        self.dispatch("M3", "verifier", 4)
        result = self.put("results/Q1.json", '{"rmse": 0.5}')
        manifest = self.put("run_manifest.yaml", {
            "solver_instance_id": "agent-solver", "seed": 42,
            "command": ["python", "solve.py"],
            "results": [{**result, "subproblem_id": "Q1"}],
        })
        validation = self.put("independent_validation.yaml", {
            "status": "PASS", "verification_agent_instance_id": "agent-verifier",
            "checked_subproblems": ["Q1"],
            "checks": [{"name": name, "status": "PASS", "evidence_ref": self.evidence["path"],
                        "evidence_sha256": self.evidence["sha256"]} for name in sorted(checker.MODEL_CHECKS)],
        })
        self.complete("M3", {
            "run_manifest": manifest,
            "model_summary_cards": self.put("model_summary_cards.yaml", {"Q1": "baseline and model"}),
            "result_interpretation_cards": self.put("result_interpretation_cards.yaml", {"Q1": "RMSE 0.5"}),
            "independent_validation": validation,
        }, ["math-model-selector", "data-science-stack"], 5)
        return result

    def m4(self):
        result = self.m3()
        for role in ("figure", "verifier", "writer"):
            self.dispatch("M4", role, 6, phase="plan" if role != "verifier" else None)
        visual = self.put("visual_argument_plan.yaml", {"slots": [{
            "slot_id": "Q1-performance", "representation": "figure",
            "generation_route": "modelviz", "evidence_refs": [result],
        }]})
        blueprint = self.put("paper_argument_blueprint.yaml", {"spine": "data-to-result"})
        m4 = self.control["nodes"]["M4"]
        m4["visual_argument_plan"] = visual
        m4["paper_argument_blueprint"] = blueprint
        m4["visual_plan_review_packet"] = self.review("M4_VISUAL_PLAN", [visual], 7)
        m4["writing_plan_review_packet"] = self.review("M4_WRITING_PLAN", [blueprint], 7)
        decision = self.put("figures/Q1_decision.yaml", {"chart": "scatter"})
        svg = self.put("figures/Q1.svg", b"<svg></svg>")
        png = self.put("figures/Q1.png", b"PNG fixture")
        registry = self.put("figure_registry.yaml", {"figures": [{
            "figure_id": "fig-Q1", "visual_slot_ids": ["Q1-performance"],
            "generator": "modelviz", "generation_route": "modelviz",
            "formats": ["svg", "png"], "insertion_format": "svg",
            "visual_qa": "passed", "qa_status": "reviewed", "caption": "Figure 1",
            "source_files": [result["path"]], "svg": svg["path"], "svg_sha256": svg["sha256"],
            "png": png["path"], "png_sha256": png["sha256"],
            "decision_author": "scipilot-figure-skill", "semantic_qa": "scipilot-figure-skill",
            "decision_card": decision["path"], "decision_card_sha256": decision["sha256"],
        }]})
        m4["figure_registry"] = registry
        material = self.put("materials/Q1.md", "Task, symbols, data, method, result, validation, figures and literature.")
        matrix = {field: {"status": "ready", **material} for field in checker.MATERIAL_FIELDS}
        readiness = self.put("paper_material_readiness.yaml", {
            "status": "PASS", "verification_agent_instance_id": "agent-verifier",
            "evidence_matrix": {"Q1": matrix},
            "chapters": [{"chapter_id": "results", "capacity": "2 pages", "material_refs": [material]}],
        })
        coverage = self.put("paper_claim_coverage.yaml", {
            "status": "PASS", "readiness_sha256": readiness["sha256"],
            "claims": [{"id": "c1", "paper_anchor": "results", "evidence_refs": [result]}],
        })
        self.dispatch("M4", "figure", 8, [visual, result], phase="generate")
        self.dispatch("M4", "writer", 8, [blueprint, readiness, coverage], phase="write", chapter_id="results")
        pdf = self.put("paper/main.pdf", b"%PDF-1.4\nfixture\n")
        chapter = self.put("paper/results.tex", "\\section{Results} RMSE is 0.5.")
        chapter_review = self.review("M4_CHAPTER:results", [chapter], 9)
        m4["chapters"] = [{"chapter_id": "results", "manuscript": chapter,
                           "review_packet": chapter_review}]
        m4["writing_started"] = True
        self.complete("M4", {
            "visual_argument_plan": visual, "figure_registry": registry,
            "paper_argument_blueprint": blueprint,
            "paper_material_readiness": readiness, "paper_claim_coverage": coverage,
            "paper_pdf": pdf,
        }, ["academic-writing", "mathmodel-latex-skill", "scipilot-figure-skill", "modelviz"], 10)
        return result, pdf

    def m5(self):
        result, pdf = self.m4()
        reproduction = self.put("reproducibility_report.yaml", {
            "status": "PASS", "exit_code": 0, "command": ["python", "solve.py"],
            "result_refs": [result],
        })
        delivery = self.put("delivery_report.yaml", {
            "status": "PASS",
            "checks": {name: {"status": "PASS", "evidence_ref": self.evidence["path"],
                             "evidence_sha256": self.evidence["sha256"]}
                       for name in checker.DELIVERY_CHECKS},
        })
        self.complete("M5", {
            "reproducibility_report": reproduction, "delivery_report": delivery,
            "paper_pdf": pdf, "submission_package": self.put("submission.zip", b"PK fixture"),
        }, ["mathmodel-latex-skill"], 11)

    def save(self):
        self.put(".contest/mathorcup_control.yaml", self.control)
        self.put(".contest/approval_log.yaml", self.log)


class MathorCupControlTests(unittest.TestCase):
    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return MathorCupFixture(Path(temp.name))

    def test_paper_blueprint_uses_mathorcup_evidence(self):
        template = yaml.safe_load((ROOT / "templates" / "mathorcup_paper_argument_blueprint.yaml").read_text(encoding="utf-8"))
        self.assertEqual(template["active_mode"], "full-contest-mathorcup")
        self.assertIn("result_interpretation_cards", template["source_refs"])
        self.assertIn("visual_argument_plan", template["source_refs"])
        self.assertNotIn("paper_narrative", template["source_refs"])

    def test_m1_and_all_nodes_pass_with_current_evidence(self):
        fixture = self.fixture()
        fixture.m5()
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M1")["status"], "PASS")
        self.assertEqual(checker.check(fixture.root, "M5")["status"], "PASS")
        self.assertEqual(checker.check(fixture.root, preflight_writing=True)["status"], "PASS")

    def test_missing_node_approval_pauses(self):
        fixture = self.fixture()
        fixture.m2()
        fixture.log["approvals"] = [entry for entry in fixture.log["approvals"] if entry["gate"] != "M2"]
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "PAUSE")

    def test_in_progress_node_with_pending_literature_pauses(self):
        fixture = self.fixture()
        fixture.m2()
        fixture.control["nodes"]["M2"]["status"] = "in_progress"
        fixture.control["nodes"]["M2"]["literature_sources"] = None
        fixture.log["approvals"] = [entry for entry in fixture.log["approvals"] if entry["gate"] != "M2"]
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "PAUSE")

    def test_second_solver_instance_blocks(self):
        fixture = self.fixture()
        fixture.m3()
        fixture.control["solver_instance_id"] = "another-solver"
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M3")["status"], "BLOCK")

    def test_astra_or_non_max_route_blocks(self):
        fixture = self.fixture()
        fixture.m1()
        fixture.control["agent_runtime_routes"]["solver"] = {"model": "gpt-6-astra", "reasoning_effort": "max"}
        fixture.control["agent_runtime_routes"]["figure"]["reasoning_effort"] = "medium"
        fixture.save()
        self.assertEqual(checker.check(fixture.root)["status"], "BLOCK")

    def test_dispatch_task_card_mismatch_blocks(self):
        fixture = self.fixture()
        fixture.m1()
        record = fixture.control["dispatch_records"][0]
        path = fixture.root / record["task_card"]
        card = yaml.safe_load(path.read_text(encoding="utf-8"))
        card["model"] = "gpt-6-astra"
        path.write_text(yaml.safe_dump(card), encoding="utf-8")
        record["task_card_sha256"] = digest(path)
        fixture.save()
        self.assertEqual(checker.check(fixture.root)["status"], "BLOCK")

    def test_leakage_audit_cannot_be_self_approved(self):
        fixture = self.fixture()
        fixture.m2()
        audit_ref = fixture.control["nodes"]["M2"]["leakage_audit"]
        path = fixture.root / audit_ref["path"]
        audit = yaml.safe_load(path.read_text(encoding="utf-8"))
        audit["verification_agent_instance_id"] = "agent-data"
        path.write_text(yaml.safe_dump(audit), encoding="utf-8")
        audit_ref["sha256"] = digest(path)
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_leakage_audit_requires_all_named_checks(self):
        fixture = self.fixture()
        fixture.m2()
        audit_ref = fixture.control["nodes"]["M2"]["leakage_audit"]
        path = fixture.root / audit_ref["path"]
        audit = yaml.safe_load(path.read_text(encoding="utf-8"))
        audit["checks"] = [{"name": "split_integrity", "status": "PASS"}]
        path.write_text(yaml.safe_dump(audit), encoding="utf-8")
        audit_ref["sha256"] = digest(path)
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_modeling_waits_for_user_literature_sources(self):
        fixture = self.fixture()
        fixture.m2()
        ref = fixture.control["nodes"]["M2"]["literature_sources"]
        path = fixture.root / ref["path"]
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        value["sources"][0]["user_supplied"] = False
        path.write_text(yaml.safe_dump(value), encoding="utf-8")
        ref["sha256"] = digest(path)
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_m3_must_cover_every_question(self):
        fixture = self.fixture()
        fixture.m3()
        fixture.control["problem_scope"]["subproblems"].append("Q2")
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M3")["status"], "BLOCK")

    def test_m3_requires_cross_question_interface_check(self):
        fixture = self.fixture()
        fixture.m3()
        ref = fixture.control["nodes"]["M3"]["independent_validation"]
        path = fixture.root / ref["path"]
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        value["checks"] = [item for item in value["checks"] if item["name"] != "cross_question_interface"]
        path.write_text(yaml.safe_dump(value), encoding="utf-8")
        ref["sha256"] = digest(path)
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M3")["status"], "BLOCK")

    def test_conditional_support_cannot_write_final_conclusions(self):
        fixture = self.fixture()
        fixture.m3()
        card = {
            "task_id": "M3-support-1", "node_id": "M3", "owner_role": "support",
            "agent_instance_id": "agent-support", "model": "gpt-6-luna",
            "reasoning_effort": "max", "objective": "Local code experiment",
            "inputs": [fixture.problem], "prohibited_actions": ["Do not change the model route"],
            "dispatch_kind": "conditional_support", "parent_solver_instance_id": "agent-solver",
            "allowed_output_kinds": ["final_conclusion"],
            "authority": {"may_change_model_route": False, "may_write_final_results": False,
                          "may_aggregate_conclusions": True},
        }
        ref = fixture.put(".contest/task_cards/M3-support-1.yaml", card)
        fixture.control["dispatch_records"].append({
            "task_id": "M3-support-1", "node_id": "M3", "owner_role": "support",
            "agent_instance_id": "agent-support", "model": "gpt-6-luna",
            "reasoning_effort": "max", "called_at": "2026-10-16T04:00:00+08:00",
            "task_card": ref["path"], "task_card_sha256": ref["sha256"],
            "dispatch_kind": "conditional_support", "parent_solver_instance_id": "agent-solver",
        })
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M3")["status"], "BLOCK")

    def test_conditional_support_with_local_evidence_passes(self):
        fixture = self.fixture()
        fixture.m3()
        card = {
            "task_id": "M3-support-1", "node_id": "M3", "owner_role": "support",
            "agent_instance_id": "agent-support", "model": "gpt-6-luna",
            "reasoning_effort": "max", "objective": "Check one code experiment",
            "inputs": [fixture.problem], "prohibited_actions": ["Do not choose the model route"],
            "dispatch_kind": "conditional_support", "parent_solver_instance_id": "agent-solver",
            "allowed_output_kinds": ["code_experiment_evidence"],
            "authority": {"may_change_model_route": False, "may_write_final_results": False,
                          "may_aggregate_conclusions": False},
        }
        ref = fixture.put(".contest/task_cards/M3-support-1.yaml", card)
        fixture.control["dispatch_records"].append({
            "task_id": "M3-support-1", "node_id": "M3", "owner_role": "support",
            "agent_instance_id": "agent-support", "model": "gpt-6-luna",
            "reasoning_effort": "max", "called_at": "2026-10-16T04:00:00+08:00",
            "task_card": ref["path"], "task_card_sha256": ref["sha256"],
            "dispatch_kind": "conditional_support", "parent_solver_instance_id": "agent-solver",
        })
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M3")["status"], "PASS")

    def test_figure_generation_requires_prior_plan_approval(self):
        fixture = self.fixture()
        fixture.m4()
        record = next(item for item in fixture.control["dispatch_records"]
                      if item["node_id"] == "M4" and item["owner_role"] == "figure" and item["task_id"].endswith("-2"))
        record["called_at"] = "2026-10-16T06:00:00+08:00"
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M4")["status"], "BLOCK")

    def test_svg_png_and_visual_qa_are_required(self):
        fixture = self.fixture()
        fixture.m4()
        ref = fixture.control["nodes"]["M4"]["figure_registry"]
        path = fixture.root / ref["path"]
        registry = yaml.safe_load(path.read_text(encoding="utf-8"))
        registry["figures"][0]["visual_qa"] = "not_requested"
        registry["figures"][0]["formats"] = ["png"]
        path.write_text(yaml.safe_dump(registry), encoding="utf-8")
        ref["sha256"] = digest(path)
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M4")["status"], "BLOCK")

    def test_route_diagram_uses_catalog_and_requires_skill_call(self):
        fixture = self.fixture()
        fixture.m4()
        m4 = fixture.control["nodes"]["M4"]
        catalog = yaml.safe_load((ROOT / "references" / "figure_template_catalog.yaml").read_text(encoding="utf-8"))
        template = next(item for item in catalog["templates"] if item["template_id"] == "problem-analysis-flow")
        source = (ROOT.parent / template["starter_source"]).read_bytes()
        starter = fixture.put("figures/problem-analysis-flow.json", source)
        script = fixture.put("figures/tech-route.json", source)
        plan_path = fixture.root / m4["visual_argument_plan"]["path"]
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        plan["slots"][0].update(generation_route="tech-route-maker", template_id=template["template_id"])
        fixture.put(m4["visual_argument_plan"]["path"], plan)
        registry_path = fixture.root / m4["figure_registry"]["path"]
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        figure = registry["figures"][0]
        figure.update(kind="flowchart", generator="tech-route-maker", generation_route="tech-route-maker",
                      template_id=template["template_id"], template_sha256=template["template_sha256"],
                      starter_source=starter["path"], starter_sha256=starter["sha256"],
                      script=script["path"], script_sha256=script["sha256"])
        m4["figure_registry"] = fixture.put(m4["figure_registry"]["path"], registry)
        errors = []
        self.assertEqual(checker._validate_figures(fixture.root, plan_path, registry_path, errors), 1)
        self.assertEqual(errors, [])
        checker._check_skill_calls(fixture.root, "M4", m4, True, errors)
        self.assertIn("M4: required skill invocation missing: tech-route-maker", errors)
        plan["slots"][0]["template_id"] = "model-summary-frame"
        fixture.put(m4["visual_argument_plan"]["path"], plan)
        errors = []
        checker._validate_figures(fixture.root, plan_path, registry_path, errors)
        self.assertTrue(any("template_id/route mismatch" in error for error in errors))

    def test_writing_waits_for_plan_approvals(self):
        fixture = self.fixture()
        fixture.m4()
        fixture.log["approvals"] = [entry for entry in fixture.log["approvals"]
                                    if entry["gate"] != "M4_WRITING_PLAN"]
        fixture.save()
        self.assertEqual(checker.check(fixture.root, preflight_writing=True)["status"], "BLOCK")

    def test_missing_material_readiness_pauses_before_writing(self):
        fixture = self.fixture()
        fixture.m4()
        m4 = fixture.control["nodes"]["M4"]
        m4["status"] = "in_progress"
        m4["writing_started"] = False
        m4["paper_material_readiness"] = None
        m4["chapters"] = []
        fixture.control["dispatch_records"] = [record for record in fixture.control["dispatch_records"]
                                                if not (record["node_id"] == "M4" and record["owner_role"] == "writer" and record["task_id"].endswith("-2"))]
        fixture.save()
        self.assertEqual(checker.check(fixture.root, preflight_writing=True)["status"], "PAUSE")

    def test_ready_materials_pass_before_first_chapter(self):
        fixture = self.fixture()
        fixture.m4()
        m4 = fixture.control["nodes"]["M4"]
        m4["status"] = "in_progress"
        m4["writing_started"] = False
        m4["chapters"] = []
        fixture.control["dispatch_records"] = [record for record in fixture.control["dispatch_records"]
                                                if not (record["node_id"] == "M4" and record["owner_role"] == "writer" and record["task_id"].endswith("-2"))]
        fixture.log["approvals"] = [entry for entry in fixture.log["approvals"]
                                    if entry["gate"] not in {"M4", "M4_CHAPTER:results"}]
        fixture.save()
        self.assertEqual(checker.check(fixture.root, preflight_writing=True)["status"], "PASS")

    def test_next_chapter_waits_for_previous_chapter_approval(self):
        fixture = self.fixture()
        fixture.m4()
        m4 = fixture.control["nodes"]["M4"]
        manuscript = fixture.put("paper/discussion.tex", "\\section{Discussion} Result boundary.")
        m4["chapters"].append({
            "chapter_id": "discussion", "manuscript": manuscript,
            "review_packet": fixture.review("M4_CHAPTER:discussion", [manuscript], 11),
        })
        fixture.log["approvals"] = [entry for entry in fixture.log["approvals"] if entry["gate"] != "M4"]
        m4["review_packet"] = fixture.review("M4", [m4[key] for key in checker.NODE_ARTIFACTS["M4"]], 12)
        fixture.dispatch("M4", "writer", 8, [m4["paper_argument_blueprint"],
                         m4["paper_material_readiness"], m4["paper_claim_coverage"]],
                         phase="write", chapter_id="discussion")
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M4")["status"], "BLOCK")

    def test_unmapped_paper_claim_blocks(self):
        fixture = self.fixture()
        fixture.m4()
        ref = fixture.control["nodes"]["M4"]["paper_claim_coverage"]
        path = fixture.root / ref["path"]
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        value["claims"][0]["evidence_refs"] = []
        path.write_text(yaml.safe_dump(value), encoding="utf-8")
        ref["sha256"] = digest(path)
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M4")["status"], "BLOCK")

    def test_m5_does_not_pass_failed_reproduction(self):
        fixture = self.fixture()
        fixture.m5()
        ref = fixture.control["nodes"]["M5"]["reproducibility_report"]
        path = fixture.root / ref["path"]
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        value["exit_code"] = 1
        path.write_text(yaml.safe_dump(value), encoding="utf-8")
        ref["sha256"] = digest(path)
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M5")["status"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
