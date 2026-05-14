import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS = REPO_ROOT / "AGENTS.md"


USER_ONLY_SKILLS = ["pr", "ship", "convert-worktree"]

FRONTMATTER_KEY = "disable-model-invocation: true"

AGENTS_REQUIRED_PHRASES = [
    "user-only skills",
    "disable-model-invocation: true",
]


def read_frontmatter(skill_name):
    text = (SKILLS_DIR / skill_name / "SKILL.md").read_text()
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        raise AssertionError(f"{skill_name}: no frontmatter block found")
    return match.group(1)


class UserOnlySkillTest(unittest.TestCase):
    def test_user_only_skills_disable_model_invocation(self):
        for skill_name in USER_ONLY_SKILLS:
            with self.subTest(skill=skill_name):
                frontmatter = read_frontmatter(skill_name)
                self.assertIn(
                    FRONTMATTER_KEY,
                    frontmatter,
                    f"{skill_name}: frontmatter must declare {FRONTMATTER_KEY!r} "
                    "so the model cannot invoke it autonomously",
                )

    def test_agents_md_documents_user_only_skill_rule(self):
        text = AGENTS.read_text().lower()
        for phrase in AGENTS_REQUIRED_PHRASES:
            with self.subTest(phrase=phrase):
                self.assertIn(
                    phrase.lower(),
                    text,
                    f"AGENTS.md must document the user-only skill rule (missing {phrase!r})",
                )


if __name__ == "__main__":
    unittest.main()
