# Interrogative vs Opinionated

## Why this axis exists

This axis captures how an approach reaches decisions, which is largely a matter of taste and team culture rather than quality. Some developers want a tool that interrogates them, drawing out requirements through questions before writing anything. Others want a tool that already has a strong opinion and just drives. Neither is better, they suit different people and moments.

Negative (`interrogative`) means the approach elicits and defers to the user. Positive (`opinionated`) means it prescribes a strong default path. `io1` detects an explicit questioning or brainstorming phase, `io2` detects an enforced pipeline, and the measured `io3` reads directive vocabulary density as corroboration.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Interrogative vs Opinionated)

Poles: `interrogative` (negative) to `opinionated` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| io1 | Does it run a questioning or brainstorming phase before writing code? | classified | 3 | yes -1, partial -0.5, no +0.5 |
| io2 | Does it enforce a fixed prescribed pipeline the user is expected to follow? | classified | 3 | strict +1, guided +0.3, loose -0.5 |
| io3 | Density of directive vocabulary (must, always, never, required, enforce) in instructions. | measured | 2 | 6 terms, banded by count |
<!-- END GENERATED -->
