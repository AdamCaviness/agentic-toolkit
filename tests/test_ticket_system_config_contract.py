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


TICKET_STATE_SOURCES = [
    REPO_ROOT / "skills" / "next-ticket" / "SKILL.md",
    REPO_ROOT / "skills" / "pr" / "SKILL.md",
    REPO_ROOT / "skills" / "ship" / "SKILL.md",
    REPO_ROOT / "skills" / "create-ticket" / "SKILL.md",
    REPO_ROOT / "triage_shared" / "template.md",
    REPO_ROOT / "skills" / "triage-architecture" / "SKILL.md",
    REPO_ROOT / "skills" / "triage-bugs" / "SKILL.md",
    REPO_ROOT / "skills" / "triage-product" / "SKILL.md",
]

STATE_HEADING = "## Ticket State"


class TicketStateSectionTest(unittest.TestCase):
    """Every skill that moves a ticket carries one Ticket State section verbatim.

    A ticket's state is kept current by four skills at four moments: claimed
    (next-ticket), PR open (pr), merged (ship), and filed (create-ticket and
    the triage skills). They share one cache shape, one discovery rule that
    treats workflow labels as first-class, and one failure-caching rule, so a
    repository behaves the same whichever skill touches the ticket.
    """

    def sections(self):
        return {
            path.relative_to(REPO_ROOT): section(path.read_text(), STATE_HEADING)
            for path in TICKET_STATE_SOURCES
        }

    def test_section_is_identical_everywhere(self):
        sections = self.sections()
        self.assertEqual(len(set(sections.values())), 1, list(sections))

    def test_section_names_every_state_and_both_mechanisms(self):
        body = next(iter(self.sections().values()))
        for state in ("`in_progress`", "`in_review`", "`done`", "`filed`"):
            self.assertIn(state, body)
        self.assertIn("workflow labels", body)
        self.assertIn('"project"', body)
        self.assertIn('"labels"', body)
        self.assertIn("python3 gh_issues.py transition", body)

    def test_failure_classes_cache_only_what_is_structural(self):
        body = next(iter(self.sections().values()))
        self.assertIn(SENTINEL, body)
        self.assertRegex(body, r"skips it without discovering, applying, or printing anything")
        self.assertRegex(body, r"plain GitHub Issues with no project board")
        transient = re.search(r"\*\*Transient or declined\*\*[^\n]*", body).group(0)
        self.assertIn("cache nothing", transient)
        self.assertIn("permission denial", transient)
        stale = re.search(r"\*\*Stale\*\*[^\n]*", body).group(0)
        self.assertIn("rediscovers", stale)

    def test_each_skill_applies_its_own_state_and_never_blocks(self):
        expectations = {
            "skills/next-ticket/SKILL.md": ("## Step 4.6", "`in_progress`"),
            "skills/pr/SKILL.md": ("Apply the `in_review` state", "`in_review`"),
            "skills/ship/SKILL.md": ("Apply the `done` state", "`done`"),
            "skills/create-ticket/SKILL.md": ("apply the `filed` state", "`filed`"),
            "triage_shared/template.md": ("apply the `filed` state", "`filed`"),
        }
        for rel, (marker, state) in expectations.items():
            with self.subTest(path=rel):
                text = (REPO_ROOT / rel).read_text()
                self.assertIn(marker, text)
                self.assertIn(state, text)

    def test_next_ticket_skips_a_cached_unsupported_state_silently(self):
        step = section(NEXT_TICKET.read_text(), "## Step 4.6: Transition to In Progress")
        self.assertIn(SENTINEL, step)
        self.assertRegex(step, r"skip this entire step without discovering, applying, or printing")

    def test_schema_documents_the_sentinel(self):
        text = NEXT_TICKET.read_text()
        schema = paragraph_starting(text, "The `states` values are opaque")
        self.assertIn(SENTINEL, schema)


class PortablePolicyContractTest(unittest.TestCase):
    """A fresh cloud run has no temp cache and no operator to answer.

    The committed `.agents/ticket-policy.json` carries the saved choices inside
    the repository, ranks between the `ticketSystem:` override and the cache,
    and the `unattended` argument makes every skill that would ask a question
    use saved values or this run's judgment instead of waiting.
    """

    def test_committed_policy_sits_between_the_override_and_the_cache(self):
        for path in DETECTING_SOURCES:
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                text = path.read_text()
                override = text.index("**Project override (always wins)**")
                policy = text.index("**Committed policy**")
                cache = text.index("**Cached config**")
                self.assertLess(override, policy)
                self.assertLess(policy, cache)
                self.assertIn("python3 ticket_policy.py read", text)

    def test_unattended_runs_never_ask_during_detection(self):
        for path in DETECTING_SOURCES:
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                text = path.read_text()
                self.assertIn("In an unattended run (see Ticket State), skip the confirmation", text)
                self.assertIn("In an unattended run, stop instead and say the project should declare", text)

    def test_ticket_state_section_covers_saving_and_unattended_runs(self):
        for path in TICKET_STATE_SOURCES:
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                body = section(path.read_text(), STATE_HEADING)
                self.assertIn("committed policy (`.agents/ticket-policy.json`) first", body)
                self.assertIn("python3 ticket_policy.py export", body)
                self.assertIn("**Unattended runs.**", body)
                self.assertIn("has no saved value; skipping (unattended)", body)

    def test_correction_paragraph_covers_a_system_that_came_from_the_policy(self):
        for path in DETECTING_SOURCES:
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                block = paragraph_starting(path.read_text(), "**Correcting the ticket system.**")
                self.assertIn("(committed policy)", block)

    def test_old_github_state_values_are_rediscovered_once(self):
        for path in TICKET_STATE_SOURCES:
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                body = section(path.read_text(), STATE_HEADING)
                self.assertIn('{"version": 2, "project"', body)
                self.assertIn('for GitHub the sentinel also carries `"version": 2`', body)
                self.assertIn("rediscover it once with the old value as the starting proposal", body)
                self.assertIn("`legacy_states`", body)
        for path in (NEXT_TICKET, PR):
            with self.subTest(call_site=path.name):
                self.assertIn('on GitHub only one carrying `"version": 2`', path.read_text())

    def test_ship_updates_the_done_state_after_cleanup(self):
        text = (REPO_ROOT / "skills" / "ship" / "SKILL.md").read_text()
        cleanup = text.index("10. **Clean up**")
        update = text.index("11. **Update ticket state**")
        report = text.index("12. **Report**")
        self.assertLess(cleanup, update)
        self.assertLess(update, report)
        self.assertIn("note the ticket ID in the branch name", text)
        self.assertNotIn("Once the merged state is confirmed, apply the `done` state", text)

    def test_next_ticket_documents_the_unattended_argument(self):
        text = NEXT_TICKET.read_text()
        self.assertRegex(text, r"\| `unattended` \| No \|")
        self.assertIn("an unattended run stops instead", text)
        self.assertIn("use your recommended choices (bugs first in any group) for this run only", text)

    def test_triage_skills_accept_unattended_and_defer_instead_of_waiting(self):
        for path in TICKET_STATE_SOURCES[4:]:
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                text = path.read_text()
                self.assertIn("[unattended]", text)
                self.assertIn("**In an unattended run, do not ask.**", text)
                self.assertIn("deferred in an unattended run", text)
                # The original wait stays for attended runs.
                self.assertIn("**Wait for the operator before cleanup.", text)


if __name__ == "__main__":
    unittest.main()
