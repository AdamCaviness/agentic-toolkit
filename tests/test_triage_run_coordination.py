"""Create-mode agents submit evidence; one orchestrator files the run budget."""

import unittest
from pathlib import Path

from triage_shared.skills import SKILLS

ROOT = Path(__file__).resolve().parents[1]


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


class TriageRunCoordinationTest(unittest.TestCase):
    def test_clusters_return_complete_candidates_without_creating_tickets(self):
        for name in SKILLS:
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            create = section(text, "**Create mode**", "**Refine mode**")
            with self.subTest(skill=name):
                self.assertIn("Do NOT create tickets", create)
                self.assertIn("candidates-{CLUSTER_SLUG}.json", create)
                for field in (
                    "candidate_id",
                    "title",
                    "body",
                    "labels",
                    "severity",
                    "root_cause",
                    "trigger",
                    "effect",
                    "affected_paths",
                    "evidence",
                ):
                    self.assertIn(f'"{field}"', create)
                self.assertIn("all validated candidates", create)
                self.assertIn("empty array", create)
                self.assertNotIn("maximum 3 new tickets", create)
                self.assertNotIn("over-cap-", text)
                self.assertNotRegex(create, r"Create a new ticket|file the strongest 3")

    def test_orchestrator_deduplicates_before_ranking_and_filing(self):
        for name, data in SKILLS.items():
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            with self.subTest(skill=name):
                step = section(text, "## Step 3.7:", "## Step 4:")
                for slug in data["cluster_slugs"]:
                    self.assertIn(f"candidates-{slug}.json", step)
                self.assertIn("missing or malformed", step)
                self.assertIn("root cause", step)
                self.assertIn("different titles", step)
                self.assertIn("not-planned", step)
                self.assertLess(step.index("Deduplicate"), step.index("Rank"))
                self.assertLess(step.index("Rank"), step.index("File sequentially"))
                self.assertIn("3 new tickets for the whole run", step)
                self.assertIn("Refresh", step)
                self.assertIn("ambiguous", step)
                self.assertIn("failed refresh", step)
                self.assertIn("run-decisions.json", step)
                self.assertIn("file all", step)
                self.assertIn("skip", step)
                self.assertIn("Wait for the operator", step)
                self.assertIn("Do not delete the cache", step)
                self.assertNotIn(
                    "skip to Step 4", section(text, "## Step 3.5:", "## Step 3.7:")
                )

    def test_pending_run_resumes_without_destroying_candidates(self):
        for name in SKILLS:
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            with self.subTest(skill=name):
                stale = section(
                    text, "### Destroy stale cache", "### Timestamp contract"
                )
                self.assertIn("pending", stale)
                self.assertIn("resume step 3.7", stale.lower())
                self.assertIn("do not remove", stale)
                self.assertIn(
                    "stable candidate IDs", section(text, "## Step 3.7:", "## Step 4:")
                )

    def test_new_mode_cannot_bypass_pending_create_disposition(self):
        for name in SKILLS:
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            with self.subTest(skill=name):
                stale = section(
                    text, "### Destroy stale cache", "### Timestamp contract"
                )
                self.assertIn("stored run mode", stale)
                self.assertIn("requested mode differs", stale)
                self.assertIn("do not dispatch refine", stale)
                self.assertIn("missing or invalid mode metadata", stale)
                filing = section(text, "## Step 3.7:", "## Step 4:")
                self.assertIn('`mode: "create"`', filing)
                cleanup = text.split("## Step 4:", 1)[1]
                self.assertIn("regardless of the requested mode", cleanup)
                self.assertIn("unsettled candidates or unresolved creations", cleanup)
                self.assertLess(
                    cleanup.index("unsettled candidates"),
                    cleanup.index("Delete the cache"),
                )

    def test_create_is_journaled_before_request_and_reconciled_before_budget(self):
        for name in SKILLS:
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            with self.subTest(skill=name):
                filing = section(text, "## Step 3.7:", "## Step 4:")
                self.assertIn("pre-request ticket IDs", filing)
                self.assertIn("in-flight", filing)
                self.assertIn("count exactly once", filing)
                self.assertIn("never reset", filing)
                self.assertLess(
                    filing.index("Reconcile in-flight"),
                    filing.index("File sequentially"),
                )
                create = filing.split("File sequentially", 1)[1]
                self.assertLess(
                    create.index("persist an in-flight"),
                    create.index("Send the create request"),
                )
                self.assertIn("cannot uniquely identify", filing)
                self.assertIn("stop without spending another slot", filing)

    def test_refine_skips_filing_and_preserves_close_guard(self):
        for name in SKILLS:
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            with self.subTest(skill=name):
                self.assertIn(
                    "**Create mode only.** In refine mode, skip this step.", text
                )
                self.assertIn("**create ZERO new tickets**", text)
                self.assertIn("fetch its current state", text)
                self.assertIn("Do NOT create new tickets", text)

    def test_bug_ledger_does_not_require_unfiled_ticket_ids(self):
        text = (ROOT / "skills" / "triage-bugs" / "SKILL.md").read_text()
        ledger = section(
            text, "## Rejection Ledger", "The rejection list is not filler."
        )
        self.assertIn("candidate_id", ledger)
        self.assertIn("In refine mode", ledger)
        self.assertIn(
            "Candidates",
            section(text, "### Print Unified Summary", "### Cross-Cluster Notes"),
        )


if __name__ == "__main__":
    unittest.main()
