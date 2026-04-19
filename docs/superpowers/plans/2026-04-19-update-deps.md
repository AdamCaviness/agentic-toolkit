# update-deps Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `skills/update-deps/SKILL.md` that instructs an LLM agent to update project dependencies: discover CVE-required updates from bot PRs, apply safe minor/patch updates, research breaking changes for major bumps via parallel sub-agents, and sequentially apply major bumps with tests.

**Architecture:** Single SKILL.md file following the hybrid orchestrator pattern. Linear steps for discovery and safe updates (Steps 1-4), parallel sub-agent dispatch for major bump research (Steps 5-6), sequential application with TDD for major bumps (Step 7), finalization (Steps 8-9). Follows the conventions established by `triage-bugs/SKILL.md` (sub-agent templates) and `pr/SKILL.md` (linear flow).

**Tech Stack:** Markdown skill file (no runtime code). Follows the agentic-toolkit plugin format with YAML frontmatter.

**Reference files:**
- Design spec: `docs/superpowers/specs/2026-04-19-update-deps-design.md`
- Pattern: `skills/triage-bugs/SKILL.md` (sub-agent template pattern)
- Pattern: `skills/pr/SKILL.md` (linear skill pattern)
- Pattern: `skills/next-ticket/SKILL.md` (argument parsing, tool-agnostic detection)
- Conventions: `AGENTS.md` (commit style, no em-dashes, no Co-Authored-By)

---

### Task 1: Create SKILL.md with Frontmatter, Overview, Arguments, Prerequisites, and Branch Naming

**Files:**
- Create: `skills/update-deps/SKILL.md`

- [ ] **Step 1: Create the skill directory and file with frontmatter through branch naming**

Create `skills/update-deps/SKILL.md` with the following content:

```markdown
---
name: update-deps
description: Updates project dependencies. Checks open bot PRs for CVE patches, applies safe minor/patch updates, and researches/fixes breaking changes for major bumps. Optional scope (frontend|backend|infra|all) and major flag.
argument-hint: "[<scope>[|<scope>...]] [major]"
---

# Update Dependencies

Update project dependencies safely. Checks bot PRs for CVE-required patches, applies safe minor/patch updates in batch, and for major bumps: researches breaking changes online, scans the codebase for affected code, writes tests, fixes code, and validates.

You are a **hybrid orchestrator**. Steps 1-4 are linear (discovery and safe updates). Steps 5-6 dispatch parallel research sub-agents. Step 7 applies major bump changes sequentially. Steps 8-9 finalize.

## Arguments

Check the argument passed to this skill:

- **No argument**: All scopes, CVE-required major bumps + safe minor/patch only
- **Scope tokens**: `frontend`, `backend`, `infra`, or `all` (default). Pipe-separate for multiple: `frontend|backend`
- **`major` keyword**: Upgrade ALL deps to latest, including non-CVE major bumps, using thorough research approach

Parsing: split on whitespace. Tokens containing `|` or matching a scope name are scope specifiers. The token `major` enables full-major mode. No argument = scope `all`, no major flag.

Usage: `/update-deps`, `/update-deps frontend`, `/update-deps backend|infra major`

## Prerequisites

Verify you're in a git repo. If not, tell the user and stop.

Verify you're not on `main` or `master`. If you are, create the branch first (see Branch Naming below).

## Branch Naming

Create branch `chore/update-deps`. If a scope is specified, append it: `chore/update-deps-frontend`. If the branch already exists:
- Clean (no uncommitted work): reuse it
- Dirty (uncommitted changes): warn the user and stop
```

- [ ] **Step 2: Verify file structure**

Run: `ls -la skills/update-deps/SKILL.md`
Expected: file exists

- [ ] **Step 3: Commit**

```bash
git add skills/update-deps/SKILL.md
git commit -m "feat(skill): scaffold update-deps with frontmatter and overview"
```

---

### Task 2: Write Steps 1-2 (Manifest Detection and CVE PR Scanning)

**Files:**
- Modify: `skills/update-deps/SKILL.md`

- [ ] **Step 1: Append Step 1 (Detect Project Structure) to SKILL.md**

Add after the Branch Naming section:

```markdown

## Step 1: Detect Project Structure and Scope Mapping

Explore the repo to identify all dependency manifests. Use whatever package manager discovery mechanisms are available. Map each manifest to a scope using heuristics:

- **frontend**: manifests whose dependencies or directory context indicate a UI framework or client-side code
- **backend**: manifests whose dependencies or directory context indicate server-side code, APIs, workers
- **infra**: Dockerfiles, docker-compose files, terraform configs, k8s manifests, CI/CD configs, IaC tool configs

In monorepos, multiple manifests may exist. Classify each independently.

Print the manifest map:

\```
Detected manifests:
  packages/web/package.json        -> frontend
  packages/api/package.json        -> backend
  infra/terraform/versions.tf      -> infra
  docker-compose.yml               -> infra
\```

If the user's scope arg filters to specific scopes, only matching manifests proceed. Discard the rest.
```

- [ ] **Step 2: Append Step 2 (Check Open PRs for CVE Patches) to SKILL.md**

Add after Step 1:

```markdown

## Step 2: Check Open PRs for Automated CVE Patches

Check open PRs from automated dependency bots (dependabot, renovate, snyk, etc.) using whatever CLI is available (e.g., `gh pr list`). Identify bot PRs by author name or label conventions.

For each bot PR:

- Extract the dependency name and target version from the PR title and body
- Note the CVE or security advisory if referenced
- Record whether the update is patch, minor, or major relative to the currently installed version

These form the **CVE-required update list**. Every dep on this list MUST be updated, even if it requires a major bump.

Do NOT merge these PRs. The skill updates the deps directly; the bots will auto-close their PRs when they detect the target version is met.

If no bot PRs exist, the CVE-required list is empty. Proceed normally.
```

- [ ] **Step 3: Verify the content reads correctly**

Run: `head -120 skills/update-deps/SKILL.md`
Expected: frontmatter, overview, arguments, prerequisites, branch naming, Steps 1-2

- [ ] **Step 4: Commit**

```bash
git add skills/update-deps/SKILL.md
git commit -m "feat(skill): add manifest detection and CVE PR scanning steps"
```

---

### Task 3: Write Steps 3-4 (Outdated Dependency Listing and Safe Updates)

**Files:**
- Modify: `skills/update-deps/SKILL.md`

- [ ] **Step 1: Append Step 3 (List All Outdated Dependencies) to SKILL.md**

Add after Step 2:

```markdown

## Step 3: List All Outdated Dependencies

For each in-scope manifest, use the appropriate package manager commands to list outdated deps. Record current version, latest version, and bump type (patch, minor, major).

Classify each outdated dep into exactly one bucket:

| Bucket | Criteria | Action |
|---|---|---|
| **CVE-required** | Appears on the CVE-required list from Step 2 | MUST update, even if major |
| **Safe** | Minor or patch bump, not on CVE list | Updated in batch |
| **Major (optional)** | Major bump, not on CVE list | Only updated if `major` flag is set |

Print the classification:

\```
Dependency audit:
  CVE-required (N):
    <pkg> <current> -> <target> (<bump>) -- <CVE-ID> via <bot> PR #<n>
    ...

  Safe updates (N):
    <pkg> <current> -> <target> (<bump>)
    ...

  Major (skipped, use 'major' flag to include) (N):
    <pkg> <current> -> <target> (major)
    ...
\```

If nothing is outdated and no bot PRs exist, tell the user and stop. Don't create a branch.
```

- [ ] **Step 2: Append Step 4 (Apply Safe Updates) to SKILL.md**

Add after Step 3:

```markdown

## Step 4: Apply Safe Updates

Update all safe (minor/patch, non-CVE) deps in a single batch per manifest.

1. Run the appropriate package manager update commands for all safe deps
2. Run the project's test suite (check CLAUDE.md for the test command)
3. **Tests pass**: commit all safe updates in a single commit:

\```
Update minor/patch dependencies

- <pkg> <old> -> <new>
- <pkg> <old> -> <new>
- ...
\```

4. **Tests fail**: isolate which update caused the failure. Revert deps one at a time until tests pass. Exclude the offending dep from the batch and retry. Report any dep that can't be safely updated as needing manual attention.
```

- [ ] **Step 3: Commit**

```bash
git add skills/update-deps/SKILL.md
git commit -m "feat(skill): add dependency classification and safe update steps"
```

---

### Task 4: Write Steps 5-6 (Research Cache and Sub-Agent Dispatch)

This is the most complex section. It includes the sub-agent prompt template following the pattern from `triage-bugs/SKILL.md`.

**Files:**
- Modify: `skills/update-deps/SKILL.md`

- [ ] **Step 1: Append Step 5 (Build Research Cache) to SKILL.md**

Add after Step 4:

```markdown

## Step 5: Build Research Cache

If there are zero major bumps to process (no CVE-required majors and either no optional majors or `major` flag not set), **skip Steps 5-7 entirely**.

### Derive project identity

Determine the project root path, project name (from directory name), and a short hash of the root path. Construct `PROJECT_ID` as `<name>-<hash>` and create the cache directory at `<temp>/update-deps-<PROJECT_ID>`.

### Destroy stale cache

Remove the cache directory if it exists, then recreate it empty.

### Write research requests

Write `<cache>/research-requests.json` with an entry per major bump dep:

\```json
[
  {
    "package": "<name>",
    "current_version": "<current>",
    "target_version": "<target>",
    "reason": "cve | major",
    "cve_id": "<CVE-ID or null>",
    "manifest": "<path/to/manifest>",
    "scope": "<frontend|backend|infra>"
  }
]
\```

### Build project map

Explore the codebase and write `<cache>/project-map.md`. This is pointers and structure for sub-agents to orient, not file contents.

1. Read CLAUDE.md, README.md, and dependency manifests
2. Run a directory structure listing (pruned, excluding .git and dependency directories)
3. Identify entry points, key files, test patterns

The map should include:
- **Tech stack**: language, framework, database, testing tools
- **Directory structure**: actual tree output, pruned to reasonable depth
- **Key files**: path + one-line purpose
- **Test patterns**: framework, naming conventions, where tests live, how to run them
- **Conventions from CLAUDE.md**: project-specific conventions affecting the update
```

- [ ] **Step 2: Append Step 6 (Deploy Parallel Research Sub-Agents) with prompt template to SKILL.md**

Add after Step 5:

```markdown

## Step 6: Deploy Parallel Research Sub-Agents

Read `<cache>/research-requests.json`. Spawn **one sub-agent per major bump dep, ALL in a single message** so they run concurrently.

For each dep, construct a prompt by taking the Research Sub-Agent Prompt Template below and replacing:
- `{PACKAGE}` with the package name
- `{CURRENT_VERSION}` with the current version
- `{TARGET_VERSION}` with the target version
- `{REASON}` with `cve` or `major`
- `{CVE_ID}` with the CVE ID (or `N/A`)
- `{MANIFEST}` with the manifest path
- `{CACHE_DIR}` with the cache directory path

Use `description: "Research <package> <current> -> <target>"` for each.

---

### Research Sub-Agent Prompt Template

\```
You are a dependency upgrade researcher. Your job is to thoroughly research the breaking changes between two versions of a package, scan the codebase for affected code, and produce a detailed change plan. You do NOT modify any code.

## Your Assignment

Package: {PACKAGE}
Current version: {CURRENT_VERSION}
Target version: {TARGET_VERSION}
Reason: {REASON}
CVE: {CVE_ID}
Manifest: {MANIFEST}

## Step 1: Research Breaking Changes Online

Use WebSearch to find:

1. **Official migration guide** for {PACKAGE} from {CURRENT_VERSION} to {TARGET_VERSION}
2. **Changelog and release notes** for EVERY version between {CURRENT_VERSION} and {TARGET_VERSION}. Do not skip intermediate majors if the jump spans more than one.
3. **Blog posts, GitHub discussions, and community resources** for known pitfalls, common migration mistakes, and workarounds

Be thorough. Run multiple searches:
- "{PACKAGE} migration guide {CURRENT_VERSION} to {TARGET_VERSION}"
- "{PACKAGE} breaking changes {TARGET_VERSION}"
- "{PACKAGE} upgrade guide"
- "{PACKAGE} changelog"

Read the actual pages, not just snippets. Extract every breaking change, deprecated API, removed feature, changed default, and new requirement.

Compile a complete list of breaking changes with:
- What changed
- What replaces it (the migration path)
- What version introduced the change

## Step 2: Scan the Codebase for Affected Code

Read the project map at `{CACHE_DIR}/project-map.md` to understand the codebase structure.

For each breaking change identified in Step 1:

1. Grep the codebase for usage of the affected API, function, pattern, or configuration
2. Read each affected file to understand the context of usage
3. Determine whether the breaking change actually impacts this codebase (some breaking changes affect APIs not used here)
4. Note the specific file paths and line numbers where changes will be needed

Also scan for:
- Import statements for the package
- Configuration files that reference the package
- Deprecated API usage that may not be flagged as breaking but should be updated

## Step 3: Write Change Plan

Write your findings to `{CACHE_DIR}/change-plan-{PACKAGE}.json`:

```json
{
  "package": "{PACKAGE}",
  "current_version": "{CURRENT_VERSION}",
  "target_version": "{TARGET_VERSION}",
  "reason": "{REASON}",
  "cve_id": "{CVE_ID}",
  "breaking_changes": [
    {
      "description": "What changed",
      "migration": "How to fix it",
      "affected_files": ["path/to/file.ts:42", "path/to/other.ts:15"],
      "test_strategy": "What to test to verify the migration"
    }
  ],
  "deprecated_apis_used": [
    {
      "api": "The deprecated API",
      "replacement": "What to use instead",
      "affected_files": ["path/to/file.ts:28"]
    }
  ],
  "new_requirements": "Any new runtime or environment requirements (e.g., Node.js >= 18)",
  "estimated_risk": "low | medium | high",
  "risk_rationale": "Why this risk level",
  "sources": [
    "URL of migration guide",
    "URL of changelog"
  ]
}
```

If the package has no breaking changes affecting this codebase (all changes are internal or affect unused APIs), still write the plan file with empty `breaking_changes` and `deprecated_apis_used` arrays and `estimated_risk: "low"`.

## Rules

- Do NOT modify any code. Research and analysis only.
- Do NOT skip intermediate versions. If upgrading from v2 to v5, research v3, v4, and v5 breaking changes.
- Be specific about file paths and line numbers. The orchestrator will use these to apply changes.
- Prefer official documentation over community sources when they conflict.
- Note any breaking changes you're uncertain about. Flag uncertainty in the change plan rather than omitting.
\```

---
```

- [ ] **Step 3: Verify the sub-agent template renders correctly**

Visually check that the nested code blocks inside the template use the correct escaping. The outer fence is the template delimiter; inner JSON code blocks must be indented or use different fence lengths to render properly.

- [ ] **Step 4: Commit**

```bash
git add skills/update-deps/SKILL.md
git commit -m "feat(skill): add research cache and parallel sub-agent dispatch"
```

---

### Task 5: Write Step 7 (Sequential Major Bump Application)

**Files:**
- Modify: `skills/update-deps/SKILL.md`

- [ ] **Step 1: Append Step 7 (Sequentially Apply Each Major Bump) to SKILL.md**

Add after the sub-agent template section:

```markdown

## Step 7: Sequentially Apply Each Major Bump

After all research sub-agents complete, read the change plans from the cache directory. Apply them one at a time, sequentially.

### Determine application order

If multiple major bumps could interact (e.g., a framework and a plugin for that framework, or a library and its type definitions), apply the foundational package first. Read the change plans to identify dependency relationships and order accordingly.

### For each major bump dep:

**7a. Write tests that exercise current behavior.**

Before touching the dep, write tests (or extend existing tests) that cover the specific APIs, patterns, and call sites identified in the change plan's `affected_files` and `breaking_changes`. These tests pin the current behavior. Run them and confirm they pass. This is the "before" snapshot.

If the change plan shows empty `breaking_changes` (no impact on this codebase), skip to 7f.

**7b. Update the dependency.**

Run the package manager command to update just this one dep to the target version. Update the lockfile.

**7c. Run the "before" tests, expect failures.**

Run the tests from 7a. Failures confirm the breaking changes are real and the tests cover the right surface area. If all tests pass, the breaking changes don't affect this codebase despite what the research found. Skip to 7f.

**7d. Fix code according to the change plan.**

Using the change plan as a guide, update every affected file:
- Replace deprecated APIs with their replacements
- Adjust call signatures, configuration, and patterns
- Read the actual source documentation URLs from the plan's `sources` to verify accuracy, not just the plan summary

**7e. Run tests until green.**

Run the "before" tests from 7a plus the full project test suite. Iterate on fixes until all pass.

If stuck after reasonable effort, report the issue to the user with full context (what failed, what you tried, what the breaking change docs say). Revert the dep bump (`git checkout -- <manifest> <lockfile>` and reinstall), commit the revert if any code changes were made, and move to the next dep. Do NOT silently give up.

**7f. Commit.**

One atomic commit per dep:

\```
Update <package> <old> -> <new> [(<CVE-ID>)]

Breaking changes addressed:
- <description> (<affected files>)
- ...

Migration guide: <url>
\```

If no breaking changes were addressed (clean upgrade), simplify:

\```
Update <package> <old> -> <new> [(<CVE-ID>)]

No breaking changes affect this codebase.
\```

**7g. Repeat** for the next change plan.
```

- [ ] **Step 2: Commit**

```bash
git add skills/update-deps/SKILL.md
git commit -m "feat(skill): add sequential major bump application with TDD"
```

---

### Task 6: Write Steps 8-9, Edge Cases, and Rules

**Files:**
- Modify: `skills/update-deps/SKILL.md`

- [ ] **Step 1: Append Steps 8-9, Edge Cases, and Rules to SKILL.md**

Add after Step 7:

```markdown

## Step 8: Final Validation

After all deps are updated and committed:

1. Run the full test suite one final time to catch interaction effects between independently applied updates.
2. Run the project's linter and formatter (check CLAUDE.md for the commands). If they modify files, commit as "Auto-format and lint fixes".
3. If the final test suite fails, identify which combination of updates caused the interaction and report to the user with full context.

## Step 9: Cleanup and Summary

Delete the cache directory (`<temp>/update-deps-<PROJECT_ID>`) and verify it's gone. If cleanup fails, investigate and retry.

Print summary:

\```
Dependency update complete.

Branch: chore/update-deps[-<scope>]
Scope: <scope>
Mode: standard | major

Safe updates (1 commit):
  <pkg> <old> -> <new>, <pkg> <old> -> <new>, ... (N deps)

Major updates (N commits):
  <pkg> <old> -> <new> [(<CVE-ID>)] -- N breaking changes addressed
  ...

Skipped (manual attention needed):
  <pkg> <old> -> <new> -- <reason>
  ...

Bot PRs that should auto-close:
  #<n> (<bot>: <pkg>)
  ...

All tests passing. Ready for review.
\```

Never push, create PRs, or merge. The user reviews first.

## Edge Cases

**No outdated deps**: If discovery finds nothing to update and no bot PRs, tell the user and stop. Don't create a branch.

**No bot PRs but outdated deps exist**: Proceed normally. CVE-required list is empty.

**Mixed CVE and major flag**: If a CVE-required dep also appears on the "all majors" list, process once with CVE noted in the commit message.

**Lockfile-only updates**: Valid. Include in safe updates.

**Workspaces and monorepos**: When multiple manifests share a lockfile (npm/yarn workspaces), update at the workspace root to avoid lockfile conflicts.

## Rules

- Never push or create PRs. The user reviews first.
- Never merge bot PRs. Trust they'll auto-close.
- Never skip a CVE-required update. If it can't be done, report exactly why.
- Never update a dep outside the requested scope.
- Always run tests after each major bump. No shortcuts.
- If stuck on a major bump after reasonable effort, report with full context. Revert the dep bump and commit the revert if code can't be fixed.
```

- [ ] **Step 2: Commit**

```bash
git add skills/update-deps/SKILL.md
git commit -m "feat(skill): add finalization, edge cases, and rules"
```

---

### Task 7: Full Review and Final Commit

**Files:**
- Review: `skills/update-deps/SKILL.md`
- Reference: `docs/superpowers/specs/2026-04-19-update-deps-design.md`

- [ ] **Step 1: Spec coverage check**

Read the design spec at `docs/superpowers/specs/2026-04-19-update-deps-design.md` and the completed SKILL.md. Verify each spec requirement maps to a section in the skill:

| Spec Section | SKILL.md Coverage |
|---|---|
| Arguments (scope, major) | Arguments section |
| Frontmatter | YAML frontmatter |
| Dependency classification (CVE/safe/major) | Step 3 |
| Git strategy (single branch, atomic commits) | Branch Naming, Steps 4/7f |
| Step 1: Detect structure | Step 1 |
| Step 2: Check PRs | Step 2 |
| Step 3: List outdated | Step 3 |
| Step 4: Safe updates | Step 4 |
| Step 5: Build cache | Step 5 |
| Step 6: Sub-agents | Step 6 + template |
| Step 7: Sequential apply | Step 7 (7a-7g) |
| Step 8: Final validation | Step 8 |
| Step 9: Cleanup/summary | Step 9 |
| Edge cases | Edge Cases section |
| Rules | Rules section |

If any gap is found, add the missing content.

- [ ] **Step 2: Style check against AGENTS.md**

Verify:
- No em-dashes (use commas instead)
- No Co-Authored-By references
- No TODOs
- Commas for punctuation throughout

- [ ] **Step 3: Pattern check against existing skills**

Verify the skill follows conventions from existing skills:
- Frontmatter matches format (`name`, `description`, `argument-hint`)
- Sub-agent template uses `{PLACEHOLDER}` substitution like triage-bugs
- Tool-agnostic language ("use whatever CLI tools are available")
- Cache pattern matches triage skills (`<temp>/update-deps-<PROJECT_ID>`)
- No hardcoded tool names except as examples

- [ ] **Step 4: Fix any issues found in Steps 1-3**

If any gaps, style violations, or pattern mismatches were found, fix them and amend the last commit.

- [ ] **Step 5: Final commit if any fixes were made**

```bash
git add skills/update-deps/SKILL.md
git commit -m "fix(skill): address review findings in update-deps"
```
