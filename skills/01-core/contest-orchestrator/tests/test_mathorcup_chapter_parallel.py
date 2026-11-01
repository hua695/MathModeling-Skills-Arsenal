"""Public-entry regressions for approved chapters and asynchronous figures."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_mathorcup_control import MathorCupFixture, checker
from mathorcup_chapter_workflow import ARGUMENT_CHECKS, PROSE_CHECKS


class ChapterFixture(MathorCupFixture):
    def __init__(self, root):
        super().__init__(root)
        self.result, _ = self.m4()
        self.m = self.control["nodes"]["M4"]
        self.control["dispatch_records"] = [r for r in self.control["dispatch_records"] if r["node_id"] != "M4" or (r["owner_role"] in {"writer", "verifier"} and r["called_at"].endswith("06:00:00+08:00"))]
        self.log["approvals"] = [a for a in self.log["approvals"] if not a["gate"].startswith("M4")]
        self.order = ["modeling", "evaluation", "abstract"]
        blueprint = {"global": {"central_thesis": "Verified predictive comparison", "reader_journey": ["model", "comparison", "meaning"], "target_length": {"page_range": [20, 30], "basis": "fixture rule"}, "chapter_order": ["abstract", "modeling", "evaluation"], "writing_order": self.order}, "chapters": [{"chapter_id": c, "kind": c, "depends_on": self.order[:i], "reader_question": "What follows from the evidence?", "expected_answer": "A bounded quantitative result", "role": c, "page_capacity": "2 pages", "figure_ids": [], "table_ids": [], "claim_ids": [], "evidence_refs": [self.result]} for i, c in enumerate(self.order)]}
        self.m.update(visual_workflow="chapter_parallel", status="not_started", writing_started=False, writing_chapters=[], integration_task_id=None, abstract_framework_task_id=None, abstract_framework=None, abstract_framework_review_packet=None, final_review_packet=None, final_manuscript=None, visual_argument_plan=None, figure_registry=None, skill_invocations=[])
        self.m.pop("writing_batches", None)
        self.m["paper_argument_blueprint"] = self.put("paper_argument_blueprint.yaml", blueprint)
        readiness = self.read(self.m["paper_material_readiness"])
        readiness["chapters"] = [{"chapter_id": c, "capacity": "2 pages", "material_refs": [self.result]} for c in self.order]
        self.m["paper_material_readiness"] = self.put("paper_material_readiness.yaml", readiness)
        coverage = self.read(self.m["paper_claim_coverage"])
        coverage["readiness_sha256"] = self.m["paper_material_readiness"]["sha256"]
        self.m["paper_claim_coverage"] = self.put("paper_claim_coverage.yaml", coverage)
        inputs = [self.m[k] for k in ("paper_material_readiness", "paper_claim_coverage", "paper_argument_blueprint")]
        inputs.append(self.put("evidence_gap_matrix.yaml", {"status": "PASS", "gaps": []}))
        card = self.read(self.m["task_card"])
        card["inputs"] = inputs
        self.m["task_card"] = self.put(self.m["task_card"]["path"], card)
        report = self.read(self.m["material_readiness_review_packet"])
        report.update(task_card=self.m["task_card"], important_artifacts=inputs)
        report["checks"][0]["evidence_sha256"] = self.m["paper_material_readiness"]["sha256"]
        self.m["material_readiness_review_packet"] = self.put(self.m["material_readiness_review_packet"]["path"], report)
        self.m["writing_plan_review_packet"] = self.review("M4_WRITING_PLAN", [self.m["paper_argument_blueprint"], self.m["paper_language_profile"]], 7)

    def read(self, ref):
        return yaml.safe_load((self.root / ref["path"]).read_text(encoding="utf-8"))

    def base(self):
        return [self.m[k] for k in ("paper_argument_blueprint", "paper_language_profile", "paper_material_readiness", "paper_claim_coverage")]

    def task(self, role, phase, hour, inputs, chapter=None, revision=None):
        self.dispatch("M4", role, hour, inputs, phase=phase)
        record = self.control["dispatch_records"][-1]
        card = self.read({"path": record["task_card"]})
        card["scope"].update(chapter_id=chapter)
        if revision:
            card["scope"]["revision_id"] = revision
        record["task_card_sha256"] = self.put(record["task_card"], card)["sha256"]
        return record

    def skill(self, ref):
        self.m["skill_invocations"].append({"skill": "论文辅助", "status": "completed", "evidence_ref": ref["path"], "evidence_sha256": ref["sha256"]})

    def chapter(self, cid, hour, approve=True):
        inputs = [*self.base(), self.result, *[c["draft"] for c in self.m["writing_chapters"]]]
        if cid == "abstract":
            inputs.append(self.m["abstract_framework"])
        task = self.task("writer", "draft", hour, inputs, cid)
        draft = self.put(f"paper/drafts/{cid}.tex", f"Complete {cid}: model, derivation, verified numerical comparison and interpretation.")
        quality = self.put(f"paper/reviews/{cid}.yaml", {"status": "ready", "draft_sha256": draft["sha256"], "checks": {k: "PASS" for k in ARGUMENT_CHECKS | PROSE_CHECKS}})
        self.skill(quality)
        packet = self.review(f"M4_CHAPTER:{cid}", [draft, quality], hour+1, review_type="paper_chapter_review", reviewer_skill="论文辅助")
        if not approve:
            self.log["approvals"].pop()
        chapter = {"chapter_id": cid, "task_id": task["task_id"], "draft": draft, "draft_completed_at": f"2026-10-16T{hour:02d}:30:00+08:00", "quality_review": quality, "review_packet": packet, "visuals_required": False, "visual_prompts": []}
        self.m["writing_chapters"].append(chapter)
        return chapter

    def prompt(self, chapter, rid="r1", hour=10):
        cid = chapter["chapter_id"]
        task = self.task("writer", "figure_prompt", hour, [*self.base(), chapter["draft"], self.result], cid, rid)
        prompt = self.put(f"paper/visuals/{rid}.md", "Render the quantitative comparison from the frozen result, using labels and units specified here.")
        slots = [{"slot_id": "comparison", "representation": "figure", "generation_route": "modelviz", "reader_question": "What differs?", "body_anchor": cid, "claim": "Quantitative comparison", "evidence_refs": [self.result]}]
        plan = self.put(f"paper/visuals/{rid}.yaml", {"owner_role": "writer", "chapter_id": cid, "revision_id": rid, "draft": chapter["draft"], "slots": slots})
        revision = {"revision_id": rid, "task_id": task["task_id"], "prompt": prompt, "visual_plan": plan, "prepared_at": f"2026-10-16T{hour:02d}:30:00+08:00", "supersedes": chapter["visual_prompts"][-1]["revision_id"] if chapter["visual_prompts"] else None}
        chapter["visuals_required"] = True
        chapter["visual_prompts"].append(revision)
        return revision

    def framework(self, hour=14):
        task = self.task("writer", "abstract_framework", hour, [*self.base(), *[c["draft"] for c in self.m["writing_chapters"]]])
        self.m["abstract_framework_task_id"] = task["task_id"]
        self.m["abstract_framework"] = self.put("paper/abstract_framework.yaml", {"claims": ["bounded result"], "evidence_refs": [self.result]})
        self.m["abstract_framework_review_packet"] = self.review("M4_ABSTRACT_FRAMEWORK", [self.m["abstract_framework"]], hour+1, review_type="abstract_framework_review")

    def finish(self, figures=False):
        c = self.chapter("modeling", 8)
        revision = self.prompt(c) if figures else None
        self.chapter("evaluation", 12)
        self.framework()
        self.chapter("abstract", 16)
        slots = self.read(revision["visual_plan"])["slots"] if revision else []
        self.m["visual_argument_plan"] = self.put("visual_argument_plan.yaml", {"slots": slots})
        registry = {"figures": []}
        selected = []
        if revision:
            generation = self.task("figure", "generate", 18, [c["draft"], revision["prompt"], revision["visual_plan"]], "modeling", "r1")
            revision["generation_task_id"] = generation["task_id"]
            old = self.read(self.put("figure_fixture.yaml", self.read({"path": "figure_registry.yaml"})))
            figure = old["figures"][0]
            svg = {"path": figure["svg"], "sha256": figure["svg_sha256"]}
            png = {"path": figure["png"], "sha256": figure["png_sha256"]}
            figure.update(chapter_id="modeling", prompt_revision_id="r1", generation_task_id=generation["task_id"], visual_slot_ids=["comparison"], selected_asset=svg)
            registry["figures"] = [figure]
            selected = [svg]
            selection = self.put("paper/selection.yaml", {"chapter_id": "modeling", "revision_id": "r1", "assets": [{"slot_id": "comparison", **svg}]})
            revision["figure_selection"] = selection
            revision["figure_selection_review_packet"] = self.review("M4_FIGURE_SELECTION:modeling:r1", [selection, svg, png], 19)
        self.m["figure_registry"] = self.put("figure_registry.yaml", registry)
        drafts = [c["draft"] for c in self.m["writing_chapters"]]
        integration = self.task("writer", "write", 20, [*self.base(), *drafts, self.m["abstract_framework"], self.m["visual_argument_plan"], self.m["figure_registry"], *selected])
        self.m["integration_task_id"] = integration["task_id"]
        self.m["final_manuscript"] = self.put("paper/final.tex", "Complete approved manuscript and integrated figures.")
        checks = [{"id": k, "status": "PASS"} for k in PROSE_CHECKS | {"abstract_contract", "whole_paper_final"}]
        self.m["final_review_packet"] = self.review("M4_FINAL_PAPER", [self.m["final_manuscript"], self.m["paper_pdf"], *drafts, self.m["figure_registry"], self.m["visual_argument_plan"]], 21, review_type="paper_final_review", reviewer_skill="论文辅助", checks=checks)
        self.skill(self.m["final_review_packet"])
        self.m["skill_invocations"].extend({"skill": s, "status": "completed", "evidence_ref": self.evidence["path"], "evidence_sha256": self.evidence["sha256"]} for s in ["academic-writing", "mathmodel-latex-skill", *(["scipilot-figure-skill", "modelviz"] if figures else [])])
        self.m.update(status="approved", writing_started=True)
        refs = [self.m[k] for k in checker.NODE_ARTIFACTS["M4"]]
        self.m["review_packet"] = self.review("M4", refs, 22)
        return c, revision

    def check(self, final=False):
        self.save()
        return checker.check(self.root, through="M4") if final else checker.check(self.root, preflight_draft=True)


class ChapterParallelTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.f = ChapterFixture(Path(directory.name))

    def test_admission_without_figures_is_read_only(self):
        self.f.save()
        path = self.f.root / ".contest/mathorcup_control.yaml"
        before = path.read_bytes()
        self.assertEqual(self.f.check()["status"], "PASS")
        self.assertEqual(path.read_bytes(), before)

    def test_next_chapter_with_pending_figure(self):
        chapter = self.f.chapter("modeling", 8)
        self.f.prompt(chapter)
        self.f.chapter("evaluation", 12)
        self.assertEqual(self.f.check()["status"], "PASS", self.f.check())

    def test_next_chapter_requires_previous_approval(self):
        self.f.chapter("modeling", 8, approve=False)
        self.f.chapter("evaluation", 12)
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_prompt_requires_chapter_approval(self):
        c = self.f.chapter("modeling", 8, approve=False)
        self.f.prompt(c)
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_graphic_revision_keeps_chapter_approval(self):
        c = self.f.chapter("modeling", 8)
        self.f.prompt(c)
        before = copy.deepcopy(self.f.log["approvals"][-1])
        self.f.chapter("evaluation", 12)
        self.f.prompt(c, "r2", 14)
        self.assertIn(before, self.f.log["approvals"])
        self.assertEqual(self.f.check()["status"], "PASS", self.f.check())

    def test_framework_before_abstract_is_valid_intermediate_state(self):
        self.f.chapter("modeling", 8)
        self.f.chapter("evaluation", 12)
        self.f.framework()
        self.assertEqual(self.f.check()["status"], "PASS", self.f.check())

    def test_final_no_figure_workflow(self):
        self.f.finish()
        self.assertEqual(self.f.check(final=True)["status"], "PASS", self.f.check(final=True))

    def test_final_with_late_figure_workflow(self):
        self.f.finish(figures=True)
        self.assertEqual(self.f.check(final=True)["status"], "PASS", self.f.check(final=True))

    def test_missing_independent_m3_validation_blocks_admission(self):
        self.f.control["nodes"]["M3"]["independent_validation"] = None
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_approved_prose_hash_drift_is_rejected(self):
        chapter = self.f.chapter("modeling", 8)
        (self.f.root / chapter["draft"]["path"]).write_text("Changed", encoding="utf-8")
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_empty_slot_plan_is_rejected(self):
        chapter = self.f.chapter("modeling", 8)
        prompt = self.f.prompt(chapter)
        plan = self.f.read(prompt["visual_plan"])
        plan["slots"] = []
        prompt["visual_plan"] = self.f.put(prompt["visual_plan"]["path"], plan)
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_final_requires_every_chapter(self):
        self.f.chapter("modeling", 8)
        self.assertNotEqual(self.f.check(final=True)["status"], "PASS")

    def test_prompt_card_requires_approved_prose(self):
        c = self.f.chapter("modeling", 8)
        p = self.f.prompt(c)
        record = next(r for r in self.f.control["dispatch_records"] if r["task_id"] == p["task_id"])
        card = self.f.read({"path": record["task_card"]})
        card["inputs"].remove(c["draft"])
        record["task_card_sha256"] = self.f.put(record["task_card"], card)["sha256"]
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_approval_must_follow_completion_strictly(self):
        c = self.f.chapter("modeling", 8)
        self.f.log["approvals"][-1]["approved_at"] = c["draft_completed_at"]
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_quality_review_requires_actual_skill_evidence(self):
        self.f.chapter("modeling", 8)
        self.f.m["skill_invocations"] = []
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_print_order_cannot_be_used_as_writing_order(self):
        plan = self.f.read(self.f.m["paper_argument_blueprint"])
        plan["global"]["writing_order"] = plan["global"]["chapter_order"]
        self.f.m["paper_argument_blueprint"] = self.f.put("paper_argument_blueprint.yaml", plan)
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_no_early_abstract_framework(self):
        self.f.chapter("modeling", 8)
        self.f.framework(10)
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_latest_rejection_cannot_reuse_old_approval(self):
        self.f.chapter("modeling", 8)
        self.f.log["approvals"].append({"gate": "M4_CHAPTER:modeling", "decision": "reject", "approved_by": "user"})
        self.f.chapter("evaluation", 12)
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_final_cannot_reuse_old_generation_after_prompt_revision(self):
        c, _ = self.f.finish(figures=True)
        self.f.prompt(c, "r2", 14)
        self.assertEqual(self.f.check(final=True)["status"], "BLOCK")

    def test_graphics_approval_does_not_replace_chapter_approval(self):
        self.f.finish(figures=True)
        self.f.log["approvals"] = [a for a in self.f.log["approvals"] if a["gate"] != "M4_CHAPTER:modeling"]
        self.assertEqual(self.f.check(final=True)["status"], "BLOCK")

    def test_current_writer_cannot_hide_an_unbound_task(self):
        self.f.chapter("modeling", 8)
        self.f.task("writer", "draft", 10, [*self.f.base(), self.f.result], "evaluation")
        self.assertEqual(self.f.check()["status"], "BLOCK")

    def test_multiple_unapproved_retries_preserve_actual_history(self):
        chapter = self.f.chapter("modeling", 8)
        first = self.f.task("writer", "draft", 7, [*self.f.base(), self.f.result], "modeling")
        second = self.f.task("writer", "draft", 7, [*self.f.base(), self.f.result], "modeling")
        first.update(called_at="2026-10-16T07:10:00+08:00", superseded_by=second["task_id"], superseded_reason="Revise unapproved argument")
        second.update(called_at="2026-10-16T07:20:00+08:00", superseded_by=chapter["task_id"], superseded_reason="Complete chapter revision")
        self.assertEqual(self.f.check()["status"], "PASS", self.f.check())

    def test_cross_chapter_retry_cannot_hide_old_dispatch(self):
        chapter = self.f.chapter("modeling", 8)
        old = self.f.task("writer", "draft", 7, [*self.f.base(), self.f.result], "evaluation")
        old.update(called_at="2026-10-16T07:10:00+08:00", superseded_by=chapter["task_id"], superseded_reason="Invalid cross-chapter retry")
        self.assertEqual(self.f.check()["status"], "BLOCK")
