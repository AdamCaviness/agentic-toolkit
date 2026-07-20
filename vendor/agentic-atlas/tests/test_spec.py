"""Tests that the shipped rubric loads and validates."""

from pathlib import Path

from agentic_atlas.models import IndicatorKind
from agentic_atlas.spec import load_rubric

_RUBRIC = Path(__file__).resolve().parent.parent / "rubric" / "v1"


_EXPECTED_AXES = [
    "greenfield-vs-brownfield",
    "small-scope-vs-large-scope",
    "prototype-vs-production",
    "solo-vs-team",
    "generalist-vs-specialist",
    "fresh-vs-mature",
    "interrogative-vs-opinionated",
    "autonomous-vs-human-in-loop",
    "spec-light-vs-spec-driven",
    "test-optional-vs-test-first",
    "single-agent-vs-multi-agent",
    "prescriptive-vs-composable",
    "lightweight-vs-heavyweight",
]


def test_shipped_rubric_validates_and_parses():
    r = load_rubric(_RUBRIC, validate=True)
    assert r.rubric_version == "1.4.0"
    assert {a.id for a in r.axes} == set(_EXPECTED_AXES)


def test_manifest_order_is_preserved():
    r = load_rubric(_RUBRIC)
    assert [a.id for a in r.axes] == _EXPECTED_AXES


def test_manifest_scale_propagates_to_every_axis(tmp_path):
    # A rubric-wide scale in the manifest must reach every axis, so positions stay on one
    # shared range. Copy the shipped rubric, override the manifest scale, and check.
    import shutil

    import yaml

    dst = tmp_path / "v1"
    shutil.copytree(_RUBRIC, dst)
    manifest_path = dst / "rubric.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["scale"] = 7
    manifest_path.write_text(yaml.safe_dump(manifest))

    r = load_rubric(dst)
    assert r.axes  # sanity: axes loaded
    assert all(a.scale == 7 for a in r.axes)


def test_classified_indicators_have_answers():
    r = load_rubric(_RUBRIC)
    for axis in r.axes:
        for ind in axis.indicators:
            if ind.kind is IndicatorKind.CLASSIFIED:
                assert ind.answers, f"{ind.id} classified but has no answers"
            else:
                assert ind.signal, f"{ind.id} measured but has no signal"


def test_answer_values_in_range():
    r = load_rubric(_RUBRIC)
    for axis in r.axes:
        for ind in axis.indicators:
            for v in ind.answers.values():
                assert -1.0 <= v <= 1.0


def test_every_axis_has_plain_language_pole_meanings():
    # Every shipped axis must explain both poles so the report can teach a reader what the
    # pole words mean. The neutral middle is explained once by the renderer, not per axis.
    r = load_rubric(_RUBRIC)
    for axis in r.axes:
        assert axis.explain.negative, f"{axis.id} is missing a negative pole meaning"
        assert axis.explain.positive, f"{axis.id} is missing a positive pole meaning"
