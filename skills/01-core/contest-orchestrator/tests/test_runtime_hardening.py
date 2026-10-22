import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_module(relative_path: str, name: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RuntimeHardeningTests(unittest.TestCase):
    def test_duplicate_yaml_keys_are_rejected(self):
        checker = load_module("scripts/check_harness_control.py", "check_harness_control_runtime")
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "duplicate.yaml"
            path.write_text("status: draft\nstatus: approved\n", encoding="utf-8")
            with self.assertRaises(yaml.YAMLError):
                checker.load_mapping(path)

    def test_sha256_comparison_accepts_hex_case_variation(self):
        checker = load_module("scripts/check_harness_control.py", "check_harness_control_hash")
        self.assertTrue(checker.same_digest("A" * 64, "a" * 64))
        self.assertFalse(checker.same_digest("A" * 64, "b" * 64))

    def test_dispatch_cannot_precede_predecessor_approval(self):
        checker = load_module("scripts/check_harness_control.py", "check_harness_control_order")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contest = root / ".contest"
            contest.mkdir()
            (contest / "status_history.yaml").write_text(yaml.safe_dump({
                "transitions": [{
                    "node_id": "H3", "from_status": "review_pending", "to_status": "approved",  # H4已并入H5，H5前驱是H3
                    "timestamp": "2026-09-08T14:20:00+00:00",
                }],
            }), encoding="utf-8")
            control = {"dispatch_records": [{
                "node_id": "H5", "dispatched_at": "2026-09-08T14:19:00+00:00",
            }]}
            missing, failures = [], []
            checker.validate_dispatch_order(root, control, "H5", missing, failures)

        self.assertTrue(any("H5" in item and "H3" in item for item in failures))  # H4已并入H5，H5前驱是H3

    def test_literature_sources_are_required_before_model_route(self):
        checker = load_module("scripts/check_harness_control.py", "check_harness_control_literature")
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            request = root / "literature_request.yaml"
            request.write_text("questions: [Q1]\n", encoding="utf-8")
            nodes = {
                "H3": {
                    "status": "approved",
                    "literature_request": "literature_request.yaml",
                    "literature_sources": "literature_sources.yaml",
                },
                "H5": {"status": "approved"},  # H4已并入H5，文献门在H5检查
            }
            missing, failures = [], []
            checker.validate_literature_gate(root, nodes, "H5", missing, failures)  # H4已并入H5

        self.assertTrue(any("literature_sources" in item for item in missing))

    def test_compile_env_propagates_configured_inkscape_directory(self):
        compiler = load_module("scripts/compile_paper.py", "compile_paper_env")
        with tempfile.TemporaryDirectory() as raw:
            tool_dir = Path(raw)
            (tool_dir / "inkscape.exe").write_text("placeholder", encoding="utf-8")
            with patch.object(compiler, "WINDOWS_TOOL_DIRS", (tool_dir,)):
                env = compiler.utf8_subprocess_env()

        path_key = next(key for key in env if key.lower() == "path")
        self.assertEqual(str(tool_dir), env[path_key].split(os.pathsep)[0])


if __name__ == "__main__":
    unittest.main()
