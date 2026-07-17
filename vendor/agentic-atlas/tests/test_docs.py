"""The generated axis README blocks must stay in sync with axis.yaml."""

from pathlib import Path

from agentic_atlas import docs

_RUBRIC = Path(__file__).resolve().parent.parent / "rubric" / "v1"


def test_axis_readmes_are_in_sync():
    stale = docs.sync(_RUBRIC, check=True)
    assert stale == [], f"stale axis READMEs, run `make docs`: {stale}"
