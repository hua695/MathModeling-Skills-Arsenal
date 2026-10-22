import json
import tempfile
import unittest
from pathlib import Path

from scripts.figure_registry import validate
from scripts.check_tex_layout_patterns import check


ROOT = Path(__file__).resolve().parents[1]


class LayoutContractTests(unittest.TestCase):
    def _registry_item(self):
        return {
            "kind": "data",
            "generator": "modelviz",
            "semantic_qa": "scipilot-figure-skill",
            "decision_author": "scipilot-figure-skill",
            "decision_card": "figures/q1_decision_card.yaml",
            "source_files": ["results/result.json"],
            "script": "figures/q1/plot.py",
            "formats": ["svg", "png"],
            "insertion_format": "svg",
            "qa_status": "reviewed",
            "visual_qa": "passed",
        }

    def _validate_item(self, item):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "results").mkdir()
            (root / "figures").mkdir()
            (root / "results" / "result.json").write_text("{}", encoding="utf-8")
            (root / "figures" / "q1_decision_card.yaml").write_text("claim: test\n", encoding="utf-8")
            (root / "figures" / "q1").mkdir()
            (root / "figures" / "q1" / "plot.py").write_text("# plot\n", encoding="utf-8")
            registry = root / "figure_registry.json"
            registry.write_text(
                json.dumps({"schema_version": "2.0", "figures": {"fig_q1": item}}),
                encoding="utf-8",
            )
            return validate(registry, root)

    def test_image_registry_requires_an_explicit_page_layout_mode(self):
        report = self._validate_item(self._registry_item())
        self.assertFalse(report["passed"])
        self.assertTrue(any("missing layout_mode" in error for error in report["errors"]))

    def test_side_by_side_layout_requires_group_and_variant(self):
        item = self._registry_item()
        item["layout_mode"] = "side_by_side"
        report = self._validate_item(item)
        self.assertFalse(report["passed"])
        self.assertTrue(any("layout_group" in error for error in report["errors"]))
        self.assertTrue(any("layout_variant" in error for error in report["errors"]))

    def test_layout_checker_rejects_raw_image_insertion(self):
        source = r"""
        \section{结果}
        如图\ref{fig:q1}所示，结果呈现明显差异。
        \begin{figure}[!htbp]
          \centering
          \includegraphics[width=\textwidth]{figures/q1.png}
          \caption{结果图}\label{fig:q1}
        \end{figure}
        图后对结果作出解释。
        """
        report = check(source)
        self.assertTrue(any(item["kind"] == "raw_image_insert" for item in report["issues"]))

    def test_layout_checker_rejects_unconstrained_svg(self):
        source = r"""
        \section{结果}
        如图\ref{fig:q1}所示，结果呈现明显差异。
        \begin{figure}[!htbp]
          \centering
          \includesvg[width=\textwidth,height=.8\textheight]{figures/q1}
          \caption{结果图}\label{fig:q1}
        \end{figure}
        图后对结果作出解释。
        """
        report = check(source)
        kinds = {item["kind"] for item in report["issues"]}
        self.assertIn("svg_width_unconstrained", kinds)
        self.assertIn("svg_height_unconstrained", kinds)

    def test_layout_checker_reports_approved_layout_commands(self):
        report = check(r"\PaperFigure{caption}{fig:q1}{figures/q1}\PaperTwoColumn{left}{right}")
        self.assertEqual(report["layout_modes"]["single"], 1)
        self.assertEqual(report["layout_modes"]["side_by_side"], 1)

    def test_layout_checker_ignores_float_body_inside_layout_macro_definition(self):
        source = r"""
        \NewDocumentCommand{\PaperFigure}{O{0.76\textwidth} m m m}{%
          \begin{figure}[!htbp]
            \centering
            \includesvg{figures/example}
            \caption{图题}\label{fig:example}
          \end{figure}%
        }
        """
        report = check(source)
        kinds = {item["kind"] for item in report["issues"]}
        self.assertNotIn("figure_no_intro", kinds)
        self.assertNotIn("figure_no_explanation", kinds)
        self.assertNotIn("consecutive_floats", kinds)

    def test_generic_paper_template_exposes_controlled_layout_and_section_barrier(self):
        source = (ROOT / "templates" / "paper_template.tex").read_text(encoding="utf-8")
        for command in (
            r"\PaperFigure",
            r"\PaperTwoColumn",
            r"\PaperWrapFigure",
            r"\PaperTallFigure",
        ):
            self.assertIn(command, source, command)
        self.assertIn(r"\FloatBarrier", source)
        self.assertIn(r"\AddToHook{cmd/section/before}", source)


if __name__ == "__main__":
    unittest.main()
