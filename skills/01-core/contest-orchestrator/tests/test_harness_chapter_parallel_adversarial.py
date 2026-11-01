"""Adversarial acceptance checks for chapter-parallel Harness controls."""
import unittest

import test_harness_chapter_parallel as base_tests


class ChapterParallelAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.fixture = base_tests.ChapterParallelTests(methodName="runTest")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_prompt_task_must_receive_the_approved_chapter_snapshot(self):
        chapter = self.fixture.chapter()
        self.fixture.prompt(chapter)

        prompt_task = self.fixture.control["dispatch_records"][-1]
        card = self.fixture.root / prompt_task["task_card_path"]
        data = self.fixture.module.yaml.safe_load(card.read_text(encoding="utf-8"))
        data["inputs"] = [item for item in data["inputs"] if item != chapter["draft"]]
        card.write_text(self.fixture.module.yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        prompt_task["task_card_sha256"] = self.fixture.module.hashlib.sha256(card.read_bytes()).hexdigest()
        prompt_task["spawn_receipt"]["task_card_sha256"] = prompt_task["task_card_sha256"]

        _, errors = self.fixture.validate()
        self.assertTrue(errors, "A prompt writer without the approved prose snapshot must be blocked")

    def test_prompt_with_no_figure_slot_is_not_a_self_contained_visual_request(self):
        chapter = self.fixture.chapter()
        prompt = self.fixture.prompt(chapter)
        visual_path = self.fixture.root / prompt["visual_plan"]["path"]
        visual = self.fixture.module.yaml.safe_load(visual_path.read_text(encoding="utf-8"))
        visual["slots"] = []
        visual_path.write_text(self.fixture.module.yaml.safe_dump(visual, allow_unicode=True, sort_keys=False), encoding="utf-8")
        prompt["visual_plan"]["sha256"] = self.fixture.module.hashlib.sha256(visual_path.read_bytes()).hexdigest()

        _, errors = self.fixture.validate()
        self.assertTrue(errors, "A requested figure prompt must define at least one deliverable slot")

    def test_chapter_approval_must_strictly_follow_draft_completion(self):
        chapter = self.fixture.chapter()
        approval = next(item for item in self.fixture.log["approvals"] if item["gate"] == "H7_CHAPTER:Q1")
        approval["timestamp"] = chapter["draft_completed_at"]

        _, errors = self.fixture.validate()
        self.assertTrue(errors, "A same-instant chapter approval cannot prove review of the completed prose")

    def test_rework_chain_cannot_use_a_non_writer_bridge_to_hide_a_dispatch(self):
        old = self.fixture.dispatch("draft-Q1-rejected", "Q1", "H8_chapter_draft", 3)
        bridge = self.fixture.dispatch("non-writer-bridge", "Q1", "H8_chapter_draft", 4)
        chapter = self.fixture.chapter(start=5)
        bridge.update(node_id="H7", dispatch_kind="unrelated", superseded_by=chapter["task_id"])
        old.update(superseded_by=bridge["task_id"], superseded_reason="Requested revision")

        _, errors = self.fixture.validate()
        self.assertTrue(errors, "Every supersession link must itself be a registered H8 writer task")

    def test_h7_closure_must_not_select_an_asset_from_a_superseded_prompt(self):
        q1 = self.fixture.chapter()
        first = self.fixture.prompt(q1, "r1", 6)
        latest = self.fixture.prompt(q1, "r2", 9)
        analysis = self.fixture.chapter("analysis", start=12)
        self.fixture.prompt(analysis, "r1", 15)

        generation_card = self.fixture.put(".contest/task_cards/generate-Q1-r1.yaml", {
            "task_id": "generate-Q1-r1", "node_id": "H7",
            "scope": {"phase": "H7_generate", "chapter_id": "Q1", "revision_id": "r1",
                      "prompt_sha256": first["prompt"]["sha256"],
                      "approved_visual_plan_sha256": first["visual_plan"]["sha256"]},
        })
        self.fixture.control["dispatch_records"].append({
            "task_id": "generate-Q1-r1", "node_id": "H7", "dispatched_at": self.fixture.time(8),
            "task_card_path": generation_card["path"], "task_card_sha256": generation_card["sha256"],
        })
        registry = self.fixture.put("paper/figures/registry.yaml", {"figures": []})
        self.fixture.control["nodes"]["H7"].update({
            "status": "approved", "figure_registry": registry["path"],
            "figure_selection_review_packet": self.fixture.approve("H7_FIGURE_SELECTION", [registry], 20),
        })

        _, errors = self.fixture.validate(admission=False)
        self.assertTrue(errors, "H7 closure must require a selected result generated from the latest prompt revision")
        self.assertNotEqual(first["revision_id"], latest["revision_id"])
