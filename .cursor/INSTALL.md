# Installing Agentic Toolkit for Cursor

Cursor discovers skills from several places. Use **exactly one** of the paths below for this plugin, or every skill appears twice in **Customize → Skills** and under `/` in Agents.

| Your setup | What to do |
|---|---|
| You already use **Claude Code** with this plugin | Install once in Claude Code (path 1). Cursor picks it up automatically. Do **not** also install path 2. |
| **Cursor only** (individual plan: Hobby, Pro, Pro+, or Ultra) | Add the marketplace with the Cursor CLI, or clone into `~/.cursor/plugins/local` (path 2). |
| **Cursor Teams / Enterprise** admin | Import the marketplace from the web dashboard (path 3). Teammates install from **Customize**. |

Leave **Settings → Rules, Skills, Subagents → Include third-party Plugins, Skills, and other configs** enabled (the default) if you rely on path 1. Turning it off hides Claude Code and Codex skill roots from Cursor.

## 1. Via Claude Code (best if you use both)

In Claude Code:

```bash
/plugin marketplace add adamcaviness/agentic-marketplace
/plugin install agentic-toolkit@agentic-marketplace
```

Reload Cursor (**Developer: Reload Window**). Skills show under `/` in Agents and in **Customize → Skills**.

Stop here. Do not also install path 2, or link the skills into `~/.cursor/skills/` or `~/.agents/skills/`.

## 2. Cursor only (individual plan: Hobby, Pro, Pro+, or Ultra)

### 2a. Marketplace, with the Cursor CLI (recommended)

```bash
cursor-agent plugin marketplace add adamcaviness/agentic-marketplace
cursor-agent
```

Inside `cursor-agent`, type `/plugin`, open the **Marketplace** tab, select **agentic-toolkit**, and choose **user** scope so the plugin applies to every project. Reload the editor window and confirm in **Customize → Skills**.

The Cursor CLI has no non-interactive `plugin install` command yet, so the selection inside `/plugin` is a required step.

### 2b. Local plugin clone (no Cursor CLI)

Requires Git. macOS and Linux, user level (every project):

```bash
mkdir -p ~/.cursor/plugins/local
git clone https://github.com/adamcaviness/agentic-toolkit.git ~/.cursor/plugins/local/agentic-toolkit
```

Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.cursor\plugins\local" | Out-Null
git clone https://github.com/adamcaviness/agentic-toolkit.git "$env:USERPROFILE\.cursor\plugins\local\agentic-toolkit"
```

Run **Developer: Reload Window**. Confirm in **Customize → Skills**.

Update with `git -C ~/.cursor/plugins/local/agentic-toolkit pull` (on Windows, `git -C "$env:USERPROFILE\.cursor\plugins\local\agentic-toolkit" pull`), then reload.

Uninstall by deleting that `agentic-toolkit` directory, then reload.

## 3. Cursor Teams / Enterprise

**Dashboard** means the web admin UI at [cursor.com/dashboard](https://cursor.com/dashboard), not a screen inside the desktop app.

1. Admin: **Dashboard → Plugins → Team Marketplaces** → import `https://github.com/adamcaviness/agentic-marketplace`.
2. Teammates: install **agentic-toolkit** from **Customize** in the Cursor sidebar.

Team marketplaces are a Teams and Enterprise feature. On an individual plan (Hobby, Pro, Pro+, or Ultra), use path 1 or 2 instead.

## Why skills show up twice

Cursor reads skills from each of these user-level roots, and from the same names under a project root:

- `~/.cursor/plugins/local/` (Cursor local plugins, path 2b)
- Cursor marketplace plugins (paths 2a and 3)
- Claude Code plugins (path 1), when third-party includes are on
- `~/.cursor/skills/`
- `~/.agents/skills/`, the root the [manual install](../README.md#installation) links into. Codex and Gemini CLI read it too.
- `~/.claude/skills/` and `~/.codex/skills/`, legacy compatibility roots. This toolkit never installs into `~/.codex/skills/`, which Codex itself has deprecated.

Installing the same skills in more than one of those places duplicates every slash command. Fix: keep a single root, remove the extras, reload.
