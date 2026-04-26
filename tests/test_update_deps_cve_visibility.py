import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "skills" / "update-deps" / "SKILL.md"


class UpdateDepsCveVisibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL_PATH.read_text()
        cls.lower = cls.text.lower()

    def _step_block(self, header):
        """Return text from a `## Step N:` header to the next top-level header."""
        match = re.search(rf"(^{re.escape(header)}.*?)(?=^## )", self.text, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, f"Could not find block for {header}")
        return match.group(1)

    def _subsection_block(self, header):
        """Return text from a `### 7e.` style header to the next `### ` header."""
        match = re.search(rf"(^{re.escape(header)}.*?)(?=^### )", self.text, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, f"Could not find subsection block for {header}")
        return match.group(1)

    def test_step_7e_records_reverted_cve_deps_to_cache(self):
        block = self._subsection_block("### 7e. Iterate until green").lower()
        self.assertIn("reverted-cve-updates.json", block)
        self.assertIn("cve-required", block)
        self.assertIn("cve_id", block)
        self.assertIn("revert_commit", block)

    def test_step_9_summary_has_dedicated_cve_revert_section(self):
        block = self._step_block("## Step 9: Cleanup and Summary")
        lower = block.lower()
        # A label that mentions both "CVE" and "not applied" or "reverted",
        # distinct from the generic "Skipped (manual attention needed)" bucket.
        self.assertIn("cve updates not applied", lower)
        self.assertIn("skipped (manual attention needed)", lower)
        # The CVE-revert section must precede the generic Skipped bucket so
        # reviewers see security regressions first.
        cve_idx = lower.index("cve updates not applied")
        skipped_idx = lower.index("skipped (manual attention needed)")
        self.assertLess(cve_idx, skipped_idx)
        # And precede Safe updates and Major updates inside the rendered
        # template, putting it at the top of the summary body.
        safe_idx = lower.index("safe updates (1 commit)")
        major_idx = lower.index("major updates (2 commits)")
        self.assertLess(cve_idx, safe_idx)
        self.assertLess(cve_idx, major_idx)

    def test_step_9_reads_structured_cache_not_grep(self):
        block = self._step_block("## Step 9: Cleanup and Summary").lower()
        self.assertIn("reverted-cve-updates.json", block)
        # Cache must be read before deletion so the data is still available.
        read_idx = block.index("reverted-cve-updates.json")
        delete_idx = block.index("delete the cache directory")
        self.assertLess(read_idx, delete_idx)

    def test_step_9_headline_is_conditional_not_unconditional(self):
        block = self._step_block("## Step 9: Cleanup and Summary")
        lower = block.lower()
        # Both branches of the headline must be documented.
        self.assertIn("all tests passing. ready for review.", lower)
        self.assertIn("warning:", lower)
        self.assertIn("cve update(s) not applied", lower)
        # The conditional must be explicit. The success line cannot stand
        # on its own as the only documented headline.
        self.assertRegex(
            lower,
            r"if the reverted-cve list is empty.*all tests passing\. ready for review\.",
        )
        self.assertRegex(
            lower,
            r"if the reverted-cve list has one or more entries.*warning:",
        )
        # Guardrail against the success line being printed alongside reverts.
        self.assertIn(
            "never print the success line when any cve was reverted",
            lower,
        )


if __name__ == "__main__":
    unittest.main()
