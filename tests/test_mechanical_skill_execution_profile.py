import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS = REPO_ROOT / "AGENTS.md"


MECHANICAL_SKILLS = ["pr", "ship", "convert-worktree"]

FRONTMATTER_KEY = "disable-model-invocation: true"

AGENTS_REQUIRED_PHRASES = [
    "mechanical",
    "disable-model-invocation: true",
]


def read_frontmatter(skill_name):
    text = (SKILLS_DIR / skill_name / "SKILL.md").read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        raise AssertionError(f"{skill_name}: no frontmatter block found")
    return match.group(1)


class MechanicalSkillExecutionProfileTest(unittest.TestCase):
    def test_mechanical_skills_disable_model_invocation(self):
        for skill_name in MECHANICAL_SKILLS:
            with self.subTest(skill=skill_name):
                frontmatter = read_frontmatter(skill_name)
                self.assertIn(
                    FRONTMATTER_KEY,
                    frontmatter,
                    f"{skill_name}: frontmatter must declare {FRONTMATTER_KEY!r} "
                    "so harnesses skip model invocation for mechanical workflows",
                )

    def test_agents_md_documents_mechanical_execution_rule(self):
        text = AGENTS.read_text().lower()
        for phrase in AGENTS_REQUIRED_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(
                    phrase.lower(),
                    text,
                    f"AGENTS.md must document the mechanical-execution rule (missing {phrase!r})",
                )


if __name__ == "__main__":
    unittest.main()
