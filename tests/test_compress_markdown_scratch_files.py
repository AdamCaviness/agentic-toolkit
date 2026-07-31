import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "compress-markdown" / "SKILL.md"

# The two scratch files the skill writes into the user's own repository next to
# the file being compressed. Both are baselines a later step compares against,
# so compressing one destroys the comparison, and leaving one behind puts a
# stray file in the user's working tree.
SCRATCH_SUFFIXES = [".original.md", ".audited.md"]


class CompressMarkdownScratchFileTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text()

    def test_guard_refuses_the_skills_own_scratch_files(self):
        # Without this the skill compresses its own baseline on a second run.
        guard = self.text.partition("**Guard.**")[2].partition("\n")[0]
        self.assertTrue(guard, "the guard step is missing")
        for suffix in SCRATCH_SUFFIXES:
            with self.subTest(suffix=suffix):
                self.assertIn(
                    f"`{suffix}`",
                    guard,
                    f"the guard must refuse {suffix}, which the skill writes "
                    "itself and a later step reads as a baseline",
                )

    def test_the_audited_baseline_name_is_fixed_not_an_example(self):
        # The guard refuses one exact suffix, so the writing step must not
        # present the name as one option among several.
        step = self.text.partition("**Write the audited file.**")[2].partition("\n")[0]
        self.assertTrue(step, "the audited-file step is missing")
        self.assertIn("`<stem>.audited.md`", step)
        self.assertNotIn(
            "e.g.",
            step,
            "an example name lets a run produce a baseline the guard does not "
            "refuse, which a later run would then compress",
        )

    def test_the_audited_file_is_removed_on_every_exit_path(self):
        # Default mode's fix loop only knows about the backup, so a deep run
        # that gives up would otherwise leave the audited file behind.
        self.assertIn(
            "Remove the audited file on every exit path, including the one "
            "where the fix loop gives up and restores the backup.",
            self.text,
            "the cleanup contract for the audited file is missing",
        )


if __name__ == "__main__":
    unittest.main()
