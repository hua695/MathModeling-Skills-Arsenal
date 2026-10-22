from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_research_evidence.py"
sys.path.insert(0, str(ROOT / "scripts"))
from capture_run import make_manifest  # noqa: E402


class ResearchEvidenceContractTests(unittest.TestCase):
    def _write_file(self, root: Path, relative: str, content: str | bytes) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def _artifact(self, root: Path, relative: str, evidence_id: str, role: str) -> dict:
        path = root / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {"path": relative.replace("\\", "/"), "sha256": digest,
                "evidence_id": evidence_id, "role": role}

    def _fixture(self, root: Path) -> None:
        self._write_file(root, "paper.tex", "\\section{Q1} 主张结果 0.85。\\label{claim:score}\n")
        self._write_file(root, "solve.py", "print('ok')\n")
        self._write_file(root, "plot.py", "print('figure')\n")
        self._write_file(root, "inputs/raw.csv", "x\n1\n")
        self._write_file(root, "results/result.json", '{"score": 0.85}\n')
        references = """- ref_ID: 1
  citation_key: Smith2024
  title: A verified method
  authors: Smith A
  venue: Journal of Models
  year: 2024
  status: peer_reviewed
  doi: 10.1000/example
  url: https://doi.org/10.1000/example
  relevance: Q1 parameter basis
  key_points: Provides the parameter estimation method.
  limitations: Assumes independent observations.
  used_in: [section_Q1_modeling]
  verified_at: 2026-08-31T10:00:00+08:00
"""
        self._write_file(root, "references.yaml", references)
        citation_map = {
            "_metadata": {"research_evidence_version": "1.0"},
            "claim_evidence": [{
                "claim_id": "claim:score",
                "claim": "Q1 score is 0.85",
                "evidence": [{"source_id": "ev:result.score",
                              "locator": "results/result.json#/score",
                              "use": "supports numeric result"}],
                "location": {"file": "paper.tex", "anchor": "claim:score"},
                "use": "Q1 main result",
                "recomputable_from": [],
            }],
        }
        self._write_file(root, "citation_map.json", json.dumps(citation_map))
        model_contract = """research_evidence_version: '1.0'
subproblems:
  - id: Q1
    limitations:
      assumptions: observations are independent
      applicable_conditions: independent sampling is reasonable
      failure_conditions: strong serial correlation
      impact_direction: uncertainty is underestimated
      mitigation: add block bootstrap and sensitivity analysis
"""
        self._write_file(root, "model_contract.yaml", model_contract)
        manifest = {
            "schema_version": "1.0", "run_id": "run.research.001",
            "status": "completed",
            "command": {"argv": ["python", "solve.py"], "cwd": "."},
            "inputs": [self._artifact(root, "inputs/raw.csv", "ev:input.raw", "input")],
            "code": [self._artifact(root, "solve.py", "ev:code.solve", "code")],
            "outputs": [self._artifact(root, "results/result.json", "ev:result.score", "result")],
            "evidence": [{"evidence_id": "ev:claim.score", "kind": "numeric_claim",
                          "source_ids": ["ev:result.score"], "claim": "Q1 score is 0.85"}],
            "seed": 7, "exit_code": 0,
            "reproducibility": {
                "entrypoint": "solve.py",
                "inputs": ["inputs/raw.csv"],
                "parameters": [],
                "seed": 7,
                "command": ["python", "solve.py"],
                "outputs": ["results/result.json"],
                "figure_scripts": ["plot.py"],
                "result_paper_map": [{"claim_id": "claim:score",
                                       "output_evidence_id": "ev:result.score",
                                       "paper_location": "paper.tex#claim:score"}],
            },
        }
        run_dir = root / ".contest" / "runs" / "run.research.001"
        run_dir.mkdir(parents=True)
        self._write_file(run_dir, "run_manifest.json", json.dumps(manifest))

    def _run(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), str(root), "--strict"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def test_complete_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._fixture(root)
            result = self._run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "PASS")

    def test_missing_citation_map_returns_structured_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._fixture(root)
            (root / "citation_map.json").unlink()
            result = self._run(root)
            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("citation_map.json", report["issues"][0])

    def test_missing_source_record_field_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._fixture(root)
            text = (root / "references.yaml").read_text(encoding="utf-8")
            (root / "references.yaml").write_text(text.replace("  limitations: Assumes independent observations.\n", ""), encoding="utf-8")
            result = self._run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("limitations", result.stdout)

    def test_missing_limitation_chain_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._fixture(root)
            text = (root / "model_contract.yaml").read_text(encoding="utf-8")
            (root / "model_contract.yaml").write_text(text.replace("      mitigation: add block bootstrap and sensitivity analysis\n", ""), encoding="utf-8")
            result = self._run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mitigation", result.stdout)

    def test_derived_claim_requires_recomputable_relation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._fixture(root)
            path = root / "citation_map.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            claim = payload["claim_evidence"][0]
            claim["claim_type"] = "derived"
            claim["recomputable_from"] = []
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self._run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("recomputable_from", result.stdout)

    def test_capture_run_normalizes_reproducibility_paths(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self._fixture(root)
            spec = {
                "run_id": "run.capture.001", "status": "completed",
                "command": {"argv": ["python", "solve.py"], "cwd": "."},
                "inputs": ["inputs/raw.csv"], "code": ["solve.py"],
                "outputs": ["results/result.json"], "exit_code": 0,
                "evidence": [{"evidence_id": "ev:claim.capture", "source_ids": ["ev:artifact.results.result.json"]}],
                "reproducibility": {
                    "entrypoint": "solve.py", "inputs": ["inputs/raw.csv"], "parameters": [],
                    "seed": 7, "command": ["python", "solve.py"],
                    "outputs": ["results/result.json"], "figure_scripts": ["plot.py"],
                    "result_paper_map": [{"claim_id": "claim:score",
                                           "output_evidence_id": "ev:artifact.results.result.json",
                                           "paper_location": "paper.tex#claim:score"}],
                },
            }
            manifest = make_manifest(root, spec)
            self.assertEqual(manifest["reproducibility"]["entrypoint"], "solve.py")
            self.assertEqual(manifest["reproducibility"]["inputs"], ["inputs/raw.csv"])


if __name__ == "__main__":
    unittest.main()
