# Prescriptive vs Composable

## Why this axis exists

Whether an approach is a fixed pipeline or a toolbox of parts determines how much it bends to your process. Prescriptive gives a proven path with less freedom, composable lets you pick and reorder. Negative (`prescriptive`) means fixed pipeline, positive (`composable`) means modular parts. `pc1` weighs the overall shape, `pc2` whether steps are mandatory and ordered, and the measured `pc3` detects many independent skill or module files. This is distinct from interrogative-vs-opinionated: composability is about modularity, not directiveness.

<!-- BEGIN GENERATED: do not edit below, run `make docs` -->
### Scoring (Prescriptive vs Composable)

Poles: `prescriptive` (negative) to `composable` (positive). Scale ±10.

Position is a weighted mean of 3 indicator measurements:

```
axis_position = 10 * sum(weight * measurement) / sum(weight)
```

| id | question | kind | weight | maps to |
|---|---|---|---|---|
| pc1 | Is it a fixed pipeline you follow, or modular parts you compose? | classified | 3 | fixed_pipeline -1, mixed +0, composable +1 |
| pc2 | Are steps mandatory and ordered, or optional and reorderable? | classified | 2 | mandatory_ordered -1, mixed +0, optional_reorderable +1 |
| pc3 | Presence of many independent skill or module files. | measured | 2 |  |
<!-- END GENERATED -->
