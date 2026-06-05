---
name: pr
description: Format, lint, test, commit, push, and create a pull request. The single "I'm done" command.
disable-model-invocation: true
---

# PR: Format, Lint, Test, Commit, Push, Create Pull Request

Single command to go from "I'm done" to "PR is open."

## Workflow

0. **Resolve default branch** (shared branch lifecycle contract from AGENTS.md):

   First check the PR cache (see the PR Cache section below for its worktree-safe path). If it has a `baseBranch`, use it. Otherwise resolve it with the snippet and write it back to the cache:

   ```bash
   BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
   if [ -z "$BASE_BRANCH" ]; then
     git rev-parse --verify main >/dev/null 2>&1 && BASE_BRANCH=main || BASE_BRANCH=master
   fi
   ```

1. **Verify not on default branch**: if the current branch (from the step 2 preflight read) equals `$BASE_BRANCH`, stop and tell the user to create a feature branch first.

2. **Inventory working tree and commit implementation work**:
   - Gather the read-only preflight in a single shell call rather than one command at a time: current branch (`git branch --show-current`, which also answers step 1), working-tree state (`git status --porcelain`), and the untracked path list (`git ls-files --others --exclude-standard`). Label each section so one call covers steps 1 and 2.
   - Classify every reported path as staged, unstaged, or untracked. Run `git diff --cached` for staged content and `git diff` for unstaged content. For untracked files, do not read each one in full. Skip binary files entirely (never read binary content). For text files, use judgment about signal value: low-signal generated files (lockfiles, golden or snapshot fixtures, vendored or generated code, large data fixtures) get a light skim or no content read, then stage by path; genuine source files get read normally. You may `git add -N` the intended text paths to view them inside a single `git diff` instead of reading each separately, but still stage content explicitly by path.
   - If any paths are present, this is the implementation submission. Stage the intended paths and commit them with a Conventional Commits subject derived from the diff. Pick the type from the work itself: `feat:` for new functionality, `fix:` for bugfixes, `refactor:` for restructuring without behavior change, `docs:` for documentation, `style:` for formatting, `test:` for tests, `perf:` for performance, `build:` for build-system changes, `ci:` for CI configuration, `chore:` for everything else. Only `feat:` and `fix:` drive a release-please bump, so misclassifying functional work as `chore:` silently skips its release. Do not use a `wip:` placeholder. Do not run `git add -A` blindly; stage by explicit path so untracked files are added intentionally.
   - If a path should be excluded from the PR, the user must add it to `.gitignore` or stash it before `/pr` continues. The skill does not stash silently.
   - If the working tree is clean, skip the commit and continue. The branch must already have implementation commits ahead of `$BASE_BRANCH` (verified in step 6).

3. **Format and lint** (check CLAUDE.md for the project's commands):
   - **Skip if** passing output is visible in this conversation and no files changed since. Cite the prior result.
   - On success, report only the exit status and a one-line summary. Do not echo full passing output.
   - If it fails, report errors and stop

4. **Run tests** (check CLAUDE.md for the project's test command):
   - **Skip if** passing output is visible in this conversation and no files changed since. Cite the prior result.
   - On success, report only the pass count and a one-line summary. Do not echo full passing output.
   - If tests fail, report failures and stop

5. **Stage and commit auto-fixed files**:
   - Check `git status` for changes from formatting
   - If there are changes: stage them, commit with message `style: auto-format and lint fixes`. This is a separate commit from the implementation commit in step 2.
   - If no changes: skip

6. **Pre-push gate** (build the publication inventory before any push). Run the read-only checks below in a single shell call with labeled sections, re-resolving `BASE_BRANCH` at the top of that call since shell state does not persist between Bash invocations:

   ```bash
   BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
   if [ -z "$BASE_BRANCH" ]; then
     git rev-parse --verify main >/dev/null 2>&1 && BASE_BRANCH=main || BASE_BRANCH=master
   fi
   ```

   - Verify the branch has commits ahead of base: `git rev-list --count "$BASE_BRANCH..HEAD"`. If zero, stop and report "nothing to publish". This is the only valid no-op exit.
   - Verify the working tree is clean: `git status --porcelain` must be empty. If anything remains, stop and report which paths are still uncommitted. The skill never pushes a branch while staged, unstaged, or untracked work remains.
   - Inventory the publication content: `git diff --name-status "$BASE_BRANCH"...HEAD` lists every committed path the push will publish. Read this list.
   - Screen the publication inventory for high-risk patterns. Stop and report if any path matches `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`, `*.p12`, `*.pfx`, `*credential*`, `*secret*`, or `*.sqlite*`. The user must explicitly confirm or remove the path before push.

7. **Push to remote**:
   - Check if branch exists on remote: `git ls-remote --heads origin $(git branch --show-current)`
   - If new branch: `git push -u origin $(git branch --show-current)`
   - If existing: `git push`
   - If already up-to-date: skip

8. **Extract issue number from branch name**:
   - Pattern: `<category>/<number>-<desc>` → `#<number>`
   - Example: `fix/224-streaming-upload-size-check` → `224`
   - If no number found: warn "No issue number found in branch name. Add Closes #NNN manually if applicable."

9. **Create or update PR**:
   - Check if PR exists: `gh pr view --json number,url 2>/dev/null`
   - If PR exists: show URL, say "PR updated with latest changes"
   - If no PR exists:
     - Understand scope from commit messages and file-level stats, not a re-read of the full content diff: `git log "$BASE_BRANCH"..HEAD` (messages) plus `git diff --stat "$BASE_BRANCH"...HEAD` (changed paths). If the diff content was already captured earlier in this conversation and no commits were added since, reuse it. Read full hunks only for commits whose messages do not explain the change.
     - **Resolve PR template**: if the PR cache (see the PR Cache section below) has a `prTemplatePath` and that file still exists, use it. Otherwise discover it by checking these paths in order, using the first that exists, then write the result to the cache:

       ```bash
       PR_TEMPLATE=""
       for candidate in \
         .github/pull_request_template.md \
         .github/PULL_REQUEST_TEMPLATE.md \
         pull_request_template.md \
         PULL_REQUEST_TEMPLATE.md \
         docs/pull_request_template.md \
         docs/PULL_REQUEST_TEMPLATE.md; do
         if [ -f "$candidate" ]; then
           PR_TEMPLATE="$candidate"
           break
         fi
       done
       ```

     - **Build PR body**:
       - **If template found** (`PR_TEMPLATE` is non-empty): Read the template file. Use it as the skeleton for the PR body:
         - Preserve its structure, headings, and static content (checkboxes, boilerplate, legal text) exactly as written
         - Replace placeholders (HTML comments, blank lines after labels, explicit placeholder text like "Describe your changes") with substantive content derived from the diff, commit messages, and branch context
         - Check or uncheck checkbox items (`- [ ]` / `- [x]`) based on what the branch actually contains (tests added, docs updated, breaking changes present, etc.)
         - If a placeholder asks for information not derivable from the diff or commit history (e.g., Jira ticket URL, Figma link, deployment instructions), leave the original HTML comment in place so the author can fill it after opening the PR
         - If the issue number from step 8 is present and the filled body does not already reference it, append `Closes #<number>` after the last section
       - **If no template found** (or the template file is empty): Use the default body:

         ```
         ## Summary
         <3-5 bullet points on what and why>

         ## Changes
         <Key technical changes as bullet list>

         ## Testing
         <What was tested locally>

         Closes #<number>
         ```

     - Concise title (under 70 chars, conventional commit style)
     - Create PR with `gh pr create` passing the title and built body
   - Return PR URL to user

10. **Transition ticket to In Review (non-blocking)**:
    - Extract a ticket identifier from the branch name. The branch follows `<category>/<ticket-id>-<desc>`, where the ticket ID may be a bare number (`42`) or a prefixed key (`PROJ-42`). If no ticket ID is extractable, skip.
    - Read `next-ticket-config.json` from the system temp directory. If the file does not exist or has no ticket-system entry for the current project root, skip.
    - Reconstruct the full ticket identifier for the detected system if needed (e.g., for Jira, if only a bare number was extracted, prepend the project key from the config or repo signals).
    - Read the project-root entry from the config. If it is a plain string (no `states` key yet) or has no `states.in_review` entry, discover the state. If it has a cached `states.in_review` entry, skip to applying.
      - **Discover (first run only)**: Use whatever CLI, MCP, or API tooling fits the detected ticket system to discover what states or transitions exist. Every system exposes this differently, and teams customize state names extensively, so do not follow a hardcoded recipe. Use model judgment to identify which option represents "awaiting review" (teams call this anything: "In Review", "Review & Test", "Code Review", "QA", etc.). Confirm with the user: "Transition ticket to '<name>'? This choice will be cached for future runs." Migrate the project-root entry from a plain string to the object form (see `next-ticket` Step 4.6 for the schema) if needed, then write the result under `states.in_review`. Store enough system-specific detail to replay mechanically on future runs.
      - **Apply**: Transition the ticket using the cached system-specific details.
    - On any failure (no config file, no ticket system, no transitions available, API error, permission denied, user declines): log a one-line note and continue. This step never blocks the PR workflow.

## Error Handling

- **On default branch**: Stop immediately, suggest creating feature branch
- **Nothing to publish** (clean working tree AND zero commits ahead of `$BASE_BRANCH`): Inform user there's nothing to PR and stop
- **Working tree dirty at pre-push gate**: Stop, list the remaining staged, unstaged, and untracked paths, and tell the user to commit or exclude them
- **High-risk path in publication inventory**: Stop, name each matched path, and require the user to confirm or remove before retrying
- **Format/lint fails**: Stop, show errors. Cannot push unlinted code.
- **Tests fail**: Stop, show failures. Cannot push broken code.
- **Push rejected (behind remote)**: Suggest `git pull --rebase origin <branch>`
- **`gh` not authenticated**: Detect with `gh auth status`, show clear error
- **No issue number in branch**: Warn but continue. Don't block the PR.
- **Ticket state transition fails**: Log the reason and continue. Never block the PR workflow.

## PR Cache

- Cache stable, structural repo facts in `$(git rev-parse --git-dir)/agents/pr-cache.json`. Always resolve the path with `git rev-parse --git-dir` so worktrees are handled, and create the `agents/` directory if it is absent. The cache is local, uncommitted, and disposable.
- Cache shape:

  ```json
  {
    "schemaVersion": 1,
    "baseBranch": "main",
    "prTemplatePath": ".github/pull_request_template.md"
  }
  ```

- These entries are structural configuration, not drifting policy, so there is no TTL and no time-based invalidation. Read them and trust them.
- Repair only on failure: if a cached value stops working (the `prTemplatePath` file no longer exists, or `baseBranch` fails to resolve or yields an empty diff range), re-derive that one entry and overwrite it. Do not invalidate the whole cache.
- Do not cache the format, lint, or test commands. Read those from the project instructions each run.

## Usage

```bash
# The only command you need
/pr

# Typical workflow:
# 1. Make changes on feature branch
# 2. /pr (does everything: inventory, commit, format, lint, test, push, PR)
# 3. Review PR in GitHub
```
