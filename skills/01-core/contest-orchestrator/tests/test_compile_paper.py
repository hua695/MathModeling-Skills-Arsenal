import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import compile_paper  # noqa: E402


class CompilePaperTests(unittest.TestCase):
    def test_utf8_environment_is_explicit(self):
        env = compile_paper.utf8_subprocess_env()
        self.assertEqual(env["PYTHONUTF8"], "1")
        self.assertEqual(env["PYTHONIOENCODING"], "utf-8")
        original_path = os.environ.get("PATH", "")
        child_path = env.get("PATH", "")
        if os.name == "nt" and any(path.is_dir() for path in compile_paper.WINDOWS_TOOL_DIRS):
            self.assertNotEqual(child_path, original_path)
            self.assertTrue(
                any(str(path).lower() in child_path.lower().split(os.pathsep)
                    for path in compile_paper.WINDOWS_TOOL_DIRS if path.is_dir())
            )
        else:
            self.assertEqual(child_path, original_path)

    def test_run_command_preserves_unicode_output(self):
        with tempfile.TemporaryDirectory() as raw:
            result = compile_paper.run_command(
                [sys.executable, "-X", "utf8", "-c", "print('中文编译环境')"],
                Path(raw),
            )
        self.assertEqual(result["returncode"], 0, result)
        self.assertIn("中文编译环境", result["tail"])

    @unittest.skipUnless(os.name == "nt", "Windows latexmkrc policy")
    def test_latexmkrc_posix_construct_is_detected(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            (workspace / "latexmkrc").write_text(
                "if (system('command -v bibtex') == 0) { }\n", encoding="utf-8"
            )
            risks = compile_paper.latexmkrc_risks(workspace)
        self.assertIn("latexmkrc: command -v", risks)

    @unittest.skipUnless(os.name == "nt", "Windows latexmkrc policy")
    def test_latexmkrc_without_posix_construct_is_safe(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            (workspace / "latexmkrc").write_text(
                "$pdf_mode = 5;\n$xelatex = 'xelatex %O %S';\n", encoding="utf-8"
            )
            self.assertEqual(compile_paper.latexmkrc_risks(workspace), [])


if __name__ == "__main__":
    unittest.main()
