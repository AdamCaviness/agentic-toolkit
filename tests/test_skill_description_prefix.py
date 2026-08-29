"""Every shipped skill description starts with Use when for picker branding."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
PREFIX = "Use when "


def skill_paths() -> list[Path]:
    return sorted(
        path
        for path in SKILLS_DIR.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


def frontmatter(path: Path) -> str:
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        raise AssertionError(f"{path}: no frontmatter block found")
    return match.group(1)


def description_text(path: Path) -> str:
    lines = frontmatter(path).splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("description:"):
            continue
        rest = line[len("description:") :].strip()
        if rest in (">", "|"):
            parts: list[str] = []
            for cont in lines[index + 1 :]:
                if cont and not cont[0].isspace():
                    break
                parts.append(cont.strip())
            return " ".join(parts)
        if rest.startswith('"'):
            return json.loads(rest)
        if rest.startswith("'"):
            return rest[1:-1]
        return rest
    raise AssertionError(f"{path}: frontmatter has no description")


class SkillDescriptionPrefixTest(unittest.TestCase):
    def test_descriptions_start_with_use_when(self) -> None:
        for skill_dir in skill_paths():
            path = skill_dir / "SKILL.md"
            with self.subTest(skill=skill_dir.name):
                desc = description_text(path)
                self.assertTrue(
                    desc.startswith(PREFIX),
                    f"{path}: description must start with {PREFIX!r}, got {desc[:40]!r}...",
                )


if __name__ == "__main__":
    unittest.main()
