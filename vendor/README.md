# Vendored dependencies

## `agentic-atlas`

The [agentic-atlas](https://github.com/AdamCaviness/agentic-atlas) engine, vendored as a git
subtree so the `/agentic-atlas` skill (`skills/agentic-atlas/`) ships with the engine it
drives. The engine is deterministic and needs no API key: it computes the measured
indicators and validates classified answers, and the skill's host agent supplies those
answers. See `skills/agentic-atlas/SKILL.md`.

The engine's virtual environment is created on first skill run at
`vendor/agentic-atlas/.venv/` and is gitignored, so nothing under it is committed.

### Refresh to the latest engine

Pull the latest engine from upstream `main`. The working tree must be clean first.

```bash
git subtree pull --prefix vendor/agentic-atlas https://github.com/AdamCaviness/agentic-atlas.git main --squash
```

This mutates git history, so it is a deliberate maintenance step, never run automatically on
a skill invocation.

### First vendor (already done, for reference)

```bash
git subtree add --prefix vendor/agentic-atlas https://github.com/AdamCaviness/agentic-atlas.git main --squash
```
