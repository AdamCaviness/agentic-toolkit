# Rubric changelog (v1 major line)

All changes to the measurement standard are recorded here. Version bump rules are in `docs/versioning.md`. One directory per MAJOR version, minor and patch changes are git history within it.

Status: this rubric is an initial work in progress and nothing has settled. The `v1/` directory and these version numbers exist to afford versioning once the standard stabilizes, they are not strict release boundaries yet, and no profiles have been published. Entries below record what changed and whether it moves scores; the strict "any score move is a MAJOR bump" discipline takes full effect once the rubric settles and profiles are published, not during this phase.

## 1.4.0

Added a `path_count` measured signal and used it to fix two non-discriminating indicators found while profiling four frameworks under 1.3.0.

- **New `path_count` signal.** Bands the number of files matching a set of globs, so a large modular collection reads differently from a small one, the resolution binary `path_presence` lacks. Additive: `path_presence` stays for genuinely binary cases. It reuses the shared band shape and glob matcher and unresolves on an empty target, like the other measured signals.
- **prescriptive-vs-composable `pc3`** moved from binary `path_presence` to `path_count` over the same globs. Under 1.3.0, BMAD-METHOD and gsd-plugin tied at +1.7 because the binary signal was present for both; by module count they now separate (BMAD +0.9 from 11 matching files, gsd +2.3 from 106).
- **solo-vs-team** gained a measured `path_count` indicator (`st4`) for team and CI infrastructure (workflows, code owners, PR templates), breaking the exact four-way tie at +4.0. Its classified indicators still answer alike across the sampled tools, which are all individual skill libraries with light review workflow, so the axis stays clustered; a classified redesign and a strongly team-oriented sample tool are the next step.

Measured-only change, so committed answer sets re-score without re-answering. Saturation stays at 0%. Bumps rubric_version to 1.4.0.

## 1.3.0

Recalibrated indicator values across all 13 axes to stop pole saturation. A four-way profile (agentic-toolkit, superpowers, BMAD-METHOD, gsd-plugin) clamped 28% of axis positions to ±10; measured indicators resolved to exactly ±1.0 89% of the time, and axes carry only 2-3 indicators, so a single maxed measured signal plus one strong classified answer pinned an axis. This is a value-only recalibration: indicator ids, questions, kinds, weights, terms, globs, metrics, and band thresholds (`max_count`) are unchanged.

- Measured `vocabulary`, `git_stats`, and `github_api` band values scaled by 0.8, so a maxed measured proxy contributes at most ±0.8 and can no longer alone pin an axis.
- Measured `path_presence` softened to present +0.6 / absent -0.6: a single glob hit is suggestive, not a full pole vote.
- Classified answer values on the three chronic saturators (small-scope-vs-large-scope, generalist-vs-specialist, spec-light-vs-spec-driven) scaled by 0.8, so their strongest option stops being a guaranteed +1.

Result: saturation drops from 28% to 0% across the four profiled frameworks while axis direction and cross-tool spread are preserved. This moves scores; once the rubric settles this class of change is a MAJOR bump, recorded here during the WIP phase.

Known non-discriminating indicators remain for a follow-up: `path_presence` globs that match the whole category (for example prescriptive-vs-composable `pc3`, present for every skills-based tool) act as a constant bias rather than a signal, and solo-vs-team's indicators do not separate the profiled tools. The fix is a count-based path signal and redesigned indicators, not a value change.

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
