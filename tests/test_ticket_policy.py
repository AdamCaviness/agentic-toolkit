"""ticket_policy.py makes saved ticket choices portable to fresh runs.

The cache in `next-ticket-config.json` lives in the system temp directory, so a
scheduled cloud run or a teammate starts without it. The committed
`.agents/ticket-policy.json` carries the same choices inside the repository.
These tests pin the precedence (policy over cache), the failure handling, and
the export that lets an operator commit the cache.
"""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "skills" / "next-ticket" / "ticket_policy.py"

CANDIDATE = {"version": 2, "tiers": [["Ready", "(none)"], ["Backlog"]], "exclude": ["Idea"], "bugs": "any_tier"}
LEGACY_CANDIDATE = {"filter": "open"}
IN_PROGRESS = {"version": 2, "labels": {"add": ["in progress"], "remove": ["ready"]}}


def load_script():
    spec = importlib.util.spec_from_file_location("ticket_policy", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PolicyTestCase(unittest.TestCase):
    def setUp(self):
        self.script = load_script()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "repo"
        self.root.mkdir()
        self.cache = Path(tmp.name) / "next-ticket-config.json"
        self.policy = self.root / ".agents" / "ticket-policy.json"

    def write_cache(self, entry):
        self.cache.write_text(json.dumps({str(self.root): entry}))

    def write_policy(self, document):
        self.policy.parent.mkdir(parents=True, exist_ok=True)
        text = document if isinstance(document, str) else json.dumps(document)
        self.policy.write_text(text)

    def run_cmd(self, command):
        out = io.StringIO()
        with redirect_stdout(out):
            self.script.main([command, "--root", str(self.root), "--cache-file", str(self.cache)])
        return json.loads(out.getvalue())


class ReadTest(PolicyTestCase):
    def test_nothing_saved_anywhere(self):
        result = self.run_cmd("read")
        self.assertEqual(result["status"], "ok")
        self.assertIsNone(result["system"])
        self.assertEqual(result["states"], {})
        self.assertFalse(result["policy_present"])

    def test_cache_only_is_reported_as_cache(self):
        self.write_cache({"system": "github", "states": {"candidate": CANDIDATE}})
        result = self.run_cmd("read")
        self.assertEqual((result["system"], result["system_source"]), ("github", "cache"))
        self.assertEqual(result["states"]["candidate"]["source"], "cache")
        self.assertTrue(result["candidate_current"])

    def test_plain_string_cache_entry_is_a_system_with_no_states(self):
        self.write_cache("jira")
        result = self.run_cmd("read")
        self.assertEqual((result["system"], result["states"]), ("jira", {}))

    def test_policy_works_with_no_cache_at_all(self):
        self.write_policy({"version": 1, "system": "github", "states": {"in_progress": IN_PROGRESS}})
        result = self.run_cmd("read")
        self.assertEqual((result["system"], result["system_source"]), ("github", "policy"))
        self.assertEqual(result["states"]["in_progress"], {"value": IN_PROGRESS, "source": "policy"})
        self.assertTrue(result["policy_present"])

    def test_policy_wins_per_state_and_the_cache_fills_the_rest(self):
        self.write_cache({"system": "jira", "states": {"candidate": CANDIDATE, "in_progress": {"transition": "31"}}})
        self.write_policy({"version": 1, "system": "github", "states": {"in_progress": IN_PROGRESS}})
        result = self.run_cmd("read")
        self.assertEqual(result["system"], "github")
        self.assertEqual(result["states"]["in_progress"]["source"], "policy")
        self.assertEqual(result["states"]["in_progress"]["value"], IN_PROGRESS)
        self.assertEqual(result["states"]["candidate"]["source"], "cache")

    def test_unsupported_sentinel_in_the_policy_is_a_value(self):
        sentinel = {"unsupported": "no done label"}
        self.write_policy({"version": 1, "states": {"done": sentinel}})
        self.assertEqual(self.run_cmd("read")["states"]["done"]["value"], sentinel)

    def test_legacy_candidate_is_not_current(self):
        self.write_cache({"system": "github", "states": {"candidate": LEGACY_CANDIDATE}})
        self.assertFalse(self.run_cmd("read")["candidate_current"])

    def test_no_candidate_is_not_current(self):
        self.assertFalse(self.run_cmd("read")["candidate_current"])

    def test_invalid_policy_is_reported_and_the_cache_still_applies(self):
        self.write_cache({"system": "github", "states": {"candidate": CANDIDATE}})
        for broken in ("{not json", json.dumps([1]), json.dumps({"version": 2}),
                       json.dumps({"version": 1, "states": []}),
                       json.dumps({"version": 1, "states": {"done": "x"}}),
                       json.dumps({"version": 1, "system": 3})):
            with self.subTest(broken=broken):
                self.write_policy(broken)
                result = self.run_cmd("read")
                self.assertEqual(result["status"], "invalid_policy")
                self.assertIn("ticket-policy.json", result["detail"])
                self.assertEqual(result["system"], "github")
                self.assertEqual(result["states"]["candidate"]["source"], "cache")
                self.assertFalse(result["policy_present"])

    def test_unreadable_cache_is_not_fatal_to_a_committed_policy(self):
        self.cache.write_text("{broken")
        self.write_policy({"version": 1, "system": "github"})
        result = self.run_cmd("read")
        self.assertEqual(result["system"], "github")


class LegacyStatesTest(PolicyTestCase):
    def test_old_github_sentinel_and_old_shapes_are_legacy(self):
        self.write_cache(
            {
                "system": "github",
                "states": {
                    "in_progress": {"unsupported": "plain GitHub Issues with no project board"},
                    "in_review": {"field": "PVTSSF_x", "option": "abc"},
                    "done": {"version": 2, "unsupported": "no done label"},
                    "filed": IN_PROGRESS,
                    "candidate": LEGACY_CANDIDATE,
                },
            }
        )
        self.assertEqual(self.run_cmd("read")["legacy_states"], ["in_progress", "in_review"])

    def test_a_free_form_github_system_name_still_counts(self):
        self.write_cache({"system": "GitHub Issues", "states": {"in_progress": {"unsupported": "x"}}})
        self.assertEqual(self.run_cmd("read")["legacy_states"], ["in_progress"])

    def test_other_systems_keep_their_values(self):
        self.write_cache({"system": "jira", "states": {"in_progress": {"transition": "31"}}})
        self.assertEqual(self.run_cmd("read")["legacy_states"], [])

    def test_a_policy_value_without_a_version_is_legacy_too(self):
        self.write_policy({"version": 1, "system": "github", "states": {"in_progress": {"labels": {"add": ["x"]}}}})
        self.assertEqual(self.run_cmd("read")["legacy_states"], ["in_progress"])

    def test_export_does_not_commit_legacy_values(self):
        self.write_cache(
            {"system": "github", "states": {"in_progress": {"unsupported": "old"}, "in_review": IN_PROGRESS}}
        )
        result = self.run_cmd("export")
        self.assertEqual(result["skipped_legacy"], ["in_progress"])
        self.assertEqual(list(json.loads(self.policy.read_text())["states"]), ["in_review"])


class ExportTest(PolicyTestCase):
    def test_writes_the_cache_entry_as_a_policy_file(self):
        self.write_cache({"system": "github", "states": {"candidate": CANDIDATE, "in_progress": IN_PROGRESS}})
        result = self.run_cmd("export")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["keys"], ["candidate", "in_progress"])
        written = json.loads(self.policy.read_text())
        self.assertEqual(written, {"version": 1, "system": "github", "states": {"candidate": CANDIDATE, "in_progress": IN_PROGRESS}})
        self.assertTrue(self.policy.read_text().endswith("\n"))

    def test_exported_file_reads_back_as_policy(self):
        self.write_cache({"system": "github", "states": {"in_progress": IN_PROGRESS}})
        self.run_cmd("export")
        self.cache.unlink()
        result = self.run_cmd("read")
        self.assertEqual(result["system_source"], "policy")
        self.assertEqual(result["states"]["in_progress"]["value"], IN_PROGRESS)

    def test_keeps_policy_keys_the_cache_does_not_hold_and_the_cache_wins_ties(self):
        self.write_policy({"version": 1, "system": "github", "states": {"done": {"unsupported": "x"}, "in_progress": {"old": 1}}})
        self.write_cache({"system": "github", "states": {"in_progress": IN_PROGRESS}})
        self.run_cmd("export")
        states = json.loads(self.policy.read_text())["states"]
        self.assertEqual(states["done"], {"unsupported": "x"})
        self.assertEqual(states["in_progress"], IN_PROGRESS)

    def test_string_cache_entry_exports_only_the_system(self):
        self.write_cache("jira")
        self.run_cmd("export")
        self.assertEqual(json.loads(self.policy.read_text()), {"version": 1, "system": "jira"})

    def test_nothing_to_export(self):
        self.assertEqual(self.run_cmd("export")["status"], "no_cache_entry")
        self.assertFalse(self.policy.exists())

    def test_never_overwrites_an_invalid_policy(self):
        self.write_policy("{not json")
        self.write_cache({"system": "github", "states": {"in_progress": IN_PROGRESS}})
        self.assertEqual(self.run_cmd("export")["status"], "invalid_policy")
        self.assertEqual(self.policy.read_text(), "{not json")

    def test_leaves_no_staging_file_behind(self):
        self.write_cache({"system": "github"})
        self.run_cmd("export")
        self.assertEqual([p.name for p in self.policy.parent.iterdir()], ["ticket-policy.json"])


if __name__ == "__main__":
    unittest.main()
