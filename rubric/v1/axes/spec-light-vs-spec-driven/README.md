# Spec-light vs Spec-driven

## Why this axis exists

How much written specification precedes code is a core methodology divide. Spec-driven front-loads a PRD or plan, powerful for complex or shared work and heavy for quick changes, while spec-light gets to code fast. Negative (`spec_light`) means jump to implementation, positive (`spec_driven`) means spec or plan first. `sd1` weighs whether a spec is required, `sd2` whether artifacts persist, and the measured `sd3` corroborates with specification vocabulary. This is distinct from interrogative-vs-opinionated: a tool can ask many questions to build a spec, making it both interrogative and spec-driven.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Spec-light vs Spec-driven)

Poles: `spec_light` (negative) to `spec_driven` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| sd1 | Is a written spec, PRD, or plan required before implementation? | classified | 3 | none -1, encouraged +0.3, required +1 |
| sd2 | Are spec or plan artifacts produced and persisted (not just discussed)? | classified | 2 | no -1, some +0.3, yes +1 |
| sd3 | Density of specification vocabulary across docs and commands. | measured | 2 | 7 terms, banded by count |
<!-- END GENERATED -->
