---
name: pr
description: Format, lint, test, commit, push, and create a pull request. The single "I'm done" command.
disable-model-invocation: true
---

# PR: Format, Lint, Test, Commit, Push, Create Pull Request

Single command to go from "I'm done" to "PR is open."

## Workflow

0. **Resolve default branch** (shared branch lifecycle contract from AGENTS.md):

   ```bash
   BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
   if [ -z "$BASE_BRANCH" ]; then
     git rev-parse --verify main >/dev/null 2>&1 && BASE_BRANCH=main || BASE_BRANCH=master
   fi
   ```

1. **Verify not on default branch**: Check current branch with `git branch --show-current`
   - If equal to `$BASE_BRANCH`, stop and tell user to create a feature branch first

2. **Inventory working tree and commit implementation work**:
   - Capture the working-tree state with `git status --porcelain` and the untracked path list with `git ls-files --others --exclude-standard`
   - Classify every reported path as staged, unstaged, or untracked. Run `git diff --cached` for staged content and `git diff` for unstaged content. Read each untracked file before staging it.
   - If any paths are present, this is the implementation submission. Stage the intended paths and commit them with a descriptive message derived from the diff. Do not use a `wip:` placeholder. Do not run `git add -A` blindly; stage by explicit path so untracked files are added intentionally.
   - If a path should be excluded from the PR, the user must add it to `.gitignore` or stash it before `/pr` continues. The skill does not stash silently.
   - If the working tree is clean, skip the commit and continue. The branch must already have implementation commits ahead of `$BASE_BRANCH` (verified in step 6).

3. **Format and lint** (check CLAUDE.md for the project's commands):
   - **Skip if** passing output is visible in this conversation and no files changed since. Cite the prior result.
   - If it fails, report errors and stop

4. **Run tests** (check CLAUDE.md for the project's test command):
   - **Skip if** passing output is visible in this conversation and no files changed since. Cite the prior result.
   - If tests fail, report failures and stop

5. **Stage and commit auto-fixed files**:
   - Check `git status` for changes from formatting
   - If there are changes: stage them, commit with message "Auto-format and lint fixes". This is a separate commit from the implementation commit in step 2.
   - If no changes: skip

6. **Pre-push gate** (build the publication inventory before any push):
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
     - Analyze `git diff "$BASE_BRANCH"...HEAD` and `git log "$BASE_BRANCH"..HEAD --oneline` to understand scope
     - Create PR with `gh pr create`:
       - Concise title (under 70 chars, conventional commit style)
       - Body:
         ```
         ## Summary
         <3-5 bullet points on what and why>

         ## Changes
         <Key technical changes as bullet list>

         ## Testing
         <What was tested locally>

         Closes #<number>
         ```
   - Return PR URL to user

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

## Usage

```bash
# The only command you need
/pr

# Typical workflow:
# 1. Make changes on feature branch
# 2. /pr (does everything: inventory, commit, format, lint, test, push, PR)
# 3. Review PR in GitHub
```
