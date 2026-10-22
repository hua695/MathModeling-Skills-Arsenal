import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "collab_gate.py"


class CollabGateTests(unittest.TestCase):
    def test_colab_gate_requires_approval_and_rechecks_digest(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "artifact.md").write_text("v1\n", encoding="utf-8")
            (root / "policy.yaml").write_text("""schema_version: '1.0'
gates:
  - id: G0
    artifact_groups:
      - name: artifact
        any_of: [artifact.md]
""", encoding="utf-8")
            base = [sys.executable, str(GATE), str(root), "--gate", "G0", "--policy", str(root / "policy.yaml")]
            paused = subprocess.run(base + ["--mode", "COLLAB"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(paused.returncode, 2)
            approved = subprocess.run(base + ["--approve", "--note", "用户确认"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(approved.returncode, 0, approved.stdout)
            passed = subprocess.run(base + ["--mode", "COLLAB"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(passed.returncode, 0, passed.stdout)
            (root / "artifact.md").write_text("v2\n", encoding="utf-8")
            changed = subprocess.run(base + ["--mode", "COLLAB"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(changed.returncode, 2)


if __name__ == "__main__":
    unittest.main()
