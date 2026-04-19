# update-deps Skill Design

## Overview

A hybrid orchestrator skill that updates project dependencies. It uses linear steps for discovery and safe updates, then parallel research sub-agents with cache-to-disk for major bumps, followed by sequential application of changes.

The skill treats automated bot PRs (dependabot, renovate, snyk) as a discovery mechanism for CVE-required updates. It does not merge those PRs; instead it updates the deps directly, trusting the bots will auto-close their PRs when the target versions are met.

## Arguments

```
/update-deps                          # all scopes, CVE majors + safe minor/patch
/update-deps frontend                 # scope to frontend only
/update-deps backend|infra            # multiple scopes
/update-deps major                    # all scopes, upgrade ALL deps including majors
/update-deps frontend major           # scoped + all majors
```

**Parsing**: split argument on whitespace. Any token containing `|` or matching a known scope name (`frontend`, `backend`, `infra`, `all`) is a scope specifier. The token `major` enables full-major mode. No argument defaults to scope `all` without major flag.

**Scopes** are detected heuristically from project structure:

- **frontend**: manifests whose deps/directory indicate a UI framework or client-side code
- **backend**: manifests whose deps/directory indicate server-side code, APIs, workers
- **infra**: Dockerfiles, docker-compose, terraform, k8s manifests, CI/CD configs, IaC tool configs

In monorepos, multiple manifests may exist. Each gets classified independently.

## Frontmatter

```yaml
---
name: update-deps
description: Updates project dependencies. Checks open bot PRs for CVE patches, applies safe minor/patch updates, and researches/fixes breaking changes for major bumps. Optional scope (frontend|backend|infra|all) and major flag.
argument-hint: "[<scope>[|<scope>...]] [major]"
---
```

## Architecture

The skill is a **hybrid orchestrator**: linear steps for the straightforward parts (discovery, scope classification, safe updates, final summary), with triage-style parallel sub-agent dispatch and cache-to-disk for the major bump research phase.

### Dependency Classification

Every outdated dep is placed in exactly one bucket:

| Bucket | Criteria | Behavior |
|---|---|---|
| **CVE-required** | Referenced by a bot PR with a security advisory | MUST update, even if major bump |
| **Safe** | Minor or patch bump, not CVE-related | Updated automatically in a batch |
| **Major (optional)** | Major bump, not CVE-required | Only updated when `major` flag is set |

### Git Strategy

- Single branch: `chore/update-deps` (or `chore/update-deps-<scope>` if scoped)
- Atomic commits per dependency for major bumps (with breaking change notes in message)
- Batched single commit for all safe minor/patch updates
- Never push, never create PRs, never merge bot PRs

## Steps

### Step 1: Detect Project Structure and Scope Mapping

The agent explores the repo to identify all dependency manifests and maps each to a scope using heuristics about directory names, dependency contents, and file types.

Prints a manifest map:

```
Detected manifests:
  packages/web/package.json        -> frontend
  packages/api/package.json        -> backend
  infra/terraform/versions.tf      -> infra
  docker-compose.yml               -> infra
```

If the user's scope arg filters to specific scopes, only matching manifests proceed.

### Step 2: Check Open PRs for Automated CVE Patches

The agent checks open PRs from known bots (dependabot, renovate, snyk, etc.) using whatever CLI is available. For each bot PR:

- Extract the dependency name and target version
- Note the CVE or security advisory if referenced
- Record whether the update is patch, minor, or major relative to current

These become the **CVE-required update list**. Every dep on this list MUST be updated.

### Step 3: List All Outdated Dependencies

For each in-scope manifest, the agent uses the appropriate package manager commands to list outdated deps with current version, latest version, and bump type. Classifies each into CVE-required, safe, or major (optional).

Prints the classification:

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

### Step 4: Apply Safe Updates

Updates all safe (minor/patch, non-CVE) deps in a single batch per manifest:

1. Run appropriate update commands
2. Run the project's test suite
3. If tests pass: commit all safe updates in one commit listing the updated deps
4. If tests fail: isolate which update caused the failure (revert deps one at a time until tests pass), exclude that dep from the batch, and retry. Deps that can't be safely updated get reported as needing manual attention.

Commit message format:

```
Update minor/patch dependencies

- axios 1.6.0 -> 1.7.2
- dotenv 16.3.1 -> 16.4.1
- typescript 5.3.2 -> 5.3.3
```

### Step 5: Build Research Cache

If there are zero major bumps to process, skip Steps 5-7.

Creates cache directory at `<temp>/update-deps-<PROJECT_ID>`. Writes:

- `<cache>/research-requests.json`: array of objects with package name, current version, target version, reason (cve or major), CVE ID if applicable, manifest path, scope
- `<cache>/project-map.md`: tech stack, directory structure, key files, test patterns (same concept as triage skills, trimmed to relevant scope)

### Step 6: Deploy Parallel Research Sub-Agents

Spawn one sub-agent per major bump dep, all in a single message for parallel execution. Each sub-agent:

1. **Researches breaking changes online.** Uses WebSearch to find the official migration guide, changelog, and release notes covering every version between current and target. Reads blog posts, GitHub discussions, and community resources for known pitfalls. Thorough, not a single search query.

2. **Scans the codebase for affected code.** Using the project map, greps and reads all files that import or use the dep. Identifies every call site, pattern, or API usage affected by a breaking change.

3. **Drafts a change plan.** Writes to `<cache>/change-plan-<package-name>.json`:

```json
{
  "package": "express",
  "current_version": "4.18.2",
  "target_version": "5.1.0",
  "reason": "cve",
  "breaking_changes": [
    {
      "description": "req.host now returns host without port",
      "migration": "Use req.hostname instead, or parse port separately",
      "affected_files": ["src/middleware/proxy.ts:42", "src/routes/health.ts:15"],
      "test_strategy": "Test that host-based routing still works with and without port"
    }
  ],
  "deprecated_apis_used": [
    {
      "api": "res.sendfile()",
      "replacement": "res.sendFile()",
      "affected_files": ["src/routes/static.ts:28"]
    }
  ],
  "new_requirements": "Node.js >= 18 required",
  "estimated_risk": "medium",
  "sources": [
    "https://expressjs.com/en/guide/migrating-5.html"
  ]
}
```

4. **Does NOT modify any code.** Research only.

### Step 7: Sequentially Apply Each Major Bump

The orchestrator reads each change plan and applies them one at a time. Order: if two major bumps could interact (e.g., a framework and its plugin), apply the framework first.

For each major bump:

**7a. Write tests that exercise current behavior.** Before touching the dep, write tests (or extend existing tests) covering the specific APIs and patterns from the change plan's affected_files and breaking_changes. Run tests, confirm they pass.

**7b. Update the dependency.** Run the package manager command to update just this one dep.

**7c. Run the "before" tests, expect failures.** Failures confirm the breaking changes are real and tests cover the right surface. If all tests still pass, the breaking changes don't affect this codebase; skip to 7f.

**7d. Fix code according to the change plan.** Apply documented migration paths: replace deprecated APIs, adjust call signatures, update patterns. Read the actual breaking change documentation sources from the plan for accuracy.

**7e. Run tests until green.** Run the "before" tests plus the full project test suite. Iterate on fixes. If stuck after reasonable effort, report the issue to the user with full context rather than giving up silently. Revert the dep bump and commit the revert if code can't be fixed.

**7f. Commit.** One atomic commit per dep:

```
Update express 4.18.2 -> 5.1.0 (CVE-2024-XXXXX)

Breaking changes addressed:
- req.host -> req.hostname (proxy.ts, health.ts)
- res.sendfile() -> res.sendFile() (static.ts)

Migration guide: https://expressjs.com/en/guide/migrating-5.html
```

**7g. Repeat** for the next change plan.

### Step 8: Final Validation

1. Run the full test suite to catch interaction effects between independently applied updates.
2. Run the project's linter and formatter (from CLAUDE.md). Commit auto-fixes separately if needed.
3. If the final test suite fails, identify which combination caused the interaction and report to the user.

### Step 9: Cleanup and Summary

Delete the cache directory and verify it's gone.

Print summary:

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

Never push, create PRs, or merge. User reviews first.

## Edge Cases

**Branch naming**: `chore/update-deps`. Append scope if specified: `chore/update-deps-frontend`. If the branch already exists with uncommitted work, warn the user and stop. If clean, reuse it.

**No outdated deps**: If discovery finds nothing to update and no bot PRs, tell the user and stop. Don't create a branch.

**No bot PRs but outdated deps exist**: Proceed normally. CVE-required list is empty.

**Mixed CVE and major flag**: If a CVE-required dep also appears on the "all majors" list, process once, with CVE noted in the commit message.

**Lockfile-only updates**: Valid. Include in safe updates.

**Workspaces and monorepos**: When multiple manifests share a lockfile (npm/yarn workspaces), update at the workspace root to avoid lockfile conflicts.

## Rules

- Never push or create PRs. The user reviews first.
- Never merge bot PRs. Trust they'll auto-close.
- Never skip a CVE-required update. If it can't be done, report exactly why.
- Never update a dep outside the requested scope.
- Always run tests after each major bump. No shortcuts.
- If stuck on a major bump after reasonable effort, report with full context. Revert the dep bump and commit the revert if code can't be fixed.
