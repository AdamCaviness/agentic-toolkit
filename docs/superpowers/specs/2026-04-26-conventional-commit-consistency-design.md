# Conventional Commit Consistency Across Workflow Skills

## Gap

The repo's release pipeline uses release-please, which only bumps versions on Conventional Commits prefixed `feat:` (minor) or `fix:` (patch). Other types are silently ignored for bump purposes (`AGENTS.md`, "Commits and releases"). Several workflow skills today produce or instruct subjects that are not Conventional Commits at all, so any commits an AFK agent emits through `pr`, `ship`, `next-ticket`, `update-deps`, or `convert-worktree` may slip past release-please without a release. The user reviewing the resulting PR has no easy signal that the bump intent was lost.

The non-conformant surfaces are:

- Hardcoded subject templates: `Auto-format and lint fixes`, `Update minor/patch dependencies`, `wip: tracked changes from worktree conversion`, and the `Update express ...` example in `update-deps`.
- Prose in `pr`, `ship`, and `next-ticket` that tells the agent to write "a descriptive message derived from the diff" without naming Conventional Commits as the format.

## Type-Selection Rule

For prose-derived commits the agent must classify the work and pick from the Conventional Commits type set: `feat` for new functionality, `fix` for bugfixes, `refactor` for restructuring without behavior change, `docs` for documentation-only, `style` for whitespace and formatting, `test` for tests, `perf` for performance, `build` for build-system changes, `ci` for CI configuration, `revert` for reverts, `chore` for everything else.

For `next-ticket` the branch category resolved at Step 5 (`fix/`, `feat/`, `refactor/`, `docs/`, `chore/`) is the natural source of the commit type, so the Step 9 commit subject reuses that mapping directly.

For the hardcoded templates the type is fixed at template-write time:

- Auto-format and lint commits become `style: auto-format and lint fixes`. Conventional Commits reserves `style:` for whitespace and formatting changes that do not affect meaning, which is exactly this case.
- The batched safe-dep update commit becomes `chore(deps): update minor/patch dependencies`. Routine non-CVE bumps are not user-visible behavior changes.
- The worktree-conversion preservation commit becomes `chore(worktree): preserve tracked changes during conversion`. The original `wip:` prefix is not a Conventional Commits type; the work captured here is mechanical state preservation, not in-progress feature work.
- The per-dep major-bump example becomes `fix(deps): update express 4.18.2 to 5.1.0 (CVE-2024-XXXXX)` for the CVE example. Routine non-CVE major bumps in the same flow use `chore(deps):`. CVE patches are functional fixes, hence `fix:`. The same pattern applies generally: CVE-driven dep bumps are `fix(deps):`, routine ones are `chore(deps):`.

## Validator Strategy (`tests/test_conventional_commit_templates.py`)

The validator scans every `skills/*/SKILL.md`, walks fenced code blocks, and inspects only blocks whose first non-blank line looks like a commit subject (a single short line not matching shell, code, or JSON syntax). It also picks up backticks-wrapped phrases that read as a commit subject in prose (e.g., `commit with message "Auto-format and lint fixes"`).

Acceptable prefixes are `feat`, `fix`, `chore`, `refactor`, `docs`, `style`, `test`, `perf`, `build`, `ci`, `revert`. Optional `(scope)` and optional `!` for breaking changes are allowed. Regex: `^(feat|fix|chore|refactor|docs|style|test|perf|build|ci|revert)(\([^)]+\))?!?:\s`.

To avoid false positives on prose paragraphs that happen to live in fenced blocks (e.g., shell snippets, JSON examples), the validator targets two narrow shapes:

1. Fenced blocks whose body is a single short line ending in no terminal punctuation, or whose first line matches a Conventional Commits-shaped subject (i.e., looks like a commit subject template). These are the explicit subject templates such as `Auto-format and lint fixes`.
2. Prose mentions of literal commit messages quoted in backticks or double-quotes, where the surrounding sentence cues that this string is a commit subject (presence of "commit ... message" or "commit with message" within a small window).

Anything that matches either shape and starts with a non-Conventional prefix fails.

A self-test fixture exercises the regex directly so the validator is verified independently of the live skill content.

## Deviations from Recommended Replacements

None for the hardcoded templates; recommended replacements are adopted as written. For the prose updates (`pr` step 2, `ship` step 2, `next-ticket` step 9), the instruction adds an explicit "Conventional Commits" requirement plus the type-selection rule. `next-ticket` step 9 ties the type to the Step 5 branch category so the agent does not have to redecide.
