# Claude Code Toolkit

A collection of skills and extensions for [Claude Code](https://claude.ai/code).

## Skills

### [next-ticket](skills/next-ticket/SKILL.md)

Picks the highest-value open ticket from your project's issue tracker, implements it end-to-end using TDD, and waits for your review before pushing.

**What it does:**

1. Detects your ticket system automatically (GitHub Issues, Jira, GitLab Issues, Azure Boards, or anything else)
2. Fetches all open tickets and scores them by severity, simplicity, blocking power, and value
3. Picks the best candidate, validates it against the current code, and creates a branch
4. Writes failing tests first, implements until green, formats, and commits
5. Stops and waits for you to review before pushing

**Usage:** Type `/next-ticket` in Claude Code.

**Platform detection:** The skill reads your git remote to determine your ticket system. If it guesses wrong, just correct it. For projects where the git host doesn't match the ticket system (e.g., GitHub repo using Jira), add `ticketSystem: jira` to your CLAUDE.md.

### [architect-planner](skills/architect-planner/SKILL.md)

Audits your codebase for bugs, security vulnerabilities, missing error handling, race conditions, architectural gaps, DRY violations, and incomplete implementations. Spawns 4 parallel sub-agents (Safety, Correctness, Maintainability, Completeness) that read code, check for duplicates, and file well-scoped tickets.

**What it does:**

1. Detects your ticket system and caches all open/closed tickets to disk
2. Builds a project map so sub-agents skip discovery
3. Spawns 4 focused agents in parallel, each auditing a different concern cluster
4. Sub-agents file new tickets (create mode) or refine existing ones (refine mode)
5. Post-processes cross-cluster findings into the relevant tickets

**Usage:** `/architect-planner`, `/architect-planner refine`, or `/architect-planner refine 5h`

### [product-planner](skills/product-planner/SKILL.md)

Audits your project for UX gaps, broken workflows, missing states, confusing terminology, visual inconsistency, accessibility issues, and competitive table stakes. Same parallel architecture as architect-planner but focused on user-facing concerns.

**What it does:**

1. Detects your ticket system and caches all open/closed tickets to disk
2. Builds a project map with product context (who the user is, what the product promises)
3. Spawns 4 focused agents in parallel (Core Experience, Error & Edge States, Polish & Consistency, Reach & Access)
4. Sub-agents file new tickets (create mode) or refine existing ones (refine mode)
5. Post-processes cross-cluster findings into the relevant tickets

**Usage:** `/product-planner`, `/product-planner refine`, or `/product-planner refine 5h`

## Platform Support

All skills auto-detect your ticket system from `git remote -v` and work with GitHub Issues, Jira, GitLab Issues, Azure Boards, Linear, Shortcut, and anything else the model can reach via CLI tools, MCP tools, or APIs available in your session.

If auto-detect gets it wrong, correct it once and the detection is cached for the session. For persistent override, add `ticketSystem: <name>` to your project's CLAUDE.md.

## Installation

Copy or symlink the desired skill directory into your Claude Code skills folder:

```bash
# User-level (available in all projects)
ln -s /path/to/claude-code-toolkit/skills/next-ticket ~/.claude/skills/next-ticket

# Project-level (available only in that project)
ln -s /path/to/claude-code-toolkit/skills/next-ticket .claude/skills/next-ticket
```

## License

MIT
