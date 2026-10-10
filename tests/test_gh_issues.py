"""gh_issues.py reads GitHub issues, labels, and Projects data without a live API.

The script shapes what next-ticket sees for GitHub repositories: which open
issues are available to start, which project fields rank them, and which
failures are structural (cacheable) versus transient. Every case replaces
`run_gh` with canned GraphQL payloads modeled on a real project board: a
Status field (Idea, Backlog, Ready, In progress, Done), Priority, Track, and a
numeric Score.
"""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "skills" / "next-ticket" / "gh_issues.py"

PROJECT_ID = "PVT_board"
OTHER_PROJECT_ID = "PVT_other"


def load_script():
    spec = importlib.util.spec_from_file_location("gh_issues", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def select(field, name):
    return {
        "__typename": "ProjectV2ItemFieldSingleSelectValue",
        "name": name,
        "field": {"name": field},
    }


def number(field, value):
    return {
        "__typename": "ProjectV2ItemFieldNumberValue",
        "number": value,
        "field": {"name": field},
    }


def issue(num, title="t", labels=(), assignees=(), items=None, created="2026-01-01T00:00:00Z"):
    return {
        "number": num,
        "title": title,
        "createdAt": created,
        "labels": {"nodes": [{"name": label} for label in labels]},
        "assignees": {"nodes": [{"login": a} for a in assignees]},
        "projectItems": {
            "nodes": [
                {"project": {"id": pid}, "fieldValues": {"nodes": values}}
                for pid, values in (items or {}).items()
            ]
        },
    }


def issues_page(nodes, has_next=False, cursor=None):
    return {
        "data": {
            "repository": {
                "issues": {
                    "pageInfo": {"hasNextPage": has_next, "endCursor": cursor},
                    "nodes": nodes,
                }
            }
        }
    }


def projects_payload(projects):
    return {"data": {"repository": {"projectsV2": {"nodes": projects}}}}


BOARD = {
    "id": PROJECT_ID,
    "number": 1,
    "title": "Roadmap",
    "closed": False,
    "readme": "Bugs first, then by Score.",
    "fields": {
        "nodes": [
            {"__typename": "ProjectV2Field", "id": "f1", "name": "Title", "dataType": "TITLE"},
            {
                "__typename": "ProjectV2SingleSelectField",
                "id": "f2",
                "name": "Status",
                "options": [{"id": "o1", "name": "Idea"}, {"id": "o2", "name": "Backlog"}, {"id": "o3", "name": "Done"}],
            },
            {"__typename": "ProjectV2Field", "id": "f3", "name": "Score", "dataType": "NUMBER"},
        ]
    },
}


def board_values(status, priority=None, score=None):
    values = [select("Status", status)]
    if priority:
        values.append(select("Priority", priority))
    if score is not None:
        values.append(number("Score", score))
    return values


class FakeGh:
    """Dispatches on the GraphQL text so each test only supplies payloads."""

    def __init__(self, issue_pages=(), projects=None, fail=None, mutations=None, repo_labels=(), edit=(0, "", "")):
        self.mutations = mutations or {}
        self.repo_labels = list(repo_labels)
        self.edit = edit
        self.issue_pages = list(issue_pages)
        self.projects = projects
        self.fail = fail
        self.calls = []

    def __call__(self, args):
        self.calls.append(args)
        if self.fail:
            return self.fail
        if args[:2] == ["issue", "edit"]:
            return self.edit
        if args[:2] == ["label", "list"]:
            return 0, json.dumps([{"name": n} for n in self.repo_labels]), ""
        if args[:2] == ["repo", "view"]:
            return 0, json.dumps({"owner": {"login": "acme"}, "name": "app"}), ""
        query = next(a for a in args if a.startswith("query="))
        for marker, payload in self.mutations.items():
            if marker in query:
                return 0, json.dumps(payload), ""
        if "projectsV2" in query:
            return 0, json.dumps(projects_payload(self.projects)), ""
        return 0, json.dumps(self.issue_pages.pop(0)), ""


class ScriptTestCase(unittest.TestCase):
    def setUp(self):
        self.script = load_script()

    def run_main(self, argv):
        with mock.patch("sys.stdout") as out:
            written = []
            out.write.side_effect = written.append
            self.script.main(argv)
        return json.loads("".join(written))

    def run_cmd(self, fake, argv):
        with mock.patch.object(self.script, "run_gh", fake):
            return self.run_main(argv)


class CandidatesTest(ScriptTestCase):
    TIERS = '[["Ready","(none)"],["Backlog"]]'
    EXCLUDE = '["Idea","In progress","Done","label:blocked"]'

    def run_candidates(self, nodes, *extra, project=True):
        fake = FakeGh(issue_pages=[issues_page(nodes)])
        argv = ["candidates", "--tiers", self.TIERS, "--exclude", self.EXCLUDE]
        if project:
            argv += ["--project-id", PROJECT_ID]
        result = self.run_cmd(fake, argv + list(extra))
        self.fake = fake
        return result

    def tiers(self, result):
        return {c["id"]: c["tier"] for c in result["candidates"]}

    def test_assigns_tiers_in_order_and_hides_excluded_states(self):
        result = self.run_candidates(
            [
                issue(1, items={PROJECT_ID: board_values("Ready")}),
                issue(2, items={PROJECT_ID: board_values("Backlog")}),
                issue(3, items={PROJECT_ID: board_values("Idea")}),
                issue(4, items={PROJECT_ID: board_values("In progress")}),
                issue(5, items={PROJECT_ID: board_values("Done")}),
            ]
        )
        self.assertEqual(self.tiers(result), {"1": 1, "2": 2})

    def test_issues_with_no_signal_share_the_first_tier_that_lists_none(self):
        result = self.run_candidates([issue(1), issue(2, labels=["bug", "area:api"])])
        self.assertEqual(self.tiers(result), {"1": 1, "2": 1})

    def test_item_on_the_board_without_a_status_value_has_no_signal(self):
        result = self.run_candidates([issue(1, items={PROJECT_ID: [number("Score", 3.0)]})])
        self.assertEqual(self.tiers(result), {"1": 1})

    def test_no_signal_is_dropped_when_no_tier_lists_none(self):
        fake = FakeGh(issue_pages=[issues_page([issue(1), issue(2, items={PROJECT_ID: board_values("Backlog")})])])
        result = self.run_cmd(fake, ["candidates", "--project-id", PROJECT_ID, "--tiers", '[["Ready"],["Backlog"]]'])
        self.assertEqual(self.tiers(result), {"2": 2})

    def test_excluded_label_beats_a_ready_status(self):
        result = self.run_candidates(
            [issue(1, labels=["blocked"], items={PROJECT_ID: board_values("Ready")})]
        )
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["unclassified_states"], {})

    def test_labels_are_signals_without_a_project(self):
        fake = FakeGh(issue_pages=[issues_page([issue(1, labels=["idea"]), issue(2, labels=["ready"]), issue(3)])])
        result = self.run_cmd(
            fake,
            ["candidates", "--tiers", '[["label:ready","(none)"]]', "--exclude", '["label:idea"]'],
        )
        self.assertEqual(self.tiers(result), {"2": 1, "3": 1})
        self.assertTrue(all(c["board"] is None for c in result["candidates"]))

    def test_unlisted_status_is_hidden_and_reported(self):
        result = self.run_candidates(
            [
                issue(1, items={PROJECT_ID: board_values("In review")}),
                issue(2, items={PROJECT_ID: board_values("In review")}),
                issue(3, items={PROJECT_ID: board_values("Ready")}),
            ]
        )
        self.assertEqual(self.tiers(result), {"3": 1})
        self.assertEqual(result["unclassified_states"], {"In review": 2})

    def test_matching_is_case_insensitive(self):
        result = self.run_candidates(
            [issue(1, labels=["Blocked"]), issue(2, items={PROJECT_ID: board_values("BACKLOG")})]
        )
        self.assertEqual(self.tiers(result), {"2": 2})

    def test_without_tiers_every_non_excluded_issue_is_tier_one(self):
        fake = FakeGh(issue_pages=[issues_page([issue(1, items={PROJECT_ID: board_values("Done")}), issue(2)])])
        result = self.run_cmd(fake, ["candidates", "--project-id", PROJECT_ID, "--exclude", '["Done"]'])
        self.assertEqual(self.tiers(result), {"2": 1})

    def test_bug_flag_from_a_board_field(self):
        fake = FakeGh(
            issue_pages=[
                issues_page(
                    [
                        issue(1, items={PROJECT_ID: board_values("Ready") + [select("Track", "Bug")]}),
                        issue(2, items={PROJECT_ID: board_values("Ready") + [select("Track", "Roadmap")]}),
                        issue(3, labels=["bug"]),
                    ]
                )
            ]
        )
        result = self.run_cmd(
            fake, ["candidates", "--project-id", PROJECT_ID, "--bug-signal", "Track=Bug"]
        )
        self.assertEqual({c["id"]: c["bug"] for c in result["candidates"]}, {"1": True, "2": False, "3": False})

    def test_bug_flag_from_a_label(self):
        result = self.run_candidates(
            [issue(1, labels=["Bug"]), issue(2, labels=["feature"])], "--bug-signal", "label:bug"
        )
        self.assertEqual({c["id"]: c["bug"] for c in result["candidates"]}, {"1": True, "2": False})

    def test_no_bug_key_without_a_signal(self):
        result = self.run_candidates([issue(1)])
        self.assertNotIn("bug", result["candidates"][0])

    def test_attaches_status_and_requested_rank_fields_only(self):
        result = self.run_candidates(
            [issue(1, items={PROJECT_ID: board_values("Backlog", "P0", 4.3)})],
            "--rank-fields",
            "Priority",
        )
        self.assertEqual(result["candidates"][0]["board"], {"Status": "Backlog", "Priority": "P0"})

    def test_rows_never_carry_bodies_or_comments(self):
        result = self.run_candidates([issue(1)], "--bug-signal", "label:bug")
        self.assertEqual(
            set(result["candidates"][0]),
            {"id", "title", "labels", "assignees", "created_at", "board", "tier", "bug"},
        )

    def test_items_from_another_project_are_ignored(self):
        result = self.run_candidates([issue(8, items={OTHER_PROJECT_ID: board_values("Done")})])
        self.assertEqual(self.tiers(result), {"8": 1})
        self.assertIsNone(result["candidates"][0]["board"])

    def test_assignee_filter_keeps_unassigned_and_mine_case_insensitively(self):
        nodes = [
            issue(1, assignees=[]),
            issue(2, assignees=["Me"]),
            issue(3, assignees=["someone"]),
            issue(4, assignees=["someone", "me"]),
        ]
        self.assertEqual(sorted(self.tiers(self.run_candidates(nodes, "--me", "me"))), ["1", "2", "4"])

    def test_paginates_and_reports_truncation_at_the_limit(self):
        fake = FakeGh(
            issue_pages=[
                issues_page([issue(1), issue(2)], has_next=True, cursor="c1"),
                issues_page([issue(3), issue(4)], has_next=True, cursor="c2"),
            ]
        )
        result = self.run_cmd(fake, ["candidates", "--limit", "3"])
        self.assertEqual(sorted(self.tiers(result)), ["1", "2", "3"])
        self.assertTrue(result["truncated"])
        self.assertEqual([a for a in fake.calls[2] if a.startswith("cursor=")], ["cursor=c1"])

    def test_complete_scan_is_not_truncated(self):
        self.assertFalse(self.run_candidates([issue(1)])["truncated"])

    def test_queries_never_request_bodies_or_comments(self):
        for with_projects in (True, False):
            query = self.script.issues_query(with_projects)
            self.assertNotIn("body", query)
            self.assertNotIn("comments", query)

    def test_label_only_mode_does_not_ask_for_project_fields(self):
        self.assertIn("projectItems", self.script.issues_query(True))
        self.assertNotIn("projectItems", self.script.issues_query(False))
        fake = FakeGh(issue_pages=[issues_page([issue(1)])])
        self.run_cmd(fake, ["candidates"])
        self.assertNotIn("projectItems", next(a for a in fake.calls[-1] if a.startswith("query=")))

    def test_malformed_tiers_argument_is_a_usage_error(self):
        with self.assertRaises(SystemExit):
            self.run_cmd(FakeGh(), ["candidates", "--tiers", "nope"])


class DiscoverTest(ScriptTestCase):
    def test_reports_fields_and_per_option_counts(self):
        fake = FakeGh(
            issue_pages=[
                issues_page(
                    [
                        issue(1, items={PROJECT_ID: board_values("Backlog", score=4.0)}),
                        issue(2, items={PROJECT_ID: board_values("Idea")}),
                        issue(3, items={PROJECT_ID: board_values("Idea")}),
                        issue(4),
                    ]
                )
            ],
            projects=[BOARD],
        )
        result = self.run_cmd(fake, ["discover"])
        project = result["projects"][0]
        self.assertEqual(result["status"], "ok")
        self.assertEqual(project["id"], PROJECT_ID)
        self.assertEqual(project["readme"], "Bugs first, then by Score.")
        self.assertEqual(project["open_issues_on_board"], 3)
        self.assertEqual(project["open_issues_total"], 4)
        self.assertEqual(project["option_counts"]["Status"], {"Idea": 2, "Backlog": 1, "Done": 0})
        names = [f["name"] for f in project["fields"]]
        self.assertEqual(names, ["Title", "Status", "Score"])
        self.assertEqual(project["fields"][1]["options"], ["Idea", "Backlog", "Done"])
        self.assertEqual(project["fields"][1]["option_ids"], {"Idea": "o1", "Backlog": "o2", "Done": "o3"})
        self.assertEqual(project["fields"][2]["type"], "number")
        self.assertEqual(result["labels"], [])

    def test_no_linked_project_is_structural_and_still_reports_labels(self):
        fake = FakeGh(issue_pages=[issues_page([issue(1, labels=["idea", "bug"]), issue(2, labels=["bug"])])], projects=[])
        result = self.run_cmd(fake, ["discover"])
        self.assertEqual(result["status"], "no_project")
        self.assertEqual(result["projects"], [])
        self.assertEqual(result["labels"], [{"name": "bug", "open_issues": 2}, {"name": "idea", "open_issues": 1}])
        last_graphql = [c for c in fake.calls if c[:2] == ["api", "graphql"]][-1]
        self.assertNotIn("projectItems", next(a for a in last_graphql if a.startswith("query=")))

    def test_reports_every_repo_label_including_unused_ones(self):
        fake = FakeGh(
            issue_pages=[issues_page([issue(1, labels=["bug"])])],
            projects=[],
            repo_labels=["in progress", "bug", "blocked"],
        )
        result = self.run_cmd(fake, ["discover", "--repo", "acme/app"])
        self.assertEqual(result["repo_labels"], ["blocked", "bug", "in progress"])
        self.assertEqual([entry["name"] for entry in result["labels"]], ["bug"])

    def test_readme_is_truncated(self):
        long_readme = "x" * (self.script.README_LIMIT + 500)
        fake = FakeGh(issue_pages=[issues_page([])], projects=[{**BOARD, "readme": long_readme}])
        result = self.run_cmd(fake, ["discover"])
        self.assertEqual(len(result["projects"][0]["readme"]), self.script.README_LIMIT)

    def test_closed_projects_do_not_count(self):
        fake = FakeGh(issue_pages=[issues_page([])], projects=[{**BOARD, "closed": True}])
        self.assertEqual(self.run_cmd(fake, ["discover"])["status"], "no_project")

    def test_repo_flag_skips_repo_lookup(self):
        fake = FakeGh(issue_pages=[issues_page([])], projects=[])
        self.run_cmd(fake, ["discover", "--repo", "acme/app"])
        self.assertNotIn(["repo", "view", "--json", "owner,name"], fake.calls)


def item_payload(issue_node, items=()):
    return {
        "data": {
            "repository": {
                "issue": issue_node
                and {
                    "id": "I_node",
                    "projectItems": {"nodes": [{"id": i, "project": {"id": p}} for p, i in items]},
                }
            }
        }
    }


ADDED = {"data": {"addProjectV2ItemById": {"item": {"id": "PVTI_new"}}}}
UPDATED = {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "x"}}}}


class TransitionTest(ScriptTestCase):
    PROJECT = ["--project-id", PROJECT_ID, "--field-id", "F_status", "--option-id", "O_prog"]
    BASE = ["transition", "--issue", "42", "--repo", "acme/app"]

    def run_transition(self, argv, items=(), issue_exists=True, edit=(0, "", "")):
        fake = FakeGh(
            projects=[],
            edit=edit,
            mutations={
                "issue(number": item_payload(issue_exists, items),
                "addProjectV2ItemById": ADDED,
                "updateProjectV2ItemFieldValue": UPDATED,
            },
        )
        return fake, self.run_cmd(fake, self.BASE + argv)

    def graphql_calls(self, fake):
        return [c for c in fake.calls if c[:2] == ["api", "graphql"]]

    def test_updates_the_existing_item(self):
        fake, result = self.run_transition(self.PROJECT, items=[(PROJECT_ID, "PVTI_old")])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["applied"]["project"], {"status": "ok", "item_id": "PVTI_old", "added": False})
        self.assertEqual(len(self.graphql_calls(fake)), 2, "lookup then update, no add")
        for expected in ("item=PVTI_old", "field=F_status", "option=O_prog", "project=" + PROJECT_ID):
            self.assertIn(expected, fake.calls[-1])

    def test_ignores_items_on_other_projects(self):
        _, result = self.run_transition(self.PROJECT, items=[(OTHER_PROJECT_ID, "PVTI_other")])
        self.assertEqual(result["status"], "not_on_board")

    def test_missing_item_is_not_added_without_the_flag(self):
        fake, result = self.run_transition(self.PROJECT)
        self.assertEqual(result["status"], "not_on_board")
        self.assertEqual(len(self.graphql_calls(fake)), 1, "lookup only, no mutation")

    def test_missing_item_is_added_then_updated_with_the_flag(self):
        fake, result = self.run_transition(self.PROJECT + ["--add-if-missing"])
        self.assertEqual(result["applied"]["project"]["item_id"], "PVTI_new")
        self.assertTrue(result["applied"]["project"]["added"])
        self.assertIn("content=I_node", fake.calls[-2])
        self.assertIn("item=PVTI_new", fake.calls[-1])

    def test_issue_number_is_sent_as_an_integer(self):
        fake, _ = self.run_transition(self.PROJECT, items=[(PROJECT_ID, "PVTI_old")])
        lookup = fake.calls[0]
        self.assertEqual(lookup[lookup.index("number=42") - 1], "-F")

    def test_unknown_issue(self):
        _, result = self.run_transition(self.PROJECT, issue_exists=False)
        self.assertEqual(result["status"], "no_issue")

    def test_label_swap_without_a_project(self):
        fake, result = self.run_transition(["--add-labels", '["in progress"]', "--remove-labels", '["ready","backlog"]'])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(list(result["applied"]), ["labels"])
        self.assertEqual(self.graphql_calls(fake), [])
        edit = next(c for c in fake.calls if c[:2] == ["issue", "edit"])
        self.assertEqual(edit[2:4], ["42", "--repo"])
        self.assertIn("in progress", edit)
        self.assertEqual(edit.count("--remove-label"), 2)

    def test_project_and_labels_are_both_applied(self):
        _, result = self.run_transition(
            self.PROJECT + ["--add-labels", '["in progress"]'], items=[(PROJECT_ID, "PVTI_old")]
        )
        self.assertEqual(list(result["applied"]), ["project", "labels"])

    def test_a_missing_label_is_reported_and_earlier_parts_are_kept(self):
        _, result = self.run_transition(
            self.PROJECT + ["--add-labels", '["nope"]'],
            items=[(PROJECT_ID, "PVTI_old")],
            edit=(1, "", "failed to update: 'nope' not found"),
        )
        self.assertEqual(result["status"], "no_label")
        self.assertEqual(list(result["applied"]), ["project"])

    def test_a_project_failure_stops_before_touching_labels(self):
        fake, result = self.run_transition(self.PROJECT + ["--add-labels", '["x"]'])
        self.assertEqual(result["status"], "not_on_board")
        self.assertFalse([c for c in fake.calls if c[:2] == ["issue", "edit"]])

    def test_requires_at_least_one_part(self):
        with self.assertRaises(SystemExit):
            self.run_cmd(FakeGh(), self.BASE)

    def test_project_part_needs_field_and_option(self):
        with self.assertRaises(SystemExit):
            self.run_cmd(FakeGh(), self.BASE + ["--project-id", PROJECT_ID])


class FailureClassificationTest(ScriptTestCase):
    def status_for(self, stderr):
        fake = FakeGh(fail=(1, "", stderr))
        return self.run_cmd(fake, ["discover", "--repo", "acme/app"])["status"]

    def test_missing_project_scope(self):
        self.assertEqual(
            self.status_for("your token has not been granted the required scopes: [read:project]"),
            "no_scope",
        )

    def test_insufficient_scopes_error_type(self):
        self.assertEqual(self.status_for('{"type":"INSUFFICIENT_SCOPES"}'), "no_scope")

    def test_logged_out(self):
        self.assertEqual(
            self.status_for("To get started with GitHub CLI, please run:  gh auth login"),
            "no_auth",
        )

    def test_repository_not_on_github(self):
        self.assertEqual(
            self.status_for("Could not resolve to a Repository with the name 'a/b'."),
            "no_repo",
        )

    def test_anything_else_is_transient(self):
        self.assertEqual(self.status_for("HTTP 502: Bad Gateway"), "transient")

    def test_missing_gh_binary(self):
        with mock.patch.object(self.script.subprocess, "run", side_effect=FileNotFoundError):
            result = self.run_main(["discover", "--repo", "acme/app"])
        self.assertEqual(result["status"], "no_gh")

    def test_non_json_output_is_transient(self):
        with mock.patch.object(self.script, "run_gh", lambda args: (0, "<html>", "")):
            result = self.run_main(["discover", "--repo", "acme/app"])
        self.assertEqual(result["status"], "transient")


class SkillContractTest(unittest.TestCase):
    """next-ticket must tell the model how to run the script and every outcome."""

    def setUp(self):
        self.text = (REPO_ROOT / "skills" / "next-ticket" / "SKILL.md").read_text()

    def test_script_is_addressed_relative_to_the_skill(self):
        self.assertIn("`gh_issues.py` in the same directory as this SKILL.md", self.text)

    def test_every_script_status_is_handled_in_the_skill(self):
        for status in ("no_project", "no_scope", "no_auth", "no_gh", "no_repo", "transient"):
            with self.subTest(status=status):
                self.assertIn("`%s`" % status, self.text)

    def test_legacy_candidate_entries_are_rediscovered(self):
        text = self.text
        self.assertRegex(text, r"entry without that version is a legacy filter")
        self.assertIn("Cached candidate filter predates tiers; rediscovering.", text)
        self.assertIn("Bump the version whenever the shape of this entry changes", text)

    def test_candidate_and_rank_cache_shapes_are_documented(self):
        for key in ('"version": 2', '"provider": "github_project"', '"tiers"', '"exclude"', '"bugs"', '"bug_signal"', '"rank"'):
            with self.subTest(key=key):
                self.assertIn(key, self.text)


if __name__ == "__main__":
    unittest.main()
