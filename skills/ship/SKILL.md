---
name: ship
description: Commit, push, create/merge PR, sync local main, delete branch. The standard "I'm done with this branch" workflow.
model: sonnet
---

# Ship

Complete the current branch by committing, pushing, merging, and cleaning up.

## Steps

1. **Review uncommitted changes**: Run `git status` and `git diff` to see what's uncommitted. If any files or changes look suspect, prompt the user and wait for confirmation before committing.
2. **Commit**: Stage and commit the confirmed changes with a descriptive message based on the diff.
3. **Push**: Push the current branch to origin with `-u` flag if not already pushed.
4. **Create PR** (if none exists): Create a PR using `gh pr create`. Use commit messages to generate the title and body. For forked repos, use `--repo` targeting the user's fork (origin), never upstream.
5. **Resolve merge strategy**: Read cached repository policy from `$(git rev-parse --git-dir)/agents/repo-policy.json` if present and fresh. If missing, stale, invalid, or for a different repository, refresh it with `gh repo view --json nameWithOwner,mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed,deleteBranchOnMerge` and write the result back to the cache.
6. **Merge PR**: Choose the first allowed strategy in this order: `--merge` when `mergeCommitAllowed` is true, else `--squash` when `squashMergeAllowed` is true, else `--rebase` when `rebaseMergeAllowed` is true. Merge with `gh pr merge <strategy>`. For forked repos, use `--repo` targeting the fork. If no strategy is allowed, stop and report the repository merge policy.
7. **Sync main**: `git checkout main && git pull origin main`
8. **Clean up**: Delete the merged branch locally (`git branch -D`). Only delete the remote branch (`git push origin --delete`) if it still exists. Some repos auto-delete branches on merge.
9. **Report**: Confirm done with the merged PR URL.

## Repository Policy Cache

- Cache repository-local operational policy in the Git directory at `$(git rev-parse --git-dir)/agents/repo-policy.json`. Do not assume `.git` is a directory; always resolve it with `git rev-parse --git-dir` so worktrees are handled correctly.
- This cache is local, uncommitted, shared by coding agents, and disposable.
- For GitHub merge policy, cache this shape:

```json
{
  "schemaVersion": 1,
  "repository": "owner/name",
  "github": {
    "mergePolicy": {
      "mergeCommitAllowed": false,
      "squashMergeAllowed": true,
      "rebaseMergeAllowed": true,
      "deleteBranchOnMerge": true,
      "fetchedAt": "2026-04-15T16:55:00Z"
    }
  }
}
```

- Treat the cache as fresh for 30 days. If a merge command fails with a repository policy error, refresh the cache once and retry only with an allowed strategy. Do not retry other merge failures.

## Rules

- For forked repos (where origin and upstream differ), NEVER create or merge PRs on the upstream repo. Always target the user's fork (origin).
- If the branch has no commits ahead of main and no uncommitted changes, warn and stop.
- If there's an open PR already, push any new commits to update it, then merge it.
- If the merge fails due to stale repository policy cache, refresh the cache once and retry only with an allowed strategy.
- If the merge fails for any other reason, report the error. Don't retry or force.
- Do not bypass failing required checks, conflicts, review requirements, or permissions errors.
- If on main, warn and stop. Ship only works on feature branches.
