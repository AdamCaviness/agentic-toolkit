"""End-to-end profiler tests: measured-only, deterministic, no model or network.

These exercise the whole pipeline (evidence -> classify -> scoring) against the shipped
v1 rubric on a synthetic target, with no answers supplied.
"""

from pathlib import Path

from agentic_atlas.evidence import Target
from agentic_atlas.models import IndicatorKind
from agentic_atlas.profiler import profile_target
from agentic_atlas.spec import load_rubric

_RUBRIC = Path(__file__).resolve().parent.parent / "rubric" / "v1"


def _synthetic_target(tmp_path) -> Target:
    (tmp_path / "README.md").write_text(
        "This project enforces a mandatory review step and a spec-driven PRD before code. "
        "We always require approval and confirmation at each checkpoint."
    )
    return Target.from_path(tmp_path)


def test_profile_measured_only_is_well_formed(tmp_path):
    rubric = load_rubric(_RUBRIC)
    profile = profile_target(rubric, _synthetic_target(tmp_path))

    assert [a.axis_id for a in profile.axes] == [ax.id for ax in rubric.axes]
    assert profile.rubric_version == rubric.rubric_version
    assert profile.engine_version

    for ax in profile.axes:
        assert 0.0 <= ax.coverage <= 1.0
        # measured-only run: no classified indicator resolves
        classified = [i for i in ax.indicators if i.kind is IndicatorKind.CLASSIFIED]
        assert all(not i.resolved for i in classified)
        # a resolved score stays within the axis scale; otherwise it is None
        if ax.score is not None:
            assert -ax.scale <= ax.score <= ax.scale


def test_profile_is_deterministic(tmp_path):
    rubric = load_rubric(_RUBRIC)
    target = _synthetic_target(tmp_path)
    first = profile_target(rubric, target).to_dict()
    second = profile_target(rubric, target).to_dict()
    # the synthetic target has no git, so target_sha is None; drop it defensively
    first.pop("target_sha")
    second.pop("target_sha")
    assert first == second
