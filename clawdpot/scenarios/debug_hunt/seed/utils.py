"""Utility functions for the task manager."""

import re


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    - Lowercase
    - Replace non-alphanumeric chars with hyphens
    - Collapse multiple hyphens
    - Strip leading/trailing hyphens
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)
    # BUG 1: Does not strip leading/trailing hyphens
    return text


def truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len characters, adding '...' if truncated.

    The '...' counts toward max_len, so the actual text portion is max_len - 3.
    If text is already within max_len, return as-is.
    """
    if len(text) <= max_len:
        return text
    # BUG 2: Off-by-one — should be max_len - 3, not max_len - 2
    return text[:max_len - 2] + "..."


def parse_csv_line(line: str) -> list[str]:
    """Parse a single CSV line, respecting quoted fields.

    Fields are comma-separated. Quoted fields (double quotes) can contain commas.
    Leading/trailing whitespace in fields is stripped.
    """
    fields = []
    current = ""
    in_quotes = False

    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == "," and not in_quotes:
            fields.append(current.strip())
            current = ""
        else:
            current += char

    # BUG 3: Forgets to append the last field
    return fields
