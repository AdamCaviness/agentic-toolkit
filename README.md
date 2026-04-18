# Agentic Toolkit

A collection of skills for agentic coding tools, including [Claude Code](https://claude.ai/code), [Codex](https://openai.com/codex/), and [Gemini CLI](https://github.com/google-gemini/gemini-cli).

## Installation

Installation differs by platform. All three platforms consume the same `skills/<name>/SKILL.md` format, so one install gets you every skill.

### Claude Code

Register the marketplace, then install the plugin:

```bash
/plugin marketplace add adamcaviness/agentic-marketplace
/plugin install agentic-toolkit@agentic-marketplace
```

### Codex

See [.codex/INSTALL.md](.codex/INSTALL.md). Short version:

```bash
git clone https://github.com/adamcaviness/agentic-toolkit.git ~/.codex/agentic-toolkit
mkdir -p ~/.agents/skills
ln -s ~/.codex/agentic-toolkit/skills ~/.agents/skills/agentic-toolkit
```

Restart Codex to discover the skills.

### Gemini CLI

```bash
gemini extensions install https://github.com/adamcaviness/agentic-toolkit
```

Update with `gemini extensions update agentic-toolkit`.

<details>
<summary>Manual symlink install (any platform)</summary>

If you prefer not to use a plugin/extension system, symlink the skill directories directly.

```bash
# Claude Code (user-level)
for skill in /path/to/agentic-toolkit/skills/*/; do
  ln -s "$skill" ~/.claude/skills/"$(basename "$skill")"
done

# Codex (user-level)
for skill in /path/to/agentic-toolkit/skills/*/; do
  ln -s "$skill" ~/.agents/skills/"$(basename "$skill")"
done
```

For a single skill: `ln -s /path/to/agentic-toolkit/skills/next-ticket ~/.claude/skills/next-ticket`.

For project-level install, symlink into `.claude/skills/` or `.agents/skills/` inside the project root.

</details>

## Skills

### [next-ticket](skills/next-ticket/SKILL.md)

Picks the highest-value open ticket from your project's issue tracker, implements it end-to-end using TDD, and waits for your review before pushing.

**What it does:**

1. Detects your ticket system automatically (GitHub Issues, Jira, GitLab Issues, Azure Boards, or anything else)
2. Fetches all open tickets and scores them by severity, simplicity, blocking power, and value
3. Picks the best candidate, validates it against the current code, and creates a branch
4. Writes failing tests first, implements until green, formats, and commits
5. Stops and waits for you to review before pushing

**Usage:** Type `/next-ticket` in your agent.

**Platform detection:** The skill reads your git remote to determine your ticket system. If it guesses wrong, just correct it. For projects where the git host doesn't match the ticket system (e.g., GitHub repo using Jira), add `ticketSystem: jira` to your CLAUDE.md.

### [triage-architecture](skills/triage-architecture/SKILL.md)

Audits your codebase for bugs, security vulnerabilities, missing error handling, race conditions, architectural gaps, DRY violations, and incomplete implementations. Spawns 4 parallel sub-agents (Safety, Correctness, Maintainability, Completeness) that read code, check for duplicates, and file well-scoped tickets.

**What it does:**

1. Detects your ticket system and caches all open/closed tickets to disk
2. Builds a project map so sub-agents skip discovery
3. Spawns 4 focused agents in parallel, each auditing a different concern cluster
4. Sub-agents file new tickets (create mode) or refine existing ones (refine mode)
5. Post-processes cross-cluster findings into the relevant tickets

**Usage:** `/triage-architecture`, `/triage-architecture refine`, or `/triage-architecture refine 5h`

### [triage-product](skills/triage-product/SKILL.md)

Audits your project for UX gaps, broken workflows, missing states, confusing terminology, visual inconsistency, accessibility issues, and competitive table stakes. Same parallel architecture as triage-architecture but focused on user-facing concerns.

**What it does:**

1. Detects your ticket system and caches all open/closed tickets to disk
2. Builds a project map with product context (who the user is, what the product promises)
3. Spawns 4 focused agents in parallel (Core Experience, Error & Edge States, Polish & Consistency, Reach & Access)
4. Sub-agents file new tickets (create mode) or refine existing ones (refine mode)
5. Post-processes cross-cluster findings into the relevant tickets

**Usage:** `/triage-product`, `/triage-product refine`, or `/triage-product refine 5h`

### [triage-bugs](skills/triage-bugs/SKILL.md)

Investigates your codebase for proven defects using adversarial 4-pass analysis. Spawns 4 parallel sub-agents (Data & State, Security & Auth, Correctness, Silent Failures) that investigate, prove, and document bugs with enough rigor that a skeptical maintainer could fix each from the report alone.

**What it does:**

1. Detects your ticket system and caches all open/closed tickets to disk
2. Builds a project map with bug-relevant infrastructure (error handling, async boundaries, auth chain, database patterns)
3. Spawns 4 focused agents in parallel, each investigating a different bug category
4. Each agent applies a 4-pass method: frame the claim, trace the code, falsify, prove
5. Only files tickets that clear the certainty bar (reproduction, code-path proof, or failing test)
6. Collects a unified summary of confirmed bugs and investigated-but-rejected candidates

**Usage:** `/triage-bugs`, `/triage-bugs refine`, or `/triage-bugs refine 5h`

### [get-it-right](skills/get-it-right/SKILL.md)

Re-evaluate and re-architect the current branch's work as if starting from scratch. Reduces complexity, consolidates fragmentation, auto-implements improvements, and outputs a testing playbook.

**What it does:**

1. Identifies the scope of work on the current branch (commits, changed files, linked issue)
2. Deep-reads every changed and related file to understand context and dependencies
3. Performs retrospective analysis: what should have been done differently, where complexity is unnecessary, where fragmentation exists
4. Plans and auto-implements re-architecture without committing
5. Runs format, lint, and tests to validate
6. Outputs a brief testing playbook for manual validation

**Usage:** Type `/get-it-right` in your agent when you want a fresh look at your current branch's approach.

**Notes:** All changes are left unstaged for your review. The skill preserves existing behavior while reducing complexity and file count.

### [code-review](skills/code-review/SKILL.md)

Dispatches a code-reviewer subagent to evaluate completed work against requirements, keeping the reviewer focused on the diff and preserving your own context.

**What it does:**

1. Captures the base and head git SHAs for the changes under review
2. Fills a review template with what you built, what it should do, and the git range
3. Dispatches a code-reviewer subagent via the Task tool with that context only
4. Returns categorized feedback (Critical, Important, Minor) plus a merge verdict
5. You fix Critical/Important issues, note Minor for later, and push back on weak feedback

**Usage:** Invoke after completing a task, finishing a major feature, or before merging to main.

**Notes:** Adapted from the superpowers project's `requesting-code-review` skill under MIT. See [skills/code-review/ATTRIBUTIONS.md](skills/code-review/ATTRIBUTIONS.md).

### [pr](skills/pr/SKILL.md)

Format, lint, test, commit, push, and create a pull request. The single "I'm done" command.

**What it does:**

1. Verifies you're not on main/master
2. Runs format and lint (skips if already passing in this session)
3. Runs tests (skips if already passing in this session)
4. Commits any auto-fixed formatting changes
5. Pushes to remote
6. Extracts issue number from branch name (e.g., `fix/224-bug` → `#224`)
7. Creates PR with summary, changes, testing notes, and "Closes #NNN"

**Usage:** Type `/pr` in your agent when your feature branch is ready.

**Notes:** If format/lint or tests fail, the skill stops and reports errors. If a PR already exists, it shows the URL and confirms the update.

### [ship](skills/ship/SKILL.md)

Commit, push, create/merge PR, sync local main, and delete the branch. The complete "I'm done with this branch" workflow.

**What it does:**

1. Reviews uncommitted changes and prompts for confirmation if anything looks suspect
2. Commits with a descriptive message based on the diff
3. Pushes to origin
4. Creates a PR if none exists, or updates the existing one
5. Merges the PR
6. Syncs local main with `git pull`
7. Deletes the merged branch locally and remotely (if not auto-deleted)

**Usage:** Type `/ship` in your agent when your branch is complete and ready to merge.

**Notes:** For forked repos, PRs target your fork (origin), never upstream. Only works on feature branches, not main.

### [convert-worktree](skills/convert-worktree/SKILL.md)

Converts a git worktree into a regular local branch. Rebases onto the latest base branch, runs project cleanup, removes the worktree, and checks out the branch in the main workspace.

**What it does:**

1. Verifies you're in a worktree (not the main workspace)
2. Commits any uncommitted work as a WIP commit
3. Runs project cleanup (e.g., `make dev-stop`) while worktree context is still available
4. Rebases onto the latest base branch (auto-resolves lockfile conflicts, aborts on code conflicts)
5. Removes the worktree and checks out the branch in your main workspace

**Usage:** Type `/convert-worktree` in your agent while inside a worktree.

**Notes:** This skill replaces ExitWorktree. It never blocks on failures, so rebase conflicts or cleanup failures result in warnings, not errors. After conversion, run `npm install` (or equivalent) if lockfiles were auto-resolved.

## Ticket Systems

Ticket-aware skills (`next-ticket`, `triage-architecture`, `triage-product`, `triage-bugs`) auto-detect your system from `git remote -v` and work with GitHub Issues, Jira, GitLab Issues, Azure Boards, Linear, Shortcut, and anything else the model can reach via CLI, MCP, or APIs available in your session.

If auto-detect gets it wrong, correct it once and the detection is cached for the session. For persistent override, add `ticketSystem: <name>` to your project's CLAUDE.md.

## Releasing

Releases are fully automated by [release-please](https://github.com/googleapis/release-please). Use [Conventional Commits](https://www.conventionalcommits.org/) on PRs merged to `main`. Release-please opens a "chore: release" PR that bumps the version across `.claude-plugin/plugin.json` and `gemini-extension.json`, and updates `CHANGELOG.md`. Merge that PR to cut the release, tag, and publish GitHub Release notes. No manual tagging. After release, update the corresponding `version` entry in the companion [adamcaviness/agentic-marketplace](https://github.com/adamcaviness/agentic-marketplace) repo's `marketplace.json`.

Commit types map to changelog sections and version bumps:

| Type                          | Section                               | Bump            |
| ----------------------------- | ------------------------------------- | --------------- |
| `feat:`                       | Features                              | minor           |
| `fix:`                        | Bug Fixes                             | patch           |
| `docs:`, `perf:`, `refactor:` | Documentation/Performance/Refactoring | changelog only  |

Use `feat(skill): add X` to classify new skills. The scope appears in the changelog entry. Add `!` after the type or a `BREAKING CHANGE:` body for a major bump. Only `feat:` and `fix:` commits drive a release PR on their own, so at least one of those must land between releases.

## License

MIT
