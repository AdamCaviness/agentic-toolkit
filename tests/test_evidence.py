"""Tests for evidence collection helpers."""

import os
import subprocess

import pytest

from agentic_atlas import evidence
from agentic_atlas.evidence import (
    Target,
    _count_terms,
    _matches,
    _parse_github_slug,
    resolve_measured,
)
from agentic_atlas.models import Indicator, IndicatorKind


@pytest.mark.parametrize(
    "path,pattern,expected",
    [
        ("skills/foo.md", "**/skills/**", True),  # top-level dir, no parent segment
        ("a/b/skills/foo.md", "**/skills/**", True),  # nested
        ("skills/foo.md", "skills/**", True),
        ("src/agent.md", "**/*agent*.md", True),
        ("agents/pm/agent.md", "**/agents/**", True),
        ("readme.md", "**/skills/**", False),
        ("skillset/foo.md", "**/skills/**", False),  # must be a real path segment
        ("BROWNFIELD.md", "**/brownfield*", False),  # case-sensitive by design
        ("brownfield-guide.md", "**/brownfield*", True),
    ],
)
def test_matches(path, pattern, expected):
    assert _matches(path, pattern) is expected


def test_count_terms_matches_whole_tokens_only():
    # Short terms must not match inside unrelated words: "ci" is a substring of
    # special/decision, "api" of capital, but neither should count there.
    corpus = "a special decision about capital efficiency, and we run ci with the api"
    assert _count_terms(corpus, ["ci"]) == 1
    assert _count_terms(corpus, ["api"]) == 1


def test_count_terms_handles_multiword_and_hyphenated_terms():
    assert _count_terms("we do test-first with a pull request", ["test-first", "pull request"]) == 2
    # a longer word that merely contains the phrase does not count
    assert _count_terms("subtest-first pull requests here", ["test-first", "pull request"]) == 0


def test_count_terms_is_whole_token_not_stem():
    # Deliberate, documented limitation: matching is whole-token, so inflected forms
    # must be listed explicitly in the rubric rather than relying on a stem.
    assert _count_terms("the deployment was deployed", ["deploy"]) == 0
    assert _count_terms("the deployment was deployed", ["deployment", "deployed"]) == 2


def test_files_walked_in_deterministic_order(tmp_path):
    for name in ["z.md", "a.md", "m/b.md"]:
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    paths = Target.from_path(tmp_path).relative_paths()
    assert paths == ["a.md", "m/b.md", "z.md"]


def test_ignore_junk_files(tmp_path):
    (tmp_path / "README.md").write_text("real content")
    (tmp_path / ".DS_Store").write_bytes(b"\x00junk")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / ".DS_Store").write_bytes(b"\x00junk")
    paths = Target.from_path(tmp_path).relative_paths()
    assert "README.md" in paths
    assert not any(p.endswith(".DS_Store") for p in paths)


def test_ignore_vendored_and_build_dirs(tmp_path):
    # Vendored third-party trees and build artifacts are not the project's own content,
    # so they must not enter the corpus or the matched-path list. A project's methodology
    # signal must reflect what it authored, not code it merely bundles.
    (tmp_path / "README.md").write_text("real content here")
    for d in ["vendor", "vendored", "third_party", "third-party", "node_modules"]:
        sub = tmp_path / d / "pkg"
        sub.mkdir(parents=True)
        (sub / "doc.md").write_text("vendored spec plan test agent content")
    target = Target.from_path(tmp_path)
    paths = target.relative_paths()
    assert "README.md" in paths
    assert not any(
        p.split("/", 1)[0] in {"vendor", "vendored", "third_party", "third-party", "node_modules"}
        for p in paths
    )
    corpus = target.text_corpus(lower=False)
    assert "real content here" in corpus
    assert "vendored spec plan test agent content" not in corpus


def _git(root, *args, when=None):
    env = None
    if when is not None:
        env = {"GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
    subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, **env} if env else None,
    )


@pytest.fixture
def git_repo(tmp_path):
    """A repo with two commits exactly 400 days apart, one author, one tag."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "dev@example.com")
    _git(tmp_path, "config", "user.name", "Dev")
    (tmp_path / "a.txt").write_text("one")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "first", when="2020-01-01T00:00:00 +0000")
    (tmp_path / "b.txt").write_text("two")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "second", when="2021-02-04T00:00:00 +0000")
    _git(tmp_path, "tag", "v1.0.0")
    return Target.from_path(tmp_path)


def test_git_metrics(git_repo):
    assert git_repo.git_metric("commit_count") == 2
    assert git_repo.git_metric("contributor_count") == 1
    assert git_repo.git_metric("tag_count") == 1
    assert git_repo.git_metric("age_days") == 400.0


def _git_stats_indicator(metric, bands):
    return Indicator(
        id="fm",
        question="q",
        kind=IndicatorKind.MEASURED,
        weight=1.0,
        signal={"type": "git_stats", "metric": metric, "bands": bands},
    )


def test_git_stats_bands_a_metric(git_repo):
    bands = [
        {"max_count": 180, "value": -1.0},
        {"max_count": 730, "value": 0.3},
        {"max_count": None, "value": 1.0},
    ]
    result = resolve_measured(_git_stats_indicator("age_days", bands), git_repo)
    assert result.resolved is True
    assert result.value == 0.3  # 400 days lands in the middle band
    assert result.answer == "400.0"
    assert result.source == "engine"


def test_git_stats_unresolved_without_git(tmp_path):
    target = Target.from_path(tmp_path)  # a plain dir, no git history
    bands = [{"max_count": None, "value": 1.0}]
    result = resolve_measured(_git_stats_indicator("commit_count", bands), target)
    assert result.resolved is False
    assert result.value is None
    assert result.kind is IndicatorKind.MEASURED


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/owner/repo.git", ("owner", "repo")),
        ("https://github.com/owner/repo", ("owner", "repo")),
        ("git@github.com:owner/repo.git", ("owner", "repo")),
        ("ssh://git@github.com/owner/repo.git", ("owner", "repo")),
        ("https://github.com/owner/repo/", ("owner", "repo")),
        ("https://gitlab.com/owner/repo.git", None),
    ],
)
def test_parse_github_slug(url, expected):
    assert _parse_github_slug(url) == expected


def _github_indicator(metric, bands):
    return Indicator(
        id="fm5",
        question="q",
        kind=IndicatorKind.MEASURED,
        weight=1.0,
        signal={"type": "github_api", "metric": metric, "bands": bands},
    )


_STAR_BANDS = [
    {"max_count": 100, "value": -0.8},
    {"max_count": 2000, "value": 0.2},
    {"max_count": None, "value": 1.0},
]


def test_github_api_bands_a_metric(tmp_path, monkeypatch):
    target = Target.from_path(tmp_path)
    monkeypatch.setattr(Target, "github_slug", lambda self: ("owner", "repo"))
    monkeypatch.setattr(evidence, "_fetch_github_repo", lambda o, r: {"stargazers_count": 5000})
    result = resolve_measured(_github_indicator("stars", _STAR_BANDS), target)
    assert result.resolved is True
    assert result.value == 1.0  # 5000 stars is above the top band threshold
    assert result.answer == "5000"


def test_github_api_unresolved_without_network(tmp_path, monkeypatch):
    target = Target.from_path(tmp_path)
    monkeypatch.setattr(Target, "github_slug", lambda self: ("owner", "repo"))
    monkeypatch.setattr(evidence, "_fetch_github_repo", lambda o, r: None)
    result = resolve_measured(_github_indicator("stars", _STAR_BANDS), target)
    assert result.resolved is False
    assert result.value is None


def test_github_api_unresolved_without_remote(tmp_path, monkeypatch):
    target = Target.from_path(tmp_path)
    monkeypatch.setattr(Target, "github_slug", lambda self: None)
    called = False

    def _boom(owner, repo):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(evidence, "_fetch_github_repo", _boom)
    result = resolve_measured(_github_indicator("stars", _STAR_BANDS), target)
    assert result.resolved is False
    assert called is False  # no slug means we never hit the network


# --- unreadable-target guards -------------------------------------------------------------
# An empty or unreadable target must not read as a confident position at the absent pole.
# vocabulary/path_presence stay unresolved when there is nothing to read, and tag_count
# stays unresolved on a repo with no commits, so an empty target lands in the null state
# rather than being slammed to the negative pole at low coverage.

_ZERO_BANDS = [{"max_count": 0, "value": -1.0}, {"max_count": None, "value": 1.0}]


def _vocab_indicator(terms, bands):
    return Indicator(
        id="v",
        question="q",
        kind=IndicatorKind.MEASURED,
        weight=1.0,
        signal={"type": "vocabulary", "terms": terms, "bands": bands},
    )


def _path_indicator(globs):
    return Indicator(
        id="p",
        question="q",
        kind=IndicatorKind.MEASURED,
        weight=1.0,
        signal={"type": "path_presence", "globs": globs, "present": 1.0, "absent": -1.0},
    )


_COUNT_BANDS = [
    {"max_count": 0, "value": -0.6},
    {"max_count": 3, "value": -0.2},
    {"max_count": 15, "value": 0.3},
    {"max_count": 60, "value": 0.6},
    {"max_count": None, "value": 0.8},
]


def _path_count_indicator(globs, bands):
    return Indicator(
        id="pc",
        question="q",
        kind=IndicatorKind.MEASURED,
        weight=1.0,
        signal={"type": "path_count", "globs": globs, "bands": bands},
    )


def test_vocabulary_unresolved_on_empty_corpus(tmp_path):
    target = Target.from_path(tmp_path)  # a dir with no readable text at all
    result = resolve_measured(_vocab_indicator(["legacy", "migration"], _ZERO_BANDS), target)
    assert result.resolved is False
    assert result.value is None


def test_vocabulary_resolves_on_real_corpus_with_zero_hits(tmp_path):
    # Genuine absence in a readable corpus is a real signal and must still resolve, so the
    # guard only fires when there is nothing to read, not merely nothing matched.
    (tmp_path / "README.md").write_text("project prose without any of the target words")
    target = Target.from_path(tmp_path)
    result = resolve_measured(_vocab_indicator(["legacy", "migration"], _ZERO_BANDS), target)
    assert result.resolved is True
    assert result.value == -1.0
    assert result.answer == "0"


def test_path_presence_unresolved_when_no_files(tmp_path):
    target = Target.from_path(tmp_path)
    result = resolve_measured(_path_indicator(["**/skills/**"]), target)
    assert result.resolved is False
    assert result.value is None


def test_path_presence_absent_is_a_signal_when_files_exist(tmp_path):
    (tmp_path / "README.md").write_text("x")
    target = Target.from_path(tmp_path)
    result = resolve_measured(_path_indicator(["**/skills/**"]), target)
    assert result.resolved is True
    assert result.value == -1.0
    assert result.answer == "absent"


def test_tag_count_unresolved_without_commits(tmp_path):
    _git(tmp_path, "init", "-q")  # a repo with no commits yet
    target = Target.from_path(tmp_path)
    assert target.git_metric("tag_count") is None


def test_path_count_bands_to_the_right_value(tmp_path):
    # Five matching files land in the third band (3 < 5 <= 15) at value 0.3, so a
    # count-based signal discriminates a handful from a single presence bit.
    (tmp_path / "skills").mkdir()
    for i in range(5):
        (tmp_path / "skills" / f"s{i}.md").write_text("x")
    target = Target.from_path(tmp_path)
    result = resolve_measured(_path_count_indicator(["**/skills/**"], _COUNT_BANDS), target)
    assert result.resolved is True
    assert result.value == 0.3
    assert result.answer == "5"
    assert result.source == "engine"


def test_path_count_bands_many_files_to_top(tmp_path):
    # A large module surface reads high; 90 files clears the top threshold to 0.8.
    (tmp_path / "skills").mkdir()
    for i in range(90):
        (tmp_path / "skills" / f"s{i}.md").write_text("x")
    target = Target.from_path(tmp_path)
    result = resolve_measured(_path_count_indicator(["**/skills/**"], _COUNT_BANDS), target)
    assert result.resolved is True
    assert result.value == 0.8
    assert result.answer == "90"


def test_path_count_unresolved_when_no_files(tmp_path):
    target = Target.from_path(tmp_path)
    result = resolve_measured(_path_count_indicator(["**/skills/**"], _COUNT_BANDS), target)
    assert result.resolved is False
    assert result.value is None
    assert result.kind is IndicatorKind.MEASURED


def test_path_count_counts_across_nested_dirs(tmp_path):
    # A glob counts every match wherever it sits in the tree, and files outside the
    # glob do not inflate the count.
    for rel in ["skills/a.md", "pkg/skills/b.md", "deep/nested/skills/c.md"]:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    (tmp_path / "README.md").write_text("not a skill")
    target = Target.from_path(tmp_path)
    result = resolve_measured(_path_count_indicator(["**/skills/**"], _COUNT_BANDS), target)
    assert result.resolved is True
    assert result.answer == "3"
    assert result.value == -0.2  # 3 files lands in the second band
