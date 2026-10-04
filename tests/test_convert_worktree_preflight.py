import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "convert-worktree" / "SKILL.md"


class ConvertWorktreePreflightTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.main = Path(self.temp.name) / "main workspace"
        self.source = Path(self.temp.name) / "source worktree"
        self.main.mkdir()
        self.git(self.main, "init", "-b", "trunk")
        self.git(self.main, "config", "user.name", "Test")
        self.git(self.main, "config", "user.email", "test@example.invalid")
        (self.main / "tracked.txt").write_text("original\n")
        (self.main / ".gitignore").write_text("ignored.txt\n")
        self.git(self.main, "add", ".")
        self.git(self.main, "commit", "-m", "initial")
        self.git(self.main, "update-ref", "refs/remotes/origin/trunk", "HEAD")
        self.git(
            self.main, "symbolic-ref", "refs/remotes/origin/HEAD",
            "refs/remotes/origin/trunk",
        )
        self.git(self.main, "worktree", "add", "-b", "feat/test", str(self.source))

    def git(self, directory, *args):
        return subprocess.check_output(
            ["git", "-C", str(directory), *args], text=True,
            stderr=subprocess.PIPE,
        ).strip()

    def block(self, step):
        section = re.search(
            rf"### {step}\. .*?(?=\n### |\n## |\Z)", self.text, re.DOTALL,
        )
        self.assertIsNotNone(section, f"missing conversion step {step}")
        block = re.search(r"```bash\n(.*?)```", section[0], re.DOTALL)
        self.assertIsNotNone(block, f"step {step} needs an executable check")
        return block[1]

    def run_block(self, step, stash_oid=""):
        env = dict(os.environ, MAIN_WORKTREE=str(self.main),
                   WORKTREE_PATH=str(self.source), BRANCH="feat/test",
                   BASE_BRANCH="trunk", STASH_OID=stash_oid)
        result = subprocess.run(
            ["bash", "-c", self.block(step)], cwd=self.source, env=env,
            text=True, capture_output=True,
        )
        self.assertNotIn("syntax error", result.stderr)
        return result

    def test_dirty_destination_stops_preflight_without_mutations(self):
        (self.main / "tracked.txt").write_text("destination changes\n")
        (self.source / "tracked.txt").write_text("source changes\n")
        (self.source / "scratch.txt").write_text("source scratch\n")
        before = self.git(self.source, "status", "--porcelain")
        head = self.git(self.source, "rev-parse", "HEAD")
        result = self.run_block(1)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git(self.source, "status", "--porcelain"), before)
        self.assertEqual(self.git(self.source, "rev-parse", "HEAD"), head)
        self.assertEqual(self.git(self.source, "stash", "list"), "")
        self.assertTrue(self.source.is_dir())

    def test_detached_source_stops_preflight(self):
        self.git(self.source, "checkout", "--detach")
        result = self.run_block(1)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ignored_source_paths_stop_before_preservation(self):
        (self.source / "ignored.txt").write_text("valuable source cache\n")
        head = self.git(self.source, "rev-parse", "HEAD")
        result = self.run_block(1)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git(self.source, "rev-parse", "HEAD"), head)
        self.assertEqual(self.git(self.source, "stash", "list"), "")
        self.assertEqual((self.source / "ignored.txt").read_text(), "valuable source cache\n")

    def test_confirmation_precedes_every_source_mutation(self):
        preflight = self.text.split("### 2.")[0].lower()
        self.assertIn("confirm", preflight)
        self.assertIn("declines", preflight)
        self.assertIn("unchanged", preflight)
        for command in ("git add -u", "git commit", "git stash push", "make dev-stop",
                        "git rebase ", "git worktree remove"):
            self.assertNotIn(command, preflight)

    def stash_scratch(self):
        (self.source / "scratch.txt").write_text("preserved scratch\n")
        self.git(self.source, "stash", "push", "--include-untracked", "-m", "conversion")
        return self.git(self.source, "rev-parse", "refs/stash")

    def test_restore_uses_recorded_stash_even_when_a_newer_stash_exists(self):
        stash = self.stash_scratch()
        (self.main / "other.txt").write_text("unrelated stash\n")
        self.git(self.main, "stash", "push", "--include-untracked", "-m", "unrelated")
        newer = self.git(self.main, "rev-parse", "refs/stash")
        result = self.run_block(5, stash)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.main / "scratch.txt").read_text(), "preserved scratch\n")
        self.assertFalse((self.main / "other.txt").exists())
        self.assertEqual(self.git(self.main, "rev-parse", "refs/stash"), newer)
        self.assertFalse(self.source.exists())

    def test_failed_stash_restore_keeps_source_and_recovery_stash(self):
        stash = self.stash_scratch()
        # An ignored destination path passes a normal status check but blocks
        # stash restoration, so the source must survive that later failure.
        with (self.main / ".git" / "info" / "exclude").open("a") as handle:
            handle.write("scratch.txt\n")
        (self.main / "scratch.txt").write_text("destination scratch\n")
        result = self.run_block(5, stash)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.source.is_dir())
        self.assertEqual((self.main / "scratch.txt").read_text(), "destination scratch\n")
        self.assertIn(stash, self.git(self.main, "stash", "list", "--format=%H"))

    def test_failed_checkout_reattaches_source_and_restores_its_stash(self):
        (self.source / "feature.txt").write_text("feature content\n")
        self.git(self.source, "add", "feature.txt")
        self.git(self.source, "commit", "-m", "feat: feature file")
        stash = self.stash_scratch()
        with (self.main / ".git" / "info" / "exclude").open("a") as handle:
            handle.write("feature.txt\n")
        (self.main / "feature.txt").write_text("valuable ignored destination file\n")
        result = self.run_block(5, stash)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git(self.main, "branch", "--show-current"), "trunk")
        self.assertEqual(self.git(self.source, "branch", "--show-current"), "feat/test")
        self.assertEqual((self.source / "scratch.txt").read_text(), "preserved scratch\n")
        self.assertEqual((self.main / "feature.txt").read_text(),
                         "valuable ignored destination file\n")
        self.assertIn(stash, self.git(self.main, "stash", "list", "--format=%H"))

    def test_changed_source_branch_stops_before_detachment(self):
        self.git(self.source, "checkout", "-b", "feat/other")
        result = self.run_block(5)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git(self.source, "branch", "--show-current"), "feat/other")
        self.assertTrue(self.source.is_dir())

    def test_ignored_source_files_prevent_removal_without_force(self):
        (self.source / "ignored.txt").write_text("source artifact\n")
        result = self.run_block(5)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.source / "ignored.txt").read_text(), "source artifact\n")
        self.assertNotRegex(self.text, r"git worktree remove[^\n]*--force")

    def test_recovery_record_does_not_depend_on_shell_state(self):
        self.assertIn("recovery record", self.text.lower())
        self.assertIn("ORIGINAL_HEAD", self.text)
        self.assertIn("WIP_COMMIT", self.text)
        self.assertIn("STASH_OID", self.text)
        self.assertIn("literal values", self.text)
        self.assertIn("git stash apply", self.text)
        self.assertIn("git reset --mixed", self.text)
        self.assertNotIn("STASHED_UNTRACKED", self.text)

    def test_copy_uses_default_branch_and_safe_failure_contract(self):
        readme = (ROOT / "README.md").read_text()
        section = readme.split("### [convert-worktree]")[1].split("\n---")[0]
        self.assertNotIn("base branch", section)
        self.assertNotIn("Never blocks on failures", section)
        self.assertNotIn("latest base branch", self.text)
        self.assertNotIn("The conversion always completes", self.text)


if __name__ == "__main__":
    unittest.main()
