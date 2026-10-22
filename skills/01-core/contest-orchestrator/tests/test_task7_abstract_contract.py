#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 7 abstract contract enhancement tests.

Covers optimization-capability-driven abstract checks and numeric density
as WARN-level diagnostic.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_abstract_contract as checker  # noqa: E402


class OptimizationAbstractTests(unittest.TestCase):
    def test_optimization_abstract_requires_method_or_model(self):
        """Optimization capability abstract must mention method/model per subproblem."""
        abstract = (
            "本文研究了一个问题。"
            "问题一我们进行了分析。"
            "问题二我们进行了分析。"
            "最终得到了结果 100。"
        )
        result = checker._check_optimization_abstract(abstract, capabilities=["optimization"])
        self.assertIn("method_or_model", result.get("missing", []))

    def test_optimization_abstract_requires_quantified_result_or_feasibility(self):
        """Optimization abstract must include quantified result or feasibility conclusion."""
        abstract = (
            "本文研究了一个优化问题。"
            "问题一我们建立了线性规划模型，使用单纯形法求解。"
            "问题二我们建立了整数规划模型，使用分支定界法求解。"
            "最终模型有效。"
        )
        result = checker._check_optimization_abstract(abstract, capabilities=["optimization"])
        self.assertIn("quantified_result_or_feasibility", result.get("missing", []))

    def test_optimization_abstract_requires_objective_and_constraints(self):
        """Optimization abstract must mention objective function meaning and constraint types."""
        abstract = (
            "本文研究了一个优化问题。"
            "问题一我们建立了模型，得到了最优值 100。"
            "问题二我们建立了模型，得到了最优值 200。"
            "最终结果有效。"
        )
        result = checker._check_optimization_abstract(abstract, capabilities=["optimization"])
        self.assertIn("objective_or_constraints", result.get("missing", []))

    def test_optimization_abstract_accepts_complete_coverage(self):
        """Complete optimization abstract passes all capability checks."""
        abstract = (
            "本文针对优化决策问题，建立了多阶段规划模型。"
            "问题一建立线性规划模型，以最小化总成本为目标函数，考虑容量约束和供需平衡约束，使用单纯形法求解，得到最优成本 152.3 万元，方案可行。"
            "问题二建立混合整数规划模型，以最大化收益为目标，考虑时间窗口约束和资源约束，使用分支定界法求解，得到最优收益 289.5 万元，所有约束均满足。"
            "通过参数扰动分析验证了模型的稳健性，目标值波动小于 5%。"
            "本文模型可为同类优化决策问题提供参考。"
        )
        result = checker._check_optimization_abstract(abstract, capabilities=["optimization"])
        self.assertEqual(result.get("missing", []), [])

    def test_non_optimization_skips_optimization_checks(self):
        """Non-optimization capabilities skip optimization-specific checks."""
        abstract = "本文研究了一个预测问题。"
        result = checker._check_optimization_abstract(abstract, capabilities=["prediction"])
        self.assertEqual(result.get("status"), "skipped")


class NumericDensityTests(unittest.TestCase):
    def test_numeric_density_is_warn_not_block(self):
        """Numeric density count is WARN-level diagnostic, not BLOCK."""
        abstract = (
            "本文研究了一个优化问题。"
            "问题一建立了模型。"
            "问题二建立了模型。"
            "最终得到了结果。"
        )
        result = checker._numeric_density_diagnostic(abstract)
        self.assertEqual(result.get("level"), "WARN")
        self.assertIn("numeric_count", result)

    def test_numeric_density_excludes_reference_numbers(self):
        """Numeric density excludes year, formula, figure, section, reference numbers."""
        abstract = (
            "本文研究了 2023 年的优化问题。"
            "见图 1 和表 2。"
            "公式 (3) 给出了目标函数。"
            "参考文献 [4] 提供了方法。"
            "第一章介绍了背景。"
            "最优值为 100.5。"
        )
        result = checker._numeric_density_diagnostic(abstract)
        # Should count 100.5 but not 2023, 1, 2, 3, 4
        self.assertLessEqual(result.get("numeric_count", 99), 5)


if __name__ == "__main__":
    unittest.main()
