#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H0-H9 state machine and H8 writing plan hardening tests.

Covers status transition validation, through-rule approval chains, and
H8 writing-start gate conditions.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_harness_control as checker  # noqa: E402


def _make_base_control() -> dict:
    return {
        "active_mode": "full-contest-harness",
        "roles": {
            "主 agent": "main",
            "解题 agent": "solver",
            "验证 agent": "verifier",
            "图表 agent": "figure",
            "论文 agent": "writer",
        },
        "agent_runtime_routes": {
            "H1": {"model": "gpt-5.6-terra", "reasoning_effort": "medium"},
            "H5": {"model": "gpt-5.6-terra", "reasoning_effort": "medium"},
            "H6": {"model": "gpt-5.6-terra", "reasoning_effort": "medium"},
            "H7": {"model": "gpt-5.6-terra", "reasoning_effort": "medium"},
            "H8": {"model": "gpt-5.6-terra", "reasoning_effort": "medium"},
        },
        "bootstrap": {
            "required_skill": "superpowers:using-superpowers",
            "invocations": [{
                "skill": "superpowers:using-superpowers",
                "task_id": "sp-1",
                "completed": True,
                "status": "completed",
            }],
        },
        "nodes": {},
    }


def _make_node(node_id: str, status: str, **kwargs) -> dict:
    node = {
        "status": status,
        "owner_role": checker.ROLE_BY_NODE[node_id],
        "agent_policy": "required" if node_id in checker.AGENT_NODES else "controller_only",
        "support_agent_policy": "none",
    }
    node.update(kwargs)
    return node


class StatusTransitionTests(unittest.TestCase):
    def test_rejects_invalid_status_transition(self):
        """not_started cannot jump directly to approved."""
        transitions = checker.STATUS_TRANSITIONS
        self.assertNotIn("approved", transitions.get("not_started", set()))

    def test_accepts_valid_status_transitions(self):
        transitions = checker.STATUS_TRANSITIONS
        self.assertIn("draft", transitions["not_started"])
        self.assertIn("review_pending", transitions["draft"])
        self.assertIn("approved", transitions["review_pending"])
        self.assertIn("evidence_gap", transitions["review_pending"])
        self.assertIn("draft", transitions["evidence_gap"])
        self.assertIn("frozen", transitions["approved"])
        self.assertIn("stale", transitions["frozen"])
        self.assertIn("review_pending", transitions["stale"])

    def test_validate_transition_rejects_illegal_jump(self):
        ok, msg = checker.validate_status_transition("not_started", "approved")
        self.assertFalse(ok)
        self.assertIn("not_started", msg)

    def test_validate_transition_accepts_legal_step(self):
        ok, _ = checker.validate_status_transition("draft", "review_pending")
        self.assertTrue(ok)

    def test_node_statuses_include_evidence_gap_and_stale(self):
        self.assertIn("evidence_gap", checker.NODE_STATUSES)
        self.assertIn("stale", checker.NODE_STATUSES)


class ThroughRuleTests(unittest.TestCase):
    def test_rejects_through_ahead_of_approval(self):
        """H5 at review_pending without review packet blocks through=H6."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".contest").mkdir()
            control = _make_base_control()
            control["nodes"]["H1"] = _make_node("H1", "approved")
            control["nodes"]["H2"] = _make_node("H2", "approved")
            control["nodes"]["H3"] = _make_node("H3", "approved")
            control["nodes"]["H5"] = _make_node("H5", "approved")  # H4已并入H5
            control["nodes"]["H5"] = _make_node("H5", "review_pending")
            (root / ".contest" / "harness_control.yaml").write_text(
                yaml.safe_dump(control), encoding="utf-8")
            (root / ".contest" / "approval_log.yaml").write_text(
                yaml.safe_dump({"approvals": []}), encoding="utf-8")
            report = checker.check_harness_control(root, through="H6")
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("review" in item.lower() or "批准" in item or "packet" in item.lower()
                            for item in report["failures"] + report["missing"]),
                        f"Expected review/packet failure, got: {report['failures']} {report['missing']}")

    def test_rejects_skipped_harness_node(self):
        """H5 not_started blocks through=H6."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".contest").mkdir()
            control = _make_base_control()
            control["nodes"]["H1"] = _make_node("H1", "approved")
            control["nodes"]["H2"] = _make_node("H2", "approved")
            control["nodes"]["H3"] = _make_node("H3", "approved")
            control["nodes"]["H5"] = _make_node("H5", "approved")  # H4已并入H5
            control["nodes"]["H5"] = _make_node("H5", "not_started")
            (root / ".contest" / "harness_control.yaml").write_text(
                yaml.safe_dump(control), encoding="utf-8")
            (root / ".contest" / "approval_log.yaml").write_text(
                yaml.safe_dump({"approvals": []}), encoding="utf-8")
            report = checker.check_harness_control(root, through="H6")
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("not_started" in item for item in report["failures"]),
                        f"Expected not_started failure, got: {report['failures']}")


class H8WritingPlanTests(unittest.TestCase):
    def test_h8_writing_started_requires_approved_plan_status(self):
        """writing_started=true requires writing_plan.status=approved."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".contest").mkdir()
            (root / "paper").mkdir()
            plan = {
                "schema_version": "1.0",
                "status": "review_pending",  # not approved
                "sections": [{"section_id": "s1", "subproblem_id": "Q1"}],
            }
            (root / "writing_plan.yaml").write_text(yaml.safe_dump(plan), encoding="utf-8")
            control = _make_base_control()
            for nid in ["H1", "H2", "H3", "H5", "H6", "H7"]:  # H4已并入H5，跳过
                control["nodes"][nid] = _make_node(nid, "approved")
            control["nodes"]["H8"] = _make_node("H8", "draft",
                writing_started=True,
                writing_plan="writing_plan.yaml",
                writing_plan_sha256="a" * 64)
            (root / ".contest" / "harness_control.yaml").write_text(
                yaml.safe_dump(control), encoding="utf-8")
            (root / ".contest" / "approval_log.yaml").write_text(
                yaml.safe_dump({"approvals": []}), encoding="utf-8")
            report = checker.check_harness_control(root, through="H8")
        self.assertTrue(any("writing_plan" in item and ("approved" in item.lower() or "状态" in item)
                            for item in report["failures"]),
                        f"Expected writing_plan status failure, got: {report['failures']}")

    def test_h8_writing_plan_requires_sections(self):
        """writing_plan must contain non-empty sections list."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".contest").mkdir()
            plan = {"schema_version": "1.0", "status": "approved", "sections": []}
            (root / "writing_plan.yaml").write_text(yaml.safe_dump(plan), encoding="utf-8")
            failures, missing = [], []
            checker._validate_h8_writing_plan(root, {
                "writing_started": True,
                "writing_plan": "writing_plan.yaml",
            }, missing, failures)
        self.assertTrue(any("sections" in item for item in failures),
                        f"Expected sections failure, got: {failures}")


if __name__ == "__main__":
    unittest.main()
