# Agentic Atlas: continuation spec

This is a self-contained handoff for continuing work on Agentic Atlas
(`~/_opensource/agentic-atlas`). Read it fully before making changes,
then read `AGENTS.md`, `README.md`, and `docs/` for detail. It captures the
rationale behind decisions so you do not re-litigate them, the current state,
and the prioritized next steps.

## What this project is

An open, versioned rubric that **profiles** agentic development approaches,
frameworks, methods, and skill systems (BMAD-METHOD, Superpowers, GSD, LFG, and
similar) by **locating** each on signed bipolar axes. It is for Claude Code and
comparable coding agents.

**Purpose:** to let a person decide, as easily as possible, which approach best
suits their project and their way of working. The output supports a fit decision
("this leans hard greenfield and opinionated, which matches my project"), never
a verdict ("this is best").

## Core thesis and its rationale

- **Not a ranking, no aggregate score.** Collapsing independent axes into one
  number is meaningless (averaging signed positions cancels legitimate signal),
  and a leaderboard invites the "who are you to grade me" fight. A profile is a
  vector of positions, full stop. Do not add a total, average, or rank.
- **Signed bipolar axes.** Each axis is a continuum between two opposed poles
  with `0.0` as neutral balance. Sign = which way it leans, magnitude = how far.
  Both poles are legitimate; neither is the failure mode. Default scale is `10`
  (positions run `-10` to `+10`). "Axis" is deliberate: a profile is a coordinate
  in a multi-axis space, rendered as a radar/overlay.
- **Each axis is a weighted scoring system over N measurements.** The signed
  position is a deterministic function of many small, named, evidence-backed
  indicators:
  `axis_position = scale * sum(weight_i * measurement_i) / sum(weight_i)`.
  The "craft" of an axis is choosing its indicators and weights; that lives
  entirely in the rubric. The engine only executes the arithmetic.
- **Two indicator kinds.** `measured` = computed deterministically by the engine
  from the repository, no model (today: `vocabulary` term-density bands and
  `path_presence` globs). `classified` = a bounded answer chosen by a model or
  human, recorded with a cited quote. Keep them strictly separate; never let a
  classified indicator masquerade as measured.
- **Opinionated but contestable.** The rubric is admittedly subjective, but it is
  transparent, versioned under semver, and contestable at the level of a single
  indicator (a dispute is a PR against one axis directory). Not perfect, but
  something concrete, inspectable, and improvable, which beats a blog-post take.

### Rationale for decisions that were explicitly considered

- **Fresh vs Mature is an axis, not a separate "meter."** Maturity looks like a
  magnitude (stars, commits), but modeling it as a signed axis (fresh =
  cutting-edge/fast-moving, mature = stable/battle-tested) keeps the whole system
  one unified family of signed sliders and fits "both poles legitimate." The
  deterministic signals (stars, commit count, age, release cadence) are its
  indicators. It is deferred only because the collectors do not exist yet.
- **Spec + interpreter, two version lines.** The rubric is data (versioned under
  its own semver), the engine is code (versioned in `pyproject.toml`). Every
  profile stamps rubric version, engine version, target commit SHA, and model id
  (for classified), so any profile is reproducible and arguable.
- **Per-axis directory layout, with a generated README block.** Each axis is a
  self-contained, contestable unit. `axis.yaml` is the source of truth; the
  README's scoring block is generated from it by `agentic-atlas docs` and a drift check
  (`make docs-check`) fails CI if they diverge, so the human doc can never
  misstate the real weights. One directory per MAJOR version because only a MAJOR
  bump breaks cross-version comparability.

## Semver policy

Two independent lines. For the **rubric**, the guiding question is "would this
change move the score for identical evidence?"

- MAJOR: any change that can move an existing axis score (add/remove indicator,
  change a weight or formula or answer-to-value mapping, redefine a pole).
  Calibration changes are honestly breaking, so MAJOR bumps are common.
- MINOR: add a whole new axis, or optional metadata, leaving existing axis
  scores unchanged for identical evidence.
- PATCH: wording that cannot change any indicator value.

Profiles compare only within the same rubric MAJOR version. The **engine** uses
standard software semver. See `docs/versioning.md`.

## Current state (implemented and tested)

- Per-axis rubric layout under `rubric/v1/` with a `rubric.yaml` manifest,
  `rubric.schema.json` + `axis.schema.json`, and `axes/<id>/{axis.yaml,README.md}`.
- Deterministic weighted-scoring core (`agentic_atlas/scoring.py`), pure arithmetic.
- Evidence collectors (`agentic_atlas/evidence.py`): `vocabulary` and `path_presence`,
  with a recursive glob matcher (fnmatch does not handle `**`; this was a real
  bug that mis-scored path-presence axes). Plus `git_stats` (commit count,
  contributor count, age in days, tag count) and `github_api` (stars, forks,
  watchers, open issues) which resolve to unresolved (counted against coverage)
  when there is no git history, no origin remote, or no network.
- Indicator resolution is two symmetric functions: `evidence.resolve_measured` (computed
  from the repository) and `classify.resolve_classified` (`agentic_atlas/classify.py`),
  which validates classified answers supplied as data by an external agent; the answer must
  be a declared value and the cited quote must appear verbatim in the target, else the
  indicator is left unresolved. With no answers, classified indicators stay unresolved. The
  engine calls no model and needs no API key; answering happens in the agentic-toolkit
  skill, validation happens here.
- Orchestration (`agentic_atlas/profiler.py`), reports text/markdown/JSON (`agentic_atlas/report.py`).
- Docs generator (`agentic_atlas/docs.py`) + `agentic-atlas docs [--check]`.
- CLI (`agentic_atlas/cli.py`): `validate`, `docs`, `profile` (`--answers`), `questions`.
- Makefile: `setup test lint fmt check validate docs docs-check profile
  clean`. `make check` = lint + docs-check + test.
- release-please wired for the engine version (`release-type: python`, config +
  manifest at repo root, workflow in `.github/workflows/`). Conventional commits
  drive the bump; the workflow auto-merges the release PR (matches agentic-toolkit).
- 31 tests passing.

Verify with: `cd ~/_opensource/agentic-atlas && make check`

Note on measured-only profiles: they saturate toward the poles at low coverage
(only 1-2 measured indicators resolve per axis). This is correct, not a bug. The
reported coverage percentage is the honesty signal; full positions need the
classified indicators answered.

## The v1 axis set (13, curated)

Grouped for a readable radar (rubric is at 1.1.0):

- Context: greenfield-vs-brownfield, small-scope-vs-large-scope,
  prototype-vs-production, solo-vs-team, generalist-vs-specialist,
  fresh-vs-mature (added in 1.1.0, uses `git_stats` + `github_api`)
- Style: interrogative-vs-opinionated, autonomous-vs-human-in-loop
- Process: spec-light-vs-spec-driven, test-optional-vs-test-first
- Architecture: single-agent-vs-multi-agent, prescriptive-vs-composable
- Footprint: lightweight-vs-heavyweight

Deferred/backlog (with reasons in `rubric/v1/CHANGELOG.md`):
model-agnostic-vs-model-specific, permissive-vs-guardrailed,
stateless-vs-stateful, conversational-vs-command-driven,
single-pass-vs-review-looped, bare-vs-integration-heavy, informal-vs-ceremonial,
magic-vs-mechanical, fast-start-vs-high-setup, and the audience axes. Dropped:
implementation-first-vs-planning-first (near-duplicate of spec-light/spec-driven).

Sign conventions and weights are a first proposal and are meant to be contested
before v1 is treated as stable.

## Next steps (priority order)

1. **[DONE, rubric 1.1.0]** `git_stats` + `github_api` collectors and the
   **fresh-vs-mature** axis. Schema extended with both signal types (a shared
   `bands` def), evidence collectors added, 12 new tests (git via a temp repo,
   GitHub via a mocked fetch), axis authored with 5 measured + 1 classified
   indicators so it scores meaningfully measured-only. Smoke-tested live against
   agentic-toolkit (stars fetched, all git metrics resolved).
2. **[DONE]** Classified indicators are unlocked without an API key. The engine calls no
   model: `agentic-atlas questions <target>` emits the classified worklist (id, axis,
   question, allowed answers) as JSON, an external agent answers each, and
   `agentic-atlas profile --answers <file>` feeds them to `classify.resolve_classified`, which
   validates each deterministically (the answer must be a declared value; the cited quote
   must appear verbatim in the target) and scores the ones that pass. Provenance is stamped
   from the answer file's `source`. Validation stops fabrication but not a real-but-cherry
   picked quote, so the answer file's review is the remaining defense; this is the same
   grounding rationale that keeps a bare hand-authored path untrusted. `tests/test_classify.py`
   covers verbatim-quote acceptance, whitespace-reflow tolerance, fabricated-quote
   rejection, out-of-enum rejection, short-quote rejection, missing-answer handling, and the
   classified-question worklist.
3. **Add `agentic-atlas compare`.** Overlay 2-3 profiles on the same axes (text radar or
   markdown table), the primary intended use of the tool.
4. **Build the `/agentic-atlas` skill in agentic-toolkit.** It shells out to this engine,
   runs locally, and prints a non-persisted report. Same single code path.
5. **Publish the self-eval.** Once the axis set stabilizes, generate the public
   profile of agentic-toolkit into `profiles/` with no special treatment.
6. **Build a corpus and study axis correlation, then personas and viz.** Profile
   10 to 15 real approaches, compute the correlation matrix, and use it to drive
   axis merges, adjacency ordering, and grounded personas. The correlation study
   is the prerequisite that makes the persona-fit feature and any 3D map honest.
   Full design in `specs/personas-correlation-ordering.md`.

Related design notes: `specs/personas-correlation-ordering.md` (personas as a
layer above the rubric, axis correlation as a measured hypothesis, output
ordering, and the 2D/3D visualization plan).

## Open decisions to raise with the user

- **[RESOLVED]** GitHub org/owner is `adamcaviness`. README, docs, and both
  schema `$id` links updated from the `adamavo` placeholder.
- **[RESOLVED]** release-please is set up for the engine version.
- **[RESOLVED]** The project name is **Agentic Atlas** (repo
  `agentic-atlas`). A prior session nicknamed it "Atlas" in prose, which
  was a mistake and has been corrected. The conflict-of-interest material was
  overwrought and was collapsed to a single honest sentence (the maintainer also
  maintains agentic-toolkit, profiled with no special treatment); the standalone
  `docs/conflict-of-interest.md` was removed.
- When authoring new axes, watch correlation with existing ones; the risk is
  dilution, not coverage. Prefer merging over adding a near-duplicate.

## Conventions

- Python 3.11+. Keep `models.py`, `spec.py`, `scoring.py` dependency-light and
  fully tested. No `TODO` comments (implement or record the plan here). Document
  what the code is, not what it was. Prose uses commas rather than dashes.
- Never hand-edit the generated block between the markers in an axis README; edit
  `axis.yaml` and run `make docs`.
- Any rubric change that can move a score needs a version bump, a
  `rubric/v1/CHANGELOG.md` entry, and a rationale in the PR.
