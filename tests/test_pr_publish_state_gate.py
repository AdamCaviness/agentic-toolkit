import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PR_SKILL = REPO_ROOT / "skills" / "pr" / "SKILL.md"


class PrPublishStateGateTest(unittest.TestCase):
    def setUp(self):
        self.text = PR_SKILL.read_text()
        self.lower = self.text.lower()

    def test_pr_skill_inventories_working_tree_before_publishing(self):
        self.assertIn("git status --porcelain", self.text)
        self.assertIn("git ls-files --others --exclude-standard", self.text)
        for state in ["staged", "unstaged", "untracked"]:
            with self.subTest(state=state):
                self.assertIn(state, self.lower)

    def test_pr_skill_commits_implementation_work_before_push(self):
        self.assertRegex(self.lower, r"commit.*implementation")
        self.assertIn("auto-format and lint fixes", self.lower)

    def test_pr_skill_verifies_ahead_of_base_before_push(self):
        self.assertIn('git rev-list --count "$BASE_REF..HEAD"', self.text)

    def test_pr_skill_inventories_committed_paths_before_push(self):
        self.assertIn('git diff --name-status "$BASE_REF"...HEAD', self.text)

    def test_pr_skill_screens_high_risk_paths_before_push(self):
        # The pattern set itself is pinned across every screening skill by
        # tests/test_high_risk_path_screen.py. This asserts only that the pr
        # skill screens at all, and that the screen still covers the file
        # shapes this test was written for.
        self.assertIn("high-risk", self.lower)
        for pattern in ["env", "pem", "credential"]:
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, self.lower)

    def test_pr_skill_stops_when_nothing_to_publish(self):
        self.assertRegex(self.lower, r"nothing to publish|no commits.*to push")


if __name__ == "__main__":
    unittest.main()
