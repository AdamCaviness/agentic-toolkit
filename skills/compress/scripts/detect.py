#!/usr/bin/env python3
"""Detect whether a file is a CLAUDE.md file eligible for compression."""

import re
from pathlib import Path

CLAUDE_MD_PATTERN = re.compile(r"^claude\.md$", re.IGNORECASE)


def is_claude_md(filepath: Path) -> bool:
    """Return True if the filename is a CLAUDE.md variant (any casing)."""
    return bool(CLAUDE_MD_PATTERN.match(filepath.name))


def should_compress(filepath: Path) -> bool:
    """Return True if the file is a CLAUDE.md and should be compressed."""
    if not filepath.is_file():
        return False
    if filepath.name.endswith(".original.md"):
        return False
    return is_claude_md(filepath)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python detect.py <file1> [file2] ...")
        sys.exit(1)

    for path_str in sys.argv[1:]:
        p = Path(path_str).resolve()
        compress = should_compress(p)
        print(f"  {p.name:30s} compress={compress}")
