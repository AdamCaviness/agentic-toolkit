import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS = REPO_ROOT / "AGENTS.md"


USER_ONLY_SKILLS = ["pr", "ship", "convert-worktree"]

# Skills that write to the tracker or the remote and run from schedules, so they
# stay model-invocable and keep their descriptions to explicit requests.
UNATTENDED_WRITE_SKILLS = [
    "apply-review",
    "next-ticket",
    "triage-architecture",
    "triage-bugs",
    "triage-product",
]

FRONTMATTER_KEY = "disable-model-invocation: true"

AGENTS_REQUIRED_PHRASES = [
    "model invocation policy",
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

    def test_every_other_skill_stays_model_invocable(self):
        # Scheduled fires and routines reach a skill through the model, so the
        # key on an unattended skill silently breaks scheduled runs.
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if skill_dir.name in USER_ONLY_SKILLS or not (skill_dir / "SKILL.md").is_file():
                continue
            with self.subTest(skill=skill_dir.name):
                self.assertNotIn(
                    FRONTMATTER_KEY,
                    read_frontmatter(skill_dir.name),
                    f"{skill_dir.name} is meant to run unattended or is gated inside the "
                    "skill; see the Model invocation policy in AGENTS.md before adding the key",
                )

    def test_unattended_write_skills_describe_explicit_requests(self):
        for skill_name in UNATTENDED_WRITE_SKILLS:
            with self.subTest(skill=skill_name):
                description = next(
                    line for line in read_frontmatter(skill_name).splitlines()
                    if line.startswith("description:")
                )
                self.assertIn("Use when asked to ", description)

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
