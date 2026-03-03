"""Handler for /archive list command."""

from __future__ import annotations

from openclaw_archiver.db import (
    find_project,
    get_connection,
    list_archives,
    list_archives_by_project,
)
from openclaw_archiver.parser import extract_project_option

_SEPARATOR = "─────────────────────────────"
_EMPTY_ALL = "저장된 메세지가 없습니다. /archive save 로 메세지를 저장해보세요."
_NOT_FOUND = '"{name}" 프로젝트를 찾을 수 없습니다.'
_EMPTY_PROJECT = '"{name}" 프로젝트에 저장된 메세지가 없습니다.'


def handle(args: str, user_id: str) -> str:
    """List archived messages, optionally filtered by project."""
    # Prepend space so regex `\s+/p\s+` can match at start of args.
    _, project_name = extract_project_option(" " + args if args else args)

    conn = get_connection()
    try:
        if project_name:
            return _list_by_project(conn, user_id, project_name)
        return _list_all(conn, user_id)
    finally:
        conn.close()


def _list_all(conn, user_id: str) -> str:  # type: ignore[no-untyped-def]
    rows = list_archives(conn, user_id)
    if not rows:
        return _EMPTY_ALL

    count = len(rows)
    lines = [f"저장된 메세지 ({count}건)", f"        {_SEPARATOR}"]

    for aid, title, link, project_name, created_at in rows:
        date = created_at[:10] if created_at else ""
        proj_label = f"프로젝트: {project_name}" if project_name else "미분류"
        lines.append(f"        #{aid}  {title}")
        lines.append(f"            {link}")
        lines.append(f"            {proj_label} | {date}")
        lines.append("")

    # Remove trailing empty line.
    if lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)


def _list_by_project(conn, user_id: str, project_name: str) -> str:  # type: ignore[no-untyped-def]
    project = find_project(conn, user_id, project_name)
    if project is None:
        return _NOT_FOUND.format(name=project_name)

    project_id = project[0]
    rows = list_archives_by_project(conn, user_id, project_id)
    if not rows:
        return _EMPTY_PROJECT.format(name=project_name)

    count = len(rows)
    lines = [
        f"저장된 메세지 — {project_name} ({count}건)",
        f"        {_SEPARATOR}",
    ]

    for aid, title, link, created_at in rows:
        date = created_at[:10] if created_at else ""
        lines.append(f"        #{aid}  {title}")
        lines.append(f"            {link}")
        lines.append(f"            {date}")
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines)
