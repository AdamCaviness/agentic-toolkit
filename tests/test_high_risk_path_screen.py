import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
AGENTS = REPO_ROOT / "AGENTS.md"


# The shared secret-shaped path screen. Every skill that publishes to a remote or
# hands a change set to a reviewer carries this literal, so a change to the
# pattern set lands everywhere at once. Before this validator the screen had
# drifted into two dialects and the publishing skills screened for less than the
# reviewing ones.
CANONICAL_SCREEN = (
    r"(^|/)(\.env|\.npmrc|\.pypirc)(\.|/|$)"
    r"|(^|/)id_(rsa|dsa|ecdsa|ed25519)([-_. 0-9][^/]*)?(\.|/|$)"
    r"|(^|/)([^/]*[-_. ])?(credentials?|secrets?)([-_ ][^/.]*)?"
    r"(/|$|\.(json|ya?ml|env|txt|ini|cfg|conf|toml|properties|xml|csv|tsv|pem|key|p12|enc)$)"
    r"|\.(pem|p12|pfx|key|crt|sqlite3?|db3?|dump|env)(-(wal|shm|journal))?$"
)

# Paths the screen must catch, and paths it must leave alone. The screen
# replaced a prose glob list that matched decorated names such as
# aws-credentials.json and client_secrets_v2.json, so the credentials and
# secrets components take decoration on both sides to keep that coverage.
#
# The terminator, not the decoration, is what keeps that breadth from stopping
# a push on ordinary work: a decorated component only matches when the path
# then ends, continues into a directory, or carries a data-bearing extension.
# Source and documentation extensions are absent from that set. Every entry in
# MUST_NOT_MATCH below is a path the decoration alone would have matched.
MUST_MATCH = [
    ".env",
    ".env.local",
    ".npmrc",
    ".pypirc",
    "production.env",
    "id_rsa",
    "id_rsa2",
    "id_rsa.pub",
    "deploy/id_rsa_backup",
    ".ssh/id_ecdsa",
    ".ssh/id_ed25519",
    "credentials",
    "credentials.json",
    "secrets/prod.yaml",
    "aws-credentials.json",
    "config/app-secrets.yaml",
    "app.secrets.yaml",
    "k8s/base/db-credentials.yaml",
    "client_secrets_v2.json",
    "my_secret.txt",
    "my secret.txt",
    "server.key",
    "certs/site.pem",
    "db.sqlite",
    "db.sqlite3",
    "data.db",
    "data.db3",
    "db.sqlite-wal",
    "db.sqlite3-journal",
    "data.db-shm",
    "backup.dump",
]

MUST_NOT_MATCH = [
    "docs/managing-secrets.md",
    "docs/secrets.md",
    "src/hooks/use-secrets.ts",
    "src/config/app-secrets.ts",
    "src/secrets-manager.ts",
    "internal/aws_credentials_test.go",
    "SecretsController.java",
    "src/credentialsProvider.ts",
    "src/lib/keyboard.ts",
    "environment.ts",
    "env/bin/activate",
    "README.md",
    "docs/security.md",
]

# Skills that stop and make the user confirm or remove a matched path.
PUBLISHING_SKILLS = ["pr", "ship", "apply-review"]

# Skills that pass matches to a reviewer and never block on them.
REVIEWING_SKILLS = ["code-review", "next-ticket"]

SCREENING_SKILLS = PUBLISHING_SKILLS + REVIEWING_SKILLS

# Alternations a reviewing skill appends after the shared literal. A false
# positive costs a reviewer one glance, while a blocking gate that matches
# src/auth/token.ts, a release tarball, or a routine CI edit prompts the user on
# every single push. Publishing skills must not carry these.
REVIEW_ONLY_ALTERNATIONS = [
    r"(^|/)(token|key)(\.|/|$)",
    r"\.(zip|tar|tgz|gz)$",
    r"(^|/)\.github/workflows/",
]


def fenced_blocks(text):
    """Yield the body of every fenced code block, including indented fences."""
    blocks = []
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if current is None:
            if stripped.startswith("```"):
                current = []
        elif stripped.startswith("```"):
            blocks.append("\n".join(current))
            current = None
        else:
            current.append(line)
    return blocks


def printing_statements(block):
    """The text of every printf statement in a block, continuations included.

    Scoped to printf so a variable that is merely consumed somewhere else in
    the block, for example inside the diff range or the screen pipe, cannot
    satisfy an assertion about the block printing it.
    """
    lines = block.splitlines()
    collected = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.lstrip().startswith("printf"):
            collected.append(line)
            while line.rstrip().endswith("\\") and index + 1 < len(lines):
                index += 1
                line = lines[index]
                collected.append(line)
        index += 1
    return "\n".join(collected)


class HighRiskPathScreenTest(unittest.TestCase):
    def skill_text(self, skill_name):
        return (SKILLS_DIR / skill_name / "SKILL.md").read_text()

    def screen_block(self, skill_name):
        """The fenced block that actually runs the screen in this skill."""
        matches = [
            block
            for block in fenced_blocks(self.skill_text(skill_name))
            if CANONICAL_SCREEN in block
        ]
        self.assertEqual(
            len(matches),
            1,
            f"{skill_name}: expected exactly one fenced block to run the screen",
        )
        return matches[0]

    def test_every_screening_skill_carries_the_canonical_screen(self):
        for skill_name in SCREENING_SKILLS:
            with self.subTest(skill=skill_name):
                self.assertIn(
                    CANONICAL_SCREEN,
                    self.skill_text(skill_name),
                    f"{skill_name}: must carry the shared high-risk path screen "
                    "verbatim so the pattern set cannot drift between skills",
                )

    def test_publishing_skills_screen_before_pushing(self):
        for skill_name in PUBLISHING_SKILLS:
            with self.subTest(skill=skill_name):
                text = self.skill_text(skill_name)
                screen_index = text.find(CANONICAL_SCREEN)
                push_index = text.find("git push")
                self.assertNotEqual(push_index, -1, f"{skill_name}: no push command")
                self.assertLess(
                    screen_index,
                    push_index,
                    f"{skill_name}: the screen must precede any push command",
                )

    def test_publishing_skills_do_not_block_on_review_only_patterns(self):
        # Archives and workflow files are review signals, not push blockers.
        for skill_name in PUBLISHING_SKILLS:
            for alternation in REVIEW_ONLY_ALTERNATIONS:
                with self.subTest(skill=skill_name, alternation=alternation):
                    self.assertNotIn(
                        alternation,
                        self.skill_text(skill_name),
                        f"{skill_name}: {alternation!r} would stop a push on "
                        "routine archive or CI changes",
                    )

    def test_reviewing_skills_extend_rather_than_replace_the_screen(self):
        for skill_name in REVIEWING_SKILLS:
            text = self.skill_text(skill_name)
            for alternation in REVIEW_ONLY_ALTERNATIONS:
                with self.subTest(skill=skill_name, alternation=alternation):
                    self.assertIn(
                        alternation,
                        text,
                        f"{skill_name}: reviewing skills keep the wider screen",
                    )

    def test_reviewing_skills_stop_on_an_unresolvable_merge_base(self):
        # An empty BASE_SHA makes the range "..HEAD_SHA" malformed, which
        # misreports the change set rather than failing loudly.
        for skill_name in REVIEWING_SKILLS:
            with self.subTest(skill=skill_name):
                text = self.skill_text(skill_name)
                self.assertIn(
                    'git merge-base HEAD "$BASE_BRANCH" 2>/dev/null || true',
                    text,
                    f"{skill_name}: merge-base fallback must not abort the block",
                )
                self.assertIn(
                    "`BASE_SHA` is empty",
                    text,
                    f"{skill_name}: must name the empty merge-base case",
                )

    def test_reviewing_skills_print_the_values_their_guards_read(self):
        # The block assigns BASE_SHA, the inventory, and the screen matches,
        # then the prose tells the agent to stop when BASE_SHA or the inventory
        # is empty. Shell state does not persist between Bash invocations, so
        # an unprinted value is unobservable and both guards would be evaluated
        # against nothing.
        for skill_name in REVIEWING_SKILLS:
            with self.subTest(skill=skill_name):
                block = self.screen_block(skill_name)
                printed = printing_statements(block)
                self.assertTrue(printed, f"{skill_name}: block prints nothing")
                for variable in (
                    "$BASE_SHA",
                    "$HEAD_SHA",
                    "$HAS_UNCOMMITTED",
                    "$CHANGED_PATH_INVENTORY",
                    "$HIGH_RISK_PATHS",
                ):
                    self.assertIn(
                        f'"{variable}"',
                        printed,
                        f"{skill_name}: {variable} is assigned but never "
                        "printed, so the agent cannot read it in a later step. "
                        "Consuming it elsewhere in the block does not count.",
                    )

    def test_code_review_stops_on_an_empty_change_set(self):
        text = self.skill_text("code-review")
        self.assertIn(
            "`CHANGED_PATH_INVENTORY` is empty",
            text,
            "code-review must not dispatch a subagent against an empty diff",
        )

    def test_screen_block_resolves_and_verifies_its_own_base_branch(self):
        # Shell state does not persist between Bash invocations, so the screen
        # cannot inherit BASE_BRANCH from an earlier block. Both failure modes
        # are silent: an unset BASE_BRANCH reduces "$BASE_BRANCH"...HEAD to
        # ...HEAD, which compares HEAD with itself and prints nothing, and a
        # BASE_BRANCH naming a branch the repository lacks makes git diff fail
        # into the same empty output, which the trailing "|| true" then masks.
        # Empty output from either case reads as a clean inventory and lets a
        # committed secret through the gate. Reviewing skills reach the same
        # base through git merge-base and already stop on an empty BASE_SHA,
        # which test_reviewing_skills_stop_on_an_unresolvable_merge_base pins.
        for skill_name in PUBLISHING_SKILLS:
            with self.subTest(skill=skill_name):
                block = self.screen_block(skill_name)
                self.assertIn(
                    '"$BASE_REF"...HEAD',
                    block,
                    f"{skill_name}: the screen must diff against the verified "
                    "base ref, never a hardcoded branch name",
                )
                self.assertIn(
                    'BASE_REF="$BASE_BRANCH"',
                    block,
                    f"{skill_name}: BASE_REF must derive from the resolved "
                    "BASE_BRANCH",
                )
                self.assertIn(
                    "git symbolic-ref refs/remotes/origin/HEAD",
                    block,
                    f"{skill_name}: the screen block must resolve BASE_BRANCH "
                    "itself rather than inherit it from an earlier block",
                )
                self.assertIn(
                    'BASE_REF="origin/$BASE_BRANCH"',
                    block,
                    f"{skill_name}: a single-branch clone has origin/<base> "
                    "but no local <base>, and stopping there blocks a "
                    "legitimate push",
                )
                self.assertIn(
                    'git rev-parse --verify "$BASE_REF" >/dev/null 2>&1 || {',
                    block,
                    f"{skill_name}: the screen block must verify the base ref "
                    "resolves, since a bad base yields empty output that reads "
                    "as clean",
                )

    def test_publishing_skills_treat_a_failed_screen_as_a_stop(self):
        # The verify guard exits non-zero rather than printing paths. Without
        # prose saying so, an agent reads the empty output as a clean gate and
        # pushes, which is the same fail-open the guard was added to close.
        for skill_name in PUBLISHING_SKILLS:
            with self.subTest(skill=skill_name):
                self.assertIn(
                    "**A non-zero exit means the gate never ran.**",
                    self.skill_text(skill_name),
                    f"{skill_name}: must name the failed-screen disposition",
                )

    def test_screen_distinguishes_no_matches_from_a_failed_screen(self):
        # `|| true` swallows every grep status. grep exits 1 for "no matches",
        # which is a clean result, and 2 for a failure such as an invalid
        # pattern or a missing grep. Flattening both to success hands back the
        # same empty output, which reads as a clean gate: the exact fail-open
        # this screen exists to prevent.
        for skill_name in SCREENING_SKILLS:
            with self.subTest(skill=skill_name):
                # Only the screen itself. The reviewing blocks also carry a
                # deliberate `|| true` on the merge-base line, which lets
                # BASE_SHA come back empty so the explicit emptiness check can
                # stop on it.
                screen_tail = self.screen_block(skill_name).partition("grep -Ei")[2]
                self.assertNotIn(
                    "|| true",
                    screen_tail,
                    f"{skill_name}: `|| true` turns a failed screen into an "
                    "empty result that reads as clean",
                )
                self.assertRegex(
                    screen_tail,
                    r'\$\? -eq 1|SCREEN_STATUS" -eq 1',
                    f"{skill_name}: the screen must accept grep's exit 1 only, "
                    "and let any other status stop the gate",
                )

    def test_reviewing_skills_screen_bare_paths(self):
        # CHANGED_PATH_INVENTORY prefixes each line with a state and status
        # column separated by tabs. The screen anchors on (^|/), and a tab is
        # neither, so feeding it the annotated inventory silently hides every
        # root-level .env, id_rsa, and credentials.json. Screen the bare path
        # list instead, and keep the annotated inventory for the reviewer.
        for skill_name in REVIEWING_SKILLS:
            with self.subTest(skill=skill_name):
                block = self.screen_block(skill_name)
                # The assignment body only, so the trailing display printfs
                # that echo the annotated inventory do not count as input.
                screen_input = block.partition("HIGH_RISK_PATHS=$(")[2].partition(
                    "\n)"
                )[0]
                self.assertIn(
                    '"$CHANGED_PATHS"',
                    screen_input,
                    f"{skill_name}: the screen must read the bare path list",
                )
                self.assertNotIn(
                    '"$CHANGED_PATH_INVENTORY"',
                    screen_input,
                    f"{skill_name}: the screen must not read the annotated "
                    "inventory, whose leading tab defeats the (^|/) anchor",
                )

    def test_annotated_inventory_lines_defeat_the_screen(self):
        # Pins the reason test_reviewing_skills_screen_bare_paths exists, so a
        # future change that reroutes the annotated inventory into the screen
        # cannot look harmless.
        # Only the alternatives anchored on (^|/) are defeated. A path ending
        # in a matched extension, such as .env or server.key, still matches
        # through the $-anchored group, which is exactly what makes the bug
        # easy to miss by spot-checking.
        anchored_only = ["id_rsa", ".npmrc", "credentials", "secrets/prod.yaml"]
        for path in anchored_only:
            with self.subTest(path=path):
                self.assertIn(path, self.screened([path]), "bare path must match")
                self.assertNotIn(
                    f"committed\tA\t{path}",
                    self.screened([f"committed\tA\t{path}"]),
                    "the screen is expected to miss annotated lines, which is "
                    "why the reviewing skills must feed it bare paths",
                )

    def screened(self, paths):
        """Run the canonical screen through grep exactly as the skills do."""
        result = subprocess.run(
            ["grep", "-Ei", CANONICAL_SCREEN],
            input="\n".join(paths) + "\n",
            capture_output=True,
            text=True,
        )
        # grep exits 1 on no match, which is not an error here.
        self.assertIn(
            result.returncode, (0, 1), f"grep failed: {result.stderr.strip()}"
        )
        # Split on newlines only. A path may contain a space, and the screen is
        # expected to match one, so splitting on whitespace would shred it.
        return set(result.stdout.splitlines())

    def test_screen_matches_secret_shaped_paths(self):
        matched = self.screened(MUST_MATCH)
        for path in MUST_MATCH:
            with self.subTest(path=path):
                self.assertIn(path, matched, f"{path}: screen must catch this")

    def test_screen_leaves_ordinary_source_paths_alone(self):
        matched = self.screened(MUST_NOT_MATCH)
        for path in MUST_NOT_MATCH:
            with self.subTest(path=path):
                self.assertNotIn(
                    path,
                    matched,
                    f"{path}: a match here stops a push on an ordinary file",
                )

    def test_no_skill_screens_or_pushes_outside_the_rosters(self):
        # PUBLISHING_SKILLS and REVIEWING_SKILLS are hand-maintained, so every
        # assertion above is blind to a skill added later. A new skill that
        # pushes to a remote, or that hand-rolls its own screen, must join a
        # roster and inherit the shared literal rather than drift on its own.
        rostered = set(SCREENING_SKILLS)
        for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            skill_name = skill_file.parent.name
            if skill_name in rostered:
                continue
            text = skill_file.read_text()
            with self.subTest(skill=skill_name):
                self.assertNotIn(
                    "git push",
                    text,
                    f"{skill_name}: pushes to a remote but is not in "
                    "PUBLISHING_SKILLS, so nothing checks it screens first",
                )
                # SSH private key filenames and .pypirc have no reason to
                # appear in a skill that is not screening. `.npmrc` is
                # deliberately not a fingerprint: `update-deps` legitimately
                # discusses npm registry configuration and would be forced
                # into a roster it does not belong in.
                for fingerprint in (".pypirc", "id_rsa", "id_dsa"):
                    self.assertNotIn(
                        fingerprint,
                        text,
                        f"{skill_name}: looks like it screens for secret-shaped "
                        f"paths ({fingerprint}) but is in no roster, so it can "
                        "drift from the shared literal",
                    )

    def test_agents_md_documents_the_shared_screen(self):
        text = AGENTS.read_text()
        self.assertIn("High-risk path screen", text)
        self.assertIn(CANONICAL_SCREEN, text)


if __name__ == "__main__":
    unittest.main()
