#!/usr/bin/env python3
"""Read a GitHub repository's open issues, labels, and Projects (v2) data.

Three subcommands print one JSON object and exit 0, so the caller branches on the
`status` key instead of the exit code:

  discover    Open-issue label counts, plus the projects linked to the repository
              with their fields, README, and how many open issues sit in each
              field option.
  candidates  Open issues that are available to start. Each row carries a `tier`
              (1 is worked first), an optional `bug` flag, and the project's
              field values when a project is used. Bodies and comments are never
              requested.
  transition  Change one issue's workflow state: set a project single select
              field (for example Status) on its project item, adding the issue
              to the project first when `--add-if-missing` is given, and/or add
              and remove labels. Either part alone is valid. Used when a ticket
              is claimed, put up for review, finished, or filed.

A row's signals are its project Status value and its labels (as `label:<name>`).
`--exclude` lists signals that mean never work this. `--tiers` is an ordered list
of signal lists; the token "(none)" matches a row with no listed signal. A row
whose Status is listed nowhere is hidden and counted in `unclassified_states`.

`status` is one of: ok, no_project, no_gh, no_auth, no_scope, no_repo,
no_issue, not_on_board, no_label, transient. The first two and no_repo describe the
repository (structural). The others describe this machine, this moment, or one
issue and should not be cached.

Access comes only from the authenticated `gh` CLI. No token is read or printed.
"""

import argparse
import json
import subprocess
import sys

PAGE_SIZE = 100
DEFAULT_LIMIT = 1000
README_LIMIT = 4000
LABEL_LIMIT = 60
NO_SIGNAL = "(none)"

VALUE_FRAGMENTS = """
  __typename
  ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
  ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
  ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
"""

PROJECT_ITEMS = """
        projectItems(first: 10) {
          nodes {
            project { id }
            fieldValues(first: 30) { nodes { %s } }
          }
        }""" % VALUE_FRAGMENTS


def issues_query(with_projects):
    """The open-issue page query. Project fields need the `project` token scope."""
    return """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(states: OPEN, first: %d, after: $cursor, orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        createdAt
        labels(first: 20) { nodes { name } }
        assignees(first: 10) { nodes { login } }%s
      }
    }
  }
}
""" % (PAGE_SIZE, PROJECT_ITEMS if with_projects else "")


PROJECTS_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    projectsV2(first: 20) {
      nodes {
        id
        number
        title
        closed
        readme
        fields(first: 50) {
          nodes {
            __typename
            ... on ProjectV2Field { id name dataType }
            ... on ProjectV2SingleSelectField { id name options { id name } }
            ... on ProjectV2IterationField { id name }
          }
        }
      }
    }
  }
}
"""


ITEM_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      id
      projectItems(first: 20) { nodes { id project { id } } }
    }
  }
}
"""

ADD_ITEM = """
mutation($project: ID!, $content: ID!) {
  addProjectV2ItemById(input: {projectId: $project, contentId: $content}) { item { id } }
}
"""

SET_OPTION = """
mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $project, itemId: $item, fieldId: $field, value: {singleSelectOptionId: $option}
  }) { projectV2Item { id } }
}
"""


class GhError(Exception):
    """A `gh` failure already classified into a `status` value."""

    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def run_gh(args):
    """Run `gh` and return (returncode, stdout, stderr). Tests replace this."""
    try:
        proc = subprocess.run(
            ["gh", *args], capture_output=True, text=True, timeout=120
        )
    except FileNotFoundError:
        raise GhError("no_gh", "the gh CLI is not installed")
    except subprocess.TimeoutExpired:
        raise GhError("transient", "gh timed out")
    return proc.returncode, proc.stdout, proc.stderr


def classify_failure(stderr):
    text = stderr.lower()
    if "required scope" in text or "insufficient_scopes" in text or "read:project" in text:
        return "no_scope"
    if "gh auth login" in text or "not logged in" in text or "authentication" in text:
        return "no_auth"
    if "could not resolve to a repository" in text or "not a git repository" in text:
        return "no_repo"
    if "no git remotes" in text or "none of the git remotes" in text:
        return "no_repo"
    return "transient"


def gh_json(args):
    code, out, err = run_gh(args)
    if code != 0:
        raise GhError(classify_failure(err), err.strip() or "gh failed")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        raise GhError("transient", "gh returned output that is not JSON")


def graphql(query, variables):
    args = ["api", "graphql", "-f", "query=" + query]
    for key, value in variables.items():
        if value is not None:
            flag = "-F" if isinstance(value, int) else "-f"
            args += [flag, "%s=%s" % (key, value)]
    payload = gh_json(args)
    if payload.get("errors"):
        message = json.dumps(payload["errors"])
        raise GhError(classify_failure(message), message)
    return payload["data"]


def resolve_repo(repo):
    if repo:
        owner, _, name = repo.partition("/")
        if not name:
            raise GhError("no_repo", "--repo must look like OWNER/NAME")
        return owner, name
    data = gh_json(["repo", "view", "--json", "owner,name"])
    return data["owner"]["login"], data["name"]


def field_values(nodes):
    """Flatten a project item's field values into {field name: value}."""
    values = {}
    for node in nodes:
        if not node:
            continue
        field = (node.get("field") or {}).get("name")
        if not field:
            continue
        kind = node.get("__typename")
        if kind == "ProjectV2ItemFieldSingleSelectValue":
            values[field] = node["name"]
        elif kind == "ProjectV2ItemFieldNumberValue":
            values[field] = node["number"]
        elif kind == "ProjectV2ItemFieldTextValue":
            values[field] = node["text"]
    return values


def scan_open_issues(owner, name, limit, with_projects):
    """Return (issues, truncated). Each issue carries its per-project field values."""
    issues = []
    cursor = None
    while True:
        data = graphql(issues_query(with_projects), {"owner": owner, "name": name, "cursor": cursor})
        page = data["repository"]["issues"]
        for node in page["nodes"]:
            issues.append(
                {
                    "id": str(node["number"]),
                    "title": node["title"],
                    "labels": [label["name"] for label in node["labels"]["nodes"]],
                    "assignees": [a["login"] for a in node["assignees"]["nodes"]],
                    "created_at": node["createdAt"],
                    "boards": {
                        item["project"]["id"]: field_values(item["fieldValues"]["nodes"])
                        for item in node.get("projectItems", {}).get("nodes", [])
                        if item and item.get("project")
                    },
                }
            )
        if len(issues) >= limit:
            return issues[:limit], page["pageInfo"]["hasNextPage"] or len(issues) > limit
        if not page["pageInfo"]["hasNextPage"]:
            return issues, False
        cursor = page["pageInfo"]["endCursor"]


def describe_field(node):
    entry = {"id": node.get("id"), "name": node.get("name")}
    if node.get("__typename") == "ProjectV2SingleSelectField":
        entry["options"] = [o["name"] for o in node["options"]]
        entry["option_ids"] = {o["name"]: o["id"] for o in node["options"]}
    elif node.get("dataType"):
        entry["type"] = node["dataType"].lower()
    return entry


def label_counts(issues):
    counts = {}
    for issue in issues:
        for label in issue["labels"]:
            counts[label] = counts.get(label, 0) + 1
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return [{"name": n, "open_issues": c} for n, c in ranked[:LABEL_LIMIT]]


def repo_labels(owner, name):
    """Every label the repository defines, including ones no open issue uses yet."""
    try:
        found = gh_json(["label", "list", "--repo", "%s/%s" % (owner, name), "--limit", "200", "--json", "name"])
    except GhError:
        return []
    return sorted(entry["name"] for entry in found)


def summarize_project(project, issues):
    fields = [describe_field(f) for f in project["fields"]["nodes"] if f and f.get("name")]
    on_board = [i["boards"][project["id"]] for i in issues if project["id"] in i["boards"]]
    counts = {}
    for field in fields:
        if "options" not in field:
            continue
        tally = {option: 0 for option in field["options"]}
        for values in on_board:
            if values.get(field["name"]) in tally:
                tally[values[field["name"]]] += 1
        counts[field["name"]] = tally
    return {
        "id": project["id"],
        "number": project["number"],
        "title": project["title"],
        "readme": (project.get("readme") or "")[:README_LIMIT],
        "fields": fields,
        "open_issues_on_board": len(on_board),
        "open_issues_total": len(issues),
        "option_counts": counts,
    }


def discover(args):
    owner, name = resolve_repo(args.repo)
    meta = graphql(PROJECTS_QUERY, {"owner": owner, "name": name})
    projects = [p for p in meta["repository"]["projectsV2"]["nodes"] if p and not p["closed"]]
    issues, truncated = scan_open_issues(owner, name, args.limit, with_projects=bool(projects))
    return {
        "status": "ok" if projects else "no_project",
        "repo": "%s/%s" % (owner, name),
        "truncated": truncated,
        "labels": label_counts(issues),
        "repo_labels": repo_labels(owner, name),
        "projects": [summarize_project(p, issues) for p in projects],
    }


def split_csv(value):
    return [part.strip() for part in value.split(",") if part.strip()] if value else []


def parse_signal_lists(value, flag):
    """Parse a JSON array argument, or exit with a usage error."""
    try:
        parsed = json.loads(value) if value else []
    except json.JSONDecodeError:
        parsed = None
    if not isinstance(parsed, list):
        raise SystemExit("%s must be a JSON array" % flag)
    return parsed


def signals_of(issue, status):
    found = {"label:" + label.lower() for label in issue["labels"]}
    if status is not None:
        found.add(status.lower())
    return found


def tier_of(found, status, tiers, excluded):
    """Return the 1-based tier, or None when the row is hidden. No tiers puts every row in tier 1."""
    if found & excluded:
        return None
    if not tiers:
        return 1
    for number, tier in enumerate(tiers, start=1):
        if found & tier:
            return number
    if status is not None:
        return None
    for number, tier in enumerate(tiers, start=1):
        if NO_SIGNAL in tier:
            return number
    return None


def is_bug(issue, values, signal):
    if signal.startswith("label:"):
        return signal[len("label:"):].lower() in {label.lower() for label in issue["labels"]}
    field, _, expected = signal.partition("=")
    return values is not None and str(values.get(field, "")).lower() == expected.lower()


def candidates(args):
    tiers = [{s.lower() for s in tier} for tier in parse_signal_lists(args.tiers, "--tiers")]
    excluded = {s.lower() for s in parse_signal_lists(args.exclude, "--exclude")}
    owner, name = resolve_repo(args.repo)
    issues, truncated = scan_open_issues(owner, name, args.limit, with_projects=bool(args.project_id))
    rank_fields = split_csv(args.rank_fields)
    me = args.me.lower() if args.me else None
    rows = []
    unclassified = {}
    for issue in issues:
        if me is not None and issue["assignees"]:
            if me not in {a.lower() for a in issue["assignees"]}:
                continue
        values = issue["boards"].get(args.project_id) if args.project_id else None
        status = values.get(args.status_field) if values else None
        found = signals_of(issue, status)
        tier = tier_of(found, status, tiers, excluded)
        if tier is None:
            if status is not None and not found & excluded:
                unclassified[status] = unclassified.get(status, 0) + 1
            continue
        board = None
        if values is not None:
            keep = [args.status_field, *rank_fields] if rank_fields else list(values)
            board = {k: values[k] for k in keep if k in values}
        row = {k: v for k, v in issue.items() if k != "boards"}
        row["board"] = board
        row["tier"] = tier
        if args.bug_signal:
            row["bug"] = is_bug(issue, values, args.bug_signal)
        rows.append(row)
    return {
        "status": "ok",
        "repo": "%s/%s" % (owner, name),
        "truncated": truncated,
        "unclassified_states": unclassified,
        "candidates": rows,
    }


def set_project_status(args, owner, name):
    data = graphql(ITEM_QUERY, {"owner": owner, "name": name, "number": args.issue})
    issue = data["repository"]["issue"]
    if not issue:
        return {"status": "no_issue", "detail": "no issue #%d in %s/%s" % (args.issue, owner, name)}
    item_id = next(
        (i["id"] for i in issue["projectItems"]["nodes"] if i and i["project"]["id"] == args.project_id),
        None,
    )
    added = False
    if item_id is None:
        if not args.add_if_missing:
            return {"status": "not_on_board", "detail": "issue #%d is not on the project" % args.issue}
        added_item = graphql(ADD_ITEM, {"project": args.project_id, "content": issue["id"]})
        item_id = added_item["addProjectV2ItemById"]["item"]["id"]
        added = True
    graphql(
        SET_OPTION,
        {"project": args.project_id, "item": item_id, "field": args.field_id, "option": args.option_id},
    )
    return {"status": "ok", "item_id": item_id, "added": added}


def edit_labels(args, owner, name):
    add = parse_signal_lists(args.add_labels, "--add-labels")
    remove = parse_signal_lists(args.remove_labels, "--remove-labels")
    cmd = ["issue", "edit", str(args.issue), "--repo", "%s/%s" % (owner, name)]
    for label in add:
        cmd += ["--add-label", label]
    for label in remove:
        cmd += ["--remove-label", label]
    code, _, err = run_gh(cmd)
    if code != 0:
        status = "no_label" if "not found" in err.lower() else classify_failure(err)
        return {"status": status, "detail": err.strip() or "gh issue edit failed"}
    return {"status": "ok", "added": add, "removed": remove}


def transition(args):
    wants_project = bool(args.project_id)
    wants_labels = bool(args.add_labels or args.remove_labels)
    if wants_project and not (args.field_id and args.option_id):
        raise SystemExit("--project-id needs --field-id and --option-id")
    if not (wants_project or wants_labels):
        raise SystemExit("transition needs a project part, a label part, or both")
    parse_signal_lists(args.add_labels, "--add-labels")
    parse_signal_lists(args.remove_labels, "--remove-labels")
    owner, name = resolve_repo(args.repo)
    applied = {}
    for part, wanted, step in (
        ("project", wants_project, set_project_status),
        ("labels", wants_labels, edit_labels),
    ):
        if not wanted:
            continue
        result = step(args, owner, name)
        if result["status"] != "ok":
            return {**result, "applied": applied}
        applied[part] = result
    return {"status": "ok", "applied": applied}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("discover", "candidates", "transition"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--repo", help="OWNER/NAME; defaults to the current repository")
        if name != "transition":
            cmd.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="max open issues scanned")
    cmd = sub.choices["transition"]
    cmd.add_argument("--issue", type=int, required=True, help="issue number")
    cmd.add_argument("--project-id", help="project node id from discover; needs --field-id and --option-id")
    cmd.add_argument("--field-id", help="single select field id from discover")
    cmd.add_argument("--option-id", help="option id from the field's option_ids")
    cmd.add_argument("--add-if-missing", action="store_true", help="add the issue to the project first")
    cmd.add_argument("--add-labels", help='JSON array of existing labels to add, e.g. ["in progress"]')
    cmd.add_argument("--remove-labels", help="JSON array of labels to remove")
    cmd = sub.choices["candidates"]
    cmd.add_argument("--project-id", help="project node id from discover; omit to use labels only")
    cmd.add_argument("--status-field", default="Status")
    cmd.add_argument("--tiers", help='JSON array of signal lists, worked in order, e.g. [["Ready","(none)"],["Backlog"]]')
    cmd.add_argument("--exclude", help='JSON array of signals that mean never work this, e.g. ["Idea","label:blocked"]')
    cmd.add_argument("--rank-fields", help="comma list of extra project fields to attach to each row")
    cmd.add_argument("--bug-signal", help='"Field=Value" on the project or "label:<name>"; adds a `bug` flag')
    cmd.add_argument("--me", help="keep only issues that are unassigned or assigned to this login")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    handler = {"discover": discover, "candidates": candidates, "transition": transition}[args.command]
    try:
        result = handler(args)
    except GhError as err:
        result = {"status": err.status, "detail": err.detail}
    json.dump(result, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
