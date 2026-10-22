import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "delivery_manifest.py"
DOI = ROOT / "scripts" / "verify_doi.py"
REGISTRY = ROOT / "scripts" / "figure_registry.py"
MIGRATE = ROOT / "scripts" / "migrate_figure_registry.py"
LATEX = ROOT / "scripts" / "latex_warning_check.py"
DELIVERY = ROOT / "scripts" / "delivery_all.py"
VISUAL = ROOT / "scripts" / "visual_critic.py"
ROUTER = ROOT / "scripts" / "scope_router.py"
LITERATURE = ROOT / "scripts" / "check_literature_citation.py"
HEADINGS = ROOT / "scripts" / "check_heading_levels.py"
MODELING = ROOT / "scripts" / "check_modeling_contract.py"
APPENDIX = ROOT / "scripts" / "check_appendix_contract.py"
CODE_APPENDIX = ROOT / "scripts" / "check_code_appendix.py"
ANONYMITY = ROOT / "scripts" / "check_anonymity.py"
TRACEABILITY = ROOT / "scripts" / "check_model_traceability.py"
META_TEXT = ROOT / "scripts" / "check_submission_meta_text.py"
LAYOUT = ROOT / "scripts" / "check_tex_layout_patterns.py"
TEX_REFS = ROOT / "scripts" / "check_tex_references.py"
FORMAL_DRIFT = ROOT / "scripts" / "check_formal_delivery_drift.py"
HARD_REQUIREMENTS = ROOT / "scripts" / "check_paper_hard_requirements.py"
MODEL_EVIDENCE = ROOT / "scripts" / "check_model_evidence.py"
DERIVATION = ROOT / "scripts" / "check_derivation_chain.py"
INIT_CONTRACT = ROOT / "scripts" / "init_model_contract.py"
BLUEPRINT = ROOT / "scripts" / "compile_model_blueprint.py"
SYMBOLS = ROOT / "scripts" / "check_symbol_consistency.py"
INTERFACES = ROOT / "scripts" / "check_interface_contract.py"
PAPER_CHECK = ROOT / "scripts" / "paper_check.py"


class DeliveryToolTests(unittest.TestCase):
    def make_workspace(self):
        raw = tempfile.TemporaryDirectory()
        ws = Path(raw.name)
        paper = ws / "paper"
        paper.mkdir()
        for name in ("paper.tex", "paper.pdf", "ref.bib"):
            (paper / name).write_text(name, encoding="utf-8")
        (ws / "figure_registry.json").write_text(json.dumps({"figures": {
            "fig_01": {"kind": "data", "generator": "scipilot", "source_files": ["paper/paper.tex"],
                       "formats": ["png", "pdf"], "qa_status": "pass"}}}), encoding="utf-8")
        return raw, ws, paper

    def test_paper_check_skips_visual_qa_by_default(self):
        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw)
            (paper / "paper.tex").write_text(
                "\\begin{abstract}摘要内容。\\end{abstract}\n\\section{问题重述}\n正文。\n",
                encoding="utf-8",
            )
            (paper / "paper.pdf").write_bytes(b"placeholder")
            (paper / "results").mkdir()
            result = subprocess.run(
                [sys.executable, str(PAPER_CHECK), str(paper)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertIn("视觉质检(PDF): SKIPPED_USER_OPT_IN", result.stdout)

    def test_manifest_rejects_stale_pdf_and_records_hash(self):
        raw, ws, paper = self.make_workspace()
        try:
            pdf = paper / "paper.pdf"
            tex = paper / "paper.tex"
            now = time.time()
            os.utime(pdf, (now - 10, now - 10))
            os.utime(tex, (now, now))
            result = subprocess.run([sys.executable, str(MANIFEST), str(ws)], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("新鲜度", result.stdout)
            report = json.loads((paper / "delivery_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(report["schema_version"], "2.0")
            self.assertIn("sha256", report["files"]["paper.tex"])
            self.assertTrue(any(item["path"].endswith("paper.tex") for item in report["artifacts"]))
        finally:
            raw.cleanup()

    def test_manifest_rejects_temporary_root(self):
        raw, ws, _ = self.make_workspace()
        try:
            result = subprocess.run([sys.executable, str(MANIFEST), str(ws)], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 1)
            self.assertIn("临时", result.stdout)
        finally:
            raw.cleanup()

    def test_manifest_discovers_standard_nested_layout_and_list_registry(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_manifest", str(MANIFEST))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "03_文档" / "paper"
            paper.mkdir(parents=True)
            (paper / "paper.tex").write_text("fixture", encoding="utf-8")
            registry = root / "05_输出与交付" / "figure_registry.json"
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({"schema_version": "2.0", "figures": [
                {"id": "fig_01", "kind": "data"}
            ]}), encoding="utf-8")
            found_paper, found_registry = module.discover(root)
            self.assertEqual(found_paper, paper)
            self.assertEqual(found_registry, registry)
            self.assertEqual(module.registry_summary(registry), (1, []))
            final_report = root / "05_输出与交付" / "正式交付" / "严格门禁报告.json"
            final_report.parent.mkdir(parents=True)
            final_report.write_text("{}", encoding="utf-8")
            self.assertTrue(module.is_under(final_report, [root / "05_输出与交付" / "正式交付"]))

    def test_doi_syntax_check_and_duplicate_detection(self):
        with tempfile.TemporaryDirectory() as raw:
            bib = Path(raw) / "ref.bib"
            bib.write_text("@article{x,\n doi = {10.1234/example.doi}\n}\n@article{y, doi={10.1234/example.doi}}\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(DOI), str(bib)], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            payload = json.loads(result.stdout)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(payload["passed"])
            self.assertTrue(any(item["duplicate"] for item in payload["results"]))

    def test_figure_registry_accepts_canonical_routes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "data.csv").write_text("x,y\n1,2\n", encoding="utf-8")
            (root / "plot.py").write_text("# deterministic plot fixture\n", encoding="utf-8")
            (root / "fig_data.decision.json").write_text("{}", encoding="utf-8")
            registry = root / "figure_registry.json"
            registry.write_text(json.dumps({"schema_version": "2.0", "figures": {
                "fig_data": {"kind": "data", "generator": "modelviz", "semantic_qa": "scipilot-figure-skill", "decision_author": "scipilot-figure-skill", "decision_card": "fig_data.decision.json", "source_files": ["data.csv"], "script": "plot.py",
                             "formats": ["svg", "png"], "insertion_format": "svg", "layout_mode": "single", "qa_status": "pass"},
                "fig_flow": {"kind": "flowchart", "generator": "tech-route-maker", "diagram_role": "technical_roadmap", "source_files": ["data.csv"], "script": "route.json",
                             "formats": ["svg", "png"], "insertion_format": "svg", "layout_mode": "single", "qa_status": "reviewed"}}}), encoding="utf-8")
            (root / "route.json").write_text("{}", encoding="utf-8")
            result = subprocess.run([sys.executable, str(REGISTRY), str(registry), "--workspace", str(root)], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_figure_registry_rejects_wrong_generator(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "figure_registry.json").write_text(json.dumps({"figures": {
                "fig_flow": {"kind": "flowchart", "generator": "fireworks-tech-graph", "source_files": [],
                             "formats": ["png"], "qa_status": "pass"}}}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(REGISTRY), str(root / "figure_registry.json"), "--workspace", str(root)], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)

    def test_figure_registry_accepts_tikz_schematic_and_explicit_drawio(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "ledger.yaml").write_text("Q1: fixture\n", encoding="utf-8")
            (root / "figure.tex").write_text("\\documentclass{standalone}\n", encoding="utf-8")
            (root / "figure.drawio").write_text("<mxfile/>", encoding="utf-8")
            registry = root / "figure_registry.json"
            registry.write_text(json.dumps({"schema_version": "2.0", "figures": {
                "fig_schematic": {"kind": "schematic", "generator": "tikz-scientific-figures",
                                   "source_files": ["ledger.yaml"], "script": "figure.tex",
                                   "formats": ["svg", "png"], "insertion_format": "svg", "layout_mode": "single", "qa_status": "pass"},
                "fig_drawio": {"kind": "drawio", "generator": "drawio-diagram", "user_requested": True,
                               "source_files": ["ledger.yaml"], "script": "figure.drawio",
                               "formats": ["svg", "png"], "insertion_format": "svg", "layout_mode": "single", "qa_status": "reviewed"}
            }}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(REGISTRY), str(registry), "--workspace", str(root)],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_figure_registry_rejects_pdf_image_output(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "data.csv").write_text("x,y\n1,2\n", encoding="utf-8")
            (root / "plot.py").write_text("# fixture\n", encoding="utf-8")
            registry = root / "figure_registry.json"
            registry.write_text(json.dumps({"schema_version": "2.0", "figures": {
                "fig_data": {"kind": "data", "generator": "modelviz", "semantic_qa": "scipilot-figure-skill",
                             "source_files": ["data.csv"], "script": "plot.py", "formats": ["svg", "png", "pdf"],
                             "insertion_format": "svg", "qa_status": "pass"}
            }}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(REGISTRY), str(registry), "--workspace", str(root)],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("pdf", result.stdout.lower())

    def test_legacy_registry_migration_preserves_generator_provenance(self):
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "legacy.json"
            output = Path(raw) / "v2.json"
            source.write_text(json.dumps({"fig_old": {"type": "data", "generated_by": "python-matplotlib",
                                                       "data_source": "results/a.json, results/b.json",
                                                       "formats": ["png"], "qa_status": "reviewed"}}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(MIGRATE), str(source), "--out", str(output)], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(output.read_text(encoding="utf-8"))
            item = payload["figures"]["fig_old"]
            self.assertEqual(item["legacy_generator"], "python-matplotlib")
            self.assertEqual(item["source_files"], ["results/a.json", "results/b.json"])
            self.assertEqual(item["generator"], "")

    def test_latex_warning_body_threshold_blocks(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text("\\section{正文}\n\\appendix\n", encoding="utf-8")
            (root / "paper.log").write_text("Overfull \\hbox (4.0pt too wide) in paragraph at lines 1--2\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(LATEX), str(root)], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(json.loads((root / "latex_warning_report.json").read_text(encoding="utf-8"))["passed"])

    def test_latex_warning_detected_at_line_format_blocks(self):
        """XeLaTeX/MiKTeX 的 detected-at-line 格式也必须被识别。"""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text("\\section{正文}\n" + ("% body\n" * 100), encoding="utf-8")
            (root / "paper.log").write_text(
                "Overfull \\hbox (12.5pt too wide) detected at line 68\n",
                encoding="utf-8",
            )
            result = subprocess.run([sys.executable, str(LATEX), str(root)], capture_output=True, text=True,
                                     encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((root / "latex_warning_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["body"][0]["lines"], "68-68")

    def test_visual_critic_rejects_internal_delivery_text(self):
        with tempfile.TemporaryDirectory() as raw:
            text_path = Path(raw) / "paper.txt"
            text_path.write_text("参考文献索引\n正文参考文献数据库为 paper/ref.bib。\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VISUAL), str(text_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("论文内部交付文字/占位字段", result.stdout)

    def test_delivery_help_is_available(self):
        result = subprocess.run([sys.executable, str(DELIVERY), "--help"], capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--strict", result.stdout)
        self.assertIn("--mode", result.stdout)
        self.assertIn("--collab-policy", result.stdout)

    def test_scope_router_blocks_missing_subproblem_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            result = subprocess.run(
                [sys.executable, str(ROUTER), "--scope", "SUBPROBLEM", "--workspace", raw],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["input_gate"]["status"], "FAIL")
            self.assertEqual(payload["execution_status"], "BLOCKED")

    def test_scope_router_emits_verifiable_digest(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "problem.pdf").write_bytes(b"fixture")
            plan = root / "scope_plan.json"
            result = subprocess.run(
                [sys.executable, str(ROUTER), "--scope", "FULL_CONTEST", "--workspace", raw, "--out", str(plan)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(plan.read_text(encoding="utf-8"))
            digest = payload.pop("plan_digest")
            import hashlib
            canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            self.assertEqual(digest, hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_scope_router_infers_full_contest_for_complete_paper_delivery(self):
        result = subprocess.run(
            [sys.executable, str(ROUTER), "--prompt", "写一篇完整的论文并严格跑交付"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["scope"], "FULL_CONTEST")
        self.assertEqual(payload["execution_status"], "BLOCKED")  # no problem evidence is intentional

    def test_scope_router_prefers_formal_delivery_over_audit_words(self):
        result = subprocess.run(
            [sys.executable, str(ROUTER), "--prompt", "正式交付：完整数学建模、论文、严格审计和稳定交付包"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["scope"], "FULL_CONTEST")
        self.assertEqual(payload["execution_status"], "BLOCKED")  # no problem evidence is intentional

    def test_scope_router_rejects_skill_installation_as_workspace(self):
        result = subprocess.run(
            [sys.executable, str(ROUTER), "--scope", "FULL_CONTEST",
             "--workspace", str(ROOT), "--strict"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["canonical_workspace"])
        self.assertEqual(payload["input_gate"]["status"], "FAIL")
        self.assertIn("技能安装目录", payload["input_gate"]["message"])

    def test_delivery_all_rejects_skill_installation_root(self):
        result = subprocess.run(
            [sys.executable, str(DELIVERY), str(ROOT), "--strict"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("技能安装目录不能作为正式项目根目录", result.stdout)

    def test_visual_contract_propagates_fail_exit_code(self):
        from docx import Document

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "invalid.docx"
            document = Document()
            document.add_paragraph("short")
            document.save(path)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "check_visual_contract.py"), str(path)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("Visual Contract 结果: FAIL", result.stdout)

    def test_citation_counter_does_not_count_unused_bib_entries(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_gate", str(ROOT / "scripts" / "delivery_gate.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "ref.bib").write_text(
                "@article{used, title={Used}}\n@article{unused, title={Unused}}\n", encoding="utf-8"
            )
            stats = module.citation_stats(root, "正文 \\cite{used}。")
            self.assertEqual(stats["unique_cited_count"], 1)
            self.assertEqual(stats["unused_bib_keys"], ["unused"])

    def test_delivery_gate_rejects_data_figure_without_scipilot_decision_card(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_gate_figure_card", str(ROOT / "scripts" / "delivery_gate.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "results.json").write_text("{}", encoding="utf-8")
            (root / "plot.py").write_text("# fixture\n", encoding="utf-8")
            (root / "figure_registry.json").write_text(json.dumps({"schema_version": "2.0", "figures": {
                "fig_q1": {"kind": "data", "generator": "modelviz", "semantic_qa": "scipilot-figure-skill",
                           "source_files": ["results.json"], "script": "plot.py", "formats": ["svg", "png"],
                           "insertion_format": "svg", "layout_mode": "single", "qa_status": "pass"}
            }}), encoding="utf-8")
            issues, warns, info = [], [], []

            module.figure_registry_checks(root, issues, warns, info)

            self.assertTrue(any("SciPilot 图表决策卡" in issue for issue in issues), issues)

    def test_aux_label_page_prefers_aux_matching_target_pdf(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_gate_aux", str(ROOT / "scripts" / "delivery_gate.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            label = r"\newlabel{BodyStart}{{}{1}{}{Doc-Start}{}}\n"
            (root / "paper.aux").write_text(label.replace("{1}", "{2}"), encoding="utf-8")
            (root / "paper_v418_repair.aux").write_text(label, encoding="utf-8")
            self.assertEqual(module.aux_label_page(root, "BodyStart", "paper_v418_repair"), 1)

    def test_reference_gate_uses_hard_range_and_advisory_recommendation(self):
        import yaml
        config = yaml.safe_load((ROOT / "core" / "competition_gates.yaml").read_text(encoding="utf-8"))
        self.assertEqual(config["guosai"]["reference_min"], 6)
        self.assertEqual(config["guosai"]["reference_max"], 11)
        self.assertEqual(config["guosai"]["reference_recommended_min"], 8)
        self.assertEqual(config["guosai"]["reference_recommended_max"], 10)

    def test_all_harness_profiles_share_the_user_literature_hard_range(self):
        import yaml
        config = yaml.safe_load((ROOT / "core" / "competition_gates.yaml").read_text(encoding="utf-8"))
        for profile in ("default", "mcm_icm"):
            self.assertEqual(config[profile]["reference_min"], 6)
            self.assertEqual(config[profile]["reference_max"], 11)
            self.assertEqual(config[profile]["reference_recommended_min"], 8)
            self.assertEqual(config[profile]["reference_recommended_max"], 10)

    def test_default_and_guosai_profiles_do_not_impose_unsupported_page_minimums(self):
        import yaml
        config = yaml.safe_load((ROOT / "core" / "competition_gates.yaml").read_text(encoding="utf-8"))
        self.assertIsNone(config["default"]["body_min_pages"])
        self.assertIsNone(config["guosai"]["body_min_pages"])

    def test_unknown_profile_inherits_harness_literature_range(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_gate", str(ROOT / "scripts" / "delivery_gate.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cfg = module.load_config(ROOT / "core" / "competition_gates.yaml", "some_other_contest")
        self.assertTrue(cfg["_profile_fallback"])
        self.assertEqual(cfg["reference_min"], 6)
        self.assertEqual(cfg["reference_max"], 11)
        self.assertEqual(cfg["reference_recommended_min"], 8)
        self.assertEqual(cfg["reference_recommended_max"], 10)

    def test_literature_checker_handles_windows_unicode_output(self):
        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw) / "paper.txt"
            paper.write_text("正文没有足够引用 [1]。", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(LITERATURE), str(paper), "--verbose"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertNotIn("UnicodeEncodeError", result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_literature_checker_expands_grouped_citations_and_checks_placement(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "literature_checker", str(ROOT / "scripts" / "check_literature_citation.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        citations = module.extract_citations_from_text(
            "该模型采用公开色散参数作为参数来源[1-3]。另有算法先例[4,5]。"
        )
        self.assertEqual(sorted(c["cite_id"] for c in citations), [1, 2, 3, 4, 5])
        self.assertTrue(all(c["placement_ok"] for c in citations))

    def test_literature_checker_ignores_probability_interval_and_maps_stable_reference_ids(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "literature_checker_stable_ids", str(ROOT / "scripts" / "check_literature_citation.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        citations = module.extract_citations_from_text("概率参数位于[0,1]区间；方法依据见[1-2]。")
        self.assertEqual(sorted(c["cite_id"] for c in citations), [1, 2])
        self.assertEqual(module.reference_ids([
            {"ref_ID": "R01"}, {"ref_ID": "R02"}, {"ref_ID": "R10"}
        ]), {1, 2, 10})

    def test_abstract_checker_follows_input_source_and_parses_quad_keywords(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "abstract_checker", str(ROOT / "scripts" / "check_abstract_contract.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw)
            (paper / "sections").mkdir()
            (paper / "paper.tex").write_text(
                r"\documentclass{article}\begin{document}\input{sections/00_abstract}\end{document}",
                encoding="utf-8",
            )
            abstract = paper / "sections" / "00_abstract.tex"
            abstract.write_text(
                r"\begin{abstract}背景、假设与模型。\keywords{验收抽样\quad 状态递推\quad 稳健决策\quad 置信界}\end{abstract}",
                encoding="utf-8",
            )
            source = module._locate_source(paper)
            self.assertEqual(source, abstract.resolve())
            self.assertEqual(module._keywords("", abstract.read_text(encoding="utf-8")), [
                "验收抽样", "状态递推", "稳健决策", "置信界"
            ])

    def test_literature_checker_strictly_rejects_citation_without_role_context(self):
        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw) / "paper.txt"
            paper.write_text("某文献[1]继续说明。", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(LITERATURE), str(paper), "--strict"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("FAIL", result.stdout)

    def test_delivery_rejects_non_full_scope(self):
        result = subprocess.run(
            [sys.executable, str(DELIVERY), str(ROOT), "--scope", "DELIVERY_AUDIT"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("只接受 FULL_CONTEST", result.stdout)

    def test_delivery_resolves_relative_paper_dir_from_project_root(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_all", str(DELIVERY))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        root = Path("C:/workspace/project")
        self.assertEqual(module.find_paper_dir(root, "paper"), root / "paper")

    def test_delivery_refreshes_only_compiled_paper_evidence(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_all_refresh", str(DELIVERY))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper"
            paper.mkdir()
            tex = paper / "paper.tex"
            pdf = paper / "paper.pdf"
            source = root / "solve.py"
            tex.write_text("paper", encoding="utf-8")
            pdf.write_bytes(b"%PDF-final")
            source.write_text("print(1)\n", encoding="utf-8")
            manifest = root / ".contest" / "runs" / "run.test" / "run_manifest.json"
            manifest.parent.mkdir(parents=True)
            payload = {
                "outputs": [
                    {"path": "paper/paper.tex", "sha256": "stale"},
                    {"path": "paper/paper.pdf", "sha256": "stale"},
                    {"path": "solve.py", "sha256": "keep-me"},
                ]
            }
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            refreshed = module.refresh_compiled_paper_evidence(root, tex, pdf)
            saved = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertFalse(refreshed["errors"])
            self.assertEqual(saved["outputs"][0]["sha256"], module._sha256(tex))
            self.assertEqual(saved["outputs"][1]["sha256"], module._sha256(pdf))
            self.assertEqual(saved["outputs"][2]["sha256"], "keep-me")

    def test_delivery_syncs_formal_package_after_compile(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_all_sync", str(DELIVERY))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper"
            paper.mkdir()
            tex = paper / "paper.tex"
            pdf = paper / "paper.pdf"
            tex.write_text("source", encoding="utf-8")
            pdf.write_bytes(b"%PDF-current")
            (paper / "delivery_manifest.json").write_text("{}", encoding="utf-8")
            (root / "figure_registry.json").write_text("{}", encoding="utf-8")
            (root / "references.yaml").write_text("[]", encoding="utf-8")
            planning = root / "01_需求与规划"
            planning.mkdir()
            (planning / "citation_map.json").write_text("{}", encoding="utf-8")
            delivery = root / "05_输出与交付"
            delivery.mkdir()
            (delivery / "support_materials_demo.zip").write_bytes(b"zip")
            reports = root / "reports"
            reports.mkdir()
            (reports / "gate.json").write_text("{}", encoding="utf-8")

            result = module.sync_formal_delivery(root, tex, pdf, reports)
            formal = root / "05_输出与交付" / "正式交付"
            self.assertIn("final_submission.pdf", result["copied"])
            self.assertEqual((formal / "final_submission.pdf").read_bytes(), pdf.read_bytes())
            self.assertTrue((formal / "support_materials_demo.zip").is_file())
            self.assertTrue((formal / "reports" / "gate.json").is_file())
            self.assertIn(module._sha256(pdf).upper(), (formal / "FINAL_INDEX.md").read_text(encoding="utf-8"))

    def test_hard_requirements_accepts_reference_heading_after_table(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("hard_requirements", str(HARD_REQUIREMENTS))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(module.has_reference_heading("表3\n数据\n参考文献\n[1] 条目"))
        self.assertFalse(module.has_reference_heading("正文中提及参考文献[1]，但不是标题。"))

    def test_delivery_classifies_shadow_json_warn_as_warn(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_all_warn", str(DELIVERY))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(module.structured_warning('{"gate_status": "WARN"}'))
        self.assertFalse(module.structured_warning("DeprecationWarning: old API"))
        self.assertFalse(module.is_blocking({"status": "WARN", "blocking_on_warn": False}, True))
        self.assertTrue(module.is_blocking({"status": "WARN", "blocking_on_warn": True}, True))

    def test_heading_checker_accepts_data_preprocessing_and_keywords_macro(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_heading_levels", str(HEADINGS))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tex = r"""
\ctexset{section={name={,、},number=\chinese{section}}}
\begin{abstract}摘要内容。\keywords{\textbf{最小二乘法}；\textbf{参数估计}}\end{abstract}
\section{数据预处理}
\section{模型建立与求解}
\clearpage
\appendix
\renewcommand{\thesection}{\Alph{section}}
"""
        report = module.check(tex)
        self.assertTrue(report["7 一级标题八章"].startswith("PASS"), report)
        self.assertTrue(report["9 关键词/分页"].startswith("PASS"), report)

    def test_heading_checker_allows_references_to_flow_naturally(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_heading_levels_flowing_references", str(HEADINGS))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tex = r"""
\ctexset{section={name={,、},number=\chinese{section}}}
\noindent\textbf{关键词}：刚体链；碰撞检测
\section{问题重述}
\section{模型建立与求解}
\begin{thebibliography}{9}\end{thebibliography}
\appendix
\renewcommand{\thesection}{附录\Alph{section}}
"""
        report = module.check(tex)
        self.assertTrue(report["9 关键词/分页"].startswith("PASS"), report)

    def test_delivery_gate_rejects_large_whitespace_page(self):
        import importlib.util
        import pymupdf
        gate_path = ROOT / "scripts" / "delivery_gate.py"
        spec = importlib.util.spec_from_file_location("delivery_gate_whitespace", str(gate_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as raw:
            pdf = Path(raw) / "sparse.pdf"
            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_text((72, 90), "Only one short paragraph remains at the top of this page.")
            doc.save(str(pdf))
            doc.close()
            issues, warnings, info = [], [], []
            module.visual_sanity_checks(pdf, issues, warnings, info)
            self.assertTrue(any("大面积异常留白" in issue for issue in issues), (issues, warnings, info))

    def test_modeling_contract_rejects_underweight_model_chapter(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            tex = root / "paper.tex"
            tex.write_text(
                "\\section{问题重述}\n背景。\n"
                "\\section{模型建立与求解}\n目标函数和约束。\n"
                "\\section{模型检验与灵敏度分析}\n扰动检验。\n"
                "\\section{参考文献}\n",
                encoding="utf-8",
            )
            result = subprocess.run([sys.executable, str(MODELING), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("低于阻断阈值", result.stdout)

    def test_modeling_contract_rejects_selection_leakage_in_validation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\section{模型建立与求解}\n" + ("思路约束求解结果。" * 30) +
                "\\section{模型检验}\n为什么选择该模型的原因是稳定。\n\\section{参考文献}\n",
                encoding="utf-8",
            )
            result = subprocess.run([sys.executable, str(MODELING), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("检验章节包含模型选型叙事", result.stdout)

    def test_modeling_contract_expands_local_input_files(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "method.tex").write_text("思路约束求解结果。" * 60, encoding="utf-8")
            (root / "paper.tex").write_text(
                "\\section{问题重述}\n背景。\n\\section{模型建立与求解}\n"
                "\\input{method}\n\\section{模型检验}\n扰动结果。\n\\section{参考文献}\n",
                encoding="utf-8",
            )
            result = subprocess.run([sys.executable, str(MODELING), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_appendix_and_code_contract_require_header_and_style(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "q1.py"
            source.write_text("# 功能：求解问题一\n# 输入：数据\n# 输出：结果\nprint('ok')\n", encoding="utf-8")
            (root / "paper.tex").write_text(
                "\\appendix\n\\section{材料清单}\n\\section{源代码}\n"
                "\\lstset{backgroundcolor=\\color[gray]{0.96},frame=single,numbers=left,\n"
                "basicstyle=\\footnotesize\\ttfamily}\n"
                "\\lstinputlisting{q1.py}\n",
                encoding="utf-8",
            )
            app = subprocess.run([sys.executable, str(APPENDIX), str(root)], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace")
            code = subprocess.run([sys.executable, str(CODE_APPENDIX), str(root)], capture_output=True,
                                  text=True, encoding="utf-8", errors="replace")
            self.assertEqual(app.returncode, 0, app.stdout)
            self.assertEqual(code.returncode, 0, code.stdout)

    def test_appendix_contract_requires_no_code_statement(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text("\\appendix\n\\section{材料清单}\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(APPENDIX), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("无代码声明", result.stdout)

    def test_anonymity_contract_rejects_internal_delivery_text(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text("\\section{参考文献索引}\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(ANONYMITY), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("internal_delivery", result.stdout)

    def test_modeling_contract_strict_reports_missing_subproblem_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\section{问题重述}\n背景。\n" +
                "\\section{模型建立与求解}\n" +
                "\\subsection{问题一}\n思路、模型、求解。\n" +
                ("结果和约束。" * 80) +
                "\\section{模型检验}\n扰动结果。\n\\section{参考文献}\n",
                encoding="utf-8")
            result = subprocess.run([sys.executable, str(MODELING), str(root), "--contract-strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["gate_status"], "BLOCK")
            self.assertTrue(payload["subproblems"])
            self.assertIn("assumptions", payload["subproblems"][0]["evidence_missing"])
            self.assertIn("reliability", payload["subproblems"][0]["evidence_missing"])

    def test_modeling_contract_strict_accepts_complete_profile_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            evidence = ("思路 假设 模型 约束 推导 由式(1)可得 算法 初值 搜索区间 "
                        "终止条件 结果 表1 敏感性 扰动 残差。")
            (root / "paper.tex").write_text(
                "\\section{问题重述}\n" + ("背景分析。" * 900) + "\n"
                "\\section{符号说明}\n符号、含义与单位统一说明。\n"
                "\\section{模型建立与求解}\n\\subsection{问题一}\n"
                "本问围绕题目要求建立可计算模型，结合已知数据与约束说明建模思路，"
                "并说明本问输出与后续求解结果之间的关系。\n"
                "\\subsubsection{模型建立}\n"
                + (evidence + " 建模思路。最终求解模型如下："
                   "\\begin{equation}x=1\\label{eq:complete_model}\\end{equation}\n") * 25 +
                "\\subsubsection{模型求解与结果分析}\n"
                + (evidence + " 求解结果表明模型结果具有稳定性，结果分析与题目目标一致。") * 25 +
                "\\section{模型检验}\n扰动结果。\n\\section{参考文献}\n",
                encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(MODELING), str(root), "--contract-strict"],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["gate_status"], "PASS")
            self.assertEqual(payload["subproblems"][0]["evidence_missing"], [])

    def test_model_evidence_and_derivation_contract_pass_valid_fixture(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "results").mkdir()
            (root / "results" / "q1_results.json").write_text('{"value": 1}\n', encoding="utf-8")
            (root / "paper.tex").write_text(
                "\\section{模型建立与求解}\n\\subsection{问题一}\n"
                "问题映射。假设。符号单位。结果来源。可靠性。\n"
                "定义基础关系。由基础关系推导目标关系。代入边界条件得到结果。\n"
                "\\begin{equation}x=1\\label{eq:q1_00}\\end{equation}\n"
                "\\begin{equation}y=x+1\\label{eq:q1_01}\\end{equation}\n",
                encoding="utf-8")
            (root / "model_contract.yaml").write_text(
                "schema_version: '1.0'\nsubproblems:\n"
                "  - id: Q1\n    primary_capability: mechanistic\n    capabilities: []\n"
                "    evidence:\n"
                "      problem_mapping: {status: pass, text_anchors: ['问题映射']}\n"
                "      assumptions: {status: pass, text_anchors: ['假设']}\n"
                "      symbols_units: {status: pass, text_anchors: ['符号单位']}\n"
                "      mechanism_mapping: {status: pass, text_anchors: ['基础关系']}\n"
                "      formula_derivation: {status: pass, text_anchors: ['推导目标']}\n"
                "      result_source: {status: pass, text_anchors: ['结果来源'], source_files: ['results/q1_results.json']}\n"
                "      reliability: {status: pass, text_anchors: ['可靠性']}\n",
                encoding="utf-8")
            (root / "derivation_registry.yaml").write_text(
                "schema_version: '1.0'\nequations:\n"
                "  - {id: eq0, kind: definition, label: eq:q1_00}\n"
                "  - id: eq1\n    kind: derived\n    label: eq:q1_01\n    depends_on: [eq0]\n"
                "    assumptions: ['边界条件满足']\n"
                "    derivation_steps: ['由基础关系推导目标关系', '代入边界条件得到结果']\n",
                encoding="utf-8")
            evidence = subprocess.run([sys.executable, str(MODEL_EVIDENCE), str(root), "--strict"],
                                       capture_output=True, text=True, encoding="utf-8", errors="replace")
            derivation = subprocess.run([sys.executable, str(DERIVATION), str(root), "--strict"],
                                        capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(evidence.returncode, 0, evidence.stdout)
            self.assertEqual(derivation.returncode, 0, derivation.stdout)

    def test_init_model_contract_creates_non_destructive_draft(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\section{模型建立与求解}\n\\subsection{问题一}\n内容。\n"
                "\\subsection{问题二}\n内容。\n", encoding="utf-8")
            created = subprocess.run([sys.executable, str(INIT_CONTRACT), str(root)],
                                     capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            payload = (root / "model_contract.yaml").read_text(encoding="utf-8")
            self.assertIn("contract_version: v4.13", payload)
            self.assertIn("id: Q1", payload)
            self.assertIn("id: Q2", payload)
            second = subprocess.run([sys.executable, str(INIT_CONTRACT), str(root)],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("避免覆盖", second.stdout + second.stderr)

    def test_init_model_contract_parses_double_digit_chinese_question(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\section{模型建立与求解}\n\\subsection{问题十一}\n内容。\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(INIT_CONTRACT), str(root)],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("id: Q11", (root / "model_contract.yaml").read_text(encoding="utf-8"))

    def test_model_evidence_blocks_fabricated_anchor_in_strict_mode(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text("\\section{模型建立与求解}\n\\subsection{问题一}\n假设。\n", encoding="utf-8")
            (root / "model_contract.yaml").write_text(
                "schema_version: '1.0'\nsubproblems:\n"
                "  - id: Q1\n    capabilities: []\n    evidence:\n"
                "      problem_mapping: {status: pass, text_anchors: ['不存在的正文锚点']}\n"
                "      assumptions: {status: pass, text_anchors: ['假设']}\n"
                "      symbols_units: {status: pass, text_anchors: ['符号单位']}\n"
                "      result_source: {status: pass, text_anchors: ['结果来源']}\n"
                "      reliability: {status: pass, text_anchors: ['可靠性']}\n",
                encoding="utf-8")
            result = subprocess.run([sys.executable, str(MODEL_EVIDENCE), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("正文出现", result.stdout)

    def test_enhanced_evidence_rejects_keyword_only_card(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\section{模型建立与求解}\\n\\subsection{问题一}\\n"
                "题目 假设 符号 单位 候选 选择 舍弃 算法 初值 约束 结果 敏感性。\\n",
                encoding="utf-8")
            entries = ["problem_mapping", "assumptions", "symbols_units", "route_comparison",
                       "algorithm_card", "intermediate_results", "literature_basis", "innovation_delta",
                       "result_source", "reliability"]
            evidence = "\n".join(
                f"      {key}: {{status: pass, text_anchors: ['{key}']}}" for key in entries
            )
            (root / "model_contract.yaml").write_text(
                "schema_version: '2.1'\nevidence_quality: enhanced\nsubproblems:\n"
                "  - id: Q1\n    capabilities: []\n    evidence:\n" + evidence + "\n",
                encoding="utf-8")
            result = subprocess.run([sys.executable, str(MODEL_EVIDENCE), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("信息密度不足", result.stdout)

    def test_enhanced_evidence_accepts_rich_subproblem_card(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            body = (
                "题目输入数据映射到输出目标和变量。假设样本在观测区间内连续，简化会带来边界误差，"
                "适用范围限定在给定数据。符号变量参数及其单位和范围见表1。"
                "候选路线包括解析路线、数值路线和仿真方案，最终选择数值路线，舍弃解析路线的理由是非线性。"
                "算法选择基于非凸目标，初值来自网格搜索，搜索范围受约束处理，终止条件为收敛容差，"
                "并用多起点和重启处理局部最优。中间结果包括粗估计3.2、迭代参数和表2的可行性检查。"
                "中文文献依据给出了方法先例和约束设计参考；本文创新扩展了本题数据下的约束适配与边界处理。"
                "结果来源为results/q1.json和求解器输出，主结果见表3。敏感性和扰动分析、残差、置信区间"
                "以及交叉验证共同评估稳定性和不确定性。"
            )
            (root / "paper.tex").write_text(
                "\\section{模型建立与求解}\n\\subsection{问题一}\\label{subproblem:Q1}\n" + body + "\n",
                encoding="utf-8")
            (root / "results").mkdir()
            (root / "results" / "q1.json").write_text("{}", encoding="utf-8")
            entries = {
                "problem_mapping": "题目输入数据映射",
                "assumptions": "假设样本",
                "symbols_units": "符号变量参数",
                "route_comparison": "候选路线包括解析路线",
                "algorithm_card": "算法选择基于非凸目标",
                "intermediate_results": "中间结果包括粗估计3.2",
                "literature_basis": "中文文献依据给出了方法先例",
                "innovation_delta": "本文创新扩展了本题数据",
                "result_source": "结果来源为results/q1.json",
                "reliability": "敏感性和扰动分析",
            }
            yaml_lines = ["schema_version: '2.1'", "evidence_quality: enhanced", "subproblems:",
                          "  - id: Q1", "    capabilities: []", "    evidence:"]
            for key, anchor in entries.items():
                yaml_lines.append(f"      {key}: {{status: pass, text_anchors: ['{anchor}']" +
                                  (", source_files: ['results/q1.json']}" if key == "result_source" else "}"))
            (root / "model_contract.yaml").write_text("\n".join(yaml_lines) + "\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(MODEL_EVIDENCE), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["evidence_quality"], "enhanced")

    def test_model_evidence_blocks_missing_expected_subproblem(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\section{模型建立与求解}\n\\subsection{问题一}\\label{subproblem:Q1}\n内容。\n",
                encoding="utf-8")
            (root / "model_contract.yaml").write_text(
                "schema_version: '2.1'\nproject:\n  expected_subproblems: [Q1, Q2]\nsubproblems:\n"
                "  - id: Q1\n    capabilities: []\n    evidence: {}\n",
                encoding="utf-8")
            result = subprocess.run([sys.executable, str(MODEL_EVIDENCE), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected_subproblems", result.stdout)

    def test_model_evidence_rejects_source_escape(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            outside = Path(raw).parent / "outside_result.json"
            outside.write_text("{}", encoding="utf-8")
            try:
                (root / "paper.tex").write_text(
                    "\\section{模型建立与求解}\n\\subsection{问题一}\n结果来源 可靠性。\n",
                    encoding="utf-8")
                (root / "model_contract.yaml").write_text(
                    "schema_version: '1.0'\nsubproblems:\n"
                    "  - id: Q1\n    capabilities: []\n    evidence:\n"
                    "      result_source: {status: pass, text_anchors: ['结果来源'], source_files: ['../outside_result.json']}\n"
                    "      reliability: {status: pass, text_anchors: ['可靠性']}\n",
                    encoding="utf-8")
                result = subprocess.run([sys.executable, str(MODEL_EVIDENCE), str(root), "--strict"],
                                        capture_output=True, text=True, encoding="utf-8", errors="replace")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("项目根目录", result.stdout)
            finally:
                outside.unlink(missing_ok=True)

    def test_derivation_blocks_derived_equation_without_steps(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\section{模型建立与求解}\n\\subsection{问题一}\n"
                "\\begin{equation}x=1\\label{eq:q1_01}\\end{equation}\n", encoding="utf-8")
            (root / "derivation_registry.yaml").write_text(
                "schema_version: '1.0'\nequations:\n"
                "  - id: eq1\n    kind: derived\n    label: eq:q1_01\n    depends_on: []\n    derivation_steps: []\n",
                encoding="utf-8")
            result = subprocess.run([sys.executable, str(DERIVATION), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("没有前置公式", result.stdout)

    def test_derivation_blocks_dependency_cycle(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\section{模型建立与求解}\n\\subsection{问题一}\n"
                "由甲得到乙。由乙得到甲。\n"
                "\\begin{equation}x=1\\label{eq:q1_01}\\end{equation}\n"
                "\\begin{equation}y=x+1\\label{eq:q1_02}\\end{equation}\n", encoding="utf-8")
            (root / "derivation_registry.yaml").write_text(
                "schema_version: '1.0'\nequations:\n"
                "  - id: eq1\n    kind: derived\n    label: eq:q1_01\n    depends_on: [eq2]\n"
                "    derivation_steps: ['由乙得到甲']\n"
                "  - id: eq2\n    kind: derived\n    label: eq:q1_02\n    depends_on: [eq1]\n"
                "    derivation_steps: ['由甲得到乙']\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(DERIVATION), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("存在环", result.stdout)

    def test_model_blueprint_compiles_hybrid_pipeline(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "model_blueprint.yaml").write_text(
                "schema_version: '1.0'\nproject:\n  composition: hybrid\n"
                "  expected_subproblems: [Q1, Q2]\nsubproblems:\n"
                "  - id: Q1\n    models:\n      - id: forecast\n        family: prediction\n        modifiers: [uncertainty]\n"
                "  - id: Q2\n    composition_mode: sequential\n    connections: [{from: Q1.forecast, to: Q2.demand}]\n"
                "    models:\n      - id: mechanism\n        family: mechanistic\n      - id: dispatch\n        family: optimization\n        modifiers: [robustness]\n",
                encoding="utf-8")
            (root / "model_contract.yaml").write_text(
                "schema_version: '2.1'\nsubproblems:\n"
                "  - id: Q1\n    evidence: {preprocessing: {}, data_split: {}, baseline: {}, metrics: {}}\n"
                "  - id: Q2\n    evidence: {mechanism_mapping: {}, formula_derivation: {}, decision_variables: {}, objective: {}, constraints: {}, feasibility_check: {}}\n",
                encoding="utf-8")
            result = subprocess.run([sys.executable, str(BLUEPRINT), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout)
            report = json.loads((root / "model_blueprint_compile_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["gate_status"], "PASS")
            self.assertEqual(report["subproblems"][1]["composition_mode"], "sequential")

    def test_model_blueprint_blocks_unconnected_multi_model(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "model_blueprint.yaml").write_text(
                "schema_version: '1.0'\nproject:\n  composition: hybrid\nsubproblems:\n"
                "  - id: Q1\n    models:\n      - id: a\n        family: mechanistic\n      - id: b\n        family: optimization\n",
                encoding="utf-8")
            result = subprocess.run([sys.executable, str(BLUEPRINT), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("composition_mode", result.stdout)

    def test_model_blueprint_cannot_pass_without_evidence_contract(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "model_blueprint.yaml").write_text(
                "schema_version: '1.0'\nproject:\n  composition: single\nsubproblems:\n"
                "  - id: Q1\n    models: [{id: mechanism, family: mechanistic}]\n",
                encoding="utf-8")
            result = subprocess.run([sys.executable, str(BLUEPRINT), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("绑定正文证据", result.stdout)

    def test_symbol_consistency_blocks_cross_question_unit_conflict(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "model_contract.yaml").write_text(
                "schema_version: '2.1'\nsubproblems:\n"
                "  - id: Q1\n    symbols: [{name: x, meaning: 温度, unit: K}]\n"
                "  - id: Q2\n    symbols: [{name: x, meaning: 距离, unit: m}]\n",
                encoding="utf-8")
            result = subprocess.run([sys.executable, str(SYMBOLS), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("冲突", result.stdout)

    def test_interface_contract_checks_json_pointer(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "results").mkdir()
            (root / "results" / "q1.json").write_text('{"forecast": {"value": 1}}\n', encoding="utf-8")
            (root / "interface_contract.yaml").write_text(
                "interfaces:\n  - from: Q1.forecast\n    to: Q2.demand\n"
                "    source_file: results/q1.json\n    key_path: /forecast/value\n",
                encoding="utf-8")
            result = subprocess.run([sys.executable, str(INTERFACES), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout)
            (root / "interface_contract.yaml").write_text(
                "interfaces:\n  - from: Q1.forecast\n    to: Q2.demand\n"
                "    source_file: results/q1.json\n    key_path: /forecast/missing\n",
                encoding="utf-8")
            failed = subprocess.run([sys.executable, str(INTERFACES), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("pointer", failed.stdout)

    def test_model_traceability_and_meta_text(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text("\\section{正文}\n\\lstinputlisting{solve.py}\n", encoding="utf-8")
            (root / "solve.py").write_text("# 功能：求解\n# 输入：数据\n# 输出：结果\n", encoding="utf-8")
            trace = subprocess.run([sys.executable, str(TRACEABILITY), str(root)], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace")
            self.assertEqual(trace.returncode, 0, trace.stdout)
            (root / "paper.tex").write_text("\\section{参考文献索引}\n", encoding="utf-8")
            meta = subprocess.run([sys.executable, str(META_TEXT), str(root)], capture_output=True,
                                   text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(meta.returncode, 0)

    def test_strict_traceability_requires_resolved_chinese_method_map(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\section{模型建立与求解}\n"
                "中文文献依据支持整数规划方法，本文改进约束并采用该方法\\cite{zh1}.\n",
                encoding="utf-8")
            (root / "model_assumptions.md").write_text("假设", encoding="utf-8")
            (root / "symbol_table.md").write_text("符号", encoding="utf-8")
            (root / "results").mkdir()
            (root / "sensitivity_results.json").write_text("{}", encoding="utf-8")
            (root / "figure_registry.json").write_text("{}", encoding="utf-8")
            payload = {
                "schema_version": "1.0", "required_chinese_count": 2,
                "verified_chinese_count": 2, "status": "resolved",
                "references": [
                    {"ref_ID": 1, "citation_key": "zh1", "title": "中文方法一", "method": "整数规划", "method_summary": "约束建模"},
                    {"ref_ID": 2, "citation_key": "zh2", "title": "中文方法二", "method": "鲁棒优化", "method_summary": "扰动分析"},
                ],
                "by_subproblem": {"Q1": [
                    {"ref_ID": 1, "citation_key": "zh1", "decision": "adapt", "method": "整数规划", "innovation_delta": "针对本题约束扩展"},
                    {"ref_ID": 2, "citation_key": "zh2", "decision": "reject", "reason": "数据规模不适配"},
                ]},
            }
            (root / "method_transfer_map.json").write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            passed = subprocess.run([sys.executable, str(TRACEABILITY), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(passed.returncode, 0, passed.stdout)
            payload["by_subproblem"]["Q1"][0]["citation_key"] = "wrong_key"
            (root / "method_transfer_map.json").write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            mismatched = subprocess.run([sys.executable, str(TRACEABILITY), str(root), "--strict"],
                                        capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(mismatched.returncode, 0)
            self.assertIn("不一致", mismatched.stdout)
            payload["by_subproblem"]["Q1"][0]["citation_key"] = "zh1"
            payload["by_subproblem"]["Q1"][0]["decision"] = "pending_agent_decision"
            (root / "method_transfer_map.json").write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            failed = subprocess.run([sys.executable, str(TRACEABILITY), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("尚未决定", failed.stdout)

    def test_non_guosai_traceability_does_not_require_chinese_map(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text("\\section{模型建立与求解}\n", encoding="utf-8")
            (root / "model_assumptions.md").write_text("假设", encoding="utf-8")
            (root / "symbol_table.md").write_text("符号", encoding="utf-8")
            (root / "results").mkdir()
            (root / "results" / "sensitivity_results.json").write_text("{}", encoding="utf-8")
            (root / "figure_registry.json").write_text(json.dumps({"figures": {"fig_1": {}}}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(TRACEABILITY), str(root), "--strict", "--competition", "mcm_icm"],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("不阻断", result.stdout)

    def test_report_dir_resolves_under_project_and_rejects_skill_root(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("delivery_all_paths", str(DELIVERY))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        root = Path("C:/Users/USER/Workspace/contest_orchestrator_path_fixture")
        self.assertEqual(module.resolve_report_dir(root, "reports"), (root / "reports").resolve())
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(ValueError):
                module.resolve_report_dir(Path(raw), "reports")
        with self.assertRaises(ValueError):
            module.resolve_report_dir(root, str(module.SCRIPTS.parent))

    def test_layout_pattern_gate_rejects_hard_float_in_strict_mode(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\begin{figure}[H]\\caption{bad}\\end{figure}\n", encoding="utf-8"
            )
            result = subprocess.run([sys.executable, str(LAYOUT), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("hard_float", result.stdout)

    def test_layout_pattern_gate_accepts_float_and_flags_manual_space_as_warning(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\begin{figure}[htbp]\\caption{ok}\\end{figure}\n\\vspace{1cm}\n", encoding="utf-8"
            )
            result = subprocess.run([sys.executable, str(LAYOUT), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("large_manual_space", result.stdout)

    def test_layout_pattern_gate_rejects_consecutive_page_breaks(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "正文\\clearpage\\newpage\\section{下一节}\n", encoding="utf-8"
            )
            result = subprocess.run([sys.executable, str(LAYOUT), str(root), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("consecutive_page_break", result.stdout)

    def test_tex_reference_gate_rejects_missing_and_duplicate_labels(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.tex").write_text(
                "\\label{dup}\\label{dup}\\ref{missing}\n", encoding="utf-8"
            )
            result = subprocess.run([sys.executable, str(TEX_REFS), str(root)],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["gate_status"], "BLOCK")
            self.assertEqual({item["kind"] for item in payload["issues"]}, {"duplicate_label", "missing_label"})

    def test_tex_reference_gate_expands_inputs(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "chapter.tex").write_text("\\label{tab:one}\n", encoding="utf-8")
            (root / "paper.tex").write_text("\\input{chapter}\\ref{tab:one}\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(TEX_REFS), str(root)],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_formal_delivery_drift_gate_detects_stale_pdf_and_index(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pdf = root / "paper.pdf"
            formal = root / "05_输出与交付" / "正式交付"
            formal.mkdir(parents=True)
            pdf.write_bytes(b"current")
            stale = formal / "B题论文_正式版.pdf"
            stale.write_bytes(b"stale")
            (formal / "FINAL_INDEX.md").write_text("old hash", encoding="utf-8")
            result = subprocess.run([sys.executable, str(FORMAL_DRIFT), str(root), "--pdf", str(pdf), "--strict"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("不一致", result.stdout)


if __name__ == "__main__":
    unittest.main()
