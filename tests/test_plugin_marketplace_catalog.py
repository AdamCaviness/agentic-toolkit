"""Installer cards list the same skill catalog as the repo ships."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE = REPO_ROOT / ".claude-plugin" / "plugin.json"
CURSOR = REPO_ROOT / ".cursor-plugin" / "plugin.json"
CODEX = REPO_ROOT / ".codex-plugin" / "plugin.json"
GEMINI = REPO_ROOT / "gemini-extension.json"


def shipped_skill_names() -> set[str]:
    return {
        path.name
        for path in (REPO_ROOT / "skills").iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }


def names_in_description(description: str) -> list[str]:
    _, _, listed = description.partition(":")
    return [part.strip() for part in listed.split(",") if part.strip()]


class TestPluginMarketplaceCatalog(unittest.TestCase):
    def test_plugin_descriptions_name_every_shipped_skill(self) -> None:
        expected = shipped_skill_names()
        self.assertIn("create-ticket", expected)
        manifests = {
            ".claude-plugin/plugin.json": json.loads(CLAUDE.read_text()),
            ".cursor-plugin/plugin.json": json.loads(CURSOR.read_text()),
            ".codex-plugin/plugin.json": json.loads(CODEX.read_text()),
            "gemini-extension.json": json.loads(GEMINI.read_text()),
        }
        for path, manifest in manifests.items():
            listed = names_in_description(manifest["description"])
            self.assertEqual(
                set(listed),
                expected,
                f"{path} description must name every shipped skill, "
                "including create-ticket",
            )
            self.assertEqual(
                len(listed),
                len(set(listed)),
                f"{path} description repeats a skill name",
            )

    def test_codex_short_description_mentions_creating_tickets(self) -> None:
        codex = json.loads(CODEX.read_text())
        short = codex["interface"]["shortDescription"].lower()
        self.assertRegex(
            short,
            r"creat",
            "Codex marketplace shortDescription must mention creating tickets "
            "before install, not only triage and shipping",
        )


if __name__ == "__main__":
    unittest.main()
