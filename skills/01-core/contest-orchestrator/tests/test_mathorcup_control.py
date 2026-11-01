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
        # These fixtures exercise the historical 1.0 contract; new semantics have separate regressions.
        self.control.pop("execution_protocol", None)
        self.control["nodes"]["M4"].pop("visual_workflow", None)
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

    def dispatch(self, node, role, hour, inputs=None, phase=None, batch_id=None, chapter_ids=None):
        sequence = 1 + sum(record["node_id"] == node and record["owner_role"] == role
                           for record in self.control["dispatch_records"])
        task_id = f"{node}-{role}-{sequence}"
        model, effort = checker.ROUTES[role]
        card = {
            "task_id": task_id, "node_id": node, "owner_role": role,
            "agent_instance_id": f"agent-{role}", "model": model,
            "reasoning_effort": effort, "objective": f"Produce {node} evidence",
            "inputs": inputs or [self.problem],
            "scope": ({"phase": phase or "plan",
                       **({"batch_id": batch_id, "chapter_ids": chapter_ids} if batch_id else {})}
                      if node == "M4" else
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

    def preauthorize(self, *gates):
        self.control["approval_policy"] = checker.PREAUTH_POLICY
        self.log["authorizations"] = [{
            "id": "fixture-replay-autoadvance",
            "type": "preauthorized_autoadvance",
            "authorized_by": "user",
            "authorized_on": "2026-10-16",
            "scope": "this isolated replay only",
            "applies_to": list(gates),
            "conditions": [
                "preserve all review packets and current artifact hashes",
                "complete every non-approval technical and evidence gate",
                "do not create per-node user approval records",
            ],
        }]

    def review(self, gate, artifacts, hour, review_type=None, reviewer_skill=None, checks=None):
        checks = checks or [{"name": "evidence", "status": "PASS"}]
        normalized_checks = []
        for item in checks:
            normalized = dict(item)
            normalized.setdefault("name", normalized.get("id", "evidence"))
            normalized.setdefault("evidence_ref", self.evidence["path"])
            normalized.setdefault("evidence_sha256", self.evidence["sha256"])
            normalized_checks.append(normalized)
        packet = {
            "node_id": gate.split(":", 1)[0].split("_", 1)[0],
            "summary": f"{gate} evidence",
            "important_artifacts": artifacts,
            "checks": normalized_checks,
            "requested_decision": "approve",
        }
        if review_type:
            packet["review_type"] = review_type
        if reviewer_skill:
            packet["reviewer_skill"] = reviewer_skill
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
        language_profile = self.put("paper_language_profile.yaml", {
            "status": "approved", "approval_gate": "M4_WRITING_PLAN",
            "scope": "ordinary_prose_only", "review_targets": ["题目", "题干"],
            "source_refs": {"competition_profile": self.control["competition_profile"]},
            "change_policy": "context_review_no_global_replace",
            "term_rules": [],
            "protected_scopes": [
                "formulas", "symbols", "values", "citations", "figure_and_table_content",
                "headings", "direct_quotes", "model_logic",
            ],
            "batch_application": {
                "approved_at": "writing_plan_gate",
                "apply_only_to_ordinary_prose": True,
                "report_unresolved_contexts": True,
            },
        })
        chapter_ids = ["overview", "modeling", "results", "evaluation"]
        blueprint = self.put("paper_argument_blueprint.yaml", {
            "spine": "data-to-result",
            "global": {"target_length": {"page_range": [35, 51], "basis": "verified official rules"},
                       "chapter_order": chapter_ids},
            "chapters": [{
                "chapter_id": chapter_id, "role": f"reader-facing purpose for {chapter_id}",
                "page_capacity": "2 pages", "figure_ids": [], "table_ids": [],
                "claim_ids": ["c1"] if chapter_id == "results" else [],
                "evidence_refs": [result],
            } for chapter_id in chapter_ids],
            "writing_batches": [{"batch_id": f"B{index}", "chapter_ids": [chapter_id],
                                 "purpose": f"Draft {chapter_id}"}
                                for index, chapter_id in enumerate(chapter_ids, 1)],
        })
        m4 = self.control["nodes"]["M4"]
        m4["visual_argument_plan"] = visual
        m4["paper_argument_blueprint"] = blueprint
        m4["paper_language_profile"] = language_profile
        m4["visual_plan_review_packet"] = self.review("M4_VISUAL_PLAN", [visual], 7)
        m4["writing_plan_review_packet"] = self.review(
            "M4_WRITING_PLAN", [blueprint, language_profile], 7)
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
            "chapters": [{"chapter_id": chapter_id, "capacity": "2 pages", "material_refs": [material]}
                         for chapter_id in chapter_ids],
        })
        coverage = self.put("paper_claim_coverage.yaml", {
            "status": "PASS", "readiness_sha256": readiness["sha256"],
            "claims": [{"id": "c1", "paper_anchor": "results", "evidence_refs": [result]}],
        })
        self.dispatch("M4", "figure", 8, [visual, result], phase="generate")
        batches = []
        abstract_framework = None
        for index, chapter_id in enumerate(chapter_ids, 1):
            batch_id = f"B{index}"
            batch = {"batch_id": batch_id, "chapter_ids": [chapter_id]}
            manuscript = self.put(f"paper/{chapter_id}.tex", f"\\section{{{chapter_id}}} Evidence-backed text.")
            prior_manuscripts = [item["manuscript"] for item in batches]
            inputs = [blueprint, language_profile, readiness, coverage, *prior_manuscripts]
            if batch_id == "B4" and abstract_framework is not None:
                inputs.append(abstract_framework)
            dispatch_hour = 8 + (index - 1) * 2
            if batch_id == "B4":
                dispatch_hour = 16
            self.dispatch("M4", "writer", dispatch_hour, inputs, phase="write",
                          batch_id=batch_id, chapter_ids=[chapter_id])
            gate = f"M4_WRITING_BATCH:{batch_id}"
            check_names = ["language_profile_terms", "first_use_symbol_definitions",
                           "claim_evidence_coverage", "metadiscourse", "negative_echo"]
            if batch_id == "B4":
                check_names.extend(["abstract_contract", "whole_paper_final"])
            packet = self.review(
                gate, [manuscript], dispatch_hour + 1,
                review_type="paper_batch_review", reviewer_skill="论文辅助",
                checks=[{"id": name, "status": "PASS"} for name in check_names],
            )
            batch.update(manuscript=manuscript, review_packet=packet)
            batches.append(batch)
            if batch_id == "B3":
                self.dispatch("M4", "writer", dispatch_hour + 2,
                              [blueprint, language_profile, *prior_manuscripts, manuscript],
                              phase="abstract_framework")
                abstract_framework = self.put("paper/abstract_framework.yaml", {
                    "claims": ["c1"], "evidence_refs": [result],
                })
                m4["abstract_framework"] = abstract_framework
                m4["abstract_framework_review_packet"] = self.review(
                    "M4_ABSTRACT_FRAMEWORK", [abstract_framework], dispatch_hour + 3,
                    review_type="abstract_framework_review",
                    checks=[{"id": name, "status": "PASS"}
                            for name in ("claim_alignment", "evidence_scope", "official_limits")],
                )
        m4["writing_batches"] = batches
        gap = self.put("evidence_gap_matrix.yaml", {"status": "PASS", "gaps": []})
        readiness_card = self.put(".contest/task_cards/M4_H6-readiness.yaml", {
            "task_id": "M4-H6-readiness", "agent_instance_id": "agent-verifier",
            "inputs": [readiness, coverage, blueprint, gap],
        })
        m4["task_card"] = readiness_card
        m4["material_readiness_review_packet"] = self.put(".contest/reviews/M4_H6-readiness.yaml", {
            "task_id": "M4-H6-readiness", "node_id": "M4", "status": "PASS",
            "material_readiness": "PASS", "verification_agent_instance_id": "agent-verifier",
            "task_card": readiness_card,
            "input_hash_gate": {"status": "PASS", "declared_inputs": 4,
                                "matched_inputs": 4, "mismatches": 0},
            "important_artifacts": [readiness, coverage, blueprint, gap],
            "checks": [{"name": "readiness", "status": "PASS",
                        "evidence_ref": readiness["path"],
                        "evidence_sha256": readiness["sha256"]}],
        })
        pdf = self.put("paper/main.pdf", b"%PDF-1.4\nfixture\n")
        m4["writing_started"] = True
        self.complete("M4", {
            "visual_argument_plan": visual, "figure_registry": registry,
            "paper_argument_blueprint": blueprint,
            "paper_language_profile": language_profile,
            "paper_material_readiness": readiness, "paper_claim_coverage": coverage,
            "abstract_framework": abstract_framework, "paper_pdf": pdf,
        }, ["academic-writing", "mathmodel-latex-skill", "scipilot-figure-skill", "modelviz",
            "论文辅助", "论文辅助", "论文辅助", "论文辅助"], 18)
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
        approval_ref = self.put(".contest/approval_log.yaml", self.log)
        authorizations = self.log.get("authorizations", [])
        if isinstance(authorizations, list):
            for authorization in authorizations:
                if not isinstance(authorization, dict):
                    continue
                for gate in authorization.get("applies_to", []):
                    if not isinstance(gate, str):
                        continue
                    node_id = gate if gate in checker.NODES else ("M4" if gate.startswith("M4_") else None)
                    if node_id:
                        self.control["nodes"][node_id]["advancement_authorization"] = {
                            "id": authorization.get("id"),
                            "source": approval_ref["path"],
                            "source_sha256": approval_ref["sha256"],
                        }
        self.put(".contest/mathorcup_control.yaml", self.control)

    def remove_writing_dispatches(self):
        kept = []
        for record in self.control["dispatch_records"]:
            if record.get("node_id") == "M4" and record.get("owner_role") == "writer":
                card_path = self.root / record["task_card"]
                card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
                if card.get("scope", {}).get("phase") in {"write", "abstract_framework"}:
                    continue
            kept.append(record)
        self.control["dispatch_records"] = kept


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

    def test_explicit_replay_preauthorization_passes_without_approval_rows(self):
        fixture = self.fixture()
        fixture.m2()
        fixture.log["approvals"] = []
        fixture.preauthorize("M1", "M2")
        fixture.save()
        result = checker.check(fixture.root, "M2")
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(fixture.log["approvals"], [])

    def test_preauthorization_does_not_advance_an_in_progress_node(self):
        fixture = self.fixture()
        fixture.m2()
        fixture.control["nodes"]["M2"]["status"] = "in_progress"
        fixture.log["approvals"] = []
        fixture.preauthorize("M1", "M2")
        fixture.save()
        result = checker.check(fixture.root, "M2")
        self.assertEqual(result["status"], "PAUSE")
        self.assertIn("M2: node not approved", result["pending"])

    def test_preauthorization_is_limited_to_its_declared_gates(self):
        fixture = self.fixture()
        fixture.m2()
        fixture.log["approvals"] = []
        fixture.preauthorize("M1")
        fixture.save()
        result = checker.check(fixture.root, "M2")
        self.assertEqual(result["status"], "PAUSE")
        self.assertIn("M2: current user approval missing", result["pending"])

    def test_stale_preauthorization_binding_blocks(self):
        fixture = self.fixture()
        fixture.m1()
        fixture.log["approvals"] = []
        fixture.preauthorize("M1")
        fixture.save()
        fixture.control["nodes"]["M1"]["advancement_authorization"]["source_sha256"] = "0" * 64
        fixture.put(".contest/mathorcup_control.yaml", fixture.control)
        result = checker.check(fixture.root, "M1")
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("must bind the current approval log" in item for item in result["failures"]))

    def test_m4_preauthorization_covers_plan_and_batch_gates(self):
        fixture = self.fixture()
        fixture.m4()
        fixture.log["approvals"] = []
        fixture.preauthorize("M1", "M2", "M3", "M4", "M4_VISUAL_PLAN",
                             "M4_WRITING_PLAN", "M4_WRITING_BATCH", "M4_ABSTRACT_FRAMEWORK")
        fixture.save()
        result = checker.check(fixture.root, "M4")
        self.assertEqual(result["status"], "PASS", result)

    def test_registered_h5_material_audit_and_legacy_figure_phase_are_allowed(self):
        fixture = self.fixture()
        fixture.m4()
        visual = next(item for item in fixture.control["dispatch_records"]
                      if item["task_id"] == "M4-figure-1")
        visual_card_path = fixture.root / visual["task_card"]
        visual_card = yaml.safe_load(visual_card_path.read_text(encoding="utf-8"))
        visual_card["task_id"] = "MC25A-M4-H7-FIGURES-001"
        visual_card["scope"]["phase"] = "h7_visual_argument_and_data_figures"
        visual_card_path.write_text(yaml.safe_dump(visual_card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        visual.update(task_id=visual_card["task_id"], task_card_sha256=digest(visual_card_path))

        fixture.dispatch("M4", "solver", 7, [fixture.problem], phase="post_h6_paper_material_audit")
        audit = fixture.control["dispatch_records"][-1]
        audit_card_path = fixture.root / audit["task_card"]
        audit_card = yaml.safe_load(audit_card_path.read_text(encoding="utf-8"))
        audit_card["task_id"] = "MC25A-M4-H5-MATERIAL-AUDIT-001"
        audit_card_path.write_text(yaml.safe_dump(audit_card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        audit.update(task_id=audit_card["task_id"], task_card_sha256=digest(audit_card_path))
        fixture.preauthorize("M1", "M2", "M3", "M4", "M4_VISUAL_PLAN",
                             "M4_WRITING_PLAN", "M4_WRITING_BATCH", "M4_ABSTRACT_FRAMEWORK")
        fixture.save()

        result = checker.check(fixture.root, "M4")
        self.assertEqual(result["status"], "PASS", result)

    def test_superseded_dispatch_requires_and_accepts_a_valid_replacement(self):
        fixture = self.fixture()
        fixture.m4()
        fixture.dispatch("M4", "figure", 11, phase="plan")
        old = fixture.control["dispatch_records"][-1]
        old_card_path = fixture.root / old["task_card"]
        old_card = yaml.safe_load(old_card_path.read_text(encoding="utf-8"))
        old_card["model"] = "gpt-6.1-sol"
        old_card_path.write_text(yaml.safe_dump(old_card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        old.update(model="gpt-6.1-sol", superseded_by="M4-figure-corrected",
                   superseded_reason="The recorded figure-agent model route was incorrect; output was not accepted.",
                   task_card_sha256=digest(old_card_path))

        fixture.dispatch("M4", "figure", 12, phase="plan")
        replacement = fixture.control["dispatch_records"][-1]
        replacement_card_path = fixture.root / replacement["task_card"]
        replacement_card = yaml.safe_load(replacement_card_path.read_text(encoding="utf-8"))
        replacement_card["task_id"] = "M4-figure-corrected"
        replacement_card_path.write_text(yaml.safe_dump(replacement_card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        replacement["task_id"] = replacement_card["task_id"]
        replacement["task_card_sha256"] = digest(replacement_card_path)
        fixture.save()

        result = checker.check(fixture.root, "M4")
        self.assertEqual(result["status"], "PASS", result)

    def test_superseded_dispatch_without_replacement_blocks(self):
        fixture = self.fixture()
        fixture.m4()
        fixture.dispatch("M4", "figure", 11, phase="plan")
        old = fixture.control["dispatch_records"][-1]
        old["superseded_by"] = "missing-replacement"
        old["superseded_reason"] = "The output was not accepted because dispatch metadata was invalid."
        fixture.save()

        result = checker.check(fixture.root, "M4")
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("requires exactly one successor record" in item for item in result["failures"]))

    def test_current_h7_visual_review_packet_is_hash_checked(self):
        fixture = self.fixture()
        fixture.m4()
        m4 = fixture.control["nodes"]["M4"]
        required = sorted(checker.M4_VISUAL_PLAN_CHECKS)
        checks = [{"id": name, "status": "PASS"} for name in required]
        next(item for item in checks if item["id"] == "model_fact_scope")["status"] = "PASS_WITH_SCOPE_BOUNDARY"
        packet = {
            "node_id": "M4", "review_type": "plan_scope_and_evidence_preflight", "status": "PASS",
            "plan_path": m4["visual_argument_plan"]["path"],
            "plan_digest": {"sha256": m4["visual_argument_plan"]["sha256"]},
            "input_hash_gate": {"status": "PASS", "declared_inputs": 20,
                                "matched_inputs": 20, "mismatches": 0},
            "checks": checks,
        }
        m4["visual_plan_review_packet"] = fixture.put(".contest/reviews/native_visual_plan_review.yaml", packet)
        fixture.log["approvals"] = []
        fixture.preauthorize("M1", "M2", "M3", "M4", "M4_VISUAL_PLAN",
                             "M4_WRITING_PLAN", "M4_WRITING_BATCH", "M4_ABSTRACT_FRAMEWORK")
        fixture.save()

        errors, pauses = [], []
        _, reviewed = checker._review(
            fixture.root, fixture.control, fixture.log, "M4_VISUAL_PLAN",
            m4["visual_plan_review_packet"],
            [(m4["visual_argument_plan"]["path"],
              fixture.root / m4["visual_argument_plan"]["path"])],
            errors, pauses,
        )
        self.assertEqual(errors, [])
        self.assertEqual(pauses, [])
        self.assertIn("visual_argument_plan.yaml", reviewed)

    def test_m4_plan_review_rebinds_current_blueprint_hash_for_prior_dispatches(self):
        fixture = self.fixture()
        fixture.m4()
        m4 = fixture.control["nodes"]["M4"]
        current_blueprint = fixture.put("paper_argument_blueprint.yaml", {"spine": "reconciled"})
        m4["paper_argument_blueprint"] = current_blueprint
        m4["writing_plan_review_packet"] = fixture.review(
            "M4_WRITING_PLAN", [current_blueprint], 7)
        fixture.log["approvals"] = []
        fixture.preauthorize("M1", "M2", "M3", "M4", "M4_VISUAL_PLAN",
                             "M4_WRITING_PLAN", "M4_WRITING_BATCH", "M4_ABSTRACT_FRAMEWORK")
        fixture.save()

        result = checker.check(fixture.root, preflight_writing=True)
        self.assertFalse(any("stale input hash" in item for item in result["failures"]), result)

    def test_current_h6_readiness_review_rebinds_only_its_hash_bound_materials(self):
        fixture = self.fixture()
        fixture.m4()
        control = fixture.control
        m4 = control["nodes"]["M4"]
        m3 = control["nodes"]["M3"]
        old_readiness = dict(m4["paper_material_readiness"])
        current_readiness = fixture.put(old_readiness["path"], {
            "status": "PASS", "verification_agent_instance_id": "agent-verifier",
            "revision": "H6 final binding",
        })
        m4["paper_material_readiness"] = current_readiness
        claims = fixture.put("paper_claim_coverage.yaml", {
            "status": "PASS", "readiness_sha256": current_readiness["sha256"],
            "claims": [{"id": "c1", "paper_anchor": "results", "evidence_refs": [fixture.evidence]}],
        })
        blueprint = fixture.put("paper_argument_blueprint.yaml", {"status": "draft"})
        gap = fixture.put("evidence_gap_matrix.yaml", {"status": "PASS", "gaps": []})
        m4["paper_claim_coverage"] = claims
        m4["paper_argument_blueprint"] = blueprint
        h6_card = fixture.put(".contest/task_cards/M4_H6-final.yaml", {
            "task_id": "M4-H6-final", "agent_instance_id": "agent-verifier",
            "inputs": [current_readiness, claims, blueprint, gap],
        })
        m4["task_card"] = h6_card
        report = fixture.put(".contest/reviews/M4_H6-final.yaml", {
            "task_id": "M4-H6-final", "node_id": "M4", "status": "PASS",
            "material_readiness": "PASS", "verification_agent_instance_id": "agent-verifier",
            "task_card": h6_card,
            "input_hash_gate": {"status": "PASS", "declared_inputs": 4,
                                "matched_inputs": 4, "mismatches": 0},
            "important_artifacts": [current_readiness, claims, blueprint, gap],
            "checks": [{"name": "content", "status": "PASS",
                        "evidence_ref": current_readiness["path"],
                        "evidence_sha256": current_readiness["sha256"]}],
        })
        m4["material_readiness_review_packet"] = report

        m3_review_ref = m3["review_packet"]
        m3_review_path = fixture.root / m3_review_ref["path"]
        m3_review = yaml.safe_load(m3_review_path.read_text(encoding="utf-8"))
        m3_review["important_artifacts"].append(old_readiness)
        m3_review["checks"].append({
            "name": "readiness_snapshot", "status": "PASS",
            "evidence_ref": old_readiness["path"],
            "evidence_sha256": old_readiness["sha256"],
        })
        m3["review_packet"] = fixture.put(m3_review_ref["path"], m3_review)
        fixture.log["approvals"] = []
        fixture.preauthorize("M3")
        fixture.save()

        errors, pauses = [], []
        ids = {role: f"agent-{role}" for role in checker.ROUTES}
        rebound = checker._h6_material_rebindings(fixture.root, fixture.control, ids, errors, pauses)
        self.assertEqual(errors, [])
        self.assertEqual(pauses, [])
        self.assertEqual(rebound["paper_material_readiness.yaml"], current_readiness["sha256"])
        errors, pauses = [], []
        checker._review(fixture.root, fixture.control, fixture.log, "M3",
                        m3["review_packet"], [], errors, pauses, rebound)
        self.assertEqual(errors, [])
        self.assertEqual(pauses, [])

    def test_m4_solver_summary_card_reconciliation_is_exactly_scoped(self):
        fixture = self.fixture()
        fixture.m4()
        fixture.dispatch("M4", "solver", 11, phase="evidence_reconciliation")
        record = fixture.control["dispatch_records"][-1]
        card_path = fixture.root / record["task_card"]
        card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
        card["task_id"] = "MC25A-M4-H5-SUMMARY-CARDS-001"
        card_path.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        record["task_id"] = card["task_id"]
        record["task_card_sha256"] = digest(card_path)
        fixture.save()

        result = checker.check(fixture.root, "M4")
        self.assertEqual(result["status"], "PASS", result)

    def test_m4_solver_summary_card_rejects_other_phases(self):
        fixture = self.fixture()
        fixture.m4()
        fixture.dispatch("M4", "solver", 11, phase="write")
        record = fixture.control["dispatch_records"][-1]
        card_path = fixture.root / record["task_card"]
        card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
        card["task_id"] = "MC25A-M4-H5-SUMMARY-CARDS-001"
        card_path.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        record["task_id"] = card["task_id"]
        record["task_card_sha256"] = digest(card_path)
        fixture.save()

        result = checker.check(fixture.root, "M4")
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("M4 solver dispatch phase must be evidence_reconciliation" in item
                            for item in result["failures"]))

    def test_historical_input_hash_passes_when_current_review_rebinds_it(self):
        fixture = self.fixture()
        fixture.m2()
        node = fixture.control["nodes"]["M2"]
        old_feature = dict(node["features"])
        record = next(item for item in fixture.control["dispatch_records"]
                      if item["node_id"] == "M2" and item["owner_role"] == "data")
        card_path = fixture.root / record["task_card"]
        card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
        card["inputs"] = [old_feature]
        card_path.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        record["task_card_sha256"] = digest(card_path)

        current_feature = fixture.put(old_feature["path"], {"features": ["x"], "revision": 2})
        node["features"] = current_feature
        review_ref = node["review_packet"]
        review_path = fixture.root / review_ref["path"]
        packet = yaml.safe_load(review_path.read_text(encoding="utf-8"))
        packet["important_artifacts"] = [
            current_feature if item.get("path") == old_feature["path"] else item
            for item in packet["important_artifacts"]
        ]
        node["review_packet"] = fixture.put(review_ref["path"], packet)
        fixture.log["approvals"] = []
        fixture.preauthorize("M1", "M2")
        fixture.save()
        result = checker.check(fixture.root, "M2")
        self.assertEqual(result["status"], "PASS", result)

    def test_legacy_task_card_verification_bans_satisfy_prohibition_gate(self):
        fixture = self.fixture()
        fixture.m2()
        record = next(item for item in fixture.control["dispatch_records"]
                      if item["node_id"] == "M2" and item["owner_role"] == "data")
        card_path = fixture.root / record["task_card"]
        card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
        card.pop("prohibited_actions")
        card["verification"] = ["Do not train, tune, or select a model route."]
        card_path.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        record["task_card_sha256"] = digest(card_path)
        fixture.save()

        result = checker.check(fixture.root, "M2")
        self.assertEqual(result["status"], "PASS", result)

    def test_legacy_task_card_without_explicit_verification_ban_blocks(self):
        fixture = self.fixture()
        fixture.m2()
        record = next(item for item in fixture.control["dispatch_records"]
                      if item["node_id"] == "M2" and item["owner_role"] == "data")
        card_path = fixture.root / record["task_card"]
        card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
        card.pop("prohibited_actions")
        card["verification"] = ["Produce the EDA report."]
        card_path.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        record["task_card_sha256"] = digest(card_path)
        fixture.save()

        result = checker.check(fixture.root, "M2")
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("task card prohibited_actions required" in item for item in result["failures"]))

    def test_historical_input_hash_without_current_review_rebind_blocks(self):
        fixture = self.fixture()
        fixture.m2()
        record = next(item for item in fixture.control["dispatch_records"]
                      if item["node_id"] == "M2" and item["owner_role"] == "data")
        historical = fixture.put("inputs/revised-later.txt", "historical snapshot")
        card_path = fixture.root / record["task_card"]
        card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
        card["inputs"] = [historical]
        card_path.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        record["task_card_sha256"] = digest(card_path)
        fixture.put(historical["path"], "current content without review rebind")
        fixture.log["approvals"] = []
        fixture.preauthorize("M1", "M2")
        fixture.save()
        result = checker.check(fixture.root, "M2")
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("not rebound by the current node review" in item for item in result["failures"]))

    def test_downstream_task_accepts_upstream_artifact_rebound_by_source_review(self):
        fixture = self.fixture()
        fixture.m2()
        leakage = fixture.control["nodes"]["M2"]["leakage_audit"]
        stale_ref = {"path": leakage["path"], "sha256": "0" * 64}
        fixture.dispatch("M3", "solver", 4, [stale_ref])
        record = next(item for item in fixture.control["dispatch_records"]
                      if item["node_id"] == "M3" and item["owner_role"] == "solver")
        card_path = fixture.root / record["task_card"]
        card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
        card["inputs"] = [stale_ref]
        card_path.write_text(yaml.safe_dump(card, allow_unicode=True, sort_keys=False), encoding="utf-8")
        record["task_card_sha256"] = digest(card_path)
        fixture.control["nodes"]["M3"]["status"] = "in_progress"
        fixture.save()

        result = checker.check(fixture.root, "M3")
        self.assertEqual(result["status"], "PAUSE", result)
        self.assertFalse(any("stale input hash" in item for item in result["failures"]))

    def test_retried_dispatch_allows_same_task_id_with_distinct_submission_ids(self):
        fixture = self.fixture()
        fixture.m1()
        first = fixture.control["dispatch_records"][0]
        first["submission_id"] = "submission-1"
        retry = dict(first, called_at="2026-10-16T00:30:00+08:00", submission_id="submission-2")
        fixture.control["dispatch_records"].append(retry)
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M1")["status"], "PASS")

    def test_duplicate_task_id_without_retry_identity_blocks(self):
        fixture = self.fixture()
        fixture.m1()
        retry = dict(fixture.control["dispatch_records"][0],
                     called_at="2026-10-16T00:30:00+08:00")
        fixture.control["dispatch_records"].append(retry)
        fixture.save()
        result = checker.check(fixture.root, "M1")
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("repeated task_id requires" in item for item in result["failures"]))

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

    def test_leakage_audit_accepts_named_check_mapping_with_valid_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence = root / "evidence.txt"
            evidence.write_text("verified", encoding="utf-8")
            checks = {
                name: {"status": "PASS", "evidence_ref": "evidence.txt",
                       "evidence_sha256": digest(evidence)}
                for name in checker.LEAKAGE_CHECKS
            }
            errors = []
            checker._named_pass_checks(root, checks, checker.LEAKAGE_CHECKS,
                                       "M2.leakage_audit", errors)
            self.assertEqual(errors, [])

    def test_leakage_audit_mapping_with_failed_check_blocks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence = root / "evidence.txt"
            evidence.write_text("verified", encoding="utf-8")
            checks = {
                name: {"status": "PASS", "evidence_ref": "evidence.txt",
                       "evidence_sha256": digest(evidence)}
                for name in checker.LEAKAGE_CHECKS
            }
            checks["split_integrity"]["status"] = "FAIL"
            errors = []
            checker._named_pass_checks(root, checks, checker.LEAKAGE_CHECKS,
                                       "M2.leakage_audit", errors)
            self.assertTrue(any("named PASS check required" in item for item in errors))

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

    def test_literature_accepts_explicitly_authorized_assistant_search_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = MathorCupFixture(Path(temporary))
            summary = fixture.put("literature/Q1_summary.md", "Method, data, scope and source location.")
            source_ref = fixture.put("literature_sources.yaml", {
                "status": "PASS", "search_owner": "assistant",
                "acquisition_mode": "assistant_search_user_authorized",
                "user_authorization_date": "2026-10-18",
                "sources": [{
                    "citation_key": "study-q1", "covered_subproblems": ["Q1"],
                    "user_supplied": False,
                    "source_origin": "assistant_search_under_explicit_user_authorization",
                    "locator": "publisher section 2", "use": "method baseline",
                    "summary_ref": summary,
                }],
            })
            errors = []
            checker._validate_node_evidence(
                fixture.root, "M2", {"literature_sources": (source_ref["path"], fixture.root / source_ref["path"])},
                {}, ["Q1"], errors,
            )
            self.assertEqual(errors, [])

    def test_literature_assistant_search_without_explicit_authorization_blocks(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = MathorCupFixture(Path(temporary))
            summary = fixture.put("literature/Q1_summary.md", "Method, data, scope and source location.")
            source_ref = fixture.put("literature_sources.yaml", {
                "status": "PASS", "search_owner": "assistant",
                "acquisition_mode": "assistant_search",
                "user_authorization_date": "2026-10-18",
                "sources": [{
                    "citation_key": "study-q1", "covered_subproblems": ["Q1"],
                    "user_supplied": False,
                    "source_origin": "assistant_search_under_explicit_user_authorization",
                    "locator": "publisher section 2", "use": "method baseline",
                    "summary_ref": summary,
                }],
            })
            errors = []
            checker._validate_node_evidence(
                fixture.root, "M2", {"literature_sources": (source_ref["path"], fixture.root / source_ref["path"])},
                {}, ["Q1"], errors,
            )
            self.assertTrue(any("authorized source origin" in item for item in errors))

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

    def test_m3_accepts_legacy_command_string_and_named_review_mapping(self):
        fixture = self.fixture()
        fixture.m3()
        node = fixture.control["nodes"]["M3"]

        manifest_ref = node["run_manifest"]
        manifest_path = fixture.root / manifest_ref["path"]
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        manifest["command"] = "python solve.py"
        updated_manifest = fixture.put(manifest_ref["path"], manifest)
        node["run_manifest"] = updated_manifest

        review_ref = node["review_packet"]
        review_path = fixture.root / review_ref["path"]
        review = yaml.safe_load(review_path.read_text(encoding="utf-8"))
        review["important_artifacts"] = [
            updated_manifest if item.get("path") == manifest_ref["path"] else item
            for item in review["important_artifacts"]
        ]
        review["checks"] = {
            "m3_evidence": {
                "status": "PASS",
                "evidence_ref": fixture.evidence["path"],
                "evidence_sha256": fixture.evidence["sha256"],
            }
        }
        node["review_packet"] = fixture.put(review_ref["path"], review)
        approval = next(item for item in fixture.log["approvals"] if item["gate"] == "M3")
        approval["artifact_digests"][updated_manifest["path"]] = updated_manifest["sha256"]
        approval["artifact_digests"][node["review_packet"]["path"]] = node["review_packet"]["sha256"]

        fixture.save()
        result = checker.check(fixture.root, "M3")
        self.assertEqual(result["status"], "PASS", result)

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

    def test_route_diagram_uses_tikz_catalog_and_requires_skill_call(self):
        fixture = self.fixture()
        fixture.m4()
        m4 = fixture.control["nodes"]["M4"]
        catalog = yaml.safe_load((ROOT / "references" / "figure_template_catalog.yaml").read_text(encoding="utf-8"))
        template = next(item for item in catalog["templates"] if item["template_id"] == "problem-analysis-flow")
        source_path = ROOT.parent / template["starter_source"]
        if not source_path.is_file():
            source_path = ROOT.parents[1] / "04-figures" / template["starter_source"]
        source = source_path.read_bytes()
        starter = fixture.put("figures/problem-analysis-flow.tex", source)
        script = fixture.put("figures/problem-analysis-flow-editable.tex", source)
        plan_path = fixture.root / m4["visual_argument_plan"]["path"]
        plan = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
        plan["slots"][0].update(generation_route="tikz-scientific-figures", template_id=template["template_id"])
        fixture.put(m4["visual_argument_plan"]["path"], plan)
        registry_path = fixture.root / m4["figure_registry"]["path"]
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        figure = registry["figures"][0]
        figure.update(kind="flowchart", generator="tikz-scientific-figures", generation_route="tikz-scientific-figures",
                      template_id=template["template_id"], template_sha256=template["template_sha256"],
                      starter_source=starter["path"], starter_sha256=starter["sha256"],
                      script=script["path"], script_sha256=script["sha256"])
        m4["figure_registry"] = fixture.put(m4["figure_registry"]["path"], registry)
        errors = []
        self.assertEqual(checker._validate_figures(fixture.root, plan_path, registry_path, errors), 1)
        self.assertEqual(errors, [])
        m4["skill_invocations"].append({
            "skill": "tikz-scientific-figures", "status": "completed",
            "evidence_ref": fixture.evidence["path"],
            "evidence_sha256": fixture.evidence["sha256"],
        })
        checker._check_skill_calls(fixture.root, "M4", m4, True, errors)
        self.assertEqual(errors, [])
        plan["slots"][0]["template_id"] = "compact-result"
        fixture.put(m4["visual_argument_plan"]["path"], plan)
        errors = []
        checker._validate_figures(fixture.root, plan_path, registry_path, errors)
        self.assertTrue(any("template_id/route mismatch" in error for error in errors))

    def test_current_visual_plan_and_registry_schema_closes_figures_and_table(self):
        fixture = self.fixture()
        qa = fixture.put("results/scipilot_qa.yaml", {"status": "PASS"})
        editable = fixture.put("results/plot.py", "print('plot')")
        data = fixture.put("results/plot.csv", "x,y\n1,2\n")
        svg = fixture.put("figures/result.svg", b"<svg></svg>")
        png = fixture.put("figures/result.png", b"PNG fixture")
        table = fixture.put("tables/interface.csv", "question,value\nQ1,flag\n")
        evidence = f"{fixture.evidence['path']}#sha256={fixture.evidence['sha256']}#result"
        plan = {
            "global_visual_slots": [{
                "slot_id": "shared-interface", "representation": {"mode": "table"},
                "evidence_refs": [evidence],
            }],
            "subproblems": [{
                "subproblem_id": "Q1",
                "visual_audit": [{
                    "slot_id": "Q1-result", "disposition": "required",
                    "representation": {"mode": "figure"}, "evidence_refs": [evidence],
                    "figure_intent": {"generation_route": "modelviz", "template_id": "compact-result"},
                }],
            }],
        }
        registry = {
            "insertion_format": "svg",
            "figures": [{
                "figure_id": "fig-Q1", "visual_slot_ids": ["Q1-result"],
                "generator": "modelviz", "template_id": "compact-result",
                "formats": ["svg", "png"], "caption": "Figure 1",
                "visual_qa": {"status": "passed", "report": qa["path"]},
                "editable_source": editable, "data_source": data,
                "evidence_sources": [fixture.evidence],
                "outputs": {"svg": svg, "png": png},
            }],
            "tables": [{
                "table_id": "tab-interface", "visual_slot_ids": ["shared-interface"],
                **table, "qa": {"status": "PASS", "report": qa["path"]},
            }],
        }
        plan_ref = fixture.put("visual_argument_plan.yaml", plan)
        registry_ref = fixture.put("figure_registry.yaml", registry)
        errors = []
        count = checker._validate_figures(
            fixture.root, fixture.root / plan_ref["path"],
            fixture.root / registry_ref["path"], errors,
        )
        self.assertEqual(count, 1)
        self.assertEqual(errors, [])

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
        fixture.remove_writing_dispatches()
        fixture.save()
        self.assertEqual(checker.check(fixture.root, preflight_writing=True)["status"], "PAUSE")

    def test_ready_materials_pass_before_first_batch(self):
        fixture = self.fixture()
        fixture.m4()
        m4 = fixture.control["nodes"]["M4"]
        m4["status"] = "in_progress"
        m4["writing_started"] = False
        fixture.remove_writing_dispatches()
        fixture.log["approvals"] = [entry for entry in fixture.log["approvals"]
                                    if not entry["gate"].startswith("M4_WRITING_BATCH:")
                                    and entry["gate"] not in {"M4", "M4_ABSTRACT_FRAMEWORK"}]
        fixture.save()
        self.assertEqual(checker.check(fixture.root, preflight_writing=True)["status"], "PASS")

    def test_unapproved_language_profile_pauses_before_writing(self):
        fixture = self.fixture()
        fixture.m4()
        m4 = fixture.control["nodes"]["M4"]
        m4["status"] = "in_progress"
        m4["writing_started"] = False
        fixture.remove_writing_dispatches()
        profile = yaml.safe_load((fixture.root / m4["paper_language_profile"]["path"])
                                 .read_text(encoding="utf-8"))
        profile["status"] = "draft"
        m4["paper_language_profile"] = fixture.put(m4["paper_language_profile"]["path"], profile)
        m4["writing_plan_review_packet"] = fixture.review(
            "M4_WRITING_PLAN", [m4["paper_argument_blueprint"], m4["paper_language_profile"]], 7)
        fixture.save()
        result = checker.check(fixture.root, preflight_writing=True)
        self.assertEqual(result["status"], "PAUSE", result)
        self.assertTrue(any("paper_language_profile requires user approval" in item
                            for item in result["pending"]))

    def test_next_batch_waits_for_previous_batch_approval(self):
        fixture = self.fixture()
        fixture.m4()
        second_batch = next(record for record in fixture.control["dispatch_records"]
                            if record.get("node_id") == "M4" and record.get("owner_role") == "writer"
                            and yaml.safe_load((fixture.root / record["task_card"]).read_text(encoding="utf-8"))
                            .get("scope", {}).get("batch_id") == "B2")
        second_batch["called_at"] = "2026-10-16T08:30:00+08:00"
        fixture.save()
        result = checker.check(fixture.root, "M4")
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("B2" in item and "approval" in item for item in result["failures"]))

    def test_b4_waits_for_separate_abstract_framework_approval(self):
        fixture = self.fixture()
        fixture.m4()
        fixture.log["approvals"] = [entry for entry in fixture.log["approvals"]
                                    if entry["gate"] != "M4_ABSTRACT_FRAMEWORK"]
        fixture.save()
        result = checker.check(fixture.root, "M4")
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("B4" in item and "M4_ABSTRACT_FRAMEWORK" in item
                            for item in result["failures"]))

    def test_legacy_chapter_approval_gate_is_rejected(self):
        fixture = self.fixture()
        fixture.m4()
        fixture.log["approvals"].append({"gate": "M4_CHAPTER:results", "decision": "approve",
                                         "approved_by": "user", "approved_at": "2026-10-16T19:00:00+08:00",
                                         "artifact_digests": {}})
        fixture.save()
        result = checker.check(fixture.root, "M4")
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("chapter-level approval is not permitted" in item
                            for item in result["failures"]))

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


    def recovered_m2(self, pending=False):
        fixture = self.fixture()
        fixture.m2()
        replacements = []
        registered = []
        runtime = {}
        for role in ("data", "verifier"):
            prior = dict(fixture.control["agent_instances"][role])
            new_id = f"recovered-{role}"
            runtime[role] = {**prior, "agent_instance_id": new_id}
            replacements.append({
                "role": role, "previous_agent_instance_id": prior["agent_instance_id"],
                "new_agent_instance_id": new_id, "model": prior["model"],
                "reasoning_effort": prior["reasoning_effort"],
            })
            registered.append({"role": role, "previous_instance": prior,
                               "new_agent_instance_id": new_id})
            for record in fixture.control["dispatch_records"]:
                if record["node_id"] == "M2" and record["owner_role"] == role:
                    card_path = fixture.root / record["task_card"]
                    card = yaml.safe_load(card_path.read_text(encoding="utf-8"))
                    card["agent_instance_id"] = new_id
                    card_ref = fixture.put(record["task_card"], card)
                    record["agent_instance_id"] = new_id
                    record["task_card_sha256"] = card_ref["sha256"]
        fixture.control["runtime_instances_by_node"] = {"M2": runtime}
        node = fixture.control["nodes"]["M2"]
        audit = yaml.safe_load((fixture.root / node["leakage_audit"]["path"]).read_text(encoding="utf-8"))
        audit["verification_agent_instance_id"] = "recovered-verifier"
        node["leakage_audit"] = fixture.put(node["leakage_audit"]["path"], audit)
        artifacts = {key: node[key] for key in checker.NODE_ARTIFACTS["M2"]}
        fixture.log["approvals"] = [x for x in fixture.log["approvals"] if x["gate"] != "M2"]
        fixture.complete("M2", artifacts, ["data-science-stack"], 3)
        fixture.log["instance_recoveries"] = [{
            "id": "recover-m2", "decision": "approve", "approved_by": "user",
            "approved_at": "2026-10-16T01:30:00+08:00", "effective_from_node": "M2",
            "source_ref": fixture.put("evidence/recovery_approval.json", {"user_statement": "Restore both roles"}),
            "context_ref": fixture.control["nodes"]["M1"]["review_packet"],
            "recovery_record_ref": fixture.put(".contest/recovery.yaml", {
                "authorized_by": "user", "replacements": registered}),
            "replacements": replacements,
        }]
        if pending:
            node["status"] = "review_pending"
            fixture.log["approvals"] = [x for x in fixture.log["approvals"] if x["gate"] != "M2"]
        fixture.save()
        return fixture

    def test_authorized_recovery_preserves_both_node_identities(self):
        fixture = self.recovered_m2()
        for node in ("M1", "M2"):
            result = checker.check(fixture.root, node)
            self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(fixture.control["dispatch_records"][0]["agent_instance_id"], "agent-data")

    def test_unapproved_node_preflight_is_read_only_and_pauses(self):
        fixture = self.recovered_m2(pending=True)
        paths = [fixture.root / ".contest/mathorcup_control.yaml", fixture.root / ".contest/approval_log.yaml"]
        before = [x.read_bytes() for x in paths]
        result = checker.check(fixture.root, preflight_node="M2")
        self.assertEqual(result["status"], "PAUSE", result)
        self.assertEqual(result["evidence_status"], "PASS", result)
        self.assertFalse(result["failures"])
        self.assertEqual(before, [x.read_bytes() for x in paths])
        self.assertFalse(any(x["gate"] == "M2" for x in fixture.log["approvals"]))

    def test_pending_recovery_through_still_requires_user_approval(self):
        fixture = self.recovered_m2(pending=True)
        result = checker.check(fixture.root, "M2")
        self.assertEqual(result["status"], "PAUSE", result)
        self.assertFalse(result["failures"])

    def test_pending_preflight_catches_bad_artifact_hash(self):
        fixture = self.recovered_m2(pending=True)
        (fixture.root / "features.yaml").write_text("tampered", encoding="utf-8")
        result = checker.check(fixture.root, preflight_node="M2")
        self.assertEqual(result["status"], "BLOCK", result)
        self.assertEqual(result["evidence_status"], "BLOCK")

    def test_pending_preflight_checks_required_skill_evidence(self):
        fixture = self.recovered_m2(pending=True)
        fixture.control["nodes"]["M2"]["skill_invocations"] = []
        fixture.save()
        self.assertEqual(checker.check(fixture.root, preflight_node="M2")["status"], "BLOCK")

    def test_runtime_override_without_user_recovery_blocks(self):
        fixture = self.recovered_m2()
        fixture.log["instance_recoveries"] = []
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_recovery_rejects_non_user_approval(self):
        fixture = self.recovered_m2()
        fixture.log["instance_recoveries"][0]["approved_by"] = "assistant"
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_recovery_rejects_broken_identity_chain(self):
        fixture = self.recovered_m2()
        fixture.log["instance_recoveries"][0]["replacements"][0]["previous_agent_instance_id"] = "unrelated"
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_recovery_rejects_role_model_change(self):
        fixture = self.recovered_m2()
        fixture.log["instance_recoveries"][0]["replacements"][0]["model"] = "gpt-6.1-sol"
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_recovery_rejects_actor_reuse_between_roles(self):
        fixture = self.recovered_m2()
        fixture.log["instance_recoveries"][0]["replacements"][1]["new_agent_instance_id"] = "recovered-data"
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_recovery_requires_valid_source_and_context_hashes(self):
        for key in ("source_ref", "context_ref", "recovery_record_ref"):
            with self.subTest(key=key):
                fixture = self.recovered_m2()
                fixture.log["instance_recoveries"][0][key]["sha256"] = "0" * 64
                fixture.save()
                self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_recovery_rejects_wrong_predecessor_context(self):
        fixture = self.recovered_m2()
        fixture.log["instance_recoveries"][0]["context_ref"] = fixture.evidence
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_recovery_requires_new_instance_preload_record(self):
        fixture = self.recovered_m2()
        fixture.control["runtime_instances_by_node"]["M2"]["verifier"]["preloaded"] = []
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_recovery_cannot_apply_before_its_boundary(self):
        fixture = self.recovered_m2()
        fixture.log["instance_recoveries"][0]["effective_from_node"] = "M3"
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M2")["status"], "BLOCK")

    def test_recovery_approval_must_precede_dispatch(self):
        fixture = self.recovered_m2()
        fixture.log["instance_recoveries"][0]["approved_at"] = "2026-10-16T02:30:00+08:00"
        fixture.save()
        result = checker.check(fixture.root, "M2")
        self.assertEqual(result["status"], "BLOCK")
        self.assertTrue(any("before instance recovery approval" in x for x in result["failures"]))

    def test_recovered_verifier_signature_is_required(self):
        fixture = self.recovered_m2(pending=True)
        node = fixture.control["nodes"]["M2"]
        path = fixture.root / node["leakage_audit"]["path"]
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        value["verification_agent_instance_id"] = "agent-verifier"
        node["leakage_audit"] = fixture.put(node["leakage_audit"]["path"], value)
        node["review_packet"] = fixture.put(".contest/reviews/M2.yaml", {
            "node_id": "M2", "important_artifacts": [node[k] for k in checker.NODE_ARTIFACTS["M2"]]})
        fixture.save()
        result = checker.check(fixture.root, preflight_node="M2")
        self.assertEqual(result["status"], "BLOCK", result)
        self.assertTrue(any("independent verifier PASS" in x for x in result["failures"]))

    def test_recovery_does_not_allow_rewriting_m1_dispatch(self):
        fixture = self.recovered_m2()
        fixture.control["dispatch_records"][0]["agent_instance_id"] = "recovered-data"
        fixture.save()
        self.assertEqual(checker.check(fixture.root, "M1")["status"], "BLOCK")



if __name__ == "__main__":
    unittest.main()
