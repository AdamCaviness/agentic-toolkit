# Design

## Thesis

Comparisons of agentic workflows are usually opinion. Agentic Atlas makes the comparison a transparent, versioned computation: it profiles a tool by locating it on signed diverging axes, and each position is computed from many small, named, evidence-backed indicators.

It does not claim objective truth. It claims something you can inspect and argue with: a spec you can contest at the level of a single indicator and change with a versioned pull request.

## Not a ranking

Agentic Atlas produces a **profile**, a vector of signed axis positions, not a score. There is no aggregate number and no leaderboard. The output helps you decide fit ("this leans hard greenfield and opinionated, which matches my project"), not pick a winner.

Overlaying two or three profiles on the same axes is the primary intended use.

## Spec plus interpreter

The repository holds two independently versioned things.

### The rubric (data)

A rubric is a directory, one per MAJOR version (`rubric/v1`). It holds a `rubric.yaml` manifest (version, title, ordered axis ids), a schema for the manifest and for a single axis, and one directory per axis under `axes/<id>/` containing an `axis.yaml` (the source of truth for that axis: poles, indicators, weights) and a `README.md` whose scoring block is generated from the `axis.yaml` by `agentic-atlas docs`. The rubric carries all scoring policy, the engine embeds none.

This per-axis layout makes each axis a self-contained, contestable unit: a dispute over an indicator is a change to one directory, and the generated README block cannot drift from the weights the engine actually uses.

### The engine (code)

`agentic_atlas/` reads a rubric, gathers evidence from a target, resolves each indicator to a value, computes axis scores with a fixed formula, and renders a profile. Pipeline:

```
target ─▶ evidence ─▶ indicator resolution ─▶ scoring ─▶ report
             │              │      │
        measured       measured  classified
      (engine only)   (engine)   (model or human, cited)
```

## The two indicator kinds

The hard part is getting a deterministic result out of a subjective axis. It resolves by decomposing each axis into indicators of two kinds.

- **`measured`** indicators are computed by the engine directly from the repository, with no model. Current signal types: `vocabulary` (term density across docs and commands, bucketed into bands), `path_presence` (glob matches to a value), `git_stats` (repository facts like age and commit count), and `github_api` (host facts like stars). These are deterministic given their input.
- **`classified`** indicators require reading and selecting from a small, defined answer set (for example `yes` / `partial` / `no`). A model picks the answer and must cite a quote copied **verbatim from the target**; the engine discards any answer whose quote it cannot find, and the bounded, anchored answer set keeps independent runs consistent.

The scoring step treats both kinds identically: each resolved indicator yields a value in `[-1, 1]` and a weight. The axis score is:

```
axis_score = scale * sum(weight_i * value_i) / sum(weight_i)
```

clamped to `[-scale, +scale]` and rounded. Indicators that cannot be resolved (for example classified indicators with no answers supplied) are excluded, and the profile reports coverage so a partial profile is never mistaken for a complete one.

## Where judgment lives, and how it is constrained

The judgment call is narrower than "score this axis from -10 to 10." It becomes "answer indicator gb1 with yes, partial, or no, and cite the line that proves it." The answer is produced outside the engine (by the agentic-toolkit skill's host agent), and the engine validates it. Constraints that keep this reproducible:

- Bounded answer sets with anchored definitions in the rubric.
- The engine rejects any answer outside an indicator's declared value set.
- A required quote, verified by the engine to appear verbatim in the target. An answer whose quote cannot be found is discarded and the indicator left unresolved rather than guessed.
- The answerer treats the target's own text as untrusted data, so it cannot instruct the agent into a verdict.
- The source of each supplied answer is stamped on the profile, so a resolution is attributable.

Validation stops a fabricated citation, but it cannot tell a fair quote from a real-but-cherry-picked one. The answer file is therefore a reviewable artifact, and its provenance and review are what defend against a motivated answerer.

## Reproducibility

Every profile stamps rubric version, engine version, target commit SHA, and model id. A local run by the `/agentic-atlas` skill and a curated public profile in `profiles/` use the exact same engine, the skill simply does not persist output. There is no second code path.

## Fairness

The maintainer also maintains agentic-toolkit, itself a profilable target, which is profiled with the same rubric and engine as any other, with no special treatment.
