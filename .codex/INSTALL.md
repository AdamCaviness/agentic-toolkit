# Installing Agentic Toolkit for Codex

Enable these skills in Codex via native skill discovery. Clone the repo once, then symlink the `skills/` directory into `~/.agents/skills/`.

## Prerequisites

- Git

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/adamcaviness/agentic-toolkit.git ~/.codex/agentic-toolkit
   ```

2. **Create the skills symlink:**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/agentic-toolkit/skills ~/.agents/skills/agentic-toolkit
   ```

   **Windows (PowerShell):**
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\agentic-toolkit" "$env:USERPROFILE\.codex\agentic-toolkit\skills"
   ```

3. **Restart Codex** (quit and relaunch the CLI) to discover the skills.

## Verify

```bash
ls -la ~/.agents/skills/agentic-toolkit
```

You should see a symlink (or junction on Windows) pointing to the cloned skills directory.

## Updating

```bash
cd ~/.codex/agentic-toolkit && git pull
```

Skills update instantly through the symlink.

## Uninstalling

```bash
rm ~/.agents/skills/agentic-toolkit
```

Optionally delete the clone: `rm -rf ~/.codex/agentic-toolkit`.
