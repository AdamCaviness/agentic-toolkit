# Small-scope vs Large-scope

## Why this axis exists

How much of the delivery lifecycle an approach spans is a practical fit question. A single-task helper is perfect for a quick change and obstructive when driving a whole project, and the reverse is true for a full-lifecycle framework. Negative (`small_scope`) means one focused task, positive (`large_scope`) means idea-to-release coverage. `sl1` (phase coverage) carries the most weight because it measures span directly, `sl2` separates a one-shot command from a pipeline, and the measured `sl3` corroborates with lifecycle vocabulary.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Small-scope vs Large-scope)

Poles: `small_scope` (negative) to `large_scope` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| sl1 | How many lifecycle phases does it cover (idea, spec, plan, implement, test, review, release)? | classified | 3 | one -0.8, few -0.24, most +0.48, full_lifecycle +0.8 |
| sl2 | Is it invoked as a single command or skill, or as a multi-stage pipeline? | classified | 2 | single -0.8, mixed +0, multi_stage +0.8 |
| sl3 | Density of lifecycle vocabulary across docs and commands. | measured | 2 | 7 terms, banded by count |
<!-- END GENERATED -->
