"""Generate the scoring block of each axis README from its axis.yaml.

The human rationale in a README is hand written, above a delimited block that this
module regenerates from the axis definition. That guarantees the documented weights
and formula always match what the engine actually computes. ``check=True`` reports
drift instead of writing, for use as a CI gate.
"""

from __future__ import annotations

from pathlib import Path

from .models import Axis, IndicatorKind
from .spec import _resolve_dir, load_rubric

BEGIN = "<!-- BEGIN GENERATED: do not edit below, run `make docs` -->"
END = "<!-- END GENERATED -->"

_RATIONALE_PLACEHOLDER = (
    "## Why this axis exists\n\n"
    "_Rationale not yet written. Explain what this axis measures, what each pole "
    "means, and why the indicators and weights are set the way they are._\n"
)


def _maps_to(axis_indicator) -> str:
    if axis_indicator.kind is IndicatorKind.CLASSIFIED:
        return ", ".join(f"{k} {v:+g}" for k, v in axis_indicator.answers.items())
    signal = axis_indicator.signal or {}
    if signal.get("type") == "vocabulary":
        return f"{len(signal['terms'])} terms, banded by count"
    if signal.get("type") == "path_presence":
        return f"present {signal['present']:+g}, absent {signal['absent']:+g}"
    if signal.get("type") == "git_stats":
        return f"git {signal['metric']}, banded by count"
    if signal.get("type") == "github_api":
        return f"{signal['metric']} via GitHub API, banded by count"
    return ""


def generate_block(axis: Axis) -> str:
    lines = [
        f"### Scoring ({axis.title})",
        "",
        f"Poles: `{axis.poles.negative}` (negative) to `{axis.poles.positive}` (positive). "
        f"Scale ±{axis.scale:g}.",
        "",
        f"Position is a weighted mean of {len(axis.indicators)} indicator measurements:",
        "",
        "```",
        f"axis_position = {axis.scale:g} * sum(weight * measurement) / sum(weight)",
        "```",
        "",
        "| id | question | kind | weight | maps to |",
        "|---|---|---|---|---|",
    ]
    for ind in axis.indicators:
        q = ind.question.replace("|", "\\|")
        lines.append(f"| {ind.id} | {q} | {ind.kind.value} | {ind.weight:g} | {_maps_to(ind)} |")
    return "\n".join(lines)


def _compose(existing: str | None, axis: Axis) -> str:
    block = f"{BEGIN}\n{generate_block(axis)}\n{END}\n"
    if existing and BEGIN in existing and END in existing:
        prefix = existing[: existing.index(BEGIN)]
        suffix = existing[existing.index(END) + len(END) :].lstrip("\n")
        suffix = f"\n{suffix}" if suffix.strip() else ""
        return f"{prefix.rstrip()}\n\n{block}{suffix}"
    if existing and existing.strip():
        return f"{existing.rstrip()}\n\n{block}"
    return f"# {axis.title}\n\n{_RATIONALE_PLACEHOLDER}\n{block}"


def sync(path: str | Path, *, check: bool = False) -> list[str]:
    """Regenerate (or, with check=True, verify) every axis README.

    Returns the list of axis ids whose README changed (or would change).
    """
    rubric_dir = _resolve_dir(path)
    rubric = load_rubric(rubric_dir)
    changed: list[str] = []
    for axis in rubric.axes:
        readme = rubric_dir / "axes" / axis.id / "README.md"
        current = readme.read_text() if readme.is_file() else None
        desired = _compose(current, axis)
        if current == desired:
            continue
        changed.append(axis.id)
        if not check:
            readme.write_text(desired)
    return changed
