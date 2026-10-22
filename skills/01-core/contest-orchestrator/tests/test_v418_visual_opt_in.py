import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


DELIVERY = load_module("delivery_all_visual", ROOT / "scripts" / "delivery_all.py")
DOCX = load_module("docx_pipeline_visual", ROOT / "scripts" / "docx_pipeline.py")


class VisualOptInTests(unittest.TestCase):
    def test_delivery_skip_is_explicit_and_non_blocking(self):
        item = DELIVERY.skipped_step(3, "visual", "SKIPPED_USER_OPT_IN")
        self.assertEqual(item["status"], "SKIPPED")
        self.assertFalse(DELIVERY.is_blocking(item, strict=True))

    def test_docx_visual_flag_is_opt_in(self):
        self.assertFalse(DOCX.visual_check_requested(["paper.tex", "paper.pdf"]))
        self.assertTrue(DOCX.visual_check_requested(["paper.tex", "paper.pdf", "--visual-check"]))


if __name__ == "__main__":
    unittest.main()
