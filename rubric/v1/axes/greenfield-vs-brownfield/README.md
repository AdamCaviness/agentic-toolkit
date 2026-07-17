# Greenfield vs Brownfield

## Why this axis exists

The single biggest predictor of whether an approach will help or frustrate is whether your work is greenfield or brownfield. Greenfield methods front-load spec and product generation and assume they own the whole tree. Brownfield methods assume a large existing codebase they must read, respect, and change surgically. A tool tuned for one is often actively painful for the other, so this axis is usually the first one a reader should consult.

Negative (`greenfield`) means the approach shines starting from an idea with no product yet. Positive (`brownfield`) means it shines inside an existing codebase. The two heaviest indicators (`gb1`, `gb2`) capture the defining behaviors: does it insist on generating a spec from scratch, and does it ship real machinery for ingesting existing code. The measured indicators (`gb3`, `gb5`) corroborate with vocabulary and structure so the position does not rest entirely on judgment.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Greenfield vs Brownfield)

Poles: `greenfield` (negative) to `brownfield` (positive). Scale ±10.

Position is a weighted mean of 5 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| gb1 | Is the first mandatory step generating a spec or PRD from an idea, assuming no product exists yet? | classified | 3 | yes -1, partial -0.5, no +0 |
| gb2 | Does it ship explicit steps or agents for ingesting and mapping an existing codebase? | classified | 3 | yes +1, partial +0.5, no -0.5 |
| gb3 | Density of brownfield vocabulary across docs and commands. | measured | 2 | 6 terms, banded by count |
| gb4 | Is the default unit of work whole-project generation or a targeted small diff? | classified | 2 | whole_project -1, mixed +0, small_diff +1 |
| gb5 | Does onboarding assume a brand new repo, or point at an existing one? | measured | 1 | present +0.6, absent -0.6 |
<!-- END GENERATED -->
