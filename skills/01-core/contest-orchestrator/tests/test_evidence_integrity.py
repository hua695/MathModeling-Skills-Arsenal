from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class EvidenceIntegrityTests(unittest.TestCase):
    def run_script(self, name: str, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPTS / name), str(root), *args],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def spec(self, root: Path) -> Path:
        (root / "raw.csv").write_text("x\n1\n", encoding="utf-8")
        (root / "solve.py").write_text("print(1)\n", encoding="utf-8")
        (root / "results").mkdir()
        (root / "results" / "result.json").write_text('{"score": 0.85}\n', encoding="utf-8")
        (root / "numeric_source_map.json").write_text(json.dumps({
            "schema_version": "1.0",
            "claims": [{"id": "claim:score", "value": 0.85,
                        "source_file": "results/result.json", "json_pointer": "/score",
                        "text_anchor": "score 0.85"}]
        }), encoding="utf-8")
        spec = root / "run_spec.json"
        spec.write_text(json.dumps({
            "run_id": "run.test.001", "status": "completed",
            "command": {"argv": ["python", "solve.py"], "cwd": "."},
            "inputs": [{"path": "raw.csv", "evidence_id": "ev:input.raw"}],
            "code": [{"path": "solve.py", "evidence_id": "ev:code.solve"}],
            "outputs": [{"path": "results/result.json", "evidence_id": "ev:result.score",
                         "source_ids": ["ev:input.raw", "ev:code.solve"]}],
            "evidence": [{"evidence_id": "ev:claim.score", "kind": "numeric_claim",
                          "source_ids": ["ev:result.score"], "claim": "score 0.85"}],
            "seed": 7, "exit_code": 0
        }), encoding="utf-8")
        return spec

    def create_manifest(self, root: Path) -> None:
        spec = self.spec(root)
        (root / "numeric.tex").write_text("reported score 0.85\n", encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPTS / "capture_run.py"), str(root),
                                 "--spec", str(spec), "--out", str(root / ".contest" / "runs" / "run.test.001" / "run_manifest.json")],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_manifest_and_stale_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.create_manifest(root)
            checked = self.run_script("check_run_manifest.py", root, "--strict")
            self.assertEqual(checked.returncode, 0, checked.stdout)
            fresh = self.run_script("check_stale_evidence.py", root, "--strict")
            self.assertEqual(fresh.returncode, 0, fresh.stdout)
            numeric = self.run_script("audit_numeric_sources.py", root, "--paper", "numeric.tex", "--strict", "--require-map")
            self.assertEqual(numeric.returncode, 0, numeric.stdout)

    def test_changed_input_blocks_stale_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.create_manifest(root)
            (root / "raw.csv").write_text("x\n2\n", encoding="utf-8")
            checked = self.run_script("check_stale_evidence.py", root, "--strict")
            self.assertNotEqual(checked.returncode, 0)
            self.assertIn("哈希变化", checked.stdout)

    def test_absolute_or_unknown_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            spec = self.spec(root)
            payload = json.loads(spec.read_text(encoding="utf-8"))
            payload["outputs"][0]["source_ids"] = ["ev:not-found"]
            spec.write_text(json.dumps(payload), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPTS / "capture_run.py"), str(root),
                                     "--spec", str(spec), "--out", str(root / ".contest" / "runs" / "bad" / "run_manifest.json")],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0)
            checked = self.run_script("check_run_manifest.py", root, "--strict")
            self.assertNotEqual(checked.returncode, 0)
            self.assertIn("source_ids 未解析", checked.stdout)

    def test_numeric_source_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.spec(root)
            (root / "numeric.tex").write_text("reported score 0.85\n", encoding="utf-8")
            (root / "results" / "result.json").write_text('{"score": 0.91}\n', encoding="utf-8")
            checked = self.run_script("audit_numeric_sources.py", root, "--strict", "--require-map")
            self.assertNotEqual(checked.returncode, 0)
            self.assertIn("数值与来源不一致", checked.stdout)


if __name__ == "__main__":
    unittest.main()
