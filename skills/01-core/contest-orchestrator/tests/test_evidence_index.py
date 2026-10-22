import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_evidence_index.py"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class EvidenceIndexTests(unittest.TestCase):
    def run_script(self, root: Path, *extra: str) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run([sys.executable, str(SCRIPT), str(root), *extra],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)

    def seed_solution_sources(self, root: Path) -> None:
        for name, payload in {
            "model_contract.yaml": "schema_version: '2.1'\nsubproblems: []\n",
            "derivation_registry.yaml": "schema_version: '1.0'\nformulas: []\n",
            "modeling_solution_contract.yaml": "schema_version: '1.0'\nsubproblems: []\n",
        }.items():
            (root / name).write_text(payload, encoding="utf-8")
        write_json(root / ".contest" / "runs" / "run1" / "run_manifest.json", {
            "schema_version": "1.0", "run_id": "run1", "status": "completed", "exit_code": 0,
            "inputs": [], "outputs": [], "evidence": [], "command": {"argv": ["python"], "cwd": "."}
        })

    def test_strict_solution_builds_derived_index(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.seed_solution_sources(root)
            result = self.run_script(root, "--stage", "solution", "--strict")
            self.assertEqual(result.returncode, 0, result.stdout)
            index = json.loads((root / ".contest" / "evidence_index.json").read_text(encoding="utf-8"))
            self.assertTrue(index["derived"])
            self.assertTrue(index["passed"])
            self.assertEqual(index["kinds"]["run_manifest"], "present")

    def test_strict_solution_fails_with_missing_core_source(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "model_contract.yaml").write_text("subproblems: []\n", encoding="utf-8")
            result = self.run_script(root, "--stage", "solution", "--strict")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("缺少证据来源", result.stdout)

    def test_non_strict_missing_sources_is_visible_warning(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result = self.run_script(root, "--stage", "solution")
            self.assertEqual(result.returncode, 0)
            index = json.loads((root / ".contest" / "evidence_index.json").read_text(encoding="utf-8"))
            self.assertFalse(index["passed"])
            self.assertTrue(index["warnings"])


if __name__ == "__main__":
    unittest.main()
