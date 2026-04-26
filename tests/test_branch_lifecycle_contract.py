import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
README = REPO_ROOT / "README.md"
AGENTS = REPO_ROOT / "AGENTS.md"


LIFECYCLE_REQUIRED_SKILLS = [
    "ship",
    "pr",
    "get-it-right",
    "next-ticket",
    "convert-worktree",
    "code-review",
]

DETECTION_SNIPPET_ELEMENTS = [
    "git symbolic-ref refs/remotes/origin/HEAD",
    "BASE_BRANCH",
]

COMMAND_POSITION_FORBIDDEN = [
    r"git checkout main\b",
    r"git pull origin main\b",
    r"git pull --ff-only origin main\b",
    r"git fetch origin main\b",
    r"git merge-base HEAD origin/main\b",
    r"git merge-base HEAD main\b",
    r"git diff main\.\.\.HEAD",
    r"git log main\.\.HEAD",
]

FORBIDDEN_PATTERNS = {
    "ship": COMMAND_POSITION_FORBIDDEN + [
        r"\bahead of main\b",
        r"\bIf on main\b",
    ],
    "pr": COMMAND_POSITION_FORBIDDEN + [
        r"on `main` or `master`",
        r"\bahead of main\b",
    ],
    "get-it-right": COMMAND_POSITION_FORBIDDEN,
    "next-ticket": COMMAND_POSITION_FORBIDDEN,
    "convert-worktree": COMMAND_POSITION_FORBIDDEN,
    "code-review": COMMAND_POSITION_FORBIDDEN,
}


class BranchLifecycleContractTest(unittest.TestCase):
    def skill_text(self, skill_name):
        return (SKILLS_DIR / skill_name / "SKILL.md").read_text()

    def test_workflow_skills_include_default_branch_detection(self):
        for skill_name in LIFECYCLE_REQUIRED_SKILLS:
            with self.subTest(skill=skill_name):
                text = self.skill_text(skill_name)
                for element in DETECTION_SNIPPET_ELEMENTS:
                    self.assertIn(
                        element,
                        text,
                        f"{skill_name}: missing canonical detection element {element!r}",
                    )

    def test_workflow_skills_do_not_hardcode_default_branch_name(self):
        for skill_name, patterns in FORBIDDEN_PATTERNS.items():
            text = self.skill_text(skill_name)
            for pattern in patterns:
                with self.subTest(skill=skill_name, pattern=pattern):
                    self.assertIsNone(
                        re.search(pattern, text),
                        f"{skill_name}: forbidden hardcoded reference matched {pattern!r}",
                    )

    def test_readme_uses_default_branch_wording_for_workflow_skills(self):
        text = README.read_text().lower()
        self.assertNotIn("syncs local main", text)
        self.assertIn("default branch", text)

    def test_agents_md_documents_branch_lifecycle_contract(self):
        text = AGENTS.read_text().lower()
        self.assertIn("branch lifecycle", text)
        self.assertIn("git symbolic-ref refs/remotes/origin/head", text)


if __name__ == "__main__":
    unittest.main()
