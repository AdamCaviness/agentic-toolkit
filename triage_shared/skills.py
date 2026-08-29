"""Per-skill inputs for the triage SKILL.md generator.

Each entry maps placeholder names that appear in template.md to the
skill-specific value. The generator does straight string substitution
of `{{key}}` -> SKILLS[skill_name][key].

Keys appear here in roughly the same order they appear in template.md
so that the file reads top-to-bottom like the generated SKILL.md does.
Block-shaped values are kept as raw multi-line strings to make the
generated output easy to diff and review.
"""

# triage-architecture data
ARCHITECTURE = {
    # frontmatter
    "description": (
        "Use when auditing a codebase for structural and safety issues. "
        "Caches tickets to disk, then spawns 4 parallel sub-agents (one "
        "per focus cluster) to scrutinize and file tickets."
    ),
    "title": "Triage Architecture",
    # orchestrator preamble (sentence after "You are an **orchestrator**.")
    "orchestrator_role": (
        "You do NOT audit code yourself. Your job is to detect the ticket "
        "system, cache tickets to disk, show coverage status, spawn 4 "
        "parallel sub-agents (one per cluster), and clean up when they "
        "finish."
    ),
    # mode bullet for create
    "create_mode_bullet": (
        "**No argument or `create`**: Create mode, sub-agents read code, "
        "check existing tickets for dupes, and file new tickets. They do "
        "NOT deeply scrutinize or rewrite existing tickets (only fix "
        "links, labels, or obviously wrong info)."
    ),
    # closed-tickets fetch label list
    "closed_labels_list": "`architecture`, `product`, or `bug`",
    # project-map step 3 (the numbered list step that names what to identify)
    "project_map_step_3_identify": (
        "Identify entry points, key architectural files, and patterns "
        "(auth, validation, routing, database, config)"
    ),
    # bullets after "The map should include:"
    "project_map_bullets": (
        "- **Tech stack**: language, framework, database, testing tools (extracted from dependency manifest)\n"
        "- **Directory structure**: actual tree output, pruned to reasonable depth\n"
        "- **Key files**: path + one-line description of what it does (entry points, middleware, routes, models, schemas, config)\n"
        "- **Architectural patterns**: how auth works, how errors are handled, how data flows (just name the files/patterns, don't explain the code)\n"
        "- **Conventions from CLAUDE.md**: note any project-specific conventions that affect auditing"
    ),
    # cluster slugs and human names, in display order
    "cluster_slugs": ["safety", "correctness", "maintainability", "completeness"],
    "cluster_names": ["Safety", "Correctness", "Maintainability", "Completeness"],
    # extra rule for the assignment-rules list (bugs-only addition)
    "assignment_extra_rule": "",
    # "Cluster slugs:" inline list
    "cluster_slugs_inline": (
        "`safety`, `correctness`, `maintainability`, `completeness`"
    ),
    # coverage status block
    "coverage_cluster_list": "Safety, Correctness, Maintainability, Completeness",
    # legacy planner-state key fallback parenthetical (with leading space if present)
    "coverage_legacy_fallback": (
        " (fall back to legacy key `architect-planner` if the new key is absent)"
    ),
    # deploy step verb in `description: "Audit/Investigate <ClusterName> cluster"`
    "deploy_description_verb": "Audit",
    # mode-section label phrase ("Full Mode" vs "Create Mode")
    "deploy_mode_section_label": "Full Mode or Refine Mode",
    # sub-agent persona block (everything between the opening ``` and "## Mode: {MODE}")
    "subagent_persona": (
        "You are a senior software architect auditing this codebase. You "
        "are one of 4 parallel agents, each focused on a different "
        "concern cluster."
    ),
    # cached-tickets "may carry any label" list
    "subagent_label_carry_list": "`architecture`, `product`, `bug`, or unlabeled",
    # cached-tickets "If you add ___ to a ticket"
    "subagent_label_context_phrase": "architectural context",
    # cached-tickets self-label name
    "subagent_self_label": "architecture",
    # cached-tickets dedup-other-lens list
    "subagent_dedup_other_lens": "product, bug",
    # cached-tickets dedup focus phrase
    "subagent_dedup_focus": "the architectural root cause",
    # cross-cluster example issue ID
    "cross_cluster_example_id": "42",
    # cross-cluster related_issues array literal
    "cross_cluster_related_issues": "[15, 28]",
    # orient project-map description (middle of "It tells you ___.")
    "orient_map_description": (
        "tech stack, directory structure, key files, and architectural patterns"
    ),
    # orient extras block (between "...for your focus areas." and "## Your Cluster")
    # Includes trailing blank line so the "## Your Cluster" heading lands correctly.
    "orient_extras": (
        "Critical mindset: Don't assume features are missing. Read the code. "
        "When you find existing implementations, evaluate: Is it robust? Edge "
        "cases? Bypassable? Fails safely?\n\n"
    ),
    # focus extras block (between "Deep-read code for ALL focus areas in this cluster." and "{MODE_SECTION}")
    # Starts with a leading blank line so the previous line stays terminal,
    # and ends with a trailing blank line so {MODE_SECTION} lands correctly.
    "focus_extras": (
        "\n"
        "Before assessing any file, check for recent activity:\n"
        "git log --since=\"3 days ago\" --oneline -- <file>\n"
        "Note recent commits in tickets or skip if being addressed.\n"
        "\n"
        "## Synthesize Before Acting\n"
        "\n"
        "After reading all code for your cluster, stop. Before filing or refining any ticket, answer these questions about the code you just read:\n"
        "\n"
        "1. **Why was it built this way?** Understand the original author's intent and constraints before judging. Code that survived production earned its place. What problem was it solving?\n"
        "2. **Where does the architecture fight the problem?** Complexity that doesn't serve the domain, missing abstractions that would improve testability or clarity, over-abstraction that obscures intent without enabling anything.\n"
        "3. **Where is logic fragmented?** The same concern scattered across files that should be consolidated, or a monolith that should be decomposed for testability and clarity.\n"
        "4. **What would the right architecture look like?** Not necessarily simpler. The architecture that best fits the problem. Sometimes that means adding a proper abstraction layer, an interface for mockability, or a separation that enables independent testing. Sometimes it means consolidating.\n"
        "\n"
        "When multiple surface-level findings (a race condition here, missing validation there, inconsistent errors elsewhere) trace back to the same architectural root cause, **the root cause is your ticket**, not the individual symptoms.\n"
        "\n"
    ),
    # cluster-definitions full block (after "### Cluster Definitions\n\n")
    "cluster_definitions": (
        "**Safety** - Boundaries and defenses. What happens when bad input arrives, auth is missing, errors occur, or systems go down?\n"
        "\n"
        "| Focus Area | What to Look For |\n"
        "|------------|-----------------|\n"
        "| **Input validation** | Unsanitized user input, missing schema checks at boundaries, SQL injection, XSS vectors |\n"
        "| **Auth & secrets** | Auth bypass paths, tokens in logs/URLs, secrets in code, missing middleware on routes |\n"
        "| **Error handling** | Unhandled promise rejections, empty catch blocks, silent failures, missing error propagation |\n"
        "| **Failure modes** | What happens when DB is down? API timeout? Network partition? Graceful degradation vs. silent corruption |\n"
        "\n"
        "**Correctness** - Does the code do what it claims? Concurrency bugs, logic errors, type holes, data corruption paths.\n"
        "\n"
        "| Focus Area | What to Look For |\n"
        "|------------|-----------------|\n"
        "| **Race conditions** | Concurrent writes without locks, TOCTOU bugs, missing transactions, unsafe shared state |\n"
        "| **Logical flow** | Unreachable code, impossible states, off-by-one errors, wrong operator, inverted conditions |\n"
        "| **Type safety** | `any` types, missing type annotations on public interfaces, unsafe casts/assertions that suppress real errors, runtime type mismatches that static analysis misses |\n"
        "| **Data integrity** | Missing foreign keys, orphaned records, no cascading deletes, inconsistent state possible |\n"
        "\n"
        "**Maintainability** - Can the next developer understand and safely change this? Cruft, duplication, misleading names, structural problems.\n"
        "\n"
        "| Focus Area | What to Look For |\n"
        "|------------|-----------------|\n"
        "| **Dead code** | Unused functions, unreachable branches, imports that go nowhere, feature flags permanently on/off, commented-out code left behind, variables assigned but never read |\n"
        "| **DRY & code reuse** | Duplicated logic across files (same validation, same transformation, same API call pattern in 2+ places), copy-pasted components or controls that should be shared, near-identical functions that differ only in a parameter, opportunities to extract shared utilities or composables |\n"
        "| **Naming & semantics** | Misleading function/variable/file names, names that don't match what the code actually does, inconsistent naming for the same concept across files (e.g., `user` in one file and `account` in another for the same entity), abbreviations that obscure meaning, boolean names that read backwards |\n"
        "| **Architecture & file organization** | God files (split when a file serves multiple unrelated purposes), missing abstractions, directory structure that doesn't reflect domain boundaries, files in the wrong directory for what they do |\n"
        "\n"
        "**Completeness** - Is the work finished? Missing tests, inconsistent APIs, unused config, unhandled branches, performance gaps.\n"
        "\n"
        "| Focus Area | What to Look For |\n"
        "|------------|-----------------|\n"
        "| **API contract consistency** | Endpoints returning different response shapes for similar resources, inconsistent error formats across endpoints, fields present in one response but missing from a sibling endpoint |\n"
        "| **Configuration hygiene** | Hardcoded magic numbers/strings that should be config, config values defined but never read, env vars documented but unused (or used but undocumented) |\n"
        "| **Consistency & completeness** | A pattern used in N places but missing from the N+1th, partial migrations (old approach in some files, new approach in others), enum values or config options that exist in a definition but aren't handled in all switch/if branches, features half-wired (route exists but component doesn't use it, field added to model but never populated) |\n"
        "| **Test coverage** | Untested critical paths, missing edge case tests, no integration tests for key flows |\n"
        "| **Performance** | N+1 queries, missing indexes, unbounded loops, memory leaks, missing pagination |"
    ),
    # create-mode body block (the entire fenced ``` block under "**Create mode** ...:")
    "create_mode_section": (
        "## Create New Tickets\n"
        "\n"
        "Your job: find NEW problems in the codebase within your cluster's focus areas and file well-formed tickets.\n"
        "\n"
        "Hard cap: maximum 3 new tickets.\n"
        "\n"
        "### Dedup Check\n"
        "\n"
        "Before creating any ticket, scan existing tickets for overlap:\n"
        "1. Read ticket titles and descriptions in issues-open.json. Is this problem already covered?\n"
        "2. Check issues-closed.json. Was this already filed? For tickets closed as `completed`, you have a direct title-level duplicate. For tickets closed as `not_planned` (or wontfix in non-GitHub systems), read the closing comment, if your candidate shares the rejected ticket's threat model, assumption, or framing, treat it as a refile and do not file it, even if the title differs.\n"
        "3. If already covered and your finding adds context: if the ticket is in your edit file, edit the description directly. If it is outside your edit file, write it to your cross-cluster notes file. Do NOT add comments. Do NOT rewrite existing ticket descriptions, that's refine's job.\n"
        "4. If not covered: create a new focused ticket.\n"
        "\n"
        "If you notice an existing ticket has obviously wrong info (e.g., references a file that no longer exists, wrong label), fix it. But do NOT deeply scrutinize, rewrite descriptions, or re-evaluate severity, that's refine's job.\n"
        "\n"
        "### Over-Cap Findings\n"
        "\n"
        "When you have more than 3 valid findings, file the strongest 3. Write the rest to `{CACHE_DIR}/over-cap-{CLUSTER_SLUG}.json` as a JSON array. Each entry must be a finding that cleared dedup AND the pre-filing gate, only the cap kept it from being filed. The file must always be written, an empty array if you had no overflow, so the orchestrator can distinguish \"no overflow\" from \"agent failed to record overflow\". Each entry has this shape:\n"
        "\n"
        "\\`\\`\\`json\n"
        "[\n"
        "  {\n"
        "    \"title\": \"Candidate title that would have been filed\",\n"
        "    \"evidence\": \"path/to/file.ts:120 plus a one-line description\",\n"
        "    \"severity\": \"high | medium | low\",\n"
        "    \"why\": \"One line on why this would have been filed\"\n"
        "  }\n"
        "]\n"
        "\\`\\`\\`\n"
        "\n"
        "This is for valid findings that lost a slot to the cap. Do not use it for candidates that failed the pre-filing gate or duplicated existing tickets.\n"
        "\n"
        "### Pre-Filing Gate\n"
        "\n"
        "Before filing, ask: \"So what, and is the fix worth the trade-off?\" If the system already handles the outcome (negative balances by design, proxy handles security headers, parameterized queries make \"unvalidated\" input safe), there's no issue. If the fix adds complexity for marginal benefit, the cure is worse than the disease. A theoretical race condition whose consequence is already handled gracefully isn't a real problem.\n"
        "\n"
        "### Filing\n"
        "\n"
        "Create a new ticket with the `architecture` label and a severity label (`severity:high`, `severity:medium`, or `severity:low`). Use the following structure for the body:\n"
        "\n"
        "## Problem\n"
        "What is wrong or missing. Reference specific files and line numbers.\n"
        "\n"
        "## Root Cause\n"
        "Why this problem exists. The architectural decision, structural pattern, or missing abstraction that produced it. If multiple symptoms share this root cause, name them. Don't just describe the symptom; explain what about the current architecture allowed or caused it.\n"
        "\n"
        "## Evidence\n"
        "Code snippet or trace showing the issue. Not speculation, proof.\n"
        "\n"
        "## Risk\n"
        "What can go wrong. Severity (data loss? security breach? silent corruption? annoying log noise?).\n"
        "\n"
        "## Suggested Fix\n"
        "Describe the target architecture. What the code should look like after, not just what to change. Explain why this structure fits the problem (testability, performance, maintainability, clarity). One confident direction, not a menu of options.\n"
        "\n"
        "Severity guide:\n"
        "- severity:high: Data loss, security breach, silent corruption, or production outage possible\n"
        "- severity:medium: Incorrect behavior under edge cases, degraded reliability, or maintainability hazard\n"
        "- severity:low: Code smell, minor inconsistency, theoretical concern unlikely to bite\n"
        "\n"
        "Rules:\n"
        "- One problem per ticket\n"
        "- Label all tickets architecture + a severity label\n"
        "- Never file UX complaints, copy issues, or product gaps\n"
        "- Reference specific files and line numbers you actually read\n"
        "- Distinguish \"missing entirely\" from \"exists but has gaps\"\n"
        "- For security issues, note external vs internal exploitability"
    ),
    # refine-mode body block
    "refine_mode_section": (
        "## Refine Existing Tickets\n"
        "\n"
        "Your job: improve existing tickets related to your cluster. Do NOT create new tickets.\n"
        "\n"
        "Prioritize:\n"
        "1. Open tickets related to your cluster's focus areas\n"
        "2. Oldest open tickets without recent comments\n"
        "3. Tickets related to code you just read\n"
        "\n"
        "For each ticket you deep-read, ask:\n"
        "- Still true? Read the code NOW. Close with evidence if fixed.\n"
        "- Analysis correct? If wrong, rewrite the description with corrected analysis.\n"
        "- Symptom or root cause? Trace the problem upstream. If the ticket describes a symptom, rewrite it to address the architectural root cause. If multiple open tickets share a root cause, consolidate into one architectural ticket and close the others with a cross-reference.\n"
        "- Complete? Add line numbers, code paths, edge cases to the description.\n"
        "- Fix sound? The suggested fix should describe the target architecture, why this structure fits the problem, not just a patch. Update if it's vague, offers multiple options, or only addresses the symptom.\n"
        "- Severity right? Recalibrate and update the severity label.\n"
        "- Dependencies? If the dependency is in your edit file, add cross-references to the description. If outside your edit file, write to your cross-cluster notes file.\n"
        "\n"
        "### Editing tickets: description is the source of truth\n"
        "\n"
        "**When the ticket's core content needs changing** (problem statement, evidence, severity, fix direction), **edit the description directly**. The description must always be the canonical, accurate statement. Do NOT leave corrections as comments while the description stays wrong.\n"
        "\n"
        "**When synthesizing:** If the ticket has comments from the same user as you (prior skill runs), fold their corrections and additions into the description, then delete those comments. The description becomes one clean, authoritative ticket. Never touch comments from other users.\n"
        "\n"
        "Do not add comments to any ticket. All findings, cross-references, and dependency notes belong in the ticket description. If the target ticket is in your edit file, edit the description directly. If it is outside your edit file, write to your cross-cluster notes file.\n"
        "\n"
        "### Available operations\n"
        "\n"
        "Ticket bodies and comments are already in issues-open.json, no need to fetch them again.\n"
        "\n"
        "- Edit a ticket's description\n"
        "- Delete a redundant comment from a prior skill run (after synthesizing into description)\n"
        "- Close a resolved ticket (add a Resolution section to the description first, then close)\n"
        "\n"
        "Use whatever CLI tools or APIs are available for the detected ticket system.\n"
        "\n"
        "Do not rubber-stamp. If something feels off, dig in."
    ),
    # stay-in-lane block (the file/notfile lines, no trailing newline)
    "stay_in_lane": (
        "File about: Bugs, security, error handling, race conditions, architecture, DRY violations, naming inconsistencies, dead code, type safety gaps, API contract issues, incomplete implementations, performance, test gaps, data integrity\n"
        "NOT about: UX, user confusion, missing features, terminology, onboarding, accessibility"
    ),
    # Step 3.5 heading suffix (" and Collect Ledgers" for bugs, "" otherwise)
    "step35_heading_suffix": "",
    # Step 3.5 body intro paragraph after the heading
    "step35_intro_paragraph": (
        "After all 4 sub-agents complete, check for cross-cluster findings:"
    ),
    # bugs-only ledger collection + summary block, prepended to the
    # numbered cross-cluster file list. Empty for non-bugs.
    "step35_pre_cross_cluster": "",
    # Step 4 cleanup intro extra phrase (e.g. ", ledger collection,")
    "step4_pre_cleanup_phrase": "",
    # post-processor "integrate it into the relevant section" example field list
    "post_processor_section_examples": "Problem, Root Cause, Evidence, Risk, Suggested Fix, etc.",
}


# triage-bugs data
BUGS = {
    "description": (
        "Use when hunting proven defects. Adversarial 4-pass analysis "
        "(frame, trace, falsify, prove). Caches tickets to disk, then "
        "spawns 4 parallel sub-agents (one per bug category) to find, "
        "prove, and document bugs with enough rigor that a skeptical "
        "maintainer could fix each from the report alone."
    ),
    "title": "Triage Bugs",
    "orchestrator_role": (
        "You do NOT investigate bugs yourself. Your job is to detect the "
        "ticket system, cache tickets to disk, show coverage status, "
        "spawn 4 parallel sub-agents (one per cluster), collect their "
        "ledgers, and clean up when they finish."
    ),
    "create_mode_bullet": (
        "**No argument or `create`**: Create mode, sub-agents investigate "
        "code, check existing tickets for dupes, and file new tickets for "
        "proven defects. They do NOT deeply scrutinize or rewrite "
        "existing tickets (only fix links, labels, or obviously wrong "
        "info)."
    ),
    "closed_labels_list": "`bug`, `architecture`, or `product`",
    "project_map_step_3_identify": (
        "Identify entry points, key architectural files, patterns, and "
        "bug-relevant infrastructure"
    ),
    "project_map_bullets": (
        "- **Tech stack**: language, framework, database, testing tools (extracted from dependency manifest)\n"
        "- **Directory structure**: actual tree output, pruned to reasonable depth\n"
        "- **Key files**: path + one-line description of what it does (entry points, middleware, routes, models, schemas, config)\n"
        "- **Error handling patterns**: how errors propagate, global handlers, catch blocks, error middleware\n"
        "- **Async boundaries**: promises, callbacks, event handlers, queues, workers, pub/sub\n"
        "- **Database access patterns**: ORM vs raw queries, transaction usage, connection pooling, migration state\n"
        "- **Auth middleware chain**: which routes are protected, how tokens are validated, session management\n"
        "- **External API integrations**: third-party services, webhooks, outbound HTTP calls, retry policies\n"
        "- **Conventions from CLAUDE.md**: note any project-specific conventions that affect investigation"
    ),
    "cluster_slugs": ["data-state", "security-auth", "correctness", "silent-failures"],
    "cluster_names": ["Data & State", "Security & Auth", "Correctness", "Silent Failures"],
    "assignment_extra_rule": (
        "\n- Tickets may carry any label (`bug`, `architecture`, "
        "`product`, or unlabeled). Assign by content, not by label."
    ),
    "cluster_slugs_inline": (
        "`data-state`, `security-auth`, `correctness`, `silent-failures`"
    ),
    "coverage_cluster_list": (
        "Data & State, Security & Auth, Correctness, Silent Failures"
    ),
    "coverage_legacy_fallback": "",
    "deploy_description_verb": "Investigate",
    "deploy_mode_section_label": "Create Mode or Refine Mode",
    "subagent_persona": (
        "You are a senior bug investigator working inside this codebase. "
        "Your mandate is narrow and strict: find real defects, prove them, "
        "and document them with enough rigor that a skeptical maintainer "
        "could fix the bug from your report alone. You are one of 4 "
        "parallel agents, each focused on a different bug category.\n"
        "\n"
        "Your default posture is adversarial toward your own findings. "
        "Assume every suspected bug is innocent until you've done the "
        "work to convict it."
    ),
    "subagent_label_carry_list": "`bug`, `architecture`, `product`, or unlabeled",
    "subagent_label_context_phrase": "bug evidence",
    "subagent_self_label": "bug",
    "subagent_dedup_other_lens": "architecture, product",
    "subagent_dedup_focus": "proving the defect",
    "cross_cluster_example_id": "42",
    "cross_cluster_related_issues": "[15, 28]",
    "orient_map_description": (
        "tech stack, directory structure, key files, error handling "
        "patterns, async boundaries, database access patterns, auth "
        "chain, and external integrations"
    ),
    # bugs has the "recent activity" block in Orient (not after focus table).
    # The "your investigation" / "actively addressed" wording is bugs-specific.
    "orient_extras": (
        "Before assessing any file, check for recent activity:\n"
        "git log --since=\"3 days ago\" --oneline -- <file>\n"
        "Note recent commits in your investigation or skip if being actively addressed.\n"
        "\n"
    ),
    # bugs's focus_extras is the Certainty Bar + 4-Pass + Rejection Ledger.
    # Starts with leading blank line and ends with trailing blank line.
    "focus_extras": (
        "\n"
        "## The Certainty Bar\n"
        "\n"
        "Before you document anything, your confidence must rest on at least one of the following:\n"
        "\n"
        "- **A deterministic reproduction**, a sequence of inputs or steps that triggers the defect every time.\n"
        "- **A code-path proof**, an end-to-end trace showing the defect must occur under clearly stated conditions, with no plausible guard, validator, or handler that would prevent it.\n"
        "- **A failing test**, one you wrote or ran that isolates the defect.\n"
        "\n"
        "\"It looks wrong,\" \"this could race,\" \"this might fail under load,\" and \"this seems off\" do not clear the bar. If you can't produce one of the three above, add the candidate to your rejection ledger and move on. Weak reports poison the backlog.\n"
        "\n"
        "## 4-Pass Investigation Method\n"
        "\n"
        "For each candidate defect, work in four passes. Do not skip ahead.\n"
        "\n"
        "**Pass 1, Frame the claim.** Write down, in one sentence, the specific wrong behavior you think exists, the conditions under which it occurs, and the observable symptom. If you can't do this crisply, you don't understand it yet, keep reading code, don't start writing a report.\n"
        "\n"
        "**Pass 2, Trace the code.** Read the relevant paths end-to-end, not just the function you suspect. Follow inputs through validation, state transitions, async boundaries, persistence, authorization checks, caching layers, error handlers, and serialization/deserialization. Note every place the value could be mutated, guarded, normalized, or rescued.\n"
        "\n"
        "**Pass 3, Falsify.** Actively hunt for reasons your suspicion is wrong. Is there a validator upstream that makes the bad input unreachable? A try/catch that handles it? A default that masks it? A test that already pins the real behavior? If you find a rescue mechanism, the bug either doesn't exist or lives somewhere else, say so and move on. This pass is the one most investigators skip; skipping it is how false positives get filed.\n"
        "\n"
        "**Pass 4, Prove.** Reproduce it, write a failing test, or produce a causal trace tight enough that a reviewer cannot plausibly object. If this pass fails, the candidate is not ready to report, add it to your rejection ledger.\n"
        "\n"
        "## Rejection Ledger\n"
        "\n"
        "You MUST write a ledger file at `{CACHE_DIR}/ledger-{CLUSTER_SLUG}.json` when you finish, regardless of whether you found any bugs. Write this JSON structure:\n"
        "\n"
        "\\`\\`\\`json\n"
        "{\n"
        "  \"confirmed\": [\n"
        "    { \"id\": 201, \"title\": \"Race in session refresh allows double-spend\", \"severity\": \"high\" }\n"
        "  ],\n"
        "  \"rejected\": [\n"
        "    {\n"
        "      \"candidate\": \"Possible null deref in parseConfig\",\n"
        "      \"reason\": \"Guarded by schema validation at api/middleware.ts:44\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "\\`\\`\\`\n"
        "\n"
        "Both arrays may be empty. The file must always be written so the orchestrator can distinguish \"no findings\" from \"agent failed to write ledger.\"\n"
        "\n"
        "The rejection list is not filler. It tells the maintainer where you looked and what they don't need to re-check.\n"
        "\n"
    ),
    "cluster_definitions": (
        "**Data & State** - Data integrity, data loss, state corruption, stuck workflows, unrecoverable states.\n"
        "\n"
        "| Focus Area | What to Investigate |\n"
        "|---|---|\n"
        "| **Data loss paths** | Writes that can silently fail, truncation without warning, missing persistence after user confirmation, operations that destroy data without backup/undo |\n"
        "| **Data integrity** | Missing foreign keys causing orphans, transactions that partially commit, concurrent writes without locks that corrupt state, missing cascading deletes/updates |\n"
        "| **State corruption** | State machines that can reach impossible states, UI state that diverges from server state, caches that serve stale data after writes, workflows that get stuck with no recovery path |\n"
        "| **Stuck workflows** | Operations that hang without timeout, retry loops without backoff or limit, deadlocks, user flows that reach dead ends with no way back |\n"
        "\n"
        "**Security & Auth** - Authorization bypass, authentication defects, secrets exposure, injection vectors.\n"
        "\n"
        "| Focus Area | What to Investigate |\n"
        "|---|---|\n"
        "| **Authentication** | Login bypass paths, session fixation, token expiration not enforced, password reset flows that leak information |\n"
        "| **Authorization** | Routes/endpoints missing auth middleware, privilege escalation (user accessing admin resources), IDOR (accessing another user's data by changing an ID), missing ownership checks on mutations |\n"
        "| **Secrets** | Credentials in source, tokens logged or in URLs, API keys in client bundles, secrets in error messages |\n"
        "| **Injection** | SQL injection via string concatenation, XSS via unsanitized user content, command injection through user input, path traversal |\n"
        "\n"
        "**Correctness** - User-visible wrong results, crashes, runtime errors on supported paths.\n"
        "\n"
        "| Focus Area | What to Investigate |\n"
        "|---|---|\n"
        "| **Wrong results** | Calculations that produce incorrect output under specific inputs, filters/queries that return wrong sets, sorting that violates stated order, off-by-one errors in pagination or ranges |\n"
        "| **Crashes & runtime errors** | Null/undefined dereferences on supported code paths, unhandled exceptions in non-exceptional flows, type mismatches that survive compilation but fail at runtime |\n"
        "| **Logic errors** | Inverted conditions, unreachable code that should be reachable, boolean expressions that always evaluate the same way, switch/match with missing cases that receive real input |\n"
        "| **Regression-prone paths** | Behavior that depends on implicit ordering, code that works by coincidence (e.g., relying on map iteration order), assumptions about input shape that aren't validated |\n"
        "\n"
        "**Silent Failures** - Swallowed errors, missing retries where correctness requires them, lost writes, severe performance defects.\n"
        "\n"
        "| Focus Area | What to Investigate |\n"
        "|---|---|\n"
        "| **Swallowed errors** | Empty catch blocks, errors caught and not re-thrown or logged, promises without rejection handlers, error callbacks that do nothing |\n"
        "| **Lost writes** | Fire-and-forget mutations with no confirmation, optimistic updates with no rollback on failure, queued writes that can drop silently, race conditions between read-modify-write sequences |\n"
        "| **Missing retry/recovery** | Network calls that fail once and give up where correctness requires delivery, idempotency violations on retry, recovery paths that leave partial state |\n"
        "| **Performance as defect** | N+1 queries that degrade to unusable at realistic scale, unbounded memory growth, missing pagination on endpoints that return unbounded results, operations that block the event loop |"
    ),
    "create_mode_section": (
        "## Create New Tickets\n"
        "\n"
        "Your job: find NEW proven defects in the codebase within your cluster's focus areas and file well-formed tickets.\n"
        "\n"
        "Hard cap: maximum 3 new tickets. One excellent report beats five weak ones.\n"
        "\n"
        "### Dedup Check\n"
        "\n"
        "Before creating any ticket, scan existing tickets for overlap:\n"
        "1. Read ticket titles and descriptions in issues-open.json. Is this defect already covered?\n"
        "2. Check issues-closed.json. Was this already filed? For tickets closed as `completed`, you have a direct title-level duplicate. For tickets closed as `not_planned` (or wontfix in non-GitHub systems), read the closing comment, if your candidate shares the rejected ticket's threat model, assumption, or framing, treat it as a refile and do not file it, even if the title differs.\n"
        "3. If already covered and your finding adds evidence: if the ticket is in your edit file, edit the description to add the proof. If it is outside your edit file, write it to your cross-cluster notes file. Do NOT add comments. Do NOT rewrite existing ticket descriptions, that's refine's job.\n"
        "4. If not covered: file a new ticket after passing the pre-filing gate.\n"
        "\n"
        "If you notice an existing ticket has obviously wrong info (e.g., references a file that no longer exists, wrong label), fix it. But do NOT deeply scrutinize, rewrite descriptions, or re-evaluate severity, that's refine's job.\n"
        "\n"
        "### Over-Cap Findings\n"
        "\n"
        "When you have more than 3 confirmed defects (each cleared dedup, the certainty bar, and the pre-filing gate), file the strongest 3. Write the rest to `{CACHE_DIR}/over-cap-{CLUSTER_SLUG}.json` as a JSON array. This is distinct from the rejection ledger: the ledger holds candidates that failed the certainty bar; over-cap holds proven defects that lost a slot to the cap. The file must always be written, an empty array if you had no overflow, so the orchestrator can distinguish \"no overflow\" from \"agent failed to record overflow\". Each entry has this shape:\n"
        "\n"
        "\\`\\`\\`json\n"
        "[\n"
        "  {\n"
        "    \"title\": \"Candidate title that would have been filed\",\n"
        "    \"evidence\": \"path/to/file.ts:120 plus a one-line description\",\n"
        "    \"severity\": \"high | medium | low\",\n"
        "    \"why\": \"One line on why this would have been filed\"\n"
        "  }\n"
        "]\n"
        "\\`\\`\\`\n"
        "\n"
        "Do not move ledger-rejected candidates here. Do not move dedup-rejected candidates here. Only proven defects that fully cleared every gate.\n"
        "\n"
        "### Pre-Filing Gate\n"
        "\n"
        "Before filing, ask: \"Is this actually a bug, or am I pattern-matching on something that looks wrong but behaves correctly by design?\"\n"
        "\n"
        "Checks:\n"
        "- Is the behavior documented as intentional (in docstrings, comments, or design docs)?\n"
        "- Is there a test that asserts this exact behavior?\n"
        "- Is there a guard, validator, or handler upstream that prevents the condition from being reached?\n"
        "- If the behavior is wrong, is the impact real or purely theoretical?\n"
        "- Did I clear the certainty bar (reproduction, code-path proof, or failing test)?\n"
        "\n"
        "If on the fence, add to the rejection ledger instead of filing.\n"
        "\n"
        "### Filing\n"
        "\n"
        "Create a new ticket with the `bug` label and a severity label (`severity:high`, `severity:medium`, or `severity:low`). Use the following structure for the body:\n"
        "\n"
        "## Summary\n"
        "What the bug is and why it matters.\n"
        "\n"
        "## Impact\n"
        "Who or what is affected and how badly.\n"
        "\n"
        "## Conditions\n"
        "The precise conditions under which the bug fires.\n"
        "\n"
        "## Reproduction\n"
        "Numbered steps. If not reproduced at runtime, write:\n"
        "\"Not reproduced at runtime; confirmed by code-path analysis.\"\n"
        "and explain the trace briefly.\n"
        "\n"
        "## Expected behavior\n"
        "What should happen.\n"
        "\n"
        "## Actual behavior\n"
        "What actually happens.\n"
        "\n"
        "## Evidence\n"
        "- Files and functions involved\n"
        "- Relevant code excerpts with line references\n"
        "- Failing test name, if any\n"
        "- Stack trace or error output, if any\n"
        "\n"
        "## Root cause\n"
        "The underlying defect, explained rigorously but briefly.\n"
        "\n"
        "## Scope\n"
        "Adjacent features, routes, jobs, endpoints, or state likely also affected.\n"
        "\n"
        "## Acceptance criteria\n"
        "Concrete, checkable statements that define \"fixed.\"\n"
        "\n"
        "Severity guide:\n"
        "- severity:high: Data loss, security breach, silent corruption, crashes on supported paths\n"
        "- severity:medium: Wrong results under edge cases, degraded reliability, stuck states with workaround\n"
        "- severity:low: Silent failure with minimal impact, performance defect not yet at breaking point\n"
        "\n"
        "Rules:\n"
        "- One defect per ticket\n"
        "- Label all tickets bug + a severity label\n"
        "- Never file style, naming, or missing feature concerns\n"
        "- Reference specific files and line numbers you actually read\n"
        "- Distinguish \"missing entirely\" from \"exists but broken\"\n"
        "- For security issues, note external vs internal exploitability\n"
        "- Label severity honestly. If everything is \"critical,\" nothing is."
    ),
    "refine_mode_section": (
        "## Refine Existing Tickets\n"
        "\n"
        "Your job: improve existing tickets related to your cluster. Do NOT create new tickets.\n"
        "\n"
        "Prioritize:\n"
        "1. Open tickets related to your cluster's focus areas\n"
        "2. Oldest open tickets without recent comments\n"
        "3. Tickets related to code you just read\n"
        "\n"
        "For each ticket you deep-read, apply the 4-pass investigation method:\n"
        "- Still true? Read the code NOW. Trace the reported defect. Close with evidence if fixed.\n"
        "- Analysis correct? If the reported root cause is wrong, trace the real cause and rewrite the description.\n"
        "- Proven? Does the ticket meet the certainty bar? If not, investigate further. Add a reproduction, code-path proof, or failing test to the description. If you cannot prove it after investigation, close the ticket with an explanation of why the defect cannot be confirmed.\n"
        "- Complete? Add line numbers, code paths, edge cases, acceptance criteria to the description.\n"
        "- Severity right? Recalibrate based on your investigation and update the severity label.\n"
        "- Dependencies? If the dependency is in your edit file, add cross-references to the description. If outside your edit file, write to your cross-cluster notes file.\n"
        "\n"
        "### Promotion\n"
        "\n"
        "When investigating a ticket that carries `architecture` or `product` labels but not `bug`, and you prove it contains an actual defect (you meet the certainty bar), enrich the ticket:\n"
        "1. Add the proof sections to the description (Reproduction, Evidence, Root Cause, Acceptance Criteria)\n"
        "2. Add the `bug` label alongside the existing labels\n"
        "3. Update severity if warranted\n"
        "This enriches the ticket without disrupting its existing context.\n"
        "\n"
        "### Editing tickets: description is the source of truth\n"
        "\n"
        "**When the ticket's core content needs changing** (problem statement, evidence, severity, root cause), **edit the description directly**. The description must always be the canonical, accurate statement. Do NOT leave corrections as comments while the description stays wrong.\n"
        "\n"
        "**When synthesizing:** If the ticket has comments from the same user as you (prior skill runs), fold their corrections and additions into the description, then delete those comments. The description becomes one clean, authoritative ticket. Never touch comments from other users.\n"
        "\n"
        "Do not add comments to any ticket. All findings, cross-references, and dependency notes belong in the ticket description. If the target ticket is in your edit file, edit the description directly. If it is outside your edit file, write to your cross-cluster notes file.\n"
        "\n"
        "### Available operations\n"
        "\n"
        "Ticket bodies and comments are already in issues-open.json, no need to fetch them again.\n"
        "\n"
        "- Edit a ticket's description\n"
        "- Delete a redundant comment from a prior skill run (after synthesizing into description)\n"
        "- Close a resolved or unconfirmable ticket (add a Resolution section to the description first, then close)\n"
        "\n"
        "Use whatever CLI tools or APIs are available for the detected ticket system.\n"
        "\n"
        "Do not rubber-stamp. If something feels off, dig in."
    ),
    "stay_in_lane": (
        "File about: Proven defects, data loss, security vulnerabilities, correctness errors, crashes, silent failures, performance defects severe enough to break the user experience\n"
        "NOT about: Style, formatting, naming concerns, missing features, design preferences dressed up as bugs, speculative races without a demonstrated interleaving, dead code unless reachable and producing wrong behavior"
    ),
    # bugs collects ledgers and prints a unified summary before processing cross-cluster notes
    "step35_pre_cross_cluster": (
        "### Collect Ledgers\n"
        "\n"
        "Read all 4 ledger files from the cache directory:\n"
        "- `ledger-data-state.json`\n"
        "- `ledger-security-auth.json`\n"
        "- `ledger-correctness.json`\n"
        "- `ledger-silent-failures.json`\n"
        "\n"
        "If any ledger file is missing, note which cluster failed to produce one. Merge all confirmed and rejected entries into two master lists, tagging each with its source cluster.\n"
        "\n"
        "### Print Unified Summary\n"
        "\n"
        "```\n"
        "Triage Complete (triage-bugs):\n"
        "Mode: create | refine\n"
        "Last run: <previous timestamp or \"never\">\n"
        "\n"
        "Confirmed (N):\n"
        "  #201 \"Race in session refresh allows double-spend\", severity:high [Data & State]\n"
        "  #202 \"Missing CSRF on /api/transfer\", severity:high [Security & Auth]\n"
        "  ...\n"
        "\n"
        "Investigated & Rejected (M):\n"
        "  \"Possible null deref in parseConfig\", guarded by schema validation at api/middleware.ts:44 [Correctness]\n"
        "  \"Stale cache after write\", intentional per TTL design in cache.ts [Data & State]\n"
        "  ...\n"
        "```\n"
        "\n"
        "If all ledger files have empty confirmed and rejected arrays, print: \"No candidates investigated. The codebase may be clean for this cluster's focus areas, or the sub-agents may not have found entry points. Consider running with a different project map focus.\"\n"
        "\n"
        "### Cross-Cluster Notes\n"
        "\n"
        "Check for cross-cluster findings:\n"
        "\n"
    ),
    "step35_heading_suffix": " and Collect Ledgers",
    "step35_intro_paragraph": "After all 4 sub-agents complete:",
    "step4_pre_cleanup_phrase": ", ledger collection,",
    "post_processor_section_examples": (
        "Summary, Impact, Evidence, Root Cause, Scope, etc."
    ),
}


# triage-product data
PRODUCT = {
    "description": (
        "Use when auditing product UX and workflows. Caches tickets to "
        "disk, then spawns 4 parallel sub-agents (one per focus cluster) "
        "to scrutinize and file tickets."
    ),
    "title": "Triage Product",
    "orchestrator_role": (
        "You do NOT audit the product yourself. Your job is to detect the "
        "ticket system, cache tickets to disk, show coverage status, "
        "spawn 4 parallel sub-agents (one per cluster), and clean up "
        "when they finish."
    ),
    "create_mode_bullet": (
        "**No argument or `create`**: Create mode, sub-agents read code, "
        "check existing tickets for dupes, and file new tickets. They do "
        "NOT deeply scrutinize or rewrite existing tickets (only fix "
        "links, labels, or obviously wrong info)."
    ),
    "closed_labels_list": "`architecture`, `product`, or `bug`",
    "project_map_step_3_identify": (
        "Identify entry points, key UI components, route definitions, and patterns"
    ),
    "project_map_bullets": (
        "- **Tech stack**: language, framework, database, testing tools (extracted from dependency manifest)\n"
        "- **Directory structure**: actual tree output, pruned to reasonable depth\n"
        "- **Key files**: path + one-line description of what it does (entry points, routes, components, layouts, config)\n"
        "- **Product context**: what the product promises the user (from README), who the user is, core workflows\n"
        "- **Conventions from CLAUDE.md**: note any project-specific conventions that affect auditing"
    ),
    "cluster_slugs": ["core-experience", "error-edge", "polish", "reach-access"],
    "cluster_names": [
        "Core Experience",
        "Error & Edge States",
        "Polish & Consistency",
        "Reach & Access",
    ],
    "assignment_extra_rule": "",
    "cluster_slugs_inline": (
        "`core-experience`, `error-edge`, `polish`, `reach-access`"
    ),
    "coverage_cluster_list": (
        "Core Experience, Error & Edge States, Polish & Consistency, Reach & Access"
    ),
    "coverage_legacy_fallback": (
        " (fall back to legacy key `product-planner` if the new key is absent)"
    ),
    "deploy_description_verb": "Audit",
    "deploy_mode_section_label": "Full Mode or Refine Mode",
    "subagent_persona": (
        "You are a product manager who just watched a real user try this "
        "app for the first time. You are one of 4 parallel agents, each "
        "focused on a different concern cluster."
    ),
    "subagent_label_carry_list": "`architecture`, `product`, `bug`, or unlabeled",
    "subagent_label_context_phrase": "product context",
    "subagent_self_label": "product",
    "subagent_dedup_other_lens": "architecture, bug",
    "subagent_dedup_focus": "the user-facing impact",
    "cross_cluster_example_id": "239",
    "cross_cluster_related_issues": "[234, 237]",
    "orient_map_description": (
        "tech stack, directory structure, key files, product context, "
        "and who the user is"
    ),
    "orient_extras": (
        "Judge against what the product promises, not abstract ideals.\n"
        "\n"
    ),
    "focus_extras": (
        "\n"
        "Before assessing any file, check for recent activity:\n"
        "git log --since=\"3 days ago\" --oneline -- <file>\n"
        "Note recent commits in tickets or skip if being addressed.\n"
        "\n"
    ),
    "cluster_definitions": (
        "**Core Experience** - Can the user figure out what to do, do it, and know it worked? Onboarding, task completion, feedback, findability.\n"
        "\n"
        "| Focus Area | What to Look For |\n"
        "|------------|-----------------|\n"
        "| **First-run experience** | Onboarding, empty states, \"what do I do now?\" moments |\n"
        "| **Workflow completeness** | Can the user finish what they started? Dead ends? |\n"
        "| **Feedback loops** | Does the user know what worked? What's pending? What broke? |\n"
        "| **Information architecture** | Can users find things? Is navigation logical? |\n"
        "\n"
        "**Error & Edge States** - What happens when things go wrong or get weird? Failures, dangerous actions, back/forward/refresh behavior.\n"
        "\n"
        "| Focus Area | What to Look For |\n"
        "|------------|-----------------|\n"
        "| **Error & loading states** | What happens when things fail? Spinners? Blank screens? |\n"
        "| **Destructive action safety** | Missing confirmations for irreversible actions, no undo capability, easy to accidentally trigger deletes/overwrites, no \"are you sure?\" for data loss |\n"
        "| **State & navigation** | Browser back/forward behavior, refresh losing state, URLs not reflecting current view (deep linking), navigating away mid-action and returning, bookmark-ability |\n"
        "\n"
        "**Polish & Consistency** - Does it feel like one product? Consistent language, visuals, and data formatting.\n"
        "\n"
        "| Focus Area | What to Look For |\n"
        "|------------|-----------------|\n"
        "| **Terminology & copy** | Jargon, inconsistent labels, ambiguous buttons |\n"
        "| **Visual & design consistency** | Inconsistent spacing/colors/typography across views, similar actions styled differently, design tokens not applied uniformly, components that do the same thing but look different |\n"
        "| **Data presentation** | Inconsistent date/number formatting, text overflow/truncation, how empty or null values display, surprising sort orders, long content breaking layouts |\n"
        "\n"
        "**Reach & Access** - Can everyone use it? Keyboard/screen reader support, small screens, multi-user scenarios, expected features.\n"
        "\n"
        "| Focus Area | What to Look For |\n"
        "|------------|-----------------|\n"
        "| **Accessibility** | Keyboard nav, screen readers, contrast, focus management |\n"
        "| **Mobile / responsive** | Does it work on small screens? |\n"
        "| **Permissions & roles** | Multi-user scenarios, what happens with no access? |\n"
        "| **Competitive table stakes** | Features users expect from similar tools that are missing |"
    ),
    "create_mode_section": (
        "## Create New Tickets\n"
        "\n"
        "Your job: find NEW product gaps in the codebase within your cluster's focus areas and file well-formed tickets.\n"
        "\n"
        "Hard cap: maximum 3 new tickets.\n"
        "\n"
        "### Dedup Check\n"
        "\n"
        "Before creating any ticket, scan existing tickets for overlap:\n"
        "1. Read ticket titles and descriptions in issues-open.json. Is this problem already covered?\n"
        "2. Check issues-closed.json. Was this already filed? For tickets closed as `completed`, you have a direct title-level duplicate. For tickets closed as `not_planned` (or wontfix in non-GitHub systems), read the closing comment, if your candidate shares the rejected ticket's threat model, assumption, or framing, treat it as a refile and do not file it, even if the title differs.\n"
        "3. If already covered and your finding adds context: if the ticket is in your edit file, edit the description directly. If it is outside your edit file, write it to your cross-cluster notes file. Do NOT add comments. Do NOT rewrite existing ticket descriptions, that's refine's job.\n"
        "4. If not covered: create a new focused ticket.\n"
        "\n"
        "If you notice an existing ticket has obviously wrong info (e.g., references a component that no longer exists, wrong label), fix it. But do NOT deeply scrutinize, rewrite descriptions, or re-evaluate severity, that's refine's job.\n"
        "\n"
        "### Over-Cap Findings\n"
        "\n"
        "When you have more than 3 valid findings, file the strongest 3. Write the rest to `{CACHE_DIR}/over-cap-{CLUSTER_SLUG}.json` as a JSON array. Each entry must be a finding that cleared dedup AND the pre-filing gate, only the cap kept it from being filed. The file must always be written, an empty array if you had no overflow, so the orchestrator can distinguish \"no overflow\" from \"agent failed to record overflow\". Each entry has this shape:\n"
        "\n"
        "\\`\\`\\`json\n"
        "[\n"
        "  {\n"
        "    \"title\": \"Candidate title that would have been filed\",\n"
        "    \"evidence\": \"path/to/component.tsx:120 plus a one-line description\",\n"
        "    \"severity\": \"high | medium | low\",\n"
        "    \"why\": \"One line on why this would have been filed\"\n"
        "  }\n"
        "]\n"
        "\\`\\`\\`\n"
        "\n"
        "This is for valid findings that lost a slot to the cap. Do not use it for candidates that failed the pre-filing gate or duplicated existing tickets.\n"
        "\n"
        "### Pre-Filing Gate\n"
        "\n"
        "Before filing, ask: \"What does the fix look like, and is the current behavior actually wrong?\" If the existing UX already handles the case (a button that resets IS a retry path, a transport fallback that delivers the same data ISN'T broken, a pessimistic delete that keeps the item visible on failure IS correct), there's no issue. If the fix wouldn't survive a \"would a senior PM prioritize this?\" test, don't file it.\n"
        "\n"
        "### Filing\n"
        "\n"
        "Create a new ticket with the `product` label and a severity label (`severity:high`, `severity:medium`, or `severity:low`). Use the following structure for the body:\n"
        "\n"
        "## Problem\n"
        "What the user experiences. Be specific, reference the actual screen/flow/component.\n"
        "\n"
        "## Impact\n"
        "Why this matters to the user. What do they feel or fail to do?\n"
        "\n"
        "## Suggested Direction\n"
        "How this could be addressed (not implementation details, product direction).\n"
        "\n"
        "Severity guide:\n"
        "- severity:high: User cannot complete a core workflow, or dealbreaker in competitive evaluation\n"
        "- severity:medium: User can work around it, but causes friction or confusion\n"
        "- severity:low: Polish, nice-to-have, minor inconsistency\n"
        "\n"
        "Rules:\n"
        "- One problem per ticket\n"
        "- Label all tickets product + a severity label\n"
        "- Never file code bugs, security issues, or architectural concerns\n"
        "- Reference specific files, routes, or components you actually read\n"
        "- If unsure something is a real problem, read the code to verify before filing"
    ),
    "refine_mode_section": (
        "## Refine Existing Tickets\n"
        "\n"
        "Your job: improve existing tickets related to your cluster. Do NOT create new tickets.\n"
        "\n"
        "Prioritize:\n"
        "1. Open tickets related to your cluster's focus areas\n"
        "2. Oldest open tickets without recent comments\n"
        "3. Tickets related to code you just read\n"
        "\n"
        "For each ticket you deep-read, ask:\n"
        "- Still true? Read the code NOW. Close with evidence if fixed.\n"
        "- Accurate? If it mischaracterizes the problem, rewrite the description with the correct analysis.\n"
        "- Complete? Add file paths, affected user flows, severity context to the description.\n"
        "- Scoped right? Split conflated tickets. Note broader patterns.\n"
        "- Priority right? Re-evaluate and update the severity label.\n"
        "\n"
        "### Editing tickets: description is the source of truth\n"
        "\n"
        "**When the ticket's core content needs changing** (problem statement, impact, severity, suggested direction), **edit the description directly**. The description must always be the canonical, accurate statement. Do NOT leave corrections as comments while the description stays wrong.\n"
        "\n"
        "**When synthesizing:** If the ticket has comments from the same user as you (prior skill runs), fold their corrections and additions into the description, then delete those comments. The description becomes one clean, authoritative ticket. Never touch comments from other users.\n"
        "\n"
        "Do not add comments to any ticket. All findings, cross-references, and dependency notes belong in the ticket description. If the target ticket is in your edit file, edit the description directly. If it is outside your edit file, write to your cross-cluster notes file.\n"
        "\n"
        "### Available operations\n"
        "\n"
        "Ticket bodies and comments are already in issues-open.json, no need to fetch them again.\n"
        "\n"
        "- Edit a ticket's description\n"
        "- Delete a redundant comment from a prior skill run (after synthesizing into description)\n"
        "- Close a resolved ticket (add a Resolution section to the description first, then close)\n"
        "\n"
        "Use whatever CLI tools or APIs are available for the detected ticket system.\n"
        "\n"
        "Do not rubber-stamp. If something feels off, dig in."
    ),
    "stay_in_lane": (
        "File about: UX, flows, missing states, confusing UI, visual inconsistency, navigation/state issues, destructive action safety, data presentation, accessibility, user-facing gaps\n"
        "NOT about: Code quality, security, performance internals, test coverage, dependency versions"
    ),
    "step35_heading_suffix": "",
    "step35_intro_paragraph": (
        "After all 4 sub-agents complete, check for cross-cluster findings:"
    ),
    "step35_pre_cross_cluster": "",
    "step4_pre_cleanup_phrase": "",
    "post_processor_section_examples": (
        "Problem, Impact, Suggested Direction, etc."
    ),
}


SKILLS = {
    "triage-architecture": ARCHITECTURE,
    "triage-bugs": BUGS,
    "triage-product": PRODUCT,
}
