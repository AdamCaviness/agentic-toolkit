---
name: update-deps
description: Updates project dependencies. Checks open bot PRs for CVE patches, applies safe minor/patch updates, and researches/fixes breaking changes for major bumps. Optional scope (frontend|backend|infra|all) and major flag.
argument-hint: "[<scope>[|<scope>...]] [major]"
---

# Update Dependencies

You are a **hybrid orchestrator**. Steps 1 through 4 are linear discovery and safe-update work. Steps 5 and 6 run parallel research sub-agents (one per major bump dependency). Step 7 applies major bumps sequentially. Steps 8 and 9 finalize and summarize.

## Arguments

Parse the argument string passed to this skill by splitting on whitespace.

- Any token that contains `|` or exactly matches a known scope name (`frontend`, `backend`, `infra`, `all`) is a **scope specifier**.
- The token `major` enables **full-major mode**, which upgrades all deps including non-CVE major bumps.
- No argument defaults to scope `all` without the major flag.

Examples:

```
/update-deps                          # all scopes, CVE majors + safe minor/patch
/update-deps frontend                 # scope to frontend only
/update-deps backend|infra            # multiple scopes
/update-deps major                    # all scopes, upgrade ALL deps including majors
/update-deps frontend major           # scoped + all majors
```

## Prerequisites

Verify you are in a git repo. If not, tell the user and stop.

Verify you are NOT on `main` or `master`. If you are, tell the user to create a feature branch and stop.

## Branch Naming

Branch name: `chore/update-deps` for all-scope runs, `chore/update-deps-<scope>` for a single named scope (e.g., `chore/update-deps-frontend`). For multi-scope runs, use `chore/update-deps`.

Check whether the branch already exists:

- If it exists and is **clean** (no uncommitted changes), check it out and reuse it.
- If it exists and is **dirty** (uncommitted changes present), warn the user and stop. Do not overwrite in-progress work.
- If it does not exist, create it from the current branch.

## Step 1: Detect Project Structure and Scope Mapping

Explore the repository to identify all dependency manifests. Classify each manifest into a scope using these heuristics:

- **frontend**: `package.json` files whose `dependencies` include a UI framework (React, Vue, Angular, Svelte, Next, Nuxt, Remix, Vite, Webpack) or whose path includes `web`, `client`, `ui`, `frontend`, `app`.
- **backend**: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle` files whose path or deps indicate server-side code (`express`, `fastapi`, `actix`, `gin`, `spring`, workers, APIs).
- **infra**: Dockerfiles, `docker-compose*.yml`, Terraform `.tf` files, Kubernetes manifests, CI/CD config files (`.github/workflows`, `.gitlab-ci.yml`, `buildkite.yml`), IaC tool configs.

In monorepos, classify each manifest independently.

If the user supplied a scope argument, filter the manifest list to matching scopes only. Manifests that do not match the requested scope are excluded from all subsequent steps.

Print the manifest map:

```
Detected manifests:
  packages/web/package.json        -> frontend
  packages/api/package.json        -> backend
  infra/terraform/versions.tf      -> infra
  docker-compose.yml               -> infra
```

If no manifests match the requested scope, tell the user and stop.

## Step 2: Check Open PRs for Automated CVE Patches

Using whatever CLI is available (e.g., `gh pr list`), fetch open PRs authored by known dependency bots: `dependabot`, `renovate`, `snyk-bot`, `greenkeeper`.

For each bot PR:

1. Extract the dependency name and target version from the PR title or body.
2. Note the CVE or security advisory ID if referenced.
3. Determine whether the version bump is patch, minor, or major relative to the currently installed version.

Build the **CVE-required update list**. Every dependency on this list MUST be updated regardless of bump magnitude.

Do NOT merge, close, or comment on any bot PR. The bots will auto-close their PRs when the dependency version is satisfied.

If no bot PRs are found, proceed normally. The CVE-required list is simply empty.

## Step 3: List All Outdated Dependencies

For each in-scope manifest, run the appropriate package manager command to list outdated dependencies with current version, available version, and bump type. Common commands:

- npm: `npm outdated --json`
- yarn: `yarn outdated --json`
- pnpm: `pnpm outdated`
- pip: `pip list --outdated`
- cargo: `cargo outdated`
- go: `go list -u -m all`
- maven/gradle: use the versions plugin

Classify every outdated dep into exactly one bucket:

| Bucket | Criteria | Behavior |
|---|---|---|
| **CVE-required** | Referenced by a bot PR with a security advisory | MUST update, even if major bump |
| **Safe** | Minor or patch bump, not CVE-related | Updated automatically in a batch |
| **Major (optional)** | Major bump, not CVE-required | Only updated when `major` flag is set |

If a dep appears in both the CVE-required list and would qualify for the major-optional bucket, place it in CVE-required and process it once.

Print the classification:

```
Dependency audit (backend scope):
  CVE-required (2):
    express 4.18.2 -> 5.1.0 (major) -- CVE-2024-XXXXX via dependabot PR #87
    lodash 4.17.20 -> 4.17.21 (patch) -- CVE-2021-XXXXX via dependabot PR #92

  Safe updates (8):
    axios 1.6.0 -> 1.7.2 (minor)
    dotenv 16.3.1 -> 16.4.1 (minor)
    ...

  Major (skipped, use 'major' flag to include) (3):
    pg 8.11.0 -> 9.0.0 (major)
    ...
```

If no outdated deps are found and no bot PRs exist, tell the user everything is up to date and stop. Do not create a branch.

Lockfile-only updates are valid. Include them in safe updates.

## Step 4: Apply Safe Updates

Apply all safe (minor/patch, non-CVE) dependencies in a single batch per manifest.

1. Run the appropriate update command for each manifest (e.g., `npm update`, `pip install --upgrade`, `cargo update`).
2. Run the project's full test suite.
3. If tests pass, commit all safe updates in one commit per manifest, listing the updated deps:

```
Update minor/patch dependencies

- axios 1.6.0 -> 1.7.2
- dotenv 16.3.1 -> 16.4.1
- typescript 5.3.2 -> 5.3.3
```

4. If tests fail, isolate the cause: revert deps one at a time until tests pass, identify the offending dep, exclude it from the batch, and retry the batch without it. Report any dep that cannot be safely updated as needing manual attention.

**Workspace and monorepo note**: When multiple manifests share a lockfile (npm/yarn workspaces, pnpm workspaces), update at the workspace root to avoid lockfile conflicts.

## Step 5: Build Research Cache

**Skip Steps 5 through 7 entirely if there are zero major bumps to process** (zero CVE-required major bumps and either no major-optional deps or the `major` flag was not set).

Derive a project identity: use the project root directory name plus a short hash of the root path to produce a unique `PROJECT_ID` in the form `<project-name>-<hash>`.

Create a cache directory at `<temp>/update-deps-<PROJECT_ID>`. Remove and recreate it if it already exists.

Write two files to the cache:

**`<cache>/research-requests.json`**: a JSON array, one object per major bump dep to research:

```json
[
  {
    "package": "express",
    "current_version": "4.18.2",
    "target_version": "5.1.0",
    "reason": "cve",
    "cve_id": "CVE-2024-XXXXX",
    "manifest": "packages/api/package.json",
    "scope": "backend"
  }
]
```

`reason` is `"cve"` for CVE-required updates and `"major"` for major-optional updates.

**`<cache>/project-map.md`**: a factual guide to the codebase trimmed to the in-scope manifests and their surrounding code. No file contents, only pointers. Include:

- Tech stack (language, framework, test runner, extracted from manifests)
- Directory structure (pruned tree, excluding `.git` and dependency directories)
- Key files (path plus one-line description of purpose)
- Test patterns (where tests live, how to run them)
- Conventions from CLAUDE.md that affect dependency usage

## Step 6: Deploy Parallel Research Sub-Agents

Read `<cache>/research-requests.json`. Spawn one sub-agent per entry, **all in a single message** so they execute concurrently. Use `description: "Research <package> upgrade"` for each.

For each entry, construct a prompt by substituting the placeholders in the Sub-Agent Prompt Template below.

---

### Sub-Agent Prompt Template

```
You are a dependency upgrade researcher. Your only job is to research breaking changes and scan the codebase for affected code. You do NOT modify any code. You write a structured change plan to disk.

## Assignment

- Package: {PACKAGE}
- Current version: {CURRENT_VERSION}
- Target version: {TARGET_VERSION}
- Reason: {REASON}
- CVE ID: {CVE_ID}
- Manifest: {MANIFEST}
- Cache directory: {CACHE_DIR}

## Step 1: Research Breaking Changes Online

Use WebSearch to find the official migration guide, changelog, and release notes for every version between {CURRENT_VERSION} and {TARGET_VERSION}. Do not stop at one query. Search for:

- "{PACKAGE} {TARGET_VERSION} migration guide"
- "{PACKAGE} {TARGET_VERSION} breaking changes"
- "{PACKAGE} changelog {CURRENT_VERSION} to {TARGET_VERSION}"
- "{PACKAGE} upgrade {CURRENT_VERSION} {TARGET_VERSION}"
- GitHub release notes for the package repository

Read the actual pages, not just search result snippets. Community resources, Stack Overflow threads, and GitHub Discussions often document real-world pitfalls that official docs miss.

If a CVE ID is provided, also search for "{CVE_ID} {PACKAGE}" to understand the vulnerability and the fix.

Compile a complete list of breaking changes, deprecated APIs, renamed symbols, changed call signatures, new minimum runtime requirements, and removed features.

## Step 2: Scan the Codebase for Affected Code

Read `{CACHE_DIR}/project-map.md` to orient yourself. Then grep and read every file that imports or uses {PACKAGE}. For each affected file:

1. Note the file path and line numbers of every usage.
2. Cross-reference each usage against the breaking changes you found in Step 1.
3. Identify which usages require changes and which are unaffected.

Do not run directory listings independently. Use the project map as your guide and read specific files directly.

## Step 3: Write Change Plan

Write a JSON change plan to `{CACHE_DIR}/change-plan-{PACKAGE}.json`:

\`\`\`json
{
  "package": "{PACKAGE}",
  "current_version": "{CURRENT_VERSION}",
  "target_version": "{TARGET_VERSION}",
  "reason": "{REASON}",
  "breaking_changes": [
    {
      "description": "What changed",
      "migration": "How to fix it",
      "affected_files": ["src/file.ts:42", "src/other.ts:15"],
      "test_strategy": "What behavior to test before and after"
    }
  ],
  "deprecated_apis_used": [
    {
      "api": "old.api()",
      "replacement": "new.api()",
      "affected_files": ["src/routes/static.ts:28"]
    }
  ],
  "new_requirements": "Any new runtime or platform requirements (e.g., Node.js >= 18)",
  "estimated_risk": "low | medium | high",
  "sources": [
    "https://example.com/migration-guide"
  ]
}
\`\`\`

If there are no breaking changes that affect this codebase, `breaking_changes` and `deprecated_apis_used` may be empty arrays. Still write the file.

## Rules

- Do NOT modify any source files, manifests, lockfiles, or tests.
- Do not skip intermediate versions. Breaking changes accumulate across minor versions.
- Be specific about file paths and line numbers. Vague references are not useful.
- If the package is not found in any import or usage in the codebase, note that in `new_requirements` and set `estimated_risk` to `"low"`.
```

---

## Step 7: Sequentially Apply Each Major Bump

After all research sub-agents complete, read every `change-plan-<package>.json` file from the cache directory.

Determine application order: if two major bumps could interact (e.g., a framework and a plugin for that framework), apply the framework first. Otherwise apply in any order.

For each change plan:

### 7a. Write tests that pin current behavior

Before touching the dependency, write tests (or extend existing tests) that exercise the specific APIs and call patterns listed in `breaking_changes[].affected_files` and `deprecated_apis_used[].affected_files`. Cover the `test_strategy` described in each breaking change entry. Run the tests and confirm they pass against the current version.

### 7b. Update the dependency

Run the package manager command to update just this one dependency to the target version.

### 7c. Run the "before" tests, expect failures

Run the tests you wrote in 7a. If they fail, the breaking changes are confirmed and your tests cover the right surface. Proceed to 7d.

If all tests still pass, the breaking changes do not affect this codebase. Skip to 7f.

### 7d. Fix code according to the change plan

Apply the documented migration paths: replace deprecated APIs, adjust call signatures, update patterns. Read the source documentation URLs listed in `sources` for accuracy when the plan is ambiguous.

### 7e. Iterate until green

Run the "before" tests plus the full project test suite. Fix remaining failures. Repeat.

If you are stuck after reasonable effort, report the issue to the user with full context (which file, which test, which breaking change, what you tried). Revert the dependency bump with a commit that notes the revert reason. Do not give up silently.

### 7f. Commit

One atomic commit per dependency:

```
Update express 4.18.2 -> 5.1.0 (CVE-2024-XXXXX)

Breaking changes addressed:
- req.host -> req.hostname (proxy.ts, health.ts)
- res.sendfile() -> res.sendFile() (static.ts)

Migration guide: https://expressjs.com/en/guide/migrating-5.html
```

For non-CVE major bumps, omit the CVE reference from the subject line.

### 7g. Repeat for the next change plan

## Step 8: Final Validation

1. Run the full test suite to catch interaction effects between independently applied updates.
2. Run the project's linter and formatter (check CLAUDE.md for commands). If auto-fixes are applied, commit them separately with message `Auto-format after dependency updates`.
3. If the final test suite fails, identify which combination of updates caused the interaction and report it to the user.

## Step 9: Cleanup and Summary

Delete the cache directory and verify it is gone. If cleanup fails, investigate and retry before proceeding.

Print the final summary:

```
Dependency update complete.

Branch: chore/update-deps
Scope: backend | all
Mode: standard | major

Safe updates (1 commit):
  axios 1.6.0 -> 1.7.2, dotenv 16.3.1 -> 16.4.1, ... (8 deps)

Major updates (2 commits):
  express 4.18.2 -> 5.1.0 (CVE-2024-XXXXX) -- 3 breaking changes addressed
  pg 8.11.0 -> 9.0.0 -- 1 breaking change addressed

Skipped (manual attention needed):
  socket.io 4.6.0 -> 5.0.0 -- test failure in websocket.test.ts:44, see details above

Bot PRs that should auto-close:
  #87 (dependabot: express)
  #92 (dependabot: lodash)

All tests passing. Ready for review.
```

Never push, create PRs, or merge. The user reviews first.

## Edge Cases

**No outdated deps**: If discovery finds nothing to update and no bot PRs exist, tell the user and stop. Do not create a branch.

**No bot PRs but outdated deps exist**: Proceed normally. The CVE-required list is empty.

**Mixed CVE and major flag**: If a CVE-required dep also appears on the all-majors list, process it once, with CVE noted in the commit message.

**Lockfile-only updates**: Valid. Include them in safe updates.

**Workspaces and monorepos**: When multiple manifests share a lockfile (npm/yarn workspaces, pnpm workspaces), update at the workspace root to avoid lockfile conflicts.

**Branch already exists and is dirty**: Warn the user and stop. Do not overwrite in-progress work.

## Rules

- Never push or create PRs. The user reviews first.
- Never merge bot PRs. Trust they will auto-close when the target version is satisfied.
- Never skip a CVE-required update. If it cannot be done, report exactly why.
- Never update a dep outside the requested scope.
- Always run tests after each major bump. No shortcuts.
- If stuck on a major bump after reasonable effort, report with full context and revert the dep bump.
