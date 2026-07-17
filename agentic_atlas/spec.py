"""Load and validate a rubric into typed dataclasses.

A rubric is a directory (one per MAJOR version, e.g. ``rubric/v1``) containing:

    rubric.yaml            manifest: rubric_version, title, ordered axis ids
    rubric.schema.json     schema for the manifest
    axis.schema.json       schema for a single axis file
    axes/<id>/axis.yaml    one axis per directory (source of truth for scoring)

``load_rubric`` accepts either the directory or the ``rubric.yaml`` path.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from .models import Axis, Indicator, IndicatorKind, Poles, Rubric


def _resolve_dir(path: str | Path) -> Path:
    p = Path(path).expanduser().resolve()
    if p.is_file():
        return p.parent
    if (p / "rubric.yaml").is_file():
        return p
    raise FileNotFoundError(f"no rubric.yaml found at or in {p}")


def _validate(instance: dict, schema_path: Path) -> None:
    import jsonschema  # imported lazily so models/scoring stay dependency-light

    jsonschema.validate(instance=instance, schema=json.loads(schema_path.read_text()))


def _parse_answers(indicator: dict) -> dict[str, float]:
    answers: dict[str, float] = {}
    for k, v in indicator.get("answers", {}).items():
        if isinstance(k, bool):
            # YAML 1.1 turns unquoted yes/no/true/false into booleans. Answer keys
            # must be strings, so the author has to quote them.
            raise ValueError(
                f"indicator {indicator['id']!r} has a boolean answer key ({k!r}). "
                f'Quote yes/no/true/false answer keys in the rubric, e.g. "yes".'
            )
        answers[str(k)] = float(v)
    return answers


def parse_axis(raw: dict, scale: float = 10.0) -> Axis:
    indicators = tuple(
        Indicator(
            id=i["id"],
            question=i["question"],
            kind=IndicatorKind(i["kind"]),
            weight=float(i["weight"]),
            answers=_parse_answers(i),
            signal=i.get("signal"),
        )
        for i in raw["indicators"]
    )
    return Axis(
        id=raw["id"],
        title=raw["title"],
        poles=Poles(negative=raw["poles"]["negative"], positive=raw["poles"]["positive"]),
        indicators=indicators,
        scale=scale,
        description=raw.get("description", ""),
    )


def load_axis(
    path: str | Path,
    *,
    validate: bool = True,
    schema_dir: Path | None = None,
    scale: float = 10.0,
) -> Axis:
    path = Path(path)
    raw = yaml.safe_load(path.read_text())
    if validate:
        schema_dir = schema_dir or path.parent.parent.parent
        _validate(raw, schema_dir / "axis.schema.json")
    return parse_axis(raw, scale=scale)


def load_rubric(path: str | Path, *, validate: bool = True) -> Rubric:
    rubric_dir = _resolve_dir(path)
    manifest = yaml.safe_load((rubric_dir / "rubric.yaml").read_text())
    if validate:
        _validate(manifest, rubric_dir / "rubric.schema.json")

    # Scale is a rubric-wide constant so every axis shares the same range and stays
    # comparable. Applied to every axis here, never set per axis.
    scale = float(manifest.get("scale", 10.0))
    axes: list[Axis] = []
    for axis_id in manifest["axes"]:
        axis_path = rubric_dir / "axes" / axis_id / "axis.yaml"
        if not axis_path.is_file():
            raise FileNotFoundError(f"manifest lists {axis_id!r} but {axis_path} is missing")
        axis = load_axis(axis_path, validate=validate, schema_dir=rubric_dir, scale=scale)
        if axis.id != axis_id:
            raise ValueError(f"axis id {axis.id!r} does not match its directory {axis_id!r}")
        axes.append(axis)

    return Rubric(
        rubric_version=manifest["rubric_version"],
        title=manifest["title"],
        axes=tuple(axes),
        description=manifest.get("description", ""),
    )
