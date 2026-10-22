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
from delivery_all import resolve_blueprint_route  # noqa: E402
from check_modeling_contract import check as check_modeling  # noqa: E402
from check_model_evidence import _subproblem_spans  # noqa: E402
from check_modeling_solution_contract import _spans  # noqa: E402


class V413ContractTests(unittest.TestCase):
    def run_script(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                              cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    def fixture(self, profile: str = "optimization") -> Path:
        root = Path(tempfile.mkdtemp(prefix="contest_orchestrator_v413_test_"))
        write_fixture(root, profile)
        return root

    def test_abstract_blocks_unverified_number(self) -> None:
        root = self.fixture()
        values = {"score": 0.85, "error": 99.9, "improvement_percent": 12.5}
        (root / "results" / "q1_results.json").write_text(json.dumps(values), encoding="utf-8")
        report = self.run_script("check_abstract_contract.py", str(root / "paper"),
                                 "--project-root", str(root), "--strict")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("无法追溯", report.stdout)

    def test_derivation_blocks_missing_step_anchor(self) -> None:
        root = self.fixture()
        registry = (root / "derivation_registry.yaml").read_text(encoding="utf-8")
        registry = registry.replace("由基础关系推导目标关系", "正文不存在的伪造推导步骤")
        (root / "derivation_registry.yaml").write_text(registry, encoding="utf-8")
        report = self.run_script("check_derivation_chain.py", str(root), "--strict")
        self.assertNotEqual(report.returncode, 0)

    def test_symbol_blocks_wrong_unit(self) -> None:
        root = self.fixture()
        (root / "model_contract.yaml").write_text(
            "schema_version: '2.1'\nsubproblems:\n"
            "  - id: Q1\n    symbols: [{name: x, meaning: 状态, unit: m, scope: global}]\n"
            "  - id: Q2\n    symbols: [{name: x, meaning: 状态, unit: kg, scope: global}]\n",
            encoding="utf-8")
        report = self.run_script("check_symbol_consistency.py", str(root), "--strict")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("单位冲突", report.stdout)

    def test_result_code_blocks_mismatch(self) -> None:
        root = self.fixture()
        (root / "solve.py").write_text("RESULTS = {'score': 0.70}\n", encoding="utf-8")
        (root / "result_code_map.json").write_text(json.dumps({"checks": [{
            "result_file": "results/q1_results.json", "code_file": "solve.py",
            "code_variable": "RESULTS", "json_pointer": "/score"}]}, ensure_ascii=False), encoding="utf-8")
        report = self.run_script("check_result_code_consistency.py", str(root), "--strict")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("结果与代码不一致", report.stdout)

    def test_hybrid_route_is_strict_single_is_shadow(self) -> None:
        root = self.fixture()
        hybrid = root / "model_blueprint.yaml"
        hybrid.write_text("project:\n  composition: hybrid\nsubproblems: []\n", encoding="utf-8")
        self.assertTrue(resolve_blueprint_route(root)["strict"])
        hybrid.write_text("project:\n  composition: single\nsubproblems: []\n", encoding="utf-8")
        self.assertFalse(resolve_blueprint_route(root)["strict"])

    def test_model_ratio_prefers_rendered_pdf_pages(self) -> None:
        root = self.fixture()
        import pymupdf
        pdf = pymupdf.open()
        for heading in ("Problem analysis", "Model formulation", "Validation", "Bibliography"):
            page = pdf.new_page()
            page.insert_text((72, 72), heading, fontsize=12)
        pdf_path = root / "paper" / "paper.pdf"
        pdf.save(str(pdf_path))
        pdf.close()
        source = (root / "paper" / "paper.tex").read_text(encoding="utf-8")
        report = check_modeling(source, strict=False, pdf_path=pdf_path)
        self.assertEqual(report["measurement"], "pdf_rendered_page_count")
        self.assertEqual(report["page_details"]["model_pages"], 1)

    def test_modeling_solution_contract_blocks_unconfirmed_code(self) -> None:
        root = self.fixture()
        contract = root / "modeling_solution_contract.yaml"
        contract.write_text(contract.read_text(encoding="utf-8").replace("code_debug_status: pass", "code_debug_status: pending"), encoding="utf-8")
        report = self.run_script("check_modeling_solution_contract.py", str(root), "--strict")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("调试完成", report.stdout)

    def test_modeling_solution_contract_blocks_broken_derivation_anchor(self) -> None:
        root = self.fixture()
        contract = root / "modeling_solution_contract.yaml"
        contract.write_text(contract.read_text(encoding="utf-8").replace("最终公式对应输出目标", "正文不存在的最终公式"), encoding="utf-8")
        report = self.run_script("check_modeling_solution_contract.py", str(root), "--strict")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("正文锚点", report.stdout)

    def test_modeling_solution_contract_blocks_direct_numeric_result(self) -> None:
        root = self.fixture()
        tex = root / "paper" / "paper.tex"
        contract = root / "modeling_solution_contract.yaml"
        contract.write_text(
            contract.read_text(encoding="utf-8").replace(
                "    result_source_files: [results/q1_results.json]",
                "    result_source_files: []",
            ),
            encoding="utf-8",
        )
        tex.write_text(tex.read_text(encoding="utf-8").replace("主结果见表3", "结果为 9.9，主结果见表3"), encoding="utf-8")
        report = self.run_script("check_modeling_solution_contract.py", str(root), "--strict")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("直接写入数值结果", report.stdout)

    def test_modeling_solution_contract_blocks_formula_symbol_not_in_table(self) -> None:
        root = self.fixture()
        contract = root / "modeling_solution_contract.yaml"
        text = contract.read_text(encoding="utf-8").replace(
            "      - {symbol: z, meaning: 输出变量, unit: 1, variable_type: objective}\n", "")
        contract.write_text(text, encoding="utf-8")
        report = self.run_script("check_modeling_solution_contract.py", str(root), "--strict")
        self.assertNotEqual(report.returncode, 0)
        self.assertIn("符号表定义", report.stdout)

    def test_contract_checkers_discover_project_planning_directory(self) -> None:
        root = self.fixture()
        planning = root / "01_需求与规划"
        planning.mkdir()
        for filename in ("model_contract.yaml", "derivation_registry.yaml", "modeling_solution_contract.yaml"):
            (root / filename).replace(planning / filename)
        for script in ("check_model_evidence.py", "check_derivation_chain.py", "check_modeling_solution_contract.py"):
            report = self.run_script(script, str(root), "--strict")
            self.assertEqual(report.returncode, 0, report.stdout + report.stderr)

    def test_final_subproblem_stops_before_later_sections_and_appendix_code(self) -> None:
        text = (
            "\\section{模型建立与求解}\n"
            "\\subsection{问题一}\\label{subproblem:Q1}\nQ1 正文\n"
            "\\subsection{问题二}\\label{subproblem:Q2}\nQ2 正文\n"
            "\\section{模型检验}\n检验正文\n"
            "\\appendix\\begin{minted}{python}\nprint('code')\n\\end{minted}\n"
        )
        solution_spans = _spans(text, ["Q1", "Q2"])
        evidence_spans = _subproblem_spans(text, ["Q1", "Q2"])
        self.assertNotIn("模型检验", solution_spans["Q2"])
        self.assertNotIn("minted", solution_spans["Q2"])
        self.assertNotIn("模型检验", text[slice(*evidence_spans["Q2"])])
        self.assertNotIn("minted", text[slice(*evidence_spans["Q2"])])


if __name__ == "__main__":
    unittest.main()
