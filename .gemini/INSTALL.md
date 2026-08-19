# Installing Agentic Toolkit for Gemini CLI

Gemini CLI loads this repo as an extension from `gemini-extension.json`. Skills come from `skills/`. Session context comes from `.gemini/extension-context.md`, a short operator primer. This repository's `AGENTS.md` is the contributor guide for people changing the toolkit. It is not Gemini session context.

Use **exactly one** install path.

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

## 2. Manual (clone on disk)

Use this only if you cannot install from GitHub. Point Gemini at a local clone the way the [Gemini CLI extension docs](https://google-gemini.github.io/gemini-cli/docs/extensions/) describe for a local path, then enable the extension. Do not also run path 1 against the same clone, or the skills appear twice.

Update a clone with `git pull` in that directory, then `gemini extensions update agentic-toolkit` if the CLI still tracks it as an installed extension.

## Windows

The same `gemini extensions` commands work in PowerShell or cmd once the Gemini CLI is on `PATH`. There is no separate plugin marketplace step.
