"""Dataclasses for rubrics and profiles.

These are plain data holders. All scoring policy lives in the rubric file and is
applied by ``agentic_atlas.scoring``. No behaviour that could move a score belongs here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class IndicatorKind(str, Enum):
    MEASURED = "measured"
    CLASSIFIED = "classified"


@dataclass(frozen=True)
class Poles:
    negative: str
    positive: str


@dataclass(frozen=True)
class Explain:
    """Plain-language meaning of each pole, shown in the report so a reader who does not
    already know the pole words still understands the axis. The neutral middle is not stored
    per axis: it means the same thing on every axis (a tool near 0 does both ends well, or
    neither), so the renderer states it once rather than repeating it thirteen times."""

    negative: str = ""
    positive: str = ""


@dataclass(frozen=True)
class Indicator:
    id: str
    question: str
    kind: IndicatorKind
    weight: float
    # For classified indicators: answer key -> value in [-1, 1].
    answers: dict[str, float] = field(default_factory=dict)
    # For measured indicators: raw signal spec, interpreted by agentic_atlas.evidence.
    signal: dict | None = None


@dataclass(frozen=True)
class Axis:
    id: str
    title: str
    poles: Poles
    indicators: tuple[Indicator, ...]
    scale: float = 10.0
    description: str = ""
    explain: Explain = Explain()


@dataclass(frozen=True)
class Rubric:
    rubric_version: str
    title: str
    axes: tuple[Axis, ...]
    description: str = ""

    def axis(self, axis_id: str) -> Axis:
        for a in self.axes:
            if a.id == axis_id:
                return a
        raise KeyError(f"no axis {axis_id!r} in rubric {self.rubric_version}")


@dataclass(frozen=True)
class IndicatorResult:
    """The resolved value of one indicator, with its provenance.

    ``value`` is in [-1, 1]. ``resolved`` is False when the indicator could not be
    evaluated (for example a classified indicator with no answer supplied), in which case it
    is excluded from scoring and counted against coverage.
    """

    indicator_id: str
    kind: IndicatorKind
    weight: float
    value: float | None
    resolved: bool
    answer: str | None = None
    evidence: str | None = None
    source: str | None = None  # "engine" for measured, answer-file provenance for classified

    @classmethod
    def unresolved(
        cls,
        indicator: "Indicator",
        kind: IndicatorKind,
        reason: str | None = None,
        source: str | None = None,
    ) -> "IndicatorResult":
        """An indicator that could not be resolved: excluded from scoring, counted
        against coverage. Shared by the measured and classified resolvers so the
        unresolved shape is defined once."""
        return cls(
            indicator_id=indicator.id,
            kind=kind,
            weight=indicator.weight,
            value=None,
            resolved=False,
            answer=None,
            evidence=reason,
            source=source,
        )


@dataclass(frozen=True)
class AxisResult:
    axis_id: str
    title: str
    poles: Poles
    scale: float
    score: float | None  # None when no indicator resolved
    coverage: float  # fraction of weight that was resolvable, 0.0..1.0
    indicators: tuple[IndicatorResult, ...]
    explain: Explain = Explain()


@dataclass(frozen=True)
class Profile:
    """A full profile of one target. This is the emitted artifact.

    Note: there is deliberately no aggregate score. A profile is a vector of
    signed axis positions, never a single number.
    """

    target: str
    rubric_version: str
    engine_version: str
    target_sha: str | None
    axes: tuple[AxisResult, ...]

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "rubric_version": self.rubric_version,
            "engine_version": self.engine_version,
            "target_sha": self.target_sha,
            "axes": [
                {
                    "axis_id": ax.axis_id,
                    "title": ax.title,
                    "poles": {"negative": ax.poles.negative, "positive": ax.poles.positive},
                    "explain": {
                        "negative": ax.explain.negative,
                        "positive": ax.explain.positive,
                    },
                    "scale": ax.scale,
                    "score": ax.score,
                    "coverage": ax.coverage,
                    "indicators": [
                        {
                            "indicator_id": ir.indicator_id,
                            "kind": ir.kind.value,
                            "weight": ir.weight,
                            "value": ir.value,
                            "resolved": ir.resolved,
                            "answer": ir.answer,
                            "evidence": ir.evidence,
                            "source": ir.source,
                        }
                        for ir in ax.indicators
                    ],
                }
                for ax in self.axes
            ],
        }
