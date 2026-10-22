#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H1 input source and cross-question interface hardening tests.

Covers H1 original problem file hash verification, input/output artifact
traceability, and H5/H6 instance independence.
"""
import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_harness_control as checker  # noqa: E402


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class H1InputSourceTests(unittest.TestCase):
    def test_h1_rejects_missing_original_problem_file(self):
        """H1 must register original problem file path; missing file blocks."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "problem_statement.md").write_text("# 题目", encoding="utf-8")
            (root / "unified_problem_package.yaml").write_text("subproblems: [Q1]", encoding="utf-8")
            node = {
                "status": "draft",
                "problem_statement": "problem_statement.md",
                "unified_problem_package": "unified_problem_package.yaml",
                # missing original_problem_file
            }
            failures, missing = [], []
            checker._validate_h1_problem_statement(root, node, missing, failures)
        self.assertTrue(any("original" in item.lower() or "原始题面" in item or "题面" in item
                            for item in missing + failures),
                        f"Expected original problem file failure, got: {missing} {failures}")

    def test_h1_rejects_mismatched_input_hash(self):
        """H1 input sha256 must match actual file content."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            problem_content = "# 原始题面\n".encode("utf-8")
            (root / "original_problem.pdf").write_bytes(problem_content)
            (root / "problem_statement.md").write_text("# 题目", encoding="utf-8")
            (root / "unified_problem_package.yaml").write_text("subproblems: [Q1]", encoding="utf-8")
            node = {
                "status": "draft",
                "problem_statement": "problem_statement.md",
                "unified_problem_package": "unified_problem_package.yaml",
                "original_problem_file": "original_problem.pdf",
                "original_problem_sha256": "a" * 64,  # wrong hash
            }
            failures, missing = [], []
            checker._validate_h1_problem_statement(root, node, missing, failures)
        self.assertTrue(any("sha256" in item.lower() or "哈希" in item or "hash" in item.lower()
                            for item in failures),
                        f"Expected hash mismatch failure, got: {failures}")

    def test_h1_accepts_matching_input_hash(self):
        """H1 with correct original problem file and hash passes input checks."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            problem_content = "# 原始题面\n".encode("utf-8")
            (root / "original_problem.pdf").write_bytes(problem_content)
            (root / "problem_statement.md").write_text("# 题目", encoding="utf-8")
            (root / "unified_problem_package.yaml").write_text("subproblems: [Q1]", encoding="utf-8")
            node = {
                "status": "draft",
                "problem_statement": "problem_statement.md",
                "unified_problem_package": "unified_problem_package.yaml",
                "original_problem_file": "original_problem.pdf",
                "original_problem_sha256": _sha256(problem_content),
            }
            failures, missing = [], []
            checker._validate_h1_problem_statement(root, node, missing, failures)
        hash_failures = [f for f in failures if "sha256" in f.lower() or "哈希" in f]
        original_missing = [m for m in missing if "original" in m.lower() or "原始题面" in m]
        self.assertEqual(hash_failures, [], f"Unexpected hash failure: {hash_failures}")
        self.assertEqual(original_missing, [], f"Unexpected original missing: {original_missing}")


class H5H6InstanceTests(unittest.TestCase):
    def test_h6_rejects_same_instance_as_h5(self):
        """H6 verification instance must differ from H5 solver instance."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".contest").mkdir()
            (root / "global_interface_check.yaml").write_text(yaml.safe_dump({
                "schema_version": "1.0",
                "status": "PASS",
                "verified_by": "H6",
                "verification_agent_instance_id": "agent-same-01",
                "task_card_path": ".contest/task_cards/H6.yaml",
                "task_card_sha256": "b" * 64,
                "checks": {name: True for name in checker.INTERFACE_CHECKS},
                "issues": [],
                "per_subproblem": [{"subproblem_id": "Q1", "interface_fields": ["x"]}],
            }), encoding="utf-8")
            (root / ".contest" / "task_cards").mkdir(parents=True, exist_ok=True)
            (root / ".contest" / "task_cards" / "H6.yaml").write_text("task_card: H6", encoding="utf-8")
            nodes = {
                "H5": {"agent_instance_id": "agent-same-01", "solver_instance_id": "solver-01"},
                "H6": {"agent_instance_id": "agent-same-01",
                       "global_interface_check": "global_interface_check.yaml"},
            }
            failures, missing = [], []
            checker._validate_h6_interface(root, nodes, {"subproblems": ["Q1"]}, missing, failures)
        self.assertTrue(any("H5" in item and ("相同" in item or "same" in item.lower() or "独立" in item)
                            for item in failures),
                        f"Expected H5/H6 same instance failure, got: {failures}")


if __name__ == "__main__":
    unittest.main()
