# Single-agent vs Multi-agent

## Why this axis exists

Internal structure, one conversation versus many specialized subagents or personas, affects context hygiene, cost, and how the approach reasons. Neither is better: multi-agent can decompose big problems but adds orchestration overhead. Negative (`single_agent`) means one agent, positive (`multi_agent`) means orchestrated specialists. `ma1` weighs orchestration most, and the two measured indicators (`ma2` vocabulary, `ma3` agent-definition files) give the axis real signal even before classification.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Single-agent vs Multi-agent)

Poles: `single_agent` (negative) to `multi_agent` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| ma1 | Does it orchestrate multiple specialized subagents or personas? | classified | 3 | single -1, some +0.3, many +1 |
| ma2 | Density of multi-agent vocabulary across docs and commands. | measured | 2 | 6 terms, banded by count |
| ma3 | Presence of agent or persona definition files. | measured | 1 | present +1, absent -1 |
<!-- END GENERATED -->
