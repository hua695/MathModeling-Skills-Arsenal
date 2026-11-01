import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("harness_writer_checker", ROOT / "scripts/check_harness_control.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class WriterPreparationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.control = checker.default_control()
        self.control["visual_workflow"] = "writer_first_draft"
        self.control["agent_instances"]["H8"] = {"agent_instance_id": "writer-1"}
        self.log = {"approvals": []}
        self.plan = self.put("paper/writing_plan.yaml", {"sections": ["Q1"]})
        packet = self.review("H7_WRITING_PLAN", [self.plan], "07:00:00")
        self.prep = {"writing_plan": self.plan, "plan_review_packet": packet}
        self.control["nodes"]["H7"]["writer_preparation"] = self.prep
        self.log["approvals"].append({"gate": "H6", "decision": "approved", "timestamp": "2026-10-30T06:00:00+08:00"})

    def put(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(value, allow_unicode=True) if isinstance(value, dict) else value, encoding="utf-8")
        return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def review(self, gate, refs, time):
        packet = self.put(f".contest/reviews/{gate}.yaml", {"node_id": gate, "summary": "Review",
            "important_artifacts": refs, "checks": [{"name": "evidence", "status": "PASS"}],
            "requested_decision": "approve", "proposed_next_node": "H7"})
        self.log["approvals"].append({"gate": gate, "decision": "approved", "timestamp": f"2026-10-30T{time}+08:00",
            "artifact_digests": {r["path"]: r["sha256"] for r in [packet, *refs]}})
        return packet["path"]

    def draft(self):
        source = self.put("results/scientific.yaml", {"verified": True})
        card = self.put(".contest/task_cards/draft.yaml", {"task_id": "draft-1", "node_id": "H8",
            "owner_role": "论文 agent", "model": "gpt-5.6-sol", "reasoning_effort": "high",
            "scope": {"phase": "H8_draft_preparation"}, "inputs": [self.plan, source]})
        self.control["dispatch_records"].append({"task_id": "draft-1", "node_id": "H8", "owner_role": "论文 agent",
            "dispatch_kind": "writer_preparation", "agent_instance_id": "writer-1",
            "model": "gpt-5.6-sol", "reasoning_effort": "high", "task_card_path": card["path"],
            "task_card_sha256": card["sha256"], "dispatched_at": "2026-10-30T08:00:00+08:00",
            "spawn_receipt": {"agent_instance_id": "writer-1", "task_id": "draft-1", "task_card_sha256": card["sha256"]}})
        self.prep.update(task_id="draft-1", draft=self.put("paper/draft.tex", "Frozen scientific result; figure placeholder."),
                         draft_completed_at="2026-10-30T09:00:00+08:00")
        visual = self.put("visual_argument_plan.yaml", {"prepared_by_role": "论文 agent", "draft": self.prep["draft"],
            "prepared_at": "2026-10-30T09:10:00+08:00"})
        self.control["nodes"]["H7"]["visual_argument_plan"] = visual["path"]
        self.review("H7_VISUAL_PLAN", [visual, self.prep["draft"]], "10:00:00")

    def validate(self, admission=False):
        missing, failures = [], []
        checker._validate_writer_preparation(self.root, self.control, self.log, missing, failures, admission_only=admission)
        return missing, failures

    def test_admission_before_graphics_and_draft_is_allowed(self):
        self.assertEqual(self.validate(admission=True), ([], []))

    def test_writer_draft_and_bound_requirements_pass(self):
        self.draft()
        self.assertEqual(self.validate(), ([], []))

    def test_missing_h6_approval_blocks_draft(self):
        self.log["approvals"] = [a for a in self.log["approvals"] if a["gate"] != "H6"]
        self.assertTrue(any(self.validate(admission=True)))

    def test_unapproved_writing_plan_cannot_admit_draft(self):
        self.log["approvals"] = [a for a in self.log["approvals"] if a["gate"] != "H7_WRITING_PLAN"]
        self.assertTrue(any(self.validate(admission=True)))

    def test_unregistered_writer_is_rejected(self):
        self.draft()
        self.control["dispatch_records"][0]["agent_instance_id"] = "other"
        self.assertTrue(self.validate()[1])

    def test_early_draft_is_rejected(self):
        self.draft()
        self.control["dispatch_records"][0]["dispatched_at"] = "2026-10-30T05:00:00+08:00"
        self.assertTrue(self.validate()[1])

    def test_visual_approval_cannot_predate_requirements(self):
        self.draft()
        self.log["approvals"][-1]["timestamp"] = "2026-10-30T08:00:00+08:00"
        self.assertTrue(self.validate()[1])

    def test_stale_draft_is_rejected(self):
        self.draft()
        (self.root / self.prep["draft"]["path"]).write_text("changed", encoding="utf-8")
        self.assertTrue(any(self.validate()))

    def test_graphics_before_draft_completion_are_rejected(self):
        self.draft()
        self.control["dispatch_records"].append({"node_id": "H7", "dispatched_at": "2026-10-30T08:30:00+08:00"})
        self.assertTrue(self.validate()[1])

    def test_selected_assets_need_current_human_approval(self):
        self.draft()
        svg = self.put("figures/f1.svg", "<svg/>")
        png = self.put("figures/f1.png", "png fixture")
        registry = self.put("figure_registry.yaml", {"figures": [{"svg": svg["path"], "png": png["path"]}]})
        h7 = self.control["nodes"]["H7"]
        h7["figure_registry"] = registry["path"]
        self.control["dispatch_records"].append({"node_id": "H7", "dispatched_at": "2026-10-30T11:00:00+08:00"})
        self.assertTrue(any(self.validate()))
        h7["figure_selection_review_packet"] = self.review("H7_FIGURE_SELECTION", [registry, svg, png], "12:00:00")
        self.assertEqual(self.validate(), ([], []))
        (self.root / svg["path"]).write_text("<svg>new</svg>", encoding="utf-8")
        self.assertTrue(any(self.validate()))

    def test_h8_approval_does_not_replace_h6_approval(self):
        self.log["approvals"] = [a for a in self.log["approvals"] if a["gate"] != "H6"]
        self.log["approvals"].append({"gate": "H8", "decision": "approved", "timestamp": "2026-10-30T06:00:00+08:00"})
        self.assertTrue(any(self.validate(admission=True)))

    def test_preparation_cannot_be_used_as_formal_h8_task(self):
        self.draft()
        self.control["nodes"]["H8"]["task_card"] = self.control["dispatch_records"][0]["task_card_path"]
        self.assertTrue(self.validate()[1])

    def test_public_draft_admission_keeps_full_h6_gates_and_is_read_only(self):
        control = self.put(".contest/harness_control.yaml", self.control)
        log = self.put(".contest/approval_log.yaml", self.log)
        before = [(self.root / ref["path"]).read_bytes() for ref in (control, log)]
        report = checker.check_harness_control(self.root, preflight_draft=True)
        self.assertNotEqual(report["status"], "PASS")  # a plan cannot replace missing bootstrap/H6 evidence
        self.assertEqual(report["through"], "H7-draft")
        self.assertEqual([(self.root / ref["path"]).read_bytes() for ref in (control, log)], before)
