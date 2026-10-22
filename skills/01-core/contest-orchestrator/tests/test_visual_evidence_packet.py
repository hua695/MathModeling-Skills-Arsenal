import hashlib
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts import check_harness_control
from scripts import check_visual_evidence


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_evidence(root: Path, text: str = "frozen evidence") -> dict:
    path = root / "results.yaml"
    path.write_text(text + "\n", encoding="utf-8")
    return {
        "path": "results.yaml",
        "sha256": _sha256(path),
        "locator": "#/q1/result",
    }


def _packet(root: Path, *, status: str = "draft") -> dict:
    evidence = _write_evidence(root)
    model_contract = root / "model_contract.yaml"
    model_contract.write_text("model: frozen\n", encoding="utf-8")
    return {
        "schema_version": "1.0",
        "status": status,
        "package_mode": "indexed_minimal",
        "source_node": "H5",
        "created_by": "H5",
        "verified_by": "H6" if status == "verified" else None,
        "verification_agent_instance_id": "H6-agent-01" if status == "verified" else None,
        "model_contract_sha256": _sha256(model_contract),
        "subproblems": [{
            "subproblem_id": "Q1",
            "task_goal": "确定最优配置",
            "model_role": "给出可计算的配置方案",
            "information_units": [
                {
                    "unit_id": "Q1-U01",
                    "unit_type": "model",
                    "statement": "目标函数在约束下给出最优配置",
                    "meaning": "说明模型输出的决策对象",
                    "evidence_refs": [evidence],
                    "scope": "给定需求和约束",
                    "unit": "无量纲",
                },
                {
                    "unit_id": "Q1-U02",
                    "unit_type": "result",
                    "statement": "最优配置满足全部硬约束",
                    "meaning": "说明方案具备可行性",
                    "evidence_refs": [evidence],
                    "scope": "当前数据版本",
                    "unit": "无量纲",
                },
            ],
        }],
        "cross_question_interfaces": [],
    }


class VisualEvidencePacketTests(unittest.TestCase):
    def test_packet_accepts_indexed_frozen_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            report = check_visual_evidence.validate_visual_evidence_packet(
                _packet(root), root=root, expected_subproblems=["Q1"], stage="h5"
            )
            self.assertEqual(report["status"], "PASS", report)
            self.assertEqual(report["metrics"]["information_unit_count"], 2)

    def test_packet_rejects_missing_information_units(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            packet = _packet(root)
            packet["subproblems"][0]["information_units"] = []
            report = check_visual_evidence.validate_visual_evidence_packet(
                packet, root=root, expected_subproblems=["Q1"], stage="h5"
            )
            self.assertEqual(report["status"], "BLOCK")
            self.assertTrue(any("information_units" in item for item in report["errors"]))

    def test_packet_rejects_single_information_unit(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            packet = _packet(root)
            packet["subproblems"][0]["information_units"] = packet["subproblems"][0]["information_units"][:1]
            report = check_visual_evidence.validate_visual_evidence_packet(
                packet, root=root, expected_subproblems=["Q1"], stage="h5"
            )
            self.assertEqual(report["status"], "BLOCK")
            self.assertTrue(any("至少需要 2 个独立信息单元" in item for item in report["errors"]))

    def test_packet_rejects_duplicate_unit_statement_and_stale_hash(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            packet = _packet(root)
            duplicate = dict(packet["subproblems"][0]["information_units"][0])
            duplicate["unit_id"] = "Q1-U03"
            packet["subproblems"][0]["information_units"].append(duplicate)
            (root / "results.yaml").write_text("changed evidence\n", encoding="utf-8")
            report = check_visual_evidence.validate_visual_evidence_packet(
                packet, root=root, expected_subproblems=["Q1"], stage="h5"
            )
            self.assertEqual(report["status"], "BLOCK")
            self.assertTrue(any("重复" in item for item in report["errors"]))
            self.assertTrue(any("哈希" in item or "证据" in item for item in report["errors"]))

    def test_h6_packet_requires_verified_current_instance(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            report = check_visual_evidence.validate_visual_evidence_packet(
                _packet(root),
                root=root,
                expected_subproblems=["Q1"],
                stage="h6",
                expected_h6_instance="H6-agent-01",
            )
            self.assertEqual(report["status"], "BLOCK")
            self.assertTrue(any("verified" in item or "H6" in item for item in report["errors"]))

    def test_harness_requires_packet_for_h6_and_h7_inputs(self):
        self.assertIn("visual_evidence_packet.yaml", check_harness_control.REQUIRED_INPUT_BY_NODE["H6"])
        self.assertIn("visual_evidence_packet.yaml", check_harness_control.REQUIRED_INPUT_BY_NODE["H7"])

    def test_harness_gate_blocks_missing_packet_before_h6(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            control = check_harness_control.default_control()
            missing = []
            failures = []
            check_harness_control._validate_visual_evidence_packet(
                root,
                control["nodes"],
                {"subproblems": ["Q1"]},
                "H6",
                missing,
                failures,
            )
            self.assertTrue(any("H5" in item and "visual_evidence_packet" in item for item in missing))
            self.assertTrue(any("H6" in item and "visual_evidence_packet" in item for item in missing))

    def test_harness_gate_accepts_verified_packet_through_h7(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            packet = _packet(root, status="verified")
            (root / "visual_evidence_packet.yaml").write_text(
                yaml.safe_dump(packet, allow_unicode=True), encoding="utf-8"
            )
            control = check_harness_control.default_control()
            control["nodes"]["H5"]["model_contract"] = "model_contract.yaml"
            control["nodes"]["H6"]["agent_instance_id"] = "H6-agent-01"
            for node_id in ("H5", "H6", "H7"):
                control["nodes"][node_id]["visual_evidence_packet"] = "visual_evidence_packet.yaml"
            missing = []
            failures = []
            check_harness_control._validate_visual_evidence_packet(
                root,
                control["nodes"],
                {"subproblems": ["Q1"]},
                "H7",
                missing,
                failures,
            )
            self.assertEqual(missing, [])
            self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
