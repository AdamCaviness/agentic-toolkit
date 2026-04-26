import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "convert-worktree" / "SKILL.md"


class ConvertWorktreeUntrackedReviewGateTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text()
        self.lower = self.text.lower()

    def test_skill_inventories_working_tree_before_touching_it(self):
        self.assertIn("git status --short", self.text)

    def test_skill_does_not_blanket_stage_untracked_into_history(self):
        # Forbid `git add -A` as an actual command in any fenced code block,
        # but allow prose to reference it as the failure mode being avoided.
        for block in re.findall(r"```[a-zA-Z]*\n(.*?)```", self.text, flags=re.DOTALL):
            for line in block.splitlines():
                self.assertFalse(
                    re.match(r"^\s*git add -A\b", line),
                    f"convert-worktree skill must not run `git add -A` as a command: {line!r}",
                )

    def test_skill_stages_only_tracked_modifications_for_wip_commit(self):
        self.assertIn("git add -u", self.text)

    def test_skill_only_commits_when_index_has_content(self):
        self.assertIn('git diff --cached --name-only', self.text)

    def test_skill_stashes_untracked_files_outside_history(self):
        self.assertIn("git ls-files --others --exclude-standard", self.text)
        self.assertRegex(
            self.text,
            r"git stash push --include-untracked.*convert-worktree:untracked",
        )

    def test_skill_pops_untracked_stash_after_main_workspace_checkout(self):
        match = re.search(r'git checkout "\$BRANCH"', self.text)
        self.assertIsNotNone(match, "skill must checkout branch in main workspace")
        tail = self.text[match.end():]
        self.assertIn("git stash pop", tail)
        self.assertIn("STASHED_UNTRACKED", tail)

    def test_skill_drops_misleading_gitignore_safety_claim(self):
        self.assertNotIn(
            "`.gitignore` handles exclusions so `git add -A` is safe",
            self.text,
        )

    def test_skill_rules_forbid_auto_committing_untracked_files(self):
        self.assertRegex(
            self.lower,
            r"never auto-commit untracked files",
        )

    def test_skill_report_surfaces_preserved_untracked_paths(self):
        self.assertRegex(
            self.lower,
            r"untracked.*popped from stash",
        )


if __name__ == "__main__":
    unittest.main()
