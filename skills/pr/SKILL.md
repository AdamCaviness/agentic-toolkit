---
name: pr
description: Format, lint, test, commit, push, and create a pull request — the single "I'm done" command.
---

# PR — Format, Lint, Test, Commit, Push, Create Pull Request

Single command to go from "I'm done" to "PR is open."

## Workflow

1. **Verify not on main**: Check current branch with `git branch --show-current`
   - If on `main` or `master`, stop and tell user to create a feature branch first

2. **Format and lint** (check CLAUDE.md for the project's commands):
   - **Skip if** passing output is visible in this conversation and no files changed since. Cite the prior result.
   - If it fails, report errors and stop

3. **Run tests** (check CLAUDE.md for the project's test command):
   - **Skip if** passing output is visible in this conversation and no files changed since. Cite the prior result.
   - If tests fail, report failures and stop

4. **Stage and commit auto-fixed files**:
   - Check `git status` for changes from formatting
   - If there are changes: stage them, commit with message "Auto-format and lint fixes"
   - If no changes: skip

5. **Push to remote**:
   - Check if branch exists on remote: `git ls-remote --heads origin $(git branch --show-current)`
   - If new branch: `git push -u origin $(git branch --show-current)`
   - If existing: `git push`
   - If already up-to-date: skip

6. **Extract issue number from branch name**:
   - Pattern: `<category>/<number>-<desc>` → `#<number>`
   - Example: `fix/224-streaming-upload-size-check` → `224`
   - If no number found: warn "No issue number found in branch name — add Closes #NNN manually if applicable"

7. **Create or update PR**:
   - Check if PR exists: `gh pr view --json number,url 2>/dev/null`
   - If PR exists: show URL, say "PR updated with latest changes"
   - If no PR exists:
     - Analyze `git diff main...HEAD` and `git log main..HEAD --oneline` to understand scope
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

         Generated with [Claude Code](https://claude.com/claude-code)
         ```
   - Return PR URL to user

## Error Handling

- **On main branch**: Stop immediately, suggest creating feature branch
- **No changes AND no commits ahead of main**: Inform user there's nothing to PR
- **Format/lint fails**: Stop, show errors — cannot push unlinted code
- **Tests fail**: Stop, show failures — cannot push broken code
- **Push rejected (behind remote)**: Suggest `git pull --rebase origin <branch>`
- **`gh` not authenticated**: Detect with `gh auth status`, show clear error
- **No issue number in branch**: Warn but continue — don't block the PR

## Usage

```bash
# The only command you need
/pr

# Typical workflow:
# 1. Make changes on feature branch
# 2. /pr (does everything: format, lint, test, commit, push, PR)
# 3. Review PR in GitHub
```
