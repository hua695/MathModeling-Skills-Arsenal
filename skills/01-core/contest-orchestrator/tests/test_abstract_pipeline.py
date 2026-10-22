import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import check_harness_control


SKILL_ROOT = Path(__file__).resolve().parents[1]


class AbstractPipelineTests(unittest.TestCase):
    def test_abstract_argument_card_template_declares_reader_contract(self):
        path = SKILL_ROOT / "templates" / "abstract_argument_card.yaml"
        self.assertTrue(path.exists())
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for key in (
            "reader_contract",
            "central_thesis",
            "modeling_line",
            "questions",
            "validation",
            "final_synthesis",
            "keywords",
        ):
            self.assertIn(key, data)

    def test_chapter_card_carries_abstract_contribution(self):
        path = SKILL_ROOT / "templates" / "chapter_writing_card.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        contribution = data["abstract_contribution"]
        for key in ("method", "result", "meaning", "evidence_refs"):
            self.assertIn(key, contribution)

    def test_paper_spine_separates_assumptions_and_symbols(self):
        for relative in (
            "templates/paper_narrative.yaml",
            "templates/paper_author_brief.yaml",
            "templates/paper_continuity_context.yaml",
            "templates/paper_argument_blueprint.yaml",
        ):
            data = yaml.safe_load((SKILL_ROOT / relative).read_text(encoding="utf-8"))
            spine = data.get("paper_spine")
            if spine is None:
                if "narrative" in data:
                    spine = data["narrative"]["global"]["paper_spine"]
                else:
                    spine = data["global"]["paper_spine"]
            self.assertNotIn("assumptions_symbols", spine.get("support_chapters", []))
            self.assertIn("assumptions", spine.get("support_chapters", []))
            self.assertIn("symbols", spine.get("support_chapters", []))
            self.assertIn("assumptions", spine.get("chapter_order", []))
            self.assertIn("symbols", spine.get("chapter_order", []))

    def test_h8_requires_abstract_argument_card(self):
        self.assertIn(
            "abstract_argument_card.yaml",
            check_harness_control.REQUIRED_INPUT_BY_NODE["H8"],
        )

    def test_h8_control_exposes_abstract_closure_fields(self):
        control = check_harness_control.default_control()
        h8 = control["nodes"]["H8"]
        self.assertIn("abstract_argument_card", h8)
        self.assertIn("abstract_contract_report", h8)
        self.assertIn("abstract_written", h8)

    def test_latex_template_uses_requested_heading_scheme(self):
        tex = (SKILL_ROOT / "templates" / "paper_template.tex").read_text(encoding="utf-8")
        self.assertIn(r"section = {name = {,、}, number = \chinese{section}", tex)
        self.assertIn(r"\renewcommand{\thesubsection}{\arabic{section}.\arabic{subsection}}", tex)
        self.assertIn(r"\renewcommand{\thesubsubsection}{\arabic{section}.\arabic{subsection}.\arabic{subsubsection}}", tex)
        self.assertIn(r"\section{模型假设}", tex)
        self.assertIn(r"\section{符号说明}", tex)
        self.assertIn(r"\section{模型建立与求解}", tex)

    def test_h8_documents_bind_abstract_card_to_final_closure(self):
        execution = (SKILL_ROOT / "references" / "h8_chapter_execution.md").read_text(encoding="utf-8")
        warmup = (SKILL_ROOT / "references" / "warmup" / "h8_writer_warmup.md").read_text(encoding="utf-8")
        for content in (execution, warmup):
            self.assertIn("abstract_argument_card.yaml", content)
            self.assertIn("abstract_contribution", content)
            self.assertIn("H8C", content)
        self.assertIn("check_abstract_contract.py --strict", execution)

    def test_abstract_card_validator_rejects_uncovered_question(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "abstract_argument_card.yaml").write_text(
                yaml.safe_dump(
                    {
                        "schema_version": "1.0",
                        "status": "approved",
                        "reader_contract": "回答题目并给出可核验结论",
                        "central_thesis": "统一建模主线",
                        "modeling_line": "分析到求解再到验证",
                        "questions": [
                            {
                                "id": "Q1",
                                "reader_question": "问题一问什么",
                                "method": "方法",
                                "result": "结果",
                                "meaning": "意义",
                                "evidence_refs": ["result_cards/Q1.yaml"],
                            }
                        ],
                        "validation": {"method": "独立验证", "result": "通过"},
                        "final_synthesis": "结论",
                        "keywords": ["关键词一", "关键词二"],
                    },
                    allow_unicode=True,
                ),
                encoding="utf-8",
            )
            report = check_harness_control.validate_abstract_argument_card(
                root / "abstract_argument_card.yaml",
                expected_question_ids=["Q1", "Q2"],
            )
            self.assertFalse(report["passed"])
            self.assertTrue(any("Q2" in issue for issue in report["issues"]))


if __name__ == "__main__":
    unittest.main()
