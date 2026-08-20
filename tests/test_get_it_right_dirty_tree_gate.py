import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "skills" / "get-it-right" / "SKILL.md"


class GetItRightDirtyTreeGateTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL_PATH.read_text()
        self.lower = self.text.lower()

    def test_scope_step_checks_porcelain_before_auto_implement(self):
        scope = self._section("### 1. Identify Scope", "### ")
        auto_impl_idx = self.text.index("### 5. Auto-Implement")
        scope_idx = self.text.index("### 1. Identify Scope")
        self.assertLess(scope_idx, auto_impl_idx)
        self.assertIn("git status --porcelain", scope)

    def test_dirty_tree_lists_paths_and_stops(self):
        scope = self._section("### 1. Identify Scope", "### ").lower()
        self.assertRegex(scope, r"list (the )?paths")
        self.assertRegex(scope, r"\bstop\b")
        self.assertRegex(
            scope,
            r"do not (enter|auto-implement)|not enter step 2|until the (operator|user) (responds|says)",
        )

    def test_uncommitted_paths_are_not_assumed_leftover(self):
        scope = self._section("### 1. Identify Scope", "### ").lower()
        self.assertRegex(
            scope,
            r"do not treat|not leftover|not treat those paths as leftover",
        )
        self.assertNotRegex(
            scope,
            r"uncommitted work this skill may have left from an earlier run",
        )

    def test_gate_offers_leftover_proceed_or_unrelated_stop(self):
        scope = self._section("### 1. Identify Scope", "### ").lower()
        self.assertIn("leftover", scope)
        self.assertRegex(scope, r"proceed")
        self.assertRegex(
            scope,
            r"commit.*(stash|discard)|stash.*(commit|discard)|discard.*(commit|stash)",
        )
        self.assertRegex(scope, r"apply-review|update-deps")

    def test_key_principles_keep_unconfirmed_dirty_tree_out_of_scope(self):
        principles = self._section("## Key Principles", None).lower()
        self.assertRegex(
            principles,
            r"dirty tree|uncommitted",
        )
        self.assertRegex(
            principles,
            r"intended footprint|not in-scope|not leftover until",
        )

    def _section(self, heading: str, next_heading_prefix: str | None) -> str:
        start = self.text.index(heading)
        if next_heading_prefix is None:
            return self.text[start:]
        rest = self.text[start + len(heading) :]
        nxt = rest.find("\n" + next_heading_prefix)
        if nxt == -1:
            return self.text[start:]
        return self.text[start : start + len(heading) + nxt]


if __name__ == "__main__":
    unittest.main()
