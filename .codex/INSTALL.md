# Installing Agentic Toolkit for Codex

Install from [agentic-marketplace](https://github.com/adamcaviness/agentic-marketplace). Codex loads the plugin (all 13 skills) from `.codex-plugin/plugin.json`. Use **exactly one** path, or skills appear twice.

If you previously linked the skills into `~/.agents/skills/` (path 3), remove those links before installing from the marketplace (desktop or CLI) with the uninstall steps in the [manual install](../README.md#installation). If `~/.agents/skills/agentic-toolkit` exists as a single link to the whole `skills/` directory, remove it with `rm ~/.agents/skills/agentic-toolkit`.

## 1. ChatGPT desktop (recommended)

1. Open **Plugins** → **Add plugin marketplace**.
2. Source: `adamcaviness/agentic-marketplace` (not `github.com/...`).
3. Git ref: `main`.
4. Sparse paths: leave empty.
5. Add the marketplace, then install **agentic-toolkit**.
6. Restart ChatGPT / Codex if the plugin does not appear, then start a new chat.

## 2. Codex CLI (optional)

```bash
codex plugin marketplace add adamcaviness/agentic-marketplace --ref main
codex plugin add agentic-toolkit@agentic-marketplace
```

The same commands work in PowerShell. List with `codex plugin list --marketplace agentic-marketplace`. Remove with `codex plugin remove agentic-toolkit@agentic-marketplace`.

## 3. Manual fallback (clone and link)

Use this only if you cannot add a marketplace. Do **not** combine it with path 1 or 2.

Follow the [manual install](../README.md#installation) with the `~/.agents/skills/` root. It covers macOS, Linux, and Windows, plus update and uninstall. Restart Codex afterwards.

Codex reads `~/.agents/skills/`. Do not use `~/.codex/skills/`, which Codex has deprecated and still reads, so skills in both places load twice.

> **Also use Cursor or Gemini CLI?** Both read `~/.agents/skills/` too, so the manual links already serve them. Do not also install the Cursor plugin or the Gemini extension on top of those links. For dual Claude Code and Cursor setups, prefer the paths in [.cursor/INSTALL.md](../.cursor/INSTALL.md).
