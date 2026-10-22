import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_latex_appendix_contract.py"


GOOD_TEX = r"""\documentclass{article}
\usepackage{minted}
\usepackage{fontspec}
\setmonofont{Consolas}
\definecolor{codebg}{gray}{0.96}
\usemintedstyle{vs}
\begin{document}
\section{正文}正文详见附录A，参见附录B，详见附录C。
\section{参考文献}
\bibliography{ref}
\appendix
\section{附录A 长推导}
\begin{table}[ht]
\caption{样本数据}\label{tab:A-1}
\end{table}
\section{附录B 核心代码}
\medskip
\begin{minted}[bgcolor=codebg,linenos,breaklines,tabsize=4,fontsize=\small,framesep=6pt]{python}
# 功能：核心计算；输入：数据；输出：结果
print(1)
\end{minted}
\medskip
\section{附录C 支撑材料}
支撑材料文件清单：src/full.py。\par
编译提示：-shell-escape；依赖 Pygments。
\end{document}
"""


def write_fixture(root: Path, tex: str = GOOD_TEX) -> None:
    (root / "paper.tex").write_text(tex, encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "full.py").write_text("# full source\n", encoding="utf-8")
    (root / "derivation.md").write_text("真实长推导\n", encoding="utf-8")
    (root / "raw.csv").write_text("x\n1\n", encoding="utf-8")
    (root / "appendix_contract.yaml").write_text(
        """schema_version: '1.0'
required_appendix_ids: [A, B, C]
source_inputs:
  program_used: true
  full_source_files: [src/full.py]
  long_derivation_files: [derivation.md]
  raw_data_files: [raw.csv]
  support_material_files: [src/full.py]
""", encoding="utf-8")


def run(root: Path, *extra: str) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(root), *extra],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )
    return result.returncode, json.loads(result.stdout)


def write_dual_layer_fixture(root: Path, bind_core: bool = True,
                             include_all_support_sources: bool = True) -> None:
    (root / "paper.tex").write_text(r"""\documentclass{article}
\usepackage{minted}
\usepackage{fontspec}
\setmonofont{Consolas}
\definecolor{codebg}{gray}{0.96}
\usemintedstyle{vs}
\begin{document}
正文详见附录A，参见附录B，详见附录C。
\section{参考文献}
\bibliography{ref}
\appendix
\section{附录A 支撑材料文件清单}
支撑材料文件清单：support_materials/source_bundle.zip、src/core.py、src/common.py。
\section{附录B 核心源代码}
\textbf{代码文件：""" + ("src/core.py" if bind_core else "核心求解程序") + r"""}
\medskip
\begin{minted}[bgcolor=codebg,linenos,breaklines,tabsize=4,fontsize=\small,framesep=6pt]{python}
# 功能：核心计算；输入：数据；输出：结果
print(1)
\end{minted}
\medskip
\section{附录C 补充结果}
\begin{table}[ht]
\caption{补充结果}\label{tab:C-1}
\end{table}
编译提示：-shell-escape；依赖 Pygments。
\end{document}
""", encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "core.py").write_text("print(1)\n", encoding="utf-8")
    (root / "src" / "common.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "support_materials").mkdir()
    (root / "support_materials" / "source_bundle.zip").write_bytes(b"bundle")
    support_sources = "  support_source_files: [src/core.py, src/common.py]\n" if include_all_support_sources else "  support_source_files: [src/core.py]\n"
    (root / "appendix_plan.yaml").write_text("""schema_version: '2.0'
status: READY
planning_contract: coverage_first
official_format:
  appendix_ids: [A, B, C]
subproblems:
  - id: Q1
    primary_type: hybrid
    capabilities: [code]
appendix_modules:
  - module_id: app-code
    kind: source_code
    used_by: [Q1]
    required: true
    source_files: [src/core.py]
    paper_anchor: app:code
    include_in_pdf: true
coverage_matrix:
  - subproblem_id: Q1
    main_section: '6.1'
    core_code_module: app-code
    long_derivation_module: null
    verification_module: null
source_inputs:
  program_used: true
  appendix_code_mode: core_only
  core_source_files: [src/core.py]
  full_source_files: [src/core.py, src/common.py]
""" + support_sources + """  support_material_files: [support_materials/source_bundle.zip, src/core.py, src/common.py]
""", encoding="utf-8")


class LatexAppendixContractTests(unittest.TestCase):
    def test_dual_layer_code_contract_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_dual_layer_fixture(root)
            code, report = run(root, "--strict")
            self.assertEqual(code, 0, report)
            self.assertEqual(report["details"]["appendix_code_mode"], "core_only")
            self.assertEqual(report["details"]["core_source_files"], ["src/core.py"])
            self.assertEqual(report["details"]["full_source_files"], ["src/core.py", "src/common.py"])

    def test_core_source_must_be_bound_to_code_region(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_dual_layer_fixture(root, bind_core=False)
            code, report = run(root, "--strict")
            self.assertNotEqual(code, 0, report)
            self.assertTrue(any("核心源码未绑定" in item for item in report["issues"]))

    def test_full_source_files_must_be_in_support_inventory(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_dual_layer_fixture(root, include_all_support_sources=False)
            code, report = run(root, "--strict")
            self.assertNotEqual(code, 0, report)
            self.assertTrue(any("完整源码未纳入支撑材料" in item for item in report["issues"]))

    def test_valid_minted_appendix_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_fixture(root)
            code, report = run(root, "--strict")
            self.assertEqual(code, 0, report)
            self.assertTrue(report["passed"])
            self.assertEqual(len(report["self_check"]), 11)

    def test_project_root_allows_materials_outside_paper_dir(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper"
            paper.mkdir()
            write_fixture(paper)
            # Move the evidence inputs to stable project-level locations.
            (root / "data").mkdir()
            (root / "data" / "raw.csv").write_text("x\n1\n", encoding="utf-8")
            (root / "derivations").mkdir()
            (root / "derivations" / "q1.md").write_text("真实长推导\n", encoding="utf-8")
            (root / "support").mkdir()
            (root / "support" / "full.py").write_text("# full source\n", encoding="utf-8")
            (root / "appendix_contract.yaml").write_text(
                """schema_version: '1.0'
required_appendix_ids: [A, B, C]
source_inputs:
  program_used: true
  full_source_files: [support/full.py]
  long_derivation_files: [derivations/q1.md]
  raw_data_files: [data/raw.csv]
  support_material_files: [support/full.py]
""", encoding="utf-8")
            code, report = run(paper, "--project-root", str(root), "--strict")
            self.assertEqual(code, 0, report)

    def test_missing_input_contract_blocks(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(GOOD_TEX, encoding="utf-8")
            code, report = run(root, "--strict")
            self.assertNotEqual(code, 0)
            self.assertIn("appendix_contract", report["issues"][0])

    def test_appendix_before_references_blocks(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_fixture(root, GOOD_TEX.replace("\\section{参考文献}\n\\bibliography{ref}\n", ""))
            tex = (root / "paper.tex").read_text(encoding="utf-8")
            tex = tex.replace("\\appendix\n", "\\appendix\n\\section{参考文献}\n\\bibliography{ref}\n", 1)
            (root / "paper.tex").write_text(tex, encoding="utf-8")
            code, report = run(root, "--strict")
            self.assertNotEqual(code, 0)
            self.assertTrue(any("参考文献之前" in item for item in report["issues"]))

    def test_lstlisting_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_fixture(root, GOOD_TEX.replace("\\begin{minted}[bgcolor=codebg,linenos,breaklines,tabsize=4,fontsize=\\small,framesep=6pt]{python}\n# 功能：核心计算；输入：数据；输出：结果\nprint(1)\n\\end{minted}", "\\begin{lstlisting}\nprint(1)\n\\end{lstlisting}"))
            code, report = run(root, "--strict")
            self.assertNotEqual(code, 0)
            self.assertTrue(any("lstlisting" in item for item in report["issues"]))

    def test_missing_minted_option_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            tex = GOOD_TEX.replace("framesep=6pt", "framesep=4pt")
            write_fixture(root, tex)
            code, report = run(root, "--strict")
            self.assertNotEqual(code, 0)
            self.assertTrue(any("framesep=6pt" in item for item in report["issues"]))

    def test_unresolved_appendix_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_fixture(root, GOOD_TEX.replace("详见附录C", "详见附录D"))
            code, report = run(root, "--strict")
            self.assertNotEqual(code, 0)
            self.assertTrue(any("正文引用附录D" in item for item in report["issues"]))


if __name__ == "__main__":
    unittest.main()
