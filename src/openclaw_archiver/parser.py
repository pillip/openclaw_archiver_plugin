"""Deterministic input parser — URL extraction, /p option, save args."""

from __future__ import annotations

import re

# Matches http:// or https:// followed by non-whitespace characters.
_URL_RE = re.compile(r"https?://\S+")

# Matches ` /p <project>` at the end of a string.
# The space before /p is required so that "a/p" in the middle is NOT matched.
_PROJECT_RE = re.compile(r"\s+/p\s+(\S+)\s*$")


def extract_project_option(text: str) -> tuple[str, str | None]:
    """Extract ``/p <project>`` from the **end** of *text*.

    Returns:
        (remaining_text, project_name) — project_name is None when absent.
    """
    m = _PROJECT_RE.search(text)
    if m:
        return text[: m.start()], m.group(1)
    return text, None


def extract_url(text: str) -> tuple[str, str | None]:
    """Extract the first URL from *text*.

    Returns:
        (remaining_text, url) — url is None when no URL is found.
    """
    m = _URL_RE.search(text)
    if m:
        remaining = (text[: m.start()] + text[m.end() :]).strip()
        return remaining, m.group(0)
    return text.strip(), None


def parse_save(args: str) -> tuple[str | None, str | None, str | None]:
    """Parse the arguments of a ``save`` command.

    Parsing order:
        1. Extract ``/p <project>`` from end of string.
        2. Extract URL.
        3. Remaining text = title.

    Returns:
        (title, link, project) — any field may be None if absent/empty.
    """
    remaining, project = extract_project_option(args)
    remaining, link = extract_url(remaining)
    title = remaining.strip() or None
    return title, link, project
