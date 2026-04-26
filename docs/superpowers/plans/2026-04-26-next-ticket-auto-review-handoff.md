# next-ticket Auto-Review Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chain `code-review` into the end of `next-ticket` so the AFK return shows implementation status and review verdict together. Cross-platform (Claude Code, Codex, Gemini) with no harness-specific config.

**Architecture:** Two skill changes plus one new file. Extract the reviewer subagent's prompt template from `skills/code-review/SKILL.md` into a standalone `skills/code-review/reviewer-prompt.md` (single source of truth). Insert a new Step 9.5 in `skills/next-ticket/SKILL.md` between commit (Step 9) and announce (Step 10) that loads the same template, fills placeholders, dispatches the unspecialized reviewer subagent, and threads the findings into the Step 10 print.

**Tech Stack:** Markdown skill files (no runtime code). Python `unittest` for skill prose validation.

**Reference files:**
- Design spec: `docs/superpowers/specs/2026-04-26-next-ticket-auto-review-handoff-design.md`
- Existing skill: `skills/code-review/SKILL.md` (template extraction source)
- Existing skill: `skills/next-ticket/SKILL.md` (Step 9.5 insertion target)
- Existing test: `tests/test_code_review_inventory.py` (retarget assertions)
- Conventions: `AGENTS.md` (commit style, no em-dashes, no Co-Authored-By, branch lifecycle contract)
- User rules: `~/.claude/CLAUDE.md` (no em-dashes anywhere, branch naming, no TODO comments)

---

### Task 1: Extract Reviewer Prompt Template to Standalone File

This task moves the reviewer subagent's prompt template out of `code-review/SKILL.md` (where it currently lives as a fenced code block at the bottom) into its own file at `skills/code-review/reviewer-prompt.md`. After this task, `code-review/SKILL.md` references the new file in a single short paragraph; the file becomes the single source of truth that `next-ticket` will also load in Task 2.

**Files:**
- Create: `skills/code-review/reviewer-prompt.md`
- Modify: `skills/code-review/SKILL.md` (replace fenced template block with reference paragraph)
- Modify: `tests/test_code_review_inventory.py` (retarget assertions from SKILL.md to reviewer-prompt.md)

- [ ] **Step 1: Update the existing test to read from the new file path**

Replace the entire contents of `tests/test_code_review_inventory.py` with:

```python
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_REVIEW_SKILL = REPO_ROOT / "skills" / "code-review" / "SKILL.md"
REVIEWER_PROMPT = REPO_ROOT / "skills" / "code-review" / "reviewer-prompt.md"
README = REPO_ROOT / "README.md"


class CodeReviewInventoryTest(unittest.TestCase):
    def test_reviewer_prompt_defines_complete_changed_path_inventory(self):
        text = REVIEWER_PROMPT.read_text().lower()

        self.assertIn("{changed_path_inventory}", text)
        self.assertIn("changed path inventory", text)
        self.assertIn("git diff --name-status {base_sha}..{head_sha}", text)
        self.assertIn("git diff --cached --name-status", text)
        self.assertIn("git diff --name-status", text)
        self.assertIn("git ls-files --others --exclude-standard", text)

        for path_state in ["committed", "staged", "unstaged", "untracked"]:
            with self.subTest(path_state=path_state):
                self.assertIn(path_state, text)

        self.assertIn("account for every path", text)
        self.assertIn("read each untracked file", text)
        self.assertIn("high-risk", text)

    def test_template_body_not_duplicated_in_skill_md(self):
        skill_text = CODE_REVIEW_SKILL.read_text()
        self.assertNotIn(
            "You are reviewing code changes for production readiness.",
            skill_text,
            "Reviewer template body must live in reviewer-prompt.md only, not in SKILL.md",
        )

    def test_skill_md_references_reviewer_prompt_file(self):
        skill_text = CODE_REVIEW_SKILL.read_text()
        self.assertIn("skills/code-review/reviewer-prompt.md", skill_text)

    def test_readme_describes_untracked_files_in_review_scope(self):
        text = README.read_text().lower()

        self.assertIn("staged, unstaged, or untracked changes", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the updated test to confirm it fails**

Run: `python3 -m unittest tests.test_code_review_inventory -v`

Expected: three failures.
- `test_reviewer_prompt_defines_complete_changed_path_inventory`: `FileNotFoundError` for `skills/code-review/reviewer-prompt.md`.
- `test_template_body_not_duplicated_in_skill_md`: AssertionError (template body still present in SKILL.md).
- `test_skill_md_references_reviewer_prompt_file`: AssertionError (no reference paragraph yet).
- `test_readme_describes_untracked_files_in_review_scope` should still pass.

- [ ] **Step 3: Create `skills/code-review/reviewer-prompt.md` with the extracted template**

Open `skills/code-review/SKILL.md`. Locate the section heading `## Reviewer prompt template` and the fenced block that follows it (the outer fence uses four backticks `` ```` `` to allow inner triple-backtick code blocks). The fenced block currently spans from the line `You are reviewing code changes for production readiness.` through the line `**Reasoning:** Core implementation is solid with good architecture and tests. Important issues (help text, date validation) are easily fixed and don't affect core functionality.` followed by the closing ` ``` ` of the inner example.

Copy the entire body of that fenced block (everything between the two outer four-backtick fences, exclusive of the fences themselves) into a new file `skills/code-review/reviewer-prompt.md`. Do not modify any character of the body: every `{PLACEHOLDER}`, every git command, every checklist item, every example line stays byte-identical.

- [ ] **Step 4: Replace the fenced template block in `code-review/SKILL.md` with a reference paragraph**

In `skills/code-review/SKILL.md`, find the section starting with `## Reviewer prompt template` and ending at the closing four-backtick fence. Replace that entire section (heading plus introductory sentence plus fenced block) with:

```markdown
## Reviewer prompt template

Load `skills/code-review/reviewer-prompt.md`, substitute each `{PLACEHOLDER}` listed in the "How to Request" section above, and pass the resulting text as the prompt to the unspecialized reviewer subagent. The subagent sees only that text. The file is the single source of truth; do not embed the template inline anywhere else in this skill or in callers.
```

The "## Example" section that follows must remain untouched.

- [ ] **Step 5: Run the full test suite to confirm green**

Run: `python3 -m unittest discover tests -v`

Expected: All tests pass, including `test_reviewer_prompt_defines_complete_changed_path_inventory` now reading from the new file.

- [ ] **Step 6: Commit**

```bash
git add skills/code-review/reviewer-prompt.md skills/code-review/SKILL.md tests/test_code_review_inventory.py
git commit -m "refactor(code-review): extract reviewer prompt template to standalone file"
```

---

### Task 2: Add Step 9.5 Auto-Review and Update Step 10 Print in next-ticket

This task adds a new Step 9.5 between Step 9 (commit) and Step 10 (announce) in `skills/next-ticket/SKILL.md`. The new step builds the same SHA range and inventory variables that `code-review/SKILL.md` documents, fills the reviewer prompt placeholders, dispatches the unspecialized reviewer subagent, and threads the findings into Step 10's summary print.

**Files:**
- Create: `tests/test_next_ticket_auto_review.py`
- Modify: `skills/next-ticket/SKILL.md` (insert Step 9.5; update Step 10 print template)

- [ ] **Step 1: Write the failing test**

Create `tests/test_next_ticket_auto_review.py` with the following content:

```python
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NEXT_TICKET_SKILL = REPO_ROOT / "skills" / "next-ticket" / "SKILL.md"


class NextTicketAutoReviewTest(unittest.TestCase):
    def test_step_9_5_exists_and_references_reviewer_prompt(self):
        text = NEXT_TICKET_SKILL.read_text()
        self.assertIn("Step 9.5", text)
        self.assertIn("skills/code-review/reviewer-prompt.md", text)

    def test_step_9_5_builds_shared_inventory_variables(self):
        text = NEXT_TICKET_SKILL.read_text()
        for var in ["BASE_SHA", "HEAD_SHA", "CHANGED_PATH_INVENTORY", "HIGH_RISK_PATHS"]:
            with self.subTest(var=var):
                self.assertIn(var, text)
        self.assertIn('git merge-base HEAD "origin/$BASE_BRANCH"', text)
        self.assertIn("git ls-files --others --exclude-standard", text)

    def test_step_9_5_lists_reviewer_placeholders(self):
        text = NEXT_TICKET_SKILL.read_text()
        for placeholder in [
            "WHAT_WAS_IMPLEMENTED",
            "PLAN_OR_REQUIREMENTS",
            "DESCRIPTION",
            "HAS_UNCOMMITTED",
        ]:
            with self.subTest(placeholder=placeholder):
                self.assertIn(placeholder, text)

    def test_step_10_summary_includes_review_block(self):
        text = NEXT_TICKET_SKILL.read_text()
        self.assertIn("Review: Critical", text)
        self.assertIn("Important", text)
        self.assertIn("Minor", text)
        self.assertIn("Verdict:", text)
        self.assertIn("Top issues:", text)

    def test_step_9_5_documents_failure_mode(self):
        text = NEXT_TICKET_SKILL.read_text()
        self.assertIn("Review: skipped", text)
        lower = text.lower()
        self.assertIn("do not retry", lower)
        self.assertIn("do not block", lower)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new test to confirm it fails**

Run: `python3 -m unittest tests.test_next_ticket_auto_review -v`

Expected: All five test methods fail; `next-ticket/SKILL.md` does not yet contain Step 9.5 or the new Step 10 fields.

- [ ] **Step 3: Insert Step 9.5 into `skills/next-ticket/SKILL.md`**

Open `skills/next-ticket/SKILL.md`. Find the existing `## Step 10: Wait for Review` heading. Immediately before that heading, insert the following new section:

````markdown
## Step 9.5: Run Code Review

Before announcing completion, dispatch the code-reviewer subagent against the work just committed. The reviewer's findings are folded into the Step 10 summary so the user gets implementation status and review verdict in one shot.

1. **Resolve the default branch and build review variables.** Re-resolve `BASE_BRANCH` per the AGENTS.md branch lifecycle contract; shell state does not persist between Bash invocations.

```bash
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
if [ -z "$BASE_BRANCH" ]; then
  git rev-parse --verify main >/dev/null 2>&1 && BASE_BRANCH=main || BASE_BRANCH=master
fi
BASE_SHA=$(git merge-base HEAD "origin/$BASE_BRANCH" 2>/dev/null || git merge-base HEAD "$BASE_BRANCH")
HEAD_SHA=$(git rev-parse HEAD)
CHANGED_PATH_INVENTORY=$(
  {
    git diff --name-status "$BASE_SHA..$HEAD_SHA" | sed 's/^/committed\t/'
    git diff --cached --name-status | sed 's/^/staged\t/'
    git diff --name-status | sed 's/^/unstaged\t/'
    git ls-files --others --exclude-standard | sed 's/^/untracked\t/'
  } | sort -u
)
HIGH_RISK_PATHS=$(
  printf '%s\n' "$CHANGED_PATH_INVENTORY" |
    grep -Ei '(^|/)(\.env|\.npmrc|\.pypirc|id_rsa|id_dsa|credentials|secrets?|token|key)(\.|/|$)|\.(pem|p12|pfx|key|crt|sqlite|db|dump|zip|tar|tgz|gz)$|(^|/)\.github/workflows/' || true
)
```

`HAS_UNCOMMITTED` is `no`. Step 9 just committed; the working tree is clean.

2. **Build the narrative placeholders:**
   - `WHAT_WAS_IMPLEMENTED` and `DESCRIPTION`: a one to two sentence summary of the change you just implemented.
   - `PLAN_OR_REQUIREMENTS`: the ticket title plus the ticket body, verbatim, as fetched in Step 2.

3. **Load and dispatch.** Read `skills/code-review/reviewer-prompt.md`, substitute every `{PLACEHOLDER}` with the values built above, and pass the resulting text as the prompt to the unspecialized reviewer subagent via the Task tool / equivalent. Do not name a specialized reviewer agent from another plugin; the unspecialized subagent takes the template as its full instructions, which is what the template is written for.

4. **Capture findings.** Parse the reviewer's structured output for severity counts (Critical, Important, Minor), the Assessment verdict line (Yes / No / With fixes), and the top issues in severity order with their file:line references. Cap the captured issues at five.

5. **Failure mode.** If the dispatch errors, the capability is unavailable, the reviewer-prompt file cannot be read, or any other failure prevents review, capture `Review: skipped (<reason>)` and proceed to Step 10. Do not retry. Do not block Step 10. The user can run `/code-review` manually if they care.

````

- [ ] **Step 4: Update Step 10's print template**

In `skills/next-ticket/SKILL.md`, replace the entire body of `## Step 10: Wait for Review` with:

````markdown
## Step 10: Wait for Review

Print a brief summary that folds in the Step 9.5 review findings:

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

To test in the UI: <one sentence describing the specific UI action that exercises this change>
```

If the reviewer found zero issues, replace the two Review lines with `Review: clean | Verdict: Yes`. If review failed or was skipped per Step 9.5's failure mode, replace them with `Review: skipped (<reason>)`. The `Top issues:` block is omitted when there are no captured issues.

The UI testing tip must be **specific and actionable**, not "test the feature" but "log in, wait 15 minutes for the token to expire, then click any nav link, it should refresh silently instead of kicking you to login."
````

- [ ] **Step 5: Run the targeted test to confirm green**

Run: `python3 -m unittest tests.test_next_ticket_auto_review -v`

Expected: All five test methods pass.

- [ ] **Step 6: Run the full test suite to confirm no regressions**

Run: `python3 -m unittest discover tests -v`

Expected: Every test in `tests/` passes, including `test_branch_lifecycle_contract`, `test_capability_vocabulary`, `test_code_review_inventory`, `test_conventional_commit_templates`, `test_untrusted_content_boundary`, and the new `test_next_ticket_auto_review`.

- [ ] **Step 7: Commit**

```bash
git add skills/next-ticket/SKILL.md tests/test_next_ticket_auto_review.py
git commit -m "feat(next-ticket): auto-invoke code-review and surface findings in done summary"
```

---

### Self-review checklist (run after Task 2)

- [ ] **Spec coverage:** Each section of `docs/superpowers/specs/2026-04-26-next-ticket-auto-review-handoff-design.md` maps to a task above:
  - "Architecture: New: reviewer-prompt.md" → Task 1
  - "Architecture: Edit: code-review/SKILL.md" → Task 1
  - "Architecture: Edit: next-ticket/SKILL.md" → Task 2
  - "Step 9.5 placeholder contents" → Task 2 Step 3
  - "Final summary format" → Task 2 Step 4
  - "Verification handling" → no plan task; the design explicitly chose no coordination, so no SKILL change is needed
  - "Failure mode" → Task 2 Step 3 (sub-step 5) and asserted by the new test
  - "Cross-platform contract" → satisfied implicitly by editing the canonical SKILL.md only and using a sibling-file load
  - "Out of scope" items → not implemented, by design
- [ ] **Placeholder scan:** No "TBD", "TODO", "implement later", "similar to Task N", or vague "handle edge cases" steps appear in this plan.
- [ ] **Type consistency:** Variable names (`BASE_SHA`, `HEAD_SHA`, `CHANGED_PATH_INVENTORY`, `HIGH_RISK_PATHS`, `HAS_UNCOMMITTED`) match the names used in `skills/code-review/SKILL.md`. Placeholder names (`WHAT_WAS_IMPLEMENTED`, `PLAN_OR_REQUIREMENTS`, `DESCRIPTION`) match the placeholder list documented in `code-review/SKILL.md`'s "How to Request" section. The new file path `skills/code-review/reviewer-prompt.md` is identical in every reference (Task 1, Task 2, both tests, the Step 9.5 instruction).
- [ ] **Branch and commit conventions:** Both commits use Conventional Commits scope-prefixed types (`refactor(code-review):`, `feat(next-ticket):`) per AGENTS.md and release-please policy. No `Co-Authored-By` trailers. No em-dashes in commit messages or skill prose.
