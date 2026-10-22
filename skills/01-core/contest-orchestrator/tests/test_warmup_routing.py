import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WarmupRoutingTests(unittest.TestCase):
    def test_h6_warmup_is_compact_and_routes_to_protocol(self):
        content = (ROOT / "references" / "warmup" / "h6_verifier_warmup.md").read_text(encoding="utf-8")
        self.assertLess(len(content), 2600)
        self.assertIn("h6_verification_scope.yaml", content)
        self.assertIn("h6_validation_protocol.md", content)
        self.assertTrue((ROOT / "references" / "h6_validation_protocol.md").is_file())

    def test_h8_warmup_is_compact_and_routes_to_chapter_execution(self):
        content = (ROOT / "references" / "warmup" / "h8_writer_warmup.md").read_text(encoding="utf-8")
        self.assertLess(len(content), 4200)
        self.assertIn("论文作者", content)
        self.assertIn("paper_argument_blueprint.yaml", content)
        self.assertIn("visual_argument_plan.yaml", content)
        self.assertIn("h8_chapter_execution.md", content)
        self.assertTrue((ROOT / "references" / "h8_chapter_execution.md").is_file())


if __name__ == "__main__":
    unittest.main()
