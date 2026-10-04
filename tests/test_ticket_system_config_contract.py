"""The ticket-system cache in next-ticket-config.json is correctable and honest.

Every skill that detects the ticket system shares one cache. A wrong cached
answer used to stick forever because the cache always won, and the documented
`ticketSystem:` override was never consulted once a cache entry existed.
create-ticket reached a missing or logged-out ticket CLI only after research,
drafting, and approval. And a transition the project structurally cannot make
(plain GitHub Issues has no in-progress state) was rediscovered and re-warned
on every run because only successes were cached.
"""

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

DETECTING_SOURCES = [
    REPO_ROOT / "skills" / "next-ticket" / "SKILL.md",
    REPO_ROOT / "skills" / "create-ticket" / "SKILL.md",
    REPO_ROOT / "triage_shared" / "template.md",
    REPO_ROOT / "skills" / "triage-architecture" / "SKILL.md",
    REPO_ROOT / "skills" / "triage-bugs" / "SKILL.md",
    REPO_ROOT / "skills" / "triage-product" / "SKILL.md",
]

TRACKER_READERS = [
    REPO_ROOT / "skills" / "pr" / "SKILL.md",
    REPO_ROOT / "skills" / "get-it-right" / "SKILL.md",
]

CREATE_TICKET = REPO_ROOT / "skills" / "create-ticket" / "SKILL.md"
NEXT_TICKET = REPO_ROOT / "skills" / "next-ticket" / "SKILL.md"
PR = REPO_ROOT / "skills" / "pr" / "SKILL.md"

SENTINEL = '{"unsupported": "<reason>"}'


def paragraph_starting(text, marker):
    start = text.index(marker)
    end = text.find("\n\n", start)
    return text[start:] if end == -1 else text[start:end]


def section(text, heading):
    start = text.index(heading)
    nxt = text.find("\n## ", start + len(heading))
    return text[start:] if nxt == -1 else text[start:nxt]


class TicketSystemDetectionTest(unittest.TestCase):
    def test_project_override_is_checked_before_cache(self):
        for path in DETECTING_SOURCES:
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                text = path.read_text()
                override = text.index("**Project override (always wins)**")
                cache = text.index("**Cached config**")
                self.assertLess(override, cache)
                self.assertNotIn("**Cached config (always wins)**", text)

    def test_correction_block_is_identical_everywhere(self):
        marker = "**Correcting the ticket system.**"
        blocks = {
            path.relative_to(REPO_ROOT): paragraph_starting(path.read_text(), marker)
            for path in DETECTING_SOURCES
        }
        self.assertEqual(len(set(blocks.values())), 1, blocks)
        block = next(iter(blocks.values()))
        self.assertIn("cached for <project root>", block)
        self.assertIn("`__user__`", block)
        self.assertRegex(block, r"[Nn]ever ask the operator to find or edit the cache")

    def test_tracker_readers_honor_the_override(self):
        for path in TRACKER_READERS:
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                text = path.read_text()
                override = text.index("ticketSystem: <name>")
                cache = text.index("next-ticket-config.json", override)
                self.assertLess(override, cache)


class CreateTicketAccessGateTest(unittest.TestCase):
    def setUp(self):
        self.text = CREATE_TICKET.read_text()

    def test_access_is_verified_before_research(self):
        gate = self.text.index("## Step 0b: Verify Ticket-System Access")
        self.assertLess(self.text.index("## Step 0: Detect"), gate)
        self.assertLess(gate, self.text.index("## Step 1: Understand the Idea"))
        body = section(self.text, "## Step 0b: Verify Ticket-System Access")
        self.assertIn("gh auth status", body)
        self.assertRegex(body, r"stop before Step 1")

    def test_dedup_no_longer_skips_on_missing_cli(self):
        dedup = section(self.text, "## Step 4: Dedup Check")
        self.assertNotRegex(dedup, r"CLI is unavailable.*skip dedup")
        self.assertRegex(dedup, r"failed fetch is not an empty backlog")

    def test_failed_filing_keeps_the_approved_draft(self):
        filing = section(self.text, "## Step 8: File")
        self.assertRegex(filing, r"print the approved draft")


class UnsupportedTransitionCacheTest(unittest.TestCase):
    def test_next_ticket_caches_structural_failure_only(self):
        step = section(NEXT_TICKET.read_text(), "## Step 4.6: Transition to In Progress")
        self.assertIn(SENTINEL, step)
        self.assertRegex(step, r"skip this entire step without discovering, applying, or printing")
        self.assertRegex(step, r"plain GitHub Issues with no project board")
        transient = re.search(r"\*\*Transient or declined\*\*[^\n]*", step).group(0)
        self.assertIn("cache nothing", transient)
        self.assertIn("permission denial", transient)

    def test_schema_documents_the_sentinel(self):
        text = NEXT_TICKET.read_text()
        schema = paragraph_starting(text, "A project-root entry without `states`")
        self.assertIn(SENTINEL, schema)

    def test_pr_in_review_uses_the_same_sentinel(self):
        text = PR.read_text()
        self.assertGreaterEqual(text.count(SENTINEL), 2)
        self.assertRegex(text, r"Cache nothing for a missing config file, an API error")


if __name__ == "__main__":
    unittest.main()
