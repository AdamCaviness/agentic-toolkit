# Solo vs Team

## Why this axis exists

Whether an approach assumes one developer or many changes its coordination overhead entirely. A solo developer does not want claiming, assignment, and handoff ceremony, and a team is hampered without it. Negative (`solo`) means built for one, positive (`team`) means multi-contributor and team-safe. `st1` weighs collaboration safety most, `st2` captures handoffs between people, and the measured `st3` corroborates with team vocabulary.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Solo vs Team)

Poles: `solo` (negative) to `team` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| st1 | Does it provide team-safe collaboration (claiming or assigning work, avoiding conflicts between contributors)? | classified | 3 | none -1, partial +0.2, strong +1 |
| st2 | Are there defined handoffs between people or human reviewers? | classified | 2 | none -1, some +0.3, many +1 |
| st3 | Density of team-collaboration vocabulary across docs and commands. | measured | 2 | 7 terms, banded by count |
<!-- END GENERATED -->
