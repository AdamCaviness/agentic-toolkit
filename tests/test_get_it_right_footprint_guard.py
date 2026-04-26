import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "skills" / "get-it-right" / "SKILL.md"


class GetItRightFootprintGuardTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL_PATH.read_text()
        self.lower = self.text.lower()

    def _index_of(self, needle, *, start=0):
        idx = self.lower.find(needle.lower(), start)
        self.assertNotEqual(
            idx,
            -1,
            f"expected to find {needle!r} in skills/get-it-right/SKILL.md",
        )
        return idx

    def test_footprint_guard_appears_before_auto_implement_step(self):
        guard_idx = self._index_of("footprint guard")
        auto_impl_idx = self._index_of("### 5. auto-implement")
        self.assertLess(
            guard_idx,
            auto_impl_idx,
            "footprint guard prose must appear before Step 5 (Auto-Implement)",
        )

    def test_guard_compares_planned_footprint_to_original_branch_diff(self):
        # The guard must define what it compares: a planned footprint vs the
        # branch's existing diff against the default branch.
        for phrase in [
            "planned footprint",
            "original footprint",
            'git diff --name-only "$base_branch"...head',
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(
                    phrase,
                    self.lower,
                    f"footprint guard must reference {phrase!r}",
                )

    def test_guard_names_a_stop_and_confirm_condition(self):
        # The guard must name a stop point tied to the original-branch footprint,
        # not just describe the comparison abstractly.
        guard_section = self._extract_guard_section()
        guard_lower = guard_section.lower()
        self.assertTrue(
            "stop" in guard_lower and "confirm" in guard_lower,
            "guard prose must name a stop-and-confirm condition",
        )
        self.assertIn(
            "net-new",
            guard_lower,
            "guard must describe net-new files vs the original footprint",
        )
        # A documented threshold must be present, expressed as prose.
        self.assertTrue(
            re.search(r"\b50\s*%|\bfifty percent\b", guard_lower),
            "guard must publish a concrete threshold in prose",
        )

    def test_guard_appears_in_key_principles(self):
        principles_idx = self._index_of("## key principles")
        principles_section = self.lower[principles_idx:]
        self.assertIn(
            "stay within the branch's footprint",
            principles_section,
            "Key Principles list must include the bounded-footprint principle",
        )
        self.assertIn(
            "footprint guard",
            principles_section,
            "Key Principles must point at the footprint guard step",
        )

    def test_workflow_digraph_includes_footprint_guard_node(self):
        # The workflow diagram at the top must show the new checkpoint between
        # planning and auto-implementation.
        digraph_match = re.search(
            r"```dot.*?```",
            self.text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(
            digraph_match,
            "workflow digraph block must exist in SKILL.md",
        )
        digraph = digraph_match.group(0).lower()
        self.assertIn("footprint guard", digraph)
        self.assertIn(
            '"plan re-architecture" -> "footprint guard"',
            digraph,
            "digraph must wire planning into the footprint guard",
        )
        self.assertIn(
            '"footprint guard" -> "auto-implement (no commit)"',
            digraph,
            "digraph must wire the footprint guard into auto-implementation",
        )

    def _extract_guard_section(self):
        start = self._index_of("### 4.5. footprint guard")
        end = self._index_of("### 5. auto-implement", start=start)
        return self.text[start:end]


if __name__ == "__main__":
    unittest.main()
