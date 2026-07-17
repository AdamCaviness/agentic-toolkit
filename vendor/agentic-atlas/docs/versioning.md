# Versioning

Two independent version lines. Do not conflate them.

## Status: pre-settled

This rubric is an initial work in progress; nothing has settled. The `rubric/v1/` directory exists to afford versioning later, it is not a statement that v1 is finished. Until the standard stabilizes and profiles are published, score-moving changes are recorded honestly in `rubric/CHANGELOG.md` but do not each mint a new MAJOR version or directory. The discipline below takes full effect once the rubric settles and comparable profiles exist.

## Rubric version

Declared as `rubric_version` inside the manifest (`rubric/v1/rubric.yaml`), with one directory per MAJOR version (`rubric/v1`, `rubric/v2`). This versions the measurement standard itself. The guiding question for a bump is: **would this change move the score for identical evidence?**

- **MAJOR** (`x.0.0`): any change that can move an existing axis score given the same evidence. This includes adding or removing an indicator, changing a weight, changing the scoring formula, changing an answer-to-value mapping, or redefining a pole. After a MAJOR bump, profiles from earlier MAJOR versions are no longer comparable.
- **MINOR** (`1.x.0`): add a whole new axis, or add optional metadata, such that every existing axis produces an identical score for identical evidence.
- **PATCH** (`1.0.x`): wording changes that cannot change any indicator value. Typos, clearer examples, expanded rationale.

Calibration changes are honestly breaking, so expect MAJOR bumps to be common. That is correct for a measurement standard. A profile is only ever compared to another profile computed under the same rubric MAJOR version.

Every rubric change records an entry in `rubric/CHANGELOG.md` and a rationale in the pull request.

## Engine version

Standard software semver on the `agentic_atlas` Python package, declared in `pyproject.toml`. MAJOR for breaking CLI or API changes, MINOR for features, PATCH for fixes. The engine version is independent of the rubric version, a new engine must still correctly interpret older rubric files within the schema's supported range.

## What a profile stamps

Every emitted profile records both versions plus the target commit SHA and, for classified indicators, the model id. Two profiles are directly comparable only when their rubric MAJOR versions match.
