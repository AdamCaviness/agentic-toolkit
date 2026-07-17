# Personas, axis correlation, and output ordering

Status: **design proposal**. The persona ranges and axis correlations below are
**hypotheses**, not measured data. Nothing here is implemented. The point of the
note is to fix the shape of the idea and the sequence that would ground it in
data, so it is not lost or re-litigated. See `specs/handoff.md` for project state.

## Motivating question

Do our axes relate, such that a development persona (vibe coding, TDD, spec-driven,
and so on) wants qualities within specific ranges across axes? If so, that
relationship could inform how axes are ordered in output (text, 2D, 3D) and could
power a "which approach fits me" feature.

Short answer: yes, personas map to coherent regions and axes visibly co-move, but
the correlations must be **measured** across a real corpus before we bake them in,
or we build a circular design that discovers only what it assumed.

## A persona is a region in axis-space

A persona is not a point, it is a preferred region: a target value, a tolerance,
and an importance-weight per axis. Sketches (sign convention is negative pole
first, per each axis id):

- **Vibe coder** (fast, throwaway): prototype (−−), spec-light (−−),
  lightweight (−−), small-scope (−), test-optional (−), opinionated (+),
  autonomous (+), fresh (−). Indifferent to team, brownfield.
- **TDD craftsperson**: test-first (++), production (+), composable (+),
  human-in-loop (−autonomous), specialist (+). Neutral on greenfield/brownfield.
- **Spec-driven architect / enterprise**: spec-driven (++), large-scope (++),
  team (+), production (+), opinionated (+), multi-agent (+), heavyweight (+),
  mature (+). Cares about nearly every axis.
- **Brownfield maintainer**: brownfield (++), small-scope (−), production (+),
  test-first (+), human-in-loop (−autonomous), mature (+).
- **Autonomous delegator**: autonomous (++), prescriptive (+), opinionated (+),
  mid scope. Indifferent to greenfield/brownfield.

Two observations. Personas land in coherent regions, not scatter. And the axes
co-move: a `spec-driven + large-scope + heavyweight + team + opinionated +
multi-agent` "structured/enterprise" lobe, a `prototype + spec-light + lightweight
+ small-scope` "quick/vibe" lobe, and `production + test-first` look nearly joined.

## Correlation is a hypothesis to measure, not to assume

We have essentially zero real profiles today. If we hard-code these correlations
and persona ranges from intuition, then order axes and merge them to match, we
have built a circle. The rigorous sequence:

1. Ship the rubric (13 axes, at 1.1.0).
2. Profile a real corpus, 10 to 20 tools (BMAD-METHOD, Superpowers, GSD, LFG,
   spec-kit, agentic-toolkit, and peers).
3. Compute the correlation matrix across those profiles.
4. Then let data drive three decisions:
   - **Merge** near-duplicate axes. First pair to scrutinize: `prototype-vs-production`
     and `test-optional-vs-test-first`.
   - **Adjacency order** for output (see below).
   - **Grounded persona definitions** from real clusters.

Until then, persona thinking earns its keep only as a sanity check on axis
independence: any two axes we can already predict will always co-move are
merge candidates to flag, not separate spokes that inflate one lobe.

## Architecture: personas are a layer above the rubric

The rubric measures how a tool scores. A persona encodes what a user wants. These
are different kinds of subjective and they change independently, so keep them
separate:

- **Rubric** (`rubric/`): axis definitions and scoring. Pure measurement.
- **Personas** (`personas/*.yaml`, a new sibling, own version line): per-axis
  target value, tolerance, importance-weight.
- **Fit**: a distance function between a tool profile and a persona region.

Sketch of a persona file:

```yaml
persona_version: 0.1.0
id: tdd-craftsperson
title: TDD craftsperson
axes:
  test-optional-vs-test-first: { target: 8, tolerance: 3, weight: 3 }
  prototype-vs-production:      { target: 5, tolerance: 4, weight: 2 }
  autonomous-vs-human-in-loop:  { target: -4, tolerance: 4, weight: 2 }
  # axes omitted are "don't care" (weight 0)
```

Fit is a weighted distance: for each axis the persona cares about, how far the
tool sits outside the persona's tolerance band, weighted by importance, summed and
normalized. Lower is a closer fit.

### Why persona-fit does not violate "no aggregate score"

The invariant forbids a context-free quality grade ("this tool is 7/10"). A fit
score is different in kind: it is "relative to what **you** said you want, this
tool is close or far." It is a property of the (tool, your-preferences) pair, not
of the tool alone. That is the entire purpose of the product, the difference
between a leaderboard and a recommender. Document it as a deliberate boundary so a
future contributor does not mistake fit-ranking for the forbidden aggregate.

## Output ordering

- **Freeze a canonical order for comparability.** Overlays only work if every
  tool's spokes sit in the same positions. The base order in text, 2D, and 3D must
  be fixed. The current semantic grouping (context, style, process, architecture,
  footprint) is a fine, human-scannable canonical order to keep for now.
- **Let correlation choose adjacency, later.** Once the correlation matrix exists,
  use hierarchical clustering or matrix seriation (optimal leaf ordering) to place
  correlated axes adjacent. Then a radar's lobes become meaningful (a bulge is a
  real cluster) instead of an artifact of arbitrary spoke order. Freeze the result
  as the new canonical order under a rubric version bump.
- **Persona is a highlight/weight overlay, not a reorder.** Different personas want
  different emphasis, so per-persona reordering would break comparability. An
  interactive "view as persona X" mode dims axes the persona ignores, emphasizes
  the ones it weights, and draws the persona's target region as a ghost polygon to
  compare against. The base spokes never move.

## Synthesis with the 3D idea

This is also the honest precondition for meaningful 3D. If the correlation study
shows the 13 axes collapse to roughly 3 latent factors (for example
"structure/ceremony," "autonomy," "code-vs-idea"), those factors are real, nameable
dimensions, and a 3D map with tools as points and personas as regions is
legitimate rather than decorative. So the persona/correlation work is what would
make the 3D instinct pay off. See the 2D-first, 3D-signature-toggle plan in
`specs/handoff.md` and the visualization backlog.

## Recommended next step

Do not build viz or personas from intuition. The unlock is a real corpus of
profiles, because it converts every downstream decision (merges, ordering,
personas, 3D) from guesswork into measurement. Concretely: get the classified-answer
path (`questions` then `profile --answers`) working end to end through the skill,
profile 10 to 15 real approaches into `profiles/`, and compute
the correlation matrix. That single artifact answers "how related are the axes"
with data, and everything here becomes actionable.
