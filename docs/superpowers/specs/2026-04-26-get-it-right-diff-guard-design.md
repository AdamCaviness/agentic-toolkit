# get-it-right Footprint Guard Design

## Problem

`skills/get-it-right/SKILL.md` re-architects the current branch and auto-implements without committing. Its only safety rails are "tests must pass" and the principle "preserve all existing behavior." For projects with thin test coverage, the skill can silently rewrite far beyond the branch's original footprint, then hand the user a 3 to 6 item testing playbook. An AFK reviewer who only validates the playbook and merges has no signal that the change set ballooned.

## Fix

Add a quantitative checkpoint between Step 4 (Plan the Re-architecture) and Step 5 (Auto-Implement). The skill compares the planned footprint to the branch's existing footprint against the default branch and stops to confirm with the user when the plan strays beyond a documented bound. The guard is a stop-and-report, not a kill-switch. Within bounds, the skill proceeds to auto-implement as before.

## Footprint definitions

- Original footprint: `git diff --name-only "$BASE_BRANCH"...HEAD`. Files the branch already touches against the default branch.
- Planned footprint: every file the Step 4 plan intends to modify, create, or delete.
- Net-new files: files in the planned footprint that are not in the original footprint.
- Net-removed files: files in the original footprint the plan no longer touches at all (rare but possible when consolidation absorbs a file's contents elsewhere).

## Threshold

Stop and ask the user to confirm when any of these is true:

1. Net-new files exceed 50% of the original footprint count.
2. Original footprint has 1 to 3 files and net-new files exceed 2. The percentage rule alone is too sharp on tiny branches; a 1-file branch tripping at 1 net-new file would be noise.
3. Any net-new or net-removed file is not justified by a stated retrospective insight from Step 3.

50% is the published threshold. It tolerates ordinary re-architecture moves (extract one helper, split one module) on a typical branch of 4 to 20 files, while catching the failure mode where the plan triples the footprint. The exact number is debatable and the prose flags it as such; the load-bearing requirement is that there is a documented limit and a stop point.

## Step order

```
1. Identify Scope
1.5. Untrusted Content Boundary
2. Deep-Read Current Implementation
3. Retrospective Analysis
4. Plan the Re-architecture
4.5. Footprint Guard            <-- new checkpoint
5. Auto-Implement
6. Output Testing Playbook
```

Step 4.5 prints the original footprint, the planned footprint, the net-new and net-removed lists with their justifying retrospective insight (or "no insight cited" if absent), the count delta, and the percentage. If any threshold trips, the skill stops and asks the user to confirm or revise the plan. If all thresholds hold, it proceeds to Step 5 without prompting.

The workflow digraph at the top of `SKILL.md` gains a `"Plan re-architecture" -> "Footprint guard" -> "Auto-implement (no commit)"` edge.

## Key Principles update

Add: "Stay within the branch's footprint. Re-architecture that adds files outside the branch's existing diff against the default branch needs the user's confirmation before auto-implementing."

## Test

`tests/test_get_it_right_footprint_guard.py` asserts the SKILL.md prose:

- Mentions a footprint comparison before Step 5 / Auto-Implement.
- Names a stop-and-confirm condition tied to original-branch footprint.
- Carries the bounded-footprint principle in Key Principles.
