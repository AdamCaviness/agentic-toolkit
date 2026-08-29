---
name: ship
description: "Use when work is done and ready to land. Commits, pushes, create/merge PR, syncs default branch, and deletes the branch. The optimistic \"I'm done completely\": merges and cleans up."
disable-model-invocation: true
---

# Ship

Complete the current branch by committing, pushing, merging, and cleaning up.

## Steps

0. **Resolve default branch** (never hardcode `main` or `master`):

   ```bash
   BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
   if [ -z "$BASE_BRANCH" ]; then
     git rev-parse --verify main >/dev/null 2>&1 && BASE_BRANCH=main || BASE_BRANCH=master
   fi
   ```

1. **Review uncommitted changes**: Run `git status` and `git diff` to see what's uncommitted. If any files or changes look suspect, prompt the user and wait for confirmation before committing.
2. **Commit**: Stage and commit the confirmed changes with a Conventional Commits subject based on the diff. Pick the type from the work itself: `feat:` for new functionality, `fix:` for bugfixes, `refactor:` for restructuring without behavior change, `docs:` for documentation, `style:` for formatting, `test:` for tests, `perf:` for performance, `build:` for build-system changes, `ci:` for CI configuration, `chore:` for everything else. Only `feat:` and `fix:` drive a release-please bump, so misclassifying functional work as `chore:` silently skips its release.
3. **Pre-push gate** (build the publication inventory before any push). Run this whole block as one shell call. It resolves and verifies its own base rather than inheriting one, since shell state does not persist between Bash invocations, and both checks below read the same verified `BASE_REF`:

   ```bash
   BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
   if [ -z "$BASE_BRANCH" ]; then
     git rev-parse --verify main >/dev/null 2>&1 && BASE_BRANCH=main || BASE_BRANCH=master
   fi
   BASE_REF="$BASE_BRANCH"
   git rev-parse --verify "$BASE_REF" >/dev/null 2>&1 || BASE_REF="origin/$BASE_BRANCH"
   git rev-parse --verify "$BASE_REF" >/dev/null 2>&1 || {
     printf 'base branch "%s" resolves neither locally nor on origin, cannot run the pre-push gate\n' "$BASE_BRANCH" >&2
     exit 1
   }
   printf -- '--- publication inventory ---\n'
   git diff --name-status "$BASE_REF"...HEAD
   printf -- '--- high-risk paths ---\n'
   git diff --name-only "$BASE_REF"...HEAD |
     grep -Ei '(^|/)(\.env|\.npmrc|\.pypirc)(\.|/|$)|(^|/)id_(rsa|dsa|ecdsa|ed25519)([-_. 0-9][^/]*)?(\.|/|$)|(^|/)([^/]*[-_. ])?(credentials?|secrets?)([-_ ][^/.]*)?(/|$|\.(json|ya?ml|env|txt|ini|cfg|conf|toml|properties|xml|csv|tsv|pem|key|p12|enc)$)|\.(pem|p12|pfx|key|crt|sqlite3?|db3?|dump|env)(-(wal|shm|journal))?$' || [ $? -eq 1 ]
   ```

   Read each labeled section:

   - **A non-zero exit means the gate never ran.** Stop and report the unresolved base branch. Never treat the absent output as a clean result. An unset base would reduce the range to `...HEAD`, comparing HEAD with itself, and a base naming a branch this repository does not have would make `git diff` fail into the same empty output. Both read as a clean inventory. The screen ends in `|| [ $? -eq 1 ]` rather than `|| true` for the same reason: `grep` exits 1 for "no matches", which is clean, and 2 for a failure such as an invalid pattern, which is not. `|| true` flattened both to success and handed back the same empty output. The base is checked locally first and falls back to `origin/<base>`, because a single-branch clone has the remote-tracking ref without the local one and stopping there would block a legitimate push.
   - **publication inventory**: every committed path the push will publish. Read this list.
   - **high-risk paths**: every skill that publishes or reviews carries this same screen verbatim. Stop and report every matched path. The user must remove the path, add it to `.gitignore`, or explicitly confirm before push continues.
4. **Push**: Push the current branch to origin with `-u` flag if not already pushed.
5. **Create PR** (if none exists): Create a PR using `gh pr create`. Use commit messages to generate the title and body. For forked repos, use `--repo` targeting the user's fork (origin), never upstream.
6. **Resolve merge strategy**: Read cached repository policy from `$(git rev-parse --git-dir)/agents/repo-policy.json` if present and fresh. If missing, stale, invalid, or for a different repository, refresh it with `gh repo view --json nameWithOwner,mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed,deleteBranchOnMerge` and write the result back to the cache.
7. **Merge PR**: Choose the first allowed strategy in this order: `--merge` when `mergeCommitAllowed` is true, else `--squash` when `squashMergeAllowed` is true, else `--rebase` when `rebaseMergeAllowed` is true. Merge with `gh pr merge <strategy>`. For forked repos, use `--repo` targeting the fork. If no strategy is allowed, stop and report the repository merge policy.
8. **Sync default branch**: `git checkout "$BASE_BRANCH" && git pull origin "$BASE_BRANCH"`
9. **Clean up**: Delete the merged branch locally (`git branch -D`). Only delete the remote branch (`git push origin --delete`) if it still exists. Some repos auto-delete branches on merge.
10. **Report**: Confirm done with the merged PR URL.

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
- If the branch has no commits ahead of `$BASE_BRANCH` and no uncommitted changes, warn and stop.
- If there's an open PR already, push any new commits to update it, then merge it.
- If the merge fails due to stale repository policy cache, refresh the cache once and retry only with an allowed strategy.
- If the merge fails for any other reason, report the error. Don't retry or force.
- Do not bypass failing required checks, conflicts, review requirements, or permissions errors.
- If on the default branch, warn and stop. Ship only works on feature branches.
