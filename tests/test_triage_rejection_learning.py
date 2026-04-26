"""Rejection-learning contract for the triage skills.

When the operator closes a ticket as not-planned (GitHub `stateReason`,
Jira `resolution`, or the analogous "won't do" marker on other systems),
the triage skills must cache the rejection reasoning and surface it to
sub-agents during dedup so a refile under a slightly different title gets
caught. This test pins the contract surface in two places:

1. AGENTS.md documents the deployment context that grounds rejection
   decisions for this repo.

2. Each triage skill (`triage-architecture`, `triage-bugs`,
   `triage-product`) instructs the orchestrator to fetch close-state
   metadata plus closing comments for not-planned tickets, and instructs
   sub-agents to use that reasoning during dedup, not just title matches.
"""

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS = REPO_ROOT / "AGENTS.md"


TRIAGE_SKILLS = [
    "triage-architecture",
    "triage-bugs",
    "triage-product",
]


AGENTS_REQUIRED_PHRASES = [
    "deployment context",
    "personal-machine tooling",
    "rejection-learning",
    "not-planned",
]


# Phrases that pin the closed-fetch contract: orchestrator must capture
# close-state metadata and the closing comment for rejected tickets.
SKILL_FETCH_PHRASES = [
    "rejection reasoning",
    "stateReason",
    "not-planned",
    "closing comment",
]


# Phrases that pin the dedup-check contract: sub-agents must read
# rejection reasoning, not just title-match the closed cache. Each phrase
# is load-bearing in a *different* location so a half-revert in any one
# location is detected:
# - "direct title-level duplicate" appears only in the Dedup Check step.
# - "do not just dedup by title" appears only in the Cached Tickets blurb.
# - "threat model" appears in both, plus AGENTS.md.
# - "not_planned" appears in the Step 1 fetch and the Dedup Check step.
SKILL_DEDUP_PHRASES = [
    "not_planned",
    "threat model",
    "do not just dedup by title",
    "direct title-level duplicate",
]


class TriageRejectionLearningTest(unittest.TestCase):
    def skill_text(self, skill_name):
        return (SKILLS_DIR / skill_name / "SKILL.md").read_text()

    def test_agents_md_documents_deployment_context(self):
        text = AGENTS.read_text().lower()
        for phrase in AGENTS_REQUIRED_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(
                    phrase.lower(),
                    text,
                    f"AGENTS.md must include {phrase!r} so triage runs in "
                    "this repo can ground their threat-model decisions",
                )

    def test_triage_skills_fetch_close_reason_and_reasoning(self):
        for skill_name in TRIAGE_SKILLS:
            text = self.skill_text(skill_name).lower()
            for phrase in SKILL_FETCH_PHRASES:
                with self.subTest(skill=skill_name, phrase=phrase):
                    self.assertIn(
                        phrase.lower(),
                        text,
                        f"{skill_name}: closed-ticket fetch must preserve "
                        f"{phrase!r} so sub-agents can learn from prior "
                        "rejections",
                    )

    def test_triage_dedup_uses_rejection_reasoning_not_just_titles(self):
        for skill_name in TRIAGE_SKILLS:
            text = self.skill_text(skill_name).lower()
            for phrase in SKILL_DEDUP_PHRASES:
                with self.subTest(skill=skill_name, phrase=phrase):
                    self.assertIn(
                        phrase.lower(),
                        text,
                        f"{skill_name}: dedup check must include {phrase!r} "
                        "so a refile under a different title still gets "
                        "caught when its premise was already rejected",
                    )


if __name__ == "__main__":
    unittest.main()
