#!/usr/bin/env python3
"""Validate that compression preserved structural elements."""

import re
import sys
from pathlib import Path

URL_REGEX = re.compile(r"https?://[^\s)]+")
FENCE_OPEN_REGEX = re.compile(r"^(\s{0,3})(`{3,}|~{3,})(.*)$")
HEADING_REGEX = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)
BULLET_REGEX = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
INLINE_CODE_REGEX = re.compile(r"(?<!`)(`(?!`)(.+?)(?<!`)`)(?!`)")
PATH_REGEX = re.compile(
    r"(?:\./|\.\./|/|[A-Za-z]:\\)[\w\-/\\\.]+|[\w\-\.]+[/\\][\w\-/\\\.]+")
FRONTMATTER_REGEX = re.compile(r"\A---\n(.*?\n)---\n", re.DOTALL)


def extract_frontmatter(text):
    m = FRONTMATTER_REGEX.match(text)
    return m.group(0) if m else None


def extract_headings(text):
    return [(level, title.strip()) for level, title in HEADING_REGEX.findall(text)]


def extract_code_blocks(text):
    blocks = []
    lines = text.split("\n")
    i = 0
    n = len(lines)
    while i < n:
        m = FENCE_OPEN_REGEX.match(lines[i])
        if not m:
            i += 1
            continue
        fence_char = m.group(2)[0]
        fence_len = len(m.group(2))
        block_lines = [lines[i]]
        i += 1
        closed = False
        while i < n:
            close_m = FENCE_OPEN_REGEX.match(lines[i])
            if (
                close_m
                and close_m.group(2)[0] == fence_char
                and len(close_m.group(2)) >= fence_len
                and close_m.group(3).strip() == ""
            ):
                block_lines.append(lines[i])
                closed = True
                i += 1
                break
            block_lines.append(lines[i])
            i += 1
        if closed:
            blocks.append("\n".join(block_lines))
    return blocks


def extract_inline_code(text):
    return sorted(m.group(2) for m in INLINE_CODE_REGEX.finditer(text))


def extract_urls(text):
    return set(URL_REGEX.findall(text))


def extract_paths(text):
    return set(PATH_REGEX.findall(text))


def count_bullets(text):
    return len(BULLET_REGEX.findall(text))


def validate(original_path, compressed_path):
    orig = Path(original_path).read_text(errors="ignore")
    comp = Path(compressed_path).read_text(errors="ignore")

    errors = []
    warnings = []

    fm1 = extract_frontmatter(orig)
    fm2 = extract_frontmatter(comp)
    if fm1 != fm2:
        if fm1 and not fm2:
            errors.append("Frontmatter was removed")
        elif fm1 and fm2:
            errors.append("Frontmatter was modified")

    h1 = extract_headings(orig)
    h2 = extract_headings(comp)
    if h1 != h2:
        errors.append(f"Heading mismatch: expected {len(h1)}, got {len(h2)}")

    c1 = extract_code_blocks(orig)
    c2 = extract_code_blocks(comp)
    if c1 != c2:
        errors.append("Code blocks not preserved exactly")

    ic1 = extract_inline_code(orig)
    ic2 = extract_inline_code(comp)
    missing_ic = set(ic1) - set(ic2)
    if missing_ic:
        errors.append(f"Inline code lost: {missing_ic}")

    u1 = extract_urls(orig)
    u2 = extract_urls(comp)
    if u1 != u2:
        errors.append(f"URL mismatch: lost={u1 - u2}, added={u2 - u1}")

    p1 = extract_paths(orig)
    p2 = extract_paths(comp)
    if p1 != p2:
        errors.append(f"Path mismatch: lost={p1 - p2}, added={p2 - p1}")

    b1 = count_bullets(orig)
    b2 = count_bullets(comp)
    if b1 > 0 and abs(b1 - b2) / b1 > 0.15:
        warnings.append(f"Bullet count changed significantly: {b1} -> {b2}")

    is_valid = len(errors) == 0

    print(f"Valid: {is_valid}")
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")

    return is_valid


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python validate.py <original> <compressed>")
        sys.exit(1)
    valid = validate(sys.argv[1], sys.argv[2])
    sys.exit(0 if valid else 1)
