"""Concrete-leak validator for public skills.

Public skills are distributed to multiple harnesses (Claude Code, Codex,
Gemini). Most prose may legitimately use harness-specific tool names; the
narrow contract this test enforces covers only the failure modes that are
concrete and untested abstractions cannot fix:

1. AGENTS.md documents the capability glossary so future skills and adapter
   docs have a shared lexicon to reach for.
2. Public skill bodies do not contain the literal Claude API parameter shape
   `subagent_type` or its value `general-purpose`. Those tokens are
   meaningless on Codex and Gemini, where no such parameter exists.
3. Generated PR or commit output does not brand a single harness, since the
   output is user-visible on every harness that runs the skill.

Stylistic harness-specific nouns (`Task tool`, `Agent tool`, `WebSearch`)
are *not* enforced. Replacing them with abstract capability names removes
the noun but degrades execution on the harness that has the tool, with no
measured benefit on harnesses that don't.
"""

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS = REPO_ROOT / "AGENTS.md"


CAPABILITIES = [
    "project.instructions",
    "ticket.read",
    "ticket.write",
    "subagent.dispatch",
    "subagent.dispatch.parallel",
    "web.research",
    "verification.run",
]


FORBIDDEN_TOKENS = [
    "subagent_type",
    "general-purpose",
]


FORBIDDEN_ATTRIBUTION_LINES = [
    "Generated with [Claude Code]",
]


def strip_frontmatter(text):
    match = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
    return text[match.end():] if match else text


def public_skill_files():
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


class CapabilityVocabularyTest(unittest.TestCase):
    def test_agents_md_documents_capability_glossary(self):
        text = AGENTS.read_text()
        self.assertIn(
            "Capability glossary",
            text,
            "AGENTS.md must include a 'Capability glossary' section so "
            "future skills and adapter docs share a lexicon",
        )
        for capability in CAPABILITIES:
            with self.subTest(capability=capability):
                self.assertIn(
                    capability,
                    text,
                    f"AGENTS.md must name the capability {capability!r}",
                )

    def test_public_skill_bodies_avoid_claude_api_parameter_shapes(self):
        for skill_path in public_skill_files():
            skill_name = skill_path.parent.name
            body = strip_frontmatter(skill_path.read_text())
            for token in FORBIDDEN_TOKENS:
                with self.subTest(skill=skill_name, token=token):
                    self.assertNotIn(
                        token,
                        body,
                        f"{skill_name}: token {token!r} is a literal Claude "
                        "API parameter shape that has no meaning on Codex or "
                        "Gemini. Reword to describe the behavior, not the "
                        "parameter.",
                    )

    def test_public_skill_bodies_do_not_brand_generated_output(self):
        for skill_path in public_skill_files():
            skill_name = skill_path.parent.name
            body = strip_frontmatter(skill_path.read_text())
            for line in FORBIDDEN_ATTRIBUTION_LINES:
                with self.subTest(skill=skill_name, line=line):
                    self.assertNotIn(
                        line,
                        body,
                        f"{skill_name}: hardcoded {line!r} in generated PR or "
                        "commit output brands a cross-harness skill for one "
                        "harness. Remove or make neutral.",
                    )


if __name__ == "__main__":
    unittest.main()
