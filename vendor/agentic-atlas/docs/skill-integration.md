# Skill integration: how the engine is driven

The primary way a human profiles a target is the `/agentic-atlas` skill in
[agentic-toolkit](https://github.com/adamcaviness/agentic-toolkit), running inside their
own agentic coding harness (Claude Code). This engine is deterministic and needs no API
key. It computes the measured indicators and validates classified answers; it never calls
a model. The skill's host agent (the user's coding agent) is the model that answers the
classified questions, so the full profile is produced with no key and no extra cost.

This file is the contract the skill targets. It is stable engine surface.

## Flow

1. **Measured, deterministic, always available.** A bare run resolves the measured
   indicators and reports the rest as `needs interpretation`, with a pointer to the skill.

   ```bash
   agentic-atlas profile <target>
   ```

2. **Get the classified worklist.**

   ```bash
   agentic-atlas questions <target>
   ```

   Emits JSON:

   ```json
   {
     "rubric_version": "1.2.0",
     "target": "/abs/path",
     "instructions": "...",
     "questions": [
       {"id": "sd1", "axis": "spec-light-vs-spec-driven",
        "question": "Is a written spec, PRD, or plan required before implementation?",
        "answers": ["encouraged", "none", "required"]}
     ]
   }
   ```

3. **The host agent answers each question** from the target repository only, choosing one
   value from `answers` and citing a quote copied verbatim from the target.

4. **Feed the answers back to score them.** The file (or stdin, via `-`) is:

   ```json
   {
     "source": "agentic-toolkit:claude-opus-4-8",
     "answers": {
       "sd1": {"answer": "none", "evidence": "a verbatim quote from the target"}
     }
   }
   ```

   ```bash
   agentic-atlas questions <target> \
     | ... agent answers ... \
     | agentic-atlas profile <target> --answers -
   ```

## What the engine guarantees

- **Validation, not trust.** Every supplied answer must name one of the indicator's
  declared values and cite a quote found verbatim in the target. A missing or failing
  answer leaves the indicator unresolved and out of the score. Validation stops a
  fabricated citation; it cannot catch a real-but-cherry-picked one, so the answers file
  is a reviewable artifact and its provenance (`source`) is stamped on the profile.
- **Determinism.** Given the same answers, the score is identical. Measured values the
  engine derives; classified values are inputs it validates and scores.
- **Reproducibility.** An answers file can be committed next to a published profile, so a
  classified-complete profile is reproducible without re-running any model.
