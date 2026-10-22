import importlib.util
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("audit_project", "scripts/audit_project.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class AuditProjectCopyTests(unittest.TestCase):
    def test_isolated_copy_ignores_recursive_diagnostics(self):
        names = ["paper", "tmp", "paper-before", "论文历史快照归档20260830", "results", "figures"]
        ignored = MODULE.isolated_copy_ignore("workspace", names)
        self.assertEqual(ignored, {"tmp", "paper-before", "论文历史快照归档20260830"})

    def test_isolated_copy_preserves_project_artifact_directories(self):
        names = ["paper", "results", "figures", "formal_delivery"]
        self.assertEqual(MODULE.isolated_copy_ignore("workspace", names), set())

    def test_visual_audit_is_skipped_without_explicit_opt_in(self):
        result = MODULE.visual_audit_result(Path("paper.pdf"), Path("."), False)
        self.assertEqual(result["status"], "SKIPPED")
        self.assertEqual(result["returncode"], 0)
        self.assertIn("SKIPPED_USER_OPT_IN", result["output_tail"])

    def test_visual_audit_runs_only_when_explicitly_enabled(self):
        with tempfile.TemporaryDirectory() as raw:
            paper = Path(raw) / "paper.txt"
            paper.write_text("正文内容。", encoding="utf-8")
            result = MODULE.visual_audit_result(paper, Path(raw), True)
            self.assertEqual(result["name"], "visual_critic")
            self.assertNotEqual(result["status"], "SKIPPED")


if __name__ == "__main__":
    unittest.main()
