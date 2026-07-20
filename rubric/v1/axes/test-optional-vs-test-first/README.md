# Test-optional vs Test-first

## Why this axis exists

Whether testing is enforced up front (TDD) or left to the user is both a quality and a taste decision. Test-first suits teams and production code and can feel heavy during exploration. Negative (`test_optional`) means incidental testing, positive (`test_first`) means enforced TDD. `tf1` weighs enforcement most, `tf2` whether testing is a first-class phase, and the measured `tf3` corroborates with test-first vocabulary.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Test-optional vs Test-first)

Poles: `test_optional` (negative) to `test_first` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| tf1 | Does it enforce writing tests before implementation (TDD)? | classified | 3 | no -1, encouraged +0.3, enforced +1 |
| tf2 | Is testing a first-class phase, or incidental? | classified | 1 | incidental -1, present +0.3, first_class +1 |
| tf3 | Density of test-first vocabulary across docs and commands. | measured | 2 | 7 terms, banded by count |
<!-- END GENERATED -->
