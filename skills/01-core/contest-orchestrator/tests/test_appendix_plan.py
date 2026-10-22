import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_latex_appendix_contract.py"
PLANNER = ROOT / "scripts" / "appendix_planner.py"


def run_checker(root: Path, *args: str):
    result = subprocess.run([sys.executable, str(CHECKER), str(root), *args],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    return result.returncode, json.loads(result.stdout)


class AppendixPlanTests(unittest.TestCase):
    def test_planner_code_draft_exposes_core_appendix_mode(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "model_blueprint.yaml").write_text("""schema_version: '2.0'
project:
  composition: optimization
subproblems:
  - id: Q1
    models:
      - id: m1
        family: optimization
        modifiers: [code]
""", encoding="utf-8")
            result = subprocess.run([sys.executable, str(PLANNER), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace",
                                    env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
            self.assertEqual(result.returncode, 0, result.stdout)
            plan = json.loads(result.stdout)["plan"]
            source = plan["source_inputs"]
            self.assertEqual(source["appendix_code_mode"], "core_only")
            self.assertEqual(source["core_source_files"], [])
            code_modules = [item for item in plan["appendix_modules"] if item["kind"] == "source_code"]
            self.assertEqual(len(code_modules), 1)
            self.assertTrue(code_modules[0]["include_in_pdf"])

    def test_ready_program_plan_requires_core_and_full_source_declarations(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "appendix_plan.yaml").write_text("""schema_version: '2.0'
status: READY
planning_contract: coverage_first
subproblems:
  - id: Q1
    primary_type: optimization
    capabilities: [code]
appendix_modules:
  - module_id: app-code
    kind: source_code
    used_by: [Q1]
    required: true
    source_files: []
    paper_anchor: app:code
coverage_matrix:
  - subproblem_id: Q1
    main_section: '6.1'
    core_code_module: app-code
    long_derivation_module: null
    verification_module: null
source_inputs:
  program_used: true
  appendix_code_mode: core_only
  core_source_files: []
  full_source_files: []
  support_material_files: []
""", encoding="utf-8")
            result = subprocess.run([sys.executable, str(PLANNER), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace",
                                    env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("core_source_files", result.stdout)
            self.assertIn("full_source_files", result.stdout)

    def test_delivery_gate_code_requirement_follows_plan(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_gate_plan", str(ROOT / "scripts" / "delivery_gate.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "appendix_plan.yaml").write_text("""schema_version: '2.0'
subproblems: []
appendix_modules: []
source_inputs:
  program_used: false
""", encoding="utf-8")
            self.assertFalse(module.appendix_code_required(root, "", {"appendix_code_required": True}))
            (root / "appendix_plan.yaml").write_text("""schema_version: '2.0'
subproblems: []
appendix_modules:
  - module_id: app-code
    kind: source_code
    required: true
source_inputs: {}
""", encoding="utf-8")
            self.assertTrue(module.appendix_code_required(root, "", {"appendix_code_required": False}))

    def test_no_code_derivation_plan_does_not_require_minted(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(r"""\documentclass{article}
\begin{document}
正文详见附录A。
\section{参考文献}\bibliography{ref}
\appendix
\section{附录A 解析推导}
推导步骤和结果验证。\par
本论文没有用到程序。本论文没有支撑材料。
编译提示：-shell-escape；依赖 Pygments。
\end{document}
""", encoding="utf-8")
            (root / "derivation.md").write_text("真实长推导\n", encoding="utf-8")
            (root / "appendix_plan.yaml").write_text("""schema_version: '2.0'
status: READY
official_format:
  numbering: official_abc_if_required
  appendix_ids: [A]
subproblems:
  - id: Q1
    primary_type: analytic
    capabilities: [derivation]
appendix_modules:
  - module_id: app-q1-derivation
    kind: derivation
    used_by: [Q1]
    required: true
    source_files: [derivation.md]
    paper_anchor: app:q1-derivation
source_inputs:
  program_used: false
  long_derivation_files: [derivation.md]
""", encoding="utf-8")
            code, report = run_checker(root, "--strict")
            self.assertEqual(code, 0, report)
            self.assertEqual(report["manifest_kind"], "plan")
            self.assertFalse(report["details"]["program_used"])

    def test_draft_plan_cannot_pass_strict_gate(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(r"""\documentclass{article}
\begin{document}\section{参考文献}\bibliography{ref}\appendix
\section{附录A 推导}本论文没有用到程序。本论文没有支撑材料。
编译提示：-shell-escape；依赖 Pygments。\end{document}
""", encoding="utf-8")
            (root / "appendix_plan.yaml").write_text("""schema_version: '2.0'
status: DRAFT
official_format:
  appendix_ids: [A]
subproblems:
  - id: Q1
    primary_type: analytic
    capabilities: []
appendix_modules: []
source_inputs:
  program_used: false
""", encoding="utf-8")
            code, report = run_checker(root, "--strict")
            self.assertNotEqual(code, 0, report)
            self.assertTrue(any("DRAFT" in item for item in report["issues"]))

    def test_plan_can_define_non_three_appendix_slots(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(r"""\documentclass{article}
\usepackage{minted}\usepackage{fontspec}\setmonofont{Consolas}
\definecolor{codebg}{gray}{0.96}\usemintedstyle{vs}
\begin{document}
正文详见附录A，参见附录B。
\section{参考文献}\bibliography{ref}
\appendix
\section{附录A 推导}
\section{附录B 代码}
\medskip
\begin{minted}[bgcolor=codebg,linenos,breaklines,tabsize=4,fontsize=\small,framesep=6pt]{python}
print(1)
\end{minted}
\medskip
支撑材料文件清单：src/full.py。
编译提示：-shell-escape；依赖 Pygments。
\end{document}
""", encoding="utf-8")
            (root / "src").mkdir()
            (root / "src" / "full.py").write_text("print(1)\n", encoding="utf-8")
            (root / "derivation.md").write_text("真实推导\n", encoding="utf-8")
            (root / "appendix_plan.yaml").write_text("""schema_version: '2.0'
status: READY
official_format:
  numbering: official_abc_if_required
  appendix_ids: [A, B]
subproblems:
  - id: Q1
    primary_type: hybrid
    capabilities: [derivation, code]
appendix_modules:
  - module_id: app-derivation
    kind: derivation
    used_by: [Q1]
    required: true
    source_files: [derivation.md]
    paper_anchor: app:derivation
  - module_id: app-code
    kind: source_code
    used_by: [Q1]
    required: true
    source_files: [src/full.py]
    paper_anchor: app:code
source_inputs:
  program_used: true
  full_source_files: [src/full.py]
  long_derivation_files: [derivation.md]
  support_material_files: [src/full.py]
""", encoding="utf-8")
            code, report = run_checker(root, "--strict")
            self.assertEqual(code, 0, report)
            self.assertEqual(report["required_appendix_ids"], ["A", "B"])

    def test_planner_derives_draft_without_inventing_sources(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "model_blueprint.yaml").write_text("""schema_version: '2.0'
project:
  composition: hybrid
subproblems:
  - id: Q1
    models:
      - id: m1
        family: prediction
        modifiers: []
  - id: Q2
    models:
      - id: m2
        family: optimization
        modifiers: [uncertainty]
""", encoding="utf-8")
            result = subprocess.run([sys.executable, str(PLANNER), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace",
                                    env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "DRAFT")
            self.assertEqual(payload["plan"]["source_inputs"]["full_source_files"], [])
            kinds = {item["kind"] for item in payload["plan"]["appendix_modules"]}
            self.assertIn("prediction", kinds)
            self.assertIn("optimization", kinds)

    def test_planner_discovers_project_planning_directory(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            planning = root / "01_需求与规划"
            planning.mkdir()
            (planning / "appendix_plan.yaml").write_text("""schema_version: '2.0'
status: DRAFT
subproblems:
  - id: Q1
    primary_type: analytic
    capabilities: []
appendix_modules: []
source_inputs:
  program_used: false
""", encoding="utf-8")
            result = subprocess.run([sys.executable, str(PLANNER), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace",
                                    env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "DRAFT")
            self.assertEqual(Path(payload["plan_path"]).parent.name, "01_需求与规划")
            self.assertEqual(Path(payload["plan_path"]).name, "appendix_plan.yaml")

    def test_checker_discovers_project_planning_directory(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper"
            planning = root / "01_需求与规划"
            paper.mkdir(); planning.mkdir()
            (paper / "paper.tex").write_text(r"""\documentclass{article}
\begin{document}
正文详见附录A。
\section{参考文献}\bibliography{ref}
\appendix
\section{附录A 推导}推导材料。\par
本论文没有用到程序。本论文没有支撑材料。
编译提示：-shell-escape；依赖 Pygments。
\end{document}
""", encoding="utf-8")
            (root / "derivation.md").write_text("真实推导\n", encoding="utf-8")
            (planning / "appendix_plan.yaml").write_text("""schema_version: '2.0'
status: READY
official_format:
  appendix_ids: [A]
subproblems:
  - id: Q1
    primary_type: analytic
    capabilities: [derivation]
appendix_modules:
  - module_id: app-derivation
    kind: derivation
    used_by: [Q1]
    required: true
    source_files: [derivation.md]
    paper_anchor: app:derivation
source_inputs:
  program_used: false
  long_derivation_files: [derivation.md]
""", encoding="utf-8")
            code, report = run_checker(paper, "--project-root", str(root), "--strict")
            self.assertEqual(code, 0, report)
            self.assertIn("01_需求与规划", report["contract"])

    def test_coverage_first_plan_requires_real_per_question_mapping(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "appendix_plan.yaml").write_text("""schema_version: '2.0'
status: READY
planning_contract: coverage_first
subproblems:
  - id: Q1
    primary_type: optimization
    capabilities: [code]
appendix_modules:
  - module_id: app-code
    kind: source_code
    used_by: [Q1]
    required: true
    source_files: [src/core.py]
    paper_anchor: app:code
source_inputs:
  program_used: true
  appendix_code_mode: core_only
  core_source_files: [src/core.py]
  full_source_files: [src/core.py]
  support_source_files: [src/core.py]
  support_material_files: [src/core.py]
""", encoding="utf-8")
            result = subprocess.run([sys.executable, str(PLANNER), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("coverage_matrix", result.stdout)
            plan = (root / "appendix_plan.yaml").read_text(encoding="utf-8") + """coverage_matrix:
  - subproblem_id: Q1
    main_section: '6.1'
    core_code_module: app-code
    long_derivation_module: null
    verification_module: null
"""
            (root / "appendix_plan.yaml").write_text(plan, encoding="utf-8")
            result = subprocess.run([sys.executable, str(PLANNER), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
