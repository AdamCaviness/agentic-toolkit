# Agent instructions: Agentic Atlas

This file is the canonical guidance for AI agents (Claude Code and others) working in this repository. `CLAUDE.md` is a symlink to this file.

## What this project is

Agentic Atlas profiles agentic development approaches and frameworks by locating each on signed, diverging axes. It is **not** a ranking tool and there is **no aggregate score**. Read `README.md` and `docs/design.md` before making architectural changes.

## Core invariants (do not violate without a versioned rubric change)

1. **No aggregate score.** Never sum, average, or otherwise collapse axes into a single number. Axes are independent positions, and averaging signed positions is meaningless.
2. **The rubric is data, the engine is code.** Scoring logic that belongs to the rubric (weights, indicator definitions, formulas) lives in `rubric/*.yaml`, never hardcoded in `agentic_atlas/`. The engine interprets the rubric, it does not embed a specific rubric.
3. **The axis score is a deterministic function of indicators.** The engine's `scoring.py` is pure arithmetic. Given the same indicator values it must always return the same axis score.
4. **Every profile is reproducible.** Stamp rubric version, engine version, target commit SHA, and (for classified indicators) the model id, on every emitted profile.
5. **`measured` vs `classified` stays separated.** `measured` indicators are computed by the engine with no model. `classified` indicators require reading and a bounded answer plus a cited quote. Never let a classified indicator masquerade as measured.

## Semver

Two independent version lines:

- **Rubric version** (`rubric_version` in each rubric file). MAJOR = any change that moves scores for identical evidence (add/remove indicator, change weight or formula, redefine a pole). MINOR = add a whole new axis or optional metadata that leaves existing axis scores untouched. PATCH = wording that cannot change any indicator value. See `docs/versioning.md`.
- **Engine version** (package version in `pyproject.toml`). Standard software semver.

A profile only compares to another profile computed with the same rubric MAJOR version.

## Layout

```
rubric/v1/                   One directory per MAJOR version
  rubric.yaml                Manifest: version, title, ordered axis ids
  rubric.schema.json         Schema for the manifest
  axis.schema.json           Schema for a single axis file
  axes/<id>/axis.yaml        Source of truth for one axis (poles, indicators, weights)
  axes/<id>/README.md        Human rationale + a generated scoring block
  CHANGELOG.md
agentic_atlas/ Python engine (spec, scoring, evidence, classify, profiler, report, docs, cli)
docs/          Design, axis authoring method, versioning policy
tests/         Tests, with the deterministic scoring core covered first
profiles/      Curated public profiles (generated JSON), including self-eval
```

Each axis README's scoring block is generated from its `axis.yaml` by `agentic-atlas docs`
(`make docs`). Never hand-edit the block between the generated markers, edit the
`axis.yaml` and regenerate. `make docs-check` (part of `make check`) fails on drift.

## Conventions

- Python 3.11+. Keep the deterministic core (`models.py`, `spec.py`, `scoring.py`) dependency-light and fully tested.
- No `TODO` comments. Implement it, or record the plan in `docs/`.
- Document what the code **is**, not what it was. Git history covers the past.
- Prose in docs uses commas rather than dashes for punctuation.

## When changing the rubric

Any edit under `rubric/` that can move scores requires: a version bump, a `rubric/CHANGELOG.md` entry, and a rationale in the PR description. Do not silently recalibrate.
