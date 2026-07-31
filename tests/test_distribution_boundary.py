import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"

# AGENTS.md alone, because it is the only filename that means two things at
# once. This repository uses it as the contributor guide, and it is also a
# standard name for a project's own convention file. CONTRIBUTING.md and
# README are not listed: a skill telling the agent to read the user's
# CONTRIBUTING.md is asking for exactly the right file.
CONTRIBUTOR_DOCS = ["AGENTS.md"]

# The one legitimate way a shipped skill names AGENTS.md: as one of the target
# project's convention files, listed beside CLAUDE.md. That means the end
# user's own file, which is the intended reading.
TARGET_PROJECT_MARKER = "CLAUDE.md"


def shipped_markdown():
    """Every markdown file distributed inside skills/."""
    return sorted(SKILLS_DIR.rglob("*.md"))


class DistributionBoundaryTest(unittest.TestCase):
    """Skills ship without the repository around them.

    `skills/` is public API. A skill installed as a plugin runs inside someone
    else's project, where a bare `AGENTS.md` resolves to *their* file rather
    than this repository's contributor guide. Citing a contributor doc as the
    source of a shared contract therefore points the reader at unrelated
    third-party text, and for the high-risk path screen that means sourcing a
    security control from a document the skill's own Untrusted Content Boundary
    classifies as untrusted. Shared content is kept in sync by the validators
    in this directory, not by a reference the end user cannot follow.
    """

    def test_shipped_skills_do_not_cite_contributor_docs(self):
        for path in shipped_markdown():
            rel = path.relative_to(REPO_ROOT)
            text = path.read_text()
            for line_number, line in enumerate(text.splitlines(), start=1):
                for doc in CONTRIBUTOR_DOCS:
                    if doc not in line:
                        continue
                    if doc == "AGENTS.md" and TARGET_PROJECT_MARKER in line:
                        # "read CLAUDE.md, AGENTS.md, GEMINI.md for the
                        # project's conventions" means the user's own files.
                        continue
                    self.fail(
                        f"{rel}:{line_number} cites {doc}, which is not "
                        "distributed with the skill. On an end user's machine "
                        f"that name resolves to their own {doc}. State the "
                        "contract in the skill instead, and leave the "
                        "rationale in the contributor doc."
                    )

    def test_shipped_skills_do_not_reference_repository_only_paths(self):
        # A skill cannot reach tests/, triage_shared/, docs/, or scripts/ at
        # runtime; those directories exist in this repository, not in the
        # project the skill is invoked against.
        repo_only = ["tests/", "triage_shared/", "docs/superpowers/", "scripts/"]
        for path in shipped_markdown():
            rel = path.relative_to(REPO_ROOT)
            text = path.read_text()
            for line_number, line in enumerate(text.splitlines(), start=1):
                # An HTML comment is contributor provenance, such as the
                # "GENERATED FROM triage_shared/template.md" marker. It is
                # invisible when rendered and instructs the runtime agent to
                # do nothing.
                if line.lstrip().startswith("<!--"):
                    continue
                for prefix in repo_only:
                    if prefix in line:
                        self.fail(
                            f"{rel}:{line_number} references {prefix}, which "
                            "does not exist in the project a skill runs "
                            "against. Reference paths relative to the skill's "
                            "own directory instead."
                        )


if __name__ == "__main__":
    unittest.main()
