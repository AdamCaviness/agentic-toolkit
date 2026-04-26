import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SHIP_SKILL = REPO_ROOT / "skills" / "ship" / "SKILL.md"


class ShipPublishStateGateTest(unittest.TestCase):
    def setUp(self):
        self.text = SHIP_SKILL.read_text()
        self.lower = self.text.lower()

    def test_ship_skill_inventories_committed_paths_before_push(self):
        self.assertIn('git diff --name-status "$BASE_BRANCH"...HEAD', self.text)

    def test_ship_skill_screens_high_risk_paths_before_push(self):
        self.assertIn("high-risk", self.lower)
        for pattern in [".env", ".pem", "credential"]:
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, self.lower)

    def test_ship_skill_pre_push_gate_precedes_push_step(self):
        gate_index = self.lower.find("high-risk")
        push_index = self.text.find("git push")
        self.assertNotEqual(gate_index, -1, "high-risk gate prose missing")
        self.assertNotEqual(push_index, -1, "git push command missing")
        self.assertLess(
            gate_index,
            push_index,
            "high-risk screen must appear before any push command",
        )

    def test_ship_skill_resolves_base_branch_in_gate_block(self):
        self.assertIn(
            'BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD',
            self.text,
        )


if __name__ == "__main__":
    unittest.main()
