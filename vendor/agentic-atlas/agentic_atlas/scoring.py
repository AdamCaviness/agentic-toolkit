"""The deterministic scoring core.

Pure arithmetic. Given the same indicator results, these functions always return
the same axis score. This is the heart of the "subjective axis, deterministic
result" design, and it must stay free of I/O, models, and rubric-specific logic.

    axis_score = scale * sum(weight_i * value_i) / sum(weight_i)

computed over resolved indicators only, then clamped to [-scale, +scale].
"""

from __future__ import annotations

from .models import Axis, AxisResult, IndicatorResult, Profile


def score_axis(axis: Axis, results: list[IndicatorResult], *, ndigits: int = 1) -> AxisResult:
    resolved = [r for r in results if r.resolved and r.value is not None]

    total_weight = sum(r.weight for r in results)
    resolved_weight = sum(r.weight for r in resolved)
    coverage = (resolved_weight / total_weight) if total_weight else 0.0

    if resolved_weight == 0:
        score = None
    else:
        raw = sum(r.weight * r.value for r in resolved) / resolved_weight  # in [-1, 1]
        scaled = raw * axis.scale
        score = round(_clamp(scaled, -axis.scale, axis.scale), ndigits)

    return AxisResult(
        axis_id=axis.id,
        title=axis.title,
        poles=axis.poles,
        scale=axis.scale,
        score=score,
        coverage=round(coverage, 4),
        indicators=tuple(results),
    )


def score_profile(
    *,
    target: str,
    rubric_version: str,
    engine_version: str,
    target_sha: str | None,
    axis_results: list[AxisResult],
) -> Profile:
    return Profile(
        target=target,
        rubric_version=rubric_version,
        engine_version=engine_version,
        target_sha=target_sha,
        axes=tuple(axis_results),
    )


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))
