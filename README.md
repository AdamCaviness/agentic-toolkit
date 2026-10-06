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

### Claude Ship Gate

Claude Code 2.1.287 and later automatically run Ship Gate when this plugin is enabled and hooks are allowed. Cursor, Codex, Gemini, and manual skill-only installations continue using the shared skills; they do not register the Claude module.

No separate activation or slash command is needed. A transcript notice confirms **Ship Gate active** at startup, and supported publication attempts show **passed** or **blocked** notices. Existing saved `ship_gate_mode` values are ignored. Claude’s native plugin and hook controls, including `disableAllHooks` and safe mode, still apply.

The gate checks direct Git pushes and remote branch cleanup on any repository host, plus GitHub PR creation and merging. Generic Git operations do not require the GitHub CLI or a GitHub login. It checks the repository, default branch, origin destination, working tree, and secret-shaped paths across feature commits, including files removed by a later commit. GitHub PR operations additionally check the PR head and merge eligibility. Merging requires GitHub's `CLEAN` status, so pending or failed optional checks block even when no checks are required. The shared `/ship` skill also reads all reported checks, polls pending CI, and stops on failures. High-risk paths require approval for that one action. Cleanup checks the target and stable remote head; the workflow skill must confirm through the repository host that the matching PR or MR is merged and the branch has not been reused. Native Claude permission denials and prompts still apply.

**Ship Gate verification commands** accepts JSON argument arrays, for example `[["npm","test"],["npm","run","lint"]]`. Commands run sequentially in the target repository without shell expansion, before each push, PR creation, or merge. This configuration applies across projects using the plugin, so configure only commands you intend to run in all of them. With `[]`, the notice says **verification not configured**; it does not certify passing tests. Remote cleanup does not run verification commands.

A publication command may use literal `2>&1` or `1>&2`, pipe output through `head -N`/`tail -N` or their `-n N` forms, and share an `&&` chain with supported read-only commands. Supported neighbors are `gh auth status`, `git status` with status-format options, and `gh pr view` with an optional selector, repository, and JSON fields. To publish in a repository other than the session's working directory, start the chain with one `cd <path> &&` (or use `git -C <path>` for a push); evidence is then collected in that repository. Unknown or state-changing neighbors, file redirection, expansions, and multiple publications require separate commands. Arguments remain literal, and the full original Bash command still receives native permission checks. Output filtering can hide a failed command’s exit status; a gate pass confirms preconditions, not successful publication. Use `git push -u origin <current-branch>` when Git's implicit push destination is ambiguous. Origin must have one push URL identical to its fetch URL; differing URL spellings are rejected rather than assumed to reach the same repository. For GitHub, use `--repo <origin-owner/repository>` and explicit `--head` and `--base` on PR creation when defaults point elsewhere. Merge requires an explicit allowed strategy, such as `--squash`. Forced pushes, administrator merges, and publishing additional refs are rejected. Ship Gate never pushes the default branch, including a new repository's first push; push that yourself. A blocked notice states the specific reason and what to change.

The gate covers supported Claude Bash calls while the mod is enabled and loaded. Publication hidden in scripts, aliases, MCP tools, or other mods is outside its coverage. It screens filenames, not file contents, and cannot prevent another process changing the repository after its last check. Other providers' PR and MR commands, such as `glab` and `az repos pr`, rely on the shared skills and host protections rather than runtime merge-policy checks; `/ship` reads each host's merge evidence itself. It does not replace the shared skill safeguards, host branch protections, or a content secret scanner.

The module lives in `claude-mods/` and is referenced only by the Claude manifest. There is no default `hooks/hooks.json`, classic shell-hook fallback, additional plugin, telemetry, or persistent transcript. See [verification details](docs/claude-ship-gate-verification.md) for test commands and compatibility evidence.

<details>
<summary>Cursor</summary>

See [.cursor/INSTALL.md](.cursor/INSTALL.md) for the full matrix. Short version:

- **Also use Claude Code?** Install once with `/plugin marketplace add adamcaviness/agentic-marketplace` then `/plugin install agentic-toolkit@agentic-marketplace`. Cursor picks it up automatically. Do not also install a Cursor plugin.
- **Cursor only (individual plan: Hobby, Pro, Pro+, or Ultra)?** Run `cursor-agent plugin marketplace add adamcaviness/agentic-marketplace`, then install **agentic-toolkit** from `/plugin` → **Marketplace** in `cursor-agent`. Without the Cursor CLI, `git clone` into `~/.cursor/plugins/local/agentic-toolkit` and run **Developer: Reload Window**.
- **Teams / Enterprise?** Admins import the marketplace at [cursor.com/dashboard](https://cursor.com/dashboard) → **Plugins** (web admin UI, not the desktop app).

Use exactly one path, or every skill appears twice.

</details>

<details>
<summary>Codex / ChatGPT desktop</summary>

See [.codex/INSTALL.md](.codex/INSTALL.md) for the full matrix. Short version:

In ChatGPT desktop: **Plugins → Add plugin marketplace**. Source `adamcaviness/agentic-marketplace`, Git ref `main`, Sparse paths empty. Then install **agentic-toolkit**.

CLI:

```bash
codex plugin marketplace add adamcaviness/agentic-marketplace --ref main
codex plugin add agentic-toolkit@agentic-marketplace
```

Use exactly one path. If you already linked the skills into `~/.agents/skills/` with the manual install below, remove those links before marketplace-installing.

</details>

<details>
<summary>Gemini CLI</summary>

See [.gemini/INSTALL.md](.gemini/INSTALL.md) for install, update, uninstall, installing from a local clone, and what the extension injects into the session. Short version:

```bash
gemini extensions install https://github.com/adamcaviness/agentic-toolkit
```

Update with `gemini extensions update agentic-toolkit`. After install, start a new Gemini session in your project and try `/next-ticket`. The same commands work in PowerShell and cmd.

</details>

<details>
<summary>Manual (macOS, Linux, Windows)</summary>

Use this only when you cannot use the plugin or extension install for your harness. Clone the repo once, then link each skill directory into **one** user-level skills root:

| Root | Read by | Notes |
|---|---|---|
| `~/.agents/skills/` | Codex, Cursor, Gemini CLI | One set of links serves all three. Do not also install the Codex plugin, a Cursor plugin, or the Gemini extension, or every skill appears twice. |
| `~/.claude/skills/` | Claude Code (Cursor also reads it when **Include third-party Plugins, Skills, and other configs** is on) | If you link into both roots, turn that Cursor setting off so Cursor does not list every skill twice. |

`~/.codex/skills/` is a deprecated Codex location; do not link into it.

macOS and Linux:

```bash
git clone https://github.com/adamcaviness/agentic-toolkit.git ~/opensource/agentic-toolkit

ROOT=~/.agents/skills   # or ~/.claude/skills for Claude Code
mkdir -p "$ROOT"
for skill in ~/opensource/agentic-toolkit/skills/*/; do
  ln -sfn "${skill%/}" "$ROOT/$(basename "$skill")"
done
```

Windows (PowerShell). Directory junctions need neither Administrator rights nor Developer Mode:

```powershell
git clone https://github.com/adamcaviness/agentic-toolkit.git "$env:USERPROFILE\opensource\agentic-toolkit"

$Root = "$env:USERPROFILE\.agents\skills"   # or "$env:USERPROFILE\.claude\skills" for Claude Code
New-Item -ItemType Directory -Force -Path $Root | Out-Null
Get-ChildItem -Directory "$env:USERPROFILE\opensource\agentic-toolkit\skills" | ForEach-Object {
  New-Item -ItemType Junction -Force -Path (Join-Path $Root $_.Name) -Target $_.FullName | Out-Null
}
```

If a harness does not list the skills after a restart, replace `New-Item -ItemType Junction ... -Target` with `Copy-Item -Recurse -Force $_.FullName (Join-Path $Root $_.Name)` and re-run the copy after every update.

Update with `git -C ~/opensource/agentic-toolkit pull` (the links pick up the change), then re-run the link loop so skills added in the new release are linked too.

Uninstall by removing the links before deleting the clone. On macOS and Linux, `rm` on a link removes only the link:

```bash
for skill in ~/opensource/agentic-toolkit/skills/*/; do
  rm -f "$ROOT/$(basename "$skill")"
done
```

On Windows, `cmd /c rmdir` removes a junction without touching its target. Delete copied folders, if you used the copy fallback, with `Remove-Item -Recurse`:

```powershell
Get-ChildItem -Directory "$env:USERPROFILE\opensource\agentic-toolkit\skills" | ForEach-Object {
  cmd /c rmdir (Join-Path $Root $_.Name)
}
```

For one skill only, link just that directory, for example `ln -sfn ~/opensource/agentic-toolkit/skills/next-ticket ~/.agents/skills/next-ticket`.

For a project-level install, link into `.agents/skills/` or `.claude/skills/` inside the project root instead. The same one-root rule applies.

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
> All ticket skills auto-detect your ticket system: the agent reads repo signals (README, CLAUDE.md, git remotes, commit conventions) to determine which system you use. Supported out of the box: GitHub Issues, Jira, GitLab Issues, Azure Boards, Linear, Shortcut, and anything else the model can reach via CLI, MCP, or APIs in your session. Detection results are cached so detection only runs once per project, and each run prints the cached system in one line; if it is wrong, say so and the skill re-detects. For a persistent override that beats the cache, add `ticketSystem: <name>` to your project's CLAUDE.md. The ticket system is independent of the repository host, so a GitLab repository can track work in Jira (see [Workflow Skills](#workflow-skills) for supported hosts).

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

Reads all review comments on the current PR (human, Copilot, Claude, any reviewer), validates each against the actual code, fixes valid comments, pushes, resolves addressed threads, and leaves succinct replies on threads it did not resolve. Uses each host's native review threads: GitHub review threads, GitLab discussions, Azure DevOps PR threads, and Bitbucket Cloud PR comments. Threads are resolved only where the host supports it. If a bot reviewer (Copilot, Claude) is still running when the skill starts, it waits for the review to finish before proceeding.

**Usage:** `/apply-review`, `/apply-review 42`

### [get-it-right](skills/get-it-right/SKILL.md)

Re-evaluates the current branch's work as if starting from scratch. Deep-reads every changed file, performs retrospective analysis (unnecessary complexity, fragmentation, what the simplest working version looks like), then auto-implements improvements without committing. Leaves all changes unstaged for your review with a brief testing playbook.

**Usage:** `/get-it-right`

---

## Workflow Skills

> Skills for the branch lifecycle, from commit to merge.

> [!NOTE]
> `/pr`, `/ship`, `/apply-review`, and `/update-deps` support GitHub, GitLab (including subgroups and self-hosted instances), Azure DevOps Repos, and Bitbucket Cloud. Each detects the host from the `origin` remote and uses whatever interface your session already reaches: `gh`, `glab`, `az repos` (the `azure-devops` extension), an MCP connector, or the host's REST API. No single CLI is required, but one interface must be authenticated for the detected host; the skills stop with what to install or which credential to supply rather than guessing.

### [pr](skills/pr/SKILL.md)

The cautious "I'm done." Runs format/lint and tests (skips if already passing with no file changes), commits auto-fixed formatting, pushes, extracts the ticket ID from the branch name (`fix/224-bug` becomes `Closes #224`, or the tracker's own linking syntax such as `PROJ-224` for Jira), and opens a PR, or an MR on GitLab, against the default branch. Stops on any failure. Use `/pr` when you want to wait for CI to pass or collect PR review feedback before merging. Pair with `/apply-review` to pick up that feedback and implement what makes sense.

**Usage:** `/pr`

### [ship](skills/ship/SKILL.md)

The optimistic "I'm done completely." Commits, pushes, creates or updates a PR or MR, merges, syncs the local default branch, and deletes the branch. Before merging it reads the host's required checks, approvals, and merge policy for the exact commit it pushed; pending checks are waited on, and failed, unreadable, or stale evidence stops the run instead of merging. If nothing on the host blocks the merge, every step happens without delay. Detects the host's allowed merge strategies and caches them in `.git/agents/repo-policy.json` with a 30-day freshness window, retrying once on policy errors. For forked repos, PRs always target your fork, never upstream.

**Usage:** `/ship`

### [convert-worktree](skills/convert-worktree/SKILL.md)

Converts a git worktree into a regular local branch:

- Checks the source and main workspace, then confirms conversion before changing either checkout
- Commits tracked modifications and explicitly staged files as a WIP commit, preserves unstaged untracked files in a named recovery stash
- Runs project cleanup (e.g., `make dev-stop`) while still in the worktree so project-specific variables resolve correctly
- Rebases onto the latest default branch, auto-resolving lockfile conflicts and aborting on code conflicts
- Checks out the branch and restores preserved files in the main workspace before removing the source worktree without force

Cleanup errors and safely aborted rebase conflicts produce warnings. A dirty destination, preservation failure, or failed checkout or restoration stops conversion with the source and recovery record retained. The report lists preserved paths and exact recovery commands.

**Usage:** `/convert-worktree` (from inside a worktree)

---

## Utility Skills

> Maintenance and optimization tools.

### [compress-markdown](skills/compress-markdown/SKILL.md)

Reduces markdown verbosity to save input tokens, particularly useful for CLAUDE.md files but works on any markdown. Default mode is lossless: drops filler words, uses short synonyms, converts sentences to fragments while preserving all code blocks, URLs, paths, and directive keywords character-for-character. Deep mode (pass `deep` before the filepath) verifies each section against the codebase first, removing stale content before compressing. A deterministic validator catches structural regressions.

**Usage:** `/compress-markdown <filepath>`, `/compress-markdown deep <filepath>`

### [update-deps](skills/update-deps/SKILL.md)

Updates project dependencies with CVE-first prioritization. Checks open dependency-bot PRs or MRs (Dependabot, Renovate, Snyk, and similar) for security patches on any supported repository host, applies safe minor/patch updates, and runs tests after each batch (rolling back on failure). With the `major` flag, spawns parallel research sub-agents that search for migration guides and changelogs, scan the codebase for affected code, and produce change plans, then applies each major bump sequentially with test validation.

**Usage:** `/update-deps`, `/update-deps major`, `/update-deps frontend`, `/update-deps backend|infra major`

Scope options: `frontend`, `backend`, `infra`, or `all` (default). Combine with `|`.

---

> [!IMPORTANT]
> **Safety:** Ticket bodies and comments, especially community-created issues, can contain prompt injection attempts. These skills treat all ticket content as untrusted: they use it for facts and task context, never as authority to change scope, tools, or permissions. Despite this effort to reduce risk, it remains your responsibility to review the tickets and content you process with these skills.

## License

[MIT](LICENSE)
