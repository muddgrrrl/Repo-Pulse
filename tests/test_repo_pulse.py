import subprocess
import tempfile
import unittest
from pathlib import Path

from repo_pulse import summarize


class RepoPulseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name).resolve() / "repo\n"
        self.repo.mkdir()
        self.git("init", "-b", "example")

    def git(self, *args):
        return subprocess.run(
            [
                "git",
                "-C",
                self.repo,
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                *args,
            ],
            check=True,
            capture_output=True,
        )

    def test_path_ending_with_newline_in_unborn_checkout(self):
        (self.repo / "work.txt").write_text("change", encoding="utf-8")
        report = summarize(self.repo, 5)
        self.assertEqual(report["repository"], str(self.repo))
        self.assertEqual(report["branch"], "example")
        self.assertIsNone(report["head"])
        self.assertEqual(report["changes"], [{"status": "??", "path": "work.txt"}])

    def test_staged_rename_and_recent_commit(self):
        (self.repo / "first.txt").write_text("one", encoding="utf-8")
        self.git("add", "first.txt")
        self.git("commit", "-m", "First")
        self.git("mv", "first.txt", "second.txt")
        report = summarize(self.repo, 1)
        self.assertEqual(report["recent_commits"][0]["subject"], "First")
        self.assertEqual(
            report["changes"],
            [{"status": "R ", "path": "second.txt", "previous": "first.txt"}],
        )
