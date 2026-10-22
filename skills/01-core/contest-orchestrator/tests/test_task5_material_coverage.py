#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 5 material readiness, gap matrix, and claim coverage hardening tests.

Covers gap matrix priority field validation and claim coverage structure.
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


class GapMatrixPriorityTests(unittest.TestCase):
    def test_gap_matrix_rejects_missing_priority(self):
        """evidence_gap_matrix entries must include non-empty priority."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "readiness.yaml").write_text(yaml.safe_dump({
                "status": "PAUSE",
                "prepared_by": "H5",
                "verified_by": "H6",
                "verification_agent_instance_id": "h6-01",
                "target_length": {"whole_pdf_recommended_range": [35, 51]},
                "subproblems": [{"id": "Q1", "materials": {}}],
                "claim_requirements": [],
            }), encoding="utf-8")
            (root / "gap_matrix.yaml").write_text(yaml.safe_dump({
                "schema_version": "1.0",
                "readiness_sha256": checker.digest(root / "readiness.yaml"),
                "gaps": [{
                    "gap_id": "GAP-Q1-validation",
                    "subproblem_id": "Q1",
                    "requirement": "validation",
                    "responsible_node": "H6",
                    "required_artifact": "validation/q1.yaml",
                    "acceptance_criteria": "包含独立验证",
                    "return_to": "H6",
                    # missing priority
                }],
            }), encoding="utf-8")
            node = {"evidence_gap_matrix": "gap_matrix.yaml"}
            gaps = [{"subproblem_id": "Q1", "requirement": "validation", "responsible_node": "H6"}]
            failures, missing = [], []
            checker._validate_gap_matrix(root, node, root / "readiness.yaml", gaps, missing, failures)
        self.assertTrue(any("priority" in item.lower() for item in failures),
                        f"Expected priority failure, got: {failures}")

    def test_gap_matrix_accepts_valid_priority(self):
        """evidence_gap_matrix with valid priority passes priority check."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "readiness.yaml").write_text(yaml.safe_dump({
                "status": "PAUSE",
                "prepared_by": "H5",
                "verified_by": "H6",
                "verification_agent_instance_id": "h6-01",
                "target_length": {"whole_pdf_recommended_range": [35, 51]},
                "subproblems": [{"id": "Q1", "materials": {}}],
                "claim_requirements": [],
            }), encoding="utf-8")
            (root / "gap_matrix.yaml").write_text(yaml.safe_dump({
                "schema_version": "1.0",
                "readiness_sha256": checker.digest(root / "readiness.yaml"),
                "gaps": [{
                    "gap_id": "GAP-Q1-validation",
                    "subproblem_id": "Q1",
                    "requirement": "validation",
                    "responsible_node": "H6",
                    "required_artifact": "validation/q1.yaml",
                    "acceptance_criteria": "包含独立验证",
                    "return_to": "H6",
                    "priority": "P1",
                }],
            }), encoding="utf-8")
            node = {"evidence_gap_matrix": "gap_matrix.yaml"}
            gaps = [{"subproblem_id": "Q1", "requirement": "validation", "responsible_node": "H6"}]
            failures, missing = [], []
            checker._validate_gap_matrix(root, node, root / "readiness.yaml", gaps, missing, failures)
        priority_failures = [f for f in failures if "priority" in f.lower()]
        self.assertEqual(priority_failures, [], f"Unexpected priority failure: {priority_failures}")


class MaterialFieldCompletenessTests(unittest.TestCase):
    def test_material_fields_cover_all_required(self):
        """MATERIAL_FIELDS must contain all 10 required material categories."""
        expected = {
            "problem_mapping", "assumptions", "symbols", "derivation",
            "algorithm_and_parameters", "quantified_results", "validation",
            "figures_or_tables", "literature_use", "conclusion_and_boundary",
        }
        self.assertEqual(set(checker.MATERIAL_FIELDS), expected)

    def test_material_owner_covers_all_fields(self):
        """Every material field must have a responsible node."""
        for field in checker.MATERIAL_FIELDS:
            self.assertIn(field, checker.MATERIAL_OWNER, f"Missing owner for {field}")
            self.assertIn(checker.MATERIAL_OWNER[field], {"H5", "H6", "H7"})


if __name__ == "__main__":
    unittest.main()
