import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_mathorcup_control import MathorCupFixture, checker


class WriterFirstTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.fixture = MathorCupFixture(Path(directory.name))
        self.fixture.m3()
        self.m4 = self.fixture.control["nodes"]["M4"]
        self.m4["visual_workflow"] = "writer_first_batches"

    def case(self, figure=True):
        f = self.fixture
        draft = f.put("paper/drafts/B1.tex", "Verified result; figure placeholder.")
        plan = f.put("paper/visuals/B1.yaml", {
            "owner_role": "writer", "batch_id": "B1", "draft": draft,
            "prepared_at": "2026-10-16T07:00:00+08:00",
            "slots": [{"slot_id": "s1", "representation": "figure", "generation_route": "modelviz",
                       "reader_question": "Which targets differ?", "body_anchor": "results",
                       "claim": "Targets differ", "evidence_refs": [f.evidence]}] if figure else [],
        })
        batch = {"batch_id": "B1", "chapter_ids": ["results"], "draft": draft,
                 "draft_completed_at": "2026-10-16T06:30:00+08:00", "visual_argument_plan": plan}
        batch["visual_plan_review_packet"] = f.review("M4_VISUAL_PLAN:B1", [draft, plan], 8)
        self.m4["writing_batches"] = [batch]
        f.dispatch("M4", "writer", 6, phase="draft", batch_id="B1", chapter_ids=["results"])
        if figure:
            f.dispatch("M4", "figure", 9, [draft, plan], phase="generate")
            record = f.control["dispatch_records"][-1]
            card = yaml.safe_load((f.root / record["task_card"]).read_text(encoding="utf-8"))
            card["scope"]["batch_id"] = "B1"
            record["task_card_sha256"] = f.put(record["task_card"], card)["sha256"]
            asset = f.put("figures/s1.svg", "<svg/>")
            selection = f.put("paper/visuals/B1_selection.yaml", {
                "batch_id": "B1", "assets": [{"slot_id": "s1", **asset}]})
            batch["figure_selection"] = selection
            batch["figure_selection_review_packet"] = f.review("M4_FIGURE_SELECTION:B1", [selection, asset], 10)
        f.dispatch("M4", "writer", 11, phase="write", batch_id="B1", chapter_ids=["results"])
        return batch

    def validate(self, final=False):
        errors, pauses = [], []
        times = {"M4_WRITING_PLAN": checker._time("2026-10-16T05:30:00+08:00")}
        checker._check_batch_visual_workflow(self.fixture.root, self.fixture.control, self.fixture.log,
                                            times, errors, pauses, final=final)
        return errors, pauses

    def test_draft_then_approved_requirements_generation_selection_and_integration(self):
        self.case()
        self.assertEqual(self.validate(), ([], []))

    def test_no_visual_batch_does_not_require_figure_generation_or_selection(self):
        self.case(figure=False)
        self.assertEqual(self.validate(), ([], []))

    def test_requirements_must_be_authored_by_writer(self):
        batch = self.case()
        path = batch["visual_argument_plan"]["path"]
        plan = yaml.safe_load((self.fixture.root / path).read_text(encoding="utf-8"))
        plan["owner_role"] = "figure"
        batch["visual_argument_plan"] = self.fixture.put(path, plan)
        self.assertTrue(self.validate()[0])

    def test_generation_before_human_requirement_approval_is_rejected(self):
        self.case()
        record = next(r for r in self.fixture.control["dispatch_records"] if r["node_id"] == "M4" and r["owner_role"] == "figure")
        record["called_at"] = "2026-10-16T07:30:00+08:00"
        self.assertTrue(self.validate()[0])

    def test_missing_user_selection_is_pending(self):
        self.case()
        self.fixture.log["approvals"] = [a for a in self.fixture.log["approvals"] if a["gate"] != "M4_FIGURE_SELECTION:B1"]
        errors, pauses = self.validate()
        self.assertTrue(errors or pauses)

    def test_integration_before_selection_is_rejected(self):
        self.case()
        self.fixture.control["dispatch_records"][-1]["called_at"] = "2026-10-16T09:30:00+08:00"
        self.assertTrue(self.validate()[0])

    def test_stale_draft_is_rejected(self):
        batch = self.case()
        (self.fixture.root / batch["draft"]["path"]).write_text("Changed draft", encoding="utf-8")
        self.assertTrue(self.validate()[0])

    def test_wrong_selected_slot_is_rejected(self):
        batch = self.case()
        selection = self.fixture.put("paper/visuals/B1_selection.yaml", {"batch_id": "B1", "assets": []})
        batch["figure_selection"] = selection
        self.assertTrue(self.validate()[0])

    def test_draft_admission_does_not_require_final_figures(self):
        f = self.fixture
        f.m4()
        m4 = f.control["nodes"]["M4"]
        m4.update(visual_workflow="writer_first_batches", visual_argument_plan=None,
                  figure_registry=None, visual_plan_review_packet=None, writing_started=False)
        m4["writing_batches"] = [{"batch_id": b["batch_id"], "chapter_ids": b["chapter_ids"]}
                                  for b in m4["writing_batches"]]
        f.remove_writing_dispatches()
        f.control["dispatch_records"] = [r for r in f.control["dispatch_records"]
                                         if not (r["node_id"] == "M4" and r["owner_role"] == "figure")]
        f.save()
        state_paths = [f.root / ".contest/mathorcup_control.yaml", f.root / ".contest/approval_log.yaml"]
        before = [path.read_bytes() for path in state_paths]
        result = checker.check(f.root, preflight_draft=True)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual([path.read_bytes() for path in state_paths], before)

    def finished_case(self, figure=True):
        f = MathorCupFixture(self.fixture.root)
        f.m4()
        self.fixture = f
        self.m4 = m4 = f.control["nodes"]["M4"]
        m4["visual_workflow"] = "writer_first_batches"
        global_plan = yaml.safe_load((f.root / m4["visual_argument_plan"]["path"]).read_text(encoding="utf-8"))
        slots = global_plan["slots"]
        slots[0].update(reader_question="What differs?", body_anchor="overview", claim="Performance differs")
        registry = yaml.safe_load((f.root / m4["figure_registry"]["path"]).read_text(encoding="utf-8"))
        asset = {"path": registry["figures"][0]["svg"], "sha256": registry["figures"][0]["svg_sha256"]}
        registry["figures"][0]["selected_asset"] = asset
        if not figure:
            slots = []
            registry["figures"] = []
            f.control["dispatch_records"] = [r for r in f.control["dispatch_records"]
                                             if not (r["node_id"] == "M4" and r["owner_role"] == "figure")]
        m4["figure_registry"] = f.put("figure_registry.yaml", registry)
        m4["visual_argument_plan"] = f.put("visual_argument_plan.yaml", {"slots": slots})
        for index, batch in enumerate(m4["writing_batches"]):
            batch_id = batch["batch_id"]
            hour = [7, 9, 11, 15][index]
            timestamp = lambda minute: f"2026-10-16T{hour:02d}:{minute:02d}:00+08:00"
            draft = f.put(f"paper/drafts/{batch_id}.tex", f"Draft {batch_id} based on verified results")
            f.dispatch("M4", "writer", hour, phase="draft", batch_id=batch_id, chapter_ids=batch["chapter_ids"])
            record = f.control["dispatch_records"][-1]
            record["called_at"] = timestamp(5)
            card_path = record["task_card"]
            card = yaml.safe_load((f.root / card_path).read_text(encoding="utf-8"))
            card["inputs"] = [m4[key] for key in ("paper_argument_blueprint", "paper_language_profile",
                                                 "paper_material_readiness", "paper_claim_coverage")]
            card["inputs"].extend(b["manuscript"] for b in m4["writing_batches"][:index])
            if batch_id == "B4":
                card["inputs"].append(m4["abstract_framework"])
            record["task_card_sha256"] = f.put(card_path, card)["sha256"]
            plan = f.put(f"paper/visuals/{batch_id}.yaml", {
                "owner_role": "writer", "batch_id": batch_id, "draft": draft,
                "prepared_at": timestamp(15), "slots": slots if index == 0 else []})
            batch.update(draft=draft, draft_completed_at=timestamp(10), visual_argument_plan=plan)
            batch["visual_plan_review_packet"] = f.review(f"M4_VISUAL_PLAN:{batch_id}", [draft, plan], hour)
            f.log["approvals"][-1]["approved_at"] = timestamp(20)
            extra = [draft, plan]
            if index == 0 and figure:
                selection = f.put("paper/visuals/B1_selection.yaml", {
                    "batch_id": batch_id, "assets": [{"slot_id": slots[0]["slot_id"], **asset}]})
                batch["figure_selection"] = selection
                batch["figure_selection_review_packet"] = f.review("M4_FIGURE_SELECTION:B1", [selection, asset], hour)
                f.log["approvals"][-1]["approved_at"] = timestamp(30)
                extra.extend([selection, asset])
                gen = next(r for r in f.control["dispatch_records"] if r["node_id"] == "M4" and r["owner_role"] == "figure"
                           and yaml.safe_load((f.root / r["task_card"]).read_text())["scope"]["phase"] == "generate")
                gen["called_at"] = timestamp(25)
                card = yaml.safe_load((f.root / gen["task_card"]).read_text())
                card["scope"]["batch_id"] = batch_id
                card["inputs"] = [draft, plan]
                gen["task_card_sha256"] = f.put(gen["task_card"], card)["sha256"]
            write = next(r for r in f.control["dispatch_records"] if r["node_id"] == "M4" and r["owner_role"] == "writer"
                         and yaml.safe_load((f.root / r["task_card"]).read_text())["scope"].get("phase") == "write"
                         and yaml.safe_load((f.root / r["task_card"]).read_text())["scope"].get("batch_id") == batch_id)
            card = yaml.safe_load((f.root / write["task_card"]).read_text())
            card["inputs"].extend(extra)
            write["task_card_sha256"] = f.put(write["task_card"], card)["sha256"]
            packet = yaml.safe_load((f.root / batch["review_packet"]["path"]).read_text(encoding="utf-8"))
            batch["review_packet"] = f.review(f"M4_WRITING_BATCH:{batch_id}", [batch["manuscript"], *extra],
                                               [9, 11, 13, 17][index], review_type="paper_batch_review",
                                               reviewer_skill="论文辅助", checks=packet["checks"])
        artifacts = {key: m4[key] for key in checker.NODE_ARTIFACTS["M4"]}
        f.complete("M4", artifacts, ["academic-writing", "mathmodel-latex-skill", "scipilot-figure-skill", "modelviz",
                                    "论文辅助", "论文辅助", "论文辅助", "论文辅助"], 18)
        f.save()
        return f

    def test_complete_four_batch_workflow_passes_normal_node_checker(self):
        f = self.finished_case()
        result = checker.check(f.root, through="M4")
        self.assertEqual(result["status"], "PASS", result)

    def test_complete_workflow_rejects_registry_selection_drift(self):
        f = self.finished_case()
        path = f.root / "figures/Q1.svg"
        path.write_text("<svg>unapproved variant</svg>", encoding="utf-8")
        result = checker.check(f.root, through="M4")
        self.assertEqual(result["status"], "BLOCK", result)

    def test_complete_text_only_paper_needs_no_figure_dispatch(self):
        f = self.finished_case(figure=False)
        result = checker.check(f.root, through="M4")
        self.assertEqual(result["status"], "PASS", result)

    def test_visual_plan_cannot_be_prepared_before_draft_completion(self):
        batch = self.case()
        path = batch["visual_argument_plan"]["path"]
        plan = yaml.safe_load((self.fixture.root / path).read_text(encoding="utf-8"))
        plan["prepared_at"] = "2026-10-16T06:10:00+08:00"
        batch["visual_argument_plan"] = self.fixture.put(path, plan)
        self.assertTrue(self.validate()[0])

    def test_later_draft_cannot_start_before_previous_batch_approval(self):
        self.case()
        batch = self.m4["writing_batches"][0]
        batch["batch_id"] = "B2"
        self.assertTrue(self.validate()[0])


if __name__ == "__main__":
    unittest.main()
