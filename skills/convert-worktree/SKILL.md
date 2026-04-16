---
name: convert-worktree
description: Convert a git worktree into a local branch — rebase onto latest main, clean up project resources, remove worktree, checkout branch in main workspace. Use when finishing work in a worktree.
disable-model-invocation: true
---

# Convert Worktree

Convert a git worktree into a regular local branch. Rebases onto the latest base branch, runs project cleanup, removes the worktree, and checks out the branch in the main workspace.

This skill replaces ExitWorktree — do not call ExitWorktree after this skill runs.

## Steps

### 1. Verify context

Run these checks. Fail fast if any fail.

```bash
# Get main worktree path
MAIN_WORKTREE=$(git worktree list --porcelain 2>/dev/null | head -1 | sed 's/worktree //')

# Confirm we're in a worktree (current dir differs from main worktree)
if [ "$MAIN_WORKTREE" = "$(pwd)" ] || [ -z "$MAIN_WORKTREE" ]; then
  # FAIL: "Not in a worktree. This skill only works from inside a worktree."
fi

# Confirm not detached HEAD
BRANCH=$(git branch --show-current)
if [ -z "$BRANCH" ]; then
  # FAIL: "Detached HEAD — nothing to convert. Checkout a branch first."
fi

WORKTREE_PATH=$(pwd)
```

Detect the base branch dynamically:
```bash
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
# Fall back to main, then master
if [ -z "$BASE_BRANCH" ]; then
  git rev-parse --verify main >/dev/null 2>&1 && BASE_BRANCH=main || BASE_BRANCH=master
fi
```

Announce: "Converting worktree `<WORKTREE_PATH>` (branch `<BRANCH>`) → main workspace at `<MAIN_WORKTREE>`"

### 2. Commit uncommitted work

```bash
# Check for any changes (staged, unstaged, or untracked)
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "wip: uncommitted changes from worktree conversion"
fi
```

`.gitignore` handles exclusions so `git add -A` is safe.

### 3. Project cleanup

Run while still in the worktree so project-specific variables (DB names, ports) resolve correctly.

```bash
# Convention-based: if Makefile has dev-stop, run it
if [ -f Makefile ] && grep -q '^dev-stop:' Makefile; then
  make dev-stop || echo "Warning: make dev-stop failed, continuing"
fi
```

Cleanup failure must not block the conversion.

### 4. Rebase onto latest base branch

```bash
# Fetch latest (skip if no origin remote)
git fetch origin "$BASE_BRANCH" 2>/dev/null || true

# Determine rebase target
if git rev-parse --verify "origin/$BASE_BRANCH" >/dev/null 2>&1; then
  REBASE_TARGET="origin/$BASE_BRANCH"
else
  REBASE_TARGET="$BASE_BRANCH"
fi

# Check if already up-to-date
if git merge-base --is-ancestor "$REBASE_TARGET" HEAD 2>/dev/null; then
  # Already up-to-date, skip rebase
fi
```

Run rebase. Handle conflicts:

- **Lockfiles** (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Cargo.lock`, `go.sum`): accept theirs and stage:
  ```bash
  git checkout --theirs <lockfile>
  git add <lockfile>
  git rebase --continue
  ```
  Note: lockfile will be slightly stale. Remind user to run `npm install` (or equivalent) after checkout.

- **Code conflicts**: if rebase hits a conflict that isn't a lockfile, abort immediately:
  ```bash
  git rebase --abort
  ```
  Warn the user that the branch is un-rebased. Continue with the rest of the conversion.

Never block the conversion on rebase failure.

### 5. Remove worktree, checkout branch in main workspace

```bash
# Check main workspace is clean before attempting checkout
cd "$MAIN_WORKTREE"
if [ -n "$(git status --porcelain)" ]; then
  # WARN: "Main workspace has uncommitted changes. Checkout may fail."
  # Ask user: proceed or abort?
fi

git worktree remove "$WORKTREE_PATH" --force
git checkout "$BRANCH"
```

### 6. Report

Print a summary:

```
Branch <BRANCH> checked out in <MAIN_WORKTREE>
  Rebase: <succeeded | skipped (already up-to-date) | failed (branch is un-rebased)>
  Cleanup: <ran make dev-stop | no cleanup target found | cleanup failed>
  <If lockfiles were auto-resolved: "Run npm install (or equivalent) to update lockfiles">
```

## Rules

- **Never block on failure.** Rebase failure, cleanup failure, and lockfile conflicts are all warnings. The conversion always completes.
- **Never push, create PRs, delete branches, or merge.** Those are separate user decisions.
- **Cleanup before rebase.** Project cleanup needs worktree context (variables, paths). Rebase happens after.
- **Always use `git add -A` for WIP commits.** New untracked files are common in worktrees. `.gitignore` handles exclusions.
- **Detect the base branch dynamically.** Don't hardcode `main` — check `git symbolic-ref refs/remotes/origin/HEAD`, fall back to `main`, then `master`.
- If on main/master or not in a worktree, warn and stop.
