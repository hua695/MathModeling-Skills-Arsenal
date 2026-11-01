import copy
import hashlib
import importlib
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


class ChapterParallelTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.module = importlib.import_module("harness_chapter_workflow")
        self.control = {"visual_workflow": "chapter_parallel", "agent_instances": {"H8": {"agent_instance_id": "writer"}},
                        "agent_runtime_routes": {"H8": {"model": "writer-model", "reasoning_effort": "high"}},
                        "nodes": {"H7": {"status": "draft"}, "H8": {"status": "not_started"}}, "dispatch_records": []}
        self.log = {"approvals": [{"gate": "H6", "decision": "approved", "timestamp": self.time(1)}]}
        self.plan_data = {"chapter_order": ["abstract", "analysis", "Q1"], "writing_order": ["Q1", "analysis", "abstract"],
                          "central_thesis": "A frozen unified model answers the task", "reader_journey": ["Model", "Interpret", "Conclude"],
                          "chapters": [{"chapter_id": "Q1", "kind": "modeling", "depends_on": []},
                                       {"chapter_id": "analysis", "kind": "analysis", "depends_on": ["Q1"]},
                                       {"chapter_id": "abstract", "kind": "abstract", "depends_on": ["analysis"]}]}
        source = self.put("results/frozen.yaml", {"result": 1})
        for chapter in self.plan_data["chapters"]:
            chapter.update(reader_question="What does this chapter establish?", expected_answer="A bounded evidence-backed answer", evidence_refs=[source])
        self.plan = self.put("paper/plan.yaml", self.plan_data)
        self.prep = {"writing_plan": self.plan, "plan_review_packet": self.approve("H7_WRITING_PLAN", [self.plan], 2), "chapters": []}
        self.control["nodes"]["H7"]["writer_preparation"] = self.prep

    def time(self, hour):
        return f"2026-10-30T{hour:02d}:00:00+08:00"

    def put(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False) if isinstance(value, dict) else value, encoding="utf-8")
        return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def approve(self, gate, refs, hour):
        packet = self.put(f".contest/reviews/{gate.replace(':', '_')}.yaml", {"node_id": gate,
            "requested_decision": "approve", "important_artifacts": refs, "checks": [{"status": "PASS"}]})
        self.log["approvals"].append({"gate": gate, "decision": "approved", "timestamp": self.time(hour),
            "artifact_digests": {r["path"]: r["sha256"] for r in [packet, *refs]}})
        return packet["path"]

    def dispatch(self, task, chapter, phase, hour):
        science = self.put("results/science.yaml", {"frozen": True})
        inputs = [self.plan, science]
        definition = next(c for c in self.plan_data["chapters"] if c["chapter_id"] == chapter)
        inputs.extend(definition["evidence_refs"])
        if phase == "H8_figure_prompt":
            inputs.extend(c["draft"] for c in self.prep["chapters"] if c["chapter_id"] == chapter)
        card = self.put(f".contest/task_cards/{task}.yaml", {"task_id": task, "node_id": "H8", "owner_role": "论文 agent",
            "model": "writer-model", "reasoning_effort": "high", "inputs": inputs,
            "scope": {"phase": phase, "chapter_id": chapter}})
        record = {"task_id": task, "node_id": "H8", "owner_role": "论文 agent", "dispatch_kind": "writer_preparation",
            "agent_instance_id": "writer", "model": "writer-model", "reasoning_effort": "high", "dispatched_at": self.time(hour),
            "task_card_path": card["path"], "task_card_sha256": card["sha256"],
            "spawn_receipt": {"task_id": task, "agent_instance_id": "writer", "task_card_sha256": card["sha256"]}}
        self.control["dispatch_records"].append(record)
        return record

    def chapter(self, name="Q1", start=3, approved=True):
        record = self.dispatch(f"draft-{name}", name, "H8_chapter_draft", start)
        draft = self.put(f"paper/drafts/{name}.tex", f"Complete evidence-based argument for {name}.")
        report = self.put(f"paper/reviews/{name}.yaml", {"draft_sha256": draft["sha256"], "status": "ready",
            "checks": {k: "PASS" for k in ("problem_answer", "model_and_derivation", "result_comparison", "interpretation", "continuity", "evidence_provenance")}})
        chapter = {"chapter_id": name, "task_id": record["task_id"], "draft": draft, "quality_review": report,
                   "draft_completed_at": self.time(start + 1), "visual_prompts": []}
        self.prep["chapters"].append(chapter)
        if approved:
            chapter["review_packet"] = self.approve(f"H7_CHAPTER:{name}", [draft, report], start + 2)
        return chapter

    def prompt(self, chapter, revision="r1", start=6):
        name = chapter["chapter_id"]
        task = f"prompt-{name}-{revision}"
        self.dispatch(task, name, "H8_figure_prompt", start)
        plan = self.put(f"paper/visuals/{name}_{revision}.yaml", {"chapter_id": name, "revision_id": revision,
            "draft": chapter["draft"], "slots": [{"slot_id": f"{name}-result", "representation": "figure", "generation_route": "modelviz"}]})
        prompt = self.put(f"paper/prompts/{name}_{revision}.md", "Reader question, frozen data, chapter context, required comparison and placement.")
        result = {"revision_id": revision, "task_id": task, "prompt": prompt, "visual_plan": plan,
                  "prepared_at": self.time(start + 1), "supersedes": chapter["visual_prompts"][-1]["revision_id"] if chapter["visual_prompts"] else None}
        chapter["visual_prompts"].append(result)
        return result

    def validate(self, admission=True):
        missing, errors = [], []
        self.module.validate(self.root, self.control, self.log, missing, errors, admission_only=admission)
        return missing, errors

    def test_admission_needs_no_draft_or_figures(self):
        self.assertEqual(self.validate(), ([], []))

    def test_approved_core_chapter_can_be_followed_while_figure_is_missing(self):
        self.prompt(self.chapter())
        self.chapter("analysis", start=8)
        self.assertEqual(self.validate(), ([], []))

    def test_next_chapter_cannot_start_without_previous_approval(self):
        self.chapter(approved=False)
        self.chapter("analysis", start=8)
        self.assertTrue(self.validate()[1])

    def test_prompt_cannot_precede_chapter_approval(self):
        chapter = self.chapter()
        self.prompt(chapter, start=4)
        self.assertTrue(self.validate()[1])

    def test_graphic_repair_does_not_revoke_chapter_approval(self):
        chapter = self.chapter()
        self.prompt(chapter)
        self.chapter("analysis", start=8)
        self.prompt(chapter, revision="r2", start=12)
        self.assertEqual(self.validate(), ([], []))

    def test_changed_approved_prose_is_rejected(self):
        chapter = self.chapter()
        (self.root / chapter["draft"]["path"]).write_text("changed", encoding="utf-8")
        self.assertTrue(any(self.validate()))

    def test_print_order_can_differ_from_writing_order(self):
        self.assertEqual(self.validate(), ([], []))

    def test_analysis_before_modeling_is_rejected(self):
        self.plan_data["writing_order"] = ["analysis", "Q1", "abstract"]
        self.prep["writing_plan"] = self.put("paper/plan.yaml", self.plan_data)
        self.assertTrue(any(self.validate()))

    def test_abstract_cannot_be_drafted_during_figure_preparation(self):
        self.chapter("abstract")
        self.assertTrue(self.validate()[1])

    def test_quality_review_must_bind_actual_draft(self):
        chapter = self.chapter()
        chapter["quality_review"] = self.put("paper/reviews/Q1.yaml", {"status": "ready", "draft_sha256": "0" * 64, "checks": {}})
        self.assertTrue(any(self.validate()))

    def closed_case(self):
        first = self.chapter()
        p1 = self.prompt(first)
        second = self.chapter("analysis", start=8)
        p2 = self.prompt(second, start=11)
        figures, refs, slots = [], [], []
        for name, prompt in (("Q1", p1), ("analysis", p2)):
            plan = yaml.safe_load((self.root / prompt["visual_plan"]["path"]).read_text(encoding="utf-8"))
            slots.extend(plan["slots"])
            svg = self.put(f"figures/{name}.svg", "<svg/>")
            png = self.put(f"figures/{name}.png", "preview")
            task = f"generate-{name}"
            card = self.put(f".contest/task_cards/{task}.yaml", {"scope": {"phase": "H7_generate", "chapter_id": name,
                "revision_id": "r1", "prompt_sha256": prompt["prompt"]["sha256"],
                "approved_visual_plan_sha256": prompt["visual_plan"]["sha256"]}})
            self.control["dispatch_records"].append({"task_id": task, "node_id": "H7", "task_card_path": card["path"],
                "task_card_sha256": card["sha256"], "dispatched_at": self.time(14)})
            figures.append({"figure_id": name, "chapter_id": name, "prompt_revision_id": "r1", "generation_task_id": task,
                            "svg": svg["path"], "png": png["path"]})
            refs.extend([svg, png])
        registry = self.put("figure_registry.yaml", {"figures": figures})
        aggregate = self.put("visual_argument_plan.yaml", {"slots": slots})
        h7 = self.control["nodes"]["H7"]
        h7.update(status="review_pending", figure_registry=registry["path"], visual_argument_plan=aggregate["path"],
                  figure_selection_review_packet=self.approve("H7_FIGURE_SELECTION", [registry, *refs], 16))

    def test_final_graphic_closure_checks_actual_latest_prompt_versions(self):
        self.closed_case()
        self.assertEqual(self.validate(admission=False), ([], []))

    def test_graphic_repair_can_continue_writing_but_blocks_final_closure_until_done(self):
        self.closed_case()
        self.prompt(self.prep["chapters"][0], revision="r2", start=17)
        self.assertEqual(self.validate(admission=True), ([], []))
        self.assertTrue(any(self.validate(admission=False)))

    def test_unrequested_global_slot_is_rejected_at_closure(self):
        self.closed_case()
        self.put("visual_argument_plan.yaml", {"slots": [{"slot_id": "unrequested"}]})
        self.assertTrue(any(self.validate(admission=False)))

    def test_rejected_chapter_can_be_reworked_before_approval_without_losing_dispatch_history(self):
        old = self.dispatch("draft-Q1-rejected", "Q1", "H8_chapter_draft", 3)
        chapter = self.chapter(start=4)
        old.update(superseded_by=chapter["task_id"], superseded_reason="User requested a clearer derivation before approval")
        self.assertEqual(self.validate(), ([], []))

    def test_rework_cannot_hide_another_chapters_dispatch(self):
        old = self.dispatch("unbound-analysis", "analysis", "H8_chapter_draft", 3)
        chapter = self.chapter(start=4)
        old.update(superseded_by=chapter["task_id"], superseded_reason="Incorrectly relabelled")
        self.assertTrue(any(self.validate()))

    def test_multiple_rework_rounds_can_resolve_to_one_approved_chapter(self):
        first = self.dispatch("draft-Q1-v1", "Q1", "H8_chapter_draft", 3)
        second = self.dispatch("draft-Q1-v2", "Q1", "H8_chapter_draft", 4)
        chapter = self.chapter(start=5)
        first.update(superseded_by=second["task_id"], superseded_reason="First requested revision")
        second.update(superseded_by=chapter["task_id"], superseded_reason="Second requested revision")
        self.assertEqual(self.validate(), ([], []))
