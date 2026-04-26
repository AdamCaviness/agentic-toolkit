# AGENTS.md

## `skills/` is distribution, not local config

Every `skills/<name>/` is public API. All three harnesses discover the same `SKILL.md` content; each has its own install mechanism (see README). Edits go live on the next release, so treat them accordingly.

## Skills

Never duplicate a skill into a harness-specific subtree. All three harnesses auto-discover `skills/<name>/SKILL.md`. The `model` frontmatter key is honored by Claude Code and ignored by Codex and Gemini.

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

## Commits and releases

- Only `feat:` (minor) and `fix:` (patch) drive a release PR. Other conventional types are silently ignored by release-please for bump purposes. Use `feat(skill):` scopes to classify new skills.
- Never hand-edit `version` in any manifest. Release-please bumps via JSONPath.
- Never manually tag. Release-please tags when its release PR merges.

## Attribution

Ported skills require an `ATTRIBUTIONS.md` next to `SKILL.md` with the source project's full license text.

## Style

- Commas, not em-dashes or hyphens, for punctuation.
- Document what **is**, not what **was**.
- No `Co-Authored-By` trailers.
- No TODOs in code.
