"""Execute the distributed timestamp helpers against offsets and legacy state."""

import re
import unittest
from datetime import datetime, timezone
from pathlib import Path

from triage_shared.skills import SKILLS

ROOT = Path(__file__).resolve().parents[1]


class TriageTimestampTest(unittest.TestCase):
    def helpers(self, text):
        match = re.search(
            r"```python\n(# Timestamp helpers\n.*?)\n```", text, re.DOTALL
        )
        self.assertIsNotNone(match, "skills need executable aware timestamp helpers")
        namespace = {}
        exec(match.group(1), namespace)
        return namespace

    def test_helpers_normalize_offsets_legacy_state_and_duration_cutoffs(self):
        for name in SKILLS:
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            with self.subTest(skill=name):
                helpers = self.helpers(text)
                parse = helpers["parse_timestamp"]
                format_utc = helpers["format_timestamp"]
                cutoff = helpers["refine_cutoff"]
                self.assertEqual(
                    format_utc(parse("2026-03-15T10:30:00Z")), "2026-03-15T10:30:00Z"
                )
                self.assertEqual(
                    format_utc(parse("2026-03-15T06:30:00-04:00")),
                    "2026-03-15T10:30:00Z",
                )
                for value in ("2026-03-15T10:30:00", "2026-03-15 10:30"):
                    expected = datetime.fromisoformat(value).astimezone(timezone.utc)
                    self.assertEqual(parse(value), expected)
                now = parse("2026-11-01T06:30:00Z")
                self.assertEqual(format_utc(cutoff("5h", now)), "2026-11-01T01:30:00Z")
                self.assertEqual(format_utc(cutoff("10m", now)), "2026-11-01T06:20:00Z")
                self.assertEqual(format_utc(cutoff("6d", now)), "2026-10-26T06:30:00Z")
                self.assertIsNone(cutoff("invalid", now))
                self.assertIsNone(cutoff(None, now))
                self.assertEqual(parse("2026-11-01T02:30:00-04:00"), now)
                self.assertGreaterEqual(
                    parse("2026-11-01T01:30:00Z"), cutoff("5h", now)
                )
                with self.assertRaises(ValueError):
                    parse("bad state")

    def test_display_write_and_comparisons_share_utc_contract(self):
        for name in SKILLS:
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            with self.subTest(skill=name):
                self.assertIn("Last run: 2026-03-15T10:30:00Z", text)
                self.assertNotIn("Last run: 2026-03-15 10:30", text)
                self.assertIn(
                    "set `"
                    + name
                    + "` to `format_timestamp(datetime.now(timezone.utc))`",
                    text,
                )
                self.assertIn("parse_timestamp(created_at) >= cutoff", text)
                self.assertIn("legacy timezone assumption", text)
                self.assertIn("Invalid timestamps", text)
                self.assertIn("do not silently drop", text)


if __name__ == "__main__":
    unittest.main()
