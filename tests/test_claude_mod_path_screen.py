"""The runtime uses the publication screen without changing its breadth."""

import re
import unittest
from pathlib import Path

from test_high_risk_path_screen import CANONICAL_SCREEN, MUST_MATCH, MUST_NOT_MATCH

ROOT = Path(__file__).resolve().parents[1]


class ClaudeModPathScreenTest(unittest.TestCase):
    def test_canonical_literal_is_identical(self):
        text = (ROOT / 'claude-mods/policy.ts').read_text()
        match = re.search(r'HIGH_RISK_SCREEN = String.raw`([^`]+)`', text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), CANONICAL_SCREEN)

    def test_native_tests_cover_the_existing_path_corpus(self):
        text = (ROOT / 'claude-mods/tests/paths.test.ts').read_text()
        for path in MUST_MATCH + MUST_NOT_MATCH:
            self.assertIn(repr(path), text)
