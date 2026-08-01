import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "get-it-right" / "SKILL.md"

# The footprint is the guard's denominator. A path missing from it is scored as
# net-new against the plan, which inflates the net-new count and trips the
# guard on work the branch already contains.
#
# tests/test_get_it_right_footprint_guard.py asserts the skill *names* the
# right commands. This runs them. The distinction matters: `git diff HEAD` and
# a bare `git diff` differ only by the word HEAD, and only the first includes
# staged paths, so a one-word edit could silently drop every staged file while
# the prose still looked correct.


def footprint_script():
    """The union block from the skill, extracted rather than transcribed.

    Copying the commands into this file would let the two drift apart, which
    is the failure this test exists to catch.
    """
    lines = SKILL.read_text().splitlines()
    start = next(
        i for i, line in enumerate(lines) if line.strip() == "{"
        and "git diff --name-only" in lines[i + 1]
    )
    end = next(i for i in range(start, len(lines)) if lines[i].startswith("} | sort -u"))
    return "\n".join(lines[start : end + 1])


def run(cwd, *args):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)


class GetItRightFootprintBehaviorTest(unittest.TestCase):
    def test_footprint_union_covers_every_uncommitted_state(self):
        script = footprint_script()
        self.assertIn("git ls-files --others", script, "extracted the wrong block")

        with tempfile.TemporaryDirectory() as tmp:
            run(tmp, "git", "init", "-q", "-b", "main", ".")
            run(tmp, "git", "config", "user.email", "test@example.com")
            run(tmp, "git", "config", "user.name", "test")
            Path(tmp, "base.txt").write_text("base\n")
            run(tmp, "git", "add", "-A")
            run(tmp, "git", "commit", "-qm", "base")

            run(tmp, "git", "checkout", "-qb", "feature")
            Path(tmp, "committed.txt").write_text("c\n")
            run(tmp, "git", "add", "-A")
            run(tmp, "git", "commit", "-qm", "on branch")

            Path(tmp, "staged.txt").write_text("s\n")
            run(tmp, "git", "add", "staged.txt")
            Path(tmp, "base.txt").write_text("base\nunstaged\n")
            Path(tmp, "untracked.txt").write_text("n\n")

            result = subprocess.run(
                ["bash", "-c", f'BASE_REF=main\n{script}'],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode, 0, f"footprint block failed: {result.stderr}"
            )
            footprint = set(result.stdout.split())

        for path, state in [
            ("committed.txt", "committed on the branch"),
            ("staged.txt", "staged but not committed"),
            ("base.txt", "modified but not staged"),
            ("untracked.txt", "untracked"),
        ]:
            with self.subTest(state=state):
                self.assertIn(
                    path,
                    footprint,
                    f"the original footprint omits work that is {state}, so the "
                    "guard would score it as net-new and trip on the branch's "
                    "own contents",
                )


if __name__ == "__main__":
    unittest.main()
