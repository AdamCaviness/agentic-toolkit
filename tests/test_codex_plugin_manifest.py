"""Codex plugin manifest is a peer of the Claude Code plugin manifest."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE = REPO_ROOT / ".claude-plugin" / "plugin.json"
CODEX = REPO_ROOT / ".codex-plugin" / "plugin.json"

PEER_KEYS = (
    "name",
    "description",
    "version",
    "homepage",
    "repository",
    "license",
    "keywords",
)


class TestCodexPluginManifest(unittest.TestCase):
    def test_codex_plugin_json_exists(self) -> None:
        self.assertTrue(CODEX.is_file(), f"missing {CODEX}")

    def test_codex_peers_claude_identity_fields(self) -> None:
        claude = json.loads(CLAUDE.read_text())
        codex = json.loads(CODEX.read_text())
        for key in PEER_KEYS:
            self.assertIn(key, codex, f"codex missing {key}")
            self.assertEqual(codex[key], claude[key], f"mismatch on {key}")
        self.assertEqual(codex["author"]["name"], claude["author"]["name"])

    def test_codex_points_skills_at_repo_skills_dir(self) -> None:
        codex = json.loads(CODEX.read_text())
        self.assertEqual(codex["skills"], "./skills/")
        skill_dirs = [
            path
            for path in (REPO_ROOT / "skills").iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        ]
        self.assertEqual(len(skill_dirs), 13)

    def test_release_please_bumps_codex_plugin_version(self) -> None:
        config = json.loads(
            (REPO_ROOT / "release-please-config.json").read_text()
        )
        extra = config["packages"]["."]["extra-files"]
        codex_entries = [
            e
            for e in extra
            if e.get("path") == ".codex-plugin/plugin.json"
            and e.get("jsonpath") == "$.version"
        ]
        self.assertEqual(
            len(codex_entries),
            1,
            "release-please must bump .codex-plugin/plugin.json $.version",
        )


if __name__ == "__main__":
    unittest.main()
