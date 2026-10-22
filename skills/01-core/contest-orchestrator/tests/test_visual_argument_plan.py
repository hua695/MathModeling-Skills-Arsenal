import json
import copy
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import check_visual_evidence
from scripts import check_harness_control


def _model_cards():
    return {
        "schema_version": "1.0",
        "status": "verified",
        "cards": [
            {
                "card_id": f"Q{index}-final-model",
                "subproblem_id": f"Q{index}",
                "purpose": f"Q{index} 的优化决策",
                "model_family": "optimization",
                "decision_variables": [
                    {"symbol": "x", "meaning": "决策量", "unit": "单位", "domain": "非负", "variable_type": "continuous"},
                    {"symbol": "y", "meaning": "辅助决策量", "unit": "单位", "domain": "非负", "variable_type": "continuous"},
                ],
                "parameters": [],
                "final_formulation": {"kind": "optimization", "expression": "min f(x, y)"},
                "solver_interface": {"method": "PSO iteration", "inputs": ["x"], "outputs": ["objective"]},
            }
            for index in range(1, 5)
        ],
    }


def _figure_intent(category):
    route = {
        "mechanism": "tikz-scientific-figures",
        "model_structure": "tikz-scientific-figures",
        "result_evidence": "modelviz",
        "validation_robustness": "modelviz",
    }.get(category, "tech-route-maker")
    template_id = {
        "orientation": "problem-analysis-flow",
        "algorithm_process": "algorithm-iteration-flow",
        "global_story": "contest-mainline-route",
        "model_structure": "model-summary-frame",
        "mechanism": "free-body-mechanism",
        "result_evidence": "modelviz/result-figure",
        "validation_robustness": "modelviz/validation-figure",
    }.get(category, "problem-analysis-flow")
    return {
        "reader_question": f"图表如何回答 {category} 的读者问题？",
        "explanatory_relation": f"冻结证据中的 {category} 关系",
        "must_show": [f"{category} 的关键对象"],
        "must_not_show": ["未被证据支持的公式或数值"],
        "body_anchor": "对应问题的模型建立或模型求解与结果分析小节",
        "pre_text_function": "引出图表要回答的具体问题",
        "post_text_function": "解释图表对本问结论的直接贡献及边界",
        "generation_route": route,
        "template_status": "native",
        "template_id": template_id,
        "visible_element_map": [
            {
                "element": f"{category} 的关键对象",
                "role": "node",
                "evidence_refs": [f"model_summary_cards.yaml#/{category}/object"],
            },
            {
                "element": f"{category} 的解释关系",
                "role": "edge",
                "evidence_refs": [f"model_summary_cards.yaml#/{category}/relation"],
            },
        ],
        "canvas_profile": {
            "orientation": "horizontal",
            "target_layout": "single",
            "top_level_node_limit": 7,
        },
    }


def _lazy_visual_plan():
    categories = (
        "orientation",
        "mechanism",
        "model_structure",
        "algorithm_process",
        "result_evidence",
        "validation_robustness",
    )
    subproblems = []
    for index in range(1, 5):
        subproblems.append({
            "subproblem_id": f"Q{index}",
            "reader_question": f"Q{index} 的结果如何回答题目？",
            "visual_audit": [
                {
                    "slot_id": f"Q{index}-{category}",
                    "category": category,
                    "disposition": "text_sufficient",
                    "reader_question": f"读者是否需要看到 Q{index} 的 {category}？",
                    "reader_gain": "正文已可以直接说明",
                    "evidence_refs": [f"model_summary_cards.yaml#/cards/Q{index}"],
                    "rationale": "文字可以完整表达该关系",
                    "planned_figure_ids": [],
                }
                for category in categories
            ],
        })
    return {
        "schema_version": "1.0",
        "status": "approved",
        "prepared_by": "h7-figure-agent",
        "source_node": "H7",
        "scope": {"subproblems": ["Q1", "Q2", "Q3", "Q4"], "cross_question_dependencies": True},
        "global_visual_slots": [{
            "slot_id": "global-story-01",
            "category": "global_story",
            "disposition": "text_sufficient",
            "reader_question": "各小问如何递进？",
            "reader_gain": "正文已经说明",
            "evidence_refs": ["paper_narrative.yaml#/narrative/global/storyline"],
            "rationale": "不需要图",
            "planned_figure_ids": [],
        }],
        "subproblems": subproblems,
        "coverage_summary": {
            "required_figure_slots": 0,
            "planned_figure_count": 0,
        },
    }


def _valid_visual_plan():
    categories = (
        "orientation",
        "mechanism",
        "model_structure",
        "algorithm_process",
        "result_evidence",
        "validation_robustness",
    )
    subproblems = []
    for index in range(1, 3):
        qid = f"Q{index}"
        audit = []
        for category in categories:
            if category == "mechanism":
                audit.append({
                    "slot_id": f"{qid}-mechanism",
                    "category": category,
                    "disposition": "not_applicable",
                    "reader_question": "读者是否需要机理示意？",
                    "reader_gain": "本问不存在空间或物理机理关系",
                    "evidence_refs": [f"model_summary_cards.yaml#/{qid}"],
                    "rationale": "模型变量为抽象资源分配量，文字和公式已能完整表达关系",
                    "planned_figure_ids": [],
                })
                continue
            disposition = "recommended" if category == "orientation" else "required"
            audit.append({
                "slot_id": f"{qid}-{category}",
                "category": category,
                "disposition": disposition,
                "reader_question": f"读者需要从图中理解 {qid} 的 {category} 吗？",
                "reader_gain": f"把 {qid} 的 {category} 关系压缩为可读的视觉证据",
                "evidence_refs": [f"model_summary_cards.yaml#/{qid}/{category}"],
                "planned_figure_ids": [f"fig-{qid.lower()}-{category}"],
                "figure_intent": _figure_intent(category),
            })
        subproblems.append({
            "subproblem_id": qid,
            "complexity": "complex",
            "reader_question": f"{qid} 的模型和结果如何回答题目？",
            "visual_audit": audit,
        })
    return {
        "schema_version": "1.0",
        "status": "approved",
        "prepared_by": "h7-figure-agent",
        "source_node": "H7",
        "scope": {"subproblems": ["Q1", "Q2"], "cross_question_dependencies": True},
        "global_visual_slots": [{
            "slot_id": "global-story-01",
            "category": "global_story",
            "disposition": "required",
            "reader_question": "各小问如何递进？",
            "reader_gain": "让读者先看到统一的问题—模型—结果主线",
            "evidence_refs": ["paper_narrative.yaml#/narrative/global/storyline"],
            "planned_figure_ids": ["fig-global-story"],
            "figure_intent": {
                **_figure_intent("global_story"),
                "reader_question": "各小问如何递进？",
                "explanatory_relation": "统一的问题—模型—结果主线",
            },
        }],
        "subproblems": subproblems,
        "coverage_summary": {
            "required_visual_slots": 9,
            "required_figure_slots": 9,
            "planned_figure_count": 11,
        },
    }


def _registry_for(plan):
    figure_ids = ["fig-global-story"]
    for item in plan["subproblems"]:
        for slot in item["visual_audit"]:
            figure_ids.extend(slot.get("planned_figure_ids", []))
    entries = []
    for figure_id in figure_ids:
        slot_ids = []
        if figure_id == "fig-global-story":
            slot_ids = ["global-story-01"]
        else:
            slot_ids = [
                slot["slot_id"]
                for item in plan["subproblems"]
                for slot in item["visual_audit"]
                if figure_id in slot.get("planned_figure_ids", [])
            ]
        source_slot = (
            plan["global_visual_slots"][0]
            if figure_id == "fig-global-story"
            else next(
                slot
                for item in plan["subproblems"]
                for slot in item["visual_audit"]
                if figure_id in slot.get("planned_figure_ids", [])
            )
        )
        route = source_slot["figure_intent"]["generation_route"]
        template_id = source_slot["figure_intent"]["template_id"]
        catalog_entry = check_visual_evidence._template_catalog().get(template_id, {})
        entries.append({
            "figure_id": figure_id,
            "visual_slot_ids": slot_ids,
            "generator": route,
            "template_status": source_slot["figure_intent"]["template_status"],
            "template_id": template_id,
            "starter_source": (
                "tech-route-maker/assets/contest-starters/"
                f"{template_id}.json"
                if route == "tech-route-maker"
                else "tikz-scientific-figures/assets/contest-starters/"
                f"{template_id}.tex"
                if route == "tikz-scientific-figures"
                else None
            ),
            "template_source": "modelviz/catalog/result-figure.py" if route == "modelviz" else None,
            "template_sha256": catalog_entry.get("template_sha256", "a" * 64),
            "visible_element_map": source_slot["figure_intent"]["visible_element_map"],
            "canvas_profile": source_slot["figure_intent"]["canvas_profile"],
            "template_fixture": {
                "fixture_id": (
                    f"{route}/{template_id}"
                ),
                "status": "passed",
                "report": f"figures/{figure_id}/template_fixture.yaml",
            },
            "visual_qa": "passed",
            "qa_status": "reviewed",
            "layout_mode": "single",
            "claim": f"{figure_id} 支持的论证主张",
            "reader_takeaway": f"读者可据此理解 {figure_id} 的核心关系",
        })
    return {"figures": entries}


def _visual_evidence_packet():
    return {
        "schema_version": "1.0",
        "status": "verified",
        "package_mode": "indexed_minimal",
        "source_node": "H5",
        "created_by": "H5",
        "verified_by": "H6",
        "verification_agent_instance_id": "h6-test-instance",
        "model_contract_sha256": "a" * 64,
        "subproblems": [
            {
                "subproblem_id": f"Q{index}",
                "task_goal": f"Q{index} 目标",
                "model_role": f"Q{index} 模型作用",
                "information_units": [
                    {
                        "unit_id": f"Q{index}-U01",
                        "unit_type": "model",
                        "statement": f"Q{index} 的模型结构可计算",
                        "meaning": "说明模型结构",
                        "evidence_refs": ["model_contract.yaml#/model"],
                        "scope": "本小问",
                        "unit": "无量纲",
                    },
                    {
                        "unit_id": f"Q{index}-U02",
                        "unit_type": "result",
                        "statement": f"Q{index} 的结果支持决策",
                        "meaning": "说明结果含义",
                        "evidence_refs": ["results.yaml#/result"],
                        "scope": "当前结果版本",
                        "unit": "无量纲",
                    },
                ],
            }
            for index in range(1, 3)
        ],
    }


def _bind_plan_to_packet(plan):
    for item in plan["subproblems"]:
        qid = item["subproblem_id"]
        for slot in item["visual_audit"]:
            if slot["planned_figure_ids"]:
                slot["information_unit_ids"] = [f"{qid}-U01", f"{qid}-U02"]
                slot["density_profile"] = "standard"
    plan["global_visual_slots"][0]["information_unit_ids"] = ["Q1-U01", "Q2-U01"]
    plan["global_visual_slots"][0]["density_profile"] = "standard"
    return plan


def _bind_registry_to_packet(plan, registry):
    for entry in registry["figures"]:
        slot_id = entry["visual_slot_ids"][0]
        slot = next(
            slot for item in plan["subproblems"] for slot in item["visual_audit"]
            if slot["slot_id"] == slot_id
        ) if slot_id != "global-story-01" else plan["global_visual_slots"][0]
        entry["information_unit_ids"] = list(slot["information_unit_ids"])
        entry["realized_information_unit_ids"] = list(slot["information_unit_ids"])
        entry["density_profile"] = slot["density_profile"]
    return registry


class VisualArgumentPlanTests(unittest.TestCase):
    def test_contest_templates_define_intent_for_every_figure_slot(self):
        root = Path(check_visual_evidence.__file__).resolve().parents[1]
        for path in (
            root / "templates" / "visual_argument_plan.yaml",
            root / "templates" / "b_project_template" / "visual_argument_plan.yaml",
        ):
            plan = yaml.safe_load(path.read_text(encoding="utf-8"))
            slots = [
                slot
                for item in plan.get("subproblems", [])
                for slot in item.get("visual_audit", [])
                if slot.get("planned_figure_ids")
            ]
            self.assertTrue(slots, path)
            for slot in slots:
                with self.subTest(path=path, slot=slot.get("slot_id")):
                    intent = slot.get("figure_intent")
                    self.assertIsInstance(intent, dict)
                    self.assertTrue({
                        "reader_question", "explanatory_relation", "must_show", "must_not_show",
                        "body_anchor", "pre_text_function", "post_text_function",
                        "generation_route", "template_status", "template_id",
                        "visible_element_map", "canvas_profile",
                    } <= set(intent))

    def test_figure_slot_requires_reader_first_intent_contract(self):
        plan = _valid_visual_plan()
        figure_slot = next(
            slot for item in plan["subproblems"] for slot in item["visual_audit"]
            if slot["planned_figure_ids"]
        )
        del figure_slot["figure_intent"]
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            stage="plan",
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("figure_intent" in item for item in report["errors"]))

    def test_figure_intent_requires_template_execution_brief(self):
        required_fields = ("template_id", "visible_element_map", "canvas_profile")
        for field in required_fields:
            with self.subTest(field=field):
                plan = _valid_visual_plan()
                figure_slot = next(
                    slot for item in plan["subproblems"] for slot in item["visual_audit"]
                    if slot["planned_figure_ids"]
                )
                del figure_slot["figure_intent"][field]
                report = check_visual_evidence.validate_visual_argument_plan(
                    plan,
                    expected_subproblems=["Q1", "Q2"],
                    model_cards=_model_cards(),
                    stage="plan",
                )
                self.assertEqual(report["status"], "BLOCK")
                self.assertTrue(any(field in item for item in report["errors"]))

    def test_template_id_must_match_generation_route(self):
        plan = _valid_visual_plan()
        figure_slot = next(
            slot for item in plan["subproblems"] for slot in item["visual_audit"]
            if slot["figure_intent"]["generation_route"] == "tech-route-maker"
        )
        figure_slot["figure_intent"]["template_id"] = "model-summary-frame"
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            stage="plan",
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("template_id" in item and "路由" in item for item in report["errors"]))

    def test_final_registry_requires_template_fixture_hash_and_visual_qa(self):
        plan = _bind_plan_to_packet(_valid_visual_plan())
        registry = _bind_registry_to_packet(plan, _registry_for(plan))
        for field in ("template_sha256", "template_fixture", "visual_qa"):
            with self.subTest(field=field):
                candidate = copy.deepcopy(registry)
                del candidate["figures"][0][field]
                report = check_visual_evidence.validate_visual_argument_plan(
                    plan,
                    expected_subproblems=["Q1", "Q2"],
                    model_cards=_model_cards(),
                    evidence_packet=_visual_evidence_packet(),
                    registry=candidate,
                    stage="final",
                )
                self.assertEqual(report["status"], "BLOCK")
                self.assertTrue(any(field in item for item in report["errors"]))

    def test_final_stage_requires_registry_route_and_template_to_match_plan(self):
        plan = _valid_visual_plan()
        registry = _registry_for(plan)
        result_entry = next(item for item in registry["figures"] if item["generator"] == "modelviz")
        result_entry["generator"] = "tech-route-maker"
        result_entry["template_status"] = "custom_required"
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            registry=registry,
            stage="final",
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("generator 必须与视觉计划路由一致" in item for item in report["errors"]))
        self.assertTrue(any("template_status 必须与视觉计划一致" in item for item in report["errors"]))

    def test_complex_multi_question_plan_cannot_hide_all_visual_needs_in_text(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "model_summary_cards.yaml").write_text(
                yaml.safe_dump(_model_cards(), allow_unicode=True), encoding="utf-8"
            )
            (root / "visual_argument_plan.yaml").write_text(
                yaml.safe_dump(_lazy_visual_plan(), allow_unicode=True), encoding="utf-8"
            )
            payload = {
                "visual_policy": {"table_to_figure_review_ratio": 1.5},
                "content_budget": {"subproblems": [
                    {"id": f"Q{index}", "visual_decision": {"status": "table_justified", "rationale": "fixture"},
                     "visual_evidence": []}
                    for index in range(1, 5)
                ]},
            }
            (root / "content_budget_plan.json").write_text(json.dumps(payload), encoding="utf-8")

            report = check_visual_evidence.check(payload, root, "blueprint", None)

            self.assertEqual(report["status"], "BLOCK")
            self.assertTrue(any("visual" in item.lower() or "视觉" in item for item in report["errors"]))

    def test_complex_plan_passes_with_distinct_reader_value_slots(self):
        plan = _valid_visual_plan()
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            stage="plan",
        )
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual(report["metrics"]["required_figure_slots"], 9)

    def test_table_justification_without_structured_evidence_is_blocked(self):
        plan = _valid_visual_plan()
        result_slot = next(
            slot for slot in plan["subproblems"][0]["visual_audit"]
            if slot["category"] == "result_evidence"
        )
        result_slot["disposition"] = "table_justified"
        result_slot["planned_figure_ids"] = []
        result_slot["table_refs"] = []
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            stage="plan",
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("table_justification" in item for item in report["errors"]))

    def test_coverage_summary_cannot_omit_recomputed_field(self):
        plan = _valid_visual_plan()
        del plan["coverage_summary"]["required_visual_slots"]
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            stage="plan",
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("required_visual_slots" in item for item in report["errors"]))

    def test_visual_plan_requires_model_summary_cards_for_inference(self):
        report = check_visual_evidence.validate_visual_argument_plan(
            _valid_visual_plan(),
            expected_subproblems=["Q1", "Q2"],
            model_cards=None,
            stage="plan",
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("model_summary_cards" in item for item in report["errors"]))

    def test_final_stage_rejects_registry_figure_outside_approved_plan(self):
        plan = _valid_visual_plan()
        registry = _registry_for(plan)
        registry["figures"].append({
            "figure_id": "fig-unplanned",
            "visual_slot_ids": ["not-a-slot"],
            "claim": "没有计划依据的主张",
            "reader_takeaway": "没有计划依据的收获",
        })
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            registry=registry,
            stage="final",
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("未绑定已批准" in item for item in report["errors"]))

    def test_final_stage_requires_figure_slot_closure(self):
        plan = _valid_visual_plan()
        registry = _registry_for(plan)
        registry["figures"] = registry["figures"][1:]
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            registry=registry,
            stage="final",
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("未在 figure_registry 中登记" in item for item in report["errors"]))

    def test_packet_binding_requires_information_density(self):
        plan = _bind_plan_to_packet(_valid_visual_plan())
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            evidence_packet=_visual_evidence_packet(),
            stage="plan",
        )
        self.assertEqual(report["status"], "PASS", report)

        result_slot = next(
            slot for slot in plan["subproblems"][0]["visual_audit"]
            if slot["category"] == "result_evidence"
        )
        result_slot["information_unit_ids"] = ["Q1-U01"]
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            evidence_packet=_visual_evidence_packet(),
            stage="plan",
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("至少需要 2 个独立信息单元" in item for item in report["errors"]))

    def test_packet_binding_closes_planned_and_realized_registry_evidence(self):
        plan = _bind_plan_to_packet(_valid_visual_plan())
        registry = _bind_registry_to_packet(plan, _registry_for(plan))
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            evidence_packet=_visual_evidence_packet(),
            registry=registry,
            stage="final",
        )
        self.assertEqual(report["status"], "PASS", report)

        registry["figures"][0]["realized_information_unit_ids"] = ["Q1-U01"]
        report = check_visual_evidence.validate_visual_argument_plan(
            plan,
            expected_subproblems=["Q1", "Q2"],
            model_cards=_model_cards(),
            evidence_packet=_visual_evidence_packet(),
            registry=registry,
            stage="final",
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("realized_information_unit_ids" in item for item in report["errors"]))

    def test_h7_control_requires_visual_argument_plan_artifact(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".contest").mkdir()
            control = check_harness_control.default_control()
            control["problem_scope"] = {"subproblems": ["Q1"]}
            (root / ".contest" / "harness_control.yaml").write_text(
                yaml.safe_dump(control, allow_unicode=True), encoding="utf-8"
            )

            report = check_harness_control.check_harness_control(root, through="H7")

            self.assertTrue(any("visual_argument_plan" in item for item in report["missing"]))

    def test_h7_generation_requires_separate_visual_plan_approval(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plan_path = root / "visual_argument_plan.yaml"
            plan_path.write_text(
                yaml.safe_dump(_valid_visual_plan(), allow_unicode=True), encoding="utf-8"
            )
            missing: list[str] = []
            failures: list[str] = []
            check_harness_control._validate_h7_visual_plan_approval(
                root,
                {
                    "status": "approved",
                    "visual_argument_plan": "visual_argument_plan.yaml",
                    "visual_plan_review_packet": ".contest/reviews/H7_visual_plan_review_packet.yaml",
                },
                {"approvals": []},
                plan_path,
                missing,
                failures,
            )
            self.assertTrue(any("H7_VISUAL_PLAN" in item for item in missing))

    def test_h7_visual_plan_approval_accepts_matching_packet_and_hashes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reviews = root / ".contest" / "reviews"
            reviews.mkdir(parents=True)
            plan_path = root / "visual_argument_plan.yaml"
            plan_path.write_text(
                yaml.safe_dump(_valid_visual_plan(), allow_unicode=True), encoding="utf-8"
            )
            packet_path = reviews / "H7_visual_plan_review_packet.yaml"
            packet = {
                "node_id": "H7_VISUAL_PLAN",
                "summary": "视觉论证方案审查",
                "important_artifacts": [{
                    "path": "visual_argument_plan.yaml",
                    "sha256": check_harness_control.digest(plan_path),
                }],
                "checks": ["逐小问视觉义务与证据覆盖检查"],
                "requested_decision": "approve",
                "proposed_next_node": "H7_GENERATE",
            }
            packet_path.write_text(
                yaml.safe_dump(packet, allow_unicode=True), encoding="utf-8"
            )
            packet_ref = ".contest/reviews/H7_visual_plan_review_packet.yaml"
            log = {"approvals": [{
                "gate": "H7_VISUAL_PLAN",
                "decision": "approved",
                "artifact_digests": {
                    packet_ref: check_harness_control.digest(packet_path),
                    "visual_argument_plan.yaml": check_harness_control.digest(plan_path),
                },
            }]}
            missing: list[str] = []
            failures: list[str] = []
            check_harness_control._validate_h7_visual_plan_approval(
                root,
                {
                    "status": "approved",
                    "visual_argument_plan": "visual_argument_plan.yaml",
                    "visual_plan_review_packet": packet_ref,
                },
                log,
                plan_path,
                missing,
                failures,
            )
            self.assertEqual(missing, [])
            self.assertEqual(failures, [])

    def test_h7_control_invokes_visual_plan_gate_before_final_review(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".contest").mkdir()
            plan_path = root / "visual_argument_plan.yaml"
            cards_path = root / "model_summary_cards.yaml"
            plan_path.write_text(
                yaml.safe_dump(_valid_visual_plan(), allow_unicode=True), encoding="utf-8"
            )
            cards_path.write_text(
                yaml.safe_dump(_model_cards(), allow_unicode=True), encoding="utf-8"
            )
            control = check_harness_control.default_control()
            control["problem_scope"] = {"subproblems": ["Q1", "Q2"]}
            control["nodes"]["H7"].update({
                "status": "approved",
                "visual_argument_plan": "visual_argument_plan.yaml",
                "model_summary_cards": "model_summary_cards.yaml",
            })
            (root / ".contest" / "harness_control.yaml").write_text(
                yaml.safe_dump(control, allow_unicode=True), encoding="utf-8"
            )
            report = check_harness_control.check_harness_control(root, through="H7")
            self.assertTrue(any("H7_VISUAL_PLAN" in item for item in report["missing"]))

    def test_h7_plan_phase_uses_visual_gate_without_final_figure_review(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".contest" / "reviews").mkdir(parents=True)
            plan_path = root / "visual_argument_plan.yaml"
            cards_path = root / "model_summary_cards.yaml"
            plan_path.write_text(
                yaml.safe_dump(_valid_visual_plan(), allow_unicode=True), encoding="utf-8"
            )
            cards_path.write_text(
                yaml.safe_dump(_model_cards(), allow_unicode=True), encoding="utf-8"
            )
            packet_path = root / ".contest" / "reviews" / "H7_visual_plan_review_packet.yaml"
            packet = {
                "node_id": "H7_VISUAL_PLAN",
                "summary": "视觉论证方案审查",
                "important_artifacts": [{
                    "path": "visual_argument_plan.yaml",
                    "sha256": check_harness_control.digest(plan_path),
                }],
                "checks": ["视觉义务检查"],
                "requested_decision": "approve",
                "proposed_next_node": "H7_GENERATE",
            }
            packet_path.write_text(
                yaml.safe_dump(packet, allow_unicode=True), encoding="utf-8"
            )
            packet_ref = ".contest/reviews/H7_visual_plan_review_packet.yaml"
            control = check_harness_control.default_control()
            control["problem_scope"] = {"subproblems": ["Q1", "Q2"]}
            control["nodes"]["H7"].update({
                "status": "draft",
                "visual_argument_plan": "visual_argument_plan.yaml",
                "visual_plan_review_packet": packet_ref,
                "model_summary_cards": "model_summary_cards.yaml",
            })
            (root / ".contest" / "approval_log.yaml").write_text(
                yaml.safe_dump({"approvals": [{
                    "gate": "H7_VISUAL_PLAN",
                    "decision": "approved",
                    "artifact_digests": {
                        packet_ref: check_harness_control.digest(packet_path),
                        "visual_argument_plan.yaml": check_harness_control.digest(plan_path),
                    },
                }]}, allow_unicode=True), encoding="utf-8"
            )
            (root / ".contest" / "harness_control.yaml").write_text(
                yaml.safe_dump(control, allow_unicode=True), encoding="utf-8"
            )
            report = check_harness_control.check_harness_control(root, through="H7")
            self.assertFalse(any(item == "H7: 缺少 review_packet" for item in report["missing"]))


if __name__ == "__main__":
    unittest.main()
