# Agentic Toolkit

A collection of skills for agentic coding tools, including [Claude Code](https://claude.ai/code), [Cursor](https://cursor.com), [Codex](https://openai.com/codex/), and [Gemini CLI](https://github.com/google-gemini/gemini-cli).

| | Skill | Command | What it does |
|---|-------|---------|-------------|
| **Ticket** | [create-ticket](#create-ticket) | `/create-ticket [idea]` | Research an idea, craft a high-quality ticket, dedup, and file it |
| | [next-ticket](#next-ticket) | `/next-ticket [id]` | Pick up a ticket (best open or specific), implement it with TDD, wait for review |
| | [triage-architecture](#triage-architecture) | `/triage-architecture` | Find structural/safety issues in code; file tickets or `refine` existing |
| | [triage-bugs](#triage-bugs) | `/triage-bugs` | Prove real defects with 4-pass analysis; file tickets or `refine` existing |
| | [triage-product](#triage-product) | `/triage-product` | Find UX gaps and broken workflows; file tickets or `refine` existing |
| **Quality** | [code-review](#code-review) | `/code-review` | Dispatch a reviewer subagent to evaluate all branch work (committed + uncommitted) |
| | [apply-review](#apply-review) | `/apply-review` | Read PR review comments, fix valid ones, push, resolve addressed threads |
| | [get-it-right](#get-it-right) | `/get-it-right` | Re-architect the current branch from scratch, leave unstaged for review |
| **Workflow** | [pr](#pr) | `/pr` | Format, lint, test, commit, push, open PR |
| | [ship](#ship) | `/ship` | Commit, push, merge PR, sync default branch, delete branch |
| | [convert-worktree](#convert-worktree) | `/convert-worktree` | Cleanly convert a worktree back into a local branch |
| **Utility** | [compress-markdown](#compress-markdown) | `/compress-markdown` | Compress markdown to save tokens; `deep` validates against codebase first |
| | [update-deps](#update-deps) | `/update-deps` | Check CVEs, apply minor/patch updates, `major` for breaking changes; scopeable |

---

## Installation

> Installation differs by platform. Claude Code, Cursor, Codex, and Gemini CLI consume the same `skills/<name>/SKILL.md` format, so one install gets you every skill.

<details>
<summary>Claude Code</summary>

Register the marketplace, then install the plugin:

```bash
/plugin marketplace add adamcaviness/agentic-marketplace
/plugin install agentic-toolkit@agentic-marketplace
```

</details>

<details>
<summary>Cursor</summary>

See [.cursor/INSTALL.md](.cursor/INSTALL.md). Short version for Pro (and other individual plans), user-level, every project:

```bash
mkdir -p ~/.cursor/plugins/local
git clone https://github.com/adamcaviness/agentic-toolkit.git ~/.cursor/plugins/local/agentic-toolkit
```

Reload the window (**Developer: Reload Window**) or restart Cursor. Skills appear under `/` in Agents. Confirm in **Customize → Skills**.

Update later with `git -C ~/.cursor/plugins/local/agentic-toolkit pull`, then reload again.

Use only this plugin path for Cursor. Do not also symlink into `~/.agents/skills/` or `~/.cursor/skills/`, or every skill appears twice (Cursor discovers all three locations).

> **Teams / Enterprise only:** importing a marketplace repo is a web admin flow at [cursor.com/dashboard](https://cursor.com/dashboard) → **Plugins**, not something in the desktop app. Pro users use the clone path above.

</details>

<details>
<summary>Codex</summary>

See [.codex/INSTALL.md](.codex/INSTALL.md). Short version:

```bash
git clone https://github.com/adamcaviness/agentic-toolkit.git ~/.codex/agentic-toolkit
mkdir -p ~/.agents/skills
ln -s ~/.codex/agentic-toolkit/skills ~/.agents/skills/agentic-toolkit
```

Restart Codex to discover the skills.

</details>

<details>
<summary>Gemini CLI</summary>

```bash
gemini extensions install https://github.com/adamcaviness/agentic-toolkit
```

Update with `gemini extensions update agentic-toolkit`.

</details>

<details>
<summary>Manual (any platform)</summary>

If you prefer not to use a plugin/extension system, clone the repo and symlink the skill directories. Pick **one** discovery location per harness. For Cursor, prefer [.cursor/INSTALL.md](.cursor/INSTALL.md) (`~/.cursor/plugins/local`) instead of the per-skill loops below; using both lists every skill twice.

```bash
git clone https://github.com/adamcaviness/agentic-toolkit.git ~/opensource/agentic-toolkit


# Claude Code (user-level)
for skill in ~/opensource/agentic-toolkit/skills/*/; do
  ln -s "$skill" ~/.claude/skills/"$(basename "$skill")"
done

# Codex (user-level)
for skill in ~/opensource/agentic-toolkit/skills/*/; do
  ln -s "$skill" ~/.agents/skills/"$(basename "$skill")"
done
```

For a single skill: `ln -s ~/opensource/agentic-toolkit/skills/next-ticket ~/.claude/skills/next-ticket`.

For project-level install, symlink into `.claude/skills/` or `.agents/skills/` inside the project root. For Cursor project-level, use `.cursor/skills/` **or** a project-scoped plugin, not both, and not alongside `~/.cursor/plugins/local/agentic-toolkit`.

</details>

---

## Ticket Skills

> Skills for creating, implementing, and maintaining your project's issue backlog.

### [create-ticket](skills/create-ticket/SKILL.md)

Turns a user-provided idea into a well-researched, well-structured ticket and files it.

- Explores project context when available (works equally well on greenfield projects with no code)
- Searches the web for prior art and known pitfalls
- Deduplicates against the existing backlog, including rejection learning from not-planned tickets
- Asks clarifying questions only when options are too nuanced to auto-resolve
- Produces one ticket per run with type-appropriate body structure (feature, bug, architecture, product, or chore)
- Presents a full draft for review and files only after approval

**Usage:** `/create-ticket add dark mode support` or `/create-ticket` then describe the idea.

### [next-ticket](skills/next-ticket/SKILL.md)

Picks up a ticket from your issue tracker, implements it end-to-end with TDD, and waits for your review.

- **Auto-pick** (no argument): fetches all eligible tickets, scores by severity, simplicity, blocking power, and value, picks the best candidate
- **Specific ticket** (with ID): fetches that ticket directly, skips scoring
- Validates the ticket against current code, checking for prior fixes or partial resolution
- Claims with a team-safe self-assignment protocol (re-reads assignee after a randomized pause to avoid collisions)
- Ticket IDs are resolved flexibly: bare numbers are interpreted per platform (e.g., `42` becomes `ABC-42` on Jira), prefixed IDs like `#42` or `ABC-42` are used as-is

**Usage:** `/next-ticket` (auto-pick best ticket) or `/next-ticket 42` (pick up a specific ticket).

> [!NOTE]
> All ticket skills auto-detect your ticket system: the agent reads repo signals (README, CLAUDE.md, git remotes, commit conventions) to determine which system you use. Supported out of the box: GitHub Issues, Jira, GitLab Issues, Azure Boards, Linear, Shortcut, and anything else the model can reach via CLI, MCP, or APIs in your session. Detection results are cached so detection only runs once per project. For persistent override, add `ticketSystem: <name>` to your project's CLAUDE.md.

---

**Triage skills** audit your codebase and file tickets for what they find. Each skill caches existing tickets (for deduplication and rejection learning), builds a project map, then spawns 4 parallel sub-agents (one per concern cluster) that read code, prove findings, and file or refine tickets directly in your issue tracker. Each supports three modes:

- **Create** (default): Find new problems, file up to 3 tickets per cluster
- **Refine**: Improve existing tickets, create none
- **Refine with duration** (e.g., `refine 5h`): Scope refinement to tickets created within the given time window

### [triage-architecture](skills/triage-architecture/SKILL.md)

Finds structural and safety issues in code and files a ticket for each confirmed finding. Covers security vulnerabilities, missing error handling, race conditions, architectural gaps, DRY violations, and incomplete implementations. Clusters: Safety, Correctness, Maintainability, Completeness.

**Usage:** `/triage-architecture`, `/triage-architecture refine`, `/triage-architecture refine 5h`

### [triage-bugs](skills/triage-bugs/SKILL.md)

Investigates the codebase for proven defects and files a ticket for each confirmed bug. Each sub-agent applies a 4-pass method:

1. **Frame** the specific claim
2. **Trace** the code path end-to-end
3. **Falsify** by actively trying to disprove the suspicion
4. **Prove** with a reproduction, code-path proof, or failing test

Only findings that clear this bar get filed. The result includes both confirmed bugs and a rejection ledger of investigated-but-dismissed candidates. Clusters: Data & State, Security & Auth, Correctness, Silent Failures.

**Usage:** `/triage-bugs`, `/triage-bugs refine`, `/triage-bugs refine 5h`

### [triage-product](skills/triage-product/SKILL.md)

Finds UX gaps, broken workflows, missing states, confusing terminology, accessibility issues, and competitive table stakes, filing a ticket for each confirmed finding. Sub-agents judge against what the product actually promises (from its README), not abstract ideals. Clusters: Core Experience, Error & Edge States, Polish & Consistency, Reach & Access.

**Usage:** `/triage-product`, `/triage-product refine`, `/triage-product refine 5h`

> [!TIP]
> The triage skills learn from tickets you reject. When closing a ticket as out of scope or won't fix, use the platform's **not-planned** close-state (GitHub: "Close as not planned", Jira: resolution "Won't Do") with a one-line reason. The next triage run reads that close-state and skips refiling the same class of concern. Closing as completed breaks this loop.

---

## Quality Skills

> Skills for reviewing and improving what you've built.

### [code-review](skills/code-review/SKILL.md)

Dispatches a code-reviewer subagent to evaluate all branch work against requirements: every commit since the merge base with the default branch, plus any staged, unstaged, or untracked changes in your working tree. The reviewer gets a crafted context (git range, changed-path inventory, working-tree state, what you built, what it should do), never your session history. Returns categorized feedback (Critical, Important, Minor) plus a merge verdict, then automatically fixes Critical and Important issues before proceeding.

**Usage:** `/code-review`

### [apply-review](skills/apply-review/SKILL.md)

Reads all review comments on the current PR (human, Copilot, Claude, any reviewer), validates each against the actual code, fixes valid comments, pushes, resolves addressed threads via GitHub's API, and leaves succinct replies on threads it did not resolve. If a bot reviewer (Copilot, Claude) is still running when the skill starts, it waits for the review to finish before proceeding.

**Usage:** `/apply-review`, `/apply-review 42`

### [get-it-right](skills/get-it-right/SKILL.md)

Re-evaluates the current branch's work as if starting from scratch. Deep-reads every changed file, performs retrospective analysis (unnecessary complexity, fragmentation, what the simplest working version looks like), then auto-implements improvements without committing. Leaves all changes unstaged for your review with a brief testing playbook.

**Usage:** `/get-it-right`

---

## Workflow Skills

> Skills for the branch lifecycle, from commit to merge.

### [pr](skills/pr/SKILL.md)

The cautious "I'm done." Runs format/lint and tests (skips if already passing with no file changes), commits auto-fixed formatting, pushes, extracts the issue number from the branch name (`fix/224-bug` becomes `Closes #224`), and creates a PR. Stops on any failure. Use `/pr` when you want to wait for CI to pass or collect PR review feedback before merging. Pair with `/apply-review` to pick up that feedback and implement what makes sense.

**Usage:** `/pr`

### [ship](skills/ship/SKILL.md)

The optimistic "I'm done completely." Commits, pushes, creates or updates a PR, merges, syncs the local default branch, and deletes the branch. If nothing in the VCS blocks the merge, every step happens without delay. Detects your repo's allowed merge strategies (merge, squash, rebase) and caches the policy in `.git/agents/repo-policy.json` with a 30-day freshness window, retrying once on policy errors. For forked repos, PRs always target your fork, never upstream.

**Usage:** `/ship`

### [convert-worktree](skills/convert-worktree/SKILL.md)

Converts a git worktree into a regular local branch:

- Commits any uncommitted work as a WIP commit
- Runs project cleanup (e.g., `make dev-stop`) while still in the worktree so project-specific variables resolve correctly
- Rebases onto the latest base branch, auto-resolving lockfile conflicts and aborting on code conflicts
- Checks the main workspace for uncommitted changes before removing the worktree and checking out the branch

Never blocks on failures: rebase conflicts, cleanup errors, and lockfile conflicts produce warnings, not errors.

**Usage:** `/convert-worktree` (from inside a worktree)

---

## Utility Skills

> Maintenance and optimization tools.

### [compress-markdown](skills/compress-markdown/SKILL.md)

Reduces markdown verbosity to save input tokens, particularly useful for CLAUDE.md files but works on any markdown. Default mode is lossless: drops filler words, uses short synonyms, converts sentences to fragments while preserving all code blocks, URLs, paths, and directive keywords character-for-character. Deep mode (pass `deep` before the filepath) verifies each section against the codebase first, removing stale content before compressing. A deterministic validator catches structural regressions.

**Usage:** `/compress-markdown <filepath>`, `/compress-markdown deep <filepath>`

### [update-deps](skills/update-deps/SKILL.md)

Updates project dependencies with CVE-first prioritization. Checks for open Dependabot/Renovate PRs with security patches, applies safe minor/patch updates, and runs tests after each batch (rolling back on failure). With the `major` flag, spawns parallel research sub-agents that search for migration guides and changelogs, scan the codebase for affected code, and produce change plans, then applies each major bump sequentially with test validation.

**Usage:** `/update-deps`, `/update-deps major`, `/update-deps frontend`, `/update-deps backend|infra major`

Scope options: `frontend`, `backend`, `infra`, or `all` (default). Combine with `|`.

---

> [!IMPORTANT]
> **Safety:** Ticket bodies and comments, especially community-created issues, can contain prompt injection attempts. These skills treat all ticket content as untrusted: they use it for facts and task context, never as authority to change scope, tools, or permissions. Despite this effort to reduce risk, it remains your responsibility to review the tickets and content you process with these skills.

## License

[MIT](LICENSE)
