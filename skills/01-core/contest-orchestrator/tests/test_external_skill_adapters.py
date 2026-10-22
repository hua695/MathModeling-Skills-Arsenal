"""Contract tests for skills called by contest-orchestrator.

These tests intentionally describe the local adapter boundary rather than the
upstream skills' generic capabilities.  They keep each external skill from
silently becoming a second orchestrator or leaking unverified process text
into project deliverables.
"""

from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(r"C:\Users\USER\.agents\skills")
ORCHESTRATOR_ROOT = SKILL_ROOT / "contest-orchestrator"


def skill_text(name: str) -> str:
    return (SKILL_ROOT / name / "SKILL.md").read_text(encoding="utf-8")


class ExternalSkillAdapterContractTests(unittest.TestCase):
    def test_orchestrator_uses_one_adapter_contract_and_split_visual_policy(self):
        skill = (ORCHESTRATOR_ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        contract = (ORCHESTRATOR_ROOT / "references" / "external_skill_adapters.md").read_text(encoding="utf-8").lower()
        figures = (ORCHESTRATOR_ROOT / "references" / "figure_policy.md").read_text(encoding="utf-8").lower()
        self.assertIn("references/external_skill_adapters.md", skill)
        self.assertIn("绘图技能的截图、渲染复核和 ai 视觉检查默认开启", contract)
        self.assertIn("非绘图流程默认关闭视觉检查", contract)
        self.assertIn("on by default", figures)

    def test_all_direct_routes_declare_the_local_adapter(self):
        routes = {
            "math-model-selector": "Contest-Orchestrator Adapter",
            "math-modeling": "Contest-Orchestrator Adapter",
            "data-science-stack": "Contest-Orchestrator Adapter",
            "heuristic-algorithms": "Contest-Orchestrator Adapter",
            "pyomo": "Contest-Orchestrator Adapter",
            "academic-writing": "数学建模论文写作适配层",
            "humanizer-zh": "Contest-Orchestrator Adapter",
            "mathmodel-latex-skill": "Contest-Orchestrator Adapter",
            "latex-paper-en": "Contest-Orchestrator Adapter",
            "modelviz": "Contest-Orchestrator Adapter",
            "scipilot-figure-skill": "Contest-Orchestrator Adapter",
            "tech-route-maker": "Contest-Orchestrator Adapter",
            "tikz-scientific-figures": "Contest-Orchestrator Adapter",
            "drawio-diagram": "Contest-Orchestrator Adapter",
            "mineru-parse": "Contest-Orchestrator Adapter",
            "bzd-review-paper": "Contest-Orchestrator Adapter",
            "word-document": "Contest-Orchestrator Adapter",
            "web-access": "Contest-Orchestrator Adapter",
        }
        for name, marker in routes.items():
            with self.subTest(skill=name):
                text = skill_text(name)
                self.assertIn("contest-orchestrator", text.lower())
                self.assertIn(marker.lower(), text.lower())

    def test_common_boundary_is_explicit(self):
        for name in (
            "math-model-selector", "math-modeling", "data-science-stack",
            "heuristic-algorithms", "pyomo", "academic-writing", "humanizer-zh",
            "mathmodel-latex-skill", "latex-paper-en", "modelviz",
            "scipilot-figure-skill", "tech-route-maker", "tikz-scientific-figures",
            "drawio-diagram", "mineru-parse", "bzd-review-paper", "word-document",
            "web-access",
        ):
            text = skill_text(name).lower()
            with self.subTest(skill=name):
                self.assertRegex(text, r"workspace|项目工作区")
                self.assertRegex(text, r"evidence|证据|provenance|来源")
                self.assertRegex(text, r"handoff|回流|节点|task card|任务卡")
                self.assertRegex(text, r"negative echo|负回响|元话语|内部交流")

    def test_modeling_and_solver_routes_return_machine_readable_evidence(self):
        for name in ("math-model-selector", "math-modeling", "data-science-stack", "heuristic-algorithms", "pyomo"):
            text = skill_text(name).lower()
            with self.subTest(skill=name):
                self.assertRegex(text, r"model_contract|model blueprint|model_blueprint")
                self.assertRegex(text, r"run_manifest|result_registry|结果登记|运行清单")
                self.assertRegex(text, r"numeric_source|数值来源|seed|随机种子")

    def test_paper_routes_protect_claims_and_ordinary_prose(self):
        for name in ("academic-writing", "humanizer-zh", "mathmodel-latex-skill", "latex-paper-en"):
            text = skill_text(name).lower()
            with self.subTest(skill=name):
                self.assertRegex(text, r"formula|公式")
                self.assertRegex(text, r"citation|引用")
                self.assertRegex(text, r"ordinary prose|普通正文|元话语|内部交流")
                self.assertRegex(text, r"symbol|符号")

    def test_figure_routes_make_visual_review_default(self):
        for name in ("modelviz", "scipilot-figure-skill", "tech-route-maker", "tikz-scientific-figures", "drawio-diagram"):
            text = skill_text(name).lower()
            with self.subTest(skill=name):
                self.assertRegex(text, r"visual.*(default|always|must)|视觉.*(默认|必须|闭环)")
                self.assertRegex(text, r"render|渲染")

    def test_scipilot_modelviz_pipeline_has_single_owner_per_phase(self):
        scipilot = skill_text("scipilot-figure-skill").lower()
        modelviz = skill_text("modelviz").lower()
        contract = (ORCHESTRATOR_ROOT / "references" / "external_skill_adapters.md").read_text(
            encoding="utf-8"
        ).lower()
        for marker in ("discovery phase", "decision card", "qa phase", "semantic check", "technical check", "visual check"):
            self.assertIn(marker, scipilot)
        for marker in ("approved decision card", "execution and format export", "svg and png", "does not produce pdf"):
            self.assertIn(marker, modelviz)
        for marker in ("scipilot discovery", "modelviz generation", "scipilot qa", "contest-orchestrator registry"):
            self.assertIn(marker, contract)

    def test_figure_and_latex_formats_are_svg_png_only(self):
        policy = (ORCHESTRATOR_ROOT / "references" / "figure_policy.md").read_text(encoding="utf-8").lower()
        latex = skill_text("mathmodel-latex-skill").lower()
        self.assertIn("formats: [svg, png]", policy)
        self.assertIn("insertion_format: svg", policy)
        self.assertIn(r"\includesvg", latex)
        self.assertIn("formal figure insertion format is svg", latex)

    def test_non_figure_routes_keep_visual_review_off_by_default(self):
        for name in ("math-modeling", "data-science-stack", "heuristic-algorithms", "pyomo", "academic-writing", "humanizer-zh", "mathmodel-latex-skill", "latex-paper-en", "mineru-parse", "bzd-review-paper", "word-document", "web-access"):
            text = skill_text(name).lower()
            with self.subTest(skill=name):
                self.assertRegex(text, r"visual.*(off|opt-in|explicit)|视觉.*(关闭|默认|明确要求)")

    def test_input_and_review_routes_preserve_source_boundary(self):
        for name in ("mineru-parse", "bzd-review-paper", "word-document", "web-access"):
            text = skill_text(name).lower()
            with self.subTest(skill=name):
                self.assertRegex(text, r"source|来源|evidence|证据")
                self.assertRegex(text, r"project|workspace|项目|工作区")
                self.assertRegex(text, r"citation|引用|provenance|可追溯")


if __name__ == "__main__":
    unittest.main()
