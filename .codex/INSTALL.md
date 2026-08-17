# Installing Agentic Toolkit for Codex

Install from [agentic-marketplace](https://github.com/adamcaviness/agentic-marketplace). Codex loads the plugin (all 13 skills) from `.codex-plugin/plugin.json`. Use **exactly one** path, or skills appear twice.

## 1. ChatGPT desktop (recommended)

1. Open **Plugins** → **Add plugin marketplace**.
2. Source: `adamcaviness/agentic-marketplace` (not `github.com/...`).
3. Git ref: `main`.
4. Sparse paths: leave empty.
5. Add the marketplace, then install **agentic-toolkit**.
6. Restart ChatGPT / Codex if the plugin does not appear, then start a new chat.

If you previously cloned this repo and symlinked `skills/` into `~/.agents/skills/agentic-toolkit`, remove that link before installing from the marketplace:

```bash
rm ~/.agents/skills/agentic-toolkit
```

## 2. Codex CLI (optional)

```bash
codex plugin marketplace add adamcaviness/agentic-marketplace --ref main
codex plugin add agentic-toolkit@agentic-marketplace
```

List with `codex plugin list --marketplace agentic-marketplace`. Remove with `codex plugin remove agentic-toolkit@agentic-marketplace`.

## 3. Manual fallback (clone and symlink)

Use this only if you cannot add a marketplace. Do **not** combine it with path 1 or 2.

```bash
git clone https://github.com/adamcaviness/agentic-toolkit.git ~/.codex/agentic-toolkit
mkdir -p ~/.agents/skills
ln -s ~/.codex/agentic-toolkit/skills ~/.agents/skills/agentic-toolkit
```

**Windows (PowerShell):**

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\agentic-toolkit" "$env:USERPROFILE\.codex\agentic-toolkit\skills"
```

Restart Codex. Update with `git -C ~/.codex/agentic-toolkit pull`. Uninstall with `rm ~/.agents/skills/agentic-toolkit`.

> **Also use Cursor?** Cursor can load skills from `~/.agents/skills/` when third-party includes are on. Prefer the Claude Code or Cursor install paths in [.cursor/INSTALL.md](../.cursor/INSTALL.md) for dual Claude Code + Cursor setups, and do not stack a Cursor `~/.cursor/plugins/local` install on top of a Codex symlink for the same skills.
