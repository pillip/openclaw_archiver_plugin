"""Shared output formatting helpers."""

from __future__ import annotations

SEPARATOR = "───"


def format_date(created_at: str | None) -> str:
    """Extract YYYY-MM-DD from an ISO timestamp."""
    return created_at[:10] if created_at else ""


def format_archive_rows(
    rows: list[tuple],
    *,
    include_project: bool = True,
) -> list[str]:
    """Format archive rows into display lines.

    Args:
        rows: Tuples of (id, title, link, [project_name,] created_at).
              When *include_project* is True the tuple must contain
              project_name; otherwise it is omitted.
        include_project: Whether to display project label per item.

    Returns:
        List of formatted lines (no trailing blank line).
    """
    lines: list[str] = []
    for i, row in enumerate(rows):
        if include_project:
            aid, title, link, project_name, created_at = row
            date = format_date(created_at)
            proj_label = project_name if project_name else "미분류"
            lines.append(f"#{aid} {title}")
            lines.append(f"<{link}|링크> | {proj_label} | {date}")
        else:
            aid, title, link, created_at = row
            date = format_date(created_at)
            lines.append(f"#{aid} {title}")
            lines.append(f"<{link}|링크> | {date}")
        # Add blank line between items (not after last).
        if i < len(rows) - 1:
            lines.append("")

    return lines


def parse_archive_id(raw: str, command: str) -> tuple[int, str | None]:
    """Parse a raw string as an archive ID.

    Returns:
        (archive_id, None) on success, or (0, error_message) on failure.
    """
    try:
        return int(raw), None
    except ValueError:
        return 0, f"ID는 숫자여야 합니다. 사용법: /archive {command}"


def require_project(conn, user_id: str, project_name: str):  # type: ignore[no-untyped-def]
    """Look up a project; return (project_id, None) or (None, error_message)."""
    from openclaw_archiver.db import find_project

    project = find_project(conn, user_id, project_name)
    if project is None:
        return None, f'"{project_name}" 프로젝트를 찾을 수 없습니다.'
    return project[0], None
