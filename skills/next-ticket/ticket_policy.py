#!/usr/bin/env python3
"""Read and export a project's saved ticket choices.

The ticket skills remember the ticket system and per-state choices (candidate
tiers, rank fields, and the in_progress, in_review, done, and filed updates) in
`next-ticket-config.json` in the system temp directory. That file does not
survive a fresh cloud run or reach a teammate. A project can commit the same
choices as `.agents/ticket-policy.json` at its repository root, which wins over
the cache.

Two subcommands print one JSON object and exit 0, so the caller branches on the
`status` key:

  read    The effective system and states, with where each value came from
          (`policy` or `cache`), the cache and policy paths, and whether the
          candidate filter is the current version, and `legacy_states`, the
          GitHub transition values an older release wrote that must be
          rediscovered once. An invalid policy file is
          reported as `invalid_policy` with the cache values still returned,
          so the caller can say so and carry on.
  export  Write the cache entry for this repository into the policy file, so
          the operator can commit it. Existing policy keys the cache does not
          hold are kept, and legacy GitHub values are not exported.

`status` is one of: ok, no_repo, invalid_policy, no_cache_entry.

The policy file holds names, option IDs, and label names only. It never holds a
URL or a token, and it is read as data.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

POLICY_RELATIVE = os.path.join(".agents", "ticket-policy.json")
CACHE_NAME = "next-ticket-config.json"
POLICY_VERSION = 1
CANDIDATE_VERSION = 2
STATE_VERSION = 2
TRANSITION_STATES = ("in_progress", "in_review", "done", "filed")


class PolicyError(Exception):
    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def repo_root(explicit):
    if explicit:
        return os.path.abspath(explicit)
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise PolicyError("no_repo", "not inside a git repository")
    return proc.stdout.strip()


def cache_path(explicit):
    return explicit or os.path.join(tempfile.gettempdir(), CACHE_NAME)


def load_json(path):
    try:
        with open(path) as handle:
            return json.load(handle)
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as err:
        raise PolicyError("invalid_policy", "%s: %s" % (path, err))


def load_policy(path):
    policy = load_json(path)
    if policy is None:
        return None
    problem = None
    if not isinstance(policy, dict):
        problem = "the file must hold a JSON object"
    elif policy.get("version") != POLICY_VERSION:
        problem = "version must be %d" % POLICY_VERSION
    elif "system" in policy and not isinstance(policy["system"], str):
        problem = "system must be a string"
    elif not isinstance(policy.get("states", {}), dict):
        problem = "states must be an object"
    elif any(not isinstance(v, dict) for v in policy.get("states", {}).values()):
        problem = "every state must be an object"
    if problem:
        raise PolicyError("invalid_policy", "%s: %s" % (path, problem))
    return policy


def cache_entry(path, root):
    """The cache entry for this root, normalized to {"system", "states"}."""
    try:
        cache = load_json(path)
    except PolicyError:
        cache = None  # a damaged temp cache must not block a committed policy
    entry = cache.get(root) if isinstance(cache, dict) else None
    if isinstance(entry, str):
        return {"system": entry, "states": {}}
    if isinstance(entry, dict):
        return {"system": entry.get("system"), "states": entry.get("states") or {}}
    return None


def effective(policy, entry):
    system, system_source = None, None
    if policy and policy.get("system"):
        system, system_source = policy["system"], "policy"
    elif entry and entry.get("system"):
        system, system_source = entry["system"], "cache"
    states = {}
    for source, holder in (("cache", entry), ("policy", policy)):
        for name, value in ((holder or {}).get("states") or {}).items():
            states[name] = {"value": value, "source": source}
    return {"system": system, "system_source": system_source, "states": states}


def legacy_states(system, states):
    """GitHub transition values written before workflow labels counted.

    An older release cached plain GitHub Issues as unsupported, or stored a
    shape without the project and labels parts, so such a value is stale and
    must be rediscovered once. Values for other systems keep their meaning.
    """
    if not (system or "").lower().startswith("github"):
        return []
    return [
        name
        for name in TRANSITION_STATES
        if name in states and states[name].get("version") != STATE_VERSION
    ]


def read(args):
    root = repo_root(args.root)
    policy_file = os.path.join(root, POLICY_RELATIVE)
    cache_file = cache_path(args.cache_file)
    problem = None
    try:
        policy = load_policy(policy_file)
    except PolicyError as err:
        policy, problem = None, err.detail
    entry = cache_entry(cache_file, root)
    result = effective(policy, entry)
    candidate = result["states"].get("candidate")
    result["candidate_current"] = bool(
        candidate and candidate["value"].get("version") == CANDIDATE_VERSION
    )
    result["legacy_states"] = legacy_states(
        result["system"], {n: v["value"] for n, v in result["states"].items()}
    )
    result.update(
        {
            "status": "invalid_policy" if problem else "ok",
            "root": root,
            "policy_path": policy_file,
            "policy_present": policy is not None,
            "cache_path": cache_file,
        }
    )
    if problem:
        result["detail"] = problem
    return result


def export(args):
    root = repo_root(args.root)
    policy_file = os.path.join(root, POLICY_RELATIVE)
    entry = cache_entry(cache_path(args.cache_file), root)
    if not entry or not (entry.get("system") or entry.get("states")):
        raise PolicyError("no_cache_entry", "no saved choices for %s" % root)
    existing = load_policy(policy_file) or {}
    system = entry.get("system") or existing.get("system")
    stale = legacy_states(system, entry["states"])
    current = {n: v for n, v in entry["states"].items() if n not in stale}
    merged = {
        "version": POLICY_VERSION,
        "system": system,
        "states": {**existing.get("states", {}), **current},
    }
    merged = {k: v for k, v in merged.items() if v not in (None, {})}
    os.makedirs(os.path.dirname(policy_file), exist_ok=True)
    staging = policy_file + ".tmp"
    with open(staging, "w") as handle:
        json.dump(merged, handle, indent=2)
        handle.write("\n")
    os.replace(staging, policy_file)
    return {
        "status": "ok",
        "path": policy_file,
        "keys": sorted(merged.get("states", {})),
        "skipped_legacy": stale,
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("read", "export"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--root", help="repository root; defaults to the current repository")
        cmd.add_argument("--cache-file", help="override the cache path (tests)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    handler = {"read": read, "export": export}[args.command]
    try:
        result = handler(args)
    except PolicyError as err:
        result = {"status": err.status, "detail": err.detail}
    json.dump(result, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
