"""Tests for the report renderer: the coverage floor, coverage-by-kind, and the
opinionated first-run pointer to the skill."""

from agentic_atlas.models import AxisResult, IndicatorKind, IndicatorResult, Poles, Profile
from agentic_atlas.report import render_text


def _ind(kind: IndicatorKind, resolved: bool, weight: float = 1.0) -> IndicatorResult:
    return IndicatorResult(
        indicator_id="x",
        kind=kind,
        weight=weight,
        value=1.0 if resolved else None,
        resolved=resolved,
        answer="yes" if resolved else None,
    )


def _axis(title, score, coverage, indicators) -> AxisResult:
    return AxisResult(
        axis_id=title.lower(),
        title=title,
        poles=Poles(negative="left", positive="right"),
        scale=10.0,
        score=score,
        coverage=coverage,
        indicators=tuple(indicators),
    )


def _profile(axes) -> Profile:
    return Profile(
        target="/t",
        rubric_version="1.2.0",
        engine_version="0.2.0",
        target_sha="abc123",
        axes=tuple(axes),
    )


def test_below_floor_axis_shows_needs_interpretation_and_no_bar():
    ax = _axis(
        "Thin",
        score=10.0,
        coverage=0.29,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, False)],
    )
    out = render_text(_profile([ax]))
    assert "needs interpretation" in out
    assert "+10.0" not in out  # a sliver of evidence is never dressed up as a verdict
    assert "#" not in out  # no bar drawn


def test_above_floor_axis_plots_a_position():
    ax = _axis(
        "Solid",
        score=-5.5,
        coverage=0.8,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.MEASURED, True)],
    )
    out = render_text(_profile([ax]))
    assert "-5.5" in out
    assert "#" in out  # a bar is drawn
    assert "needs interpretation" not in out


def test_coverage_reported_by_kind():
    ax = _axis(
        "Split",
        score=-5.5,
        coverage=0.8,
        indicators=[
            _ind(IndicatorKind.MEASURED, True),
            _ind(IndicatorKind.MEASURED, True),
            _ind(IndicatorKind.CLASSIFIED, False),
        ],
    )
    out = render_text(_profile([ax]))
    assert "measured 2/2 · classified 0/1" in out


def test_skill_hint_shows_when_classified_unanswered():
    ax = _axis(
        "Thin",
        score=10.0,
        coverage=0.29,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, False)],
    )
    out = render_text(_profile([ax]))
    assert "/agentic-atlas skill" in out


def test_no_skill_hint_when_everything_resolved():
    ax = _axis(
        "Full",
        score=-5.5,
        coverage=1.0,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, True)],
    )
    out = render_text(_profile([ax]))
    assert "/agentic-atlas skill" not in out
