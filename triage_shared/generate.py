"""Generator for the triage SKILL.md files.

Reads template.md plus per-skill inputs from skills.py and produces the
public `skills/triage-*/SKILL.md` files. Run with:

    python3 -m triage_shared.generate

Use --check to compare generated output against the on-disk files
without writing. Returns exit 0 if they match, 1 if they diverge.
"""

import argparse
import re
import sys
from pathlib import Path

from triage_shared.skills import SKILLS


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = Path(__file__).parent / "template.md"
SKILLS_DIR = REPO_ROOT / "skills"


def _build_substitutions(skill_name, skill_data):
    """Take the raw per-skill data and add derived strings.

    Lists derived from `cluster_slugs` and `cluster_names` are computed
    here so the per-skill data stays focused on the source-of-truth
    fields (slugs, names) rather than every list that mentions them.
    """
    slugs = skill_data["cluster_slugs"]
    names = skill_data["cluster_names"]
    if len(slugs) != 4 or len(names) != 4:
        raise ValueError(
            f"{skill_name}: cluster_slugs and cluster_names must each have 4 entries"
        )

    issues_edit_lines = "\n".join(
        f"   - `<cache>/issues-edit-{slug}.json`" for slug in slugs
    )
    cross_cluster_lines = "\n".join(
        f"   - `cross-cluster-{slug}.json`" for slug in slugs
    )
    over_cap_lines = "\n".join(
        f"   - `over-cap-{slug}.json`" for slug in slugs
    )
    assignment_example = (
        f"  <id> \"Ticket title...\" -> {names[0]}\n"
        f"  <id> \"Ticket title...\" -> {names[1]}\n"
        f"  ..."
    )

    subs = dict(skill_data)
    subs["name"] = skill_name
    subs["issues_edit_files"] = issues_edit_lines
    subs["cross_cluster_files"] = cross_cluster_lines
    subs["over_cap_files"] = over_cap_lines
    subs["cluster_assignment_example"] = assignment_example
    subs["example_cluster_name"] = names[0]
    return subs


def _apply_substitutions(template, subs):
    """Replace every `{{key}}` in `template` with `subs[key]`.

    Detects unresolved placeholders so a typo in a key surfaces as a
    clear error rather than landing in the generated file.
    """
    out = template
    for key, value in subs.items():
        if not isinstance(value, str):
            continue
        out = out.replace("{{" + key + "}}", value)

    leftover = re.findall(r"\{\{[a-zA-Z0-9_]+\}\}", out)
    if leftover:
        unique = sorted(set(leftover))
        raise ValueError(
            f"unresolved template placeholders: {', '.join(unique)}"
        )
    return out


def generate(skill_name):
    """Return the full SKILL.md text for `skill_name`."""
    if skill_name not in SKILLS:
        raise KeyError(f"unknown skill: {skill_name}")
    template = TEMPLATE_PATH.read_text()
    subs = _build_substitutions(skill_name, SKILLS[skill_name])
    return _apply_substitutions(template, subs)


def write_all():
    """Write every triage SKILL.md to disk. Returns the list of paths written."""
    written = []
    for skill_name in SKILLS:
        path = SKILLS_DIR / skill_name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(generate(skill_name))
        written.append(path)
    return written


def check_all():
    """Compare generated output against on-disk files. Returns list of diffs."""
    diffs = []
    for skill_name in SKILLS:
        path = SKILLS_DIR / skill_name / "SKILL.md"
        on_disk = path.read_text() if path.exists() else ""
        regenerated = generate(skill_name)
        if on_disk != regenerated:
            diffs.append(skill_name)
    return diffs


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify on-disk files match generator output without writing",
    )
    args = parser.parse_args()

    if args.check:
        diffs = check_all()
        if diffs:
            print(
                "Generator output diverges from on-disk SKILL.md for: "
                + ", ".join(diffs),
                file=sys.stderr,
            )
            print(
                "Run: python3 -m triage_shared.generate",
                file=sys.stderr,
            )
            return 1
        print("All triage SKILL.md files match the shared source.")
        return 0

    paths = write_all()
    for path in paths:
        print(f"wrote {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
