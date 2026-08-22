"""Skill frontmatter must be valid YAML, or Cursor drops the slash command.

An unquoted `description:` value may not contain `: `. YAML treats that as a
nested mapping, the parse fails, and plugin-delivered skills vanish from the
`/` picker. `/pr` and `/ship` hit this after the #111 copy change. The
existing picker-copy tests read the description line with a regex, so they
cannot catch it. This walks every shipped SKILL.md.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"

# One-line `key: value` entries. Block scalars (`>` / `|`) and quoted values
# are YAML-legal ways to carry a colon; an unquoted plain scalar is not.
LINE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.*)$")


def frontmatter(path: Path) -> str:
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        raise AssertionError(f"{path}: no frontmatter block found")
    return match.group(1)


def skill_paths() -> list[Path]:
    return sorted(
        path
        for path in SKILLS_DIR.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


class SkillFrontmatterYamlTest(unittest.TestCase):
    def test_unquoted_frontmatter_values_do_not_contain_colon_space(self):
        for skill_dir in skill_paths():
            path = skill_dir / "SKILL.md"
            with self.subTest(skill=skill_dir.name):
                for raw in frontmatter(path).splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    match = LINE.match(line)
                    if match is None:
                        continue
                    value = match.group(2)
                    if not value or value[0] in "\"'>|{[":
                        continue
                    self.assertNotIn(
                        ": ",
                        value,
                        f"{path}: unquoted `{match.group(1)}:` value contains "
                        "`: `, which is invalid YAML and hides the skill from "
                        "Cursor's slash picker. Quote the value or drop the "
                        "colon.",
                    )


if __name__ == "__main__":
    unittest.main()
