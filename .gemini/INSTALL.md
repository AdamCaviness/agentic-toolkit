# Installing Agentic Toolkit for Gemini CLI

Gemini CLI loads this repo as an extension from `gemini-extension.json`. Skills come from `skills/`. Session context comes from `.gemini/extension-context.md`, a short operator primer. This repository's `AGENTS.md` is the contributor guide for people changing the toolkit. It is not Gemini session context.

Use **exactly one** install path. The `gemini extensions` commands below work the same in bash, zsh, PowerShell, and cmd once the Gemini CLI is on `PATH`.

## 1. Gemini CLI (recommended)

```bash
gemini extensions install https://github.com/adamcaviness/agentic-toolkit
```

Start a new Gemini session in the project you want to work on. Try `/next-ticket`.

Update:

```bash
gemini extensions update agentic-toolkit
```

List with `gemini extensions list`. Remove with `gemini extensions uninstall agentic-toolkit`.

## 2. Extension from a local clone

Use this only if you cannot install from GitHub. Clone the repo, then choose one of:

```bash
gemini extensions install /path/to/agentic-toolkit   # copies the clone into ~/.gemini/extensions
gemini extensions link /path/to/agentic-toolkit      # points Gemini at the clone itself
```

- **`install`** keeps a copy. After `git pull` in the clone, run `gemini extensions update agentic-toolkit` to refresh the copy.
- **`link`** reads the clone directly, so `git pull` alone updates it. On Windows, `link` creates a symbolic link, which needs Developer Mode or an Administrator shell; use `install` otherwise.

Remove either with `gemini extensions uninstall agentic-toolkit`. Do not also run path 1, or the extension is installed twice.

## 3. Skills only, without the extension

Gemini CLI also reads skills from `~/.agents/skills/` (and `~/.gemini/skills/`). The [manual install](../README.md#installation) links the skills into `~/.agents/skills/` on macOS, Linux, and Windows, and the same links serve Codex and Cursor. This path skips the extension's session primer.

Do not combine it with path 1 or 2. Gemini gives skills in `~/.agents/skills/` precedence over the extension's copies, so the extension's skills are silently shadowed and an extension update no longer changes what runs.
