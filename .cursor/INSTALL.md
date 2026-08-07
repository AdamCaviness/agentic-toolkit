# Installing Agentic Toolkit for Cursor

User-level install for Cursor desktop and CLI (Pro, Hobby, and other non-Teams plans). Skills are available in every project after one reload.

## Install (copy-paste)

Requires Git. Paste into Terminal:

```bash
mkdir -p ~/.cursor/plugins/local
git clone https://github.com/adamcaviness/agentic-toolkit.git ~/.cursor/plugins/local/agentic-toolkit
```

Then in Cursor: Command Palette → **Developer: Reload Window** (or quit and reopen Cursor).

Confirm in **Customize → Skills**, or type `/` in Agents (for example `/pr`, `/triage-bugs`).

## Update

```bash
git -C ~/.cursor/plugins/local/agentic-toolkit pull
```

Reload the window again.

## Uninstall

```bash
rm -rf ~/.cursor/plugins/local/agentic-toolkit
```

Reload the window.

## Already have a clone?

If you keep a working copy elsewhere (for example this repo), link it instead of cloning twice:

```bash
mkdir -p ~/.cursor/plugins/local
ln -sfn /absolute/path/to/agentic-toolkit ~/.cursor/plugins/local/agentic-toolkit
```

## Teams / Enterprise

Team Marketplace import is a web admin flow at [cursor.com/dashboard](https://cursor.com/dashboard) → **Plugins**, not a screen in the desktop app. Individuals on Pro should use the install block above.
