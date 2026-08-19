"""Gemini extension context is operator-facing, not maintainer AGENTS.md."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "gemini-extension.json"
README = REPO_ROOT / "README.md"
INSTALL = REPO_ROOT / ".gemini" / "INSTALL.md"

# Phrases that belong in this repository's contributor contract, not in the
# briefing Gemini injects into every end-user session.
MAINTAINER_MARKERS = (
    "triage_shared",
    "scripts/dev-link.sh",
    "release-please",
    "personal-machine threat model",
    "do not hand-edit",
    "BASE_BRANCH",
    "high-risk path",
)


class TestGeminiExtensionContext(unittest.TestCase):
    def test_manifest_does_not_inject_maintainer_agents_md(self) -> None:
        self.assertTrue(MANIFEST.is_file(), f"missing {MANIFEST}")
        manifest = json.loads(MANIFEST.read_text())
        context_name = manifest.get("contextFileName")
        self.assertIsInstance(context_name, str)
        self.assertNotEqual(
            context_name,
            "AGENTS.md",
            "Gemini CLI loads contextFileName into every user session; "
            "that must not be this repository's maintainer AGENTS.md",
        )
        context_path = REPO_ROOT / context_name
        self.assertTrue(
            context_path.is_file(),
            f"contextFileName {context_name!r} does not exist at {context_path}",
        )

    def test_extension_context_is_operator_facing(self) -> None:
        manifest = json.loads(MANIFEST.read_text())
        context_path = REPO_ROOT / manifest["contextFileName"]
        text = context_path.read_text()
        self.assertIn("/next-ticket", text)
        self.assertRegex(
            text,
            r"CLAUDE\.md|AGENTS\.md|GEMINI\.md",
            "primer should send the agent to the user's project convention files",
        )
        for marker in MAINTAINER_MARKERS:
            self.assertNotIn(
                marker,
                text,
                f"extension context must not carry maintainer policy ({marker!r})",
            )

    def test_gemini_install_docs_match_other_harnesses(self) -> None:
        self.assertTrue(INSTALL.is_file(), f"missing {INSTALL}")
        install = INSTALL.read_text()
        self.assertIn("gemini extensions install", install)
        self.assertIn("gemini extensions update agentic-toolkit", install)
        readme = README.read_text()
        gemini_block = readme.split("<summary>Gemini CLI</summary>", 1)[1]
        gemini_block = gemini_block.split("</details>", 1)[0]
        self.assertIn(".gemini/INSTALL.md", gemini_block)


if __name__ == "__main__":
    unittest.main()
