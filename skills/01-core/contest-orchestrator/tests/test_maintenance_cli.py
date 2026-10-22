import os
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_help(script: str):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )


class MaintenanceCliTests(unittest.TestCase):
    def test_sync_help_is_read_only(self):
        result = run_help("sync_skill_to_workbuddy.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout.lower())
        self.assertNotIn("已同步", result.stdout)

    def test_conversion_help_is_read_only(self):
        result = run_help("convert_wb_to_jsonl.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout.lower())
        self.assertNotIn("转换案例", result.stdout)

    def test_mutating_maintenance_scripts_expose_apply_and_help_is_safe(self):
        scripts = [
            "import_experience.py", "import_public_experience.py",
            "import_public_jsonl.py",
            "retag_real_replay.py", "add_meta_fd.py", "rm_bad_fd522.py",
            "dedup_wbp9.py", "retag_wb_fd.py", "archive_user_artifacts.py",
            "semantic_replay.py",
        ]
        for script in scripts:
            result = run_help(script)
            self.assertEqual(result.returncode, 0, f"{script}: {result.stderr}")
            self.assertIn("usage:", result.stdout.lower(), script)
            if script != "semantic_replay.py":
                self.assertIn("--apply", result.stdout, script)

    def test_archive_dry_run_does_not_create_archive(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "skill"
            (root / "scripts" / "archive").mkdir(parents=True)
            (root / "scripts" / "archive" / "old.py").write_text("old", encoding="utf-8")
            archive = Path(td) / "archive"
            command = [sys.executable, str(ROOT / "scripts" / "archive_user_artifacts.py"),
                       "--skill-root", str(root), "--archive-root", str(archive), "--dry-run"]
            result = subprocess.run(command, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "scripts" / "archive" / "old.py").exists())
            self.assertFalse(archive.exists())

    def test_archive_apply_records_hash_verification(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "skill"
            (root / "scripts" / "archive").mkdir(parents=True)
            (root / "scripts" / "archive" / "old.py").write_text("old", encoding="utf-8")
            archive = Path(td) / "archive"
            command = [sys.executable, str(ROOT / "scripts" / "archive_user_artifacts.py"),
                       "--skill-root", str(root), "--archive-root", str(archive), "--apply"]
            result = subprocess.run(command, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stderr)
            manifests = list(archive.rglob("archive_manifest.json"))
            self.assertEqual(len(manifests), 1)
            item = json.loads(manifests[0].read_text(encoding="utf-8"))["items"][0]
            self.assertTrue(item["verified"])
            self.assertFalse((root / "scripts" / "archive").exists())

    def test_runtime_artifact_archive_excludes_memory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "skill"
            (root / "competition_replay").mkdir(parents=True)
            (root / "competition_replay" / "result.json").write_text("{}", encoding="utf-8")
            (root / "memory" / "inbox").mkdir(parents=True)
            (root / "memory" / "inbox" / "keep.yaml").write_text("id: keep", encoding="utf-8")
            archive = Path(td) / "archive"
            command = [sys.executable, str(ROOT / "scripts" / "archive_user_artifacts.py"),
                       "--skill-root", str(root), "--archive-root", str(archive),
                       "--include", "runtime-artifacts", "--apply"]
            result = subprocess.run(command, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "competition_replay").exists())
            self.assertTrue((root / "memory" / "inbox" / "keep.yaml").exists())


if __name__ == "__main__":
    unittest.main()
