#!/usr/bin/env bash
# Thin launcher for the vendored agentic-atlas engine.
#
# It resolves the engine that ships alongside this skill (vendor/agentic-atlas),
# ensures a runnable interpreter with the engine's deps, then forwards every
# argument to the engine unchanged. The /agentic-atlas skill calls it as:
#
#   bash atlas.sh questions <target>
#   bash atlas.sh profile  <target> --answers - --format json
#
# All bootstrap chatter is written to stderr, so the engine's stdout (JSON or a
# report) can be piped or captured cleanly. The engine itself is deterministic
# and needs no API key; this script only makes it runnable.

set -euo pipefail

log() { printf '%s\n' "atlas.sh: $*" >&2; }
die() { log "$*"; exit 1; }

# --- Resolve this script's real directory, following symlinks -----------------
# Skills are distributed by symlinking the skill directory (Codex, manual
# installs), so $0 may be a symlink. The engine lives relative to the *real*
# file, not the symlink, so resolve the chain before walking up.
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [ "${SOURCE#/}" = "$SOURCE" ] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"

# --- Locate the vendored engine -----------------------------------------------
# AGENTIC_ATLAS_ENGINE overrides discovery (useful for testing against a
# checkout elsewhere). Otherwise walk up from this skill to the repo root and
# find vendor/agentic-atlas by its pyproject.toml.
ENGINE="${AGENTIC_ATLAS_ENGINE:-}"
if [ -z "$ENGINE" ]; then
  dir="$SCRIPT_DIR"
  while [ "$dir" != "/" ]; do
    if [ -f "$dir/vendor/agentic-atlas/pyproject.toml" ]; then
      ENGINE="$dir/vendor/agentic-atlas"
      break
    fi
    dir="$(dirname "$dir")"
  done
fi
[ -n "$ENGINE" ] && [ -f "$ENGINE/pyproject.toml" ] \
  || die "could not find the vendored engine (vendor/agentic-atlas). Set AGENTIC_ATLAS_ENGINE to its path."

# The repo root is the directory that holds vendor/agentic-atlas. The skill's --save step
# resolves it here so profile artifacts land in the agentic-toolkit checkout, not the target
# project or the current directory.
REPO_ROOT="$(cd "$ENGINE/../.." >/dev/null 2>&1 && pwd)"
if [ "${1:-}" = "--repo-root" ]; then
  printf '%s\n' "$REPO_ROOT"
  exit 0
fi

VENV="$ENGINE/.venv"
ATLAS="$VENV/bin/agentic-atlas"
PY="$VENV/bin/python"

# --- Pick a system interpreter for bootstrapping ------------------------------
# The engine requires Python >= 3.11. Only used to CREATE the venv; once the
# venv exists this is not consulted again.
find_python() {
  for cand in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
      if "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 11) else 1)' 2>/dev/null; then
        command -v "$cand"
        return 0
      fi
    fi
  done
  return 1
}

venv_ok() {
  # A venv is usable only if the console script exists and the interpreter can
  # import the engine and its two runtime deps. This catches a half-built or
  # dependency-missing venv, not just an absent one.
  [ -x "$ATLAS" ] && [ -x "$PY" ] \
    && "$PY" -c 'import agentic_atlas, yaml, jsonschema' >/dev/null 2>&1
}

if ! venv_ok; then
  # Build (or rebuild) the engine venv. Remove a broken one first so the rebuild
  # starts clean. The editable install pulls the two runtime deps and creates the
  # agentic-atlas console script, which is all the skill needs (no dev extras).
  log "bootstrapping engine venv at $VENV (first run)"
  [ -e "$VENV" ] && rm -rf "$VENV"
  sys_py="$(find_python)" || die "need Python >= 3.11 on PATH to build the engine venv"
  "$sys_py" -m venv "$VENV" 1>&2
  "$PY" -m pip install -q --upgrade pip 1>&2
  "$PY" -m pip install -q -e "$ENGINE" 1>&2
  venv_ok || die "engine venv is still not runnable after bootstrap"
fi

exec "$ATLAS" "$@"
