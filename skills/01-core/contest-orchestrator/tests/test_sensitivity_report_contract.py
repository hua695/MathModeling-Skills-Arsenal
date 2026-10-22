#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 6 integration: sensitivity report contract check in check_model_evidence.

Ensures that when a subproblem declares optimization capability, the
sensitivity_report.yaml or robustness_report.yaml exists and has valid format.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_model_evidence as checker  # noqa: E402


class SensitivityReportContractTests(unittest.TestCase):
    def test_optimization_subproblem_requires_sensitivity_report(self):
        """Optimization capability subproblem must have sensitivity or robustness report."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            # Create minimal paper.tex
            (root / "paper.tex").write_text(
                "\\documentclass{article}\n\\begin{document}\n"
                "\\label{subproblem:Q1}\nTest.\n"
                "\\end{document}\n", encoding="utf-8")
            # Create model_contract.yaml with optimization capability
            contract = {
                "schema_version": "2.1",
                "subproblems": [{
                    "id": "Q1",
                    "capabilities": ["optimization"],
                    "evidence": {
                        "decision_variables": {"status": "pass", "text_anchors": ["决策变量"], "source_files": []},
                        "objective": {"status": "pass", "text_anchors": ["目标函数"], "source_files": []},
                        "constraints": {"status": "pass", "text_anchors": ["约束"], "source_files": []},
                        "feasibility_check": {"status": "pass", "text_anchors": ["可行"], "source_files": []},
                    },
                }],
            }
            (root / "model_contract.yaml").write_text(yaml.safe_dump(contract), encoding="utf-8")
            # No sensitivity report created
            report = checker.validate(root, root / "model_contract.yaml", strict=False)
            sensitivity_issues = [i for i in report.get("warnings", []) if "sensitivity" in i.lower() or "灵敏度" in i or "robustness" in i.lower()]
            self.assertTrue(len(sensitivity_issues) > 0,
                            f"Expected sensitivity warning, got warnings: {report.get('warnings', [])}")

    def test_optimization_subproblem_with_valid_report_passes(self):
        """Optimization subproblem with valid sensitivity_report.yaml passes check."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\documentclass{article}\n\\begin{document}\n"
                "\\label{subproblem:Q1}\nTest.\n"
                "\\end{document}\n", encoding="utf-8")
            contract = {
                "schema_version": "2.1",
                "subproblems": [{
                    "id": "Q1",
                    "capabilities": ["optimization"],
                    "evidence": {
                        "decision_variables": {"status": "pass", "text_anchors": ["决策变量"], "source_files": []},
                        "objective": {"status": "pass", "text_anchors": ["目标函数"], "source_files": []},
                        "constraints": {"status": "pass", "text_anchors": ["约束"], "source_files": []},
                        "feasibility_check": {"status": "pass", "text_anchors": ["可行"], "source_files": []},
                    },
                }],
            }
            (root / "model_contract.yaml").write_text(yaml.safe_dump(contract), encoding="utf-8")
            # Create valid sensitivity_report.yaml (status=verified with real numeric values)
            sensitivity = {
                "schema_version": "1.0",
                "status": "verified",
                "subproblem_id": "Q1",
                "method": "parameter_perturbation",
                "parameters_analyzed": 1,
                "results": [{
                    "parameter": "demand",
                    "baseline": 100,
                    "perturbation_points": [
                        {"value": 80, "objective": 950.0, "feasible": True, "decision_change": "none"},
                        {"value": 100, "objective": 1000.0, "feasible": True, "decision_change": "none"},
                        {"value": 120, "objective": 1050.0, "feasible": True, "decision_change": "none"},
                    ],
                }],
            }
            (root / "sensitivity_report.yaml").write_text(yaml.safe_dump(sensitivity), encoding="utf-8")
            report = checker.validate(root, root / "model_contract.yaml", strict=False)
            sensitivity_issues = [i for i in report.get("warnings", []) + report.get("issues", [])
                                   if "sensitivity" in i.lower() or "灵敏度" in i or "robustness" in i.lower()]
            self.assertEqual(sensitivity_issues, [],
                             f"Unexpected sensitivity issues: {sensitivity_issues}")

    def test_non_optimization_subproblem_skips_sensitivity_check(self):
        """Non-optimization subproblem skips sensitivity report check."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\documentclass{article}\n\\begin{document}\n"
                "\\label{subproblem:Q1}\nTest.\n"
                "\\end{document}\n", encoding="utf-8")
            contract = {
                "schema_version": "2.1",
                "subproblems": [{
                    "id": "Q1",
                    "capabilities": ["prediction"],
                    "evidence": {
                        "preprocessing": {"status": "pass", "text_anchors": ["预处理"], "source_files": []},
                        "data_split": {"status": "pass", "text_anchors": ["数据划分"], "source_files": []},
                        "baseline": {"status": "pass", "text_anchors": ["基线"], "source_files": []},
                        "metrics": {"status": "pass", "text_anchors": ["指标"], "source_files": []},
                    },
                }],
            }
            (root / "model_contract.yaml").write_text(yaml.safe_dump(contract), encoding="utf-8")
            report = checker.validate(root, root / "model_contract.yaml", strict=False)
            sensitivity_issues = [i for i in report.get("warnings", []) + report.get("issues", [])
                                   if "sensitivity" in i.lower() or "灵敏度" in i or "robustness" in i.lower()]
            self.assertEqual(sensitivity_issues, [])

    def test_sensitivity_report_invalid_format_triggers_warning(self):
        """Sensitivity report with invalid schema_version triggers warning."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\documentclass{article}\n\\begin{document}\n"
                "\\label{subproblem:Q1}\nTest.\n"
                "\\end{document}\n", encoding="utf-8")
            contract = {
                "schema_version": "2.1",
                "subproblems": [{
                    "id": "Q1",
                    "capabilities": ["optimization"],
                    "evidence": {
                        "decision_variables": {"status": "pass", "text_anchors": ["决策变量"], "source_files": []},
                        "objective": {"status": "pass", "text_anchors": ["目标函数"], "source_files": []},
                        "constraints": {"status": "pass", "text_anchors": ["约束"], "source_files": []},
                        "feasibility_check": {"status": "pass", "text_anchors": ["可行"], "source_files": []},
                    },
                }],
            }
            (root / "model_contract.yaml").write_text(yaml.safe_dump(contract), encoding="utf-8")
            # Create invalid sensitivity_report.yaml (missing schema_version)
            (root / "sensitivity_report.yaml").write_text("status: invalid\n", encoding="utf-8")
            report = checker.validate(root, root / "model_contract.yaml", strict=False)
            sensitivity_issues = [i for i in report.get("warnings", [])
                                   if "sensitivity" in i.lower() or "灵敏度" in i or "格式" in i or "schema" in i.lower()]
            self.assertTrue(len(sensitivity_issues) > 0,
                            f"Expected format warning, got: {report.get('warnings', [])}")


if __name__ == "__main__":
    unittest.main()
