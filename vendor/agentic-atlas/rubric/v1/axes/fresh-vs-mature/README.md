# Fresh vs Mature

## Why this axis exists

Maturity reads like a magnitude (more stars, more commits, more age), but the rubric models it as a signed axis so it stays in the same family as every other slider and so both ends are framed as legitimate. Negative (`fresh`) means new, fast-moving, and cutting-edge: you get the newest ideas at the cost of churn and a thin track record. Positive (`mature`) means established, stable, and battle-tested: you get fewer surprises at the cost of inertia. A reader choosing an approach for a conservative production team and a reader chasing the latest technique want opposite ends of this axis, and both are making a sound choice.

This axis is the reason the `git_stats` and `github_api` collectors exist. Its weight sits deliberately on deterministic repository facts (`fm1` through `fm5` are all measured), so it produces a meaningful position with no model in the loop, which is exactly why a classified-only maturity axis was rejected during v1 curation. The single classified indicator (`fm6`) only nudges the position by reading how the project describes its own stability. The two host facts that vary over time (`fm5` stars) record the fetched value verbatim as evidence, and resolve to unresolved (counted against coverage) when there is no network or origin remote, so a partial run is never mistaken for a complete one.

Bands are a first proposal calibrated to open-source norms (roughly: under 6 months / 100 commits / 2 contributors reads as fresh, multi-year with a thousand-plus commits and a real release history reads as mature) and are expected to be contested before v1 is treated as stable.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Fresh vs Mature)

Poles: `fresh` (negative) to `mature` (positive). Scale ±10.

Position is a weighted mean of 6 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| fm1 | How old is the repository, from its first commit to HEAD? | measured | 2 | git age_days, banded by count |
| fm2 | How many commits has the repository accumulated? | measured | 2 | git commit_count, banded by count |
| fm3 | How many distinct contributors have committed? | measured | 1 | git contributor_count, banded by count |
| fm4 | How many release tags exist, as a proxy for an established release cadence? | measured | 1 | git tag_count, banded by count |
| fm5 | How much adoption does the host show, by star count? | measured | 2 | stars via GitHub API, banded by count |
| fm6 | How does the project describe its own stability in its docs? | classified | 2 | experimental -1, evolving +0, stable +1 |
<!-- END GENERATED -->
