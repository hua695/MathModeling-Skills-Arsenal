import unittest

from scripts import check_harness_control, check_reader_evidence, check_visual_evidence


def _valid_model_card():
    return {
        "card_id": "Q1-final-model",
        "subproblem_id": "Q1",
        "reader_evidence": {
            "problem_need": "确定满足需求与约束的最优配置",
            "model_choice_reason": "目标与约束均可显式表达，适合采用优化模型",
            "data_scope": {
                "mode": "hybrid",
                "shared_inputs": ["题目给定需求"],
                "question_specific_inputs": ["Q1成本参数"],
                "placement_rationale": "公共数据在数据预处理章节统一说明，Q1参数在本问建模前说明",
            },
            "assumption_traceability": [
                {
                    "assumption_id": "A1",
                    "statement": "周期内需求参数保持不变",
                    "basis": "题面给定周期和需求口径",
                    "model_role": "使需求约束可写成确定性约束",
                    "impact_if_violated": "需求波动会改变可行域和最优解",
                    "validation_refs": ["validation_contract.yaml#/assumptions/A1"],
                }
            ],
            "derivation_arc": [
                {
                    "from": "题面需求约束",
                    "to": "需求平衡式",
                    "reason": "把文字条件转成可计算关系",
                }
            ],
            "final_model_reading": "求解器接收决策变量、目标函数、约束和参数并输出最优配置",
            "evaluation": {
                "strengths": [
                    {"claim": "约束含义清晰", "evidence_refs": ["validation_contract.yaml#/checks/constraints"]}
                ],
                "limitations": [
                    {
                        "source": "需求参数采用给定周期估计",
                        "impact": "极端需求变化下最优方案可能偏移",
                        "scope": "当前数据周期",
                        "evidence_refs": ["sensitivity_report.yaml#/results/0"],
                    }
                ],
                "improvements": [
                    {
                        "addresses": "需求波动影响",
                        "change": "引入情景或鲁棒约束",
                        "expected_effect": "扩大不确定需求下的适用范围",
                    }
                ],
            },
        },
    }


class ReaderEvidenceContractTests(unittest.TestCase):
    def test_complete_model_reader_evidence_passes(self):
        self.assertEqual(check_reader_evidence.validate_model_card(_valid_model_card()), [])

    def test_missing_assumption_traceability_blocks(self):
        card = _valid_model_card()
        del card["reader_evidence"]["assumption_traceability"]
        errors = check_reader_evidence.validate_model_card(card)
        self.assertTrue(any("assumption_traceability" in error for error in errors))

    def test_result_card_requires_observation_and_decision_interpretation(self):
        card = {
            "card_id": "Q1-result-01",
            "subproblem_id": "Q1",
            "result_statement": "方案成本为 10",
            "meaning": "回答成本最小化问题",
            "reasoning_basis": "由冻结求解结果支持",
            "supported_scope": "当前数据",
            "evidence_refs": ["results/Q1.yaml#/cost"],
            "reader_analysis": {
                "observed_pattern": "方案A低于基线",
                "comparison_basis": "与基线方案比较",
                "decision_implication": "推荐方案A",
                "boundary_or_exception": "在当前约束范围内成立",
            },
        }
        self.assertEqual(check_reader_evidence.validate_result_card(card), [])
        del card["reader_analysis"]["decision_implication"]
        errors = check_reader_evidence.validate_result_card(card)
        self.assertTrue(any("decision_implication" in error for error in errors))

    def test_author_chapter_requires_narrative_logic(self):
        chapter = {
            "section_id": "Q1",
            "reader_question": "如何得到Q1的可执行方案？",
            "chapter_purpose": "把题意转化为可求解模型并解释结果",
            "chapter_answer": "模型给出方案A",
            "reader_takeaway": "读者理解模型如何回答Q1",
            "authoring_arc": {
                "opening_tension": "需要在资源限制下满足需求",
                "evidence_sequence": ["题面条件", "模型推导", "冻结结果"],
                "interpretive_move": "把结果与基线和约束联系起来",
                "transition_question": "该方案在参数变化下是否稳定？",
            },
        }
        self.assertEqual(check_reader_evidence.validate_author_chapter(chapter), [])
        del chapter["authoring_arc"]["interpretive_move"]
        errors = check_reader_evidence.validate_author_chapter(chapter)
        self.assertTrue(any("interpretive_move" in error for error in errors))

    def test_visual_representation_must_match_disposition(self):
        slot = {
            "slot_id": "Q1-result",
            "category": "result_evidence",
            "disposition": "required",
            "representation": {
                "mode": "figure",
                "reason": "连续结果需要展示趋势",
                "pre_text_role": "先说明比较对象与指标",
                "post_text_role": "解释趋势对决策的含义",
            },
        }
        self.assertEqual(check_reader_evidence.validate_visual_representation(slot), [])
        slot["representation"]["mode"] = "table"
        errors = check_reader_evidence.validate_visual_representation(slot)
        self.assertTrue(any("mode" in error for error in errors))

    def test_control_activation_cannot_be_omitted_from_artifact(self):
        failures = []
        enabled = check_harness_control._reader_protocol_state(
            {"reader_evidence_protocol": "1.0"}, {}, "artifact", failures,
        )
        self.assertTrue(enabled)
        self.assertTrue(any("reader_evidence_version" in error for error in failures))

    def test_visual_plan_control_activation_requires_protocol_marker(self):
        report = check_visual_evidence.validate_visual_argument_plan(
            {}, reader_protocol_enabled=True,
        )
        self.assertTrue(any("reader_evidence_version" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
