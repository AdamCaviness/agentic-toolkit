import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_REVIEW_SKILL = REPO_ROOT / "skills" / "code-review" / "SKILL.md"
README = REPO_ROOT / "README.md"


class CodeReviewInventoryTest(unittest.TestCase):
    def test_reviewer_prompt_defines_complete_changed_path_inventory(self):
        text = CODE_REVIEW_SKILL.read_text().lower()

        self.assertIn("{changed_path_inventory}", text)
        self.assertIn("changed path inventory", text)
        self.assertIn("git diff --name-status {base_sha}..{head_sha}", text)
        self.assertIn("git diff --cached --name-status", text)
        self.assertIn("git diff --name-status", text)
        self.assertIn("git ls-files --others --exclude-standard", text)

        for path_state in ["committed", "staged", "unstaged", "untracked"]:
            with self.subTest(path_state=path_state):
                self.assertIn(path_state, text)

        self.assertIn("account for every path", text)
        self.assertIn("read each untracked file", text)
        self.assertIn("high-risk", text)

    def test_readme_describes_untracked_files_in_review_scope(self):
        text = README.read_text().lower()

        self.assertIn("staged, unstaged, or untracked changes", text)


if __name__ == "__main__":
    unittest.main()
