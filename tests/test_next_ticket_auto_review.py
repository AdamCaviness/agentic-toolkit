import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NEXT_TICKET_SKILL = REPO_ROOT / "skills" / "next-ticket" / "SKILL.md"


class NextTicketAutoReviewTest(unittest.TestCase):
    def test_step_9_5_exists_and_references_reviewer_prompt(self):
        text = NEXT_TICKET_SKILL.read_text()
        self.assertIn("Step 9.5", text)
        self.assertIn("skills/code-review/reviewer-prompt.md", text)

    def test_step_9_5_builds_shared_inventory_variables(self):
        text = NEXT_TICKET_SKILL.read_text()
        for var in ["BASE_SHA", "HEAD_SHA", "CHANGED_PATH_INVENTORY", "HIGH_RISK_PATHS"]:
            with self.subTest(var=var):
                self.assertIn(var, text)
        self.assertIn('git merge-base HEAD "origin/$BASE_BRANCH"', text)
        self.assertIn("git ls-files --others --exclude-standard", text)

    def test_step_9_5_lists_reviewer_placeholders(self):
        text = NEXT_TICKET_SKILL.read_text()
        for placeholder in [
            "PLAN_OR_REQUIREMENTS",
            "DESCRIPTION",
            "HAS_UNCOMMITTED",
        ]:
            with self.subTest(placeholder=placeholder):
                self.assertIn(placeholder, text)

    def test_step_10_summary_includes_review_block(self):
        text = NEXT_TICKET_SKILL.read_text()
        self.assertIn("Review: Critical", text)
        self.assertIn("Important", text)
        self.assertIn("Minor", text)
        self.assertIn("Verdict:", text)
        self.assertIn("Top issues:", text)

    def test_step_9_5_documents_failure_mode(self):
        text = NEXT_TICKET_SKILL.read_text()
        self.assertIn("Review: skipped", text)
        lower = text.lower()
        self.assertIn("do not retry", lower)
        self.assertIn("do not block", lower)


if __name__ == "__main__":
    unittest.main()
