#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""H7 figure registry and H9 delivery provenance hardening tests.

Covers duplicate figure_id rejection, hash verification for registered
artifacts, execution_provenance structure, and SHA-256 recomputation.
"""
import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_harness_control as checker  # noqa: E402


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _make_base_figure(figure_id="F1", kind="data", generator="modelviz"):
    return {
        "figure_id": figure_id,
        "kind": kind,
        "generator": generator,
        "formats": ["svg", "png"],
        "source": "results/result.json",
        "qa_status": "reviewed",
        "insertion_format": "svg",
        "layout_mode": "single",
        "visual_qa": "passed",
        "caption_claim": "测试图注主张",
        "paper_location": "5.2",
        "decision_author": "scipilot-figure-skill",
        "semantic_qa": "scipilot-figure-skill",
        "decision_card": "figures/F1.decision.json",
    }


def _write_registry(root: Path, figures: list, pipeline: dict | None = None):
    if pipeline is None:
        pipeline = {
            "scipilot_decision": {"status": "passed"},
            "modelviz_generation": {"status": "passed"},
            "scipilot_qa": {"status": "passed"},
        }
    (root / "registry.yaml").write_text(
        yaml.safe_dump({"pipeline_audit": pipeline, "figures": figures}),
        encoding="utf-8",
    )


class H7DuplicateIdTests(unittest.TestCase):
    def test_rejects_duplicate_figure_id(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "figures").mkdir()
            (root / "results").mkdir()
            (root / "results" / "result.json").write_text("{}", encoding="utf-8")
            (root / "figures" / "F1.decision.json").write_text("{}", encoding="utf-8")
            f1 = _make_base_figure("F1")
            f2 = _make_base_figure("F1")
            f2["decision_card"] = "figures/F1.decision.json"
            _write_registry(root, [f1, f2])
            failures, missing = [], []
            checker._validate_h7_figures(root, {"figure_registry": "registry.yaml"}, missing, failures)
        self.assertTrue(any("duplicate" in item.lower() or "重复" in item for item in failures),
                        f"Expected duplicate figure_id failure, got: {failures}")

    def test_accepts_unique_figure_ids(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "figures").mkdir()
            (root / "results").mkdir()
            (root / "results" / "result.json").write_text("{}", encoding="utf-8")
            (root / "figures" / "F1.decision.json").write_text("{}", encoding="utf-8")
            (root / "figures" / "F2.decision.json").write_text("{}", encoding="utf-8")
            f1 = _make_base_figure("F1")
            f2 = _make_base_figure("F2")
            f2["decision_card"] = "figures/F2.decision.json"
            _write_registry(root, [f1, f2])
            failures, missing = [], []
            checker._validate_h7_figures(root, {"figure_registry": "registry.yaml"}, missing, failures)
        dup_failures = [f for f in failures if "duplicate" in f.lower() or "重复" in f]
        self.assertEqual(dup_failures, [], f"Unexpected duplicate failure: {dup_failures}")


class H7HashVerificationTests(unittest.TestCase):
    def test_rejects_mismatched_decision_card_hash(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "figures").mkdir()
            (root / "results").mkdir()
            (root / "results" / "result.json").write_text("{}", encoding="utf-8")
            dc_content = b'{"decision": "valid"}'
            (root / "figures" / "F1.decision.json").write_bytes(dc_content)
            fig = _make_base_figure("F1")
            fig["decision_card_sha256"] = "a" * 64  # wrong hash
            _write_registry(root, [fig])
            failures, missing = [], []
            checker._validate_h7_figures(root, {"figure_registry": "registry.yaml"}, missing, failures)
        self.assertTrue(any("decision_card" in item and ("hash" in item.lower() or "哈希" in item or "sha256" in item.lower())
                            for item in failures),
                        f"Expected decision_card hash failure, got: {failures}")

    def test_accepts_matching_decision_card_hash(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "figures").mkdir()
            (root / "results").mkdir()
            (root / "results" / "result.json").write_text("{}", encoding="utf-8")
            dc_content = b'{"decision": "valid"}'
            (root / "figures" / "F1.decision.json").write_bytes(dc_content)
            fig = _make_base_figure("F1")
            fig["decision_card_sha256"] = _sha256(dc_content)
            _write_registry(root, [fig])
            failures, missing = [], []
            checker._validate_h7_figures(root, {"figure_registry": "registry.yaml"}, missing, failures)
        hash_failures = [f for f in failures if "sha256" in f.lower() or "哈希" in f]
        self.assertEqual(hash_failures, [], f"Unexpected hash failure: {hash_failures}")

    def test_rejects_mismatched_output_file_hash(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "figures").mkdir()
            (root / "results").mkdir()
            (root / "results" / "result.json").write_text("{}", encoding="utf-8")
            (root / "figures" / "F1.decision.json").write_text("{}", encoding="utf-8")
            svg_content = b"<svg></svg>"
            (root / "figures" / "F1.svg").write_bytes(svg_content)
            (root / "figures" / "F1.png").write_bytes(b"\x89PNG\r\n")
            fig = _make_base_figure("F1")
            fig["svg"] = "figures/F1.svg"
            fig["png"] = "figures/F1.png"
            fig["svg_sha256"] = "b" * 64  # wrong hash
            _write_registry(root, [fig])
            failures, missing = [], []
            checker._validate_h7_figures(root, {"figure_registry": "registry.yaml"}, missing, failures)
        self.assertTrue(any("svg" in item.lower() and ("sha256" in item.lower() or "哈希" in item)
                            for item in failures),
                        f"Expected svg hash failure, got: {failures}")


class H9ExecutionProvenanceTests(unittest.TestCase):
    def _make_delivery_report(self, root: Path, **overrides):
        report = {
            "status": "PASS",
            "command": "python scripts/delivery_all.py . --strict",
            "project_root": str(root),
            "run_at": "2026-09-05T00:00:00Z",
            "input_sha256": "c" * 64,
            "artifacts": [
                {"path": "paper.pdf", "sha256": "d" * 64},
            ],
        }
        report.update(overrides)
        return report

    def test_rejects_echo_command(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.pdf").write_bytes(b"%PDF-1.4\n%%EOF")
            report = self._make_delivery_report(root, command="echo python scripts/delivery_all.py . --strict")
            (root / "delivery_report.yaml").write_text(yaml.safe_dump(report), encoding="utf-8")
            failures, missing = [], []
            checker._validate_h9_delivery(root, {"delivery_report": "delivery_report.yaml"}, missing, failures)
        self.assertTrue(any("echo" in item.lower() or "伪造" in item or "真实 python" in item
                            for item in failures),
                        f"Expected echo command failure, got: {failures}")

    def test_rejects_fake_project_root(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.pdf").write_bytes(b"%PDF-1.4\n%%EOF")
            report = self._make_delivery_report(root, project_root="/nonexistent/fake/root")
            (root / "delivery_report.yaml").write_text(yaml.safe_dump(report), encoding="utf-8")
            failures, missing = [], []
            checker._validate_h9_delivery(root, {"delivery_report": "delivery_report.yaml"}, missing, failures)
        self.assertTrue(any("project_root" in item and ("不一致" in item or "mismatch" in item.lower())
                            for item in failures),
                        f"Expected project_root mismatch failure, got: {failures}")

    def test_rejects_invalid_input_hash(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "paper.pdf").write_bytes(b"%PDF-1.4\n%%EOF")
            report = self._make_delivery_report(root, input_sha256="not-a-valid-hash")
            (root / "delivery_report.yaml").write_text(yaml.safe_dump(report), encoding="utf-8")
            failures, missing = [], []
            checker._validate_h9_delivery(root, {"delivery_report": "delivery_report.yaml"}, missing, failures)
        self.assertTrue(any("input_sha256" in item for item in failures),
                        f"Expected input_sha256 failure, got: {failures}")


class H9ArtifactHashRecomputeTests(unittest.TestCase):
    def test_rejects_mismatched_artifact_hash(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pdf_content = b"%PDF-1.4\n%%EOF\n"
            (root / "paper.pdf").write_bytes(pdf_content)
            report = {
                "status": "PASS",
                "command": "python scripts/delivery_all.py . --strict",
                "project_root": str(root),
                "run_at": "2026-09-05T00:00:00Z",
                "input_sha256": "e" * 64,
                "artifacts": [
                    {"path": "paper.pdf", "sha256": "f" * 64},  # wrong hash
                ],
            }
            (root / "delivery_report.yaml").write_text(yaml.safe_dump(report), encoding="utf-8")
            failures, missing = [], []
            checker._validate_h9_delivery(root, {"delivery_report": "delivery_report.yaml"}, missing, failures)
        self.assertTrue(any("paper.pdf" in item and ("sha256" in item.lower() or "哈希" in item or "mismatch" in item.lower())
                            for item in failures),
                        f"Expected artifact hash mismatch failure, got: {failures}")

    def test_accepts_matching_artifact_hash(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            pdf_content = b"%PDF-1.4\n%%EOF\n"
            (root / "paper.pdf").write_bytes(pdf_content)
            pdf_hash = _sha256(pdf_content)
            # Build input_manifest and compute total hash
            manifest_files = [{"path": "paper.pdf", "sha256": pdf_hash}]
            manifest_content = "\n".join(sorted(f"{mf['path']}:{mf['sha256']}" for mf in manifest_files))
            input_total = hashlib.sha256(manifest_content.encode("utf-8")).hexdigest()
            (root / "input_manifest.yaml").write_text(
                yaml.safe_dump({"files": manifest_files}), encoding="utf-8")
            report = {
                "status": "PASS",
                "command": "python scripts/delivery_all.py . --strict",
                "project_root": str(root),
                "run_at": "2026-09-05T00:00:00Z",
                "input_sha256": input_total,
                "input_manifest": "input_manifest.yaml",
                "artifacts": [
                    {"path": "paper.pdf", "sha256": pdf_hash},
                ],
            }
            (root / "delivery_report.yaml").write_text(yaml.safe_dump(report), encoding="utf-8")
            failures, missing = [], []
            checker._validate_h9_delivery(root, {"delivery_report": "delivery_report.yaml"}, missing, failures)
        hash_failures = [f for f in failures if "sha256" in f.lower() or "哈希" in f or "mismatch" in f.lower()
                         or "input_manifest" in f.lower()]
        self.assertEqual(hash_failures, [], f"Unexpected hash failure: {hash_failures}")


if __name__ == "__main__":
    unittest.main()
