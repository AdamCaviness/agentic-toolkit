"""Tests for the report renderer: the coverage floor, coverage-by-kind, and the
opinionated first-run pointer to the skill."""

from agentic_atlas.models import AxisResult, IndicatorKind, IndicatorResult, Poles, Profile
from agentic_atlas.report import render_html, render_text


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


# --- render_html --------------------------------------------------------------------------


def test_html_is_byte_identical_for_same_profile():
    # Determinism: a pure function of the Profile, no timestamps or random ids.
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    profile = _profile([ax])
    assert render_html(profile) == render_html(profile)


def test_html_draws_a_solid_bar_above_floor():
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_html(_profile([ax]))
    assert 'class="fill neg"' in out  # a real bar, drawn solid
    assert 'class="fill neg prov"' not in out  # not faded
    assert "low evidence" not in out  # the provisional tag is absent
    assert "nothing could be read" not in out


def test_html_always_draws_a_faded_bar_below_floor():
    # Unlike the terminal renderer, HTML never hides a scored axis: below the floor it
    # fades and tags the bar rather than dropping it.
    ax = _axis(
        "Thin",
        score=10.0,
        coverage=0.29,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, False)],
    )
    out = render_html(_profile([ax]))
    assert "fill pos prov" in out  # a bar is still drawn, faded
    assert "low evidence" in out
    assert "nothing could be read" not in out
    assert "+10.0" in out  # the number is shown, just marked provisional


def test_html_null_state_when_nothing_resolved():
    # score None (nothing resolved) is the only no-bar case, and it says so plainly.
    ax = _axis(
        "Empty",
        score=None,
        coverage=0.0,
        indicators=[_ind(IndicatorKind.MEASURED, False), _ind(IndicatorKind.CLASSIFIED, False)],
    )
    out = render_html(_profile([ax]))
    assert "nothing could be read" in out
    assert 'class="fill' not in out  # no bar drawn at all


def test_html_uses_plain_labels_not_engine_jargon():
    ax = _axis(
        "Split",
        score=-5.5,
        coverage=0.8,
        indicators=[_ind(IndicatorKind.MEASURED, True), _ind(IndicatorKind.CLASSIFIED, True)],
    )
    out = render_html(_profile([ax]))
    assert ">detected</span>" in out  # measured, in plain words
    assert ">judged</span>" in out  # classified, in plain words
    assert "% evidence" in out  # coverage, in plain words
    # the engine's kind vocabulary never surfaces as a visible label
    assert ">measured<" not in out
    assert ">classified<" not in out


def test_html_escapes_untrusted_evidence():
    evil = IndicatorResult(
        indicator_id="x",
        kind=IndicatorKind.MEASURED,
        weight=1.0,
        value=1.0,
        resolved=True,
        answer="a",
        evidence="<script>alert('xss')</script>",
        source="engine",
    )
    ax = _axis("Esc", score=5.0, coverage=0.8, indicators=[evil])
    out = render_html(_profile([ax]))
    assert "<script>alert" not in out  # never emitted raw
    assert "&lt;script&gt;" in out  # escaped instead


def test_html_states_there_is_no_aggregate_score():
    ax = _axis("Solid", score=-5.5, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_html(_profile([ax]))
    assert "no overall grade" in out  # the no-aggregate invariant, stated to the reader


def test_html_neutral_score_reads_as_neutral_not_positive():
    ax = _axis("Mid", score=0.0, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_html(_profile([ax]))
    assert '<span class="score zero">0.0</span>' in out  # neutral, no forced sign
    assert "+0.0" not in out  # a zero is never dressed up as a faint positive
    assert 'class="fill' not in out  # a neutral axis has no lean fill


def test_text_neutral_score_has_no_forced_sign():
    ax = _axis("Mid", score=0.0, coverage=0.8, indicators=[_ind(IndicatorKind.MEASURED, True)])
    out = render_text(_profile([ax]))
    assert "0.0" in out
    assert "+0.0" not in out
