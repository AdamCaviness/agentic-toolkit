# Installing Agentic Toolkit for Cursor

Cursor discovers skills from several places. Use **exactly one** of the paths below for this plugin, or every skill appears twice in **Customize → Skills** and under `/` in Agents.

| Your setup | What to do |
|---|---|
| You already use **Claude Code** with this plugin | Install once in Claude Code (path 1). Cursor picks it up automatically. Do **not** also install path 2. |
| **Cursor only** (Pro / Hobby / individual) | Clone or link into `~/.cursor/plugins/local` (path 2). |
| **Cursor Teams / Enterprise** admin | Import the marketplace from the web dashboard (path 3). Teammates install from **Customize**. |

Leave **Settings → Rules, Skills, Subagents → Include third-party Plugins, Skills, and other configs** enabled (the default) if you rely on path 1. Turning it off hides Claude Code / Codex skill roots from Cursor.

## 1. Via Claude Code (best if you use both)

In Claude Code:

```bash
/plugin marketplace add adamcaviness/agentic-marketplace
/plugin install agentic-toolkit@agentic-marketplace
```

Reload Cursor (**Developer: Reload Window**). Skills show under `/` in Agents and in **Customize → Skills**.

Stop here. Do not also clone or symlink into `~/.cursor/plugins/local`, `~/.cursor/skills/`, or `~/.agents/skills/`.

## 2. Cursor only (Pro / individual, no Claude Code install)

Requires Git. User-level (every project):

```bash
mkdir -p ~/.cursor/plugins/local
git clone https://github.com/adamcaviness/agentic-toolkit.git ~/.cursor/plugins/local/agentic-toolkit
```

Or, if you already have a clone on disk:

```bash
mkdir -p ~/.cursor/plugins/local
ln -sfn /absolute/path/to/agentic-toolkit ~/.cursor/plugins/local/agentic-toolkit
```

Reload the window. Confirm in **Customize → Skills**.

Update a clone install with `git -C ~/.cursor/plugins/local/agentic-toolkit pull`, then reload.

Uninstall:

```bash
rm -rf ~/.cursor/plugins/local/agentic-toolkit
# only if you also linked elsewhere (usually you should not):
rm -f ~/.agents/skills/agentic-toolkit
```

## 3. Cursor Teams / Enterprise

**Dashboard** means the web admin UI at [cursor.com/dashboard](https://cursor.com/dashboard), not a screen inside the Mac app.

1. Admin: **Dashboard → Plugins → Team Marketplaces** → import `https://github.com/adamcaviness/agentic-marketplace`.
2. Teammates: install **agentic-toolkit** from **Customize** in the Cursor sidebar.

Individuals on Pro should use path 1 or 2 instead.

## Why skills show up twice

Cursor scans, among other roots:

- `~/.cursor/plugins/local/` (Cursor local plugins)
- `~/.claude/plugins/` (Claude Code marketplace installs), when third-party includes are on
- `~/.agents/skills/` and `~/.cursor/skills/`
- `~/.codex/skills/` (Codex), when third-party includes are on

Installing the same skills in more than one of those places duplicates every slash command. Fix: keep a single root, remove the extras, reload.
