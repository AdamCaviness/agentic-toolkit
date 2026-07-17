"""Command line interface for the Agentic Atlas engine.

    agentic-atlas validate <rubric>
    agentic-atlas profile <target> [--rubric DIR] [--answers FILE] [--format text|md|json|html]
    agentic-atlas questions <target> [--rubric DIR]

The engine is deterministic and needs no API key. A bare ``profile`` run resolves the
measured indicators only. The classified indicators are unlocked by supplying answers
(``--answers``) produced outside the engine, the intended producer being the
agentic-toolkit skill, whose host agent reads the repo and answers each question from
``questions``. The engine validates those answers, it never calls a model.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import docs
from .classify import classified_questions
from .evidence import Target
from .profiler import profile_target
from .report import render_html, render_markdown, render_text
from .spec import load_rubric

_DEFAULT_RUBRIC = Path(__file__).resolve().parent.parent / "rubric" / "v1"


def _cmd_validate(args: argparse.Namespace) -> int:
    load_rubric(args.rubric, validate=True)
    print(f"ok: {args.rubric} is a valid rubric")
    return 0


def _cmd_docs(args: argparse.Namespace) -> int:
    changed = docs.sync(args.rubric, check=args.check)
    if args.check:
        if changed:
            print("stale axis READMEs (run `make docs`): " + ", ".join(changed))
            return 1
        print("ok: all axis READMEs are in sync")
        return 0
    print(f"updated: {', '.join(changed) if changed else 'none'}")
    return 0


def _cmd_questions(args: argparse.Namespace) -> int:
    rubric = load_rubric(args.rubric, validate=True)
    target = Target.from_path(args.target)
    print(
        json.dumps(
            {
                "rubric_version": rubric.rubric_version,
                "target": str(target.root),
                "instructions": (
                    "Answer each question from the target repository only. Return an "
                    'object keyed by indicator id: {"answer": <one allowed value>, '
                    '"evidence": <a quote copied verbatim from the target>}. Feed the '
                    "result back with `agentic-atlas profile --answers`."
                ),
                "questions": classified_questions(rubric),
            },
            indent=2,
        )
    )
    return 0


def _load_answers(path: str) -> tuple[dict, str]:
    """Read a supplied-answers file (or stdin, via '-'), returning (answers, source)."""
    try:
        # "-" reads stdin, so the skill can pipe answers straight in without a temp file.
        raw = sys.stdin.read() if path == "-" else Path(path).read_text()
        data = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot read answers file {path!r}: {exc}")
    answers = data.get("answers")
    if not isinstance(answers, dict):
        raise SystemExit(f"answers file {path!r} must have an object under key 'answers'")
    return answers, str(data.get("source") or "supplied")


def _cmd_profile(args: argparse.Namespace) -> int:
    rubric = load_rubric(args.rubric, validate=True)
    target = Target.from_path(args.target)
    answers, source = _load_answers(args.answers) if args.answers else (None, "supplied")
    profile = profile_target(rubric, target, answers=answers, answers_source=source)

    if args.format == "json":
        print(json.dumps(profile.to_dict(), indent=2))
    elif args.format == "md":
        print(render_markdown(profile))
    elif args.format == "html":
        print(render_html(profile))
    else:
        # Color only for an interactive terminal, and never when NO_COLOR is set
        # (https://no-color.org). Piped or redirected output stays plain ASCII.
        color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
        print(render_text(profile, color=color))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agentic-atlas", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="validate a rubric against the schema")
    v.add_argument("rubric", nargs="?", default=str(_DEFAULT_RUBRIC))
    v.set_defaults(func=_cmd_validate)

    d = sub.add_parser("docs", help="regenerate axis README scoring blocks from axis.yaml")
    d.add_argument("rubric", nargs="?", default=str(_DEFAULT_RUBRIC))
    d.add_argument("--check", action="store_true", help="report drift instead of writing")
    d.set_defaults(func=_cmd_docs)

    pr = sub.add_parser("profile", help="profile a target directory")
    pr.add_argument("target", help="path to the target approach/framework directory")
    pr.add_argument("--rubric", default=str(_DEFAULT_RUBRIC))
    pr.add_argument(
        "--answers",
        help="JSON file of classified answers (from the agentic-toolkit skill) to "
        "validate and score, or '-' to read them from stdin; without it the profile "
        "is measured-only",
    )
    pr.add_argument("--format", choices=["text", "md", "json", "html"], default="text")
    pr.set_defaults(func=_cmd_profile)

    q = sub.add_parser(
        "questions", help="emit the classified questions to answer for a target (JSON)"
    )
    q.add_argument("target", help="path to the target approach/framework directory")
    q.add_argument("--rubric", default=str(_DEFAULT_RUBRIC))
    q.set_defaults(func=_cmd_questions)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
