import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NEXT_TICKET_SKILL = REPO_ROOT / "skills" / "next-ticket" / "SKILL.md"


class NextTicketCleanTreeGateTest(unittest.TestCase):
    def setUp(self):
        self.text = NEXT_TICKET_SKILL.read_text()
        self.lower = self.text.lower()

    def test_prerequisites_require_clean_working_tree(self):
        prereq = self._section("## Prerequisites", "## ")
        self.assertIn("git status --porcelain", prereq)
        self.assertRegex(
            prereq.lower(),
            r"commit.*(stash|discard)|stash.*(commit|discard)|discard.*(commit|stash)",
        )

    def test_dirty_tree_stop_lists_paths(self):
        prereq = self._section("## Prerequisites", "## ")
        self.assertRegex(prereq.lower(), r"list (the )?paths|print.*(paths|files)")

    def test_gate_runs_before_claim(self):
        claim_idx = self.text.index("## Step 4.5: Claim the Ticket")
        prereq_idx = self.text.index("## Prerequisites")
        self.assertLess(prereq_idx, claim_idx)
        # The only porcelain check before claim must be the gate, not the
        # post-commit HAS_UNCOMMITTED inventory used by Step 9.5.
        before_claim = self.text[:claim_idx]
        self.assertIn("git status --porcelain", before_claim)
        self.assertNotIn("HAS_UNCOMMITTED", before_claim)

    def test_rules_forbid_treating_dirty_tree_as_ticket_work(self):
        rules = self._section("## Rules", None)
        self.assertRegex(
            rules.lower(),
            r"dirty|uncommitted|clean working tree",
        )
        self.assertRegex(
            rules.lower(),
            r"do not treat|not.*in-scope|not.*ticket work|stop",
        )

    def _section(self, heading: str, next_heading_prefix: str | None) -> str:
        start = self.text.index(heading)
        if next_heading_prefix is None:
            return self.text[start:]
        rest = self.text[start + len(heading) :]
        # Find the next markdown heading at the same level that starts the
        # following section (any "## " after this one).
        nxt = rest.find("\n## ")
        if nxt == -1:
            return self.text[start:]
        return self.text[start : start + len(heading) + nxt]


if __name__ == "__main__":
    unittest.main()
