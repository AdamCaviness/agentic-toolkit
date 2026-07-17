"""Gather evidence from a target and resolve measured indicators.

Measured indicators are deterministic given their input: the engine computes them
directly from the repository with no model. Signal types supported today:

- ``vocabulary``    term density across the text corpus, banded by count.
- ``path_presence`` glob matches to a present/absent value.
- ``git_stats``     a fact read from the target's git history (commit count,
  contributors, age, tags), banded to a value.
- ``github_api``    a point-in-time fact from the GitHub host API for the origin
  remote (stars, forks, watchers, open issues), banded to a value.

``git_stats`` and ``github_api`` can fail to resolve (no git history, no origin
remote, no network). When that happens the indicator is marked unresolved and
counted against coverage rather than crashing the profile. ``github_api`` is
point-in-time and not pinned by the target SHA, so the fetched value is recorded
verbatim as evidence, which is the honesty signal for a mutable host fact.

Adding a signal type means extending ``resolve_measured`` and the schema, and is a
rubric-affecting change only if an existing rubric starts using it.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .models import Indicator, IndicatorKind, IndicatorResult


@lru_cache(maxsize=256)
def _glob_regex(pattern: str) -> re.Pattern:
    """Compile a glob to regex with recursive ``**`` support.

    fnmatch treats ``**`` as ``*`` and does not cross directories usefully, so a
    pattern like ``**/skills/**`` fails to match a top-level ``skills/`` directory.
    This translation makes ``**`` match any number of path segments, ``*`` match
    within a segment, and ``?`` match one non-separator character.
    """
    out, i, n = "", 0, len(pattern)
    while i < n:
        c = pattern[i]
        i += 1
        if c == "*":
            if i < n and pattern[i] == "*":
                i += 1
                if i < n and pattern[i] == "/":
                    i += 1
                    out += "(?:.*/)?"
                else:
                    out += ".*"
            else:
                out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        else:
            out += re.escape(c)
    return re.compile(f"^{out}$", re.DOTALL)


def _matches(path: str, pattern: str) -> bool:
    return _glob_regex(pattern).match(path) is not None


@lru_cache(maxsize=1024)
def _term_pattern(term: str) -> re.Pattern:
    """Match ``term`` as a whole token.

    A short term like ``ci`` or ``api`` must not match inside an unrelated word
    (``special``, ``capital``); lookarounds require a non-word character (or the
    string edge) on both sides, which also handles multi-word and hyphenated terms.
    """
    return re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)")


def _count_terms(corpus: str, terms: list[str]) -> int:
    return sum(len(_term_pattern(t.lower()).findall(corpus)) for t in terms)


# File extensions that make up an approach's readable surface.
_TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".yaml", ".yml", ".json", ".toml"}
_MAX_FILE_BYTES = 512_000
# Directories that never hold the approach's own authored content: VCS internals, build
# artifacts and virtualenvs, and vendored third-party dependencies. A project's methodology
# signal must not be diluted by code it merely bundles, so vendored trees are excluded the
# same way ``node_modules`` already is.
_IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    "vendor", "vendored", "third_party", "third-party",
}
# OS and editor cruft that should never count as target content or a matched path.
_IGNORE_FILES = {".DS_Store", "Thumbs.db"}


@dataclass
class Target:
    """A profiling target: a local directory, optionally a git checkout."""

    root: Path
    # The text corpus is read from disk once and reused: both the measured vocabulary
    # signals and the classified verbatim-quote check ask for it, once per indicator.
    _corpus: dict[str, str] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_path(cls, path: str | Path) -> "Target":
        root = Path(path).expanduser().resolve()
        if not root.is_dir():
            raise NotADirectoryError(f"target is not a directory: {root}")
        return cls(root=root)

    def _run_git(self, *args: str) -> str | None:
        try:
            out = subprocess.run(
                ["git", "-C", str(self.root), *args],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return out.stdout.strip() if out.returncode == 0 else None

    def git_sha(self) -> str | None:
        return self._run_git("rev-parse", "HEAD") or None

    def git_metric(self, metric: str) -> int | float | None:
        """Return a deterministic git-history metric, or None if unavailable.

        ``age_days`` spans the first commit to HEAD (git log lists newest first),
        so it is a function of the checked-out history, not of wall-clock now.
        """
        if metric == "commit_count":
            out = self._run_git("rev-list", "--count", "HEAD")
            return int(out) if out and out.isdigit() else None
        if metric == "contributor_count":
            out = self._run_git("log", "--format=%ae")
            if not out:
                return None
            return len({line.strip() for line in out.splitlines() if line.strip()})
        if metric == "tag_count":
            out = self._run_git("tag", "--list")
            if out is None:
                return None
            return len([line for line in out.splitlines() if line.strip()])
        if metric == "age_days":
            out = self._run_git("log", "--format=%ct")
            if not out:
                return None
            stamps = [int(x) for x in out.splitlines() if x.strip().isdigit()]
            if not stamps:
                return None
            return (stamps[0] - stamps[-1]) / 86400.0
        return None

    def github_slug(self) -> tuple[str, str] | None:
        url = self._run_git("remote", "get-url", "origin")
        return _parse_github_slug(url) if url else None

    def _files(self) -> list[Path]:
        files: list[Path] = []
        # Sorted so evidence strings and the corpus are deterministic across machines,
        # not dependent on filesystem walk order.
        for p in sorted(self.root.rglob("*")):
            if not p.is_file():
                continue
            if p.name in _IGNORE_FILES:
                continue
            if any(part in _IGNORE_DIRS for part in p.relative_to(self.root).parts):
                continue
            files.append(p)
        return files

    def text_corpus(self, *, lower: bool = True) -> str:
        if "raw" not in self._corpus:
            chunks: list[str] = []
            for p in self._files():
                if p.suffix.lower() not in _TEXT_SUFFIXES:
                    continue
                try:
                    if p.stat().st_size > _MAX_FILE_BYTES:
                        continue
                    chunks.append(p.read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    continue
            self._corpus["raw"] = "\n".join(chunks)
        if not lower:
            return self._corpus["raw"]
        if "lower" not in self._corpus:
            self._corpus["lower"] = self._corpus["raw"].lower()
        return self._corpus["lower"]

    def relative_paths(self) -> list[str]:
        return [str(p.relative_to(self.root)) for p in self._files()]


def resolve_measured(indicator: Indicator, target: Target) -> IndicatorResult:
    signal = indicator.signal or {}
    stype = signal.get("type")
    if stype == "vocabulary":
        return _resolve_vocabulary(indicator, target, signal)
    if stype == "path_presence":
        return _resolve_path_presence(indicator, target, signal)
    if stype == "git_stats":
        return _resolve_git_stats(indicator, target, signal)
    if stype == "github_api":
        return _resolve_github_api(indicator, target, signal)
    raise ValueError(f"unknown measured signal type {stype!r} for indicator {indicator.id}")


def _unresolved_measured(indicator: Indicator, reason: str) -> IndicatorResult:
    """A measured indicator the engine could not compute (missing git/network).

    Marked unresolved so it is excluded from scoring and counted against coverage,
    exactly like an unanswered classified indicator.
    """
    return IndicatorResult.unresolved(indicator, IndicatorKind.MEASURED, reason, source="engine")


def _resolve_vocabulary(indicator: Indicator, target: Target, signal: dict) -> IndicatorResult:
    corpus = target.text_corpus()
    count = _count_terms(corpus, signal["terms"])
    value = _band_value(count, signal["bands"])
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.MEASURED,
        weight=indicator.weight,
        value=value,
        resolved=True,
        answer=str(count),
        evidence=f"{count} occurrences of {signal['terms']} across the text corpus",
        source="engine",
    )


def _band_value(count: int, bands: list[dict]) -> float:
    for band in bands:
        max_count = band.get("max_count")
        if max_count is None or count <= max_count:
            return float(band["value"])
    # No catch-all band matched. Fall back to the last band's value.
    return float(bands[-1]["value"])


def _resolve_path_presence(indicator: Indicator, target: Target, signal: dict) -> IndicatorResult:
    paths = target.relative_paths()
    matched = [p for p in paths if any(_matches(p, g) for g in signal["globs"])]
    present = bool(matched)
    value = float(signal["present"]) if present else float(signal["absent"])
    evidence = f"matched {matched[:5]}" if present else f"no path matched {signal['globs']}"
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.MEASURED,
        weight=indicator.weight,
        value=value,
        resolved=True,
        answer="present" if present else "absent",
        evidence=evidence,
        source="engine",
    )


def _resolve_git_stats(indicator: Indicator, target: Target, signal: dict) -> IndicatorResult:
    metric = signal["metric"]
    raw = target.git_metric(metric)
    if raw is None:
        return _unresolved_measured(
            indicator, f"git metric {metric!r} unavailable (target has no git history)"
        )
    value = _band_value(raw, signal["bands"])
    answer = f"{raw:.1f}" if isinstance(raw, float) else str(raw)
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.MEASURED,
        weight=indicator.weight,
        value=value,
        resolved=True,
        answer=answer,
        evidence=f"git {metric} = {answer}",
        source="engine",
    )


_GITHUB_METRIC_KEYS = {
    "stars": "stargazers_count",
    "forks": "forks_count",
    "watchers": "subscribers_count",
    "open_issues": "open_issues_count",
}


def _parse_github_slug(url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from an https or ssh GitHub remote URL, or None."""
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?/?$", url.strip())
    return (m.group(1), m.group(2)) if m else None


@lru_cache(maxsize=64)
def _fetch_github_repo(owner: str, repo: str) -> dict | None:
    """Fetch the repo object from the GitHub API, or None on any failure.

    Uses ``GITHUB_TOKEN``/``GH_TOKEN`` if present (higher rate limit). Returns None
    on missing network, non-200, timeout, or malformed JSON so callers degrade to
    an unresolved indicator rather than raising.
    """
    request = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "agentic-atlas",
        },
    )
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None


def _resolve_github_api(indicator: Indicator, target: Target, signal: dict) -> IndicatorResult:
    slug = target.github_slug()
    if slug is None:
        return _unresolved_measured(indicator, "no GitHub origin remote on target")
    data = _fetch_github_repo(*slug)
    if data is None:
        return _unresolved_measured(
            indicator, "GitHub API unavailable (no network or rate limited)"
        )
    key = _GITHUB_METRIC_KEYS[signal["metric"]]
    raw = data.get(key)
    if not isinstance(raw, (int, float)):
        return _unresolved_measured(indicator, f"GitHub API response missing {key!r}")
    value = _band_value(raw, signal["bands"])
    owner, repo = slug
    return IndicatorResult(
        indicator_id=indicator.id,
        kind=IndicatorKind.MEASURED,
        weight=indicator.weight,
        value=value,
        resolved=True,
        answer=str(raw),
        evidence=f"{signal['metric']} = {raw} for {owner}/{repo} via GitHub API",
        source="engine",
    )
