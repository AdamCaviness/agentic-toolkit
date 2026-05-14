# AGENTS.md

## `skills/` is distribution, not local config

Every `skills/<name>/` is public API. All three harnesses discover the same `SKILL.md` content; each has its own install mechanism (see README). Edits go live on the next release, so treat them accordingly.

## Skills

Never duplicate a skill into a harness-specific subtree. All three harnesses auto-discover `skills/<name>/SKILL.md`. The `model` frontmatter key is honored by Claude Code and ignored by Codex and Gemini.

## Deployment context for this repo

The skills in this repo are personal-machine tooling for an individual operator, not multi-user infrastructure. Threat models that assume shared hosts, shared `$TMPDIR`, untrusted local processes, network-exposed services, or supply-chain attackers reading per-user temp do not apply when triaging this codebase. Cached ticket bodies, project maps, and run state live in the operator's per-user temp (on macOS, `/var/folders/.../T/`, mode 700, owned by the operator) alongside `~/.ssh/`, `~/.aws/`, browser cookies, and keychain data the operating system already keeps private.

When `triage-architecture`, `triage-bugs`, or any other skill audits this repo, ground every security or robustness concern in this context. Hardening proposed with the framing "in case the cache is read by another user", "if `$TMPDIR` is shared", "if a co-tenant on the host", or "to defend against a local attacker" is out of scope and should be downgraded or rejected, not filed. Real concerns in this context look like: secrets actually committed to the repo, dependency CVEs that affect runtime behavior, public-API correctness bugs, data loss in the operator's own workflow, or footguns that turn into real bugs on a single-user machine.

This boundary is load-bearing for the triage skills' rejection-learning loop: when the operator closes a ticket as not-planned with reasoning grounded in this context, the triage skills cache that reasoning into `issues-closed.json` so future runs can recognize the same class of concern under a different title and skip refiling.

## User-only skills

Skills that should only be triggered by the user (not autonomously by the model) declare `disable-model-invocation: true` in frontmatter. This prevents the model from invoking the skill on its own initiative; the user must type the slash command explicitly. It does not restrict what the model does during execution. Currently honored by Claude Code, tolerated by Codex and Gemini. Apply to skills with side effects or timing sensitivity where the user controls when they run: `pr`, `ship`, and `convert-worktree`. Add the key to any future skill the user should invoke deliberately rather than the model triggering automatically.

## Branch lifecycle

Workflow skills that compare against, sync with, or guard the default branch share one contract. Resolve the default branch into `BASE_BRANCH` with this snippet, then use `$BASE_BRANCH` in every command and prose mention:

```bash
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
if [ -z "$BASE_BRANCH" ]; then
  git rev-parse --verify main >/dev/null 2>&1 && BASE_BRANCH=main || BASE_BRANCH=master
fi
```

Never hardcode `main` or `master` in skill commands, guards, diff ranges, or user-facing wording. Use "default branch" in prose. The ahead-of-base check is `git rev-list --count "$BASE_BRANCH..HEAD"`. The diff range for a feature branch is `"$BASE_BRANCH"...HEAD`. The post-merge sync is `git checkout "$BASE_BRANCH" && git pull origin "$BASE_BRANCH"`. The remote-tracking reference is `"origin/$BASE_BRANCH"`. Skills that document the resolved default branch back to the user should print `$BASE_BRANCH`, not the literal word `main`.

Shell state does not persist between separate Bash tool invocations. Each skill must either re-resolve `BASE_BRANCH` at the top of every bash block that consumes it, or substitute the resolved literal branch name into the commands the agent runs (instead of letting `$BASE_BRANCH` expand in a fresh shell where it is unset). Do not assume a variable set in step N is still in scope in step N+1.

## Capability glossary for public skills

Public skills are distributed to Claude Code, Codex, and Gemini. Skill prose may use harness-specific tool names where they read naturally (`Task tool`, `WebSearch`, `Agent tool`); other harnesses generally infer the equivalent. This is a **glossary**, not a required vocabulary, that names recurring capabilities so future skills and adapter docs have a shared lexicon to reach for.

| Capability | What it provides |
| --- | --- |
| `project.instructions` | The project's own contributor instructions, found in `CLAUDE.md`, `AGENTS.md`, or `GEMINI.md` depending on harness. |
| `ticket.read` | Read access to the project's ticket system (GitHub Issues, Jira, GitLab Issues, Azure Boards, Linear, etc.). |
| `ticket.write` | Create, update, comment on, or close tickets in the project's ticket system. |
| `subagent.dispatch` | Dispatch one isolated subagent with a fresh context, given a single prompt as its full instructions. |
| `subagent.dispatch.parallel` | Dispatch multiple isolated subagents in parallel from one orchestrator turn. |
| `web.research` | Fetch content from the public web (search engines, documentation, package registries, release notes). |
| `verification.run` | Execute the project's verification commands (tests, linters, formatters, type checks) and return their output. |

Two things *are* enforced in public skill bodies because they are concrete failure modes, not stylistic ones, and because untested abstraction would be a bigger regression risk than the current prose. The validator in `tests/test_capability_vocabulary.py` checks both:

- The literal Claude API parameter shape `subagent_type` and its value `general-purpose` must not appear. They are meaningless on Codex and Gemini, where no such parameter exists.
- Generated PR or commit output must not brand a single harness (no `Generated with [Claude Code]` trailer in PR body templates).

Frontmatter keys (`model:`, `disable-model-invocation:`) are allowed to stay harness-specific.

## Commits and releases

- Only `feat:` (minor) and `fix:` (patch) drive a release PR. Other conventional types are silently ignored by release-please for bump purposes. Use `feat(skill):` scopes to classify new skills.
- Never hand-edit `version` in any manifest. Release-please bumps via JSONPath.
- Never manually tag. Release-please tags when its release PR merges.

## Attribution

Ported skills require an `ATTRIBUTIONS.md` next to `SKILL.md` with the source project's full license text.

## Triage skills share one source

The `triage-architecture`, `triage-bugs`, and `triage-product` SKILL.md files are generated from `triage_shared/template.md` plus per-skill inputs in `triage_shared/skills.py`. The generated public files stay standalone so all three harnesses still discover `skills/<name>/SKILL.md`, but maintainers edit the shared mechanics (ticket-system detection, two-tier cache, untrusted-content boundary, cross-cluster notes, post-processing, cleanup, planner-state updates) in one place.

Do not hand-edit `skills/triage-architecture/SKILL.md`, `skills/triage-bugs/SKILL.md`, or `skills/triage-product/SKILL.md`. Edit `triage_shared/template.md` for shared mechanics or `triage_shared/skills.py` for per-skill policy, then run `python3 -m triage_shared.generate` to regenerate the public files. The `tests/test_triage_shared_source.py` validator refuses merges that bypass that flow.

## Style

- Commas, not em-dashes or hyphens, for punctuation.
- Document what **is**, not what **was**.
- No `Co-Authored-By` trailers.
- No TODOs in code.
