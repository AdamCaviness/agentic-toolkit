import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "skills" / "update-deps" / "SKILL.md"


class UpdateDepsCveDiscoveryGateTest(unittest.TestCase):
    """#124: missing/failing gh must not look like an empty bot-PR list."""

    @classmethod
    def setUpClass(cls):
        cls.text = SKILL_PATH.read_text()
        cls.lower = cls.text.lower()

    def _step_2(self):
        match = re.search(
            r"(^## Step 2: Check Open PRs for Automated CVE Patches.*?)(?=^## )",
            self.text,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match, "Could not find Step 2 block")
        return match.group(1)

    def test_step_2_does_not_swallow_gh_stderr_on_bot_queries(self):
        block = self._step_2()
        # The fail-open pattern that hid missing/unauthenticated gh.
        self.assertNotRegex(
            block,
            r"gh pr list[^\n]*2>/dev/null",
            "gh pr list must not redirect stderr to /dev/null",
        )

    def test_step_2_bot_query_block_aborts_on_any_failed_query(self):
        block = self._step_2()
        # pipefail alone is not enough: a subshell of `gh; gh; …` exits with
        # the last status, so an early failure can still look like success.
        self.assertRegex(
            block,
            r"set -e|gh pr list[^\n]*&&\s*gh pr list",
            "bot queries must abort on first failure (set -e or &&)",
        )

    def test_step_2_requires_gh_availability_or_auth_before_empty_bot_list(self):
        block = self._step_2().lower()
        self.assertRegex(
            block,
            r"gh auth status|command -v gh|not (installed|authenticated)|missing",
        )
        # Discovery failure must be named distinctly from "no bot PRs".
        self.assertRegex(
            block,
            r"cve[- ]?pr discovery failed|discovery failed|failed to (discover|list|query)",
        )

    def test_step_2_empty_bot_list_only_after_successful_discovery(self):
        block = self._step_2().lower()
        # The empty-list proceed path must not apply when discovery failed.
        self.assertRegex(
            block,
            r"(confirm|explicitly).*(skip|skipping).*(check|discovery)|"
            r"do not continue as if.*(empty|no bot)",
        )
        self.assertIn("if no bot prs are found, proceed normally", block)

    def test_edge_cases_distinguish_discovery_failure_from_no_bot_prs(self):
        edge = re.search(
            r"(^## Edge Cases.*?)(?=^## Rules)",
            self.text,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(edge, "Could not find Edge Cases block")
        lower = edge.group(1).lower()
        self.assertRegex(
            lower,
            r"(gh|github cli).*(missing|not authenticated|fail)|"
            r"discovery fail",
        )


if __name__ == "__main__":
    unittest.main()
