# Rubric changelog (v1 major line)

All changes to the measurement standard are recorded here. Version bump rules are in `docs/versioning.md`. One directory per MAJOR version, minor and patch changes are git history within it.

Status: this rubric is an initial work in progress and nothing has settled. The `v1/` directory and these version numbers exist to afford versioning once the standard stabilizes, they are not strict release boundaries yet, and no profiles have been published. Entries below record what changed and whether it moves scores; the strict "any score move is a MAJOR bump" discipline takes full effect once the rubric settles and profiles are published, not during this phase.

## 1.2.0

Two changes to how axes are scored and displayed.

- **Scale is now a rubric-wide constant.** Moved `scale` from a per-axis field to a single value in `rubric.yaml` (`scale: 10`), removed from `axis.schema.json`, added to `rubric.schema.json`. No score moves: scale is only a display multiplier on the normalized weighted mean and every axis already used `10`. A shared scale is what keeps positions comparable across axes, so a per-axis knob was an unused degree of freedom that could only break comparability. The engine still carries `scale` per axis internally, populated from the manifest at load time.
- **Vocabulary signals match whole tokens, not substrings.** A term like `spec` no longer matches inside `specification`, nor `ci` inside `decision`. This is a correctness fix, but it does move measured scores for identical evidence: counts drop for short or inflectable terms, so banded values and axis positions can shift. Once the rubric settles this class of change is a MAJOR bump; during this WIP phase it is recorded here rather than treated as a comparability boundary.

## 1.1.0

Added the **fresh-vs-mature** axis (context group, after generalist-vs-specialist). MINOR because it introduces a whole new axis and leaves every existing axis score untouched for identical evidence.

Its indicators lean on two new measured signal types, `git_stats` (repository age, commit count, contributor count, tag count) and `github_api` (stars), both banded to a value the same way `vocabulary` counts are. Five of its six indicators are measured, so the axis scores meaningfully with no model in the loop; this is what made it worth shipping now, since the reason it was deferred from 1.0.0 was that a classified-only maturity axis would be weak. The single classified indicator reads how the project describes its own stability. Host facts that vary over time (stars) record the fetched value verbatim as evidence and resolve to unresolved (counted against coverage) when there is no network or origin remote.

Bands are a first proposal calibrated to open-source norms and, like all v1 weights, are expected to be contested before this rubric is treated as stable.

## 1.0.0

Initial curated rubric of 12 axes, grouped for a readable radar:

- Context: greenfield-vs-brownfield, small-scope-vs-large-scope, prototype-vs-production, solo-vs-team, generalist-vs-specialist
- Style: interrogative-vs-opinionated, autonomous-vs-human-in-loop
- Process: spec-light-vs-spec-driven, test-optional-vs-test-first
- Architecture: single-agent-vs-multi-agent, prescriptive-vs-composable
- Footprint: lightweight-vs-heavyweight

Curation notes. Implementation-first-vs-planning-first was dropped as a near-duplicate of spec-light-vs-spec-driven. Fresh-vs-mature is deferred until git and host-API evidence collectors exist, because a classified-only maturity axis would be weak. Magic-vs-mechanical, informal-vs-ceremonial, fast-start-vs-high-setup, and the audience axes are deferred as too correlated with existing axes to add signal yet. Model-agnostic-vs-model-specific, permissive-vs-guardrailed, stateless-vs-stateful, conversational-vs-command-driven, single-pass-vs-review-looped, and bare-vs-integration-heavy are backlog candidates.

Sign conventions, weights, and answer-to-value mappings are a first proposal and are expected to change before this rubric is treated as stable. Any change that can move a score for identical evidence bumps the MAJOR version.
