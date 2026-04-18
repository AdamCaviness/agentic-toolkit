# AGENTS.md

## `skills/` is distribution, not local config

Every `skills/<name>/` is public API. All three harnesses discover the same `SKILL.md` content; each has its own install mechanism (see README). Edits go live on the next release, so treat them accordingly.

## Skills

Never duplicate a skill into a harness-specific subtree. All three harnesses auto-discover `skills/<name>/SKILL.md`. The `model` frontmatter key is honored by Claude Code and ignored by Codex and Gemini.

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
