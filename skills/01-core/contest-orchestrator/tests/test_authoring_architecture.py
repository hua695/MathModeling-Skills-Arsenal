import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_harness_control.py"
SPEC = importlib.util.spec_from_file_location("check_harness_control", CHECKER)
checker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(checker)


class AuthoringArchitectureTests(unittest.TestCase):
    def _write_brief_fixture(self, root: Path):
        blueprint = root / "paper_argument_blueprint.yaml"
        spine = {
            "core_chapters": ["Q1"], "support_chapters": [],
            "chapter_order": ["Q1"], "chapter_edges": [],
        }
        blueprint.write_text(yaml.safe_dump({
            "status": "approved",
            "global": {
                "central_thesis": "受限结论",
                "reader_journey": "从问题到证据再到结论",
                "paper_spine": spine,
            },
        }, allow_unicode=True), encoding="utf-8")
        brief = root / "paper_author_brief.yaml"
        brief.write_text(yaml.safe_dump({
            "status": "approved",
            "prepared_by": "academic-writing",
            "argument_blueprint_sha256": checker.digest(blueprint),
            "central_thesis": "受限结论",
            "reader_journey": "从问题到证据再到结论",
            "paper_spine": spine,
            "chapters": [{
                "section_id": "Q1", "chapter_kind": "modeling_question",
                "reader_question": "问题是什么？",
                "chapter_purpose": "说明方法的必要性", "chapter_answer": "给出受限回答",
                "opening_bridge": "本问围绕受限资源下的决策问题展开。",
                "section_structure": {
                    "numbered_sections": ["模型建立", "模型求解与结果分析"],
                    "summary_location": "模型建立小节末尾", "optional_sections": [],
                },
                "argument_ids": ["arg-01"], "evidence_refs": [],
                "figure_roles": [], "reader_takeaway": "理解结论范围",
                "excluded_material": [], "chapter_role": "core", "reads_from": [],
                "feeds_to": [], "new_claims_allowed": ["arg-01"],
                "handoff_question": "本问结果如何汇入总论证？",
            }],
        }, allow_unicode=True), encoding="utf-8")
        return blueprint, brief

    def test_h8_writing_cannot_start_without_approved_author_brief(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            blueprint = root / "paper_argument_blueprint.yaml"
            blueprint.write_text("status: approved\n", encoding="utf-8")
            checker._validate_paper_author_brief(
                root,
                {"paper_argument_blueprint": "paper_argument_blueprint.yaml", "writing_started": True},
                missing,
                failures,
            )
        self.assertTrue(any("paper_author_brief" in item for item in missing))

    def test_author_brief_must_bind_to_the_approved_argument_blueprint(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            blueprint = root / "paper_argument_blueprint.yaml"
            blueprint.write_text("status: approved\n", encoding="utf-8")
            brief = root / "paper_author_brief.yaml"
            brief.write_text(yaml.safe_dump({
                "status": "approved",
                "prepared_by": "academic-writing",
                "argument_blueprint_sha256": "wrong",
                "central_thesis": "受限结论",
                "chapters": [{
                    "section_id": "Q1", "chapter_kind": "modeling_question",
                    "reader_question": "问题是什么？",
                    "chapter_purpose": "说明方法的必要性", "chapter_answer": "给出受限回答",
                    "opening_bridge": "本问围绕受限资源下的决策问题展开。",
                    "section_structure": {
                        "numbered_sections": ["模型建立", "模型求解与结果分析"],
                        "summary_location": "模型建立小节末尾", "optional_sections": [],
                    },
                    "argument_ids": ["arg-01"], "evidence_refs": [],
                    "figure_roles": [], "reader_takeaway": "理解结论范围",
                    "excluded_material": [],
                }],
            }, allow_unicode=True), encoding="utf-8")
            checker._validate_paper_author_brief(
                root,
                {"paper_argument_blueprint": "paper_argument_blueprint.yaml",
                 "paper_author_brief": "paper_author_brief.yaml", "writing_started": True},
                missing,
                failures,
            )
        self.assertTrue(any("argument_blueprint_sha256" in item for item in failures))

    def test_author_brief_requires_chapter_role_and_handoff_contract(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _, brief = self._write_brief_fixture(root)
            document = yaml.safe_load(brief.read_text(encoding="utf-8"))
            document["chapters"][0].pop("chapter_role", None)
            brief.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
            checker._validate_paper_author_brief(
                root,
                {"paper_argument_blueprint": "paper_argument_blueprint.yaml",
                 "paper_author_brief": "paper_author_brief.yaml", "writing_started": True},
                missing,
                failures,
            )
        self.assertTrue(any("chapter_role" in item for item in failures))

    def test_writing_started_requires_a_current_chapter_card(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_brief_fixture(root)
            checker._validate_chapter_writing_cards(
                root,
                {"paper_author_brief": "paper_author_brief.yaml", "chapter_writing_cards": [],
                 "writing_started": True},
                missing,
                failures,
            )
        self.assertTrue(any("chapter_writing_cards" in item for item in missing))

    def test_chapter_card_must_bind_to_author_brief_hash(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_brief_fixture(root)
            card = root / "chapter_writing_card.yaml"
            card.write_text(yaml.safe_dump({
                "status": "ready",
                "prepared_from_author_brief_sha256": "wrong",
                "chapter_id": "Q1", "chapter_kind": "modeling_question", "reader_question": "问题是什么？",
                "chapter_purpose": "说明方法的必要性", "chapter_answer": "给出受限回答",
                "opening_bridge": "本问围绕受限资源下的决策问题展开。",
                "section_structure": {"numbered_sections": ["模型建立", "模型求解与结果分析"],
                                      "summary_location": "模型建立小节末尾", "optional_sections": []},
                "model_summary_card": "model_summary_cards.yaml",
                "abstract_contribution": {
                    "method": "受限资源配置模型",
                    "result": "得到可行配置",
                    "meaning": "为总方案提供基础",
                    "evidence_refs": ["result_cards/Q1.yaml"],
                },
                "argument_ids": ["arg-01"], "evidence_refs": [], "figure_roles": [],
                "reader_takeaway": "理解结论范围", "writer_instruction": "连贯写作",
                "excluded_material": [], "chapter_role": "core", "reads_from": [],
                "feeds_to": [], "new_claims_allowed": ["arg-01"],
                "handoff_question": "本问结果如何汇入总论证？",
            }, allow_unicode=True), encoding="utf-8")
            checker._validate_chapter_writing_cards(
                root,
                {"paper_author_brief": "paper_author_brief.yaml",
                 "chapter_writing_cards": ["chapter_writing_card.yaml"],
                 "active_chapter_card": "chapter_writing_card.yaml",
                 "writing_started": True},
                missing,
                failures,
            )
        self.assertTrue(any("prepared_from_author_brief_sha256" in item for item in failures))

    def test_chapter_card_cannot_expand_author_brief_arguments(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_brief_fixture(root)
            card = root / "chapter_writing_card.yaml"
            card.write_text(yaml.safe_dump({
                "status": "ready",
                "prepared_from_author_brief_sha256": checker.digest(root / "paper_author_brief.yaml"),
                "chapter_id": "Q1", "chapter_kind": "modeling_question", "reader_question": "问题是什么？",
                "chapter_purpose": "说明方法的必要性", "chapter_answer": "给出受限回答",
                "opening_bridge": "本问围绕受限资源下的决策问题展开。",
                "section_structure": {"numbered_sections": ["模型建立", "模型求解与结果分析"],
                                      "summary_location": "模型建立小节末尾", "optional_sections": []},
                "model_summary_card": "model_summary_cards.yaml",
                "argument_ids": ["arg-unknown"], "evidence_refs": [], "figure_roles": [],
                "reader_takeaway": "理解结论范围", "writer_instruction": "连贯写作",
                "excluded_material": [],
            }, allow_unicode=True), encoding="utf-8")
            checker._validate_chapter_writing_cards(
                root,
                {"paper_author_brief": "paper_author_brief.yaml",
                 "chapter_writing_cards": ["chapter_writing_card.yaml"],
                 "active_chapter_card": "chapter_writing_card.yaml",
                 "writing_started": True},
                missing,
                failures,
            )
        self.assertTrue(any("argument_ids" in item for item in failures))

    def test_scoped_chapter_card_is_accepted(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_brief_fixture(root)
            card = root / "chapter_writing_card.yaml"
            card.write_text(yaml.safe_dump({
                "status": "ready",
                "prepared_from_author_brief_sha256": checker.digest(root / "paper_author_brief.yaml"),
                "chapter_id": "Q1", "chapter_kind": "modeling_question", "reader_question": "问题是什么？",
                "chapter_purpose": "说明方法的必要性", "chapter_answer": "给出受限回答",
                "opening_bridge": "本问围绕受限资源下的决策问题展开。",
                "section_structure": {"numbered_sections": ["模型建立", "模型求解与结果分析"],
                                      "summary_location": "模型建立小节末尾", "optional_sections": []},
                "model_summary_card": "model_summary_cards.yaml",
                "abstract_contribution": {
                    "method": "受限资源配置模型",
                    "result": "得到可行配置",
                    "meaning": "为总方案提供基础",
                    "evidence_refs": ["result_cards/Q1.yaml"],
                },
                "argument_ids": ["arg-01"], "evidence_refs": [], "figure_roles": [],
                "reader_takeaway": "理解结论范围", "writer_instruction": "连贯写作",
                "excluded_material": [], "chapter_role": "core", "reads_from": [],
                "feeds_to": [], "new_claims_allowed": ["arg-01"],
                "handoff_question": "本问结果如何汇入总论证？",
            }, allow_unicode=True), encoding="utf-8")
            checker._validate_chapter_writing_cards(
                root,
                {"paper_author_brief": "paper_author_brief.yaml",
                 "chapter_writing_cards": ["chapter_writing_card.yaml"],
                 "active_chapter_card": "chapter_writing_card.yaml",
                 "writing_started": True},
                missing,
                failures,
            )
        self.assertEqual(missing, [])
        self.assertEqual(failures, [])

    def test_chapter_card_handoff_must_match_author_brief(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _, brief = self._write_brief_fixture(root)
            card = root / "chapter_writing_card.yaml"
            card.write_text(yaml.safe_dump({
                "status": "ready",
                "prepared_from_author_brief_sha256": checker.digest(brief),
                "chapter_id": "Q1", "chapter_kind": "modeling_question", "reader_question": "问题是什么？",
                "chapter_purpose": "说明方法的必要性", "chapter_answer": "给出受限回答",
                "opening_bridge": "本问围绕受限资源下的决策问题展开。",
                "section_structure": {"numbered_sections": ["模型建立", "模型求解与结果分析"],
                                      "summary_location": "模型建立小节末尾", "optional_sections": []},
                "model_summary_card": "model_summary_cards.yaml",
                "argument_ids": ["arg-01"], "evidence_refs": [], "figure_roles": [],
                "reader_takeaway": "理解结论范围", "writer_instruction": "连贯写作",
                "excluded_material": [], "chapter_role": "core", "reads_from": [],
                "feeds_to": ["Q2"], "new_claims_allowed": ["arg-01"],
                "handoff_question": "下一问如何扩展？",
            }, allow_unicode=True), encoding="utf-8")
            checker._validate_chapter_writing_cards(
                root,
                {"paper_author_brief": "paper_author_brief.yaml",
                 "chapter_writing_cards": ["chapter_writing_card.yaml"],
                 "active_chapter_card": "chapter_writing_card.yaml", "writing_started": True},
                missing,
                failures,
            )
        self.assertTrue(any("feeds_to" in item or "handoff" in item for item in failures))

    def test_h6_stage_rejects_unverified_model_summary_cards(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            summary = root / "model_summary_cards.yaml"
            summary.write_text(yaml.safe_dump({
                "schema_version": "1.0",
                "status": "draft",
                "created_by": "H5",
                "verified_by": "H6",
                "cards": [],
            }, allow_unicode=True), encoding="utf-8")
            nodes = {
                "H5": {"model_summary_cards": "model_summary_cards.yaml"},
                "H6": {"status": "approved", "agent_instance_id": "h6-01",
                       "model_summary_cards": "model_summary_cards.yaml"},
            }
            checker._validate_model_summary_cards(
                root, nodes, {"subproblems": [{"id": "Q1"}]}, missing, failures,
            )
        self.assertTrue(any("status" in item and "verified" in item for item in failures))

    def test_h8b_task_card_without_authoring_protocol_is_blocked(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            input_file = root / "input.md"
            input_file.write_text("冻结输入", encoding="utf-8")
            task_card = root / "H8.yaml"
            task_card.write_text(yaml.safe_dump({
                "task_id": "H8-task-001", "node_id": "H8", "owner_role": "论文 agent",
                "objective": "按章节卡写作", "inputs": [{"path": "input.md", "sha256": checker.digest(input_file)}],
                "scope": "Q1", "required_outputs": ["draft"], "verification": ["check"],
                "prohibited_actions": ["越权"], "evidence_handoff": ["draft"],
                "model": "gpt-5.6-sol", "reasoning_effort": "high",
            }, allow_unicode=True), encoding="utf-8")
            checker._validate_task_card(
                root, "H8",
                {"task_card": "H8.yaml", "agent_instance_id": "h8-01", "writing_started": True},
                checker.AGENT_RUNTIME_BY_NODE["H8"], set(), missing, failures,
            )
        self.assertTrue(any("authoring_protocol" in item for item in missing))

    def test_writing_started_requires_a_paper_continuity_context(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_brief_fixture(root)
            checker._validate_paper_continuity_context(
                root,
                {
                    "paper_author_brief": "paper_author_brief.yaml",
                    "active_chapter_card": "chapter_writing_card.yaml",
                    "paper_continuity_context": None,
                    "writing_started": True,
                },
                missing,
                failures,
            )
        self.assertTrue(any("paper_continuity_context" in item for item in missing))

    def test_paper_continuity_context_must_bind_to_author_brief_and_active_chapter(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _, brief = self._write_brief_fixture(root)
            card = root / "chapter_writing_card.yaml"
            card.write_text(yaml.safe_dump({
                "status": "ready",
                "prepared_from_author_brief_sha256": checker.digest(brief),
                "chapter_id": "Q1", "chapter_kind": "modeling_question", "reader_question": "问题是什么？",
                "chapter_purpose": "说明方法的必要性", "chapter_answer": "给出受限回答",
                "opening_bridge": "本问围绕受限资源下的决策问题展开。",
                "section_structure": {"numbered_sections": ["模型建立", "模型求解与结果分析"],
                                      "summary_location": "模型建立小节末尾", "optional_sections": []},
                "model_summary_card": "model_summary_cards.yaml",
                "argument_ids": ["arg-01"], "evidence_refs": [], "figure_roles": [],
                "reader_takeaway": "理解结论范围", "writer_instruction": "连贯写作",
                "excluded_material": [], "chapter_role": "core", "reads_from": [],
                "feeds_to": [], "new_claims_allowed": ["arg-01"],
                "handoff_question": "本问结果如何汇入总论证？",
            }, allow_unicode=True), encoding="utf-8")
            context = root / "paper_continuity_context.yaml"
            context.write_text(yaml.safe_dump({
                "status": "ready",
                "paper_author_brief_sha256": "wrong",
                "central_thesis": "受限结论",
                "reader_journey": "从问题到证据再到结论",
                "current_chapter_id": "Q2",
                "previous_section_takeaway": "前章收束",
                "next_section_question": "下一章问题",
                "completed_chapters": [], "terminology_lock": [],
                "voice": "客观、连贯、面向读者",
            }, allow_unicode=True), encoding="utf-8")
            checker._validate_paper_continuity_context(
                root,
                {
                    "paper_author_brief": "paper_author_brief.yaml",
                    "active_chapter_card": "chapter_writing_card.yaml",
                    "paper_continuity_context": "paper_continuity_context.yaml",
                    "writing_started": True,
                },
                missing,
                failures,
            )
        self.assertTrue(any("paper_author_brief_sha256" in item for item in failures))
        self.assertTrue(any("current_chapter_id" in item for item in failures))

    def test_valid_paper_continuity_context_is_accepted(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _, brief = self._write_brief_fixture(root)
            card = root / "chapter_writing_card.yaml"
            card.write_text(yaml.safe_dump({
                "status": "ready",
                "prepared_from_author_brief_sha256": checker.digest(brief),
                "chapter_id": "Q1", "chapter_kind": "modeling_question", "reader_question": "问题是什么？",
                "chapter_purpose": "说明方法的必要性", "chapter_answer": "给出受限回答",
                "opening_bridge": "本问围绕受限资源下的决策问题展开。",
                "section_structure": {"numbered_sections": ["模型建立", "模型求解与结果分析"],
                                      "summary_location": "模型建立小节末尾", "optional_sections": []},
                "model_summary_card": "model_summary_cards.yaml",
                "argument_ids": ["arg-01"], "evidence_refs": [], "figure_roles": [],
                "reader_takeaway": "理解结论范围", "writer_instruction": "连贯写作",
                "excluded_material": [],
            }, allow_unicode=True), encoding="utf-8")
            context = root / "paper_continuity_context.yaml"
            context.write_text(yaml.safe_dump({
                "status": "current",
                "paper_author_brief_sha256": checker.digest(brief),
                "chapter_writing_card_sha256": checker.digest(card),
                "central_thesis": "受限结论",
                "reader_journey": "从问题到证据再到结论",
                "current_chapter_id": "Q1",
                "previous_section_takeaway": "无前置章节",
                "next_section_question": "下一章如何解释结果？",
                "completed_chapters": [], "terminology_lock": [],
                "voice": "客观、连贯、面向读者",
                "paper_spine": {"core_chapters": ["Q1"], "support_chapters": [],
                                "chapter_order": ["Q1"], "chapter_edges": []},
            }, allow_unicode=True), encoding="utf-8")
            checker._validate_paper_continuity_context(
                root,
                {
                    "paper_author_brief": "paper_author_brief.yaml",
                    "active_chapter_card": "chapter_writing_card.yaml",
                    "paper_continuity_context": "paper_continuity_context.yaml",
                    "writing_started": True,
                },
                missing,
                failures,
            )
        self.assertEqual(missing, [])
        self.assertEqual(failures, [])

    def test_continuity_context_must_bind_to_the_paper_spine(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _, brief = self._write_brief_fixture(root)
            card = root / "chapter_writing_card.yaml"
            card.write_text(yaml.safe_dump({
                "status": "ready",
                "prepared_from_author_brief_sha256": checker.digest(brief),
                "chapter_id": "Q1", "chapter_kind": "modeling_question", "reader_question": "问题是什么？",
                "chapter_purpose": "说明方法的必要性", "chapter_answer": "给出受限回答",
                "opening_bridge": "本问围绕受限资源下的决策问题展开。",
                "section_structure": {"numbered_sections": ["模型建立", "模型求解与结果分析"],
                                      "summary_location": "模型建立小节末尾", "optional_sections": []},
                "model_summary_card": "model_summary_cards.yaml",
                "argument_ids": ["arg-01"], "evidence_refs": [], "figure_roles": [],
                "reader_takeaway": "理解结论范围", "writer_instruction": "连贯写作",
                "excluded_material": [], "chapter_role": "core", "reads_from": [], "feeds_to": [],
                "new_claims_allowed": ["arg-01"], "handoff_question": "下一问如何扩展？",
            }, allow_unicode=True), encoding="utf-8")
            context = root / "paper_continuity_context.yaml"
            context.write_text(yaml.safe_dump({
                "status": "current",
                "paper_author_brief_sha256": checker.digest(brief),
                "chapter_writing_card_sha256": checker.digest(card),
                "central_thesis": "受限结论", "reader_journey": "从问题到证据再到结论",
                "current_chapter_id": "Q1", "previous_section_takeaway": "无前置章节",
                "next_section_question": "下一章如何解释结果？", "completed_chapters": [],
                "terminology_lock": [], "voice": "客观、连贯、面向读者",
                "paper_spine": {
                    "core_chapters": ["Q1"], "support_chapters": ["problem_analysis"],
                    "chapter_order": ["problem_analysis", "Q1"],
                    "chapter_edges": [{"from": "problem_analysis", "to": "Q1",
                                       "relation": "feeds", "handoff_question": "题意如何进入模型？"}],
                },
            }, allow_unicode=True), encoding="utf-8")
            checker._validate_paper_continuity_context(
                root,
                {"paper_author_brief": "paper_author_brief.yaml", "active_chapter_card": "chapter_writing_card.yaml",
                 "paper_continuity_context": "paper_continuity_context.yaml", "writing_started": True},
                missing,
                failures,
            )
        self.assertTrue(any("paper_spine" in item for item in failures))

    def test_h8b_task_card_requires_continuity_context_input(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            input_file = root / "input.md"
            brief = root / "paper_author_brief.yaml"
            card = root / "chapter_writing_card.yaml"
            input_file.write_text("冻结输入", encoding="utf-8")
            brief.write_text("作者简报", encoding="utf-8")
            card.write_text("章节卡", encoding="utf-8")
            task_card = root / "H8.yaml"
            task_card.write_text(yaml.safe_dump({
                "task_id": "H8-task-002", "node_id": "H8", "owner_role": "论文 agent",
                "objective": "按章节卡写作",
                "inputs": [
                    {"path": "paper_author_brief.yaml", "sha256": checker.digest(brief)},
                    {"path": "chapter_writing_card.yaml", "sha256": checker.digest(card)},
                ],
                "scope": "Q1", "required_outputs": ["draft"], "verification": ["check"],
                "prohibited_actions": ["越权"], "evidence_handoff": ["draft"],
                "model": "gpt-5.6-sol", "reasoning_effort": "high",
                "authoring_protocol": {
                    "stage": "H8B",
                    "chapter_writing_card": "chapter_writing_card.yaml",
                    "paper_continuity_context": "paper_continuity_context.yaml",
                    "writer_first_protocol": "contest-orchestrator/references/h8_writer_first_protocol.md",
                },
            }, allow_unicode=True), encoding="utf-8")
            checker._validate_task_card(
                root, "H8",
                {
                    "task_card": "H8.yaml", "agent_instance_id": "h8-01",
                    "active_chapter_card": "chapter_writing_card.yaml",
                    "paper_continuity_context": "paper_continuity_context.yaml",
                    "writing_started": True,
                },
                checker.AGENT_RUNTIME_BY_NODE["H8"], set(), missing, failures,
            )
        self.assertTrue(any("paper_continuity_context.yaml" in item for item in missing))

    def test_h8_writer_warmup_routes_to_author_brief_and_chapter_card(self):
        content = (ROOT / "references" / "warmup" / "h8_writer_warmup.md").read_text(encoding="utf-8")
        self.assertIn("paper_author_brief.yaml", content)
        self.assertIn("chapter_writing_card.yaml", content)
        self.assertIn("paper_continuity_context.yaml", content)
        self.assertIn("model_summary_cards.yaml", content)
        self.assertIn("model_summary_protocol.md", content)
        self.assertIn("writer-first", content.lower())

    def test_h8_execution_requires_whole_paper_readthrough(self):
        execution = (ROOT / "references" / "h8_chapter_execution.md").read_text(encoding="utf-8")
        self.assertIn("paper_continuity_context.yaml", execution)
        self.assertIn("通读全文", execution)
        self.assertIn("先写论证", execution)

    def test_academic_writing_h8c_uses_reader_first_full_paper_pass(self):
        skill = (ROOT.parent / "academic-writing" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("H8C", skill)
        self.assertIn("通读全文", skill)
        self.assertIn("读者路径", skill)

    def test_b_chapter_templates_use_the_canonical_two_section_layout(self):
        templates_root = ROOT.parent / "academic-writing" / "references" / "b_chapter_templates"
        readme = (templates_root / "README.md").read_text(encoding="utf-8")
        self.assertIn("统一章节骨架", readme)
        self.assertIn("模型建立", readme)
        self.assertIn("模型求解与结果分析", readme)
        for path in templates_root.rglob("*.md"):
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("六小节", content, str(path))
            self.assertNotIn("模型建立→求解", content, str(path))

    def test_authoring_templates_are_discoverable(self):
        for name in (
            "paper_author_brief.yaml",
            "chapter_writing_card.yaml",
            "paper_continuity_context.yaml",
            "model_summary_cards.yaml",
        ):
            self.assertTrue((ROOT / "templates" / name).is_file(), name)

    def test_modeling_structure_protocol_is_present(self):
        protocol = ROOT / "references" / "model_summary_protocol.md"
        self.assertTrue(protocol.is_file())
        content = protocol.read_text(encoding="utf-8")
        for phrase in (
            "全局符号说明",
            "问题引入与建模思路",
            "模型建立",
            "模型求解与结果分析",
            "最终求解模型",
        ):
            self.assertIn(phrase, content)

    def test_h8_writing_requires_verified_model_summary_cards(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            checker._validate_model_summary_cards(
                root,
                {"H8": {"writing_started": True, "model_summary_cards": None}},
                {"subproblems": [{"id": "Q1"}]},
                missing,
                failures,
            )
        self.assertTrue(any("model_summary_cards" in item for item in missing))

    def test_model_summary_card_requires_final_formulation_and_section_structure(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            summary = root / "model_summary_cards.yaml"
            summary.write_text(yaml.safe_dump({
                "schema_version": "1.0",
                "status": "verified",
                "created_by": "H5",
                "verified_by": "H6",
                "cards": [{
                    "card_id": "Q1-final-model",
                    "subproblem_id": "Q1",
                    "purpose": "给出可计算模型",
                    "model_family": "constrained_optimization",
                    "decision_variables": [{"symbol": "x", "meaning": "决策量", "unit": "无量纲", "domain": "x>=0"}],
                    "parameters": [],
                    "final_formulation": {"kind": "optimization", "expression": ""},
                    "solver_interface": {"method": "求解器", "inputs": ["x"], "outputs": ["x"]},
                    "source_equation_refs": ["eq:1"],
                }],
            }, allow_unicode=True), encoding="utf-8")
            nodes = {
                "H5": {"model_summary_cards": "model_summary_cards.yaml"},
                "H6": {"model_summary_cards": "model_summary_cards.yaml"},
                "H8": {"writing_started": True, "model_summary_cards": "model_summary_cards.yaml"},
            }
            checker._validate_model_summary_cards(
                root, nodes, {"subproblems": [{"id": "Q1"}]}, missing, failures,
            )
        self.assertTrue(any("final_formulation" in item for item in failures))
        self.assertTrue(any("paper_structure" in item for item in failures))

    def test_valid_model_summary_card_is_accepted(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            summary = root / "model_summary_cards.yaml"
            summary.write_text(yaml.safe_dump({
                "schema_version": "1.0",
                "status": "verified",
                "created_by": "H5",
                "verified_by": "H6",
                "cards": [{
                    "card_id": "Q1-final-model",
                    "subproblem_id": "Q1",
                    "purpose": "给出可计算模型",
                    "model_family": "constrained_optimization",
                    "decision_variables": [{"symbol": "x", "meaning": "决策量", "unit": "无量纲", "domain": "x>=0"}],
                    "parameters": [],
                    "final_formulation": {"kind": "optimization", "expression": "min f(x) s.t. x>=0"},
                    "solver_interface": {"method": "求解器", "inputs": ["x"], "outputs": ["x"]},
                    "source_equation_refs": ["eq:1"],
                    "paper_structure": {
                        "opening_bridge": "本问围绕资源约束下的最优决策展开。",
                        "numbered_sections": ["模型建立", "模型求解与结果分析"],
                        "summary_location": "模型建立小节末尾",
                        "optional_sections": [],
                    },
                }],
            }, allow_unicode=True), encoding="utf-8")
            nodes = {
                "H5": {"model_summary_cards": "model_summary_cards.yaml"},
                "H6": {"model_summary_cards": "model_summary_cards.yaml"},
                "H8": {"writing_started": True, "model_summary_cards": "model_summary_cards.yaml"},
            }
            checker._validate_model_summary_cards(
                root, nodes, {"subproblems": [{"id": "Q1"}]}, missing, failures,
            )
        self.assertEqual(missing, [])
        self.assertEqual(failures, [])

    def test_chapter_card_requires_opening_bridge_and_two_section_layout(self):
        failures, missing = [], []
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._write_brief_fixture(root)
            card = root / "chapter_writing_card.yaml"
            card.write_text(yaml.safe_dump({
                "status": "ready",
                "prepared_from_author_brief_sha256": checker.digest(root / "paper_author_brief.yaml"),
                "chapter_id": "Q1", "reader_question": "问题是什么？",
                "chapter_purpose": "说明方法的必要性", "chapter_answer": "给出受限回答",
                "argument_ids": ["arg-01"], "evidence_refs": [], "figure_roles": [],
                "reader_takeaway": "理解结论范围", "writer_instruction": "连贯写作",
                "excluded_material": [],
            }, allow_unicode=True), encoding="utf-8")
            checker._validate_chapter_writing_cards(
                root,
                {"paper_author_brief": "paper_author_brief.yaml",
                 "chapter_writing_cards": ["chapter_writing_card.yaml"],
                 "active_chapter_card": "chapter_writing_card.yaml",
                 "writing_started": True},
                missing,
                failures,
            )
        self.assertTrue(any("opening_bridge" in item or "section_structure" in item for item in failures))

    def test_h8_documents_declare_global_spine_and_chapter_handoffs(self):
        protocol = (ROOT / "references" / "h8_writer_first_protocol.md").read_text(encoding="utf-8")
        execution = (ROOT / "references" / "h8_chapter_execution.md").read_text(encoding="utf-8")
        warmup = (ROOT / "references" / "warmup" / "h8_writer_warmup.md").read_text(encoding="utf-8")
        for content in (protocol, execution, warmup):
            self.assertIn("paper_spine", content)
            self.assertIn("handoff_question", content)
        self.assertIn("核心章节", protocol)
        self.assertIn("支撑章节", protocol)

    def test_h8_documents_prioritize_modeling_as_the_core_argument(self):
        protocol = (ROOT / "references" / "h8_writer_first_protocol.md").read_text(encoding="utf-8")
        execution = (ROOT / "references" / "h8_chapter_execution.md").read_text(encoding="utf-8")
        self.assertIn("建模与求解", protocol)
        self.assertIn("核心", protocol)
        self.assertIn("建模与求解", execution)
        self.assertIn("支撑", execution)


if __name__ == "__main__":
    unittest.main()
