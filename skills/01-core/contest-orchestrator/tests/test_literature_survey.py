import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Make test discovery independent of the caller's current working directory.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from planner import literature_survey as ls


class LiteratureSurveyGateTests(unittest.TestCase):
    def setUp(self):
        self.problem_graph = {
            "direction_zh": "海岛微电网容量优化",
            "questions": ["确定容量配置", "开展调度与敏感性分析"],
            "real_world_constraints": ["功率平衡"],
        }
        self.fingerprint = {
            "primary": "优化决策", "subtype": "容量配置", "keywords": ["容量", "调度"],
            "constraints": ["integer"], "objective": "single", "data_scale": "medium",
        }

    def _english_hit(self):
        return [{"source": "crossref", "title": "Robust microgrid capacity planning",
                 "abstract": "A mixed integer robust optimization method with sensitivity analysis.",
                 "authors": ["A Author"], "year": "2024", "journal": "Energy", "doi": "10.1000/x",
                 "link": "https://doi.org/10.1000/x", "cited_by": 10}]

    def _english_sources(self, count=4):
        return [
            {"language": "en", "title": f"Robust microgrid capacity planning {i}",
             "authors": f"Author {i}", "venue": "Energy", "year": 2024,
             "doi_or_url": f"10.1000/en.{i}",
             "abstract": "A mixed integer robust optimization method with sensitivity analysis.",
             "full_text_summary": "The paper compares robust capacity plans under demand scenarios.",
             "method_summary": "Mixed integer robust optimization with sensitivity analysis.",
             "data_summary": "Synthetic demand scenarios and capacity parameters.",
             "limitations": "The scenario set may not cover all operational conditions.",
             "evidence_locators": ["Section 3", "Table 2"],
             "candidate_questions": ["Q1", "Q2"],
             "use_in_paper": "Provide a documented modeling or validation precedent."}
            for i in range(1, count + 1)
        ]

    def _valid_sources(self, records):
        """Build auditable user-returned records for literature gate tests."""
        sources = []
        for index, (language, questions) in enumerate(records, 1):
            chinese = language == "zh"
            sources.append({
                "language": language,
                "title": f"{'微电网优化研究' if chinese else 'Microgrid optimization study'} {index}",
                "authors": "张三" if chinese else f"Author {index}",
                "venue": "系统工程理论与实践" if chinese else "Energy",
                "year": 2024,
                "doi_or_url": f"10.1000/{language}.{index}",
                "abstract": "研究给出了可复核的模型、数据与结论。",
                "full_text_summary": "全文总结包括方法、数据、参数、边界和可迁移结论。",
                "method_summary": "采用优化模型并说明约束与求解步骤。",
                "data_summary": "给出变量、参数和数据来源。",
                "limitations": "适用范围受场景与参数条件约束。",
                "evidence_locators": ["第3节", "表2"],
                "candidate_questions": questions,
                "use_in_paper": "作为本题模型或参数依据，并在方法迁移登记中落位。",
            })
        return sources

    def _zh_payload(self):
        return [
            {"title": "海岛微电网容量配置优化研究", "authors": "张三, 李四", "journal": "电力系统自动化",
             "year": "2023", "doi": "10.1234/zh.1", "official_link": "https://example.org/zh1",
             "method_summary": "建立混合整数规划模型，考虑储能和功率平衡约束。",
             "use_in_paper": "作为容量配置与约束设计的方法先例，对应问题一。",
             "innovation_opportunity": "将本题的时序负荷和可靠性约束加入模型。"},
            {"title": "独立微电网储能调度与鲁棒优化", "authors": "王五, 赵六", "journal": "电工技术学报",
             "year": "2022", "doi": "10.1234/zh.2", "official_link": "https://example.org/zh2",
             "method_summary": "采用鲁棒优化和蒙特卡洛扰动分析储能调度方案。",
             "use_in_paper": "作为储能调度与敏感性检验的方法依据，对应问题二。",
             "innovation_opportunity": "将鲁棒预算与本文的多场景需求联立。"},
        ]

    def test_user_owns_literature_search_and_receives_requirement_card(self):
        with tempfile.TemporaryDirectory() as raw:
            with patch.object(ls, "_fetch_arxiv", side_effect=AssertionError("network search must not run")), \
                 patch.object(ls, "_fetch_crossref", side_effect=AssertionError("network search must not run")), \
                 patch.object(ls, "_fetch_semantic_scholar", side_effect=AssertionError("network search must not run")):
                result = ls.run_survey(self.problem_graph, self.fingerprint,
                                       competition="guosai", year=2026, qn="A", replay_root=raw)
            self.assertEqual(result["status"], "PAUSE")
            out = Path(raw) / "guosai_2026_A"
            request = (out / "literature_request.md").read_text(encoding="utf-8")
            self.assertIn("中文文献：每个小问至少 1 篇", request)
            self.assertIn("英文文献：不设硬性最低数量", request)
            self.assertIn("文献总数硬范围：6–11 篇", request)
            self.assertIn("推荐数量：8–10 篇", request)
            self.assertIn("Q1", request)
            self.assertIn("Q2", request)
            self.assertTrue((out / "literature_request.yaml").exists())
            prompt = (out / "literature_agent_prompt.md").read_text(encoding="utf-8")
            self.assertIn("full_text_summary", prompt)
            self.assertIn("data_summary", prompt)
            self.assertIn("下载对应全文", prompt)
            self.assertIn("literature_sources.yaml", prompt)
            self.assertFalse((out / "literature_report.md").exists())

    def test_six_sources_with_chinese_coverage_and_one_english_unlocks(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "guosai_2026_A"
            out.mkdir(parents=True)
            import yaml
            sources = self._valid_sources([
                ("zh", ["Q1"]), ("zh", ["Q2"]), ("zh", ["Q1"]),
                ("zh", ["Q2"]), ("zh", ["Q1", "Q2"]), ("en", ["Q1"]),
            ])
            (out / "literature_sources.yaml").write_text(
                yaml.safe_dump(sources, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            result = ls.run_survey(self.problem_graph, self.fingerprint,
                                   competition="guosai", year=2026, qn="A", replay_root=raw)
            self.assertEqual(result["status"], "READY")
            policy = result["search_summary"]["literature_policy"]
            self.assertEqual(policy["total_count"], 6)
            self.assertFalse(policy["recommended_total_met"])
            self.assertFalse(policy["english_coverage_recommendation_met"])

    def test_six_chinese_sources_without_english_unlocks(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "guosai_2026_A"
            out.mkdir(parents=True)
            import yaml
            sources = self._valid_sources([
                ("zh", ["Q1"]), ("zh", ["Q2"]), ("zh", ["Q1"]),
                ("zh", ["Q2"]), ("zh", ["Q1", "Q2"]), ("zh", ["Q1", "Q2"]),
            ])
            (out / "literature_sources.yaml").write_text(
                yaml.safe_dump(sources, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            result = ls.run_survey(self.problem_graph, self.fingerprint,
                                   competition="guosai", year=2026, qn="A", replay_root=raw)
            self.assertEqual(result["status"], "READY")
            policy = result["search_summary"]["literature_policy"]
            self.assertEqual(policy["total_count"], 6)
            self.assertEqual(policy["english_covered_questions"], [])
            self.assertFalse(policy["english_coverage_recommendation_met"])

    def test_missing_chinese_coverage_for_any_question_pauses(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "guosai_2026_A"
            out.mkdir(parents=True)
            import yaml
            sources = self._valid_sources([
                ("zh", ["Q1"]), ("zh", ["Q1"]), ("zh", ["Q1"]),
                ("zh", ["Q1"]), ("zh", ["Q1"]), ("en", ["Q1", "Q2"]),
            ])
            (out / "literature_sources.yaml").write_text(
                yaml.safe_dump(sources, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            result = ls.run_survey(self.problem_graph, self.fingerprint,
                                   competition="guosai", year=2026, qn="A", replay_root=raw)
            self.assertEqual(result["status"], "PAUSE")
            self.assertIn("Q2", result["search_summary"]["validation_errors"][-1])

    def test_twelve_sources_exceed_hard_maximum(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "guosai_2026_A"
            out.mkdir(parents=True)
            import yaml
            sources = self._valid_sources(
                [("zh", ["Q1"]), ("zh", ["Q2"]), ("en", ["Q1", "Q2"])] * 4
            )
            (out / "literature_sources.yaml").write_text(
                yaml.safe_dump(sources, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            result = ls.run_survey(self.problem_graph, self.fingerprint,
                                   competition="guosai", year=2026, qn="A", replay_root=raw)
            self.assertEqual(result["status"], "PAUSE")
            self.assertIn("超过上限 11", result["search_summary"]["validation_errors"][-1])

    def test_full_text_payload_is_rejected_at_main_agent_boundary(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "guosai_2026_A"
            out.mkdir(parents=True)
            import yaml
            payload = self._zh_payload()[:2] + self._english_sources(4)
            for source in payload:
                source.setdefault("language", "zh" if "中文" in source.get("title", "") else "en")
                source.setdefault("abstract", source.get("method_summary", "abstract"))
                source.setdefault("full_text_summary", "summary")
                source.setdefault("data_summary", "data")
                source.setdefault("limitations", "limitation")
                source.setdefault("evidence_locators", ["Section 1"])
                source.setdefault("candidate_questions", ["Q1", "Q2"])
            payload[0]["full_text"] = "raw full text must not enter"
            path = out / "literature_sources.yaml"
            path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
            result = ls.run_survey(self.problem_graph, self.fingerprint,
                                   competition="guosai", year=2026, qn="A", replay_root=raw)
            self.assertEqual(result["status"], "PAUSE")
            self.assertTrue(any("全文字段" in item for item in result["search_summary"]["validation_errors"]))

    def test_missing_chinese_sources_is_hard_pause(self):
        with tempfile.TemporaryDirectory() as raw:
            result = ls.run_survey(self.problem_graph, self.fingerprint,
                                   competition="guosai", year=2026, qn="A", replay_root=raw)
            self.assertEqual(result["status"], "PAUSE")
            out = Path(raw) / "guosai_2026_A"
            self.assertTrue((out / "literature_request.md").exists())
            self.assertTrue((out / "literature_request.yaml").exists())
            self.assertTrue((out / "literature_pause.json").exists())
            self.assertFalse((out / "literature_report.md").exists())
            pause = json.loads((out / "literature_pause.json").read_text(encoding="utf-8"))
            self.assertEqual(pause["reason"], "user_literature_required")

    def test_two_chinese_sources_unlock_and_create_method_map(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "guosai_2026_A"
            out.mkdir(parents=True)
            import yaml
            sources = self._zh_payload() + self._english_sources(4)
            for source in sources[:2]:
                source["abstract"] = source["method_summary"]
                source["language"] = "zh"
                source["full_text_summary"] = source["method_summary"]
                source["data_summary"] = "时序负荷、储能参数和功率平衡约束。"
                source["limitations"] = "参数依赖具体运行场景。"
                source["evidence_locators"] = ["第3节", "表2"]
                source["candidate_questions"] = ["Q1", "Q2"]
            sources_path = out / "literature_sources.yaml"
            sources_path.write_text(yaml.safe_dump(sources, allow_unicode=True, sort_keys=False), encoding="utf-8")
            result = ls.run_survey(self.problem_graph, self.fingerprint,
                                   competition="guosai", year=2026, qn="A", replay_root=raw)
            self.assertEqual(result.get("status"), "READY")
            transfer = json.loads((out / "method_transfer_map.json").read_text(encoding="utf-8"))
            self.assertEqual(transfer["verified_chinese_count"], 2)
            self.assertEqual(transfer["required_chinese_count"], 2)
            self.assertTrue(transfer["references"])
            self.assertTrue(transfer["references"][0]["citation_key"])
            for field in ("status", "venue", "url", "relevance", "key_points",
                          "limitations", "used_in", "verified_at"):
                self.assertIn(field, result["references"][0])
                self.assertIn(field, transfer["references"][0])
            self.assertEqual(result["citation_map"]["_metadata"]["research_evidence_version"], "1.0")
            self.assertEqual(result["citation_map"]["claim_evidence"], [])
            self.assertTrue((out / "literature_report.md").exists())
            self.assertIn("method_transfer_map.json", result["citation_map"]["method_transfer_map"])
            self.assertEqual(result["citation_map"]["section_Q1_modeling"][:2], ["1", "2"])
            self.assertEqual(
                result["citation_map"]["section_Q1_modeling_citations"][:2],
                [
                    {"ref_ID": "1", "citation_key": transfer["references"][0]["citation_key"]},
                    {"ref_ID": "2", "citation_key": transfer["references"][1]["citation_key"]},
                ],
            )

    def test_language_and_coverage_policy_applies_to_every_harness_profile(self):
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "mcm_icm_2026_A"
            out.mkdir(parents=True)
            import yaml
            (out / "literature_sources.yaml").write_text(
                yaml.safe_dump(self._valid_sources([("en", ["Q1", "Q2"])] * 6), allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            result = ls.run_survey(self.problem_graph, self.fingerprint,
                                   competition="mcm_icm", year=2026, qn="A", replay_root=raw)
            self.assertEqual(result["status"], "PAUSE")
            self.assertIn("中文文献未覆盖小问", result["search_summary"]["validation_errors"][-1])

    def test_method_classifier_avoids_ode_substring_and_covers_chinese_metaheuristics(self):
        papers = [
            {"title": "Model-based capacity planning", "abstract": "A model for robust design.",
             "authors": ["A"], "year": "2024", "language": "en"},
            {"title": "基于自适应引力搜索算法的定日镜场优化布置", "abstract": "",
             "authors": ["张三"], "year": "2024", "language": "zh"},
        ]
        insights = ls._extract_insights(papers, self.problem_graph, self.fingerprint)
        self.assertNotIn("微分方程/ODE/PDE", insights[0]["matched_methods"])
        self.assertIn("启发式优化", insights[1]["matched_methods"])


if __name__ == "__main__":
    unittest.main()
