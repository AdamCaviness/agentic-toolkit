"""Tests for the deterministic scoring core."""

from agentic_atlas.models import Axis, Indicator, IndicatorKind, IndicatorResult, Poles
from agentic_atlas.scoring import score_axis


def _axis(scale=10.0):
    return Axis(
        id="a",
        title="A",
        poles=Poles(negative="left", positive="right"),
        scale=scale,
        indicators=(
            Indicator("i1", "?", IndicatorKind.CLASSIFIED, weight=3, answers={"x": -1.0}),
            Indicator("i2", "?", IndicatorKind.MEASURED, weight=1, signal={}),
        ),
    )


def _res(iid, weight, value, resolved=True):
    return IndicatorResult(
        indicator_id=iid,
        kind=IndicatorKind.MEASURED,
        weight=weight,
        value=value,
        resolved=resolved,
    )


def test_weighted_mean_scaled():
    axis = _axis(scale=10.0)
    # (3*-1.0 + 1*1.0) / 4 = -0.5 -> -5.0
    results = [_res("i1", 3, -1.0), _res("i2", 1, 1.0)]
    ar = score_axis(axis, results)
    assert ar.score == -5.0
    assert ar.coverage == 1.0


def test_full_lean_hits_scale_bound():
    axis = _axis(scale=10.0)
    results = [_res("i1", 3, -1.0), _res("i2", 1, -1.0)]
    assert score_axis(axis, results).score == -10.0


def test_unresolved_excluded_and_coverage_reported():
    axis = _axis(scale=10.0)
    results = [_res("i1", 3, -1.0), _res("i2", 1, None, resolved=False)]
    ar = score_axis(axis, results)
    # Only i1 counts: -1.0 * 10 = -10.0, coverage 3/4.
    assert ar.score == -10.0
    assert ar.coverage == 0.75


def test_no_resolution_yields_none_score():
    axis = _axis()
    results = [_res("i1", 3, None, resolved=False), _res("i2", 1, None, resolved=False)]
    ar = score_axis(axis, results)
    assert ar.score is None
    assert ar.coverage == 0.0


def test_custom_scale():
    axis = _axis(scale=5.0)
    results = [_res("i1", 1, 1.0)]
    assert score_axis(axis, results).score == 5.0
