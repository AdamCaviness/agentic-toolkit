"""Orchestrate a full profile: evidence, then classification, then scoring.

This is the single code path. The /agentic-atlas skill and any curated public profile both
run through here, they differ only in whether they persist the result.

The two indicator forms are resolved by two symmetric functions: measured indicators by
``evidence.resolve_measured`` (computed from the repository), classified indicators by
``classify.resolve_classified`` (validated from answers the caller supplies). With no
answers, classified indicators stay unresolved and the profile is measured-only.
"""

from __future__ import annotations

from . import __version__
from .classify import resolve_classified
from .evidence import Target, resolve_measured
from .models import IndicatorKind, Profile, Rubric
from .scoring import score_axis, score_profile


def profile_target(
    rubric: Rubric,
    target: Target,
    answers: dict[str, dict] | None = None,
    answers_source: str = "supplied",
) -> Profile:
    axis_results = []
    for axis in rubric.axes:
        results = []
        for ind in axis.indicators:
            if ind.kind is IndicatorKind.MEASURED:
                results.append(resolve_measured(ind, target))
            else:
                results.append(resolve_classified(ind, target, answers, answers_source))
        axis_results.append(score_axis(axis, results))

    return score_profile(
        target=str(target.root),
        rubric_version=rubric.rubric_version,
        engine_version=__version__,
        target_sha=target.git_sha(),
        axis_results=axis_results,
    )
