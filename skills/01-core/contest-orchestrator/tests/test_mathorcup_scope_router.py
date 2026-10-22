import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import scope_router


class MathorCupScopeRouterTests(unittest.TestCase):
    def test_selected_mode_uses_m_nodes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "problem.pdf").write_bytes(b"problem fixture")
            report = scope_router.build_plan("FULL_CONTEST", root, mode="full-contest-mathorcup")
        self.assertEqual(report["execution_status"], "READY")
        self.assertEqual(report["active_mode"], "full-contest-mathorcup")
        self.assertEqual(report["phases"], ["M1", "M2", "M3", "M4", "M5"])

    def test_selected_mode_rejects_non_full_scope(self):
        report = scope_router.build_plan("PLAN_ONLY", None, mode="full-contest-mathorcup")
        self.assertEqual(report["execution_status"], "BLOCKED")

    def test_default_scope_route_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "problem.pdf").write_bytes(b"problem fixture")
            report = scope_router.build_plan("FULL_CONTEST", root)
        self.assertEqual(report["phases"], list("ABCDEFG"))


if __name__ == "__main__":
    unittest.main()
