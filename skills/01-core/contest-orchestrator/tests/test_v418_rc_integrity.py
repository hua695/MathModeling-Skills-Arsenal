import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_paper_integrity.py"


class V418IntegrityTests(unittest.TestCase):
    def _run(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(root), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def _write_clean_fixture(self, root: Path) -> tuple[Path, Path, Path]:
        paper = root / "paper"
        paper.mkdir()
        symbols = root / "model_contract.yaml"
        symbols.write_text(
            "schema_version: '2.1'\nsubproblems:\n"
            "  - id: Q1\n    symbols:\n"
            "      - {name: 'd^\\star', meaning: 最优距离, unit: m}\n",
            encoding="utf-8",
        )
        symbol_table = paper / "04_symbols.tex"
        symbol_table.write_text("$d^\\star$ & 最优距离 & m\\\\\n", encoding="utf-8")
        (paper / "06_model.tex").write_text(
            "本文研究装配网络。设 $d^\\star$ 表示最优距离。\n"
            "本节定义状态转移关系，由式（1）可得目标值。\n",
            encoding="utf-8",
        )
        pdf_text = root / "paper.txt"
        pdf_text.write_text("本文研究装配网络。设 d^\\star 表示最优距离。\n", encoding="utf-8")
        delivery = root / "formal_delivery"
        delivery.mkdir()
        (delivery / "paper.pdf").write_bytes(b"pdf")
        return symbols, symbol_table, pdf_text

    def test_clean_candidate_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            symbols, symbol_table, pdf_text = self._write_clean_fixture(root)
            result = self._run(
                root / "paper",
                "--symbols", str(symbols),
                "--symbol-table", str(symbol_table),
                "--pdf-text", str(pdf_text),
                "--delivery-dir", str(root / "formal_delivery"),
            )
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue(json.loads(result.stdout)["passed"])

    def test_negative_echo_and_internal_meta_block(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            paper = root / "paper"
            paper.mkdir()
            (paper / "paper.tex").write_text(
                "根据评审意见，本轮修复了原方案。\n", encoding="utf-8"
            )
            result = self._run(paper)
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertTrue(report["negative_echo_hits"])
            self.assertTrue(report["internal_meta_hits"])

    def test_missing_first_use_definition_and_delivery_pollution_block(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            symbols, symbol_table, pdf_text = self._write_clean_fixture(root)
            model = root / "paper" / "06_model.tex"
            model.write_text("目标值包含 $d^\\star$。\n", encoding="utf-8")
            (root / "formal_delivery" / "tmp").mkdir()
            result = self._run(
                root / "paper",
                "--symbols", str(symbols),
                "--symbol-table", str(symbol_table),
                "--pdf-text", str(pdf_text),
                "--delivery-dir", str(root / "formal_delivery"),
                "--strict-first-use",
            )
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertTrue(report["packaging_hits"])
            self.assertEqual(len(report["symbol_report"]["issues"]), 1)
            self.assertIn("首次", report["symbol_report"]["issues"][0])


if __name__ == "__main__":
    unittest.main()
