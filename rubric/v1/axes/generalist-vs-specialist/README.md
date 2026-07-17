# Generalist vs Specialist

## Why this axis exists

Some approaches claim any domain (BMAD markets business and wellness uses), while most specialize in software. This matters if your work is not code, or if you specifically want software-aware machinery. Negative (`generalist`) means domain-agnostic, positive (`specialist`) means software delivery specifically. `gs1` weighs the framing most, `gs2` checks for explicit broad claims, and the measured `gs3` corroborates with software vocabulary density.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Generalist vs Specialist)

Poles: `generalist` (negative) to `specialist` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| gs1 | Is it framed for any domain, or specifically for software engineering? | classified | 3 | any_domain -0.8, mostly_software +0.4, software_only +0.8 |
| gs2 | Does it explicitly claim applicability beyond code (business, writing, wellness)? | classified | 1 | yes_broad -0.8, some +0, no +0.8 |
| gs3 | Density of software-specific vocabulary across docs and commands. | measured | 2 | 7 terms, banded by count |
<!-- END GENERATED -->
