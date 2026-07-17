#!/usr/bin/env bash
# Dogfood this repo's skills locally, scoped to this project only.
#
# Symlinks every skills/<name>/ into project-level .claude/skills/, which Claude
# Code discovers only while your cwd is this repo. The links are bare-named
# (/pr, /agentic-atlas), so they sit alongside the global marketplace plugin's
# namespaced commands (/agentic-toolkit:pr) without conflict, and they serve the
# live working tree instead of a pinned release.
#
# Idempotent: re-run after adding a skill to link the new one and prune links
# whose skill was removed. `.claude/skills/` is gitignored (local dev only).
# To stop dogfooding: rm -rf .claude/skills
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$REPO_ROOT/.claude/skills"
fresh=0
[ -d "$DEST" ] || fresh=1
mkdir -p "$DEST"

linked=0
for skill in "$REPO_ROOT"/skills/*/; do
  [ -f "${skill}SKILL.md" ] || continue
  name="$(basename "$skill")"
  # Never clobber a real file or directory that happens to share a skill name;
  # replace only our own symlinks (or a broken one). ln -sfn onto a real dir
  # would nest the link inside it rather than replace it.
  if [ -e "$DEST/$name" ] && [ ! -L "$DEST/$name" ]; then
    echo "skipping $name: $DEST/$name exists and is not a symlink" >&2
    continue
  fi
  # Target is relative to the link's own location ($DEST/<name>), so it stays
  # valid wherever the repo is checked out.
  ln -sfn "../../skills/$name" "$DEST/$name"
  linked=$((linked + 1))
done

# Prune links whose target skill no longer exists.
for link in "$DEST"/*; do
  [ -L "$link" ] || continue
  [ -e "$link" ] || { rm -f "$link"; echo "pruned stale link: $(basename "$link")"; }
done

echo "linked $linked skill(s) into $DEST"
if [ "$fresh" = 1 ]; then
  echo "note: .claude/skills/ was just created, so restart Claude Code once for it to be watched; after that, edits and new links are picked up live."
fi
