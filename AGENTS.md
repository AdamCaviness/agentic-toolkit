# AGENTS.md

## `skills/` is distribution, not local config

Every `skills/<name>/` is public API. Claude Code, Cursor, Codex, and Gemini discover the same `SKILL.md` content; each has its own install mechanism (see README). Edits go live on the next release, so treat them accordingly.

A shipped skill runs inside someone else's project, with none of this repository around it. It must therefore never cite this file. On an end user's machine the bare name `AGENTS.md` resolves to *their* project's file, not this one, so a citation points the reader at unrelated third-party text. For the high-risk path screen that is worse than a dead link: it would source a security control from a document the skill's own Untrusted Content Boundary classifies as untrusted.

The same applies to paths. A skill addresses a file it ships with relative to its own directory, never by repository path. `skills/code-review/reviewer-prompt.md` names nothing in the project a skill runs against; "the `reviewer-prompt.md` in the same directory as this SKILL.md" resolves everywhere, and a sibling skill is reached as `../<skill-name>/<file>`. The plugin layout `skills/<name>/` is stable across Claude Code, Cursor, Codex, and Gemini, so a sibling reference is safe; a repository-rooted one is not.

State the contract inside the skill and keep the rationale here. Shared content stays identical across copies because `tests/` asserts it verbatim, not because a skill tells the reader where the content came from. The one legitimate mention of `AGENTS.md` in a shipped skill is as one of the *target project's* convention files, listed beside `CLAUDE.md`, which means the user's own file and is the intended reading. The same applies to repository-only paths: `tests/`, `triage_shared/`, `docs/`, and `scripts/` do not exist in the project a skill is invoked against. `tests/test_distribution_boundary.py` enforces both rules.

## Skills

Never duplicate a skill into a harness-specific subtree. Claude Code, Cursor, Codex, and Gemini auto-discover `skills/<name>/SKILL.md`. The `model` frontmatter key is honored by Claude Code and ignored by Cursor, Codex, and Gemini.

## Dogfooding skills locally

`scripts/dev-link.sh` symlinks every `skills/<name>/` into project-level `.claude/skills/`, so Claude Code serves the live working-tree skills (bare-named, `/pr`) only while your cwd is this repo. They coexist with the global marketplace plugin's namespaced commands (`/agentic-toolkit:pr`), which stay pinned to the released version and remain the only commands visible in other projects. The script is idempotent: re-run it after adding a skill to link the new one and prune removed ones. `.claude/skills/` is gitignored. Creating it for the first time needs one Claude Code restart before the project skills are watched. To stop dogfooding: `rm -rf .claude/skills`.

## Deployment context for this repo

The skills in this repo are personal-machine tooling for an individual operator, not multi-user infrastructure. Threat models that assume shared hosts, shared `$TMPDIR`, untrusted local processes, network-exposed services, or supply-chain attackers reading per-user temp do not apply when triaging this codebase. Cached ticket bodies, project maps, and run state live in the operator's per-user temp (on macOS, `/var/folders/.../T/`, mode 700, owned by the operator) alongside `~/.ssh/`, `~/.aws/`, browser cookies, and keychain data the operating system already keeps private.

When `triage-architecture`, `triage-bugs`, or any other skill audits this repo, ground every security or robustness concern in this context. Hardening proposed with the framing "in case the cache is read by another user", "if `$TMPDIR` is shared", "if a co-tenant on the host", or "to defend against a local attacker" is out of scope and should be downgraded or rejected, not filed. Real concerns in this context look like: secrets actually committed to the repo, dependency CVEs that affect runtime behavior, public-API correctness bugs, data loss in the operator's own workflow, or footguns that turn into real bugs on a single-user machine.

This boundary is load-bearing for the triage skills' rejection-learning loop: when the operator closes a ticket as not-planned with reasoning grounded in this context, the triage skills cache that reasoning into `issues-closed.json` so future runs can recognize the same class of concern under a different title and skip refiling.

## User-only skills

Skills that should only be triggered by the user (not autonomously by the model) declare `disable-model-invocation: true` in frontmatter. This prevents the model from invoking the skill on its own initiative; the user must type the slash command explicitly. It does not restrict what the model does during execution. Currently honored by Claude Code and Cursor, tolerated by Codex and Gemini. Apply to skills with side effects or timing sensitivity where the user controls when they run: `pr`, `ship`, and `convert-worktree`. Add the key to any future skill the user should invoke deliberately rather than the model triggering automatically.

## Branch lifecycle

Workflow skills that compare against, sync with, or guard the default branch share one contract. Resolve the default branch into `BASE_BRANCH` with this snippet, then use `$BASE_BRANCH` in every command and prose mention:

```bash
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
if [ -z "$BASE_BRANCH" ]; then
  git rev-parse --verify main >/dev/null 2>&1 && BASE_BRANCH=main || BASE_BRANCH=master
fi
```

`BASE_BRANCH` is a branch *name*. It is not guaranteed to resolve as a ref. A single-branch clone has `origin/<base>` and no local `<base>`, so `git diff "$BASE_BRANCH"...HEAD` exits 128 there while the identical command against `origin/<base>` succeeds. Any block that walks a range therefore derives `BASE_REF` first and uses that:

```bash
BASE_REF="$BASE_BRANCH"
git rev-parse --verify "$BASE_REF" >/dev/null 2>&1 || BASE_REF="origin/$BASE_BRANCH"
git rev-parse --verify "$BASE_REF" >/dev/null 2>&1 || {
  printf 'base branch "%s" resolves neither locally nor on origin\n' "$BASE_BRANCH" >&2
  exit 1
}
```

Keep the two apart by what the command needs. A command that needs the *name* uses `$BASE_BRANCH`: `git checkout "$BASE_BRANCH"`, `git pull origin "$BASE_BRANCH"`, comparing the current branch against the default, and every prose mention. A command that walks a *range* uses `$BASE_REF`: `git rev-list --count "$BASE_REF..HEAD"`, `git diff "$BASE_REF"...HEAD`, `git log "$BASE_REF"..HEAD`. Mixing them inside one block is the bug this rule exists to prevent, since the verified ref sitting two lines above an unverified range reads as safe and is not.

Never hardcode `main` or `master` in skill commands, guards, diff ranges, or user-facing wording. Use "default branch" in prose. Skills that document the resolved default branch back to the user should print `$BASE_BRANCH`, not the literal word `main`.

Shell state does not persist between separate Bash tool invocations. Each skill must either re-resolve `BASE_BRANCH` at the top of every bash block that consumes it, or substitute the resolved literal branch name into the commands the agent runs (instead of letting `$BASE_BRANCH` expand in a fresh shell where it is unset). Do not assume a variable set in step N is still in scope in step N+1.

## High-risk path screen

Skills that publish to a remote, or that hand a change set to a reviewer, screen the path inventory for secret-shaped files with one shared regex. Carry it verbatim so a change to the pattern set lands everywhere at once:

```
(^|/)(\.env|\.npmrc|\.pypirc)(\.|/|$)|(^|/)id_(rsa|dsa|ecdsa|ed25519)([-_. 0-9][^/]*)?(\.|/|$)|(^|/)([^/]*[-_. ])?(credentials?|secrets?)([-_ ][^/.]*)?(/|$|\.(json|ya?ml|env|txt|ini|cfg|conf|toml|properties|xml|csv|tsv|pem|key|p12|enc)$)|\.(pem|p12|pfx|key|crt|sqlite3?|db3?|dump|env)(-(wal|shm|journal))?$
```

The fenced block that runs the screen resolves and verifies `BASE_BRANCH` itself, and never inherits it from an earlier block. Both ways of getting the base wrong fail silently in the same direction. An unset `BASE_BRANCH` reduces `"$BASE_BRANCH"...HEAD` to `...HEAD`, which compares HEAD with itself and prints nothing, and a `BASE_BRANCH` naming a branch the repository does not have makes `git diff` fail into the same empty output, which the trailing `|| true` then masks. Empty output reads as a clean inventory, so a gate that skipped the check would pass a committed secret through. The publishing skills therefore verify the base resolves before the diff, and stop rather than reporting clean. They check the local branch first and fall back to `origin/<base>`, because a single-branch clone has the remote-tracking ref without the local one, and stopping there would block a legitimate push. The reviewing skills reach the same base through `git merge-base`, which returns nothing when neither ref resolves; `code-review` stops there and `next-ticket` records `Review: skipped` and continues to its final report.

The `credentials` and `secrets` components take decoration on both sides, so the screen matches `aws-credentials.json`, `config/app-secrets.yaml`, `my_secret.txt`, and `client_secrets_v2.json`. The prose glob list this regex replaced matched those through `*credential*` and `*secret*`, and dropping them would have narrowed the gate while unifying it.

What keeps that breadth from blocking ordinary work is the terminator, not the decoration. A decorated component only matches when the path then ends, continues into a directory, or carries a data-bearing extension from the listed set. Source and documentation extensions are absent from that set, so `docs/managing-secrets.md`, `src/hooks/use-secrets.ts`, `src/secrets-manager.ts`, and `internal/aws_credentials_test.go` do not stop a push, while `k8s/base/db-credentials.yaml` and `aws-credentials.json` do. Trailing decoration also excludes dots, `([-_ ][^/.]*)?`, so it cannot swallow an extension and reach the end-of-path alternative. Adding a data extension to that list widens the gate; adding one that source files use would start blocking source files.

The SSH component covers `id_ecdsa` and `id_ed25519` alongside `id_rsa` and `id_dsa`, and accepts a suffix so `id_rsa2` and `deploy/id_rsa_backup` match. The extension group covers the SQLite sidecar files, `db.sqlite3-journal` and `data.db-shm`, which sit beside a matched database and hold the same rows.

The screen ends in `|| [ $? -eq 1 ]`, never `|| true`. `grep` exits 1 for "no matches", which is a clean result, and 2 for a failure such as an invalid pattern or an unreadable input. `|| true` flattens both to success and returns the same empty output, so a screen that never ran is indistinguishable from a screen that found nothing. That is the fail-open the gate exists to prevent, and it defeats the "a non-zero exit means the gate never ran" contract the surrounding prose relies on. Where the screen's output is captured into a variable rather than printed, the same rule applies through an explicit status check, since a failed command substitution otherwise leaves the variable empty and the reviewer is told there is nothing to look at.

`tests/test_high_risk_path_screen.py` asserts every skill that screens paths carries this literal, and runs the literal through `grep` against a list of paths it must match and a list it must leave alone, so a future widening cannot quietly start blocking ordinary source files. Before the validator existed the screen had drifted into two dialects: `pr`, `ship`, and `apply-review` used a prose glob list, while `code-review` and `next-ticket` used a wider regex. The publishing skills were screening for less than the reporting ones, which is backwards.

The validator also fails when a skill outside the two rosters contains `git push` or a screen fingerprint such as `id_rsa`. The rosters are hand-maintained, so without that check a skill added later could push without screening, or hand-roll its own pattern set, and every other assertion in the file would stay silent. `.npmrc` is deliberately not a fingerprint, since `update-deps` legitimately discusses npm registry configuration.

Disposition differs by skill, the pattern set does not. A publishing skill stops and makes the user confirm or remove the path. A reviewing skill passes the matches to the reviewer as `{HIGH_RISK_PATHS}` and never blocks.

Reviewing skills append three alternations after the shared literal: bare `token` and `key` path components, archives, and `.github/workflows/`. Those stay out of the publishing gate on purpose. A false positive costs a reviewer one glance, while a blocking gate that matches `src/auth/token.ts`, a release tarball, or a routine CI edit prompts the user on every single push. The shared literal still catches a real `server.key` or `id_rsa` through the extension group and the credential components.

## Capability glossary for public skills

Public skills are distributed to Claude Code, Cursor, Codex, and Gemini. Skill prose may use harness-specific tool names where they read naturally (`Task tool`, `WebSearch`, `Agent tool`); other harnesses generally infer the equivalent. This is a **glossary**, not a required vocabulary, that names recurring capabilities so future skills and adapter docs have a shared lexicon to reach for.

| Capability | What it provides |
| --- | --- |
| `project.instructions` | The project's own contributor instructions, found in `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`, or `GEMINI.md` depending on harness. |
| `ticket.read` | Read access to the project's ticket system (GitHub Issues, Jira, GitLab Issues, Azure Boards, Linear, etc.). |
| `ticket.write` | Create, update, comment on, or close tickets in the project's ticket system. |
| `subagent.dispatch` | Dispatch one isolated subagent with a fresh context, given a single prompt as its full instructions. |
| `subagent.dispatch.parallel` | Dispatch multiple isolated subagents in parallel from one orchestrator turn. |
| `web.research` | Fetch content from the public web (search engines, documentation, package registries, release notes). |
| `verification.run` | Execute the project's verification commands (tests, linters, formatters, type checks) and return their output. |

Two things *are* enforced in public skill bodies because they are concrete failure modes, not stylistic ones, and because untested abstraction would be a bigger regression risk than the current prose. The validator in `tests/test_capability_vocabulary.py` checks both:

- The literal Claude API parameter shape `subagent_type` and its value `general-purpose` must not appear. They are meaningless on Cursor, Codex, and Gemini, where no such parameter exists.
- Generated PR or commit output must not brand a single harness (no `Generated with [Claude Code]` trailer in PR body templates).

Frontmatter keys (`model:`, `disable-model-invocation:`) are allowed to stay harness-specific.

## Commits and releases

- Only `feat:` (minor) and `fix:` (patch) drive a release PR. Other conventional types are silently ignored by release-please for bump purposes. Use `feat(skill):` scopes to classify new skills.
- Never hand-edit `version` in any manifest. Release-please bumps via JSONPath.
- Never manually tag. Release-please tags when its release PR merges.

## Attribution

Ported skills require an `ATTRIBUTIONS.md` next to `SKILL.md` with the source project's full license text.

## Triage skills share one source

The `triage-architecture`, `triage-bugs`, and `triage-product` SKILL.md files are generated from `triage_shared/template.md` plus per-skill inputs in `triage_shared/skills.py`. The generated public files stay standalone so Claude Code, Cursor, Codex, and Gemini still discover `skills/<name>/SKILL.md`, but maintainers edit the shared mechanics (ticket-system detection, two-tier cache, untrusted-content boundary, cross-cluster notes, post-processing, cleanup, planner-state updates) in one place.

Do not hand-edit `skills/triage-architecture/SKILL.md`, `skills/triage-bugs/SKILL.md`, or `skills/triage-product/SKILL.md`. Edit `triage_shared/template.md` for shared mechanics or `triage_shared/skills.py` for per-skill policy, then run `python3 -m triage_shared.generate` to regenerate the public files. The `tests/test_triage_shared_source.py` validator refuses merges that bypass that flow.

## Style

- Commas, not em-dashes or hyphens, for punctuation.
- Document what **is**, not what **was**.
- No `Co-Authored-By` trailers.
- No TODOs in code.
