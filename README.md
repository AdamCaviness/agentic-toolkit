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
