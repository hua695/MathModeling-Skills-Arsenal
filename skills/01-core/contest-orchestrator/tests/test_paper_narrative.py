import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_paper_narrative.py"
SPEC = importlib.util.spec_from_file_location("check_paper_narrative", CHECKER)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PaperNarrativeTests(unittest.TestCase):
    def test_modeling_section_accepts_question_bridge_and_two_numbered_subsections(self):
        text = (
            r"\section{模型建立与求解}"
            r"\subsection{问题一：资源配置}"
            r"本问围绕资源约束下的最优配置展开，建模思路是得到可执行方案并解释结果。"
            r"\subsubsection{模型建立}"
            r"\textbf{最终求解模型}\begin{equation}x\geq0\end{equation}"
            r"\subsubsection{模型求解与结果分析}"
            r"采用算法求解，结果表明方案可行且满足约束。"
            r"\section{参考文献}"
        )
        sections = MODULE.split_sections(text)

        warnings = MODULE.check_modeling_section_structure(sections)

        self.assertEqual(warnings, [])

    def test_modeling_section_rejects_fragmented_question_layout(self):
        text = (
            r"\section{模型建立与求解}"
            r"\subsection{问题一：资源配置}"
            r"\subsubsection{决策变量}变量。"
            r"\subsubsection{目标函数}目标。"
            r"\subsubsection{约束条件}约束。"
            r"\subsubsection{模型求解}结果。"
            r"\section{参考文献}"
        )
        sections = MODULE.split_sections(text)

        warnings = MODULE.check_modeling_section_structure(sections)

        self.assertTrue(any("模型建立" in item or "问题引入" in item for item in warnings))

    def test_modeling_questions_cannot_be_top_level_sections(self):
        text = (
            r"\section{问题一：资源配置}"
            r"\subsection{模型建立}最终求解模型\begin{equation}x\geq0\end{equation}"
            r"\subsection{模型求解与结果分析}结果表明方案可行。"
            r"\section{参考文献}"
        )

        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw) / "paper.tex"
            paper.write_text(text, encoding="utf-8")
            report = MODULE.check(paper, strict=True)

        self.assertTrue(any("一级章节" in item or "模型建立与求解" in item for item in report["warnings"]))

    def test_assumptions_and_symbols_cannot_be_combined(self):
        text = r"\section{模型假设与统一符号}"
        sections = MODULE.split_sections(text)
        warnings = MODULE.check_global_assumptions_symbol_layout(sections)
        self.assertTrue(any("分别设置" in item for item in warnings))

    def test_decimal_values_are_not_split_at_decimal_point(self):
        text = "结果为 0.85、3.2、12.5%、0.96、1.25、2.5%，结果表明模型稳定。"

        warnings = MODULE.check_result_explanation(text)

        self.assertEqual(warnings, [])

    def test_core_modeling_sections_require_a_reader_handoff(self):
        text = (
            r"\section{模型建立与求解}"
            r"\subsection{问题一：资源配置}"
            r"问题一给出资源配置模型。"
            r"\subsubsection{模型建立}最终求解模型\begin{equation}x\geq0\end{equation}"
            r"\subsubsection{模型求解与结果分析}结果表明方案可行。"
            r"\subsection{问题二：网络优化}"
            r"本问从新的定义开始。"
            r"\subsubsection{模型建立}最终求解模型\begin{equation}y\geq0\end{equation}"
            r"\subsubsection{模型求解与结果分析}结果说明方案有效。"
            r"\section{参考文献}"
        )

        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw) / "paper.tex"
            paper.write_text(text, encoding="utf-8")
            report = MODULE.check(paper)
        handoff_warnings = report["warnings"]

        self.assertTrue(any("章节承接" in item for item in handoff_warnings))

    def test_core_modeling_sections_with_reader_handoff_are_accepted(self):
        text = (
            r"\section{模型建立与求解}"
            r"\subsection{问题一：资源配置}"
            r"问题一给出资源配置模型。"
            r"\subsubsection{模型建立}最终求解模型\begin{equation}x\geq0\end{equation}"
            r"\subsubsection{模型求解与结果分析}结果表明方案可行。"
            r"\subsection{问题二：网络优化}"
            r"基于问题一得到的资源配置结果，本问进一步分析网络结构。"
            r"\subsubsection{模型建立}最终求解模型\begin{equation}y\geq0\end{equation}"
            r"\subsubsection{模型求解与结果分析}结果说明方案有效。"
            r"\section{参考文献}"
        )

        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw) / "paper.tex"
            paper.write_text(text, encoding="utf-8")
            report = MODULE.check(paper)
        handoff_warnings = [item for item in report["warnings"] if "章节承接" in item]

        self.assertEqual(handoff_warnings, [])


if __name__ == "__main__":
    unittest.main()
