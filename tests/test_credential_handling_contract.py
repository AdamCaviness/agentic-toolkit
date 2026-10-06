"""Skills that reach a repository host or ticket tracker share one credential rule.

The host and ticket skills told the agent to use "credentials the session
already holds" without saying where those come from, which invites a search
through environment variables, dotfiles, and keychains. Every skill that talks
to a repository host or ticket tracker now carries one `## Credentials` section
verbatim: access comes only from an authenticated CLI, an MCP connector, or an
environment variable the operator named; a token is referenced by variable name
and never printed; and a credential goes only to the system it belongs to.
"""

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"

CREDENTIAL_SKILLS = [
    "pr",
    "ship",
    "apply-review",
    "update-deps",
    "create-ticket",
    "next-ticket",
    "get-it-right",
    "triage-architecture",
    "triage-bugs",
    "triage-product",
]

# A skill that runs a repository host or ticket tracker operation.
EXTERNAL_SYSTEM = re.compile(
    r"\bgh (pr|api|repo|issue)\b|\bglab (mr|api|issue)\b|\baz (repos|boards)\b"
    r"|\bREST API\b|ticket tracker"
)

# Phrasings that leave the source of a credential open.
VAGUE_SOURCES = [
    "credentials the session already holds",
    "credentials already present",
    "the session's credentials",
    "which credential to supply",
]


def skill_text(name):
    return (SKILLS_DIR / name / "SKILL.md").read_text()


def credentials_section(text):
    match = re.search(r"^## Credentials\n(.*?)(?=^## |^```|\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else None


class CredentialSectionTest(unittest.TestCase):
    def test_every_listed_skill_carries_the_section(self):
        for name in CREDENTIAL_SKILLS:
            with self.subTest(skill=name):
                self.assertIsNotNone(credentials_section(skill_text(name)))

    def test_section_is_identical_across_skills(self):
        reference = credentials_section(skill_text(CREDENTIAL_SKILLS[0]))
        for name in CREDENTIAL_SKILLS[1:]:
            with self.subTest(skill=name):
                self.assertEqual(credentials_section(skill_text(name)), reference)

    def test_triage_sub_agents_receive_the_section(self):
        reference = credentials_section(skill_text(CREDENTIAL_SKILLS[0]))
        for name in ["triage-architecture", "triage-bugs", "triage-product"]:
            with self.subTest(skill=name):
                text = skill_text(name)
                prompt = text[text.index("### Sub-Agent Prompt Template"):]
                self.assertEqual(credentials_section(prompt), reference)

    def test_skills_reaching_external_systems_are_listed(self):
        for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            name = path.parent.name
            if name in CREDENTIAL_SKILLS:
                continue
            with self.subTest(skill=name):
                self.assertIsNone(
                    EXTERNAL_SYSTEM.search(path.read_text()),
                    f"{name} reaches a host or tracker; add the ## Credentials "
                    "section and list it in CREDENTIAL_SKILLS",
                )

    def test_no_skill_leaves_the_credential_source_open(self):
        for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            text = path.read_text()
            for phrase in VAGUE_SOURCES:
                with self.subTest(skill=path.parent.name, phrase=phrase):
                    self.assertNotIn(phrase, text)


class CredentialRuleContentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = credentials_section(skill_text("pr")) or ""

    def test_names_the_only_allowed_sources(self):
        for source in ["authenticated CLI", "MCP connector", "environment variable the operator named"]:
            with self.subTest(source=source):
                self.assertIn(source, self.text)

    def test_forbids_searching_for_tokens(self):
        self.assertIn("Never look for a token anywhere else", self.text)
        self.assertIn("never ask the operator to paste one", self.text)

    def test_references_tokens_by_variable_name(self):
        self.assertIn("never its value", self.text)
        self.assertIn("Never print, log, or write a token's value", self.text)

    def test_limits_where_credentials_go(self):
        self.assertIn("git remote get-url origin", self.text)
        self.assertIn("untrusted text", self.text)


if __name__ == "__main__":
    unittest.main()
