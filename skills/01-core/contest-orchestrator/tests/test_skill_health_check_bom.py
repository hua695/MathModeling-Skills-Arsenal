#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOM compatibility regression tests for skill_health_check.py.

Verifies that Python source files with a UTF-8 BOM are read and compiled
without false syntax failures, while genuinely invalid files still fail.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import skill_health_check  # noqa: E402


class BomCompatibilityTests(unittest.TestCase):
    def test_bom_valid_file_passes_compilation(self):
        valid_source = b"\xef\xbb\xbf" + b"VALUE = 1\n"
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "valid_bom.py"
            path.write_bytes(valid_source)
            source = skill_health_check._read_python_source(path)
            self.assertNotIn("\ufeff", source)
            compile(source, str(path), "exec")  # must not raise

    def test_bom_invalid_file_still_fails(self):
        invalid_source = b"\xef\xbb\xbf" + b"def broken(:\n"
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "invalid_bom.py"
            path.write_bytes(invalid_source)
            source = skill_health_check._read_python_source(path)
            with self.assertRaises(SyntaxError):
                compile(source, str(path), "exec")

    def test_utf8_without_bom_passes(self):
        normal_source = b"# -*- coding: utf-8 -*-\nVALUE = 1\n"
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "normal.py"
            path.write_bytes(normal_source)
            source = skill_health_check._read_python_source(path)
            compile(source, str(path), "exec")  # must not raise

    def test_check_function_reports_no_syntax_error_for_bom_file(self):
        """The full check() function must not report a syntax error for a
        valid BOM-bearing Python file.  We only assert on the syntax-error
        portion of the failures list; other required-file failures are
        expected in this minimal fixture."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "contest-orchestrator"
            root.mkdir()
            (root / "scripts").mkdir()
            bom_file = root / "scripts" / "bom_module.py"
            bom_file.write_bytes(b"\xef\xbb\xbf" + b"VALUE = 1\n")
            report = skill_health_check.check(root, strict=False, smoke=False)
            syntax_failures = [f for f in report["failures"] if f.startswith("syntax error:")]
            self.assertEqual(syntax_failures, [], f"Unexpected syntax failures: {syntax_failures}")


if __name__ == "__main__":
    unittest.main()
