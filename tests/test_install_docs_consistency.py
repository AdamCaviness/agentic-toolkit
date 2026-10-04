"""Install docs name one Cursor audience, one shared skills root, and every OS.

README.md and the per-harness INSTALL.md files are read side by side by people
choosing exactly one install path. A plan name or skills root that differs
between them sends readers to the wrong path or leaves a duplicate root behind.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
CURSOR = REPO_ROOT / ".cursor" / "INSTALL.md"
CODEX = REPO_ROOT / ".codex" / "INSTALL.md"
GEMINI = REPO_ROOT / ".gemini" / "INSTALL.md"

CURSOR_AUDIENCE = "individual plan: Hobby, Pro, Pro+, or Ultra"
SHARED_ROOT = "~/.agents/skills/"
DEPRECATED_CODEX_ROOT = "~/.codex/skills"


def details_block(text: str, summary: str) -> str:
    block = text.split(f"<summary>{summary}</summary>", 1)[1]
    return block.split("</details>", 1)[0]


class TestInstallDocsConsistency(unittest.TestCase):
    def test_cursor_audience_label_is_identical_everywhere(self) -> None:
        readme_cursor = details_block(README.read_text(), "Cursor")
        self.assertIn(CURSOR_AUDIENCE, readme_cursor)
        cursor = CURSOR.read_text()
        table_row = next(
            line for line in cursor.splitlines() if line.startswith("| **Cursor only**")
        )
        self.assertIn(CURSOR_AUDIENCE, table_row)
        self.assertIn(f"## 2. Cursor only ({CURSOR_AUDIENCE})", cursor)
        team_section = cursor.split("## 3.", 1)[1].split("## Why", 1)[0]
        self.assertIn("Hobby, Pro, Pro+, or Ultra", team_section)

    def test_no_doc_installs_into_the_deprecated_codex_root(self) -> None:
        # The deprecated root may be named only as something not to use.
        for path in (README, CURSOR, CODEX, GEMINI):
            for line in path.read_text().splitlines():
                if DEPRECATED_CODEX_ROOT in line:
                    self.assertRegex(
                        line,
                        r"deprecated",
                        f"{path.relative_to(REPO_ROOT)} names {DEPRECATED_CODEX_ROOT} "
                        "without marking it deprecated",
                    )

    def test_shared_root_is_named_for_every_harness_that_reads_it(self) -> None:
        manual = details_block(README.read_text(), "Manual (macOS, Linux, Windows)")
        self.assertIn(f"`{SHARED_ROOT}` | Codex, Cursor, Gemini CLI", manual)
        for path in (CURSOR, CODEX, GEMINI):
            self.assertIn(SHARED_ROOT, path.read_text(), path)

    def test_manual_install_covers_windows(self) -> None:
        manual = details_block(README.read_text(), "Manual (macOS, Linux, Windows)")
        self.assertIn("```powershell", manual)
        self.assertIn("-ItemType Junction", manual)
        self.assertIn("```powershell", CURSOR.read_text())
        self.assertIn("Windows", GEMINI.read_text())
        self.assertIn("PowerShell", CODEX.read_text())


if __name__ == "__main__":
    unittest.main()
