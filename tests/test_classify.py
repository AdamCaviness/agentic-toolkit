"""Tests for classified-indicator resolution.

The engine never calls a model, so these are pure and need no network or fake client.
They exercise the deterministic validation that makes a supplied classified answer
trustworthy: the answer must be a declared value and the cited quote must appear verbatim
in the target, or the indicator is left unresolved.
"""

from agentic_atlas.classify import classified_questions, resolve_classified
from agentic_atlas.evidence import Target
from agentic_atlas.models import Axis, Indicator, IndicatorKind, Poles, Rubric


def _classified_indicator() -> Indicator:
    return Indicator(
        id="c1",
        question="Does the approach document a review step?",
        kind=IndicatorKind.CLASSIFIED,
        weight=1.0,
        answers={"yes": 1.0, "no": -1.0},
    )


def _target(tmp_path, text: str) -> Target:
    (tmp_path / "readme.md").write_text(text)
    return Target.from_path(tmp_path)


def _answer(answer, evidence):
    return {"c1": {"answer": answer, "evidence": evidence}}


def test_no_answer_leaves_classified_unresolved(tmp_path):
    result = resolve_classified(_classified_indicator(), Target.from_path(tmp_path), None)
    assert result.resolved is False
    assert result.value is None


def test_resolves_with_verbatim_quote(tmp_path):
    target = _target(tmp_path, "We always run a review step before every merge.")
    result = resolve_classified(
        _classified_indicator(),
        target,
        _answer("yes", "run a review step before every merge"),
        source="agentic-toolkit:test",
    )
    assert result.resolved is True
    assert result.value == 1.0
    assert result.answer == "yes"
    assert result.evidence == "run a review step before every merge"
    assert result.source == "agentic-toolkit:test"


def test_verbatim_check_tolerates_whitespace_reflow(tmp_path):
    target = _target(tmp_path, "We always run\na review step before every merge.")
    result = resolve_classified(
        _classified_indicator(), target, _answer("yes", "run a review step")
    )
    assert result.resolved is True


def test_fabricated_quote_is_rejected(tmp_path):
    target = _target(tmp_path, "This project has some text but says nothing about reviews.")
    result = resolve_classified(
        _classified_indicator(), target, _answer("yes", "enforces a mandatory review gate")
    )
    assert result.resolved is False
    assert result.value is None
    assert result.source is None


def test_out_of_enum_answer_is_rejected(tmp_path):
    target = _target(tmp_path, "We always run a review step before every merge.")
    result = resolve_classified(
        _classified_indicator(), target, _answer("maybe", "run a review step before every merge")
    )
    assert result.resolved is False
    assert result.value is None


def test_trivially_short_quote_is_rejected(tmp_path):
    target = _target(tmp_path, "We run a review step before every merge.")
    result = resolve_classified(_classified_indicator(), target, _answer("yes", "review"))
    assert result.resolved is False


def test_missing_indicator_answer_is_unresolved(tmp_path):
    target = _target(tmp_path, "We always run a review step before every merge.")
    # answers dict present but without an entry for this indicator
    result = resolve_classified(_classified_indicator(), target, {"other": {}})
    assert result.resolved is False
    assert result.value is None


def test_classified_questions_lists_only_classified_indicators():
    rubric = Rubric(
        rubric_version="0.0.0",
        title="t",
        axes=(
            Axis(
                id="ax",
                title="Ax",
                poles=Poles(negative="a", positive="b"),
                indicators=(
                    _classified_indicator(),
                    Indicator(
                        id="m1",
                        question="measured",
                        kind=IndicatorKind.MEASURED,
                        weight=1.0,
                        signal={"type": "vocabulary", "terms": ["x"], "bands": []},
                    ),
                ),
            ),
        ),
    )
    qs = classified_questions(rubric)
    assert [q["id"] for q in qs] == ["c1"]
    assert qs[0]["axis"] == "ax"
    assert qs[0]["answers"] == ["no", "yes"]
