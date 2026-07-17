# Lightweight vs Heavyweight

## Why this axis exists

How much a user must learn and install before getting value is a real adoption cost. Lightweight tools pay off immediately, heavyweight tools ask for concepts, roles, and setup first, which can be worth it for large efforts. Negative (`lightweight`) means small footprint and little ceremony, positive (`heavyweight`) means many concepts and steps. `lw1` weighs concepts and ceremony most, `lw2` the install footprint, and the measured `lw3` corroborates with ceremony vocabulary.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Lightweight vs Heavyweight)

Poles: `lightweight` (negative) to `heavyweight` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| lw1 | How many concepts and how much ceremony must a user learn before getting value? | classified | 3 | minimal -1, moderate +0.2, heavy +1 |
| lw2 | How large is the install and setup footprint? | classified | 2 | tiny -1, moderate +0, large +1 |
| lw3 | Density of ceremony vocabulary across docs and commands. | measured | 2 | 8 terms, banded by count |
<!-- END GENERATED -->
