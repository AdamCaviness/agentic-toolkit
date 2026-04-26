# Triage Quality Pass Design

A targeted set of fixes to the triage skill family that close gaps surfaced during recent operator runs. All shared mechanics are edited in `triage_shared/template.md` or `triage_shared/skills.py`, then `python3 -m triage_shared.generate` regenerates the public `skills/triage-{architecture,bugs,product}/SKILL.md` files. The shared-source validator at `tests/test_triage_shared_source.py` enforces that flow.

## Fix 1: Detection cache is written after user confirmation

The Step 0 detection sequence currently caches the auto-detected ticket system before the user has had a chance to correct it. The companion skill `next-ticket` already has the right shape: the cache write follows confirmation, and a correction overwrites the cache rather than racing it.

The fix reorders Step 0 so the auto-detect or ask result is presented to the user first, then the cache write happens after the user confirms or corrects. A correction goes straight into the cache as the canonical value. The wording mirrors `next-ticket`: "If they confirm, cache it. If they correct, cache the correction."

## Fix 2: Cross-cluster post-processor guards against closed tickets

In refine mode, a cluster agent may close a ticket as resolved. A different cluster's cross-cluster note can target that same ticket. The post-processor runs after all clusters finish, so when it edits the target description it can be writing to a ticket that another cluster just closed.

The fix adds a state check to the post-processor's per-ticket loop: before editing, fetch the ticket's current state. If closed, skip the note and log the skip to stderr so the operator can see what was dropped. The rule is scoped to refine mode in the post-processor prompt, since create-mode cluster agents cannot close tickets and the race is unreachable there.

## Fix 3: Surface valid findings dropped by the ticket cap

Each cluster agent has a hard cap of 3 new tickets per run. Findings that clear every gate (dedup, certainty bar, pre-filing gate) but fall outside the cap are silently discarded today, so the operator never sees what was deferred.

The fix adds a structured over-cap output. After hitting the cap, the cluster agent writes a JSON file at `{CACHE_DIR}/over-cap-{CLUSTER_SLUG}.json`. Each entry carries the candidate title, file:line evidence, severity, and a one-line "why it would have been filed". The orchestrator collects these in the run summary so the operator sees the full deferred list. For triage-bugs, this stays distinct from the rejection ledger: the ledger holds candidates that failed the certainty bar; the over-cap file holds candidates that cleared every gate but lost a slot.

## Fix 4: Sub-agents read the project's own instruction files directly

The orchestrator builds a project map that captures structure and key files, but distillation can drop project-specific carve-outs (for example, the deployment-context paragraph in this repo's `AGENTS.md` that scopes threat models). When sub-agents only read the map, those carve-outs do not reach them.

The fix has the project map remain as orientation and adds a parallel instruction: each sub-agent also reads `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md` from the project root verbatim, whichever exist. The map tells them what to read in the codebase; the convention files reach them with no lossy distillation. A new check in `tests/test_triage_shared_source.py` (or a sibling test) asserts every sub-agent prompt instructs reading those files.

## Fix 5: Document the not-planned close-state for rejection learning

The rejection-learning loop depends on the operator closing rejected tickets with the platform's not-planned (GitHub `stateReason: not_planned`) or wontfix-equivalent (Jira resolution) state, plus a one-line reason in the closing comment. The default close action on most platforms uses `completed`, which the loop cannot distinguish from a normal fix and silently breaks learning.

The fix adds a short user-facing tip to each generated triage SKILL.md, near the run-complete summary, telling the operator which close-state to use and why. The README's Tickets section gains the same note so the operator does not have to read a SKILL.md to learn it.

## Fix 6: Closed-tickets fetch falls back to the unlabelled recent window

The closed-tickets fetch filters by the per-skill labels list (`architecture, product, bug`). Projects that label tickets differently or do not label at all return zero closed tickets, and rejection learning has nothing to work with.

The fix adds a fallback: if the labelled fetch returns zero results, fetch the most recent N closed tickets unfiltered (N = 50). The detector signals this case to the orchestrator's status output so the operator sees "Fallback: project has no labelled closed tickets, using recent 50 closed tickets unfiltered." This is a graceful degradation, not a silent change of behavior.
