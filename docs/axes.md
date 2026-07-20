# Axis authoring

## What an axis is

An axis is a signed spectrum between two named poles, with `0.0` as neutral balance. The sign indicates lean, the magnitude indicates strength of lean. The scale is symmetric (default `10`, so scores run `-10` to `+10`).

An axis is never "good vs bad." Both poles are legitimate design choices. The profile locates a tool so a reader can judge fit for their own context.

## How an axis is built

Do not score the axis directly. An axis is a **weighted scoring system over N measurements**. Decompose it into indicators, each a narrow question (one measurement) with a bounded answer that maps to a value in `[-1, 1]` signed toward one pole. Give each indicator a weight expressing its importance to the axis. The engine then folds those N measurements into the single signed position on the continuum:

```
axis_position = scale * sum(weight_i * measurement_i) / sum(weight_i)
```

The crafting of the axis is choosing the indicators and their weights. That craft lives entirely in the rubric, the engine only executes the arithmetic. A well built axis has enough indicators that no single one dominates, and enough `measured` indicators that a meaningful position exists even before any classification.

## Worked example: Greenfield vs Brownfield

Sign convention: negative pole = greenfield, positive pole = brownfield. A method that shines when starting from an idea and weakens on existing code lands strongly negative.

| id  | question                                                        | kind       | weight | maps to |
|-----|-----------------------------------------------------------------|------------|--------|---------|
| gb1 | First mandatory step generates a spec/PRD from an idea?         | classified | 3      | yes -1.0, partial -0.5, no 0.0 |
| gb2 | Ships explicit steps/agents for ingesting an existing codebase? | classified | 3      | yes +1.0, partial +0.5, no -0.5 |
| gb3 | Density of brownfield vocabulary in docs/commands               | measured   | 2      | none -1.0, some +0.3, heavy +1.0 |
| gb4 | Default unit of work: whole-project generation vs small diff    | classified | 2      | whole -1.0, mixed 0.0, small_diff +1.0 |
| gb5 | Onboarding assumes a new repo vs pointing at an existing one    | measured   | 1      | new_repo -1.0, either 0.0, existing +1.0 |

The full machine-readable form of this axis is in `rubric/v1/axes/greenfield-vs-brownfield/axis.yaml`, and its generated scoring block is in the sibling `README.md`.

## The axis catalog

The working catalog of candidate axes, grouped by the decision each helps a reader make (sign shown as `negative ↔ positive`). Axes marked **[v1]** ship in the current rubric, the rest are backlog, because heavily correlated axes dilute a profile rather than sharpen it. Example indicators are illustrative, the authoritative definitions live in `rubric/v1/axes/*/axis.yaml`.

### A. Interaction and control style (how you drive it)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Interrogative ↔ Opinionated** **[v1]** | Elicits and asks vs prescribes a strong default path | brainstorming phase present, directive vocabulary density, fixed pipeline enforced |
| **Human-in-loop ↔ Autonomous** **[v1]** | Frequent checkpoints vs unattended autopilot | approval-between-phases, autopilot mode advertised, checkpoint vocabulary density |
| **Conversational ↔ Command-driven** | Free chat vs slash commands and structured invocation | command/skill count, ratio of prose docs to command specs |
| **Permissive ↔ Guardrailed** | Runs freely vs guards destructive actions | confirmation gates on destructive ops, safety language, dry-run defaults |
| **Magic ↔ Mechanical** | Hides steps for low cognitive load vs exposes every step for control and auditability | visibility of intermediate artifacts, explicit phase logs, hidden automation |

### B. Project and context fit (what it is for)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Greenfield ↔ Brownfield** **[v1]** | Excels from an idea vs excels inside an existing codebase | spec-from-idea first step, codebase-ingestion steps, brownfield vocabulary, small-diff default |
| **Small-scope ↔ Large-scope** **[v1]** | One task vs the whole delivery lifecycle | phases covered (idea to release), single-command vs multi-stage, role coverage |
| **Prototype ↔ Production** **[v1]** | Fast throwaway output vs production hardening | testing and review emphasis, CI/deploy awareness, "vibe" vs "production" language |
| **Solo ↔ Team** **[v1]** | Single developer vs multi-contributor and team-safe | claim/assignment safety, shared state, review handoffs, role personas |
| **Generalist ↔ Specialist** **[v1]** | Any domain vs software delivery specifically | domain-agnostic framing vs code-specific tooling and vocabulary |
| **Fresh ↔ Mature** **[v1]** | New, fast-moving, cutting-edge vs established, stable, battle-tested | repository age, commit count, contributor count, release-tag cadence, stars |

### C. Process and methodology (how it works)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Spec-light ↔ Spec-driven** **[v1]** | Jumps to code vs plans and specs first | mandatory PRD/plan step, spec artifacts, plan-before-code enforcement |
| **Test-optional ↔ Test-first** **[v1]** | Testing incidental vs TDD enforced | red-green-refactor language, test-first gates, coverage expectations |
| **Informal ↔ Ceremonial** | Minimal ritual vs roles, phases, and agile ceremony | named roles/personas, phase gates, ceremony vocabulary |
| **Single-pass ↔ Review-looped** | One shot vs built-in critique and iteration | self-review/critic steps, iteration loops, verification stages |
| **Implementation-first ↔ Planning-first** | Starts building vs invests up front in planning | ordering of first actions, depth of planning artifacts |

### D. Architecture and mechanics (how it is built)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Single-agent ↔ Multi-agent** **[v1]** | One conversation vs specialized subagents or personas | subagent usage, persona definitions, orchestration layer |
| **Prescriptive ↔ Composable** **[v1]** | Fixed pipeline vs pick-and-choose parts | modular skill count, optional vs required steps, dependency between steps |
| **Stateless ↔ Stateful** | No memory vs persistent project state and memory | memory files, cross-session state, project-state backing store |
| **Monolithic-context ↔ Context-partitioned** | One long session vs fresh-context phases | fresh-context spawning, per-phase context isolation, context-rot mitigation |
| **Bare ↔ Integration-heavy** | Few dependencies vs many MCP servers, hooks, and tools | MCP/hook/integration count, external tool requirements |

### E. Cost, footprint, and portability (what it takes to run)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Lightweight ↔ Heavyweight** **[v1]** | Small footprint and little ceremony vs large and elaborate | file count, install steps, config surface, concepts to learn |
| **Context-frugal ↔ Context-hungry** | Token disciplined vs consumes large context | fresh-context patterns, prompt sizes, token-saving mechanisms |
| **Model-agnostic ↔ Model-specific** | Portable across agents vs tied to one host | multi-host support, Claude-only features, portability claims |
| **Fast-start ↔ High-setup** | Useful immediately vs significant setup before value | steps to first useful run, prerequisites, configuration required |

### F. Audience and learnability (who it is for)

| Axis | Meaning: negative ↔ positive | Example indicators |
|---|---|---|
| **Beginner-friendly ↔ Expert-oriented** | Gentle on-ramp vs assumes expertise | onboarding quality, jargon density, worked examples |
| **Low-config ↔ Highly-configurable** | Works out of the box vs extensive knobs | default coverage, number of configuration options, extension points |

`rubric/v1/axes/*/axis.yaml` is the authoritative source for the shipped axes, this catalog is the map.

Some axes need evidence collectors beyond the defaults. Fresh↔Mature, for example, uses the `git_stats` (age, commit count) and `github_api` (stars) collectors that were added for it. Adding a collector is an engine change, and it only affects scores once a rubric actually uses it.

## Authoring checklist

- Both poles are legitimate, neither is framed as the failure mode.
- Both poles have a plain-language `explain` meaning (one sharp sentence each), so the report can teach a reader what the pole words mean. The neutral middle is explained once by the renderer, not per axis, because it means the same thing on every axis.
- At least one `measured` indicator, so the axis is not fully dependent on classification.
- Every `classified` indicator has a small, mutually exclusive, defined answer set.
- Weights are integers and their intent is documented in the rubric `description`.
- Adding or reweighting an indicator triggers a MAJOR rubric bump. See `docs/versioning.md`.

## Planned calibration: vocabulary signals are weak priors

Eleven of the v1 axes lean on a single `vocabulary` word-count as their only measured
indicator. A word-count measures how much a project *talks about* a topic, not whether it
*practices* it, so it over-fires on meta-tooling whose content is itself about agentic
process (`sd3` scored agentic-toolkit maximally spec-driven off 121 mentions of
`plan`/`spec`, while the project ships no spec files). This is tolerable today because the
report's coverage floor stops a lone vocabulary hit from rendering as a position, and
because the intended experience resolves the classified indicators (which carry the real
weight) through the skill, leaving vocabulary a minor prior.

The planned fix, for the calibration pass that accompanies the first curated-profile
corpus: where a structural artifact genuinely signals the practice, convert the
`vocabulary` indicator to `path_presence` (spec-driven → a `specs/` tree or PRD
templates; test-first → test directories plus CI config; production → CI/deploy/
observability config). Where no structural proxy exists (for example the tone of
interrogative-vs-opinionated), move the judgment into a `classified` indicator, which the
skill answers for free, rather than approximating it with a word-count. Both are MAJOR
rubric changes and go through `rubric/CHANGELOG.md` with a rationale.
