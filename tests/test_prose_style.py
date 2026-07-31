import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

# AGENTS.md requires commas, not em-dashes or hyphens, for punctuation. The rule
# existed with nothing enforcing it, which is how an em-dash reached a
# distributed skill. Scoped to the surfaces the rule governs: the public skills,
# the shared triage source they are generated from, the contributor docs, and
# these tests. docs/superpowers/ is excluded on purpose; those plans and specs
# are historical design records, not living prose.
CHECKED_TREES = ["skills", "tests", "triage_shared"]
CHECKED_FILES = ["AGENTS.md", "README.md"]

# Written as escapes so this validator does not match its own source.
DASHES = {"\u2014": "em-dash", "\u2013": "en-dash"}


def checked_paths():
    for tree in CHECKED_TREES:
        for path in sorted((REPO_ROOT / tree).rglob("*")):
            if path.is_file() and path.suffix in {".md", ".py"}:
                yield path
    for name in CHECKED_FILES:
        yield REPO_ROOT / name


class ProseStyleTest(unittest.TestCase):
    def test_no_em_or_en_dashes_in_living_prose(self):
        violations = []
        for path in checked_paths():
            rel = path.relative_to(REPO_ROOT)
            for line_number, line in enumerate(
                path.read_text().splitlines(), start=1
            ):
                for char, name in DASHES.items():
                    if char in line:
                        violations.append(f"{rel}:{line_number} ({name})")
        self.assertEqual(
            violations,
            [],
            "AGENTS.md requires commas for punctuation, found: "
            + ", ".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
