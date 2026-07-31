# get-it-right Footprint Guard Design

## Problem

`skills/get-it-right/SKILL.md` re-architects the current branch and auto-implements without committing. Its only safety rails are "tests must pass" and the principle "preserve all existing behavior." For projects with thin test coverage, the skill can silently rewrite far beyond the branch's original footprint, then hand the user a 3 to 6 item testing playbook. An AFK reviewer who only validates the playbook and merges has no signal that the change set ballooned.

## Fix

Add a quantitative checkpoint between Step 4 (Plan the Re-architecture) and Step 5 (Auto-Implement). The skill compares the planned footprint to the branch's existing footprint against the default branch and stops to confirm with the user when the plan strays beyond a documented bound. The guard is a stop-and-report, not a kill-switch. Within bounds, the skill proceeds to auto-implement as before.

## Footprint definitions

- Original footprint: the union of `git diff --name-only "$BASE_BRANCH"...HEAD` (committed work), `git diff --name-only HEAD` (tracked edits), and `git ls-files --others --exclude-standard` (untracked additions). Files the branch already touches, committed or not. The committed range alone is not enough: Step 5 deliberately leaves its output uncommitted, so a second run against the same branch would score the first run's files as net-new and trip the guard on its own work.
- Planned footprint: every file the Step 4 plan intends to modify, create, or delete.
- Net-new files: files in the planned footprint that are not in the original footprint.
- Net-removed files: files in the original footprint the plan no longer touches at all (rare but possible when consolidation absorbs a file's contents elsewhere).

## Threshold

Stop and ask the user to confirm when either is true:

1. The net-new count exceeds the allowance, which is the larger of 2 files or 50% of the original footprint count.
2. Any net-new or net-removed file is not justified by a stated retrospective insight from Step 3.

50% is the published threshold. It tolerates ordinary re-architecture moves (extract one helper, split one module) on a branch of 4 to 20 files, while catching the failure mode where the plan triples the footprint. The exact number is debatable; the load-bearing requirement is that there is a documented limit and a stop point.

The 2 file floor is the allowance's lower bound rather than a separate tiny-branch rule. A percentage alone is too sharp on small branches, where a 1-file branch would trip at 1 net-new file. Folding the floor into a single `max(2, 50%)` allowance keeps the threshold stated once, in one place, so a change to it cannot leave a stale copy behind.

## Empty scope

A branch with no commits against the default branch and a clean working tree has a zero-file footprint. The percentage is undefined against it and there is nothing to re-architect, so Step 1 stops and asks the user which branch or change set to target rather than letting an empty scope reach Step 4.5.

## Step order

```
1. Identify Scope                (stops on an empty scope)
1.5. Untrusted Content Boundary
2. Deep-Read Current Implementation
3. Retrospective Analysis
4. Plan the Re-architecture
4.5. Footprint Guard             <-- checkpoint
5. Auto-Implement
6. Output Testing Playbook
```

Step 4.5 prints the original footprint, the planned footprint, the net-new and net-removed lists with their justifying retrospective insight (or "no insight cited" if absent), the count delta, and the net-new count against the allowance. If either condition trips, the skill stops and asks the user to confirm or revise the plan. If both hold, it proceeds to Step 5 without prompting.

The workflow digraph at the top of `SKILL.md` gains a `"Plan re-architecture" -> "Footprint guard" -> "Auto-implement (no commit)"` edge.

## Key Principles update

Add: "Stay within the branch's footprint. Re-architecture that adds files the branch does not already touch needs the user's confirmation before auto-implementing." The bullet points at Step 4.5 for the allowance and the stop point instead of restating either, so the threshold has one home.

## Test

`tests/test_get_it_right_footprint_guard.py` asserts the SKILL.md prose:

- Mentions a footprint comparison before Step 5 / Auto-Implement.
- Names a stop-and-confirm condition tied to original-branch footprint.
- Builds the original footprint from uncommitted work as well as the committed range.
- Stops in Step 1 when the branch has no work to re-architect.
- States the threshold exactly once, and keeps it out of Key Principles.
- Carries the bounded-footprint principle in Key Principles.
