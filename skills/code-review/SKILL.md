---
name: code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
---

# Code Review

Dispatch a code-reviewer subagent to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation, never your session's history. This keeps the reviewer focused on the work product, not your thought process, and preserves your own context for continued work.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in multi-task development
- After completing a major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing a complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Dispatch the code-reviewer subagent:**

Use the Task tool with `subagent_type: "general-purpose"` (or the code-reviewer agent type if your harness has one registered), passing the filled template at `code-reviewer.md` as the prompt. The reviewer sees only the template, never your session history.

**Placeholders:**
- `{WHAT_WAS_IMPLEMENTED}`, what you just built
- `{PLAN_OR_REQUIREMENTS}`, what it should do
- `{BASE_SHA}`, starting commit
- `{HEAD_SHA}`, ending commit
- `{DESCRIPTION}`, brief summary

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if the reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch code-reviewer subagent]
  WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Multi-Task Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to the next task

**Executing Plans:**
- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If the reviewer is wrong:**
- Push back with technical reasoning
- Show code or tests that prove it works
- Request clarification

See template at: code-review/code-reviewer.md
