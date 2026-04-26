# next-ticket Auto-Review Handoff Design

## Problem

`skills/next-ticket/SKILL.md` ends Step 9 with a commit and Step 10 with `Done. Ready for review.`. The user, who started the run AFK, has to come back, notice the run finished, and manually invoke `/code-review` to get a verdict on the work. The two skills sit side by side with no integration; the gap between them is filled by a human.

The fix is to chain `code-review` into `next-ticket` as the closing step, so the AFK return shows the implementation summary and the review findings together. The integration must be portable across all three harnesses the repo targets (Claude Code, Codex, Gemini) without harness-specific config.

## Architecture

Three file changes, one new file. No hooks, no `settings.toml`, no `.gemini/hooks/`, no harness-specific config.

### New: `skills/code-review/reviewer-prompt.md`

Standalone file containing the reviewer subagent's prompt template, currently a fenced block at the bottom of `skills/code-review/SKILL.md`. Placeholders (`{WHAT_WAS_IMPLEMENTED}`, `{PLAN_OR_REQUIREMENTS}`, `{BASE_SHA}`, `{HEAD_SHA}`, `{HAS_UNCOMMITTED}`, `{CHANGED_PATH_INVENTORY}`, `{HIGH_RISK_PATHS}`, `{DESCRIPTION}`) preserved character-for-character.

This becomes the single source of truth for the reviewer contract. Both `code-review` and `next-ticket` reference it; the template cannot drift because there is only one copy.

### Edit: `skills/code-review/SKILL.md`

The fenced reviewer prompt at the bottom is replaced with a one-paragraph instruction:

> Load `skills/code-review/reviewer-prompt.md`, substitute the placeholders below, and pass the resulting text as the prompt to the unspecialized reviewer subagent.

The placeholder list, "How to Request" steps, "When to Request Review" rules, dispatch guidance, and example output stay intact. The skill remains the canonical owner of the reviewer dispatch logic.

### Edit: `skills/next-ticket/SKILL.md`

A new Step 9.5 is inserted between Step 9 (commit) and Step 10 (announce). Step 10's print is updated to include a Review block.

Step 9.5 body:

1. Resolve `BASE_BRANCH` per AGENTS.md branch lifecycle contract.
2. Build placeholder values:
   - `BASE_SHA = git merge-base HEAD "origin/$BASE_BRANCH"` (fallback `git merge-base HEAD "$BASE_BRANCH"`)
   - `HEAD_SHA = git rev-parse HEAD`
   - `HAS_UNCOMMITTED = no` (Step 9 just committed; working tree is clean)
   - `CHANGED_PATH_INVENTORY` and `HIGH_RISK_PATHS` per the same shell snippet `code-review/SKILL.md` already documents
   - `DESCRIPTION`: a one to two sentence implementor summary of the change
   - `PLAN_OR_REQUIREMENTS`: ticket title + ticket body, verbatim from the source system
3. Load `skills/code-review/reviewer-prompt.md`, substitute, dispatch the unspecialized reviewer subagent with the resulting text as its prompt. The dispatch wording uses "Task tool / equivalent" per the AGENTS.md capability glossary; do not name a specialized reviewer agent from another plugin.
4. Capture the reviewer's structured output. Parse out the severity counts (Critical, Important, Minor), the Assessment verdict line (Yes / No / With fixes), and the top issues in severity order, capped at five.

Step 10's print becomes:

```
Done. Ready for review.

Branch: <branch-name>
Ticket: <ticket-id> - <ticket title>
Files:  <list changed files>

Review: Critical <N> | Important <N> | Minor <N> | Verdict: <Yes/No/With fixes>
Top issues:
  - <file>:<line> - <what's wrong>
  - <file>:<line> - <what's wrong>
  ...

To test in the UI: <one sentence>
```

If the reviewer found zero issues, the two Review lines collapse to `Review: clean | Verdict: Yes` and `Top issues:` is omitted.

## Verification handling

No coordination between implementor and reviewer. The reviewer's existing rule, "Run project verification if available and fast, else skip with reason," self-tunes:

- Fast suites: reviewer re-runs. Small duplicate cost; acceptable.
- Slow suites: reviewer auto-skips with honest "skipped: would exceed fast budget" reason.

A `verification_already_run` placeholder was considered and rejected. It would erode the reviewer's independent-evidence role (which exists on purpose, especially given the untrusted-content boundary applied to ticket bodies upstream) and would widen the reviewer's formal contract for one caller's optimization. Skill outputs should be the skill's own work product; skill inputs should match the skill's formal template.

## Failure mode

If the reviewer subagent dispatch errors, the capability is unavailable, or any other failure prevents review, Step 9.5 replaces the Review block with one line: `Review: skipped (<reason>)`. No retries. Step 10 still prints. The user can run `/code-review` manually if they care. The AFK posture is preserved; the original "Done" summary is never lost to a review failure.

## Cross-platform contract

- Single canonical `skills/<name>/SKILL.md` per skill; no harness-specific subtree (matches AGENTS.md "skills/ is distribution, not local config" rule).
- Sibling-file load (`skills/code-review/reviewer-prompt.md`) is a plain relative file read; identical semantics in Claude Code, Codex, and Gemini.
- Subagent dispatch uses "Task tool / equivalent" wording, authorized by the AGENTS.md capability glossary.
- Frontmatter unchanged. No `disable-model-invocation` flips. No new harness-specific keys.
- No hooks, no platform-specific settings files.

## Out of scope

- Cross-platform packaging changes (already conformed; AGENTS.md codifies the rule).
- Hook-driven auto-review (`AfterTool` / `PostToolUse`): platform-specific config, fires on every tool call rather than at workflow boundaries, fragments three harnesses. Rejected.
- Orchestrator skill that chains `next-ticket` and `code-review` as sub-skills: adds a third skill for what one inline directive does. Rejected.
- Skip flag on `next-ticket` to bypass the auto-review: YAGNI; review is always-on per stated intent and is fast or auto-skips on slow suites.
- Auto-fixing review findings inside `next-ticket`: matches the chosen "review after commit" placement; the user reviews before push, no autonomous follow-up edits.
- `pr` and `ship` invocations of `code-review`: separate scope.

## Files touched

- `skills/code-review/reviewer-prompt.md` (new)
- `skills/code-review/SKILL.md` (replace fenced template with one-paragraph reference)
- `skills/next-ticket/SKILL.md` (insert Step 9.5, update Step 10 print template)
- `tests/test_code_review_inventory.py` (retarget assertions from `code-review/SKILL.md` to `code-review/reviewer-prompt.md`; the placeholder strings now live in the new file)
- `tests/test_next_ticket_auto_review.py` (new; see Test plan)
- `docs/superpowers/specs/2026-04-26-next-ticket-auto-review-handoff-design.md` (this spec)

## Test plan

Update `tests/test_code_review_inventory.py` so the placeholder and inventory assertions read from `skills/code-review/reviewer-prompt.md` instead of `skills/code-review/SKILL.md`. The test still validates the same contract; only the source path moves.

Add `tests/test_next_ticket_auto_review.py` asserting against `skills/next-ticket/SKILL.md`:

- A Step 9.5 (or equivalent named step between commit and the final summary) exists and references `skills/code-review/reviewer-prompt.md`.
- The step builds `BASE_SHA`, `HEAD_SHA`, `CHANGED_PATH_INVENTORY`, and `HIGH_RISK_PATHS` using the same shell snippet `code-review/SKILL.md` documents (shared inventory contract, no drift).
- The Step 10 summary template includes a `Review:` line with severity counts and a verdict, plus a `Top issues:` block.
- A failure-mode line documents `Review: skipped (<reason>)` for dispatch failures, with no retry and no blocking of Step 10.

`python3 -m unittest discover tests` must pass.

Manual verification, run once after implementation:

- End-to-end: run `/next-ticket` on a repo with open tickets; confirm the Review block appears in the Step 10 output and the verdict matches a manual `/code-review` baseline run on the same commit.
- Regression: run `/code-review` standalone on a different branch; output format must be unchanged from pre-refactor.
- Failure path: simulate a reviewer dispatch failure (revoke the subagent capability or break the file path); confirm the graceful `Review: skipped` line and that Step 10 still prints.
