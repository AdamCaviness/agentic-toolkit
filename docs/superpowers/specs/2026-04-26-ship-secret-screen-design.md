# ship Secret-Path Screen Design

## Gap

`skills/ship/SKILL.md` auto-commits, pushes, opens a PR, merges, syncs the default branch, and deletes the feature branch in one shot. Its only safety prose for accidental secret publication is `"If any files or changes look suspect, prompt the user."` That is judgement-driven, not mechanical. `skills/pr/SKILL.md`, whose blast radius is strictly smaller (push only, no merge, no branch delete), already runs an explicit pattern screen against the publication inventory before push. Ship must do at least the same.

## Chosen pattern

Mirror pr character-for-character so the two skills can be deduplicated later. The patterns are:

```
.env, .env.*, *.pem, *.key, id_rsa*, *.p12, *.pfx, *credential*, *secret*, *.sqlite*
```

The screen runs against the publication inventory (`git diff --name-status "$BASE_BRANCH"...HEAD`), not the working-tree status. Working-tree-only paths cannot leak to the remote. Committed paths can.

## Where the gate inserts

Ship's current numbered flow places **Push** at step 3, immediately after **Commit** at step 2. The screen must run after the commit (so the publication inventory is final) and before the push (so secrets never reach the remote at all).

The new ordering inserts a pre-push gate as step 3. The previous push step shifts to step 4, and every subsequent step shifts by one. The gate body reuses pr's exact wording for the high-risk pattern list and the resolution paths (remove, gitignore, or explicit user confirmation). It also re-resolves `BASE_BRANCH` at the top of its bash block per AGENTS.md, since shell state does not persist across Bash tool invocations.

## Test plan

Add `tests/test_ship_publish_state_gate.py` modeled on `tests/test_pr_publish_state_gate.py`. The test asserts the ship SKILL.md:

- inventories committed paths with `git diff --name-status "$BASE_BRANCH"...HEAD` before push
- mentions `high-risk` in the gate prose
- contains the substrings `.env`, `.pem`, and `credential` (the same anchors the pr test uses)

`python3 -m unittest discover tests` must pass with the existing pr gate test plus the new ship gate test.
