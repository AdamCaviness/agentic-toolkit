"""Render a Profile (or several) to a human-readable report.

Renders a signed bar per axis so the sign and magnitude read at a glance. There is
no total row, by design, a profile is a position not a grade.

The text renderer can emit ANSI color (opt-in via ``color=True``, decided by the
CLI from TTY detection and ``NO_COLOR``). The two poles get distinct, non-judgmental
hues, neither pole is "good", so color must never imply valence. Coverage is the one
quality signal where a green/yellow/red gradient is honest: higher means the axis
position rests on more of its intended evidence.
"""

from __future__ import annotations

from .models import AxisResult, IndicatorKind, Profile

_BAR_HALF = 20  # characters on each side of the neutral center

# Below this fraction of resolved weight, an axis has too little evidence to plot a
# position. It reports "needs interpretation" instead of a bar so a sliver of measured
# evidence is never dressed up as a confident, clamped verdict. Tunable, presentation
# only: the score and coverage are still emitted verbatim in the JSON.
_COVERAGE_FLOOR = 0.5

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_NEG = "\033[36m"  # cyan, the left/negative pole
_POS = "\033[35m"  # magenta, the right/positive pole
_COV_GOOD = "\033[32m"  # green
_COV_MID = "\033[33m"  # yellow
_COV_LOW = "\033[31m"  # red


def _paint(text: str, *codes: str, on: bool) -> str:
    if not on or not text:
        return text
    return "".join(codes) + text + _RESET


def _coverage_code(coverage: float) -> str:
    if coverage >= 0.67:
        return _COV_GOOD
    if coverage >= 0.34:
        return _COV_MID
    return _COV_LOW


def _bar(score: float | None, scale: float, color: bool = False) -> str:
    if score is None:
        return " " * _BAR_HALF + _paint("|", _DIM, on=color) + " " * _BAR_HALF + "  (no data)"
    frac = max(-1.0, min(1.0, score / scale))
    fill = round(abs(frac) * _BAR_HALF)
    if frac < 0:
        left = " " * (_BAR_HALF - fill) + _paint("#" * fill, _NEG, on=color)
        right = " " * _BAR_HALF
    else:
        left = " " * _BAR_HALF
        right = _paint("#" * fill, _POS, on=color) + " " * (_BAR_HALF - fill)
    return f"{left}{_paint('|', _DIM, on=color)}{right}"


_SKILL_HINT = (
    "of {total} axes need interpretation for lack of classified answers. "
    "Run the /agentic-atlas skill in agentic-toolkit (inside Claude Code) to answer them "
    "with your coding agent, no API key, and get a complete profile."
)


def _needs_interpretation(ax: AxisResult) -> bool:
    return ax.score is None or ax.coverage < _COVERAGE_FLOOR


def _skill_hint(profile: Profile) -> str | None:
    """The opinionated first-run pointer: how to resolve the unplottable axes.

    Shown only when axes are unplottable *because classified answers are missing*, which
    is the bare deterministic run. Once the skill supplies answers there is nothing to
    nudge toward, so the hint disappears.
    """
    pending = [ax for ax in profile.axes if _needs_interpretation(ax)]
    has_unanswered_classified = any(
        ir.kind is IndicatorKind.CLASSIFIED and not ir.resolved
        for ax in pending
        for ir in ax.indicators
    )
    if not pending or not has_unanswered_classified:
        return None
    return f"{len(pending)} " + _SKILL_HINT.format(total=len(profile.axes))


def _kind_counts(ax: AxisResult) -> tuple[int, int, int, int]:
    """Resolved/total indicator counts split by kind: (m_resolved, m_total, c_resolved, c_total)."""
    m_total = m_res = c_total = c_res = 0
    for ir in ax.indicators:
        if ir.kind is IndicatorKind.MEASURED:
            m_total += 1
            m_res += ir.resolved
        else:
            c_total += 1
            c_res += ir.resolved
    return m_res, m_total, c_res, c_total


def _coverage_detail(ax: AxisResult, color: bool = False) -> str:
    # Split coverage by kind so a keyless run reads as "you ran the measured half," not
    # a broken percentage. Classified indicators need answers from the toolkit skill.
    m_res, m_total, c_res, c_total = _kind_counts(ax)
    text = f"measured {m_res}/{m_total} · classified {c_res}/{c_total}"
    return _paint(text, _coverage_code(ax.coverage), on=color)


def _axis_lines(ax: AxisResult, color: bool = False) -> list[str]:
    detail = _coverage_detail(ax, color)
    title = _paint(ax.title, _BOLD, on=color)
    if ax.score is None or ax.coverage < _COVERAGE_FLOOR:
        # Not enough resolved weight to claim a position. Say so, and draw no bar.
        return [f"{title}  {_paint('needs interpretation', _DIM, on=color)}  {detail}"]
    side = _NEG if ax.score < 0 else _POS
    score_txt = _paint(f"{ax.score:+.1f}", side, _BOLD, on=color)
    # Scale is a rubric-wide constant stated once in the header, so the per-axis line
    # just shows the signed value.
    header = f"{title}  {score_txt}  {detail}"
    poles = f"  {ax.poles.negative:<20}{_bar(ax.score, ax.scale, color)}{ax.poles.positive:>20}"
    return [header, poles]


def render_markdown(profile: Profile) -> str:
    lines = [
        f"# Profile: {profile.target}",
        "",
        f"- rubric: `{profile.rubric_version}`",
        f"- engine: `{profile.engine_version}`",
        f"- target sha: `{profile.target_sha or 'unknown'}`",
        "",
        "No aggregate score by design. Each axis is an independent position.",
        "",
    ]
    for ax in profile.axes:
        if ax.score is None or ax.coverage < _COVERAGE_FLOOR:
            score = "needs interpretation"
        else:
            score = f"{ax.score:+.1f} (±{ax.scale:g})"
        m_res, m_total, c_res, c_total = _kind_counts(ax)
        lines.append(f"## {ax.title}: {score}")
        lines.append(
            f"Poles: `{ax.poles.negative}` (-) ↔ `{ax.poles.positive}` (+). "
            f"Coverage: measured {m_res}/{m_total}, classified {c_res}/{c_total}."
        )
        lines.append("")
        lines.append("| indicator | kind | weight | answer | value | evidence | source |")
        lines.append("|---|---|---|---|---|---|---|")
        for ir in ax.indicators:
            val = "" if ir.value is None else f"{ir.value:+.2f}"
            ev = (ir.evidence or "").replace("|", "\\|")[:80]
            lines.append(
                f"| {ir.indicator_id} | {ir.kind.value} | {ir.weight:g} | "
                f"{ir.answer or '-'} | {val} | {ev} | {ir.source or '-'} |"
            )
        lines.append("")
    hint = _skill_hint(profile)
    if hint:
        lines.append(f"> {hint}")
    return "\n".join(lines)


def render_text(profile: Profile, color: bool = False) -> str:
    lines = [
        f"Profile: {profile.target}",
        _paint(
            f"rubric {profile.rubric_version} | engine {profile.engine_version} | "
            f"sha {(profile.target_sha or 'unknown')[:12]}",
            _DIM,
            on=color,
        ),
    ]
    if profile.axes:
        # Scale is rubric-wide, so every axis shares it. State it once here.
        scale = profile.axes[0].scale
        lines.append(_paint(f"scale ±{scale:g} per axis · no aggregate score", _DIM, on=color))
    lines.append("")
    for ax in profile.axes:
        lines.extend(_axis_lines(ax, color=color))
        lines.append("")
    hint = _skill_hint(profile)
    if hint:
        lines.append(_paint(f"→ {hint}", _BOLD, on=color))
    return "\n".join(lines)
