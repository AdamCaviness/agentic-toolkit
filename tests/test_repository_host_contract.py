"""Workflow skills support every repository host the ticket skills invite.

Issue #118: the ticket skills branch on GitHub, GitLab, Azure Boards, Jira and
more, while /pr, /ship, /apply-review, and /update-deps hard-required `gh` and a
GitHub-shaped API. A GitLab or Azure DevOps operator could pick up a ticket and
then not publish it. Every skill that talks to the repository host carries one
shared `## Repository Host` section verbatim, the way the high-risk path screen
is carried, so host detection and interface selection change in one edit.
"""

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
README = REPO_ROOT / "README.md"

HOST_SKILLS = ["pr", "ship", "apply-review", "update-deps"]

# A host operation written for one provider's CLI or API. `gh issue` is the
# ticket tracker, not the repository host, so next-ticket and create-ticket
# are not caught by it.
HOST_COMMAND = re.compile(r"\bgh (pr|api|repo)\b|\bglab (mr|api)\b|\baz repos\b")


def skill_text(name):
    return (SKILLS_DIR / name / "SKILL.md").read_text()


def section(text, header):
    match = re.search(
        rf"^{re.escape(header)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    return match.group(1) if match else None


class SharedRepositoryHostSectionTest(unittest.TestCase):
    def test_every_host_skill_carries_the_section(self):
        for name in HOST_SKILLS:
            with self.subTest(skill=name):
                self.assertIsNotNone(
                    section(skill_text(name), "## Repository Host"),
                    f"{name} must carry the shared ## Repository Host section",
                )

    def test_section_is_identical_across_skills(self):
        reference = section(skill_text(HOST_SKILLS[0]), "## Repository Host")
        self.assertIsNotNone(reference)
        for name in HOST_SKILLS[1:]:
            with self.subTest(skill=name):
                self.assertEqual(
                    section(skill_text(name), "## Repository Host"),
                    reference,
                    f"{name} drifted from the shared ## Repository Host section",
                )

    def test_skills_outside_the_roster_issue_no_host_commands(self):
        for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            name = path.parent.name
            if name in HOST_SKILLS:
                continue
            with self.subTest(skill=name):
                self.assertIsNone(
                    HOST_COMMAND.search(path.read_text()),
                    f"{name} runs a repository host command without the shared "
                    "## Repository Host section; add it to HOST_SKILLS",
                )


class RepositoryHostSectionContentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = section(skill_text("pr"), "## Repository Host") or ""
        cls.lower = cls.text.lower()

    def test_names_every_supported_provider(self):
        for provider in ["GitHub", "GitLab", "Azure DevOps Repos", "Bitbucket Cloud"]:
            with self.subTest(provider=provider):
                self.assertIn(provider, self.text)

    def test_detects_from_origin_remote(self):
        self.assertIn("git remote get-url origin", self.text)

    def test_maps_representative_remotes(self):
        # Fixtures for the scenarios the ticket names: GitLab subgroups and a
        # self-hosted GitLab whose host name does not name the provider.
        for remote in [
            "git@github.com:",
            "git@gitlab.com:acme/platform/api.git",
            "https://git.acme.dev/",
            "dev.azure.com/",
            "bitbucket.org",
        ]:
            with self.subTest(remote=remote):
                self.assertIn(remote, self.text)
        self.assertIn("acme/platform/api", self.text)
        self.assertIn("subgroup", self.lower)
        self.assertIn("self-hosted", self.lower)

    def test_keeps_ticket_tracker_independent(self):
        self.assertRegex(self.lower, r"independent of the ticket tracker")

    def test_never_requires_gh_off_github(self):
        self.assertIn("never require `gh` on a host that is not github", self.lower)
        for interface in ["`glab`", "`az repos`", "mcp", "rest api"]:
            with self.subTest(interface=interface):
                self.assertIn(interface, self.lower)

    def test_unreachable_host_is_not_an_empty_result(self):
        self.assertRegex(self.lower, r"never an empty result")


class PrSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = skill_text("pr")

    def test_host_interface_is_confirmed_before_push(self):
        confirm = self.text.index("confirm one interface authenticates")
        push = self.text.index("**Push to remote**")
        self.assertLess(confirm, push)

    def test_no_hard_stop_on_gh_for_every_host(self):
        self.assertNotIn("**`gh` not authenticated**", self.text)

    def test_discovers_non_github_templates(self):
        self.assertIn(".gitlab/merge_request_templates/Default.md", self.text)
        self.assertIn(".azuredevops/pull_request_template.md", self.text)

    def test_creates_against_detected_default_branch(self):
        host = section(self.text, "## Repository Host")
        for create in [
            "gh pr create --repo <owner/repo> --base",
            "glab mr create",
            "--target-branch",
            "az repos pr create",
            "destination.branch.name",
        ]:
            with self.subTest(create=create):
                self.assertIn(create, host)


class ShipSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = skill_text("ship")
        cls.lower = cls.text.lower()

    def test_reads_merge_evidence_per_provider(self):
        for evidence in [
            "gh pr checks <number> --repo <owner/repo> --required",
            "detailed_merge_status",
            "az repos pr policy list",
            "/statuses",
        ]:
            with self.subTest(evidence=evidence):
                self.assertIn(evidence, self.text)

    def test_github_repo_without_required_checks_is_not_failed(self):
        # `gh pr checks --required` exits 1 when a repository requires no
        # checks. Reading that as a failure stopped /ship on every such repo.
        # Issue #165, PR #164: no required checks plus UNSTABLE hid three
        # pending optional checks. Absence of required checks must trigger
        # an all-checks read, never approval from mergeability alone.
        self.assertIn("no required checks reported", self.text)
        self.assertRegex(self.lower, r"`unknown` is pending")
        self.assertIn("`gh pr checks <number> --repo <owner/repo>`", self.text)
        self.assertIn("no checks reported", self.text)
        self.assertNotIn("let `mergeStateStatus` decide", self.text)

    def test_github_reads_optional_checks_even_when_required_checks_pass(self):
        self.assertRegex(self.lower, r"always [^.\n]*all checks")
        self.assertIn("even when required checks passed", self.lower)

    def test_github_classifies_all_checks_before_mergeability(self):
        self.assertRegex(self.lower, r"exit 8[^.\n]*pending")
        self.assertRegex(self.lower, r"exit 1[^.\n]*failed check[^.\n]*failed")
        self.assertIn("failed optional checks block", self.lower)
        self.assertIn("cancelled checks also block", self.lower)
        self.assertIn("checks take precedence over pending checks", self.lower)
        self.assertIn("adding `--json` changes the exit behavior", self.lower)
        self.assertRegex(self.lower, r"any other error is \*\*inaccessible\*\*")
        self.assertIn("poll every 30 seconds", self.lower)
        self.assertIn("after 10 minutes", self.lower)

    def test_github_unstable_is_never_ready(self):
        self.assertIn("`UNSTABLE` means non-passing commit status", self.text)
        self.assertIn("Ready only when `mergeStateStatus` is `CLEAN`", self.text)
        self.assertIn("`UNSTABLE` never approves a merge", self.text)
        self.assertNotIn("only non-required checks failing", self.text)

    def test_github_rechecks_head_after_reading_checks(self):
        self.assertIn("Re-read the PR after the checks", self.text)
        self.assertIn("headRefOid", self.text)

    def test_ship_operator_copy_uses_default_branch(self):
        self.assertNotIn("base branch", self.lower)

    def test_github_commands_target_origin_not_upstream(self):
        for command in re.findall(r"`(gh (?:pr|repo) [^`]*)`", self.text):
            with self.subTest(command=command):
                # `gh repo view` takes the repository positionally.
                self.assertIn("<owner/repo>", command)

    def test_evidence_is_pinned_to_current_head(self):
        self.assertIn("git rev-parse HEAD", self.text)
        self.assertIn("stale", self.lower)
        self.assertIn("--match-head-commit", self.text)
        self.assertIn("--sha", self.text)

    def test_pending_failed_and_inaccessible_never_approve(self):
        for state in ["pending", "failed", "inaccessible"]:
            with self.subTest(state=state):
                self.assertIn(state, self.lower)
        self.assertIn("never read missing evidence as approval", self.lower)

    def test_evidence_precedes_merge_and_merge_precedes_cleanup(self):
        evidence = self.lower.index("read merge evidence")
        merge = self.lower.index("**merge")
        cleanup = self.lower.index("**clean up**")
        self.assertLess(evidence, merge)
        self.assertLess(merge, cleanup)

    def test_scheduled_auto_merge_is_not_a_confirmed_merge(self):
        self.assertRegex(self.lower, r"auto-merge or auto-complete is not a merge")

    def test_never_bypasses_policy(self):
        self.assertIn("--bypass-policy", self.text)
        self.assertRegex(self.lower, r"never [^.\n]*--bypass-policy")

    def test_policy_cache_is_keyed_by_provider(self):
        for provider in ['"github"', '"gitlab"']:
            with self.subTest(provider=provider):
                self.assertIn(provider, self.text)


class ApplyReviewSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = skill_text("apply-review")
        cls.lower = cls.text.lower()

    def test_reads_native_threads_per_provider(self):
        for api in ["/discussions", "/threads", "/comments"]:
            with self.subTest(api=api):
                self.assertIn(api, self.text)

    def test_resolution_is_conditional_on_provider_support(self):
        self.assertIn('"fixed"', self.text)
        self.assertIn("resolved=true", self.text)
        self.assertRegex(self.lower, r"does not support (thread )?resolution")

    def test_copilot_rerequest_is_github_only(self):
        copilot = section(self.text, "## Step 11: Offer to Re-request Copilot Review")
        self.assertIsNotNone(copilot)
        self.assertRegex(copilot.lower(), r"github only|only on github")

    def test_graphql_is_conditional_on_github(self):
        fetch = section(self.text, "## Step 4: Fetch Review Threads")
        self.assertIsNotNone(fetch)
        graphql = fetch.index("gh api graphql")
        self.assertIn("**GitHub**", fetch[:graphql])


class UpdateDepsSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = skill_text("update-deps")
        cls.step_2 = section(
            cls.text, "## Step 2: Check Open PRs for Automated CVE Patches"
        )

    def test_gh_gate_applies_only_on_github(self):
        lower = self.step_2.lower()
        gate = lower.index("gh auth status")
        self.assertIn("**github**", lower[:gate])

    def test_does_not_assume_dependabot_off_github(self):
        lower = self.step_2.lower()
        self.assertIn("renovate/", lower)
        self.assertRegex(lower, r"source branch")

    def test_unsupported_listing_is_distinct_from_empty(self):
        self.assertRegex(self.step_2.lower(), r"unsupported|cannot list")


class GetItRightSkillTest(unittest.TestCase):
    def test_reads_intent_from_detected_ticket_tracker(self):
        text = skill_text("get-it-right")
        self.assertNotIn("GitHub issue", text)
        self.assertIn("next-ticket-config.json", text)
        self.assertRegex(text.lower(), r"ticket tracker")


class ReadmeSupportClaimsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = README.read_text()

    def test_workflow_section_names_supported_hosts(self):
        workflow = section(self.text, "## Workflow Skills")
        self.assertIsNotNone(workflow)
        for provider in ["GitHub", "GitLab", "Azure DevOps Repos", "Bitbucket Cloud"]:
            with self.subTest(provider=provider):
                self.assertIn(provider, workflow)

    def test_apply_review_claim_is_not_github_only(self):
        self.assertNotIn("resolves addressed threads via GitHub's API", self.text)

    def test_ship_gate_no_longer_defers_to_this_ticket(self):
        self.assertNotIn("issues/118", self.text)

    def test_ship_gate_documents_optional_ci_policy(self):
        gate = section(self.text, "### Claude Ship Gate")
        self.assertIn("pending or failed optional checks", gate)
        self.assertIn("`CLEAN`", gate)


if __name__ == "__main__":
    unittest.main()
