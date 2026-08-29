"""Terminal summaries must name the next command in the advertised loop.

Issue #114: /create-ticket, /next-ticket, /pr, /ship, and /apply-review form a
loop in the README, but the implement and empty-state skills stop without
naming the follow-on. Keep the never-auto-push rule; add the handoff.

Issue #122: /code-review is in that same loop after implementation and before
/pr or /ship, and must close with the same publish handoff rather than
stopping after fixes.
"""

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS = REPO_ROOT / "skills"


def skill_text(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text()


def step_block(text: str, header: str) -> str:
    match = re.search(
        rf"(^{re.escape(header)}.*?)(?=^## )",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"Could not find block for {header}")
    return match.group(1)


class LoopNextCommandHandoffTest(unittest.TestCase):
    def test_next_ticket_empty_backlog_names_create_ticket(self):
        block = step_block(skill_text("next-ticket"), "## Step 2: Fetch Tickets")
        self.assertIn("zero actionable tickets", block.lower())
        self.assertIn("/create-ticket", block)

    def test_next_ticket_done_summary_names_pr_and_ship(self):
        block = step_block(skill_text("next-ticket"), "## Step 10: Wait for Review")
        self.assertIn("/pr", block)
        self.assertIn("/ship", block)

    def test_next_ticket_done_summary_says_review_locally_first(self):
        block = step_block(skill_text("next-ticket"), "## Step 10: Wait for Review")
        lower = block.lower()
        self.assertRegex(
            lower,
            r"review locally first|the user reviews first|do not push",
        )

    def test_next_ticket_still_forbids_auto_push(self):
        text = skill_text("next-ticket")
        self.assertIn("Never push or create PRs.", text)
        step_10 = step_block(text, "## Step 10: Wait for Review")
        self.assertNotRegex(
            step_10.lower(),
            r"run /pr now|then run /pr|proceed to /pr",
            "handoff names /pr; it must not collapse next-ticket into publishing",
        )

    def test_create_ticket_filed_summary_names_next_ticket(self):
        block = step_block(skill_text("create-ticket"), "## Step 8: File")
        self.assertIn("/next-ticket", block)

    def test_update_deps_summary_names_pr_or_ship(self):
        block = step_block(
            skill_text("update-deps"), "## Step 9: Cleanup and Summary"
        )
        self.assertTrue(
            "/pr" in block and "/ship" in block,
            "update-deps closing summary must name /pr and /ship",
        )
        self.assertIn("Never push, create PRs, or merge.", block)

    def test_update_deps_publish_handoff_follows_either_headline(self):
        block = step_block(
            skill_text("update-deps"), "## Step 9: Cleanup and Summary"
        )
        bullets = block.split("Final summary template:", 1)[0]
        self.assertIn("/pr", bullets)
        self.assertIn("/ship", bullets)
        self.assertRegex(
            bullets.lower(),
            r"after whichever headline|always print",
            "success-path close must instruct the publish line after either headline, "
            "not only under the WARNING example in the template",
        )

    def test_get_it_right_playbook_names_pr(self):
        text = skill_text("get-it-right")
        match = re.search(
            r"(^### 6\. Output Testing Playbook.*?)(?=^## )",
            text,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match, "Could not find get-it-right playbook section")
        block = match.group(1)
        self.assertIn("/pr", block)
        self.assertRegex(
            block.lower(),
            r"don't commit|do not commit|review",
        )

    def test_apply_review_summary_names_ship(self):
        block = step_block(skill_text("apply-review"), "## Step 10: Summary")
        self.assertIn("/ship", block)

    def test_code_review_wrap_up_names_pr_and_ship(self):
        block = step_block(skill_text("code-review"), "## How to Request")
        self.assertIn("/pr", block)
        self.assertIn("/ship", block)
        self.assertIn("Review locally first", block)

    def test_code_review_wrap_up_is_closing_script_not_second_review(self):
        block = step_block(skill_text("code-review"), "## How to Request")
        lower = block.lower()
        self.assertIn("wrap up", lower)
        self.assertRegex(
            lower,
            r"not a second review|do not dispatch the reviewer again|end of the skill",
        )

    def test_code_review_wrap_up_does_not_auto_publish(self):
        block = step_block(skill_text("code-review"), "## How to Request")
        lower = block.lower()
        self.assertRegex(
            lower,
            r"do not push|never push",
        )
        self.assertNotRegex(
            lower,
            r"run /pr now|then run /pr|proceed to /pr",
            "handoff names /pr; it must not collapse code-review into publishing",
        )


if __name__ == "__main__":
    unittest.main()
