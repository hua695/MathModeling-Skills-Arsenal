from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from replay_profiles import write_fixture  # noqa: E402
from check_modeling_solution_contract import _spans  # noqa: E402
from check_modeling_contract import check as check_modeling_contract  # noqa: E402


class ModelingHardeningTests(unittest.TestCase):
    def fixture(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="contest_orchestrator_hardening_"))
        write_fixture(root, "optimization")
        return root

    def run_script(self, name: str, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPTS / name), str(root), *args],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def test_mixed_question_scope_does_not_fallback_to_whole_text(self) -> None:
        spans = _spans(r"\label{subproblem:Q1} only q1", ["Q1", "Q2"])
        self.assertEqual(set(spans), {"Q1"})

    def test_schema_11_requires_substantive_derivation_anchor(self) -> None:
        root = self.fixture()
        path = root / "modeling_solution_contract.yaml"
        text = path.read_text(encoding="utf-8").replace(
            "derivation_anchor: '由基础关系推导目标关系'", "derivation_anchor: '不存在的推导步骤'")
        path.write_text(text, encoding="utf-8")
        report = self.run_script("check_modeling_solution_contract.py", root, "--strict")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("实质整理/推导步骤", report.stdout)

    def test_algorithm_manifest_blocks_parameter_drift(self) -> None:
        root = self.fixture()
        (root / "q1_config.json").write_text(json.dumps({"convergence_tolerance": 2e-6}), encoding="utf-8")
        report = self.run_script("check_algorithm_manifest.py", root, "--strict")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("参数 convergence_tolerance", report.stdout)

    def test_derived_result_check_recomputes_value(self) -> None:
        root = self.fixture()
        (root / "result_code_map.json").write_text(json.dumps({
            "derived_checks": [{"result_file": "results/q1_results.json", "target_pointer": "/score",
                                 "input_pointers": ["/score", "/score"], "operation": "mean"}]
        }), encoding="utf-8")
        report = self.run_script("check_result_code_consistency.py", root, "--strict")
        self.assertEqual(report.returncode, 0)

    def test_derived_result_check_blocks_arithmetic_drift(self) -> None:
        root = self.fixture()
        data = {"a": 1, "b": 2, "total": 9}
        (root / "results" / "derived.json").write_text(json.dumps(data), encoding="utf-8")
        (root / "result_code_map.json").write_text(json.dumps({
            "derived_checks": [{"result_file": "results/derived.json", "target_pointer": "/total",
                                 "input_pointers": ["/a", "/b"], "operation": "sum"}]
        }), encoding="utf-8")
        report = self.run_script("check_result_code_consistency.py", root, "--strict")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("/total", report.stdout)

    def test_dimension_checker_blocks_declared_mismatch(self) -> None:
        root = self.fixture()
        (root / "model_contract.yaml").write_text(
            "schema_version: '2.1'\ndimensions:\n  required: true\n  symbols:\n"
            "    x: [1, 0]\n    y: [0, 1]\n  equations:\n"
            "    - {lhs: y, rhs_terms: [x], operation: same}\n", encoding="utf-8")
        report = self.run_script("check_dimension_consistency.py", root, "--strict")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("量纲方程", report.stdout)

    def test_problem_coverage_accepts_mapped_ledger(self) -> None:
        root = self.fixture()
        report = self.run_script("check_problem_coverage.py", root, "--strict", "--require-ledger")
        self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
        self.assertIn("PASS", report.stdout)

    def test_problem_coverage_blocks_missing_ledger_in_strict_mode(self) -> None:
        root = self.fixture()
        (root / "problem_condition_ledger.yaml").unlink()
        report = self.run_script("check_problem_coverage.py", root, "--strict", "--require-ledger")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("缺少 problem_condition_ledger.yaml", report.stdout)

    def test_problem_coverage_blocks_pending_condition(self) -> None:
        root = self.fixture()
        ledger = root / "problem_condition_ledger.yaml"
        text = ledger.read_text(encoding="utf-8").replace(
            "evidence_level: confirmed", "evidence_level: pending")
        ledger.write_text(text, encoding="utf-8")
        report = self.run_script("check_problem_coverage.py", root, "--strict", "--require-ledger")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("未解决", report.stdout)

    def test_problem_coverage_blocks_cross_question_mismatch(self) -> None:
        root = self.fixture()
        ledger = root / "problem_condition_ledger.yaml"
        text = ledger.read_text(encoding="utf-8").replace(
            "affected_questions: [Q1]", "affected_questions: [Q2]")
        ledger.write_text(text, encoding="utf-8")
        report = self.run_script("check_problem_coverage.py", root, "--strict", "--require-ledger")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("source_units 与 questions 的小问集合不一致", report.stdout)

    def test_strict_modeling_structure_requires_bridge_and_final_model_block(self) -> None:
        text = r"""
        \section{模型建立与求解}
        \subsection{问题一：资源配置}
        \subsubsection{模型建立}
        结合题面建立假设，给出模型思路。由式(1)可得目标函数与约束条件，模型适用范围明确。
        \subsubsection{求解}
        采用算法求解，设置初值、搜索区间和终止条件，结果表明方案可行，并进行敏感性分析。
        """
        report = check_modeling_contract(text, strict=True)
        self.assertFalse(report["passed"])
        self.assertTrue(any("问题引入与建模思路" in item or "最终求解模型" in item
                            for item in report["issues"]))

    def test_strict_modeling_structure_accepts_two_section_question_layout(self) -> None:
        text = r"""
        \section{符号说明}
        全局符号说明：x 为决策变量，单位为无量纲，x\ge 0。
        \section{模型建立与求解}
        \subsection{问题一：资源配置}
        本问围绕资源约束下的最优配置展开，已知需求与容量，建模思路是得到可执行方案并解释结果。
        \subsubsection{模型建立}
        根据假设与题面条件，由式(1)推导目标函数和约束条件。\textbf{最终求解模型}
        \begin{equation} \min f(x) \quad \text{s.t. } x\ge 0 \end{equation}
        \subsubsection{模型求解与结果分析}
        采用算法求解，设置初值、搜索区间和终止条件。结果显示方案可行，并通过敏感性分析说明稳定性。
        """
        report = check_modeling_contract(text, strict=True)
        self.assertTrue(report["passed"], report["issues"])


if __name__ == "__main__":
    unittest.main()
