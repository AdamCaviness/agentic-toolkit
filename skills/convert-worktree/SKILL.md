---
name: convert-worktree
description: Use when finishing work in a git worktree. Rebases onto default branch, cleans up resources, removes the worktree, and checks out the branch in the main workspace.
disable-model-invocation: true
---

# Convert Worktree

Convert a git worktree into a regular local branch. Confirm the destination before preserving changes, rebase onto the latest default branch, and remove the source only after checkout and restoration succeed.

This skill replaces ExitWorktree. Do not call ExitWorktree after this skill runs.

## Steps

### 1. Preflight and confirm

Run these read-only checks before any source mutation. Use the repository root even when invoked from a subdirectory. Stop on any failed check.

```bash
set -eu
WORKTREE_PATH=$(git rev-parse --show-toplevel)
MAIN_WORKTREE=$(git worktree list --porcelain -z | python3 -c 'import os, sys; print(os.fsdecode(sys.stdin.buffer.read().split(b"\0")[0][len(b"worktree "):] ))')
BRANCH=$(git branch --show-current)
ORIGINAL_HEAD=$(git rev-parse HEAD)

if [ -z "$MAIN_WORKTREE" ] || [ "$MAIN_WORKTREE" = "$WORKTREE_PATH" ]; then
  echo "STOP: Not in a linked worktree." >&2
  exit 1
fi
if [ -z "$BRANCH" ]; then
  echo "STOP: Detached HEAD. Checkout a branch first." >&2
  exit 1
fi

BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
if [ -z "$BASE_BRANCH" ]; then
  git rev-parse --verify main >/dev/null 2>&1 && BASE_BRANCH=main || BASE_BRANCH=master
fi
BASE_REF="$BASE_BRANCH"
git rev-parse --verify "$BASE_REF" >/dev/null 2>&1 || BASE_REF="origin/$BASE_BRANCH"
git rev-parse --verify "$BASE_REF" >/dev/null 2>&1 || {
  printf 'default branch "%s" resolves neither locally nor on origin\n' "$BASE_BRANCH" >&2
  exit 1
}
if [ "$BRANCH" = "$BASE_BRANCH" ]; then
  echo "STOP: Cannot convert the default branch." >&2
  exit 1
fi

for CHECKOUT in "$WORKTREE_PATH" "$MAIN_WORKTREE"; do
  for OPERATION in rebase-merge rebase-apply MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD; do
    OPERATION_PATH=$(git -C "$CHECKOUT" rev-parse --path-format=absolute --git-path "$OPERATION")
    if [ -e "$OPERATION_PATH" ]; then
      printf 'STOP: Finish or abort %s in %s first.\n' "$OPERATION" "$CHECKOUT" >&2
      exit 1
    fi
  done
done

git -C "$WORKTREE_PATH" status --short
MAIN_STATUS=$(git -C "$MAIN_WORKTREE" status --porcelain)
if [ -n "$MAIN_STATUS" ]; then
  printf '%s\n' "$MAIN_STATUS"
  echo "STOP: Main workspace has uncommitted changes. Source worktree is unchanged." >&2
  exit 1
fi

printf 'Source: %s\nBranch: %s\nOriginal HEAD: %s\nDestination: %s\nDefault branch: %s\n' \
  "$WORKTREE_PATH" "$BRANCH" "$ORIGINAL_HEAD" "$MAIN_WORKTREE" "$BASE_BRANCH"
IGNORED_SOURCE=$(git -C "$WORKTREE_PATH" ls-files --others --ignored --exclude-standard --directory)
if [ -n "$IGNORED_SOURCE" ]; then
  printf '%s\n' "$IGNORED_SOURCE"
  echo "STOP: Move valuable ignored files or deliberately remove disposable caches, then rerun preflight." >&2
  exit 1
fi
```

If the destination is dirty, explain that conversion has stopped before committing, stashing, cleanup, or rebase. Let the user clean it up or abort, then rerun preflight. Never proceed against a dirty destination.

If ignored source paths exist, stop before preservation and explain each choice: move valuable files to a safe location outside the source, or remove disposable build and dependency caches such as `node_modules` deliberately. Show the concrete paths and proposed commands, never delete them automatically. Rerun preflight after the user's chosen action. Explain that tracked modifications and explicitly staged new files enter a WIP commit, and unstaged untracked files go into a named recovery stash. Confirm the conversion before step 2. If the user declines, stop and report that both checkouts, history, stashes, and project resources are unchanged. No restore command is needed for this early abort.

After confirmation, create a **recovery record** outside both worktrees, using a file-writing tool and a unique file in the system temp directory. Record its absolute path in the conversation. Save `WORKTREE_PATH`, `MAIN_WORKTREE`, `BRANCH`, `BASE_BRANCH`, `ORIGINAL_HEAD`, the destination's original branch or detached commit, a unique `STASH_LABEL` such as `convert-worktree:untracked:<branch>:<run-id>`, `WIP_COMMIT` and `STASH_OID` initially empty, the untracked path inventory, and the current phase. Decode a NUL-delimited `git ls-files --others --exclude-standard -z` inventory into a JSON array so spaces and newlines in filenames are preserved. Update the record immediately after each mutation and before starting the next phase. Keep it on success as well as failure.

**Shell state does not persist between tool calls.** Read the recovery record before each later shell block and explicitly assign its literal values to the variables that block uses, with proper shell quoting. Never infer a stash from the latest entry or an unset variable. An unreadable or incomplete record stops the conversion while the source still exists.

### 2. Preserve uncommitted work

Run from the recorded source root. Recheck the destination is clean before starting. If preflight inventories have changed, repeat preflight and confirmation. Any staging, commit, stash, or record-write failure stops before cleanup, rebase, or removal.

Stage tracked modifications and deletions. Anything already staged, including new files explicitly added by the user, stays staged. Unstaged untracked files stay outside history, `.gitignore` is an exclusion list, not a secret scanner.

```bash
set -eu
cd "$WORKTREE_PATH"
git status --short
git add -u
if [ -n "$(git diff --cached --name-only)" ]; then
  git commit -m "chore(worktree): preserve tracked changes during conversion"
  printf 'WIP_COMMIT=%s\n' "$(git rev-parse HEAD)"
fi
```

Save the printed `WIP_COMMIT` in the record before continuing. Then preserve untracked files:

```bash
set -eu
cd "$WORKTREE_PATH"
if [ -n "$(git ls-files --others --exclude-standard)" ]; then
  git stash push --include-untracked -m "$STASH_LABEL"
  printf 'STASH_OID=%s\n' "$(git rev-parse refs/stash)"
fi
git status --short
```

Save the exact printed `STASH_OID` immediately. If record writing fails after a stash was created, find it by the recorded unique label with `git stash list --format='%H %gs'`, record its object ID, and recover in the source. Stop if the source still has tracked or nonignored untracked changes. Keep the stash as a recovery copy, restoration uses `git stash apply "$STASH_OID"`, never an unqualified pop.

### 3. Project cleanup

Run from the source root so project-specific variables, such as DB names and ports, resolve correctly.

```bash
cd "$WORKTREE_PATH" || exit 1
if [ -f Makefile ] && grep -q '^dev-stop:' Makefile; then
  make dev-stop || echo "Warning: make dev-stop failed, continuing"
fi
```

Cleanup failure is a warning. If cleanup creates or modifies files, stop for recovery instead of committing them or forcing removal. Record cleanup status.

### 4. Rebase onto latest default branch

Resolve the default branch again in this shell, verify a target exists, and fetch it when origin is configured. A failed fetch is a warning, report that the existing ref was used.

```bash
set -eu
cd "$WORKTREE_PATH"
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
if [ -z "$BASE_BRANCH" ]; then
  git rev-parse --verify main >/dev/null 2>&1 && BASE_BRANCH=main || BASE_BRANCH=master
fi
if git remote get-url origin >/dev/null 2>&1; then
  git fetch origin "$BASE_BRANCH" || echo "Warning: fetch failed, using existing default branch ref"
fi
if git rev-parse --verify "origin/$BASE_BRANCH" >/dev/null 2>&1; then
  REBASE_TARGET="origin/$BASE_BRANCH"
else
  REBASE_TARGET="$BASE_BRANCH"
fi
git rev-parse --verify "$REBASE_TARGET" >/dev/null
if git merge-base --is-ancestor "$REBASE_TARGET" HEAD; then
  echo "Rebase skipped, already up-to-date"
else
  git rebase "$REBASE_TARGET"
fi
```

Handle rebase conflicts while the source worktree still exists:

- **Lockfiles** (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Cargo.lock`, `go.sum`): accept theirs and stage, then continue the rebase. Remind the user to run the package manager after checkout to update lockfiles.
- **Code conflicts or unsuccessful continuation**: run `git rebase --abort`. Continue conversion with a warning only if abort succeeds and there is no active operation or dirty source. A failed abort stops for recovery.

Record the rebase result and branch tip, including the rebased WIP commit if its ID changed. Cleanup and successfully aborted rebase failures are warnings, preservation and restoration failures stop conversion.

### 5. Checkout, restore, then remove the source

Load literal values from the record, including `STASH_OID`, which is explicitly empty when no stash was created. Recheck both checkouts and active operations before the handoff. If the destination changed, stop and recover in the source. Do not ask about proceeding after mutations.

Detach the source to release the branch while keeping its directory and tracked contents intact. Checkout and restore in the destination before removing anything. Keep the exact stash, even after a successful apply, as a recovery copy.

```bash
set -eu
SOURCE_STATUS=$(git -C "$WORKTREE_PATH" status --porcelain)
MAIN_STATUS=$(git -C "$MAIN_WORKTREE" status --porcelain)
if [ -n "$SOURCE_STATUS" ] || [ -n "$MAIN_STATUS" ]; then
  echo "STOP: A checkout changed. Source retained, recover before retrying." >&2
  exit 1
fi
IGNORED_SOURCE=$(git -C "$WORKTREE_PATH" ls-files --others --ignored --exclude-standard --directory)
if [ -n "$IGNORED_SOURCE" ]; then
  printf '%s\n' "$IGNORED_SOURCE"
  echo "STOP: Preserve or remove ignored source paths deliberately before handoff." >&2
  exit 1
fi
# An absent value is not evidence that no recovery stash was created.
: "${STASH_OID?Load STASH_OID from the recovery record, empty only when no stash was created}"
if [ "$(git -C "$WORKTREE_PATH" branch --show-current)" != "$BRANCH" ]; then
  echo "STOP: Source branch changed since the recovery record was created." >&2
  exit 1
fi
for CHECKOUT in "$WORKTREE_PATH" "$MAIN_WORKTREE"; do
  for OPERATION in rebase-merge rebase-apply MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD; do
    OPERATION_PATH=$(git -C "$CHECKOUT" rev-parse --path-format=absolute --git-path "$OPERATION")
    if [ -e "$OPERATION_PATH" ]; then
      echo "STOP: An active Git operation must be finished or aborted before handoff." >&2
      exit 1
    fi
  done
done
git -C "$WORKTREE_PATH" checkout --detach HEAD
if ! git -C "$MAIN_WORKTREE" checkout --no-overwrite-ignore "$BRANCH"; then
  git -C "$WORKTREE_PATH" checkout "$BRANCH" || {
    echo "STOP: Could not reattach source, directory and recovery stash retained." >&2
    exit 1
  }
  if [ -n "$STASH_OID" ]; then
    git -C "$WORKTREE_PATH" stash apply "$STASH_OID" || {
      echo "STOP: Source restore failed, keep the exact stash and inspect both copies." >&2
      exit 1
    }
  fi
  echo "STOP: Destination checkout failed. Source retained and untracked recovery attempted." >&2
  exit 1
fi
if [ -n "$STASH_OID" ]; then
  if ! git -C "$MAIN_WORKTREE" stash apply "$STASH_OID"; then
    echo "STOP: Destination restore failed. Source remains detached, exact stash retained." >&2
    exit 1
  fi
fi
git -C "$MAIN_WORKTREE" worktree remove "$WORKTREE_PATH"
```

If removal fails, keep the source. Ordinary status omits ignored paths, and even non-forced worktree removal can delete them. The explicit ignored-path check prevents this. Report their paths and let the user move or remove them deliberately. Never force deletion. If checkout or restoration fails, report each checkout's actual branch or detached commit and list restored and pending paths, conversion is incomplete. Do not retry stash application blindly after a partial restore.

### 6. Report and recovery

Always read the record for the report, even after a shell failure. List every preserved untracked path and its restored or pending location, the record path, exact stash ID and label, original HEAD, WIP commit if any, and rebase and cleanup results. Report success only when the branch is checked out in the destination, all preserved paths are restored, and source removal succeeded. On success, label the paths **Untracked (restored from stash, review before committing)** and mention that the named stash remains as a recovery copy. Never delete the record or stash during an incomplete conversion.

On any stop after preservation, show concrete commands populated from the record:

- **Before destination checkout**: abort any active rebase successfully, then restore untracked files in the source with `git -C "$WORKTREE_PATH" stash apply "$STASH_OID"` when a stash exists and those paths have not already been restored. If this fails or would collide, leave the stash and source intact and identify the conflicting paths.
- **After destination checkout**: keep the detached source and exact stash. Inspect any partially restored destination paths before retrying. The untracked snapshot is inspectable with `git ls-tree -r --name-only "$STASH_OID^3"`. Restore to a clean chosen checkout with `git -C <chosen-checkout> stash apply <recorded-stash-oid>`. Never overwrite a conflicting file or delete either copy to make a retry succeed.
- **Undo the WIP commit if requested**: explain that stopping retains this commit. Preserve the current tip on a uniquely named recovery branch before `git reset --mixed "$ORIGINAL_HEAD"` in the checkout holding `BRANCH`. This also undoes any completed rebase while leaving tracked changes on disk. Use the recorded original HEAD, never `HEAD~1`, and do not reset when no WIP commit was made or when unrelated commits have been added. Show the original and current commit IDs, run only at the user's request. The exact original staged/unstaged split is not reconstructed by a mixed reset.

An early declined conversion needs no recovery. A later stop retains recoverable work and explains the mutations that did occur, including any project resources stopped by cleanup.

## Rules

- **Confirm before mutation.** A dirty destination or declined conversion stops before committing, stashing, cleanup, or rebase.
- **Preserve before removal.** Checkout, restoration, and recovery-record failures stop. Remove the source only after successful handoff, without force.
- **Never push, create PRs, delete branches, or merge.** Those are separate user decisions.
- **Cleanup before rebase.** Cleanup needs source worktree context. Cleanup errors and safely aborted rebase conflicts are warnings.
- **Never auto-commit untracked files.** Tracked modifications and explicitly staged content enter the WIP commit, unstaged untracked files remain outside history in a named recovery stash. Never use blanket `git add -A`.
- **Detect the default branch dynamically.** Resolve and verify it before use, stop on the default branch, detached HEAD, or outside a linked worktree.
- **Recovery state survives shell calls.** Use the external record's literal values and exact stash ID, keep pending paths visible in every final report.
