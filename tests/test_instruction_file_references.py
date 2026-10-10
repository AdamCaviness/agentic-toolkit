"""Shipped skills name project instruction files harness-neutrally.

Claude Code, Cursor, Codex, Gemini, and Copilot each load a different file
(`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursor/rules/`,
`.github/copilot-instructions.md`), and several now read `AGENTS.md`. A skill
that says "check CLAUDE.md for the test command" is wrong on every harness that
does not load that file, and a `ticketSystem:` override placed in
`.cursor/rules/` is never read when the skill lists only three files. A skill
therefore either says "the project instructions" or names the full list.
"""

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

CANONICAL = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".cursor/rules/",
    ".github/copilot-instructions.md",
]

NAMED_FILES = ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]

# compress-markdown quotes CLAUDE.md as an example of a file worth compressing,
# which is its subject matter rather than an instruction about the project.
EXAMPLE_FILES = {REPO_ROOT / "skills" / "compress-markdown" / "SKILL.md"}


def shipped_sources():
    sources = sorted((REPO_ROOT / "skills").rglob("*.md"))
    sources += [REPO_ROOT / "triage_shared" / "template.md", REPO_ROOT / "triage_shared" / "skills.py"]
    return sources


class InstructionFileReferencesTest(unittest.TestCase):
    def test_a_line_naming_an_instruction_file_names_all_of_them(self):
        for path in shipped_sources():
            if path in EXAMPLE_FILES:
                continue
            for number, line in enumerate(path.read_text().splitlines(), start=1):
                if not any(name in line for name in NAMED_FILES):
                    continue
                with self.subTest(path=path.relative_to(REPO_ROOT), line=number):
                    missing = [name for name in CANONICAL if name not in line]
                    self.assertFalse(
                        missing,
                        f"{path.relative_to(REPO_ROOT)}:{number} names an instruction "
                        f"file but not {missing}. Say 'the project instructions' or "
                        "list every harness file.",
                    )

    def test_ticket_system_override_is_not_tied_to_one_harness_file(self):
        for path in shipped_sources():
            for number, line in enumerate(path.read_text().splitlines(), start=1):
                if "`ticketSystem: <name>`" not in line:
                    continue
                with self.subTest(path=path.relative_to(REPO_ROOT), line=number):
                    self.assertIn("instruction files", line)


if __name__ == "__main__":
    unittest.main()
