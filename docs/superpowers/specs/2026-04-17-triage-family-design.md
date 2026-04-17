# Triage Family: Rename and New Skill Design

## Overview

Rename the two existing planner skills to form a cohesive `triage-*` family and add a third skill for proven bug detection.

| Current | New | Purpose |
|---|---|---|
| `architect-planner` | `triage-architecture` | Audit for architectural concerns, DRY, security posture, code quality |
| `product-planner` | `triage-product` | Audit for UX gaps, broken workflows, accessibility, visual consistency |
| (new) | `triage-bugs` | Investigate and prove real defects with adversarial rigor |

All three share the same orchestrator shell: detect ticket system, cache tickets, build project map, assign tickets to clusters, deploy 4 parallel sub-agents, post-process cross-cluster notes, cleanup and update state. They differ in cluster definitions, sub-agent persona, investigation methodology, filing format, and ticket labels.

## Ticket Ownership Model

Tickets are not owned by any skill. Labels (`architecture`, `product`, `bug`) are descriptive tags indicating what the skill was looking for when it created the ticket, not possessive markers.

**Create mode:** Each skill creates tickets with its own label because that reflects the lens through which the finding was discovered.

**Refine mode:** All open tickets enter the assignment pool regardless of label. The orchestrator assigns tickets to clusters by content and topic, not by label. A sub-agent refines whatever tickets land in its edit file. If a sub-agent adds context from its domain to a ticket with a different label, it adds its own label alongside the existing one. Labels accumulate, never replace.

**Cross-skill example:** `triage-architecture create` files ticket #42 with label `architecture` about a missing transaction boundary. Later, `triage-bugs refine` assigns #42 to the Data & State cluster. The sub-agent traces the code, proves the missing transaction causes data corruption under concurrent writes, adds the proof sections (Reproduction, Evidence, Root Cause, Acceptance Criteria) to the description, and adds the `bug` label alongside `architecture`. Ticket #42 now carries both labels.

## Rename: triage-architecture (was architect-planner)

### What Changes

- Directory: `skills/architect-planner/` → `skills/triage-architecture/`
- Frontmatter `name:`: `triage-architecture`
- Cache directory: `<temp>/triage-architecture-<PROJECT_ID>`
- State file key: `triage-architecture`
- Coverage status header: `Coverage Status (triage-architecture):`
- Post-processor persona: "post-processor for triage-architecture"
- Usage examples: `/triage-architecture`, `/triage-architecture refine`, `/triage-architecture refine 5h`

### Label Language Update

**Create mode sub-agent template:**
- "Create tickets with the `architecture` label" (unchanged behavior)
- Remove: "Tickets labeled `architecture` are yours; tickets labeled `product` are cross-reference"
- Replace with: "You create `architecture` tickets. Tickets in your edit file may carry any label. Work with them based on their content, not their label. If you add architectural context to a ticket with a different label, add the `architecture` label alongside the existing ones."

**Refine mode sub-agent template:**
- Remove: "yours vs cross-reference" language
- Replace with: "Your edit file contains tickets assigned to your cluster by topic. They may carry any label. Refine based on content. If you add architectural analysis to a non-architecture ticket, add the `architecture` label alongside existing labels."

### Closed Tickets Filter Update

Currently fetches closed tickets labeled `architecture` or `product`. Update to fetch all three labels (`architecture`, `product`, `bug`) so dedup catches tickets created by any triage skill.

### What Does Not Change

- Cluster definitions (Safety, Correctness, Maintainability, Completeness)
- Sub-agent persona ("senior software architect")
- Focus tables
- Filing format (Problem, Root Cause, Evidence, Risk, Suggested Fix)
- Mode-specific sections (create/refine logic)
- Severity labels and guide
- Stay In Your Lane boundaries
- Cross-cluster notes mechanism
- Post-processor logic
- 3-ticket hard cap in create mode
- Ticket system detection (shared `next-ticket-config.json`, unchanged)

### State File Migration

The state file at `<temp>/planner-state/<PROJECT_ID>.json` currently stores keys `architect-planner` and `product-planner`. After rename:
- Read: check for both old key (`architect-planner`) and new key (`triage-architecture`). Use whichever is present; prefer new if both exist.
- Write: always write the new key (`triage-architecture`). Do not delete the old key (harmless, avoids data loss if user runs old version).

## Rename: triage-product (was product-planner)

### What Changes

- Directory: `skills/product-planner/` → `skills/triage-product/`
- Frontmatter `name:`: `triage-product`
- Cache directory: `<temp>/triage-product-<PROJECT_ID>`
- State file key: `triage-product`
- Coverage status header: `Coverage Status (triage-product):`
- Post-processor persona: "post-processor for triage-product"
- Usage examples: `/triage-product`, `/triage-product refine`, `/triage-product refine 5h`

### Label Language Update

Same pattern as triage-architecture, with `product` substituted for `architecture`.

### Closed Tickets Filter Update

Same as triage-architecture: fetch all three labels (`architecture`, `product`, `bug`).

### What Does Not Change

Same scope as triage-architecture: cluster definitions, persona, focus tables, filing format, mode logic, severity, lane boundaries, cross-cluster notes, post-processor, 3-ticket cap, ticket system detection.

### State File Migration

Same pattern: read both old (`product-planner`) and new (`triage-product`), prefer new, always write new.

## New Skill: triage-bugs

### Frontmatter

```yaml
name: triage-bugs
description: Investigates a codebase for proven defects using adversarial 4-pass analysis (frame, trace, falsify, prove). Caches tickets to disk, then spawns 4 parallel sub-agents (one per bug category) to find, prove, and document bugs with enough rigor that a skeptical maintainer could fix each from the report alone.
argument-hint: "[create | refine [<duration>]]"
```

### Orchestrator Shell

Identical structure to siblings with these substitutions:

- Cache directory: `<temp>/triage-bugs-<PROJECT_ID>`
- State file key: `triage-bugs`
- Coverage status header: `Coverage Status (triage-bugs):`
- Cluster slugs: `data-state`, `security-auth`, `correctness`, `silent-failures`

### Project Map Additions

Beyond the standard map content shared with siblings, the triage-bugs project map adds:

- **Error handling patterns**: how errors propagate, global handlers, catch blocks, error middleware
- **Async boundaries**: promises, callbacks, event handlers, queues, workers, pub/sub
- **Database access patterns**: ORM vs raw queries, transaction usage, connection pooling, migration state
- **Auth middleware chain**: which routes are protected, how tokens are validated, session management
- **External API integrations**: third-party services, webhooks, outbound HTTP calls, retry policies

These guide investigators to the code paths where bugs hide.

### Closed Tickets Filter

Fetch closed tickets with any of the three labels (`bug`, `architecture`, `product`) to avoid re-filing defects already resolved by any triage skill.

### Ticket Assignment

**Create mode:** All open tickets cached for dedup awareness. Existing tickets assigned to clusters by content for cross-reference context. Sub-agents create new `bug` tickets.

**Refine mode:** All open tickets go into the assignment pool regardless of label. Assignment by content/topic match to cluster, not by label. Sub-agents refine whatever tickets are in their edit file. When adding bug proof to a non-bug ticket, add the `bug` label alongside existing labels.

### Cluster Definitions

**Data & State** — Data integrity, data loss, state corruption, stuck workflows, unrecoverable states.

| Focus Area | What to Investigate |
|---|---|
| **Data loss paths** | Writes that can silently fail, truncation without warning, missing persistence after user confirmation, operations that destroy data without backup/undo |
| **Data integrity** | Missing foreign keys causing orphans, transactions that partially commit, concurrent writes without locks that corrupt state, missing cascading deletes/updates |
| **State corruption** | State machines that can reach impossible states, UI state that diverges from server state, caches that serve stale data after writes, workflows that get stuck with no recovery path |
| **Stuck workflows** | Operations that hang without timeout, retry loops without backoff or limit, deadlocks, user flows that reach dead ends with no way back |

**Security & Auth** — Authorization bypass, authentication defects, secrets exposure, injection vectors.

| Focus Area | What to Investigate |
|---|---|
| **Authentication** | Login bypass paths, session fixation, token expiration not enforced, password reset flows that leak information |
| **Authorization** | Routes/endpoints missing auth middleware, privilege escalation (user accessing admin resources), IDOR (accessing another user's data by changing an ID), missing ownership checks on mutations |
| **Secrets** | Credentials in source, tokens logged or in URLs, API keys in client bundles, secrets in error messages |
| **Injection** | SQL injection via string concatenation, XSS via unsanitized user content, command injection through user input, path traversal |

**Correctness** — User-visible wrong results, crashes, runtime errors on supported paths.

| Focus Area | What to Investigate |
|---|---|
| **Wrong results** | Calculations that produce incorrect output under specific inputs, filters/queries that return wrong sets, sorting that violates stated order, off-by-one errors in pagination or ranges |
| **Crashes & runtime errors** | Null/undefined dereferences on supported code paths, unhandled exceptions in non-exceptional flows, type mismatches that survive compilation but fail at runtime |
| **Logic errors** | Inverted conditions, unreachable code that should be reachable, boolean expressions that always evaluate the same way, switch/match with missing cases that receive real input |
| **Regression-prone paths** | Behavior that depends on implicit ordering, code that works by coincidence (e.g., relying on map iteration order), assumptions about input shape that aren't validated |

**Silent Failures** — Swallowed errors, missing retries where correctness requires them, lost writes, severe performance defects.

| Focus Area | What to Investigate |
|---|---|
| **Swallowed errors** | Empty catch blocks, errors caught and not re-thrown or logged, promises without rejection handlers, error callbacks that do nothing |
| **Lost writes** | Fire-and-forget mutations with no confirmation, optimistic updates with no rollback on failure, queued writes that can drop silently, race conditions between read-modify-write sequences |
| **Missing retry/recovery** | Network calls that fail once and give up where correctness requires delivery, idempotency violations on retry, recovery paths that leave partial state |
| **Performance as defect** | N+1 queries that degrade to unusable at realistic scale, unbounded memory growth, missing pagination on endpoints that return unbounded results, operations that block the event loop |

### Sub-Agent Persona

"You are a senior bug investigator. Your default posture is adversarial toward your own findings. Assume every suspected bug is innocent until you've done the work to convict it."

### Recent Activity Check

Same as siblings: before assessing any file, check `git log --since="3 days ago" --oneline -- <file>`. Note recent commits in the investigation or skip if the issue is being actively addressed.

### The Certainty Bar

Hard gate before filing any ticket. Each candidate must clear at least one of:

1. **A deterministic reproduction** — a sequence of inputs or steps that triggers the defect every time.
2. **A code-path proof** — an end-to-end trace showing the defect must occur under clearly stated conditions, with no plausible guard, validator, or handler that would prevent it.
3. **A failing test** — one the agent wrote or ran that isolates the defect.

"It looks wrong," "this could race," "this might fail under load," and "this seems off" do not clear the bar. If the agent cannot produce one of the three, the candidate goes into the rejection ledger, not into a ticket.

### 4-Pass Investigation Method

For each candidate defect, work in four passes. Do not skip ahead.

**Pass 1 — Frame the claim.** Write down, in one sentence, the specific wrong behavior, the conditions under which it occurs, and the observable symptom. If this cannot be stated crisply, keep reading code.

**Pass 2 — Trace the code.** Read the relevant paths end-to-end. Follow inputs through validation, state transitions, async boundaries, persistence, authorization checks, caching layers, error handlers, and serialization/deserialization. Note every place the value could be mutated, guarded, normalized, or rescued.

**Pass 3 — Falsify.** Actively hunt for reasons the suspicion is wrong. Is there a validator upstream that makes the bad input unreachable? A try/catch that handles it? A default that masks it? A test that already pins the real behavior? If a rescue mechanism exists, the bug either does not exist or lives somewhere else. Say so and move on. This pass is the one most investigators skip; skipping it is how false positives get filed.

**Pass 4 — Prove.** Reproduce it, write a failing test, or produce a causal trace tight enough that a reviewer cannot plausibly object. If this pass fails, the candidate goes into the rejection ledger.

### Filing Format (Create Mode)

```
## Summary
What the bug is and why it matters.

## Impact
Who or what is affected and how badly.

## Conditions
The precise conditions under which the bug fires.

## Reproduction
Numbered steps. If not reproduced at runtime:
"Not reproduced at runtime; confirmed by code-path analysis."
with the trace explained.

## Expected behavior
What should happen.

## Actual behavior
What actually happens.

## Evidence
Files and functions involved, code excerpts with line references,
failing test name if any, stack trace if any.

## Root cause
The underlying defect, explained rigorously but briefly.

## Scope
Adjacent features, routes, or state likely also affected.

## Acceptance criteria
Concrete, checkable statements that define "fixed."
```

Label: `bug` + severity label (`severity:high`, `severity:medium`, `severity:low`).

Severity guide:
- **severity:high**: Data loss, security breach, silent corruption, crashes on supported paths
- **severity:medium**: Wrong results under edge cases, degraded reliability, stuck states with workaround
- **severity:low**: Silent failure with minimal impact, performance defect not yet at breaking point

Hard cap: maximum 3 new tickets per cluster (same as siblings).

### Dedup Check (Create Mode)

Same as siblings:
1. Read ticket titles and descriptions in issues-open.json. Is this defect already covered?
2. Check issues-closed.json titles. Was this already filed and resolved?
3. If already covered and the finding adds evidence: if the ticket is in the edit file, edit the description to add the proof. If outside the edit file, write to cross-cluster notes.
4. If not covered: file a new ticket.

### Pre-Filing Gate (Create Mode)

Before filing, ask: "Is this actually a bug, or am I pattern-matching on something that looks wrong but behaves correctly by design?"

Checks:
- Is the behavior documented as intentional (in docstrings, comments, or design docs)?
- Is there a test that asserts this exact behavior?
- Is there a guard, validator, or handler upstream that prevents the condition from being reached?
- If the behavior is wrong, is the impact real or purely theoretical?

One excellent report beats five weak ones. If on the fence, add to the rejection ledger instead.

### Refine Mode Behavior

Same structure as siblings (improve descriptions, close resolved tickets, correct analysis, add evidence) with one addition:

**Promotion:** When a non-bug ticket is proven to have an actual defect (the agent meets the certainty bar), the agent edits the description to add the proof sections (Reproduction, Evidence, Root Cause, Acceptance Criteria) and adds the `bug` label alongside existing labels. This enriches the ticket without disrupting its existing context.

### Rejection Ledger

Each sub-agent writes `ledger-<cluster-slug>.json` to the cache directory:

```json
{
  "confirmed": [
    { "id": 201, "title": "Race in session refresh allows double-spend", "severity": "high" }
  ],
  "rejected": [
    {
      "candidate": "Possible null deref in parseConfig",
      "reason": "Guarded by schema validation at api/middleware.ts:44"
    }
  ]
}
```

Both arrays may be empty. The file must always be written (even if both arrays are empty) so the orchestrator can distinguish "no findings" from "agent failed to write ledger."

### Unified Post-Run Summary

After collecting cross-cluster notes and before cleanup, the orchestrator:

1. Reads all 4 `ledger-*.json` files from the cache directory.
2. Prints a unified summary to the user:

```
Triage Complete (triage-bugs):
Mode: create | refine
Last run: <previous timestamp or "never">

Confirmed (N):
  #201 "Race in session refresh allows double-spend" — severity:high [Data & State]
  #202 "Missing CSRF on /api/transfer" — severity:high [Security & Auth]
  ...

Investigated & Rejected (M):
  "Possible null deref in parseConfig" — guarded by schema validation at api/middleware.ts:44 [Correctness]
  "Stale cache after write" — intentional per TTL design in cache.ts [Data & State]
  ...
```

3. Proceeds to cleanup and state file update.

If all ledger files have empty confirmed and rejected arrays, print: "No candidates investigated. The codebase may be clean for this cluster's focus areas, or the sub-agents may not have found entry points. Consider running with a different project map focus."

### Stay In Your Lane

File about: Proven defects, data loss, security vulnerabilities, correctness errors, crashes, silent failures, performance defects severe enough to break the user experience.

NOT about: Style, formatting, naming concerns, missing features, design preferences dressed up as bugs, speculative races without a demonstrated interleaving, "might be wrong" observations without a trace, dead code unless reachable and producing wrong behavior.

### What NOT to Report (Sub-Agent Guidance)

Reinforced from the investigation methodology:
- Speculative races without a demonstrated interleaving
- "Might be wrong" observations without a trace
- Missing features or design preferences dressed up as bugs
- Dead code, unless it is reachable under a real input and does something wrong when it runs
- Style, formatting, or naming concerns
- Things that "could be faster" without evidence of user-impacting degradation

### Cross-Cluster Notes

Same mechanism as siblings. JSON array written to `<cache>/cross-cluster-<cluster-slug>.json`. Post-processor weaves findings into target ticket descriptions.

### Post-Processor

Same structure as siblings, persona updated to "post-processor for triage-bugs."

## Marketplace Update

The `agentic-marketplace` repo's `.claude-plugin/marketplace.json` plugin description should be updated to reflect the new skill names:

```json
{
  "name": "agentic-toolkit",
  "source": { "source": "github", "repo": "adamcaviness/agentic-toolkit" },
  "description": "Skills for ticket triage (bugs, architecture, product), code review, and branch shipping"
}
```

## README Update

The README should be updated to reflect the new skill names and add triage-bugs to the skill table.

## Scope Summary

| Item | Action |
|---|---|
| `skills/architect-planner/SKILL.md` | Rename dir, update internals, update label language |
| `skills/product-planner/SKILL.md` | Rename dir, update internals, update label language |
| `skills/triage-bugs/SKILL.md` | New file, full skill |
| `README.md` | Update skill names and descriptions |
| `agentic-marketplace/marketplace.json` | Update plugin description |
