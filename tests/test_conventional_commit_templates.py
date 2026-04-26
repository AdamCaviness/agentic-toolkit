"""Conventional Commits validator for workflow skill templates.

The repo's release pipeline (release-please, configured in
``release-please-config.json`` and documented in ``AGENTS.md`` under
"Commits and releases") only bumps versions on commits whose subjects start
with ``feat:`` or ``fix:`` and silently ignores other types. Workflow
skills (``pr``, ``ship``, ``next-ticket``, ``update-deps``,
``convert-worktree``) are the surfaces an AFK agent uses to produce
commits, so any non-Conventional-Commits subject template they emit will
slip past release-please without bumping the version.

This validator scans every ``skills/*/SKILL.md`` for commit-subject
templates in the two shapes the skills actually use:

1. Quoted subjects in shell snippets, e.g. ``git commit -m "..."``.
2. First lines of fenced code blocks whose first line looks like a
   Conventional-Commits-shaped subject (a single short line followed by a
   blank line and a body), as ``update-deps`` uses for its per-dep major
   bump example and its safe-update batch commit.
3. Backtick-wrapped subjects in prose where the sentence cues the string
   as a commit subject ("commit ... message" within a small window).

Acceptable types: ``feat``, ``fix``, ``chore``, ``refactor``, ``docs``,
``style``, ``test``, ``perf``, ``build``, ``ci``, ``revert``. Optional
``(scope)`` and optional ``!`` for breaking changes are allowed.
"""

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"


CONVENTIONAL_TYPES = (
    "feat",
    "fix",
    "chore",
    "refactor",
    "docs",
    "style",
    "test",
    "perf",
    "build",
    "ci",
    "revert",
)

CONVENTIONAL_PREFIX_RE = re.compile(
    r"^(" + "|".join(CONVENTIONAL_TYPES) + r")(\([^)]+\))?!?:\s"
)


def is_conventional(subject):
    """Return True iff ``subject`` starts with a Conventional Commits type."""
    return bool(CONVENTIONAL_PREFIX_RE.match(subject))


def strip_frontmatter(text):
    match = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
    return text[match.end():] if match else text


def public_skill_files():
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


# Shape 1: ``git commit -m "<subject>"``. The subject is everything inside
# the matched quotes on the same line.
GIT_COMMIT_DASH_M_RE = re.compile(
    r"""git\s+commit\s+(?:[^"'\n]*\s+)?-m\s+(?P<q>["'])(?P<subject>.+?)(?P=q)"""
)


# Shape 2: a fenced code block that opens with a single short line that
# looks like a commit subject (no leading shell prompt, no backtick, no
# JSON/YAML markers), followed by an empty line and a body. We only fire
# on blocks whose first non-blank line "looks like" a commit subject by
# being short, on its own line, and not a code/markup token. The
# disambiguation criteria below are deliberately strict to avoid false
# positives on shell or JSON snippets.
FENCED_BLOCK_RE = re.compile(
    r"^```(?P<lang>[^\n]*)\n(?P<body>.*?)^```",
    re.DOTALL | re.MULTILINE,
)

# Languages whose blocks are never commit-subject templates.
NON_COMMIT_BLOCK_LANGS = {
    "bash",
    "sh",
    "shell",
    "zsh",
    "console",
    "json",
    "jsonc",
    "yaml",
    "yml",
    "toml",
    "ini",
    "python",
    "py",
    "javascript",
    "js",
    "typescript",
    "ts",
    "tsx",
    "go",
    "rust",
    "rs",
    "java",
    "kotlin",
    "ruby",
    "rb",
    "php",
    "html",
    "css",
    "diff",
    "patch",
    "dockerfile",
    "makefile",
    "xml",
    "sql",
}


def looks_like_commit_subject_block(body):
    """Heuristic: is this fenced block a commit-message template?

    A commit-message template has:
    - A first line under 100 chars that is NOT a shell prompt, JSON/YAML
      structural token, or summary header,
    - Followed by an empty line and at least one further content line OR is
      the entire block (single-line subject template).

    We restrict positives to blocks whose first line is plausibly a commit
    subject and whose body content reads as a commit body (bullets, blank
    lines, plain prose) rather than a CLI session or summary report.
    """
    lines = body.splitlines()
    if not lines:
        return False
    first = lines[0].rstrip()
    if not first:
        return False
    if len(first) > 100:
        return False
    # Reject obvious non-subject first lines.
    rejects = (
        first.startswith("$"),
        first.startswith("#"),
        first.startswith("//"),
        first.startswith("/*"),
        first.startswith("{"),
        first.startswith("["),
        first.startswith("- "),
        first.startswith("* "),
        first.startswith("> "),
        first.startswith("|"),
        first.endswith(":") and " " not in first.split(":")[0],
        first.endswith("."),
    )
    if any(rejects):
        return False
    # The first line must contain at least one space (commit subjects are
    # multi-word) and must not look like a key/value or assignment.
    if "=" in first and ":" not in first:
        return False
    # Blocks that are entire summary reports start with a sentence ending
    # in a period; we already rejected period endings above, but also
    # screen for "<word> <word> ..." lines that read as report headers.
    # A commit subject either has a Conventional prefix OR is a short
    # imperative phrase. To keep the heuristic narrow, only treat the
    # block as a commit subject when:
    #   (a) the first line itself matches the Conventional regex, OR
    #   (b) the block body contains a "Migration guide:" /
    #       "Breaking changes" cue or a leading bullet list immediately
    #       under the subject (the shape of the templates this validator
    #       guards).
    if is_conventional(first):
        return True
    has_blank_then_bullet = (
        len(lines) >= 3
        and lines[1].strip() == ""
        and (lines[2].lstrip().startswith("- ") or lines[2].lstrip().startswith("* "))
    )
    has_known_cue = any(
        cue in body
        for cue in ("Migration guide:", "Breaking changes addressed:")
    )
    return has_blank_then_bullet or has_known_cue


# Shape 3: prose mention of a commit subject in backticks or quotes,
# within a sentence that names "commit" and "message". Window is one
# sentence (no period in between).
PROSE_COMMIT_REF_RE = re.compile(
    r"commit[^.\n`\"]{0,80}?(?:message|subject)[^.\n`\"]{0,40}?"
    r"[`\"](?P<subject>[^`\"\n]{3,120})[`\"]",
    re.IGNORECASE,
)


def commit_subject_candidates(body):
    """Yield (kind, subject, context) for every commit-subject candidate."""
    # Shape 1: git commit -m "..."
    for match in GIT_COMMIT_DASH_M_RE.finditer(body):
        yield ("git-commit-dash-m", match.group("subject"), match.group(0))

    # Shape 2: fenced commit-template blocks
    for match in FENCED_BLOCK_RE.finditer(body):
        lang = match.group("lang").strip().lower()
        if lang in NON_COMMIT_BLOCK_LANGS:
            continue
        block_body = match.group("body")
        if not looks_like_commit_subject_block(block_body):
            continue
        first_line = block_body.splitlines()[0].rstrip()
        yield ("fenced-block-subject", first_line, match.group(0))

    # Shape 3: prose backtick/quoted commit refs
    for match in PROSE_COMMIT_REF_RE.finditer(body):
        yield ("prose-quoted-commit", match.group("subject"), match.group(0))


class ConventionalCommitTemplatesTest(unittest.TestCase):
    def test_skill_commit_subjects_are_conventional(self):
        any_candidates_found = False
        for skill_path in public_skill_files():
            skill_name = skill_path.parent.name
            body = strip_frontmatter(skill_path.read_text())
            for kind, subject, context in commit_subject_candidates(body):
                any_candidates_found = True
                with self.subTest(skill=skill_name, kind=kind, subject=subject):
                    self.assertTrue(
                        is_conventional(subject),
                        f"{skill_name}: {kind} subject is not a Conventional "
                        f"Commits prefix.\n"
                        f"  Subject: {subject!r}\n"
                        f"  Context: {context[:200]}\n"
                        f"  Allowed types: {', '.join(CONVENTIONAL_TYPES)}\n"
                        f"  Note: only feat: and fix: trigger a release-"
                        f"please bump; other types are valid Conventional "
                        f"Commits but produce no release.",
                    )
        # Sanity check: the validator should be exercising at least one
        # template in the current repo. If this trips, the candidate
        # detection has regressed.
        self.assertTrue(
            any_candidates_found,
            "Validator found zero commit-subject candidates across all "
            "skills. Detection has regressed.",
        )

    def test_regex_self_test(self):
        # Conventional subjects must pass.
        for subject in (
            "feat: add x",
            "fix: correct y",
            "chore(deps): update minor/patch dependencies",
            "fix(deps): update express 4.18.2 to 5.1.0 (CVE-2024-XXXXX)",
            "style: auto-format and lint fixes",
            "chore(worktree): preserve tracked changes during conversion",
            "refactor!: rename public API",
            "feat(api)!: drop legacy endpoint",
        ):
            with self.subTest(subject=subject):
                self.assertTrue(is_conventional(subject))

        # Non-Conventional subjects must fail. Each of these is a literal
        # template that previously appeared in a workflow skill on main.
        for subject in (
            "Auto-format and lint fixes",
            "Update minor/patch dependencies",
            "wip: tracked changes from worktree conversion",
            "Update express 4.18.2 -> 5.1.0 (CVE-2024-XXXXX)",
            "WIP: anything",
            "fixed a bug",
        ):
            with self.subTest(subject=subject):
                self.assertFalse(is_conventional(subject))

    def test_candidate_detection_self_test(self):
        # The validator must catch the previously-shipped non-Conventional
        # templates from main when they are reintroduced. This guards the
        # detector itself from silently going blind.
        regression_sample = (
            'Run `git commit -m "Auto-format and lint fixes"` in step 5.\n'
            "\n"
            "```\n"
            "Update minor/patch dependencies\n"
            "\n"
            "- axios 1.6.0 -> 1.7.2\n"
            "```\n"
            "\n"
            "Then commit with message `wip: tracked changes from worktree "
            "conversion`.\n"
            "\n"
            "```\n"
            "Update express 4.18.2 -> 5.1.0 (CVE-2024-XXXXX)\n"
            "\n"
            "Breaking changes addressed:\n"
            "- foo\n"
            "\n"
            "Migration guide: https://example.com\n"
            "```\n"
        )
        candidates = list(commit_subject_candidates(regression_sample))
        subjects = [subject for _, subject, _ in candidates]
        self.assertIn("Auto-format and lint fixes", subjects)
        self.assertIn("Update minor/patch dependencies", subjects)
        self.assertIn("wip: tracked changes from worktree conversion", subjects)
        self.assertIn("Update express 4.18.2 -> 5.1.0 (CVE-2024-XXXXX)", subjects)
        # And every one of those must fail the Conventional check.
        for subject in subjects:
            with self.subTest(subject=subject):
                self.assertFalse(is_conventional(subject))


if __name__ == "__main__":
    unittest.main()
