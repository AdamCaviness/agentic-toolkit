---
name: next-ticket
description: Use when looking for the next ticket to work on. Detects the project's ticket system (GitHub Issues, Jira, GitLab Issues, Azure Boards, etc.), fetches all open tickets, scores by severity/simplicity/value/blocking-power/dependencies, picks the best candidate, branches, implements, tests, formats, and waits for review with a UI testing tip.
---

# Next Ticket

Pick the highest-value open ticket, implement it end-to-end, and wait for review.

## Prerequisites

Verify you're in a git repo before starting. If not, tell the user and stop.

## Step 1: Detect Ticket System

Determine which ticket system this project uses. Check in this order:

1. **Cached config**: Check for a `next-ticket-config.json` file in the system temp directory. It maps project root paths to ticket system names. If the current project has an entry, use that value.
2. **Auto-detect**: Run `git remote -v` and interpret the host to determine the likely ticket system (e.g., github.com suggests GitHub Issues, bitbucket.org suggests Jira, gitlab.com suggests GitLab Issues, dev.azure.com or visualstudio.com suggests Azure Boards).
3. **Ask the user**: If auto-detect fails, ask: "What ticket system does this project use?" Accept a free-form answer (e.g., "jira", "github issues", "linear", "shortcut").

Once determined, cache the value in `next-ticket-config.json` in the system temp directory, keyed by project root path. Create the file if it doesn't exist. Merge with existing entries if it does.

Confirm the detected system to the user (e.g., "Detected ticket system: GitHub Issues"). If the user corrects it, update the cached value and proceed with their answer.

> **Tip**: If auto-detect consistently gets it wrong for a project (e.g., a GitHub-hosted repo that uses Jira), add `ticketSystem: jira` to the project's CLAUDE.md to skip detection.

## Step 2: Fetch All Open Tickets

Using whatever CLI tools, MCP tools, or APIs are available in the current session, fetch all open tickets from the detected system.

**Common tools by platform:**
- GitHub Issues: `gh issue list`
- Jira: `jira` CLI, Atlassian MCP tools, or REST API via `curl`
- GitLab Issues: `glab issue list`
- Azure Boards: `az boards work-item list`
- Other: Use whatever is available. If no tool is found, tell the user what to install and stop.

Normalize the fetched data into this shape (write to a temp file):

```json
[
  {
    "id": "42",
    "title": "Fix auth token refresh race condition",
    "body": "Full description...",
    "labels": ["bug", "severity:high"],
    "assignees": [],
    "created_at": "2025-01-15T10:00:00Z",
    "comments": []
  }
]
```

Also fetch recently closed/resolved tickets (titles and IDs only) to understand what's already been done.

If zero open tickets, tell the user and stop.

## Step 3: Score and Rank

Read every ticket's title, full body, labels, and comments. Build a mental scorecard for each ticket using these factors:

### Scoring Factors

| Factor | Weight | How to Assess |
|--------|--------|---------------|
| **Severity** | High | Read severity labels or priority fields. No label = medium. |
| **Simplicity** | High | From the description and suggested fix: is this a focused, well-scoped change? Prefer tickets where the fix is clear and contained over vague or sprawling ones. |
| **Blocking power** | High | Does this ticket's body or comments mention it blocks other tickets? Are other tickets referencing this one as a dependency? Prefer prereqs. |
| **Value** | Medium | Is this foundational (auth, data model, core flow)? Or cosmetic? Foundational work compounds. |
| **Dependencies** | Eliminates | If the ticket explicitly depends on another open ticket, skip it. |
| **Assignee** | Eliminates | If already assigned to someone, skip it. |
| **Age** | Low | Older tickets are slightly preferred (avoid starvation). |
| **Clarity** | Medium | Is the problem well-defined with evidence and a suggested fix? Vague tickets are riskier for AFK implementation. |

### Decision Process

1. **Eliminate** tickets that have unmet dependencies on other open tickets, or are assigned.
2. **Rank** remaining tickets. Severity and simplicity dominate. Blocking power breaks ties.
3. **Pick the top candidate.** If two tickets are very close, prefer the simpler one (higher confidence of correct AFK implementation).

### Announce Selection

Print a brief rationale, formatting the ticket ID according to the platform (e.g., `#42` for GitHub/GitLab, `PROJ-42` for Jira, `42` for Azure Boards):

```
Selected: <ticket-id> - "Fix auth token refresh race condition"
  Severity: high | Simplicity: focused (single file) | Blocks: <id>, <id>
  Reason: Highest severity, clear fix direction, unblocks two other tickets.
```

## Step 4: Validate Against Current Code

Before branching, verify the selected ticket is still valid on the latest codebase.

1. **Locate the relevant code.** Use the ticket body, referenced files, error messages, and stack traces to find the code in question. If the ticket references files or functions that no longer exist, the ticket may be stale.
2. **Check for prior fixes.** Search git log for commits referencing the ticket ID. Look for evidence of prior work on this ticket.
3. **Reproduce the problem.** Attempt to confirm the ticket is still valid:
   - **Bugs**: Read the relevant code paths. Is the described bug still present in the logic?
   - **Features**: Is the requested functionality already implemented?
   - **Refactors/chores**: Is the target code still in the state described?
4. **Verdict:**
   - **Still valid**: proceed to Step 5.
   - **100% resolved**: All items in the ticket are addressed. Mark as resolved with a comment explaining what you found, then loop back to Step 3 and pick the next candidate.
   - **Partially resolved**: Some items remain. You have two options:
     - **Work on it**: If the remaining work is a good candidate (simple, high-value), proceed to Step 5.
     - **Refine and skip**: If you'd rather pick a different ticket, do NOT close this one. Instead, edit the ticket body to remove completed items (keep only remaining work), update the title to reflect the narrower scope, add a comment summarizing what was already done, then loop back to Step 3. The refined ticket becomes eligible for future iterations.
   - **Can't determine**: proceed with caution and note uncertainty.

## Step 5: Create Branch

Determine the branch category from the ticket content:
- Bug/defect/error/crash/race condition/fix = `fix/`
- New feature/add/create/implement = `feat/`
- Refactor/rename/restructure/clean up = `refactor/`
- Documentation = `docs/`
- Everything else = `chore/`

Ensure you're on the latest default branch (typically `main` or `master`), then create a new branch following the naming convention `<category>/<ticket-id>-<brief-desc>` (e.g., `fix/42-auth-token-refresh-race`). Keep the description part to 3-5 hyphenated words derived from the ticket title.

## Step 6: Write Failing Tests (TDD)

**Tests come first.** The ticket body is your spec. Translate it into concrete test assertions before writing any implementation code.

1. **Explore**: Read the files referenced in the ticket. Understand the existing code, test patterns, framework, file naming, and style before writing anything.
2. **Derive the contract**: From the ticket body, identify the specific behaviors that should change or be added. What should be true when this ticket is resolved?
3. **Write tests that assert the desired behavior.** Match the project's existing test patterns exactly.
   - **Bugs**: Write a test that reproduces the bug. It should fail now and pass after the fix. The test asserts the *correct* behavior, not the buggy behavior.
   - **Features**: Write tests for the new functionality's expected inputs, outputs, and edge cases.
   - **Refactors**: Skip this step. Refactors should not change behavior. Proceed to Step 7.
   - **Docs/chores**: Skip this step. Proceed to Step 7.
4. **Run the new tests and confirm they fail.** If they pass already, the ticket may be resolved. Loop back to Step 4 to re-validate; it will handle the verdict. If they fail for the wrong reason (e.g., import error, syntax), fix the test before proceeding.

**Do not write implementation code until you have failing tests that represent the ticket's contract.**

## Step 7: Implement Until Green

1. **Implement**: Write the minimum code to make the failing tests pass. Follow existing code patterns and conventions. Respect CLAUDE.md rules.
2. **Run your new tests.** Iterate until they pass.
3. **Run the full test suite** to ensure nothing else broke. Use the project's test runner (e.g., `make test`, `npm test`, `pytest`, `go test ./...`, `cargo test`).
4. **Keep it focused**: Only change what the ticket requires. Don't refactor unrelated code, add unrequested features, or "improve" surrounding code.

If a pre-existing test fails:
- If your change broke it: fix your implementation to not break it, or update the test if your change intentionally changes behavior.
- If it's a pre-existing flaky test unrelated to your changes: note it and move on.

If the ticket is unclear or the fix direction is ambiguous, make the most reasonable interpretation and note your assumptions in the commit message.

**Do not proceed until all tests pass, both yours and pre-existing.**

## Step 8: Format

Run the project's formatter (e.g., `make nice`, `npm run format`, `cargo fmt`, `go fmt ./...`, `black .`). If it modifies files, that's expected. If it fails, investigate and fix.

## Step 9: Commit

Stage and commit all changes with a descriptive message referencing the ticket. Use whatever closing syntax the platform recognizes for auto-closing tickets from commits (e.g., `Closes #42` for GitHub, `Resolves PROJ-42` for Jira).

Do NOT push. Do NOT create a PR. Wait for the user.

## Step 10: Wait for Review

Print a brief summary:

```
Done. Ready for review.

Branch: <branch-name>
Ticket: <ticket-id> - <ticket title>
Files:  <list changed files>

To test in the UI: <one sentence describing the specific UI action that exercises this change>
```

The UI testing tip must be **specific and actionable**, not "test the feature" but "log in, wait 15 minutes for the token to expire, then click any nav link, it should refresh silently instead of kicking you to login."

## Rules

- **Never push or create PRs.** The user reviews first.
- **Never skip tests.** AFK implementation demands high confidence.
- **Never pick an assigned ticket.** Someone else is working on it.
- **Never pick a ticket with unmet dependencies.** It can't be completed.
- **Validation (Step 4): refine, don't close.** If a ticket has remaining work, edit the ticket to reflect only what remains (update title and body), then move to the next candidate. Never close a ticket that isn't 100% resolved.
- **Implementation (Steps 5-9): fully implement.** Once you pick a ticket, complete it entirely. No partial commits, no WIP commits, no handoffs. The scoring in Step 3 filters for simplicity and clarity precisely so that picked tickets can be fully implemented touch-free.
- **If no suitable ticket exists** (all assigned, all blocked, none clear enough for AFK), tell the user and stop.
- **Clean up temp files** when done.
