"""Picker copy for /pr and /ship must not claim a single I'm-done command.

Issue #111: skill `description` fields are what harnesses show next to the
slash commands. Uniqueness claims ("the single", "the standard") contradict
the README pairing where /pr opens a PR and stops, and /ship merges and
cleans up.
"""

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PR_SKILL = REPO_ROOT / "skills" / "pr" / "SKILL.md"
SHIP_SKILL = REPO_ROOT / "skills" / "ship" / "SKILL.md"

UNIQUENESS_CLAIMS = (
    "the single",
    "the standard",
)


def frontmatter_and_body(path: Path) -> tuple[str, str]:
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not match:
        raise AssertionError(f"{path}: no frontmatter block found")
    return match.group(1), match.group(2)


def description_line(frontmatter: str) -> str:
    for line in frontmatter.splitlines():
        if line.startswith("description:"):
            return line[len("description:") :].strip()
    raise AssertionError("frontmatter has no description: line")


class PrShipImDoneCopyTest(unittest.TestCase):
    def setUp(self):
        self.pr_fm, self.pr_body = frontmatter_and_body(PR_SKILL)
        self.ship_fm, self.ship_body = frontmatter_and_body(SHIP_SKILL)
        self.pr_desc = description_line(self.pr_fm)
        self.ship_desc = description_line(self.ship_fm)

    def test_descriptions_drop_uniqueness_claims(self):
        for label, desc in (("pr", self.pr_desc), ("ship", self.ship_desc)):
            lower = desc.lower()
            for claim in UNIQUENESS_CLAIMS:
                with self.subTest(skill=label, claim=claim):
                    self.assertNotIn(
                        claim,
                        lower,
                        f"{label} description must not claim uniqueness "
                        f"with {claim!r}; both finish commands share the "
                        "I'm-done metaphor",
                    )

    def test_pr_description_says_it_opens_a_pr_and_stops(self):
        lower = self.pr_desc.lower()
        self.assertRegex(
            lower,
            r"pull request|open(s)? a pr|\bpr\b",
            "pr description must say it opens a PR",
        )
        # Distinguish from /ship: stop short of merge/cleanup language as the
        # primary outcome, while still naming what /pr does.
        self.assertNotRegex(
            lower,
            r"\bmerge\b|\bdeletes? (the )?branch\b",
            "pr description must not claim merge/cleanup; that is /ship",
        )

    def test_ship_description_says_it_merges_and_cleans_up(self):
        lower = self.ship_desc.lower()
        self.assertRegex(
            lower,
            r"\bmerge\b",
            "ship description must say it merges",
        )
        self.assertRegex(
            lower,
            r"delete(s)? (the )?branch|clean(s)? up|sync.*(default )?branch",
            "ship description must say it cleans up after merge",
        )

    def test_pr_body_opener_does_not_claim_single_im_done_command(self):
        # First non-empty prose line after the title is the picker-adjacent
        # body copy called out in #111.
        lines = [
            line.strip()
            for line in self.pr_body.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertTrue(lines, "pr skill body has no prose after the title")
        opener = lines[0].lower()
        self.assertNotIn(
            "single command",
            opener,
            "pr body opener must not brand /pr as the single I'm-done command",
        )


if __name__ == "__main__":
    unittest.main()
